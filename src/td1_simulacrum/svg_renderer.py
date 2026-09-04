"""Deterministic reference SVG rendering for TD-1 native geometry.

The renderer consumes only a validated :class:`GeometryScene`. It may choose
projection, stroke style, labels, and other presentation details; it is never
allowed to infer or create machine state, corpus evidence, or semantic actions.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from html import escape

from .geometry import GeometryKind, GeometryPrimitive, GeometryScene, LatticePoint

SVG_RENDERER_SCHEMA = "td1.svg-render"
SVG_RENDERER_VERSION = 1
SVG_PROJECTION = "axial-int-oblique/v1"

_SAFE_ID_CHAR = re.compile(r"[A-Za-z0-9_.:-]")


class SVGRendererError(ValueError):
    """Raised when a geometry scene cannot be rendered by the reference SVG renderer."""


class SVGTheme(str, Enum):
    RELIC = "relic"
    ENGINEERING = "engineering"


@dataclass(frozen=True, slots=True)
class SVGRenderOptions:
    """Pure presentation parameters for the deterministic SVG renderer."""

    theme: SVGTheme = SVGTheme.RELIC
    unit: int = 3
    depth_x: int = 2
    depth_y: int = 1
    margin: int = 36
    show_labels: bool | None = None

    def __post_init__(self) -> None:
        if self.unit <= 0:
            raise SVGRendererError("SVG unit must be positive")
        if self.depth_x < 0 or self.depth_y < 0:
            raise SVGRendererError("SVG depth projection components must be nonnegative")
        if self.margin < 0:
            raise SVGRendererError("SVG margin must be nonnegative")

    @property
    def labels_enabled(self) -> bool:
        if self.show_labels is not None:
            return self.show_labels
        return self.theme is SVGTheme.ENGINEERING

    def as_dict(self) -> dict[str, object]:
        return {
            "theme": self.theme.value,
            "unit": self.unit,
            "depth_x": self.depth_x,
            "depth_y": self.depth_y,
            "margin": self.margin,
            "show_labels": self.labels_enabled,
        }


@dataclass(frozen=True, slots=True)
class SVGRenderArtifact:
    """Exact standalone SVG output plus immutable provenance metadata."""

    svg: str
    scene_digest: str
    metadata_digest: str
    theme: SVGTheme

    def __post_init__(self) -> None:
        if not self.svg.startswith("<?xml"):
            raise SVGRendererError("SVG artifact must be a standalone XML document")
        if len(self.scene_digest) != 64 or len(self.metadata_digest) != 64:
            raise SVGRendererError("SVG provenance digests must be SHA-256 hex strings")

    def digest(self) -> str:
        return hashlib.sha256(self.svg.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ProjectedPoint:
    """Renderer-only two-dimensional integer projection."""

    x: int
    y: int


def _project(point: LatticePoint, options: SVGRenderOptions) -> ProjectedPoint:
    """Project triangular axial coordinates and discrete depth using integers only."""
    x = (2 * point.q + point.r) * options.unit + point.z * options.depth_x
    y = 3 * point.r * options.unit - point.z * options.depth_y
    return ProjectedPoint(x, y)


def project_point(point: LatticePoint, options: SVGRenderOptions | None = None) -> tuple[int, int]:
    """Public deterministic projection helper used by renderer equivalence tests."""
    projected = _project(point, options or SVGRenderOptions())
    return projected.x, projected.y


def _safe_svg_id(identifier: str) -> str:
    """Encode an arbitrary stable primitive ID into a valid deterministic SVG ID."""
    encoded: list[str] = ["td1-"]
    for byte in identifier.encode("utf-8"):
        character = chr(byte)
        if byte < 128 and _SAFE_ID_CHAR.fullmatch(character):
            encoded.append(character)
        else:
            encoded.append(f"_x{byte:02X}_")
    return "".join(encoded)


def _attrs(attributes: list[tuple[str, str | int]]) -> str:
    return " ".join(
        f'{name}="{escape(str(value), quote=True)}"' for name, value in attributes
    )


def _primitive_data_attributes(primitive: GeometryPrimitive) -> list[tuple[str, str | int]]:
    attributes: list[tuple[str, str | int]] = [
        ("id", _safe_svg_id(primitive.primitive_id)),
        ("class", f"td1-primitive td1-{primitive.kind.value}"),
        ("data-primitive-id", primitive.primitive_id),
        ("data-kind", primitive.kind.value),
        ("data-role", primitive.role),
        ("data-scale-milli", primitive.scale_milli),
    ]
    if primitive.glyph_id is not None:
        attributes.append(("data-glyph-id", primitive.glyph_id))
    if primitive.semantic_root_id is not None:
        attributes.append(("data-semantic-root-id", primitive.semantic_root_id))
    if primitive.state_value is not None:
        attributes.append(("data-state-value", primitive.state_value))
    if primitive.motifs:
        attributes.append(("data-motifs", ",".join(primitive.motifs)))
    return attributes


def _style(theme: SVGTheme) -> str:
    """Static presentation only; neither palette carries machine semantics."""
    if theme is SVGTheme.ENGINEERING:
        return (
            ".td1-bg{fill:#ffffff;}"
            ".td1-primitive{stroke:#111827;fill:none;stroke-linecap:round;"
            "stroke-linejoin:round;vector-effect:non-scaling-stroke;}"
            ".td1-node{fill:#111827;}"
            ".td1-label{fill:#374151;font:10px ui-monospace,monospace;}"
        )
    return (
        ".td1-bg{fill:#030709;}"
        ".td1-primitive{stroke:#63f5df;fill:none;stroke-linecap:round;"
        "stroke-linejoin:round;vector-effect:non-scaling-stroke;}"
        ".td1-node{fill:#ffd166;stroke:#ffd166;}"
        ".td1-label{fill:#63f5df;font:10px ui-monospace,monospace;}"
    )


def _stroke_width(primitive: GeometryPrimitive) -> int:
    """Presentation weight derived only from the geometry's explicit scale."""
    return max(1, min(6, (primitive.scale_milli + 999) // 1000))


def _node_radius(primitive: GeometryPrimitive) -> int:
    return max(2, min(8, 1 + (primitive.scale_milli + 999) // 1000))


def _projected_primitives(
    scene: GeometryScene,
    options: SVGRenderOptions,
) -> tuple[tuple[GeometryPrimitive, tuple[ProjectedPoint, ...]], ...]:
    return tuple(
        (primitive, tuple(_project(point, options) for point in primitive.points))
        for primitive in scene.primitives
    )


def _bounds(
    projected: tuple[tuple[GeometryPrimitive, tuple[ProjectedPoint, ...]], ...],
    margin: int,
) -> tuple[int, int, int, int]:
    points = [point for _, primitive_points in projected for point in primitive_points]
    if not points:
        raise SVGRendererError("cannot render an empty geometry scene")
    min_x = min(point.x for point in points)
    max_x = max(point.x for point in points)
    min_y = min(point.y for point in points)
    max_y = max(point.y for point in points)
    translate_x = margin - min_x
    translate_y = margin - min_y
    width = max(1, max_x - min_x + 2 * margin)
    height = max(1, max_y - min_y + 2 * margin)
    return translate_x, translate_y, width, height


def _shift(point: ProjectedPoint, dx: int, dy: int) -> ProjectedPoint:
    return ProjectedPoint(point.x + dx, point.y + dy)


def _render_primitive(
    primitive: GeometryPrimitive,
    points: tuple[ProjectedPoint, ...],
    *,
    translate_x: int,
    translate_y: int,
    labels: bool,
) -> list[str]:
    shifted = tuple(_shift(point, translate_x, translate_y) for point in points)
    common = _primitive_data_attributes(primitive)
    common.append(("stroke-width", _stroke_width(primitive)))
    lines: list[str] = []

    if primitive.kind is GeometryKind.NODE:
        point = shifted[0]
        attributes = common + [
            ("cx", point.x),
            ("cy", point.y),
            ("r", _node_radius(primitive)),
        ]
        lines.append(f"    <circle {_attrs(attributes)} />")
    elif primitive.kind is GeometryKind.SEGMENT:
        start, end = shifted
        attributes = common + [
            ("x1", start.x),
            ("y1", start.y),
            ("x2", end.x),
            ("y2", end.y),
        ]
        lines.append(f"    <line {_attrs(attributes)} />")
    elif primitive.kind is GeometryKind.POLYLINE:
        encoded_points = " ".join(f"{point.x},{point.y}" for point in shifted)
        attributes = common + [("points", encoded_points)]
        lines.append(f"    <polyline {_attrs(attributes)} />")
    else:
        raise SVGRendererError(f"unsupported geometry kind {primitive.kind!r}")

    if labels:
        anchor = shifted[0]
        label = f"{primitive.primitive_id} | {primitive.role}"
        label_attributes = [
            ("class", "td1-label"),
            ("x", anchor.x + 6),
            ("y", anchor.y - 6),
            ("data-for", primitive.primitive_id),
        ]
        lines.append(
            f"    <text {_attrs(label_attributes)}>{escape(label, quote=False)}</text>"
        )
    return lines


def _metadata(scene: GeometryScene, options: SVGRenderOptions) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": SVG_RENDERER_SCHEMA,
        "version": SVG_RENDERER_VERSION,
        "projection": SVG_PROJECTION,
        "scene_digest": scene.digest(),
        "source_render_digest": scene.source_render_digest,
        "source_machine_digest": scene.source_machine_digest,
        "primitive_count": len(scene.primitives),
        "options": options.as_dict(),
    }
    if scene.profile is not None:
        payload["profile_digest"] = scene.profile.digest()
        payload["corpus_snapshot_id"] = scene.profile.snapshot_id
        payload["corpus_snapshot_digest"] = scene.profile.snapshot_digest
    if scene.applied_rules:
        payload["applied_rule_ids"] = [rule.rule_id for rule in scene.applied_rules]
    return payload


def _canonical_metadata(scene: GeometryScene, options: SVGRenderOptions) -> str:
    return json.dumps(
        _metadata(scene, options),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def render_svg(
    scene: GeometryScene,
    options: SVGRenderOptions | None = None,
) -> SVGRenderArtifact:
    """Render a validated geometry scene into deterministic standalone SVG."""
    options = options or SVGRenderOptions()
    projected = _projected_primitives(scene, options)
    translate_x, translate_y, width, height = _bounds(projected, options.margin)
    metadata_json = _canonical_metadata(scene, options)
    metadata_digest = hashlib.sha256(metadata_json.encode("utf-8")).hexdigest()

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
            f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'data-td1-scene-digest="{scene.digest()}" '
            f'data-td1-renderer-version="{SVG_RENDERER_VERSION}">'
        ),
        f"  <metadata id=\"td1-render-metadata\">{escape(metadata_json, quote=False)}</metadata>",
        f"  <style>{_style(options.theme)}</style>",
        f'  <rect class="td1-bg" x="0" y="0" width="{width}" height="{height}" />',
        (
            f'  <g id="td1-native-geometry" data-projection="{SVG_PROJECTION}" '
            f'data-primitive-count="{len(scene.primitives)}">'
        ),
    ]
    for primitive, points in projected:
        lines.extend(
            _render_primitive(
                primitive,
                points,
                translate_x=translate_x,
                translate_y=translate_y,
                labels=options.labels_enabled,
            )
        )
    lines.extend(["  </g>", "</svg>", ""])
    svg = "\n".join(lines)
    return SVGRenderArtifact(
        svg=svg,
        scene_digest=scene.digest(),
        metadata_digest=metadata_digest,
        theme=options.theme,
    )
