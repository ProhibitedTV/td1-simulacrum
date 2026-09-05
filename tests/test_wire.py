import json

import pytest

from td1_simulacrum import (
    ParityCapabilities,
    ParityOperation,
    ParityRequest,
    ParityResponse,
    ParityStatus,
    ParityVector,
    ReferenceLoopbackTransport,
    assemble,
    build_parity_campaign,
    run_parity_campaign,
    trace_program,
)
from td1_simulacrum.wire import (
    CAPABILITIES_CORRELATION,
    BenchTelemetry,
    InMemoryParityLineIO,
    JsonLineParityTransport,
    ParityWireDevice,
    ParityWireEnvelope,
    ParityWireError,
    WireKind,
    decode_wire_frame,
    encode_wire_frame,
    parity_request_correlation,
)


def _request() -> ParityRequest:
    vector = ParityVector.create(
        "WIRE-LOAD",
        ParityOperation.REGISTER_LOAD,
        3,
        ("+0-",),
    )
    return ParityRequest("WIRE-SESSION", 0, vector)


def _wire_transport(target=None) -> JsonLineParityTransport:
    target = target or ReferenceLoopbackTransport(target_id="wire.loopback", max_width=12)
    return JsonLineParityTransport(InMemoryParityLineIO(ParityWireDevice(target)))


def test_wire_frame_is_canonical_utf8_jsonl_and_round_trips() -> None:
    envelope = ParityWireEnvelope(
        kind=WireKind.CAPABILITIES_REQUEST,
        correlation_id=CAPABILITIES_CORRELATION,
        payload={},
    )
    first = encode_wire_frame(envelope)
    second = encode_wire_frame(envelope)

    assert first == second
    assert first.endswith(b"\n")
    assert b" " not in first
    restored = decode_wire_frame(first)
    assert restored == envelope
    assert restored.digest() == envelope.digest()


def test_wire_decoder_rejects_noncanonical_malformed_and_oversize_frames() -> None:
    canonical = encode_wire_frame(
        ParityWireEnvelope(
            kind=WireKind.CAPABILITIES_REQUEST,
            correlation_id=CAPABILITIES_CORRELATION,
            payload={},
        )
    )
    payload = json.loads(canonical.decode("utf-8"))
    pretty = (json.dumps(payload, indent=2) + "\n").encode("utf-8")

    with pytest.raises(ParityWireError, match="exactly one JSON line"):
        decode_wire_frame(pretty)
    with pytest.raises(ParityWireError, match="exactly one LF"):
        decode_wire_frame(canonical[:-1] + b"\r\n")
    with pytest.raises(ParityWireError, match="valid UTF-8"):
        decode_wire_frame(b"\xff\n")
    with pytest.raises(ParityWireError, match="maximum size"):
        decode_wire_frame(canonical, max_frame_bytes=len(canonical) - 1)
    with pytest.raises(ParityWireError, match="must not be empty"):
        decode_wire_frame(b"")


def test_wire_transport_performs_capability_handshake_and_parity_exchange() -> None:
    transport = _wire_transport()
    capabilities = transport.capabilities()
    assert capabilities.target_id == "wire.loopback"
    assert capabilities.max_width == 12

    request = _request()
    response = transport.exchange(request)
    assert response.status is ParityStatus.OK
    assert response.session_id == request.session_id
    assert response.sequence == request.sequence
    assert response.vector_id == request.vector.vector_id
    assert response.observed_value == request.vector.expected_value


def test_device_rejects_wrong_request_correlation() -> None:
    device = ParityWireDevice(ReferenceLoopbackTransport())
    request = _request()
    envelope = ParityWireEnvelope(
        kind=WireKind.PARITY_REQUEST,
        correlation_id="WRONG",
        payload=request.as_dict(),
    )
    with pytest.raises(ParityWireError, match="correlation mismatch"):
        device.handle_frame(encode_wire_frame(envelope))


def test_device_rejects_byte_canonical_payload_that_relies_on_type_coercion() -> None:
    device = ParityWireDevice(ReferenceLoopbackTransport())
    request = _request()
    payload = request.as_dict()
    payload["sequence"] = "0"
    envelope = ParityWireEnvelope(
        kind=WireKind.PARITY_REQUEST,
        correlation_id=parity_request_correlation(request),
        payload=payload,
    )
    frame = encode_wire_frame(envelope)

    assert decode_wire_frame(frame).payload["sequence"] == "0"
    with pytest.raises(ParityWireError, match="canonical parity schema"):
        device.handle_frame(frame)


class _ScriptedLineIO:
    def __init__(self, response: bytes) -> None:
        self.response = response
        self.written: bytes | None = None

    def write_line(self, frame: bytes) -> None:
        self.written = frame

    def read_line(self) -> bytes:
        return self.response


