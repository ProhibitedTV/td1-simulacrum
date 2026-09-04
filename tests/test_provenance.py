import pytest

from td1_simulacrum.provenance import EvidenceStatus, RequirementTrace, SourceRecord


def test_source_record_and_requirement_trace() -> None:
    source = SourceRecord(
        source_id="VB-025",
        corpus_revision="VB-TD1-001",
        summary="Participant reported layered geometric structures.",
        interpretation="Possible depth/context motif.",
    )
    assert source.source_id == "VB-025"

    trace = RequirementTrace(
        requirement_id="UI-DEPTH-001",
        motif="DEPTH",
        source_ids=(source.source_id,),
        implementation="multi-plane deterministic renderer",
        validation_method="state/render regression + sober usability testing",
        status=EvidenceStatus.REPORTED,
    )
    assert trace.as_dict()["status"] == "reported"


def test_requirement_trace_requires_sources() -> None:
    with pytest.raises(ValueError):
        RequirementTrace(
            requirement_id="UI-X",
            motif="DEPTH",
            source_ids=(),
            implementation="renderer",
            validation_method="test",
        )
