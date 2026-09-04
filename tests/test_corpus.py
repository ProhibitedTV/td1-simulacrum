import json
from pathlib import Path

import pytest

from td1_simulacrum import (
    AnnotationMethod,
    CorpusError,
    CorpusSnapshot,
    EvidenceStatus,
    Motif,
    MotifAnnotation,
    RequirementTrace,
    SourceRecord,
    VeilbreakExportAdapter,
    VeilbreakFieldMap,
    compare_snapshots,
    export_requirement_traces,
)

SNAPSHOT_FIXTURE = Path(__file__).parent / "fixtures" / "corpus_snapshot_v1.json"
EXPORT_FIXTURE = Path(__file__).parent / "fixtures" / "veilbreak_export_synthetic.json"


def _snapshot_one() -> CorpusSnapshot:
    return CorpusSnapshot.from_json(SNAPSHOT_FIXTURE.read_text(encoding="utf-8"))


def test_golden_corpus_snapshot_v1_round_trip() -> None:
    snapshot = _snapshot_one()

    assert snapshot.snapshot_id == "VB-TD1-001"
    assert snapshot.digest() == "4b358b716d41fa24b12160c6f49f0964a8ba8616dc2752e1af471942d2261ef9"
    assert CorpusSnapshot.from_json(snapshot.canonical_json()) == snapshot
    assert snapshot.motif_counts() == {"depth": 1, "lattice": 1, "microglyph": 1}


def test_veilbreak_adapter_preserves_observation_and_interpretation() -> None:
    rows = json.loads(EXPORT_FIXTURE.read_text(encoding="utf-8"))
    snapshot = VeilbreakExportAdapter.ingest(
        rows,
        snapshot_id="VB-TD1-002",
        created_at_utc="2026-09-04T16:20:00+00:00",
        source_schema="veilbreak.synthetic/v1",
        fields=VeilbreakFieldMap(
            source_id="experiment_id",
            observation="observation",
            interpretation="interpretation",
        ),
        source_revision="synthetic-002",
    )

    first = snapshot.records[0]
    assert first.summary == "Layered tiny symbols appeared behind a foreground geometric structure."
    assert first.interpretation == (
        "Participant attributed the pattern to an external intelligence."
    )


def test_adapter_refuses_to_guess_missing_schema_fields() -> None:
    with pytest.raises(CorpusError, match="missing required Veilbreak export field"):
        VeilbreakExportAdapter.ingest(
            [{"id": "x", "text": "y"}],
            snapshot_id="VB-TD1-002",
            created_at_utc="2026-09-04T16:20:00+00:00",
            source_schema="unknown",
            fields=VeilbreakFieldMap(source_id="experiment_id", observation="observation"),
        )


def test_snapshot_rejects_annotation_for_unknown_source() -> None:
    with pytest.raises(CorpusError, match="unknown source"):
        CorpusSnapshot(
            snapshot_id="VB-TD1-002",
            created_at_utc="2026-09-04T16:20:00+00:00",
            source_schema="synthetic/v1",
            records=(
                SourceRecord("known", "VB-TD1-002", "Reported observation."),
            ),
            annotations=(
                MotifAnnotation(
                    "missing",
                    Motif.DEPTH,
                    AnnotationMethod.MANUAL,
                ),
            ),
        )


def test_snapshot_order_is_canonical_not_input_order() -> None:
    snapshot = CorpusSnapshot(
        snapshot_id="VB-TD1-002",
        created_at_utc="2026-09-04T16:20:00+00:00",
        source_schema="synthetic/v1",
        records=(
            SourceRecord("B", "VB-TD1-002", "Second."),
            SourceRecord("A", "VB-TD1-002", "First."),
        ),
        annotations=(
            MotifAnnotation("B", Motif.LATTICE, AnnotationMethod.MANUAL),
            MotifAnnotation("A", Motif.DEPTH, AnnotationMethod.MANUAL),
        ),
    )

    assert [record.source_id for record in snapshot.records] == ["A", "B"]
    assert [(item.source_id, item.motif.value) for item in snapshot.annotations] == [
        ("A", "depth"),
        ("B", "lattice"),
    ]


def test_corpus_delta_reports_source_and_motif_changes() -> None:
    before = _snapshot_one()
    after = CorpusSnapshot(
        snapshot_id="VB-TD1-002",
        created_at_utc="2026-09-04T16:30:00+00:00",
        source_schema="veilbreak.synthetic/v1",
        records=(
            SourceRecord(
                "VB-SYN-001",
                "VB-TD1-002",
                "Layered tiny symbols appeared behind a foreground geometric structure.",
            ),
            SourceRecord(
                "VB-SYN-003",
                "VB-TD1-002",
                "A braided structure appeared to combine two symbol groups.",
            ),
        ),
        annotations=(
            MotifAnnotation("VB-SYN-001", Motif.DEPTH, AnnotationMethod.MANUAL, 900),
            MotifAnnotation("VB-SYN-003", Motif.BRAIDING, AnnotationMethod.MANUAL),
        ),
    )

    delta = compare_snapshots(before, after).as_dict()

    assert delta["added_sources"] == ["VB-SYN-003"]
    assert delta["removed_sources"] == ["VB-SYN-002"]
    assert delta["motif_count_delta"] == {
        "braiding": 1,
        "lattice": -1,
        "microglyph": -1,
    }


def test_requirement_export_requires_source_motif_evidence() -> None:
    snapshot = _snapshot_one()
    requirement = RequirementTrace(
        requirement_id="UI-DEPTH-001",
        motif="depth",
        source_ids=("VB-SYN-001",),
        implementation="multi-plane render state",
        validation_method="deterministic projection test",
        status=EvidenceStatus.REPORTED,
    )

    graph = export_requirement_traces(snapshot, [requirement])

    assert graph["snapshot_id"] == "VB-TD1-001"
    assert graph["traces"][0]["requirement"]["requirement_id"] == "UI-DEPTH-001"


def test_requirement_export_rejects_unannotated_claim() -> None:
    snapshot = _snapshot_one()
    requirement = RequirementTrace(
        requirement_id="UI-BRAID-001",
        motif="braiding",
        source_ids=("VB-SYN-001",),
        implementation="state weave topology",
        validation_method="A/B usability",
    )

    with pytest.raises(CorpusError, match="lacks motif annotation"):
        export_requirement_traces(snapshot, [requirement])
