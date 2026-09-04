import pytest

from td1_simulacrum import ReferenceLoopbackTransport, assemble, build_parity_campaign
from td1_simulacrum.campaign import run_parity_campaign
from td1_simulacrum.stream_io import (
    ParityStreamEmptyEOFError,
    ParityStreamFrameTooLargeError,
    ParityStreamPartialEOFError,
    ParityStreamReadError,
    ParityStreamWriteError,
    StreamParityLineIO,
)
from td1_simulacrum.trace import trace_program
from td1_simulacrum.wire import JsonLineParityTransport, ParityWireDevice
from td1_simulacrum.wire_transcript import (
    ParityBenchRun,
    RecordingParityLineIO,
    replay_bench_run,
)


class FragmentedDuplexStream:
    def __init__(
        self,
        *,
        read_bytes: bytes = b"",
        max_read: int = 3,
        max_write: int = 4,
    ) -> None:
        self.read_buffer = bytearray(read_bytes)
        self.written = bytearray()
        self.max_read = max_read
        self.max_write = max_write
        self.flush_count = 0

    def read(self, size: int = -1) -> bytes:
        if not self.read_buffer:
            return b""
        if size < 0:
            size = len(self.read_buffer)
        count = min(size, self.max_read, len(self.read_buffer))
        chunk = bytes(self.read_buffer[:count])
        del self.read_buffer[:count]
        return chunk

    def write(self, data: bytes) -> int:
        count = min(self.max_write, len(data))
        self.written.extend(data[:count])
        return count

    def flush(self) -> None:
        self.flush_count += 1


class ScriptedDeviceStream:
    """Fragmenting duplex stream that dispatches complete host wire frames."""

    def __init__(self, device: ParityWireDevice, *, max_read: int = 5, max_write: int = 7):
        self.device = device
        self.max_read = max_read
        self.max_write = max_write
        self.host_buffer = bytearray()
        self.device_buffer = bytearray()
        self.flush_count = 0

    def write(self, data: bytes) -> int:
        count = min(self.max_write, len(data))
        self.host_buffer.extend(data[:count])
        while True:
            newline = self.host_buffer.find(b"\n")
            if newline < 0:
                break
            frame = bytes(self.host_buffer[: newline + 1])
            del self.host_buffer[: newline + 1]
            self.device_buffer.extend(self.device.handle_frame(frame))
        return count

    def read(self, size: int = -1) -> bytes:
        if not self.device_buffer:
            return b""
        if size < 0:
            size = len(self.device_buffer)
        count = min(size, self.max_read, len(self.device_buffer))
        chunk = bytes(self.device_buffer[:count])
        del self.device_buffer[:count]
        return chunk

    def flush(self) -> None:
        self.flush_count += 1


class BadWriteStream(FragmentedDuplexStream):
    def __init__(self, result):
        super().__init__()
        self.result = result

    def write(self, data: bytes):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class BadReadStream(FragmentedDuplexStream):
    def __init__(self, result):
        super().__init__()
        self.result = result

    def read(self, size: int = -1):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


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


def test_stream_line_io_handles_partial_writes_and_flushes_once() -> None:
    stream = FragmentedDuplexStream(max_write=2)
    line_io = StreamParityLineIO(stream)
    frame = b'{"hello":"world"}\n'

    line_io.write_line(frame)

    assert bytes(stream.written) == frame
    assert stream.flush_count == 1
    assert line_io.stats.bytes_written == len(frame)
    assert line_io.stats.frames_written == 1
    assert line_io.stats.bytes_read == 0


def test_stream_line_io_reassembles_fragmented_reads_and_preserves_later_frame() -> None:
    first = b'{"a":1}\n'
    second = b'{"b":2}\n'
    stream = FragmentedDuplexStream(read_bytes=first + second, max_read=64)
    line_io = StreamParityLineIO(stream, read_chunk_bytes=64)

    assert line_io.read_line() == first
    first_stats = line_io.stats
    assert first_stats.frames_read == 1
    assert first_stats.bytes_read == len(first + second)
    assert first_stats.buffered_bytes == len(second)

    assert line_io.read_line() == second
    assert line_io.stats.frames_read == 2
    assert line_io.stats.buffered_bytes == 0


