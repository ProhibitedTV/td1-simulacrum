"""Replayable execution-to-geometry timelines for TD-1 Relic Mode.

This layer joins already-normative execution, render-state, geometry, delta, and
SVG contracts. It records discrete truth-bearing frames only. Animation timing,
easing, interpolation, camera motion, and audio remain presentation concerns.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .geometry import GeometryProfile, GeometryScene, build_geometry_scene
from .machine import Instruction, Machine
from .observer import ObserverState
from .render_state import RenderState
from .semantic import StateWeave
from .svg_renderer import SVGRenderArtifact, SVGRenderOptions, render_svg
from .trace import ExecutionTrace, GeometryDelta, diff_geometry, trace_program

TIMELINE_SCHEMA = "td1.relic-timeline"
TIMELINE_SCHEMA_VERSION = 1
TIMELINE_SVG_MANIFEST_SCHEMA = "td1.timeline-svg-manifest"
TIMELINE_SVG_MANIFEST_VERSION = 1


class TimelineError(ValueError):
    """Raised when a TD-1 Relic timeline is inconsistent or cannot be replayed."""


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class TimelineFrame:
    """One exact render/geometry state in a discrete execution timeline."""

    frame_index: int
    render_state: RenderState
    scene: GeometryScene
    event_index: int | None = None
    instruction_index: int | None = None
    op: str | None = None
    delta_from_previous: GeometryDelta | None = None

    def __post_init__(self) -> None:
        if self.frame_index < 0:
            raise TimelineError("timeline frame index must be nonnegative")
        if self.scene.source_machine_digest != self.render_state.machine_digest:
            raise TimelineError("timeline scene machine digest disagrees with render state")
        if self.scene.source_render_digest != self.render_state.digest():
            raise TimelineError("timeline scene render digest disagrees with render state")

        rebuilt = build_geometry_scene(self.render_state, profile=self.scene.profile)
        if rebuilt.canonical_json() != self.scene.canonical_json():
            raise TimelineError("timeline scene is not the deterministic projection of render state")

        if self.frame_index == 0:
            if any(
                item is not None
                for item in (
                    self.event_index,
                    self.instruction_index,
                    self.op,
                    self.delta_from_previous,
                )
            ):
                raise TimelineError("initial timeline frame must not claim an execution event")
        else:
            if self.event_index is None or self.instruction_index is None or self.op is None:
                raise TimelineError("noninitial timeline frame requires execution-event identity")
            if self.delta_from_previous is None:
                raise TimelineError("noninitial timeline frame requires geometry delta")

    @property
    def machine_digest(self) -> str:
        return self.render_state.machine_digest

    @property
    def render_digest(self) -> str:
        return self.render_state.digest()

    @property
    def scene_digest(self) -> str:
        return self.scene.digest()

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "frame_index": self.frame_index,
            "machine_digest": self.machine_digest,
            "render_digest": self.render_digest,
            "scene_digest": self.scene_digest,
            "render_state": self.render_state.as_dict(),
            "scene": self.scene.as_dict(),
        }
        if self.event_index is not None:
            payload["event_index"] = self.event_index
            payload["instruction_index"] = self.instruction_index
            payload["op"] = self.op
        if self.delta_from_previous is not None:
            payload["delta_from_previous"] = self.delta_from_previous.as_dict()
            payload["delta_digest"] = self.delta_from_previous.digest()
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "TimelineFrame":
        render_payload = payload.get("render_state")
        scene_payload = payload.get("scene")
        delta_payload = payload.get("delta_from_previous")
        if not isinstance(render_payload, dict) or not isinstance(scene_payload, Mapping):
            raise TimelineError("timeline frame render_state/scene must be objects")

        render_state = RenderState.from_dict(render_payload)
        scene = GeometryScene.from_dict(scene_payload)
        delta = (
            GeometryDelta.from_dict(delta_payload)
            if isinstance(delta_payload, Mapping)
            else None
        )
        frame = cls(
            frame_index=int(payload["frame_index"]),
            render_state=render_state,
            scene=scene,
            event_index=(
                int(payload["event_index"])
                if payload.get("event_index") is not None
                else None
            ),
            instruction_index=(
                int(payload["instruction_index"])
                if payload.get("instruction_index") is not None
                else None
            ),
            op=str(payload["op"]) if payload.get("op") is not None else None,
            delta_from_previous=delta,
        )
        claims = {
            "machine_digest": frame.machine_digest,
            "render_digest": frame.render_digest,
            "scene_digest": frame.scene_digest,
        }
        for key, actual in claims.items():
            claimed = payload.get(key)
            if claimed is not None and str(claimed) != actual:
                raise TimelineError(f"timeline frame {key} mismatch")
        claimed_delta = payload.get("delta_digest")
        if claimed_delta is not None:
            if delta is None or str(claimed_delta) != delta.digest():
                raise TimelineError("timeline frame delta digest mismatch")
        return frame


@dataclass(frozen=True, slots=True)
class RelicTimeline:
    """Versioned sequence joining execution events to exact native geometry."""

    program_digest: str
    execution_trace_digest: str
    frames: tuple[TimelineFrame, ...]
    schema: str = TIMELINE_SCHEMA
    version: int = TIMELINE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != TIMELINE_SCHEMA or self.version != TIMELINE_SCHEMA_VERSION:
            raise TimelineError("unsupported Relic timeline schema")
        if len(self.program_digest) != 64 or len(self.execution_trace_digest) != 64:
            raise TimelineError("timeline program/trace digests must be SHA-256 hex strings")
        if not self.frames:
            raise TimelineError("Relic timeline requires at least the initial frame")
        if tuple(frame.frame_index for frame in self.frames) != tuple(range(len(self.frames))):
            raise TimelineError("timeline frame indices must be contiguous from zero")

        profile_digests = {
            frame.scene.profile.digest() if frame.scene.profile is not None else None
            for frame in self.frames
        }
        if len(profile_digests) != 1:
            raise TimelineError("timeline geometry profile must remain stable across all frames")

        for expected_event, frame in enumerate(self.frames[1:]):
            if frame.event_index != expected_event:
                raise TimelineError("timeline event indices must map one-to-one after frame zero")
            previous = self.frames[expected_event]
            expected_delta = diff_geometry(previous.scene, frame.scene)
            if frame.delta_from_previous is None:
                raise TimelineError("noninitial timeline frame is missing geometry delta")
            if frame.delta_from_previous.canonical_json() != expected_delta.canonical_json():
                raise TimelineError("timeline geometry delta disagrees with adjacent scenes")

    @property
    def event_count(self) -> int:
        return len(self.frames) - 1

    @property
    def final_machine_digest(self) -> str:
        return self.frames[-1].machine_digest

    def as_dict(self) -> dict[str, object]:
        profile = self.frames[0].scene.profile
        payload: dict[str, object] = {
            "schema": self.schema,
            "version": self.version,
            "program_digest": self.program_digest,
            "execution_trace_digest": self.execution_trace_digest,
            "frame_count": len(self.frames),
            "event_count": self.event_count,
            "initial_machine_digest": self.frames[0].machine_digest,
            "final_machine_digest": self.final_machine_digest,
            "frames": [frame.as_dict() for frame in self.frames],
        }
        if profile is not None:
            payload["profile_digest"] = profile.digest()
            payload["corpus_snapshot_id"] = profile.snapshot_id
            payload["corpus_snapshot_digest"] = profile.snapshot_digest
        return payload

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256(self.canonical_json())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "RelicTimeline":
        raw_frames = payload.get("frames")
        if not isinstance(raw_frames, list):
            raise TimelineError("timeline frames must be a list")
        timeline = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            program_digest=str(payload["program_digest"]),
            execution_trace_digest=str(payload["execution_trace_digest"]),
            frames=tuple(TimelineFrame.from_dict(item) for item in raw_frames),
        )
        claimed_counts = {
            "frame_count": len(timeline.frames),
            "event_count": timeline.event_count,
        }
        for key, actual in claimed_counts.items():
            claimed = payload.get(key)
            if claimed is not None and int(claimed) != actual:
                raise TimelineError(f"timeline {key} mismatch")
        claimed_initial = payload.get("initial_machine_digest")
        if claimed_initial is not None and str(claimed_initial) != timeline.frames[0].machine_digest:
            raise TimelineError("timeline initial machine digest mismatch")
        claimed_final = payload.get("final_machine_digest")
        if claimed_final is not None and str(claimed_final) != timeline.final_machine_digest:
            raise TimelineError("timeline final machine digest mismatch")

        profile = timeline.frames[0].scene.profile
        claimed_profile = payload.get("profile_digest")
        if claimed_profile is not None:
            if profile is None or str(claimed_profile) != profile.digest():
                raise TimelineError("timeline profile digest mismatch")
        return timeline

    @classmethod
    def from_json(cls, text: str) -> "RelicTimeline":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise TimelineError("timeline JSON root must be an object")
        return cls.from_dict(payload)


def build_relic_timeline(
    program: Sequence[Instruction],
    *,
    initial_machine: Machine | None = None,
    profile: GeometryProfile | None = None,
    weave: StateWeave | None = None,
    observer: ObserverState | None = None,
    max_steps: int = 100_000,
) -> RelicTimeline:
    """Replay the normative execution trace into exact render/geometry frames."""
    trace: ExecutionTrace = trace_program(
        program,
        initial_machine=initial_machine,
        max_steps=max_steps,
    )
    machine = trace.initial_state.restore_machine()

    initial_render = RenderState.capture(machine, weave=weave, observer=observer)
    initial_scene = build_geometry_scene(initial_render, profile=profile)
    frames: list[TimelineFrame] = [
        TimelineFrame(
            frame_index=0,
            render_state=initial_render,
            scene=initial_scene,
        )
    ]

    for event in trace.events:
        if machine.ip != event.instruction_index:
            raise TimelineError("trace replay instruction pointer diverged before frame capture")
        machine.step(program)
        actual_digest = machine.state_digest(include_memory=True)
        if actual_digest != event.after_digest:
            raise TimelineError("trace replay machine digest diverged during timeline construction")

        render_state = RenderState.capture(machine, weave=weave, observer=observer)
        scene = build_geometry_scene(render_state, profile=profile)
        previous_scene = frames[-1].scene
        frames.append(
            TimelineFrame(
                frame_index=len(frames),
                event_index=event.event_index,
                instruction_index=event.instruction_index,
                op=event.op,
                render_state=render_state,
                scene=scene,
                delta_from_previous=diff_geometry(previous_scene, scene),
            )
        )

    if machine.state_digest(include_memory=True) != trace.final_state.machine_digest:
        raise TimelineError("timeline replay did not reach the trace final machine state")

    return RelicTimeline(
        program_digest=trace.program_digest,
        execution_trace_digest=trace.digest(),
        frames=tuple(frames),
    )


@dataclass(frozen=True, slots=True)
class TimelineSVGEntry:
    frame_index: int
    filename: str
    scene_digest: str
    svg_digest: str
    metadata_digest: str

    def as_dict(self) -> dict[str, object]:
        return {
            "frame_index": self.frame_index,
            "filename": self.filename,
            "scene_digest": self.scene_digest,
            "svg_digest": self.svg_digest,
            "metadata_digest": self.metadata_digest,
        }


@dataclass(frozen=True, slots=True)
class TimelineSVGManifest:
    timeline_digest: str
    renderer_options: SVGRenderOptions
    entries: tuple[TimelineSVGEntry, ...]
    schema: str = TIMELINE_SVG_MANIFEST_SCHEMA
    version: int = TIMELINE_SVG_MANIFEST_VERSION

    def __post_init__(self) -> None:
        if self.schema != TIMELINE_SVG_MANIFEST_SCHEMA:
            raise TimelineError("unsupported timeline SVG manifest schema")
        if self.version != TIMELINE_SVG_MANIFEST_VERSION:
            raise TimelineError("unsupported timeline SVG manifest version")
        if tuple(entry.frame_index for entry in self.entries) != tuple(range(len(self.entries))):
            raise TimelineError("timeline SVG manifest entries must be contiguous")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "timeline_digest": self.timeline_digest,
            "renderer_options": self.renderer_options.as_dict(),
            "frame_count": len(self.entries),
            "entries": [entry.as_dict() for entry in self.entries],
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256(self.canonical_json())


def render_timeline_svgs(
    timeline: RelicTimeline,
    options: SVGRenderOptions | None = None,
) -> tuple[TimelineSVGManifest, tuple[SVGRenderArtifact, ...]]:
    """Render every exact timeline frame as deterministic SVG plus one manifest."""
    options = options or SVGRenderOptions()
    artifacts = tuple(render_svg(frame.scene, options) for frame in timeline.frames)
    entries = tuple(
        TimelineSVGEntry(
            frame_index=frame.frame_index,
            filename=f"frame-{frame.frame_index:04d}.svg",
            scene_digest=artifact.scene_digest,
            svg_digest=artifact.digest(),
            metadata_digest=artifact.metadata_digest,
        )
        for frame, artifact in zip(timeline.frames, artifacts, strict=True)
    )
    return (
        TimelineSVGManifest(
            timeline_digest=timeline.digest(),
            renderer_options=options,
            entries=entries,
        ),
        artifacts,
    )
