import json

import pytest

from td1_simulacrum import ReferenceLoopbackTransport, TernaryWord, assemble, trace_program
from td1_simulacrum.campaign import (
    ParityCampaign,
    ParityCampaignError,
    ParityCampaignRun,
    build_parity_campaign,
    run_parity_campaign,
)
from td1_simulacrum.parity import ParityOperation

PROGRAM = assemble(
    """
LDI R0, 2
LDI R1, 3
MOV R2, R0
ADD R2, R1
ADDI R2, -1
NEG R2
SUB R1, R0
ST R1, R0, 10
LD R3, R0, 10
CMP R3, R1
NOP
HALT
"""
)


def _campaign() -> ParityCampaign:
    return build_parity_campaign(trace_program(PROGRAM))


def test_campaign_derives_supported_subsystem_vectors_from_real_trace() -> None:
    campaign = _campaign()
    operations = tuple(entry.vector.operation for entry in campaign.entries)
    logical_ops = tuple(entry.logical_op for entry in campaign.entries)

    assert logical_ops == ("LDI", "LDI", "MOV", "ADD", "ADDI", "NEG", "SUB", "LD")
    assert operations == (
        ParityOperation.REGISTER_LOAD,
        ParityOperation.REGISTER_LOAD,
        ParityOperation.REGISTER_LOAD,
        ParityOperation.ADD,
        ParityOperation.ADD,
        ParityOperation.NEGATE,
        ParityOperation.SUB,
        ParityOperation.REGISTER_LOAD,
    )
    assert all(entry.logical_op not in {"ST", "CMP", "NOP", "HALT"} for entry in campaign.entries)
    assert campaign.initial_checkpoint.machine_digest == campaign.trace.initial_state.machine_digest
    assert campaign.final_checkpoint.machine_digest == campaign.trace.final_state.machine_digest


def test_addi_is_explicitly_mapped_to_subsystem_add_without_decode_claim() -> None:
    campaign = _campaign()
    entry = next(item for item in campaign.entries if item.logical_op == "ADDI")

    assert entry.vector.operation is ParityOperation.ADD
    assert entry.vector.operands[1] == str(TernaryWord.from_int(-1, 12))
    assert "does not test instruction decoding" in entry.rationale
    assert entry.vector.expected_value == str(TernaryWord.from_int(4, 12))


def test_campaign_is_deterministic_and_round_trips_with_exact_derivation() -> None:
    first = _campaign()
    second = _campaign()

    assert first.canonical_json() == second.canonical_json()
    assert first.digest() == second.digest()
    assert first.vector_set_digest == second.vector_set_digest

    restored = ParityCampaign.from_json(first.canonical_json())
    assert restored == first


def test_campaign_rejects_entry_trace_and_checkpoint_tampering() -> None:
    campaign = _campaign()

    entry_payload = json.loads(campaign.canonical_json())
    entry_payload["entries"][0]["mapping"] = "ALIEN-OVERRIDE"
    with pytest.raises(ParityCampaignError, match="entries disagree"):
        ParityCampaign.from_dict(entry_payload)

    trace_payload = json.loads(campaign.canonical_json())
    delta = trace_payload["trace"]["events"][1]["register_deltas"][0]
    delta["before"] = "+" * 12
    with pytest.raises(ParityCampaignError, match="before-value disagrees"):
        ParityCampaign.from_dict(trace_payload)

    checkpoint_payload = json.loads(campaign.canonical_json())
    checkpoint_payload["initial_checkpoint"] = checkpoint_payload["final_checkpoint"]
    checkpoint_payload["initial_checkpoint_digest"] = checkpoint_payload[
        "final_checkpoint_digest"
    ]
    with pytest.raises(ParityCampaignError, match="initial checkpoint disagrees"):
        ParityCampaign.from_dict(checkpoint_payload)


def test_repeated_execution_path_keeps_event_unique_vector_identity() -> None:
    program = assemble(
        """
LDI R0, 2
LDI R1, 0
loop:
ADD R1, R0
ADDI R0, -1
LDI R2, 0
CMP R0, R2
BRP loop
HALT
"""
    )
    campaign = build_parity_campaign(trace_program(program))
    ids = [entry.vector.vector_id for entry in campaign.entries]
    add_entries = [entry for entry in campaign.entries if entry.logical_op == "ADD"]

    assert len(ids) == len(set(ids))
    assert len(add_entries) == 2
    assert add_entries[0].event_index != add_entries[1].event_index


def test_campaign_run_links_report_and_passes_reference_loopback() -> None:
    campaign = _campaign()
    run = run_parity_campaign(ReferenceLoopbackTransport(max_width=12), campaign)

    assert run.report.passed
    assert run.report.passed_count == len(campaign.entries)
    assert run.report.vector_set_digest == campaign.vector_set_digest

    restored = ParityCampaignRun.from_json(run.canonical_json())
    assert restored == run


def test_campaign_run_preserves_capability_rejection_as_failure() -> None:
    campaign = _campaign()
    run = run_parity_campaign(ReferenceLoopbackTransport(max_width=3), campaign)

    assert not run.report.passed
    assert run.report.failed_count == len(campaign.entries)
    assert all(
        record.response.status.value == "unsupported" for record in run.report.records
    )


def test_empty_trace_mapping_is_valid_but_not_runnable() -> None:
    campaign = build_parity_campaign(trace_program(assemble("HALT")))
    assert campaign.entries == ()

    with pytest.raises(ParityCampaignError, match="no derived vectors"):
        run_parity_campaign(ReferenceLoopbackTransport(), campaign)
