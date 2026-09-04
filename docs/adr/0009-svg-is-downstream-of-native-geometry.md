# ADR 0009: SVG presentation is downstream of native geometry

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 now has a deterministic `td1.geometry-scene` contract and deterministic geometry-transition deltas. A visible reference renderer is needed so the native representation can be inspected without allowing frontend code to become an alternate source of machine truth.

If a renderer reads machine registers directly, queries the Veilbreak corpus itself, or reconstructs semantics from ad-hoc UI rules, Engineering and Relic frontends can drift away from the same underlying state. If output includes timestamps, random IDs, or environment-dependent layout, frontend regression testing also becomes difficult.

## Decision

The first reference renderer will consume only a validated `GeometryScene` and emit deterministic standalone SVG.

The renderer will:

- preserve primitive identity, primitive membership, topology, and geometry metadata;
- use a versioned deterministic integer projection from axial `(q,r,z)` coordinates;
- embed geometry/render/machine provenance digests in SVG metadata;
- produce byte-identical output for identical scene and renderer options;
- provide Relic and Engineering presentation themes that share the same projected geometry;
- keep Relic output free of visible English text by default;
- derive Engineering labels only from existing primitive IDs and roles;
- XML-escape external text and deterministically encode arbitrary primitive IDs into safe SVG element IDs.

Projection, palette, stroke weight, node radius, margin, and label visibility are explicitly presentation choices. They do not carry machine semantics unless a future version documents such a mapping in a separate contract.

## Consequences

Positive:

- the native geometry contract becomes visually inspectable;
- frontend code cannot silently invent machine state;
- Relic and Engineering views can be compared for primitive/coordinate equivalence;
- SVG output is suitable for deterministic fixtures, browser inspection, documentation, and later visual regression tooling;
- future WebGL/physical-display renderers have a concrete reference implementation without being forced to copy its art direction.

Costs:

- renderer input requires a geometry-scene serialization step;
- the first SVG styling is intentionally conservative rather than final art direction;
- depth is projected into 2-D rather than rendered as a true 3-D scene;
- animation remains a separate later layer consuming geometry deltas.

## Non-decision

This ADR does not define final glyph art, animation timing, shaders, camera movement, sound, interaction, hit testing, WebGL architecture, or physical display hardware.
