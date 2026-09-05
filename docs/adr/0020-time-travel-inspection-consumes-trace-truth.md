# ADR 0020 — Time-travel inspection consumes trace truth

Status: Accepted

## Context

TD-1 now has deterministic execution traces containing exact before/after machine digests, logical instruction identity, control-state changes, and register/memory deltas. Engineers need to inspect earlier execution states, search for relevant mutations, and move backward through an execution without rerunning an interactive debugger with hidden mutable state.

A conventional debugger could become a second execution authority if it maintained its own undo semantics, private snapshots, wall-clock events, or frontend-only state transitions.

## Decision

Time-travel inspection is downstream of `td1.execution-trace`.

An inspector reconstructs a requested trace boundary from the validated initial state plus recorded deltas and requires every traversed event to reproduce its existing complete before/after machine digest chain.

Reverse movement is implemented by deterministic reconstruction of an earlier boundary, not by defining inverse opcodes or reverse-executing synthetic instructions.

Trace queries select existing events only. They do not create new execution events.

The reconstructed output state is the existing `td1.machine-state` schema rather than a new debugger-specific machine-state format.

## Consequences

Positive:

- arbitrary trace boundaries become directly inspectable;
- reverse inspection requires no opcode-specific undo semantics;
- corrupted or incomplete deltas fail against complete machine digests;
- machine-state persistence remains the only logical checkpoint format;
- query/debug tooling cannot silently redefine execution truth;
- no physical instruction encoding or timing decision is introduced.

Negative:

- seeking currently reconstructs from the trace initial state and is O(N) in the requested position;
- interactive debugging of a non-terminating program before a complete trace exists remains a separate future problem;
- traces must retain enough exact state-transition evidence for reconstruction.

## Rejected alternatives

### Store debugger snapshots after every event

Rejected because it duplicates machine-state truth, enlarges trace artifacts, and creates another persistence surface that can drift.

### Reverse-execute each logical opcode

Rejected because inverse execution introduces a second semantic implementation and is awkward or ambiguous for stores, branches, and future side effects.

### Let the browser/Relic player own rewind state

Rejected because presentation is downstream of machine truth and may not fabricate or persist logical execution state.

## Rule

**Time travel is reconstruction from trace truth, not a second execution engine.**
