"""Deterministic, corpus-traceable native geometry for TD-1.

This module converts one immutable :class:`RenderState` into renderer-independent
integer-lattice geometry. Geometry may encode and arrange state; it is never
allowed to invent machine truth.

Corpus-backed rules are opt-in through a frozen :class:`CorpusSnapshot`. If no
profile is supplied, the scene uses conservative project-native fallback
placement and no corpus-derived rule is claimed.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from itertools import pairwise

from .corpus import CorpusSnapshot, Motif
from .glyphs import glyph_id_to_triad, triad_to_glyph_id, word_to_glyph_ids
from .render_state import SEMANTIC_ROOT_IDS, RenderState
from .semantic import SemanticRoot
from .ternary import TernaryWord

GEOMETRY_SCHEMA = "td1.geometry-scene"
GEOMETRY_SCHEMA_VERSION = 1
GEOMETRY_GRID = "axial-triangular-int/v1"

# Three non-collinear axial directions. A negative trit reverses the direction,
# zero suppresses that spoke, and positive uses the direction as written.
_GLYPH_AXES: tuple[tuple[int, int], ...] = ((1, 0), (0, 1), (-1, 1))
_REGISTER_GLYPH_OFFSETS: tuple[tuple[int, int], ...] = ((0, 0), (6, 0), (0, 6), (-6, 6))


class GeometryError(ValueError):
    """Raised when TD-1 geometry violates the native geometry contract."""


class GeometryKind(str, Enum):
    NODE = "node"
    SEGMENT = "segment"
    POLYLINE = "polyline"


@dataclass(frozen=True, slots=True, order=True)
class LatticePoint:
    """Integer point in TD-1's axial triangular lattice plus discrete depth."""

    q: int
    r: int
    z: int = 0

    def offset(self, dq: int = 0, dr: int = 0, dz: int = 0) -> "LatticePoint":
        return LatticePoint(self.q + dq, self.r + dr, self.z + dz)

    def as_list(self) -> list[int]:
        return [self.q, self.r, self.z]

    @classmethod
    def from_value(cls, value: object) -> "LatticePoint":
        if not isinstance(value, list) or len(value) != 3:
            raise GeometryError("geometry point must be a three-integer list")
        return cls(*(int(item) for item in value))


@dataclass(frozen=True, slots=True)
class GeometryPrimitive:
    """One renderer-independent native geometry primitive."""

    primitive_id: str
    kind: GeometryKind
    role: str
    points: tuple[LatticePoint, ...]
    scale_milli: int = 1000
    glyph_id: int | None = None
    semantic_root_id: int | None = None
    state_value: int | None = None
    motifs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.primitive_id.strip():
            raise GeometryError("primitive_id must not be empty")
        if not self.role.strip():
            raise GeometryError("primitive role must not be empty")
        if self.scale_milli <= 0:
            raise GeometryError("primitive scale_milli must be positive")
        if self.kind is GeometryKind.NODE and len(self.points) != 1:
            raise GeometryError("node primitive requires exactly one point")
        if self.kind is GeometryKind.SEGMENT and len(self.points) != 2:
            raise GeometryError("segment primitive requires exactly two points")
        if self.kind is GeometryKind.POLYLINE and len(self.points) < 2:
            raise GeometryError("polyline primitive requires at least two points")
        if self.glyph_id is not None and not 0 <= self.glyph_id <= 26:
            raise GeometryError("glyph_id must be in 0..26")
        if self.semantic_root_id is not None and not 0 <= self.semantic_root_id <= 15:
            raise GeometryError("semantic_root_id must be in 0..15")
        canonical_motifs = tuple(sorted(set(self.motifs)))
        object.__setattr__(self, "motifs", canonical_motifs)

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "primitive_id": self.primitive_id,
            "kind": self.kind.value,
            "role": self.role,
            "points": [point.as_list() for point in self.points],
            "scale_milli": self.scale_milli,
        }
        if self.glyph_id is not None:
            payload["glyph_id"] = self.glyph_id
        if self.semantic_root_id is not None:
            payload["semantic_root_id"] = self.semantic_root_id
        if self.state_value is not None:
            payload["state_value"] = self.state_value
        if self.motifs:
            payload["motifs"] = list(self.motifs)
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "GeometryPrimitive":
        raw_points = payload.get("points")
        if not isinstance(raw_points, list):
            raise GeometryError("primitive points must be a list")
        raw_motifs = payload.get("motifs", [])
        if not isinstance(raw_motifs, list):
            raise GeometryError("primitive motifs must be a list")
        return cls(
            primitive_id=str(payload["primitive_id"]),
            kind=GeometryKind(str(payload["kind"])),
            role=str(payload["role"]),
            points=tuple(LatticePoint.from_value(item) for item in raw_points),
            scale_milli=int(payload.get("scale_milli", 1000)),
            glyph_id=int(payload["glyph_id"]) if payload.get("glyph_id") is not None else None,
            semantic_root_id=(
                int(payload["semantic_root_id"])
                if payload.get("semantic_root_id") is not None
                else None
            ),
            state_value=(
                int(payload["state_value"]) if payload.get("state_value") is not None else None
            ),
            motifs=tuple(str(item) for item in raw_motifs),
        )


