# ADR 0003: One normative render state, multiple projections

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 requires a human-readable Engineering Mode and a native Relic Mode. If each mode is built independently, they can silently diverge, allowing presentation logic to invent or omit machine state.

That would violate the project's primary rule that unusual presentation remain deterministic and inspectable.

## Decision

Introduce a versioned, renderer-independent `td1.render-state` schema.

The schema captures exact machine-visible state, reversible microglyph identity, sparse memory, optional semantic state, and optional Observer Continuity state.

Engineering and Relic modes are projections from the same captured object and carry the same source digest.

Serialized states must be round-trippable and must reconstruct the full machine digest.

Observer quantities used by the renderer are quantized to explicitly scaled integers so cross-mode parity does not depend on floating-point JSON formatting.

## Consequences

Positive:

- Engineering and Relic modes cannot legitimately disagree about underlying state.
- renderer behavior can be regression-tested without a graphical backend;
- future hardware can emit the same render-state contract;
- golden fixtures expose accidental schema drift;
- native visual experiments remain downstream of machine correctness.

Costs:

- schema changes require version discipline;
- duplicated ternary/glyph fields require consistency validation;
- sparse memory representation adds serialization machinery;
- future geometry work must respect the established state identity contract.

## Non-decision

This ADR does not define final microglyph geometry, State Weave topology, color, animation, or the final physical display technology.
