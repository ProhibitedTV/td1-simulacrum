import json
from pathlib import Path

import pytest

from td1_simulacrum import (
    AnnotationMethod,
    CorpusSnapshot,
    GeometryKind,
    GeometryProfile,
    GeometryScene,
    LatticePoint,
    Machine,
    Modifier,
    Motif,
    MotifAnnotation,
    RenderState,
    SemanticRoot,
    SourceRecord,
    StateWeave,
    build_geometry_scene,
    glyph_id_from_geometry,
    microglyph_geometry,
)

CORPUS_FIXTURE = Path(__file__).parent / "fixtures" / "corpus_snapshot_v1.json"
GLYPH_FIXTURE = Path(__file__).parent / "fixtures" / "glyph_geometry_v1.json"


def _load_profile() -> GeometryProfile:
    snapshot = CorpusSnapshot.from_json(CORPUS_FIXTURE.read_text(encoding="utf-8"))
    return GeometryProfile.from_snapshot(snapshot)


def test_all_27_microglyph_topologies_are_unique_and_reversible() -> None:
    signatures: set[str] = set()
    for glyph_id in range(27):
        geometry = microglyph_geometry(glyph_id)
        assert glyph_id_from_geometry(geometry) == glyph_id
        signature = json.dumps(
            [primitive.as_dict() for primitive in geometry],
            sort_keys=True,
            separators=(",", ":"),
        )
        signatures.add(signature)
    assert len(signatures) == 27


def test_microglyph_geometry_matches_golden_fixture() -> None:
    expected = json.loads(GLYPH_FIXTURE.read_text(encoding="utf-8"))
    actual = [primitive.as_dict() for primitive in microglyph_geometry(26)]
    assert actual == expected


def test_geometry_profile_uses_only_admitted_corpus_annotations() -> None:
    profile = _load_profile()

    assert profile.snapshot_id == "VB-TD1-001"
    assert profile.supports_motif(Motif.DEPTH)
    assert profile.supports_motif(Motif.MICROGLYPH)
    assert profile.supports_motif(Motif.LATTICE)
    assert not profile.supports_motif(Motif.BRAIDING)
    assert profile.evidence(Motif.DEPTH).source_ids == ("VB-SYN-001",)  # type: ignore[union-attr]


def test_geometry_scene_is_deterministic_and_round_trippable() -> None:
    machine = Machine()
    state = RenderState.capture(machine)
    profile = _load_profile()

    first = build_geometry_scene(state, profile=profile)
    second = build_geometry_scene(state, profile=profile)
    restored = GeometryScene.from_json(first.canonical_json())

    assert first.digest() == second.digest()
    assert restored == first
    assert restored.canonical_json() == first.canonical_json()
    assert first.source_render_digest == state.digest()
    assert first.source_machine_digest == machine.state_digest()
    assert {rule.rule_id for rule in first.applied_rules} == {
        "VB-GEO-DEPTH-001",
        "VB-GEO-LATTICE-001",
    }


def test_corpus_profile_changes_layout_only_through_explicit_rules() -> None:
    state = RenderState.capture(Machine())
    fallback = build_geometry_scene(state)
    profiled = build_geometry_scene(state, profile=_load_profile())

    fallback_r3 = next(
        primitive
        for primitive in fallback.primitives
        if primitive.primitive_id == "machine.r3.anchor"
    )
    profiled_r3 = next(
        primitive
        for primitive in profiled.primitives
        if primitive.primitive_id == "machine.r3.anchor"
    )

    assert fallback.applied_rules == ()
    assert fallback_r3.points == (LatticePoint(84, 0, 0),)
    assert profiled_r3.points == (LatticePoint(-14, 28, 100),)


def test_braiding_and_multiscale_require_matching_snapshot_evidence() -> None:
    snapshot_id = "VB-TD1-999"
    source = SourceRecord(
        source_id="VB-SYN-BRAID",
        corpus_revision=snapshot_id,
        summary="Synthetic report used only to exercise geometry rule admission.",
    )
    snapshot = CorpusSnapshot(
        snapshot_id=snapshot_id,
        created_at_utc="2026-09-04T16:30:00+00:00",
        source_schema="veilbreak.synthetic/v1",
        records=(source,),
        annotations=(
            MotifAnnotation(
                source.source_id,
                Motif.BRAIDING,
                AnnotationMethod.MANUAL,
                1000,
            ),
            MotifAnnotation(
                source.source_id,
                Motif.MULTISCALE,
                AnnotationMethod.MANUAL,
                1000,
            ),
        ),
    )
    profile = GeometryProfile.from_snapshot(snapshot)
    weave = StateWeave(
        (SemanticRoot.TIME, SemanticRoot.REFERENCE, SemanticRoot.MOTION),
        Modifier.POSITIVE,
    )
    state = RenderState.capture(Machine(), weave=weave)
    scene = build_geometry_scene(state, profile=profile)

    link = next(
        primitive for primitive in scene.primitives if primitive.primitive_id == "semantic.link0"
    )
    root_spoke = next(
        primitive
        for primitive in scene.primitives
        if primitive.primitive_id.startswith("semantic.root0.trit")
    )

    assert link.kind is GeometryKind.POLYLINE
    assert link.points[1].z == 8
    assert root_spoke.scale_milli == 3000
    assert {rule.motif for rule in scene.applied_rules} == {
        Motif.BRAIDING,
        Motif.MULTISCALE,
    }


def test_corrupt_geometry_profile_digest_is_rejected() -> None:
    scene = build_geometry_scene(RenderState.capture(Machine()), profile=_load_profile())
    payload = scene.as_dict()
    payload["profile_digest"] = "0" * 64

    with pytest.raises(ValueError, match="profile digest mismatch"):
        GeometryScene.from_dict(payload)


def test_decoder_rejects_spoke_on_wrong_axis() -> None:
    geometry = list(microglyph_geometry(26))
    spoke = geometry[1]
    geometry[1] = type(spoke)(
        primitive_id=spoke.primitive_id,
        kind=spoke.kind,
        role=spoke.role,
        points=(spoke.points[0], spoke.points[0].offset(0, 2)),
        glyph_id=spoke.glyph_id,
    )

    with pytest.raises(ValueError, match="not aligned"):
        glyph_id_from_geometry(geometry)
