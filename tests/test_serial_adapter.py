import json
import sys
from types import SimpleNamespace

import pytest

from td1_simulacrum import ReferenceLoopbackTransport, assemble, build_parity_campaign
from td1_simulacrum.campaign import ParityCampaignRun, run_parity_campaign
from td1_simulacrum.campaign_cli import main
from td1_simulacrum.serial_adapter import (
    ParitySerialClosedError,
    ParitySerialDependencyError,
    ParitySerialReadError,
    ParitySerialReadTimeoutError,
    ParitySerialWriteError,
    ParitySerialWriteTimeoutError,
    SerialConfig,
    open_pyserial_stream,
)
from td1_simulacrum.stream_io import StreamParityLineIO
from td1_simulacrum.trace import trace_program
from td1_simulacrum.wire import JsonLineParityTransport, ParityWireDevice
from td1_simulacrum.wire_transcript import (
    ParityBenchRun,
    ParityWireTranscript,
    RecordingParityLineIO,
    replay_bench_run,
)


class FakeSerialException(Exception):
    pass


class FakeSerialTimeoutException(FakeSerialException):
    pass


class FakeSerialPort:
    def __init__(
        self,
        device: ParityWireDevice | None = None,
        *,
        max_read: int = 3,
        max_write: int = 5,
        read_failure: Exception | None = None,
        write_failure: Exception | None = None,
        flush_failure: Exception | None = None,
        close_failure: Exception | None = None,
    ) -> None:
        self.device = device
        self.max_read = max_read
        self.max_write = max_write
        self.read_failure = read_failure
        self.write_failure = write_failure
        self.flush_failure = flush_failure
        self.close_failure = close_failure
        self.is_open = True
        self.host_buffer = bytearray()
        self.device_buffer = bytearray()
        self.flush_count = 0
        self.close_count = 0

    def write(self, data: bytes) -> int:
        if self.write_failure is not None:
            raise self.write_failure
        count = min(self.max_write, len(data))
        self.host_buffer.extend(data[:count])
        if self.device is not None:
            while True:
                newline = self.host_buffer.find(b"\n")
                if newline < 0:
                    break
                frame = bytes(self.host_buffer[: newline + 1])
                del self.host_buffer[: newline + 1]
                self.device_buffer.extend(self.device.handle_frame(frame))
        return count

    def read(self, size: int = -1) -> bytes:
        if self.read_failure is not None:
            raise self.read_failure
        if not self.device_buffer:
            return b""
        if size < 0:
            size = len(self.device_buffer)
        count = min(size, self.max_read, len(self.device_buffer))
        chunk = bytes(self.device_buffer[:count])
        del self.device_buffer[:count]
        return chunk

    def flush(self) -> None:
        if self.flush_failure is not None:
            raise self.flush_failure
        self.flush_count += 1

    def close(self) -> None:
        self.close_count += 1
        if self.close_failure is not None:
            raise self.close_failure
        self.is_open = False


class FakeSerialModule:
    SerialException = FakeSerialException
    SerialTimeoutException = FakeSerialTimeoutException

    def __init__(self, device: ParityWireDevice | None = None) -> None:
        self.device = device
        self.last_kwargs = None
        self.last_port = None

    def Serial(self, **kwargs):
        self.last_kwargs = kwargs
        self.last_port = FakeSerialPort(self.device)
        return self.last_port


def _campaign():
    program = assemble(
        """
LDI R0, 2
LDI R1, 3
ADD R0, R1
ADDI R0, -1
NEG R0
HALT
"""
    )
    return build_parity_campaign(trace_program(program))


def test_serial_config_requires_explicit_valid_deployment_values() -> None:
    config = SerialConfig("COM7", 115200, 1.5, 2.5)
    assert config.as_dict() == {
        "port": "COM7",
        "baudrate": 115200,
        "read_timeout_s": 1.5,
        "write_timeout_s": 2.5,
    }

    with pytest.raises(ValueError, match="port"):
        SerialConfig(" ", 115200, 1.0, 1.0)
    with pytest.raises(ValueError, match="baudrate"):
        SerialConfig("COM7", 0, 1.0, 1.0)
    with pytest.raises(ValueError, match="read_timeout"):
        SerialConfig("COM7", 115200, 0.0, 1.0)
    with pytest.raises(ValueError, match="write_timeout"):
        SerialConfig("COM7", 115200, 1.0, 0.0)


def test_open_serial_stream_uses_explicit_settings_and_closes_once() -> None:
    module = FakeSerialModule()
    config = SerialConfig("/dev/ttyACM0", 230400, 0.75, 1.25)

    with open_pyserial_stream(config, serial_module=module) as stream:
        assert stream.is_open
        assert module.last_kwargs == {
            "port": "/dev/ttyACM0",
            "baudrate": 230400,
            "timeout": 0.75,
            "write_timeout": 1.25,
        }

    assert module.last_port.close_count == 1
    assert module.last_port.is_open is False
    stream.close()
    assert module.last_port.close_count == 1