@dataclass(frozen=True, slots=True)
class MotifSupport:
    motif: Motif
    source_ids: tuple[str, ...]
    methods: tuple[str, ...]
    mean_confidence_milli: int

    def __post_init__(self) -> None:
        if not self.source_ids:
            raise GeometryError("motif support requires at least one source")
        if not 0 <= self.mean_confidence_milli <= 1000:
            raise GeometryError("mean confidence must be in 0..1000")
        object.__setattr__(self, "source_ids", tuple(sorted(set(self.source_ids))))
        object.__setattr__(self, "methods", tuple(sorted(set(self.methods))))

    def as_dict(self) -> dict[str, object]:
        return {
            "motif": self.motif.value,
            "source_ids": list(self.source_ids),
            "methods": list(self.methods),
            "mean_confidence_milli": self.mean_confidence_milli,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "MotifSupport":
        source_ids = payload.get("source_ids")
        methods = payload.get("methods")
        if not isinstance(source_ids, list) or not isinstance(methods, list):
            raise GeometryError("motif support source_ids/methods must be lists")
        return cls(
            motif=Motif(str(payload["motif"])),
            source_ids=tuple(str(item) for item in source_ids),
            methods=tuple(str(item) for item in methods),
            mean_confidence_milli=int(payload["mean_confidence_milli"]),
        )


@dataclass(frozen=True, slots=True)
class GeometryProfile:
    """Corpus evidence admitted to influence one geometry build."""

    snapshot_id: str
    snapshot_digest: str
    threshold_milli: int
    supports: tuple[MotifSupport, ...]

    def __post_init__(self) -> None:
        if not 0 <= self.threshold_milli <= 1000:
            raise GeometryError("threshold_milli must be in 0..1000")
        ordered = tuple(sorted(self.supports, key=lambda item: item.motif.value))
        if len({item.motif for item in ordered}) != len(ordered):
            raise GeometryError("geometry profile cannot repeat a motif")
        object.__setattr__(self, "supports", ordered)

    @classmethod
    def from_snapshot(
        cls,
        snapshot: CorpusSnapshot,
        *,
        threshold_milli: int = 750,
    ) -> "GeometryProfile":
        if not 0 <= threshold_milli <= 1000:
            raise GeometryError("threshold_milli must be in 0..1000")
        grouped: dict[Motif, list[object]] = defaultdict(list)
        for annotation in snapshot.annotations:
            if annotation.confidence_milli >= threshold_milli:
                grouped[annotation.motif].append(annotation)

        supports: list[MotifSupport] = []
        for motif, annotations in grouped.items():
            source_ids = tuple(annotation.source_id for annotation in annotations)
            methods = tuple(annotation.method.value for annotation in annotations)
            confidence_total = sum(annotation.confidence_milli for annotation in annotations)
            mean = confidence_total // len(annotations)
            supports.append(MotifSupport(motif, source_ids, methods, mean))
        return cls(snapshot.snapshot_id, snapshot.digest(), threshold_milli, tuple(supports))

    def supports_motif(self, motif: Motif) -> bool:
        return any(item.motif is motif for item in self.supports)

    def evidence(self, motif: Motif) -> MotifSupport | None:
        return next((item for item in self.supports if item.motif is motif), None)

    def as_dict(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_digest": self.snapshot_digest,
            "threshold_milli": self.threshold_milli,
            "supports": [item.as_dict() for item in self.supports],
        }

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "GeometryProfile":
        raw_supports = payload.get("supports")
        if not isinstance(raw_supports, list):
            raise GeometryError("geometry profile supports must be a list")
        return cls(
            snapshot_id=str(payload["snapshot_id"]),
            snapshot_digest=str(payload["snapshot_digest"]),
            threshold_milli=int(payload["threshold_milli"]),
            supports=tuple(MotifSupport.from_dict(item) for item in raw_supports),
        )


@dataclass(frozen=True, slots=True)
class AppliedGeometryRule:
    rule_id: str
    motif: Motif
    source_ids: tuple[str, ...]
    effect: str

    def __post_init__(self) -> None:
        if not self.rule_id.strip() or not self.effect.strip():
            raise GeometryError("geometry rule id/effect must not be empty")
        if not self.source_ids:
            raise GeometryError("corpus-backed geometry rule requires source IDs")
        object.__setattr__(self, "source_ids", tuple(sorted(set(self.source_ids))))

    def as_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "motif": self.motif.value,
            "source_ids": list(self.source_ids),
            "effect": self.effect,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "AppliedGeometryRule":
        source_ids = payload.get("source_ids")
        if not isinstance(source_ids, list):
            raise GeometryError("geometry rule source_ids must be a list")
        return cls(
            rule_id=str(payload["rule_id"]),
            motif=Motif(str(payload["motif"])),
            source_ids=tuple(str(item) for item in source_ids),
            effect=str(payload["effect"]),
        )


@dataclass(frozen=True, slots=True)
class GeometryScene:
    """Versioned geometry snapshot derived from one immutable RenderState."""

    source_render_digest: str
    source_machine_digest: str
    primitives: tuple[GeometryPrimitive, ...]
    applied_rules: tuple[AppliedGeometryRule, ...] = ()
    profile: GeometryProfile | None = None
    schema: str = GEOMETRY_SCHEMA
    version: int = GEOMETRY_SCHEMA_VERSION
    grid: str = GEOMETRY_GRID

    def __post_init__(self) -> None:
        if self.schema != GEOMETRY_SCHEMA:
            raise GeometryError(f"unsupported geometry schema {self.schema!r}")
        if self.version != GEOMETRY_SCHEMA_VERSION:
            raise GeometryError(f"unsupported geometry schema version {self.version}")
        if self.grid != GEOMETRY_GRID:
            raise GeometryError(f"unsupported geometry grid {self.grid!r}")
        ordered_primitives = tuple(sorted(self.primitives, key=lambda item: item.primitive_id))
        ids = tuple(item.primitive_id for item in ordered_primitives)
        if len(set(ids)) != len(ids):
            raise GeometryError("geometry primitive IDs must be unique")
        ordered_rules = tuple(sorted(self.applied_rules, key=lambda item: item.rule_id))
        if len({item.rule_id for item in ordered_rules}) != len(ordered_rules):
            raise GeometryError("geometry rule IDs must be unique")
        if ordered_rules and self.profile is None:
            raise GeometryError("applied corpus rules require a geometry profile")
        if self.profile is not None:
            for rule in ordered_rules:
                evidence = self.profile.evidence(rule.motif)
                if evidence is None:
                    raise GeometryError(f"rule {rule.rule_id} lacks admitted motif support")
                if not set(rule.source_ids).issubset(evidence.source_ids):
                    raise GeometryError(f"rule {rule.rule_id} cites sources outside motif support")
        object.__setattr__(self, "primitives", ordered_primitives)
        object.__setattr__(self, "applied_rules", ordered_rules)

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": self.schema,
            "version": self.version,
            "grid": self.grid,
            "source_render_digest": self.source_render_digest,
            "source_machine_digest": self.source_machine_digest,
            "primitives": [item.as_dict() for item in self.primitives],
            "applied_rules": [item.as_dict() for item in self.applied_rules],
        }
        if self.profile is not None:
            payload["profile"] = self.profile.as_dict()
            payload["profile_digest"] = self.profile.digest()
        return payload

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "GeometryScene":
        raw_primitives = payload.get("primitives")
        raw_rules = payload.get("applied_rules", [])
        if not isinstance(raw_primitives, list) or not isinstance(raw_rules, list):
            raise GeometryError("scene primitives/applied_rules must be lists")
        profile_payload = payload.get("profile")
        profile = (
            GeometryProfile.from_dict(profile_payload)
            if isinstance(profile_payload, Mapping)
            else None
        )
        scene = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            grid=str(payload["grid"]),
            source_render_digest=str(payload["source_render_digest"]),
            source_machine_digest=str(payload["source_machine_digest"]),
            primitives=tuple(GeometryPrimitive.from_dict(item) for item in raw_primitives),
            applied_rules=tuple(AppliedGeometryRule.from_dict(item) for item in raw_rules),
            profile=profile,
        )
        expected_profile_digest = payload.get("profile_digest")
        if expected_profile_digest is not None:
            if profile is None or profile.digest() != str(expected_profile_digest):
                raise GeometryError("geometry profile digest mismatch")
        return scene

    @classmethod
    def from_json(cls, text: str) -> "GeometryScene":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise GeometryError("geometry scene JSON root must be an object")
        return cls.from_dict(payload)


