# ADR 0010: Playback consumes state transitions

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 now has deterministic execution traces, render state, native geometry, geometry deltas, and a reference SVG renderer. The next architectural risk is assembling those layers in a frontend that advances frames or animates primitives without preserving a complete audit chain back to logical execution.

A visual player must not become a new source of machine causality.

## Decision

TD-1 will define a versioned `td1.relic-timeline` artifact between execution/geometry truth and playback.

The timeline will contain:

1. frame zero for the exact pre-execution state;
2. exactly one later frame per normative execution event;
3. the full validated `td1.render-state` and `td1.geometry-scene` for every frame;
4. machine, render, scene, program, and execution-trace digests;
5. event/instruction identity for every noninitial frame;
6. an exact `td1.geometry-delta` from each previous scene.

Timeline construction must replay the normative execution trace and reject machine-digest divergence.

Timeline deserialization must rebuild geometry from the embedded render state and frozen geometry profile, verify claimed digests, and recompute every adjacent geometry delta.

The timeline will not define duration, easing, interpolation, camera motion, audio, or speculative in-between machine state.

## Consequences

Positive:

- a future Relic Mode player receives one complete ordered source of truth;
- visible frames can be traced back to exact logical execution events;
- frontend animation can remain expressive without becoming computational authority;
- corpus-backed geometry provenance survives through playback artifacts;
- frame sequences can be rendered reproducibly to SVG, video, WebGL, or physical displays;
- deterministic manifests make visual regression and external review easier.

Costs:

- timeline files are intentionally redundant because each frame carries complete render and geometry state;
- long-running programs can produce large playback artifacts;
- serialization and verification do more work than a lightweight event-only stream;
- temporal presentation remains a separate future design problem.

The redundancy is accepted for pre-alpha work because auditability and debuggability are more valuable than storage efficiency.

## Non-decision

This ADR does not define:

- animation timing;
- easing curves;
- frame-rate policy;
- persistence/ghosting;
- camera behavior;
- audio;
- final art direction;
- hardware display transport;
- physical instruction encoding.

Those decisions must remain downstream of the exact discrete states established here.