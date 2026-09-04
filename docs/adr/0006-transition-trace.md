# ADR 0006: Trace state transitions before animating them

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 now has deterministic machine state, render state, frozen corpus provenance, and native geometry. The next implementation risk is adding animation directly in a frontend. If a frontend decides when a glyph appears, how geometry morphs, or which structure moved without a normative state-change record, presentation becomes an alternate source of machine behavior.

The project also needs replayable transition data for future emulator-versus-hardware conformance work.

## Decision

TD-1 will define two versioned transition contracts before implementing native animation:

1. `td1.execution-trace` records one logical instruction transition at a time, including before/after machine digests and exact register/memory deltas.
2. `td1.geometry-delta` classifies stable-ID geometry changes as appear, disappear, move, topology, or metadata changes.

Logical program traces fingerprint `(op, a, b, imm)` semantics without assigning physical instruction words.

Execution traces must be replay-verifiable from their captured initial state. Geometry deltas must preserve the before/after geometry digests and source render-state digests.

Neither schema will encode arbitrary animation duration, easing, color, sound, or camera behavior.

## Consequences

Positive:

- future Relic Mode animation has a deterministic source of events;
- a visual transition can be traced back to exact machine execution;
- logical replay can catch nondeterminism or accidental state drift;
- stable geometry IDs make scene changes classifiable across frontends;
- future physical parity tooling can reuse the same logical transition records.

Costs:

- reference tracing currently snapshots and compares full memory every step;
- the project maintains two additional versioned schemas;
- frontend development must consume trace/delta contracts instead of inventing convenient effects locally.

## Non-decision

This ADR does not freeze physical opcode encoding, cycle timing, animation timing, visual style, audio, hardware transport, or corpus-derived morph behavior.