def test_stream_line_io_exact_maximum_and_oversize_detection() -> None:
    exact = b"x" * 7 + b"\n"
    line_io = StreamParityLineIO(
        FragmentedDuplexStream(read_bytes=exact, max_read=8),
        max_frame_bytes=8,
        read_chunk_bytes=8,
    )
    assert line_io.read_line() == exact

    no_newline = StreamParityLineIO(
        FragmentedDuplexStream(read_bytes=b"x" * 8, max_read=8),
        max_frame_bytes=8,
        read_chunk_bytes=8,
    )
    with pytest.raises(ParityStreamFrameTooLargeError, match="unterminated"):
        no_newline.read_line()

    newline_too_late = StreamParityLineIO(
        FragmentedDuplexStream(read_bytes=b"x" * 8 + b"\n", max_read=64),
        max_frame_bytes=8,
        read_chunk_bytes=64,
    )
    with pytest.raises(ParityStreamFrameTooLargeError, match="exceeds"):
        newline_too_late.read_line()


def test_stream_line_io_distinguishes_empty_and_partial_eof() -> None:
    empty = StreamParityLineIO(FragmentedDuplexStream())
    with pytest.raises(ParityStreamEmptyEOFError, match="before the next frame"):
        empty.read_line()

    partial = StreamParityLineIO(FragmentedDuplexStream(read_bytes=b"partial", max_read=3))
    with pytest.raises(ParityStreamPartialEOFError, match="partial frame"):
        partial.read_line()


def test_stream_line_io_rejects_bad_write_progress_and_underlying_failure() -> None:
    for result, match in (
        (None, "must return an integer"),
        (0, "zero progress"),
        ("1", "must return an integer"),
        (99, "exceeded requested length"),
    ):
        line_io = StreamParityLineIO(BadWriteStream(result))
        with pytest.raises(ParityStreamWriteError, match=match):
            line_io.write_line(b"x\n")

    line_io = StreamParityLineIO(BadWriteStream(OSError("boom")))
    with pytest.raises(ParityStreamWriteError, match="write failed"):
        line_io.write_line(b"x\n")


def test_stream_line_io_rejects_bad_read_type_and_underlying_failure() -> None:
    line_io = StreamParityLineIO(BadReadStream("not-bytes"))
    with pytest.raises(ParityStreamReadError, match="must return bytes"):
        line_io.read_line()

    line_io = StreamParityLineIO(BadReadStream(OSError("boom")))
    with pytest.raises(ParityStreamReadError, match="read failed"):
        line_io.read_line()


def test_stream_line_io_supports_explicit_reader_and_writer() -> None:
    reader = FragmentedDuplexStream(read_bytes=b"response\n")
    writer = FragmentedDuplexStream(max_write=1)
    line_io = StreamParityLineIO(reader=reader, writer=writer)

    line_io.write_line(b"request\n")
    assert line_io.read_line() == b"response\n"
    assert bytes(writer.written) == b"request\n"

    with pytest.raises(ValueError, match="both reader and writer"):
        StreamParityLineIO(reader=reader)
    with pytest.raises(ValueError, match="not both"):
        StreamParityLineIO(reader, reader=reader, writer=writer)


def test_complete_campaign_runs_through_fragmented_stream_and_replays() -> None:
    target = ReferenceLoopbackTransport(target_id="stream.loopback")
    device_stream = ScriptedDeviceStream(ParityWireDevice(target), max_read=3, max_write=5)
    stream_line = StreamParityLineIO(device_stream, read_chunk_bytes=4)
    recording = RecordingParityLineIO(stream_line)
    transport = JsonLineParityTransport(recording)

    run = run_parity_campaign(transport, _campaign())
    transcript = recording.transcript()
    bench = ParityBenchRun(run, transcript)
    replayed = replay_bench_run(bench)

    assert run.report.passed
    assert replayed.canonical_json() == run.canonical_json()
    assert device_stream.host_buffer == b""
    assert device_stream.device_buffer == b""
    stats = stream_line.stats
    assert stats.frames_written == transcript.exchange_count
    assert stats.frames_read == transcript.exchange_count
    assert stats.bytes_written > 0
    assert stats.bytes_read > 0
    assert stats.buffered_bytes == 0
