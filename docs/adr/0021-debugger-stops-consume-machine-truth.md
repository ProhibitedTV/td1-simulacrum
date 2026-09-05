# ADR 0021: Debugger stops consume machine truth

## Status

Accepted.

## Context

After exact trace time-travel inspection, the emulator needs a way to stop live execution on useful engineering conditions, including non-terminating programs. A conventional debugger can easily become a second source of execution state by mutating registers, inventing breakpoint opcodes, or maintaining debugger-owned snapshots that diverge from the reference machine.

TD-1 already has a stronger authority chain:

`Machine.step()` -> `ExecutionEvent` -> digest-linked `td1.execution-trace` -> downstream inspection/presentation.

Live debugging should extend that chain rather than fork it.

## Decision

Introduce one incremental `TraceRecorder` around the reference `Machine`. Complete tracing and debugger execution both use this recorder, so event construction is shared.

A debugger run is a versioned `td1.debug-run` containing:

- the exact `td1.execution-trace` prefix produced by executed instructions;
- a deterministic stop specification;
- a stop kind;
- matched breakpoint/watchpoint labels when applicable;
- a deterministic event budget and initial-breakpoint continuation policy.

Instruction-index and opcode breakpoints are evaluated **before** execution. Register and memory watchpoints are evaluated **after** the real event that changed those locations.

A debugger pause is not a TD-1 machine event. No breakpoint opcode is added to the ISA. The machine state at a stop is exactly the final state of the embedded trace prefix.

`td1.execution-trace` is explicitly permitted to represent a complete halted execution or an exact non-halted prefix. Replay verification executes exactly the recorded event count and requires canonical equality.

## Consequences

### Positive

- normal tracing and debugging cannot silently disagree about event construction;
- non-terminating programs can be inspected without treating the host event budget as machine HALT;
- breakpoint-before and watchpoint-after semantics are explicit and testable;
- every debugger stop retains the existing machine digest chain;
- debugger artifacts are deterministic and replayable;
- future checkpoint continuation can reuse ordinary machine-state artifacts.

### Costs

- debugger metadata is a separate artifact layer that must be versioned and validated;
- continuation from a checkpoint already positioned on a breakpoint needs an explicit one-boundary skip policy;
- asynchronous/interactive physical debugging remains intentionally undefined.

## Rejected alternatives

### Add a BREAK instruction

Rejected because it would change logical ISA semantics merely to satisfy host tooling.

### Maintain debugger-owned mutable register/memory state

Rejected because it creates a competing source of machine truth.

### Reverse-execute instructions for stepping backward

Rejected. Existing time-travel inspection reconstructs earlier states from recorded trace truth instead of inventing inverse semantics.

### Use wall-clock timeouts as normative stops

Rejected because wall-clock scheduling is host behavior and would make artifacts nondeterministic. Event budgets are deterministic.

## Boundary

This ADR defines host-side logical debugging only. It does not define physical debug transport, hardware breakpoint circuitry, UART/JTAG commands, cycle timing, physical instruction encoding, or electrical behavior.