def microglyph_geometry(
    glyph_id: int,
    *,
    prefix: str = "glyph",
    origin: LatticePoint = LatticePoint(0, 0, 0),
    scale: int = 2,
    semantic_root_id: int | None = None,
    motifs: Iterable[str] = (),
) -> tuple[GeometryPrimitive, ...]:
    """Return unique reversible topology for one of the 27 microglyph states."""
    if scale <= 0:
        raise GeometryError("microglyph scale must be positive")
    triad = glyph_id_to_triad(glyph_id)
    motif_tuple = tuple(motifs)
    primitives: list[GeometryPrimitive] = [
        GeometryPrimitive(
            primitive_id=f"{prefix}.center",
            kind=GeometryKind.NODE,
            role="glyph-center",
            points=(origin,),
            glyph_id=glyph_id,
            semantic_root_id=semantic_root_id,
            scale_milli=scale * 1000,
            motifs=motif_tuple,
        )
    ]
    for slot, trit in enumerate(triad):
        if trit == 0:
            continue
        axis_q, axis_r = _GLYPH_AXES[slot]
        endpoint = origin.offset(axis_q * trit * scale, axis_r * trit * scale)
        primitives.append(
            GeometryPrimitive(
                primitive_id=f"{prefix}.trit{slot}",
                kind=GeometryKind.SEGMENT,
                role=f"glyph-trit-{slot}",
                points=(origin, endpoint),
                glyph_id=glyph_id,
                semantic_root_id=semantic_root_id,
                scale_milli=scale * 1000,
                motifs=motif_tuple,
            )
        )
    return tuple(primitives)


