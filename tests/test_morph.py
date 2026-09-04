import json

import pytest

from td1_simulacrum import (
    GeometryKind,
    GeometryPrimitive,
    GeometryProfile,
    GeometryScene,
    LatticePoint,
    MorphError,
    MorphIntent,
    MorphStrategy,
    Motif,
    MotifSupport,
    StateWeave,
    assemble,
    build_morph_plan,
    build_relic_timeline,
    build_timeline_morph_manifest,
)


def _node(primitive_id: str, q: int, r: int, z: int = 0, *, role: str = "node"):
    return GeometryPrimitive(
        primitive_id=primitive_id,
        kind=GeometryKind.NODE,
        role=role,
        points=(LatticePoint(q, r, z),),
    )


def _segment(
    primitive_id: str,
    points: tuple[LatticePoint, LatticePoint],
    *,
    role: str = "segment",
):
    return GeometryPrimitive(
        primitive_id=primitive_id,
        kind=GeometryKind.SEGMENT,
        role=role,
        points=points,
    )


def _scene(*primitives: GeometryPrimitive, profile: GeometryProfile | None = None):
    return GeometryScene(
        source_render_digest="a" * 64,
        source_machine_digest="b" * 64,
        primitives=tuple(primitives),
        profile=profile,
    )


def _temporal_profile() -> GeometryProfile:
    motifs = (
        Motif.MORPHING,
        Motif.CONTEXT_PERSISTENCE,
        Motif.FOCUS_THROUGH,
        Motif.HORIZONTAL_MOTION,
        Motif.VERTICAL_MOTION,
    )
    return GeometryProfile(
        snapshot_id="VB-TD1-999",
        snapshot_digest="c" * 64,
        threshold_milli=750,
        supports=tuple(
            MotifSupport(
                motif=motif,
                source_ids=(f"VB-SYN-{index:03d}",),
                methods=("manual",),
                mean_confidence_milli=900,
            )
            for index, motif in enumerate(motifs, start=1)
        ),
    )


def _all_change_scenes(profile: GeometryProfile | None = None):
    before = _scene(
        _node("disappear", 0, 0),
        _node("move-h", 0, 2),
        _node("move-v", 2, 0),
        _node("move-z", 3, 3, 0),
        _segment("reform", (LatticePoint(0, 0), LatticePoint(2, 0))),
        _node("retag", 7, 7, role="old-role"),
        profile=profile,
    )
    after = _scene(
        _node("appear", 9, 9),
        _node("move-h", 5, 2),
        _node("move-v", 2, 6),
        _node("move-z", 3, 3, 4),
        _segment("reform", (LatticePoint(0, 0), LatticePoint(2, 2))),
        _node("retag", 7, 7, role="new-role"),
        profile=profile,
    )
    return before, after


def test_morph_plan_covers_all_geometry_change_kinds_with_conservative_fallbacks() -> None:
    before, after = _all_change_scenes()
    plan = build_morph_plan(before, after)
    by_id = {item.primitive_id: item for item in plan.descriptors}

    assert by_id["appear"].intent is MorphIntent.ENTER
    assert by_id["appear"].strategy is MorphStrategy.ENDPOINT_APPEAR
    assert by_id["disappear"].intent is MorphIntent.EXIT
    assert by_id["disappear"].strategy is MorphStrategy.ENDPOINT_DISAPPEAR
    assert by_id["move-h"].intent is MorphIntent.TRANSLATE
    assert by_id["move-h"].translation == (5, 0, 0)
    assert by_id["move-v"].translation == (0, 6, 0)
    assert by_id["move-z"].translation == (0, 0, 4)
    assert by_id["reform"].strategy is MorphStrategy.DISCRETE_REFORM
    assert by_id["retag"].intent is MorphIntent.RETAG
    assert by_id["retag"].strategy is MorphStrategy.METADATA_UPDATE
    assert plan.applied_rules == ()


def test_corpus_temporal_rules_are_admitted_with_exact_source_provenance() -> None:
    profile = _temporal_profile()
    before, after = _all_change_scenes(profile)
    plan = build_morph_plan(before, after)
    rules = {rule.rule_id: rule for rule in plan.applied_rules}
    by_id = {item.primitive_id: item for item in plan.descriptors}

    assert set(rules) == {
        "VB-MORPH-FOCUS-001",
        "VB-MORPH-HORIZONTAL-001",
        "VB-MORPH-PERSIST-001",
        "VB-MORPH-REFORM-001",
        "VB-MORPH-VERTICAL-001",
    }
    assert all(rule.source_ids for rule in rules.values())
    assert by_id["reform"].strategy is MorphStrategy.CONTINUOUS_REFORM_ELIGIBLE
    assert by_id["reform"].rule_ids == ("VB-MORPH-REFORM-001",)
    assert "context-persistence-eligible" in by_id["disappear"].hints
    assert "horizontal-motion-emphasis-eligible" in by_id["move-h"].hints
    assert "vertical-motion-emphasis-eligible" in by_id["move-v"].hints
    assert "focus-through-eligible" in by_id["move-z"].hints


def test_morph_plan_round_trip_is_deterministic_and_rejects_tampering() -> None:
    before, after = _all_change_scenes(_temporal_profile())
    first = build_morph_plan(before, after)
    second = build_morph_plan(before, after)
    assert first.canonical_json() == second.canonical_json()
    assert first.digest() == second.digest()

    from td1_simulacrum import MorphPlan

    restored = MorphPlan.from_json(first.canonical_json())
    assert restored == first

    payload = json.loads(first.canonical_json())
    payload["descriptors"][0]["strategy"] = "metadata_update"
    with pytest.raises(MorphError):
        MorphPlan.from_dict(payload)


def test_morph_plan_v1_rejects_geometry_profile_revision_changes() -> None:
    first_profile = _temporal_profile()
    second_profile = GeometryProfile(
        snapshot_id=first_profile.snapshot_id,
        snapshot_digest="d" * 64,
        threshold_milli=first_profile.threshold_milli,
        supports=first_profile.supports,
    )
    before, _ = _all_change_scenes(first_profile)
    _, after = _all_change_scenes(second_profile)
    with pytest.raises(MorphError):
        build_morph_plan(before, after)


def test_timeline_morph_manifest_has_one_plan_per_noninitial_frame() -> None:
    program = assemble(
        """
LDI R0, 2
ADDI R0, -1
HALT
"""
    )
    timeline = build_relic_timeline(
        program,
        weave=StateWeave.parse("TIME>REFERENCE:+"),
    )
    first = build_timeline_morph_manifest(timeline)
    second = build_timeline_morph_manifest(timeline)
    assert len(first.entries) == timeline.event_count
    assert [entry.frame_index for entry in first.entries] == list(
        range(1, len(timeline.frames))
    )
    assert first.timeline_digest == timeline.digest()
    assert first.canonical_json() == second.canonical_json()
    assert first.digest() == second.digest()
