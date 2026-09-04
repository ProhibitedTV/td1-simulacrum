# ADR 0013: Machine state is a separate persistence boundary

- Status: Accepted
- Date: 2026-09-04

## Context

The reference emulator already exposes an exact complete machine-state digest,
and `td1.render-state` can reconstruct a `Machine`. Execution traces therefore
have enough information to replay the logical machine.

However, render state exists for a different architectural purpose. It is the
contract between machine truth and presentation and intentionally contains
renderer-facing redundancy such as glyph IDs. It may also carry State Weave and
Observer inputs that are not part of the logical machine itself.

Using render state as the only persistent checkpoint format would make simple
execution persistence depend on presentation concerns.

## Decision

Introduce versioned `td1.machine-state` as the machine-only persistence
boundary.

Schema v1 records:

- current logical architecture dimensions;
- instruction pointer;
- ternary condition state;
- halt state;
- executed step count;
- all registers;
- sparse exact nonzero memory;
- the existing complete reference-machine digest.

Deserialization reconstructs a `Machine` and requires its complete state digest
to equal the claimed digest.

`MachineState.from_render_state()` exists only as a compatibility bridge. It
restores the validated machine truth from render state and captures a fresh
machine checkpoint. No presentation-only field crosses that boundary.

The checkpoint contains no program image or physical instruction encoding.
Issue #2 remains independently gated on first-hardware constraints.

## Consequences

Logical execution can now be saved, verified, restored, and resumed without
loading rendering, geometry, corpus, or observer data into the persistence
schema.

Future parity/session packaging gains a renderer-independent state artifact.

Render state remains free to evolve for presentation needs without silently
becoming the only disk format for machine truth.

Execution traces remain transition-history artifacts rather than single-state
persistence artifacts.

## Rejected alternatives

### Continue using `td1.render-state` as the checkpoint format

Rejected because it couples logical persistence to presentation redundancy and
optional non-machine inputs.

### Serialize Python `Machine` objects directly

Rejected because implementation object layout is not a versioned interoperable
contract and provides no canonical JSON or migration boundary.

### Include program bytes in machine-state v1

Rejected because physical instruction encoding is intentionally not frozen.
Program-image identity belongs in the future Issue #2 contract, not in a state
format introduced before those hardware constraints are known.

### Serialize all 729 zero/nonzero memory words verbatim

Rejected for v1 because sparse storage is deterministic and lossless: every
omitted address is explicitly defined as the 12-trit zero word. The reconstructed
complete machine digest still proves equivalence with the existing emulator
state contract.