def glyph_id_from_geometry(primitives: Iterable[GeometryPrimitive]) -> int:
    """Recover a microglyph ID from its spoke topology, independent of scale."""
    items = tuple(primitives)
    centers = [item for item in items if item.role == "glyph-center"]
    if len(centers) != 1:
        raise GeometryError("microglyph topology must contain exactly one center")
    origin = centers[0].points[0]
    triad = [0, 0, 0]
    seen_slots: set[int] = set()
    for item in items:
        if not item.role.startswith("glyph-trit-"):
            continue
        try:
            slot = int(item.role.rsplit("-", 1)[1])
        except ValueError as exc:
            raise GeometryError("invalid microglyph trit role") from exc
        if slot not in (0, 1, 2) or slot in seen_slots or len(item.points) != 2:
            raise GeometryError("invalid or duplicate microglyph trit segment")
        seen_slots.add(slot)
        start, end = item.points
        if start != origin or end.z != origin.z:
            raise GeometryError("microglyph spoke must originate at the center")
        dq = end.q - origin.q
        dr = end.r - origin.r
        axis_q, axis_r = _GLYPH_AXES[slot]
        positive = _same_axial_direction(dq, dr, axis_q, axis_r)
        negative = _same_axial_direction(dq, dr, -axis_q, -axis_r)
        if positive == negative:
            raise GeometryError("microglyph spoke is not aligned to its trit axis")
        triad[slot] = 1 if positive else -1
    return triad_to_glyph_id(tuple(triad))


def _same_axial_direction(dq: int, dr: int, aq: int, ar: int) -> bool:
    if dq == 0 and dr == 0:
        return False
    if aq == 0:
        return dq == 0 and dr * ar > 0
    if ar == 0:
        return dr == 0 and dq * aq > 0
    return dq * ar == dr * aq and dq * aq > 0


def _motif_names(profile: GeometryProfile | None, *motifs: Motif) -> tuple[str, ...]:
    if profile is None:
        return ()
    return tuple(motif.value for motif in motifs if profile.supports_motif(motif))


