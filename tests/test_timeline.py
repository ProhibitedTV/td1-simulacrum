import json
from pathlib import Path

import pytest

from td1_simulacrum import (
    CorpusSnapshot,
    GeometryProfile,
    RelicTimeline,
    StateWeave,
    SVGRenderOptions,
    SVGTheme,
    TimelineError,
    assemble,
    build_relic_timeline,
    diff_geometry,
    render_timeline_svgs,
)

PROGRAM = """
LDI R0, 3
LDI R1, 0
loop:
ADD R1, R0
ADDI R0, -1
LDI R2, 0
CMP R0, R2
BRP loop
ST R1, R2, 7
HALT
"""


def _timeline() -> RelicTimeline:
    return build_relic_timeline(assemble(PROGRAM))


def test_timeline_has_initial_frame_plus_one_frame_per_real_event() -> None:
    timeline = _timeline()
    assert len(timeline.frames) == timeline.event_count + 1
    assert timeline.frames[0].event_index is None
    assert timeline.frames[-1].render_state.halted
    assert timeline.frames[-1].machine_digest == timeline.final_machine_digest
    assert [frame.event_index for frame in timeline.frames[1:]] == list(
        range(timeline.event_count)
    )


def test_every_timeline_delta_is_recomputed_from_adjacent_scenes() -> None:
    timeline = _timeline()
    for before, after in zip(timeline.frames, timeline.frames[1:], strict=False):
        expected = diff_geometry(before.scene, after.scene)
        assert after.delta_from_previous is not None
        assert after.delta_from_previous.canonical_json() == expected.canonical_json()


def test_timeline_round_trip_and_digest_are_deterministic() -> None:
    first = _timeline()
    second = _timeline()
    assert first.canonical_json() == second.canonical_json()
    assert first.digest() == second.digest()

    restored = RelicTimeline.from_json(first.canonical_json())
    assert restored == first
    assert restored.digest() == first.digest()


def test_timeline_rejects_claimed_digest_and_delta_tampering() -> None:
    timeline = _timeline()

    digest_payload = json.loads(timeline.canonical_json())
    digest_payload["frames"][0]["render_digest"] = "0" * 64
    with pytest.raises(TimelineError):
        RelicTimeline.from_dict(digest_payload)

    delta_payload = json.loads(timeline.canonical_json())
    delta_payload["frames"][1]["delta_from_previous"]["after_scene_digest"] = "f" * 64
    with pytest.raises(TimelineError):
        RelicTimeline.from_dict(delta_payload)


def test_profile_and_weave_persist_across_all_frames() -> None:
    fixture = Path(__file__).parent / "fixtures" / "corpus_snapshot_v1.json"
    snapshot = CorpusSnapshot.from_json(fixture.read_text(encoding="utf-8"))
    profile = GeometryProfile.from_snapshot(snapshot)
    weave = StateWeave.parse("TIME>REFERENCE:+")

    timeline = build_relic_timeline(
        assemble(PROGRAM),
        profile=profile,
        weave=weave,
    )
    assert all(frame.scene.profile == profile for frame in timeline.frames)
    assert all(frame.render_state.weave == weave for frame in timeline.frames)
    assert timeline.as_dict()["profile_digest"] == profile.digest()


def test_svg_timeline_manifest_is_stable_and_covers_every_frame() -> None:
    timeline = _timeline()
    options = SVGRenderOptions(theme=SVGTheme.RELIC, show_labels=False)
    first_manifest, first_artifacts = render_timeline_svgs(timeline, options)
    second_manifest, second_artifacts = render_timeline_svgs(timeline, options)

    assert first_manifest.canonical_json() == second_manifest.canonical_json()
    assert first_manifest.digest() == second_manifest.digest()
    assert len(first_manifest.entries) == len(timeline.frames)
    assert len(first_artifacts) == len(timeline.frames)
    assert [entry.filename for entry in first_manifest.entries] == [
        f"frame-{index:04d}.svg" for index in range(len(timeline.frames))
    ]
    assert [artifact.digest() for artifact in first_artifacts] == [
        artifact.digest() for artifact in second_artifacts
    ]
    for frame, entry, artifact in zip(
        timeline.frames,
        first_manifest.entries,
        first_artifacts,
        strict=True,
    ):
        assert entry.scene_digest == frame.scene_digest
        assert entry.svg_digest == artifact.digest()