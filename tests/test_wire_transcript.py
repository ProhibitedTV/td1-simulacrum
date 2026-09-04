import json

import pytest

from td1_simulacrum import ReferenceLoopbackTransport, assemble, build_parity_campaign
from td1_simulacrum.campaign import run_parity_campaign
from td1_simulacrum.trace import trace_program
from td1_simulacrum.wire import (
    CAPABILITIES_CORRELATION,
    InMemoryParityLineIO,
    JsonLineParityTransport,
    ParityWireDevice,
    ParityWireEnvelope,
    WireKind,
    encode_wire_frame,
)
from td1_simulacrum.wire_transcript import (
    ParityBenchRun,
    ParityTranscriptError,
    ParityWireTranscript,
    RecordingParityLineIO,
    ReplayParityLineIO,
    replay_bench_run,
    transcript_for_report,
)


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


def _recorded_run(*, max_width: int = 12, target_id: str = "recorded.loopback"):
    target = ReferenceLoopbackTransport(target_id=target_id, max_width=max_width)
    recording = RecordingParityLineIO(InMemoryParityLineIO(ParityWireDevice(target)))
    transport = JsonLineParityTransport(recording)
    run = run_parity_campaign(transport, _campaign())
    return run, recording.transcript()


def test_recorded_transcript_is_deterministic_and_matches_report_reconstruction() -> None:
    run, transcript = _recorded_run()
    expected = transcript_for_report(run.report)

    assert transcript.canonical_json() == expected.canonical_json()
    assert transcript.digest() == expected.digest()
    assert transcript.exchange_count == len(run.report.records) + 1
    assert transcript.records[0].kind is WireKind.CAPABILITIES_REQUEST
    assert transcript.records[1].kind is WireKind.CAPABILITIES_RESPONSE

    restored = ParityWireTranscript.from_json(transcript.canonical_json())
    assert restored == transcript
    assert restored.digest() == transcript.digest()


def test_transcript_rejects_record_tampering_and_illegal_ordering() -> None:
    _, transcript = _recorded_run()

    digest_payload = json.loads(transcript.canonical_json())
    digest_payload["records"][0]["frame_sha256"] = "0" * 64
    with pytest.raises(ParityTranscriptError, match="frame SHA-256 mismatch"):
        ParityWireTranscript.from_dict(digest_payload)

    kind_payload = json.loads(transcript.canonical_json())
    kind_payload["records"][0]["kind"] = "parity_request"
    with pytest.raises(ParityTranscriptError, match="kind disagrees"):
        ParityWireTranscript.from_dict(kind_payload)

    correlation_payload = json.loads(transcript.canonical_json())
    correlation_payload["records"][0]["correlation_id"] = "WRONG"
    with pytest.raises(ParityTranscriptError, match="correlation disagrees"):
        ParityWireTranscript.from_dict(correlation_payload)

    order_payload = json.loads(transcript.canonical_json())
    order_payload["records"][0]["direction"] = "device_to_host"
    with pytest.raises(ParityTranscriptError, match="begin host_to_device"):
        ParityWireTranscript.from_dict(order_payload)


def test_recording_channel_enforces_write_read_pairs_and_complete_finalization() -> None:
    target = ReferenceLoopbackTransport()
    recording = RecordingParityLineIO(InMemoryParityLineIO(ParityWireDevice(target)))
    request = encode_wire_frame(
        ParityWireEnvelope(
            kind=WireKind.CAPABILITIES_REQUEST,
            correlation_id=CAPABILITIES_CORRELATION,
            payload={},
        )
    )

    with pytest.raises(ParityTranscriptError, match="write before read"):
        recording.read_line()

    recording.write_line(request)
    with pytest.raises(ParityTranscriptError, match="read after write"):
        recording.write_line(request)
    with pytest.raises(ParityTranscriptError, match="unread device response"):
        recording.transcript()

    recording.read_line()
    transcript = recording.transcript()
    assert transcript.exchange_count == 1


def test_replay_requires_exact_request_bytes_order_and_complete_consumption() -> None:
    _, transcript = _recorded_run()
    replay = ReplayParityLineIO(transcript)

    with pytest.raises(ParityTranscriptError, match="host write before device read"):
        replay.read_line()
    with pytest.raises(ParityTranscriptError, match="request bytes disagree"):
        replay.write_line(b"{}\n")
    with pytest.raises(ParityTranscriptError, match="consumed 0"):
        replay.assert_consumed()

    for index in range(0, len(transcript.records), 2):
        replay.write_line(transcript.records[index].frame_bytes)
        assert replay.read_line() == transcript.records[index + 1].frame_bytes
    replay.assert_consumed()

    with pytest.raises(ParityTranscriptError, match="after transcript end"):
        replay.write_line(transcript.records[0].frame_bytes)


def test_bench_run_links_exact_report_transcript_and_replays_identically() -> None:
    run, transcript = _recorded_run()
    bench = ParityBenchRun(run, transcript)
    restored = ParityBenchRun.from_json(bench.canonical_json())

    assert restored == bench
    assert restored.digest() == bench.digest()
    replayed = replay_bench_run(restored)
    assert replayed.canonical_json() == run.canonical_json()

    other_run, other_transcript = _recorded_run(target_id="different.target")
    assert other_run.report.capabilities.target_id == "different.target"
    with pytest.raises(ParityTranscriptError, match="disagrees with campaign report"):
        ParityBenchRun(run, other_transcript)


def test_capability_rejected_campaign_transcript_contains_only_handshake() -> None:
    run, transcript = _recorded_run(max_width=3)
    assert not run.report.passed
    assert all(not record.passed for record in run.report.records)
    assert transcript.exchange_count == 1

    bench = ParityBenchRun(run, transcript)
    replayed = replay_bench_run(bench)
    assert replayed.canonical_json() == run.canonical_json()