def _rule(profile: GeometryProfile, rule_id: str, motif: Motif, effect: str) -> AppliedGeometryRule:
    evidence = profile.evidence(motif)
    if evidence is None:
        raise GeometryError(f"cannot apply {rule_id} without {motif.value} evidence")
    return AppliedGeometryRule(rule_id, motif, evidence.source_ids, effect)


def _append_word_geometry(
    primitives: list[GeometryPrimitive],
    *,
    prefix: str,
    glyph_ids: Iterable[int],
    center: LatticePoint,
    scale: int,
    role: str,
    state_value: int | None = None,
    motifs: tuple[str, ...] = (),
) -> None:
    ids = tuple(glyph_ids)
    if len(ids) != 4:
        raise GeometryError("TD-1 word geometry requires exactly four microglyph IDs")
    primitives.append(
        GeometryPrimitive(
            primitive_id=f"{prefix}.anchor",
            kind=GeometryKind.NODE,
            role=role,
            points=(center,),
            state_value=state_value,
            scale_milli=scale * 1000,
            motifs=motifs,
        )
    )
    for index, glyph_id in enumerate(ids):
        dq, dr = _REGISTER_GLYPH_OFFSETS[index]
        origin = center.offset(dq * scale, dr * scale)
        primitives.extend(
            microglyph_geometry(
                glyph_id,
                prefix=f"{prefix}.g{index}",
                origin=origin,
                scale=scale,
                motifs=motifs,
            )
        )


def _register_center(index: int, *, lattice: bool, z: int) -> LatticePoint:
    if not lattice:
        return LatticePoint(index * 28, 0, z)
    row, col = divmod(index, 3)
    return LatticePoint(col * 28 - row * 14, row * 28, z)


def _semantic_root_glyph_id(root: SemanticRoot) -> int:
    # Semantic roots occupy a stable 16-state window inside the 27-state substrate.
    return SEMANTIC_ROOT_IDS[root] + 5


def _append_weave_geometry(
    primitives: list[GeometryPrimitive],
    state: RenderState,
    *,
    z: int,
    scale: int,
    braided: bool,
    motifs: tuple[str, ...],
) -> None:
    if state.weave is None:
        return
    centers: list[LatticePoint] = []
    for index, root in enumerate(state.weave.roots):
        center = LatticePoint(index * 18, 72, z)
        centers.append(center)
        root_id = SEMANTIC_ROOT_IDS[root]
        primitives.extend(
            microglyph_geometry(
                _semantic_root_glyph_id(root),
                prefix=f"semantic.root{index}",
                origin=center,
                scale=scale,
                semantic_root_id=root_id,
                motifs=motifs,
            )
        )

    for index, (start, end) in enumerate(pairwise(centers)):
        if braided:
            midpoint = LatticePoint(
                (start.q + end.q) // 2,
                (start.r + end.r) // 2,
                z + (8 if index % 2 == 0 else -8),
            )
            points = (start, midpoint, end)
            kind = GeometryKind.POLYLINE
        else:
            points = (start, end)
            kind = GeometryKind.SEGMENT
        primitives.append(
            GeometryPrimitive(
                primitive_id=f"semantic.link{index}",
                kind=kind,
                role="state-weave-link",
                points=points,
                motifs=motifs,
            )
        )

    terminal = centers[-1]
    modifier = int(state.weave.modifier)
    if modifier > 0:
        endpoint = terminal.offset(8, 0)
    elif modifier < 0:
        endpoint = terminal.offset(-8, 0)
    else:
        endpoint = terminal.offset(0, 8)
    primitives.append(
        GeometryPrimitive(
            primitive_id="semantic.modifier",
            kind=GeometryKind.SEGMENT,
            role="state-weave-modifier",
            points=(terminal, endpoint),
            state_value=modifier,
            motifs=motifs,
        )
    )


def _append_observer_geometry(
    primitives: list[GeometryPrimitive],
    state: RenderState,
    *,
    z: int,
    scale: int,
    motifs: tuple[str, ...],
) -> None:
    if state.observer is None:
        return
    values = (
        state.observer.latitude_nanodeg,
        state.observer.longitude_nanodeg,
        state.observer.altitude_microm,
        state.observer.earth_rotation_nanorad_approx,
    )
    for index, value in enumerate(values):
        word = TernaryWord.from_int(value)
        center = LatticePoint(-42 + index * 28, 110, z)
        _append_word_geometry(
            primitives,
            prefix=f"observer.v{index}",
            glyph_ids=word_to_glyph_ids(word),
            center=center,
            scale=scale,
            role="observer-word",
            state_value=value,
            motifs=motifs,
        )


