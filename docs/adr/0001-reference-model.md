# ADR-0001: The emulator is the normative TD-1 reference model

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 is intended to transition from software modeling to physical balanced-ternary hardware. Without a normative reference, hardware behavior can drift and visual layers can accidentally redefine semantics.

## Decision

`td1-simulacrum` is the executable reference definition of TD-1 behavior.

Physical subsystems replace emulated subsystems only after differential/parity testing against the same inputs and golden vectors.

## Consequences

- hardware can evolve without redefining machine semantics;
- deterministic replay becomes a first-class requirement;
- state serialization and parity digests matter early;
- visual and phenomenological layers cannot override arithmetic correctness.