def test_host_rejects_wrong_wire_kind_and_correlation() -> None:
    wrong_kind = encode_wire_frame(
        ParityWireEnvelope(
            kind=WireKind.PARITY_RESPONSE,
            correlation_id=CAPABILITIES_CORRELATION,
            payload={},
        )
    )
    with pytest.raises(ParityWireError, match="expected wire kind"):
        JsonLineParityTransport(_ScriptedLineIO(wrong_kind)).capabilities()

    capabilities = ReferenceLoopbackTransport().capabilities()
    wrong_correlation = encode_wire_frame(
        ParityWireEnvelope(
            kind=WireKind.CAPABILITIES_RESPONSE,
            correlation_id="OTHER",
            payload=capabilities.as_dict(),
        )
    )
    with pytest.raises(ParityWireError, match="correlation_id"):
        JsonLineParityTransport(_ScriptedLineIO(wrong_correlation)).capabilities()


def test_host_rejects_byte_canonical_capabilities_payload_that_normalizes() -> None:
    capabilities = ReferenceLoopbackTransport().capabilities()
    payload = capabilities.as_dict()
    payload["max_width"] = "12"
    response = encode_wire_frame(
        ParityWireEnvelope(
            kind=WireKind.CAPABILITIES_RESPONSE,
            correlation_id=CAPABILITIES_CORRELATION,
            payload=payload,
        )
    )

    with pytest.raises(ParityWireError, match="capabilities response payload"):
        JsonLineParityTransport(_ScriptedLineIO(response)).capabilities()


def test_host_rejects_byte_canonical_parity_response_with_noncanonical_types() -> None:
    request = _request()
    response = ReferenceLoopbackTransport().exchange(request)
    payload = response.as_dict()
    payload["sequence"] = "0"
    frame = encode_wire_frame(
        ParityWireEnvelope(
            kind=WireKind.PARITY_RESPONSE,
            correlation_id=parity_request_correlation(request),
            payload=payload,
        )
    )

    transport = JsonLineParityTransport(_ScriptedLineIO(frame))
    with pytest.raises(ParityWireError, match="parity response payload"):
        transport.exchange(request)


def test_host_rejects_omitted_canonical_default_response_fields() -> None:
    request = _request()
    response = ReferenceLoopbackTransport().exchange(request)
    payload = response.as_dict()
    del payload["detail"]
    frame = encode_wire_frame(
        ParityWireEnvelope(
            kind=WireKind.PARITY_RESPONSE,
            correlation_id=parity_request_correlation(request),
            payload=payload,
        )
    )

    transport = JsonLineParityTransport(_ScriptedLineIO(frame))
    with pytest.raises(ParityWireError, match="parity response payload"):
        transport.exchange(request)


class _TelemetryTarget:
    def capabilities(self) -> ParityCapabilities:
        return ParityCapabilities(
            target_id="bench.telemetry",
            operations=(ParityOperation.REGISTER_LOAD,),
            max_width=3,
            telemetry_keys=(
                "board_revision",
                "comparator_code",
                "sample_count",
                "settle_us",
                "temperature_millic",
                "voltage_uv",
            ),
        )

    def exchange(self, request: ParityRequest) -> ParityResponse:
        telemetry = BenchTelemetry(
            voltage_uv=2_750_000,
            settle_us=43,
            comparator_code="11",
            sample_count=16,
            board_revision="TRIT-REV0",
            temperature_millic=23_125,
        )
        return ParityResponse(
            session_id=request.session_id,
            sequence=request.sequence,
            vector_id=request.vector.vector_id,
            status=ParityStatus.OK,
            observed_value=request.vector.expected_value,
            observed_state_digest=request.vector.expected_state_digest,
            telemetry=telemetry.as_pairs(),
        )


def test_bench_telemetry_convention_round_trips_without_affecting_result() -> None:
    telemetry = BenchTelemetry(
        voltage_uv=550_000,
        settle_us=31,
        comparator_code="00",
        sample_count=8,
        board_revision="TRIT-REV0",
        temperature_millic=-5_500,
    )
    assert BenchTelemetry.from_pairs(telemetry.as_pairs()) == telemetry

    transport = _wire_transport(_TelemetryTarget())
    response = transport.exchange(_request())
    assert response.status is ParityStatus.OK
    restored = BenchTelemetry.from_pairs(response.telemetry)
    assert restored.voltage_uv == 2_750_000
    assert restored.comparator_code == "11"
    assert restored.board_revision == "TRIT-REV0"


def test_bench_telemetry_rejects_unknown_or_invalid_fields() -> None:
    with pytest.raises(ParityWireError, match="unknown bench telemetry"):
        BenchTelemetry.from_pairs((("mystery", 1),))
    with pytest.raises(ParityWireError, match="sample_count must be positive"):
        BenchTelemetry(sample_count=0)
    with pytest.raises(ParityWireError, match="voltage_uv must be nonnegative"):
        BenchTelemetry(voltage_uv=-1)


def test_trace_campaign_runs_end_to_end_through_wire_codec() -> None:
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
    campaign = build_parity_campaign(trace_program(program))
    transport = _wire_transport()
    run = run_parity_campaign(transport, campaign)

    assert run.report.passed
    assert run.report.passed_count == len(campaign.entries)
    assert run.report.capabilities.target_id == "wire.loopback"