def build_geometry_scene(
    state: RenderState,
    *,
    profile: GeometryProfile | None = None,
) -> GeometryScene:
    """Derive deterministic native geometry from one immutable render state."""
    lattice = profile is not None and profile.supports_motif(Motif.LATTICE)
    depth = profile is not None and profile.supports_motif(Motif.DEPTH)
    multiscale = profile is not None and profile.supports_motif(Motif.MULTISCALE)
    braided = profile is not None and profile.supports_motif(Motif.BRAIDING)

    machine_z = 100 if depth else 0
    semantic_z = 200 if depth else 0
    observer_z = 300 if depth else 0
    machine_scale = 2
    semantic_scale = 3 if multiscale else 2

    primitives: list[GeometryPrimitive] = []
    rules: list[AppliedGeometryRule] = []
    if profile is not None:
        if lattice:
            rules.append(
                _rule(
                    profile,
                    "VB-GEO-LATTICE-001",
                    Motif.LATTICE,
                    "place the nine registers on a 3x3 triangular axial lattice",
                )
            )
        if depth:
            rules.append(
                _rule(
                    profile,
                    "VB-GEO-DEPTH-001",
                    Motif.DEPTH,
                    "separate machine, semantic, and observer planes on discrete z layers",
                )
            )
        if multiscale:
            rules.append(
                _rule(
                    profile,
                    "VB-GEO-MULTISCALE-001",
                    Motif.MULTISCALE,
                    "increase semantic-root scale relative to machine microglyphs",
                )
            )
        if braided:
            rules.append(
                _rule(
                    profile,
                    "VB-GEO-BRAID-001",
                    Motif.BRAIDING,
                    "route State Weave links through alternating depth offsets",
                )
            )

    machine_motifs = _motif_names(profile, Motif.LATTICE, Motif.DEPTH, Motif.MICROGLYPH)
    for register in state.registers:
        _append_word_geometry(
            primitives,
            prefix=f"machine.r{register.index}",
            glyph_ids=register.glyph_ids,
            center=_register_center(register.index, lattice=lattice, z=machine_z),
            scale=machine_scale,
            role="register-word",
            state_value=register.value,
            motifs=machine_motifs,
        )

    control_values = (
        ("ip", state.ip),
        ("steps", state.steps),
        ("condition", state.cond),
        ("halted", 1 if state.halted else 0),
    )
    for index, (name, value) in enumerate(control_values):
        word = TernaryWord.from_int(value)
        _append_word_geometry(
            primitives,
            prefix=f"machine.control.{name}",
            glyph_ids=word_to_glyph_ids(word),
            center=LatticePoint(-42 + index * 28, -34, machine_z),
            scale=1,
            role="machine-control-word",
            state_value=value,
            motifs=machine_motifs,
        )

    for index, cell in enumerate(state.nonzero_memory):
        row, col = divmod(index, 9)
        center = LatticePoint(col * 24, -66 - row * 22, machine_z)
        _append_word_geometry(
            primitives,
            prefix=f"memory.a{cell.address}",
            glyph_ids=cell.glyph_ids,
            center=center,
            scale=1,
            role="memory-word",
            state_value=cell.address,
            motifs=machine_motifs,
        )

    semantic_motifs = _motif_names(
        profile,
        Motif.DEPTH,
        Motif.MULTISCALE,
        Motif.BRAIDING,
        Motif.MICROGLYPH,
    )
    _append_weave_geometry(
        primitives,
        state,
        z=semantic_z,
        scale=semantic_scale,
        braided=braided,
        motifs=semantic_motifs,
    )
    _append_observer_geometry(
        primitives,
        state,
        z=observer_z,
        scale=2,
        motifs=_motif_names(profile, Motif.DEPTH, Motif.MULTISCALE),
    )

    return GeometryScene(
        source_render_digest=state.digest(),
        source_machine_digest=state.machine_digest,
        primitives=tuple(primitives),
        applied_rules=tuple(rules),
        profile=profile,
    )
