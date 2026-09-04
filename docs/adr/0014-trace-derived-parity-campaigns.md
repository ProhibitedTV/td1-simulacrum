# ADR 0014 — Trace-Derived Parity Campaigns Test Subsystems, Not Instruction Decode

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 already has three distinct contracts:

1. `td1.execution-trace` records exact logical machine transitions;
2. `td1.machine-state` persists exact logical execution state;
3. the transport-neutral parity layer tests advertised ternary subsystem operations such as register load, negate, add, and subtract.

The missing boundary was a deterministic way to turn values encountered during a real logical workload into a reproducible physical conformance campaign.

It would be easy to overstate what such a campaign proves. TD-1 does not yet have a frozen physical instruction encoding, instruction-fetch implementation, or physical decoder. Therefore a trace-derived test must not imply that a board executed the original logical instruction.

## Decision

Introduce versioned `td1.parity-campaign` artifacts derived deterministically from one validated logical execution trace.

A campaign may map a logical event to an existing parity operation only when that mapping is faithful at the **subsystem-operation** level.

Current v1 mappings are:

- `LDI` -> `register_load` using the traced destination value;
- `MOV` -> `register_load` using the traced source value;
- `LD` -> `register_load` using the traced destination value;
- `NEG` -> `negate` using the traced pre-event operand;
- `ADD` -> `add` using the two traced pre-event operands;
- `SUB` -> `sub` using the two traced pre-event operands;
- `ADDI` -> `add` using the traced target value plus the immediate represented as a fixed-width 12-trit word.

The `ADDI` mapping is explicitly labeled as a subsystem-level ALU test. It does not test or claim physical decoding of an `ADDI` instruction.

Logical events without a faithful existing parity operation are omitted rather than approximated. This includes v1 control-flow, compare, store, no-op, and halt semantics.

Each campaign embeds:

- the complete source execution trace;
- exact initial/final `td1.machine-state` checkpoints;
- deterministic trace-derived parity entries;
- the exact `ParityVector` for each entry;
- a deterministic vector-set digest.

Deserialization recomputes campaign entries from the embedded trace. Serialized mappings therefore cannot silently redefine themselves.

A second versioned artifact, `td1.parity-campaign-run`, binds one exact campaign to one exact `td1.parity-report` and requires the report vectors to equal the campaign vectors in order.

The physical/parity workflow is exposed through a dedicated `td1-parity` CLI so the normal emulator CLI does not become the authority for physical test semantics.

## Consequences

### Positive

- Real software workloads now generate reproducible physical subsystem vectors.
- Loop iterations and repeated values remain individually traceable through event-indexed vector IDs.
- Initial/final machine checkpoints make the workload boundary explicit.
- A conformance report can be tied to the exact logical execution that motivated it.
- Unsupported semantics remain visibly unsupported.
- The same campaign can later run through serial, USB, GPIO, or other transports without changing campaign semantics.

### Costs

- Campaign artifacts are intentionally verbose because they embed trace and checkpoint provenance.
- Some logical instructions produce no campaign vector until the parity surface grows.
- Passing a campaign proves only the advertised subsystem operations represented by its vectors.

## Issue #2 boundary

This decision does **not** define physical instruction words, a program-image format, instruction fetch, instruction decode, or the target opcode/register/immediate bit/trit allocation.

The proposed 12-trit physical layout remains deferred until first-hardware measurements and explicit encoding review.

A board passing a trace-derived campaign may truthfully claim conformance for those tested ternary subsystem operations. It may not claim to have physically executed the source TD-1 program unless a future physical execution contract separately proves that capability.