def test_serial_specific_failures_survive_stream_line_adapter() -> None:
    config = SerialConfig("COM9", 115200, 1.0, 1.0)

    timeout_module = FakeSerialModule()
    timeout_stream = open_pyserial_stream(config, serial_module=timeout_module)
    line_io = StreamParityLineIO(timeout_stream)
    with pytest.raises(ParitySerialReadTimeoutError, match="timed out"):
        line_io.read_line()

    port = FakeSerialPort(write_failure=FakeSerialTimeoutException("slow"))
    serial_stream = open_pyserial_stream(
        config,
        serial_module=SimpleNamespace(
            Serial=lambda **kwargs: port,
            SerialException=FakeSerialException,
            SerialTimeoutException=FakeSerialTimeoutException,
        ),
    )
    with pytest.raises(ParitySerialWriteTimeoutError, match="timed out"):
        StreamParityLineIO(serial_stream).write_line(b"x\n")

    read_port = FakeSerialPort(read_failure=FakeSerialException("broken"))
    serial_stream = open_pyserial_stream(
        config,
        serial_module=SimpleNamespace(
            Serial=lambda **kwargs: read_port,
            SerialException=FakeSerialException,
            SerialTimeoutException=FakeSerialTimeoutException,
        ),
    )
    with pytest.raises(ParitySerialReadError, match="read failed"):
        StreamParityLineIO(serial_stream).read_line()

    write_port = FakeSerialPort(write_failure=FakeSerialException("broken"))
    serial_stream = open_pyserial_stream(
        config,
        serial_module=SimpleNamespace(
            Serial=lambda **kwargs: write_port,
            SerialException=FakeSerialException,
            SerialTimeoutException=FakeSerialTimeoutException,
        ),
    )
    with pytest.raises(ParitySerialWriteError, match="write failed"):
        StreamParityLineIO(serial_stream).write_line(b"x\n")


def test_closed_serial_stream_rejects_use() -> None:
    module = FakeSerialModule()
    stream = open_pyserial_stream(SerialConfig("COM1", 9600, 1.0, 1.0), serial_module=module)
    stream.close()

    with pytest.raises(ParitySerialClosedError, match="closed"):
        stream.read(1)
    with pytest.raises(ParitySerialClosedError, match="closed"):
        stream.write(b"x")
    with pytest.raises(ParitySerialClosedError, match="closed"):
        stream.flush()


def test_missing_pyserial_dependency_is_explicit(monkeypatch) -> None:
    import td1_simulacrum.serial_adapter as serial_adapter

    def missing(name: str):
        assert name == "serial"
        raise ModuleNotFoundError("no module named serial")

    monkeypatch.setattr(serial_adapter.importlib, "import_module", missing)
    with pytest.raises(ParitySerialDependencyError, match=r"td1-simulacrum\[serial\]"):
        open_pyserial_stream(SerialConfig("COM1", 115200, 1.0, 1.0))


def test_complete_campaign_runs_over_fake_serial_and_replays() -> None:
    target = ReferenceLoopbackTransport(target_id="serial.loopback")
    module = FakeSerialModule(ParityWireDevice(target))
    config = SerialConfig("COM42", 460800, 1.0, 1.0)

    with open_pyserial_stream(config, serial_module=module) as serial_stream:
        stream_line = StreamParityLineIO(serial_stream, read_chunk_bytes=4)
        recording = RecordingParityLineIO(stream_line)
        run = run_parity_campaign(JsonLineParityTransport(recording), _campaign())
        transcript = recording.transcript()
        bench = ParityBenchRun(run, transcript)
        stats = stream_line.stats

    replayed = replay_bench_run(bench)
    assert run.report.passed
    assert replayed.canonical_json() == run.canonical_json()
    assert stats.frames_written == transcript.exchange_count
    assert stats.frames_read == transcript.exchange_count
    assert module.last_port.host_buffer == b""
    assert module.last_port.device_buffer == b""
    assert module.last_port.is_open is False


def test_serial_run_cli_emits_standard_artifacts_without_deployment_leak(
    tmp_path, monkeypatch, capsys
) -> None:
    import td1_simulacrum.campaign_cli as campaign_cli

    campaign = _campaign()
    campaign_path = tmp_path / "campaign.json"
    run_path = tmp_path / "serial.run.json"
    transcript_path = tmp_path / "serial.transcript.json"
    bench_path = tmp_path / "serial.bench.json"
    campaign_path.write_text(json.dumps(campaign.as_dict()), encoding="utf-8")

    target = ReferenceLoopbackTransport(target_id="serial.cli.loopback")
    module = FakeSerialModule(ParityWireDevice(target))

    def fake_open(config):
        return open_pyserial_stream(config, serial_module=module)

    monkeypatch.setattr(campaign_cli, "open_pyserial_stream", fake_open)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "td1-parity",
            "serial-run",
            str(campaign_path),
            "--port",
            "COM42",
            "--baud",
            "460800",
            "--read-timeout",
            "1.5",
            "--write-timeout",
            "2.5",
            "--output",
            str(run_path),
            "--transcript-output",
            str(transcript_path),
            "--bench-output",
            str(bench_path),
        ],
    )

    assert main() == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["passed"] is True
    assert summary["transport"] == "td1.parity-wire/v1+serial-stream"
    assert summary["deployment"] == {
        "port": "COM42",
        "baudrate": 460800,
        "read_timeout_s": 1.5,
        "write_timeout_s": 2.5,
    }
    assert summary["stream_stats"]["frames_read"] > 0
    assert summary["stream_stats"]["frames_written"] > 0

    run_text = run_path.read_text(encoding="utf-8")
    transcript_text = transcript_path.read_text(encoding="utf-8")
    bench_text = bench_path.read_text(encoding="utf-8")
    assert "COM42" not in run_text
    assert "COM42" not in transcript_text
    assert "COM42" not in bench_text

    run = ParityCampaignRun.from_json(run_text)
    transcript = ParityWireTranscript.from_json(transcript_text)
    bench = ParityBenchRun.from_json(bench_text)
    assert summary["run_digest"] == run.digest()
    assert summary["transcript_digest"] == transcript.digest()
    assert summary["bench_run_digest"] == bench.digest()
    assert replay_bench_run(bench).canonical_json() == run.canonical_json()
    assert module.last_port.is_open is False
