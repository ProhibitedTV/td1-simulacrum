import json

import pytest

from td1_simulacrum import (
    ConformanceReport,
    ParityCapabilities,
    ParityError,
    ParityOperation,
    ParityStatus,
    ParityVector,
    ReferenceLoopbackTransport,
    golden_alu_vectors,
    golden_parity_vectors,
    golden_register_vectors,
    run_conformance,
    ternary_state_digest,
    vector_set_digest,
)


def test_register_campaign_starts_with_all_three_physical_trit_states() -> None:
    vectors = golden_register_vectors(3)
    assert tuple(vector.vector_id for vector in vectors[:3]) == (
        "TRIT-NEG",
        "TRIT-ZERO",
        "TRIT-POS",
    )
    assert tuple(vector.expected_value for vector in vectors[:3]) == ("-", "0", "+")
    assert all(vector.operation is ParityOperation.TRIT_HOLD for vector in vectors[:3])
    assert all(vector.width == 3 for vector in vectors[3:])


def test_alu_vectors_include_fixed_width_wrap_cases() -> None:
    vectors = {vector.vector_id: vector for vector in golden_alu_vectors(3)}
    assert vectors["ALU-ADD-WRAP"].operands == ("+++", "00+")
    assert vectors["ALU-ADD-WRAP"].expected_value == "---"
    assert vectors["ALU-SUB-WRAP"].operands == ("---", "00+")
    assert vectors["ALU-SUB-WRAP"].expected_value == "+++"


def test_reference_loopback_passes_complete_golden_set_deterministically() -> None:
    vectors = golden_parity_vectors(6)
    transport = ReferenceLoopbackTransport(max_width=6)
    first = run_conformance(transport, vectors)
    second = run_conformance(transport, vectors)

    assert first.passed
    assert first.failed_count == 0
    assert first.passed_count == len(vectors)
    assert first.session_id == second.session_id
    assert first.digest() == second.digest()
    assert first.vector_set_digest == vector_set_digest(vectors)


def test_report_round_trip_revalidates_requests_responses_and_summary() -> None:
    report = run_conformance(
        ReferenceLoopbackTransport(max_width=3),
        golden_register_vectors(3),
        session_id="TD1-TEST-SESSION",
    )
    restored = ConformanceReport.from_json(report.canonical_json())
    assert restored == report
    assert restored.digest() == report.digest()

    payload = json.loads(report.canonical_json())
    payload["summary"]["failed_count"] = 99
    with pytest.raises(ParityError):
        ConformanceReport.from_dict(payload)


def test_capability_negotiation_records_unsupported_vectors_without_exchange() -> None:
    vectors = golden_register_vectors(3)
    report = run_conformance(ReferenceLoopbackTransport(max_width=1), vectors)

    assert not report.passed
    assert report.passed_count == 3
    assert report.failed_count == len(vectors) - 3
    unsupported = [
        record for record in report.records if record.response.status is ParityStatus.UNSUPPORTED
    ]
    assert len(unsupported) == len(vectors) - 3
    assert all("capability negotiation" in record.response.detail for record in unsupported)


def test_fault_timeout_and_error_statuses_are_replayable_discrepancies() -> None:
    vectors = golden_register_vectors(1)
    forced = {
        "TRIT-NEG": ParityStatus.FAULT,
        "TRIT-ZERO": ParityStatus.TIMEOUT,
        "TRIT-POS": ParityStatus.ERROR,
    }
    report = run_conformance(
        ReferenceLoopbackTransport(max_width=1, forced_status=forced),
        vectors,
    )
    by_id = {record.request.vector.vector_id: record for record in report.records}

    assert by_id["TRIT-NEG"].discrepancy.startswith("transport status: fault")
    assert by_id["TRIT-ZERO"].discrepancy.startswith("transport status: timeout")
    assert by_id["TRIT-POS"].discrepancy.startswith("transport status: error")
    assert not report.passed


def test_observed_value_mismatch_is_distinct_from_transport_failure() -> None:
    vectors = (ParityVector.create("REG", ParityOperation.REGISTER_LOAD, 3, ("00+",)),)
    report = run_conformance(
        ReferenceLoopbackTransport(max_width=3, observed_overrides={"REG": "000"}),
        vectors,
    )
    record = report.records[0]
    assert record.response.status is ParityStatus.OK
    assert not record.passed
    assert record.discrepancy == "value mismatch: expected 00+, observed 000"


def test_vector_constructor_rejects_false_reference_expectation() -> None:
    with pytest.raises(ParityError):
        ParityVector(
            vector_id="BAD",
            operation=ParityOperation.NEGATE,
            width=3,
            operands=("00+",),
            expected_value="00+",
        )


def test_state_digest_is_width_sensitive_and_transport_independent() -> None:
    assert ternary_state_digest(1, "+") != ternary_state_digest(2, "0+")
    assert ternary_state_digest(3, "+0-") == ternary_state_digest(3, "+0-")


def test_capability_descriptor_is_canonicalized() -> None:
    capabilities = ParityCapabilities(
        target_id="fixture",
        operations=(ParityOperation.SUB, ParityOperation.ADD, ParityOperation.ADD),
        max_width=12,
        protocol_versions=(1, 1),
        telemetry_keys=("voltage_uv", "voltage_uv", "settle_us"),
    )
    assert capabilities.operations == (ParityOperation.ADD, ParityOperation.SUB)
    assert capabilities.protocol_versions == (1,)
    assert capabilities.telemetry_keys == ("settle_us", "voltage_uv")
