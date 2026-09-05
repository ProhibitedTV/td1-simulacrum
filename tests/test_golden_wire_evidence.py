import json
import sys

import pytest

from td1_simulacrum.campaign_cli import main
from td1_simulacrum.golden import golden_suite, golden_trit_vectors
from td1_simulacrum.parity import (
    ParityCapabilities,
    ParityOperation,
    ParityRequest,
    ParityResponse,
    ParityStatus,
    golden_register_vectors,
    run_conformance,
    ternary_state_digest,
)
from td1_simulacrum.wire import (
    InMemoryParityLineIO,
    JsonLineParityTransport,
    ParityWireDevice,
    WireKind,
)
from td1_simulacrum.wire_evidence import ParityWireEvidence, replay_wire_evidence
from td1_simulacrum.wire_transcript import (
    ParityTranscriptError,
    ParityWireTranscript,
    RecordingParityLineIO,
    WireDirection,
)


class TritOnlyTarget:
    def __init__(self, target_id: str = "trit-only") -> None:
        self._capabilities = ParityCapabilities(
            target_id=target_id,
            operations=(ParityOperation.TRIT_HOLD,),
            max_width=1,
            telemetry_keys=("board_revision",),
        )

    def capabilities(self) -> ParityCapabilities:
        return self._capabilities

    def exchange(self, request: ParityRequest) -> ParityResponse:
        vector = request.vector
        assert vector.operation is ParityOperation.TRIT_HOLD
        observed = vector.expected_value
        return ParityResponse(
            session_id=request.session_id,
            sequence=request.sequence,
            vector_id=vector.vector_id,
            status=ParityStatus.OK,
            observed_value=observed,
            observed_state_digest=ternary_state_digest(vector.width, observed),
            telemetry=(("board_revision", "TRIT-TEST"),),
        )


class ScriptedSerialStream:
    """Tiny serial-like stream that fragments host/device wire traffic."""

    def __init__(self, device: ParityWireDevice, *, max_write: int = 5, max_read: int = 4):
        self._device = device
        self._max_write = max_write
        self._max_read = max_read
        self._host = bytearray()
        self._device_bytes = bytearray()
        self._closed = False

    def write(self, data: bytes) -> int:
        if self._closed:
            raise OSError("closed")
        count = min(self._max_write, len(data))
        self._host.extend(data[:count])
        while True:
            newline = self._host.find(b"\n")
            if newline < 0:
                break
            frame = bytes(self._host[: newline + 1])
            del self._host[: newline + 1]
            self._device_bytes.extend(self._device.handle_frame(frame))
        return count

    def read(self, size: int = -1) -> bytes:
        if self._closed:
            raise OSError("closed")
        if not self._device_bytes:
            return b""
        if size < 0:
            size = len(self._device_bytes)
        count = min(size, self._max_read, len(self._device_bytes))
        chunk = bytes(self._device_bytes[:count])
        del self._device_bytes[:count]
        return chunk

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.close()
        return False


def _record(target, vectors):
    recording = RecordingParityLineIO(InMemoryParityLineIO(ParityWireDevice(target)))
    report = run_conformance(JsonLineParityTransport(recording), vectors)
    return report, recording.transcript()


def test_golden_trit_suite_is_exactly_three_one_trit_holds() -> None:
    vectors = golden_trit_vectors()
    assert tuple(vector.vector_id for vector in vectors) == (
        "TRIT-NEG",
        "TRIT-ZERO",
        "TRIT-POS",
    )
    assert tuple(vector.operands for vector in vectors) == (("-",), ("0",), ("+",))
    assert all(vector.operation is ParityOperation.TRIT_HOLD for vector in vectors)
    assert all(vector.width == 1 for vector in vectors)
    assert golden_suite("trit", width=99) == vectors


def test_register_golden_vectors_preserve_canonical_trit_prefix() -> None:
    for width in (1, 3, 12):
        vectors = golden_register_vectors(width)
        assert golden_suite("register", width=width) == vectors
        assert vectors[:3] == golden_trit_vectors()


def test_trit_only_target_passes_exact_first_hardware_wire_session() -> None:
    report, transcript = _record(TritOnlyTarget(), golden_trit_vectors())
    evidence = ParityWireEvidence(report, transcript)

    assert report.passed
    assert len(report.records) == 3
    assert transcript.exchange_count == 4
    host_parity_requests = tuple(
        record
        for record in transcript.records
        if record.direction is WireDirection.HOST_TO_DEVICE
        and record.kind is WireKind.PARITY_REQUEST
    )
    assert len(host_parity_requests) == 3
    assert replay_wire_evidence(evidence).canonical_json() == report.canonical_json()


def test_generic_wire_evidence_rejects_tampered_transcript() -> None:
    report, transcript = _record(TritOnlyTarget(), golden_trit_vectors())
    evidence = ParityWireEvidence(report, transcript)
    payload = evidence.as_dict()
    records = payload["transcript"]["records"]
    records[0]["frame_text"] = records[0]["frame_text"].replace("CAPS-v1", "CAPS-vX")

    with pytest.raises(ParityTranscriptError):
        ParityWireEvidence.from_dict(payload)


def test_capability_rejected_register_vectors_do_not_create_fake_device_traffic() -> None:
    vectors = golden_suite("register", width=1)
    report, transcript = _record(TritOnlyTarget(), vectors)
    evidence = ParityWireEvidence(report, transcript)

    assert report.passed is False
    assert len(report.records) == len(vectors)
    assert sum(record.response.status is ParityStatus.UNSUPPORTED for record in report.records) == 6
    assert transcript.exchange_count == 4
    assert replay_wire_evidence(evidence).canonical_json() == report.canonical_json()


def test_serial_golden_cli_emits_report_transcript_and_generic_evidence(
    tmp_path, monkeypatch, capsys
) -> None:
    import td1_simulacrum.campaign_cli as campaign_cli

    target = TritOnlyTarget("fake.serial.trit")
    stream = ScriptedSerialStream(ParityWireDevice(target))

    def fake_open(config):
        assert config.port == "COM77"
        assert config.baudrate == 230400
        return stream

    monkeypatch.setattr(campaign_cli, "open_pyserial_stream", fake_open)
    report_path = tmp_path / "trit.report.json"
    transcript_path = tmp_path / "trit.transcript.json"
    evidence_path = tmp_path / "trit.evidence.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "td1-parity",
            "serial-golden",
            "--suite",
            "trit",
            "--port",
            "COM77",
            "--baud",
            "230400",
            "--read-timeout",
            "1.0",
            "--write-timeout",
            "1.0",
            "--report-output",
            str(report_path),
            "--transcript-output",
            str(transcript_path),
            "--evidence-output",
            str(evidence_path),
        ],
    )

    assert main() == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["passed"] is True
    assert summary["suite"] == "trit"
    assert summary["vector_count"] == 3
    assert summary["stream_stats"]["frames_written"] == 4
    assert summary["stream_stats"]["frames_read"] == 4

    report_text = report_path.read_text(encoding="utf-8")
    transcript_text = transcript_path.read_text(encoding="utf-8")
    evidence_text = evidence_path.read_text(encoding="utf-8")
    assert "COM77" not in report_text
    assert "COM77" not in transcript_text
    assert "COM77" not in evidence_text

    evidence = ParityWireEvidence.from_json(evidence_text)
    transcript = ParityWireTranscript.from_json(transcript_text)
    assert evidence.report.passed
    assert transcript.exchange_count == 4
    assert replay_wire_evidence(evidence).canonical_json() == evidence.report.canonical_json()
