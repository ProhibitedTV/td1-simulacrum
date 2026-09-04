"""Deterministic presentation-intent plans for TD-1 geometry transitions.

Morph plans sit downstream of exact geometry deltas and upstream of animated
frontends. They constrain how a real change may be presented without defining
timing, easing, interpolation samples, or intermediate machine state.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from .corpus import Motif
from .geometry import GeometryPrimitive, GeometryProfile, GeometryScene
from .timeline import RelicTimeline
from .trace import GeometryDelta, PrimitiveChange, PrimitiveChangeKind, diff_geometry

MORPH_PLAN_SCHEMA = "td1.morph-plan"
MORPH_PLAN_SCHEMA_VERSION = 1
TIMELINE_MORPH_SCHEMA = "td1.timeline-morph-manifest"
TIMELINE_MORPH_SCHEMA_VERSION = 1


class MorphError(ValueError):
    """Raised when a transition-intent plan disagrees with its geometry endpoints."""


class MorphIntent(str, Enum):
    ENTER = "enter"
    EXIT = "exit"
    TRANSLATE = "translate"
    REFORM = "reform"
    RETAG = "retag"


class MorphStrategy(str, Enum):
    """Renderer-independent strategy labels with no temporal semantics."""

    ENDPOINT_APPEAR = "endpoint_appear"
    ENDPOINT_DISAPPEAR = "endpoint_disappear"
    ENDPOINT_TRANSLATION = "endpoint_translation"
    DISCRETE_REFORM = "discrete_reform"
    CONTINUOUS_REFORM_ELIGIBLE = "continuous_reform_eligible"
    METADATA_UPDATE = "metadata_update"


@dataclass(frozen=True, slots=True)
class AppliedMorphRule:
    """One corpus-admitted presentation hint with exact source provenance."""

    rule_id: str
    motif: Motif
    source_ids: tuple[str, ...]
    effect: str

    def __post_init__(self) -> None:
        if not self.rule_id.strip() or not self.effect.strip():
            raise MorphError("morph rule id/effect must not be empty")
        if not self.source_ids:
            raise MorphError("corpus-backed morph rule requires source IDs")
        object.__setattr__(self, "source_ids", tuple(sorted(set(self.source_ids))))

    def as_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "motif": self.motif.value,
            "source_ids": list(self.source_ids),
            "effect": self.effect,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "AppliedMorphRule":
        source_ids = payload.get("source_ids")
        if not isinstance(source_ids, list):
            raise MorphError("morph rule source_ids must be a list")
        return cls(
            rule_id=str(payload["rule_id"]),
            motif=Motif(str(payload["motif"])),
            source_ids=tuple(str(item) for item in source_ids),
            effect=str(payload["effect"]),
        )


@dataclass(frozen=True, slots=True)
class MorphDescriptor:
    """Presentation intent for one stable geometry primitive identity."""

    primitive_id: str
    change_kind: PrimitiveChangeKind
    intent: MorphIntent
    strategy: MorphStrategy
    before: GeometryPrimitive | None
    after: GeometryPrimitive | None
    translation: tuple[int, int, int] | None = None
    hints: tuple[str, ...] = ()
    rule_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.primitive_id.strip():
            raise MorphError("morph descriptor primitive_id must not be empty")
        object.__setattr__(self, "hints", tuple(sorted(set(self.hints))))
        object.__setattr__(self, "rule_ids", tuple(sorted(set(self.rule_ids))))
        if self.change_kind is PrimitiveChangeKind.MOVE:
            if self.translation is None or self.before is None or self.after is None:
                raise MorphError("move descriptor requires endpoints and translation")
        elif self.translation is not None:
            raise MorphError("only move descriptors may carry translation")

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "primitive_id": self.primitive_id,
            "change_kind": self.change_kind.value,
            "intent": self.intent.value,
            "strategy": self.strategy.value,
            "before": self.before.as_dict() if self.before is not None else None,
            "after": self.after.as_dict() if self.after is not None else None,
            "hints": list(self.hints),
            "rule_ids": list(self.rule_ids),
        }
        if self.translation is not None:
            payload["translation"] = list(self.translation)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "MorphDescriptor":
        before = payload.get("before")
        after = payload.get("after")
        translation = payload.get("translation")
        hints = payload.get("hints", [])
        rule_ids = payload.get("rule_ids", [])
        if not isinstance(hints, list) or not isinstance(rule_ids, list):
            raise MorphError("morph descriptor hints/rule_ids must be lists")
        if translation is not None and (
            not isinstance(translation, list) or len(translation) != 3
        ):
            raise MorphError("morph translation must be a three-integer list")
        return cls(
            primitive_id=str(payload["primitive_id"]),
            change_kind=PrimitiveChangeKind(str(payload["change_kind"])),
            intent=MorphIntent(str(payload["intent"])),
            strategy=MorphStrategy(str(payload["strategy"])),
            before=(
                GeometryPrimitive.from_dict(before)
                if isinstance(before, Mapping)
                else None
            ),
            after=(
                GeometryPrimitive.from_dict(after)
                if isinstance(after, Mapping)
                else None
            ),
            translation=(
                tuple(int(item) for item in translation)
                if isinstance(translation, list)
                else None
            ),
            hints=tuple(str(item) for item in hints),
            rule_ids=tuple(str(item) for item in rule_ids),
        )


def _translation(change: PrimitiveChange) -> tuple[int, int, int]:
    if change.before is None or change.after is None:
        raise MorphError("translation requires before/after primitives")
    old = change.before.points[0]
    new = change.after.points[0]
    return new.q - old.q, new.r - old.r, new.z - old.z


def _same_profile(before: GeometryScene, after: GeometryScene) -> GeometryProfile | None:
    if before.profile is None and after.profile is None:
        return None
    if before.profile is None or after.profile is None:
        raise MorphError("morph-plan v1 requires the same geometry profile at both endpoints")
    if before.profile.digest() != after.profile.digest():
        raise MorphError("morph-plan v1 does not cross geometry-profile revisions")
    return before.profile


def _rule(
    profile: GeometryProfile,
    rule_id: str,
    motif: Motif,
    effect: str,
) -> AppliedMorphRule:
    evidence = profile.evidence(motif)
    if evidence is None:
        raise MorphError(f"cannot admit {rule_id} without {motif.value} evidence")
    return AppliedMorphRule(rule_id, motif, evidence.source_ids, effect)


def _derive_rules(
    profile: GeometryProfile | None,
    delta: GeometryDelta,
) -> tuple[AppliedMorphRule, ...]:
    if profile is None:
        return ()
    kinds = {change.kind for change in delta.changes}
    moves = [change for change in delta.changes if change.kind is PrimitiveChangeKind.MOVE]
    rules: list[AppliedMorphRule] = []

    if PrimitiveChangeKind.TOPOLOGY in kinds and profile.supports_motif(Motif.MORPHING):
        rules.append(
            _rule(
                profile,
                "VB-MORPH-REFORM-001",
                Motif.MORPHING,
                "topology changes may use an endpoint-preserving continuous reform",
            )
        )
    if PrimitiveChangeKind.DISAPPEAR in kinds and profile.supports_motif(
        Motif.CONTEXT_PERSISTENCE
    ):
        rules.append(
            _rule(
                profile,
                "VB-MORPH-PERSIST-001",
                Motif.CONTEXT_PERSISTENCE,
                "disappearing primitives are eligible for non-state visual persistence",
            )
        )
    if any(_translation(change)[2] != 0 for change in moves) and profile.supports_motif(
        Motif.FOCUS_THROUGH
    ):
        rules.append(
            _rule(
                profile,
                "VB-MORPH-FOCUS-001",
                Motif.FOCUS_THROUGH,
                "depth translations are eligible for focus-through presentation",
            )
        )
    if any(_translation(change)[1] == 0 and _translation(change)[0] != 0 for change in moves):
        if profile.supports_motif(Motif.HORIZONTAL_MOTION):
            rules.append(
                _rule(
                    profile,
                    "VB-MORPH-HORIZONTAL-001",
                    Motif.HORIZONTAL_MOTION,
                    "q-axis translations are eligible for horizontal-motion emphasis",
                )
            )
    if any(_translation(change)[0] == 0 and _translation(change)[1] != 0 for change in moves):
        if profile.supports_motif(Motif.VERTICAL_MOTION):
            rules.append(
                _rule(
                    profile,
                    "VB-MORPH-VERTICAL-001",
                    Motif.VERTICAL_MOTION,
                    "r-axis translations are eligible for vertical-motion emphasis",
                )
            )
    return tuple(sorted(rules, key=lambda item: item.rule_id))


def _descriptor(
    change: PrimitiveChange,
    rules: tuple[AppliedMorphRule, ...],
) -> MorphDescriptor:
    rule_by_id = {rule.rule_id: rule for rule in rules}
    hints: list[str] = []
    rule_ids: list[str] = []

    if change.kind is PrimitiveChangeKind.APPEAR:
        intent = MorphIntent.ENTER
        strategy = MorphStrategy.ENDPOINT_APPEAR
    elif change.kind is PrimitiveChangeKind.DISAPPEAR:
        intent = MorphIntent.EXIT
        strategy = MorphStrategy.ENDPOINT_DISAPPEAR
        if "VB-MORPH-PERSIST-001" in rule_by_id:
            hints.append("context-persistence-eligible")
            rule_ids.append("VB-MORPH-PERSIST-001")
    elif change.kind is PrimitiveChangeKind.MOVE:
        intent = MorphIntent.TRANSLATE
        strategy = MorphStrategy.ENDPOINT_TRANSLATION
        dq, dr, dz = _translation(change)
        if dz != 0 and "VB-MORPH-FOCUS-001" in rule_by_id:
            hints.append("focus-through-eligible")
            rule_ids.append("VB-MORPH-FOCUS-001")
        if dr == 0 and dq != 0 and "VB-MORPH-HORIZONTAL-001" in rule_by_id:
            hints.append("horizontal-motion-emphasis-eligible")
            rule_ids.append("VB-MORPH-HORIZONTAL-001")
        if dq == 0 and dr != 0 and "VB-MORPH-VERTICAL-001" in rule_by_id:
            hints.append("vertical-motion-emphasis-eligible")
            rule_ids.append("VB-MORPH-VERTICAL-001")
        return MorphDescriptor(
            primitive_id=change.primitive_id,
            change_kind=change.kind,
            intent=intent,
            strategy=strategy,
            before=change.before,
            after=change.after,
            translation=(dq, dr, dz),
            hints=tuple(hints),
            rule_ids=tuple(rule_ids),
        )
    elif change.kind is PrimitiveChangeKind.TOPOLOGY:
        intent = MorphIntent.REFORM
        if "VB-MORPH-REFORM-001" in rule_by_id:
            strategy = MorphStrategy.CONTINUOUS_REFORM_ELIGIBLE
            hints.append("corpus-morphing-eligible")
            rule_ids.append("VB-MORPH-REFORM-001")
        else:
            strategy = MorphStrategy.DISCRETE_REFORM
    elif change.kind is PrimitiveChangeKind.METADATA:
        intent = MorphIntent.RETAG
        strategy = MorphStrategy.METADATA_UPDATE
    else:
        raise MorphError(f"unsupported geometry change kind {change.kind!r}")

    return MorphDescriptor(
        primitive_id=change.primitive_id,
        change_kind=change.kind,
        intent=intent,
        strategy=strategy,
        before=change.before,
        after=change.after,
        hints=tuple(hints),
        rule_ids=tuple(rule_ids),
    )


def _derive_components(
    before: GeometryScene,
    after: GeometryScene,
) -> tuple[GeometryDelta, tuple[AppliedMorphRule, ...], tuple[MorphDescriptor, ...]]:
    profile = _same_profile(before, after)
    delta = diff_geometry(before, after)
    rules = _derive_rules(profile, delta)
    descriptors = tuple(_descriptor(change, rules) for change in delta.changes)
    return delta, rules, descriptors


@dataclass(frozen=True, slots=True)
class MorphPlan:
    """Validated transition intent between two exact native-geometry scenes."""

    before_scene: GeometryScene
    after_scene: GeometryScene
    delta: GeometryDelta
    descriptors: tuple[MorphDescriptor, ...]
    applied_rules: tuple[AppliedMorphRule, ...] = ()
    schema: str = MORPH_PLAN_SCHEMA
    version: int = MORPH_PLAN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != MORPH_PLAN_SCHEMA or self.version != MORPH_PLAN_SCHEMA_VERSION:
            raise MorphError("unsupported morph-plan schema")
        expected_delta, expected_rules, expected_descriptors = _derive_components(
            self.before_scene,
            self.after_scene,
        )
        if self.delta.canonical_json() != expected_delta.canonical_json():
            raise MorphError("morph plan delta disagrees with endpoint scenes")
        ordered_rules = tuple(sorted(self.applied_rules, key=lambda item: item.rule_id))
        ordered_descriptors = tuple(sorted(self.descriptors, key=lambda item: item.primitive_id))
        if ordered_rules != expected_rules:
            raise MorphError("morph plan corpus rules disagree with endpoint evidence")
        if ordered_descriptors != expected_descriptors:
            raise MorphError("morph plan descriptors disagree with deterministic derivation")
        object.__setattr__(self, "applied_rules", ordered_rules)
        object.__setattr__(self, "descriptors", ordered_descriptors)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "before_scene": self.before_scene.as_dict(),
            "after_scene": self.after_scene.as_dict(),
            "before_scene_digest": self.before_scene.digest(),
            "after_scene_digest": self.after_scene.digest(),
            "delta": self.delta.as_dict(),
            "delta_digest": self.delta.digest(),
            "applied_rules": [rule.as_dict() for rule in self.applied_rules],
            "descriptors": [descriptor.as_dict() for descriptor in self.descriptors],
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "MorphPlan":
        before = payload.get("before_scene")
        after = payload.get("after_scene")
        delta_payload = payload.get("delta")
        rules = payload.get("applied_rules", [])
        descriptors = payload.get("descriptors")
        if not isinstance(before, Mapping) or not isinstance(after, Mapping):
            raise MorphError("morph plan endpoint scenes must be objects")
        if not isinstance(delta_payload, Mapping):
            raise MorphError("morph plan delta must be an object")
        if not isinstance(rules, list) or not isinstance(descriptors, list):
            raise MorphError("morph plan rules/descriptors must be lists")
        plan = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            before_scene=GeometryScene.from_dict(before),
            after_scene=GeometryScene.from_dict(after),
            delta=GeometryDelta.from_dict(delta_payload),
            applied_rules=tuple(AppliedMorphRule.from_dict(item) for item in rules),
            descriptors=tuple(MorphDescriptor.from_dict(item) for item in descriptors),
        )
        claims = {
            "before_scene_digest": plan.before_scene.digest(),
            "after_scene_digest": plan.after_scene.digest(),
            "delta_digest": plan.delta.digest(),
        }
        for key, actual in claims.items():
            claimed = payload.get(key)
            if claimed is not None and str(claimed) != actual:
                raise MorphError(f"morph plan {key} mismatch")
        return plan

    @classmethod
    def from_json(cls, text: str) -> "MorphPlan":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise MorphError("morph plan JSON root must be an object")
        return cls.from_dict(payload)


def build_morph_plan(before: GeometryScene, after: GeometryScene) -> MorphPlan:
    delta, rules, descriptors = _derive_components(before, after)
    return MorphPlan(before, after, delta, descriptors, rules)


@dataclass(frozen=True, slots=True)
class TimelineMorphEntry:
    frame_index: int
    plan: MorphPlan

    def __post_init__(self) -> None:
        if self.frame_index <= 0:
            raise MorphError("timeline morph entries begin at frame 1")

    def as_dict(self) -> dict[str, object]:
        return {
            "frame_index": self.frame_index,
            "plan_digest": self.plan.digest(),
            "plan": self.plan.as_dict(),
        }


@dataclass(frozen=True, slots=True)
class TimelineMorphManifest:
    timeline_digest: str
    entries: tuple[TimelineMorphEntry, ...]
    schema: str = TIMELINE_MORPH_SCHEMA
    version: int = TIMELINE_MORPH_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != TIMELINE_MORPH_SCHEMA or self.version != TIMELINE_MORPH_SCHEMA_VERSION:
            raise MorphError("unsupported timeline morph manifest schema")
        expected = tuple(range(1, len(self.entries) + 1))
        if tuple(entry.frame_index for entry in self.entries) != expected:
            raise MorphError("timeline morph entries must be contiguous from frame 1")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "timeline_digest": self.timeline_digest,
            "entry_count": len(self.entries),
            "entries": [entry.as_dict() for entry in self.entries],
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def build_timeline_morph_manifest(timeline: RelicTimeline) -> TimelineMorphManifest:
    entries = tuple(
        TimelineMorphEntry(
            frame_index=after.frame_index,
            plan=build_morph_plan(before.scene, after.scene),
        )
        for before, after in zip(timeline.frames, timeline.frames[1:], strict=False)
    )
    return TimelineMorphManifest(timeline.digest(), entries)
