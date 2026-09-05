# Deterministic Trace Inspection

## Purpose

`td1.execution-trace` already records exact logical instruction transitions. v0.20 adds a time-travel inspection layer that reconstructs logical machine truth at any trace boundary without rerunning source code and without promoting debugger state into machine semantics.

The rule is simple:

> A debugger may inspect recorded truth. It may not invent new truth.

## Trace boundaries

For a trace containing `N` events there are `N + 1` inspectable boundaries:

```text
position 0       initial machine state
position 1       after event 0
position 2       after event 1
...
position N       final machine state
```

`trace_state_at(trace, position)` starts from the validated initial render-state restore boundary and applies the recorded register, memory, instruction-pointer, condition, halt, and step changes through the requested position.

The returned artifact is an ordinary `td1.machine-state` checkpoint.

## Delta validation

Time travel does not trust trace deltas merely because they are present in a valid JSON object.

For every traversed event the inspector requires:

1. the reconstructed machine digest equals `before_digest`;
2. instruction pointer, ternary condition, halt state, and step relationship match the event's recorded before-side control state;
3. every register/memory delta's recorded `before` value equals the reconstructed machine value;
4. the delta's ternary `after` value parses successfully;
5. after all data/control changes are applied, the complete machine digest equals `after_digest`.

This makes omitted, substituted, reordered, or corrupted state changes fail during reconstruction.

The trace remains the source artifact. The inspector is a deterministic verifier/consumer of that artifact.

## TraceCursor

`TraceCursor` is a small seekable view over immutable trace boundaries.

It supports:

- `state()` — exact `td1.machine-state` at the current boundary;
- `seek(position)` — jump to any valid boundary;
- `step_forward()` — move one event later;
- `step_backward()` — move one event earlier;
- `at_start` / `at_end` boundary checks.

Backward movement does not reverse-execute a synthetic inverse instruction. The cursor deterministically reconstructs the requested earlier boundary from trace truth. That distinction keeps reverse inspection independent from opcode-specific undo logic.

## Deterministic queries

`TraceQuery` searches existing execution events. Query groups are ANDed; values inside one group are ORed.

Supported criteria:

- logical instruction index;
- logical opcode;
- touched register;
- touched memory address;
- ternary condition-state change;
- transition into HALT.

Example meaning:

```text
operations = [ADD, SUB]
registers = [R1]
```

matches events that are either `ADD` or `SUB` **and** changed R1.

Query results preserve original trace order and contain the original `ExecutionEvent` objects. No derived execution event is inserted.

## CLI

v0.20 exposes trace inspection as a separate command so the ordinary execution CLI remains focused on running the reference machine:

```bash
td1-sim trace examples/sum.td1 > sum.trace.json
```

Reconstruct the exact machine after five logical events:

```bash
td1-trace state sum.trace.json --position 5
```

Write that checkpoint to disk:

```bash
td1-trace state sum.trace.json \
  --position 5 \
  --output step5.machine.json
```

Find every `ADD` that changes R1:

```bash
td1-trace find sum.trace.json --op ADD --register R1
```

Find writes to memory word 10:

```bash
td1-trace find sum.trace.json --memory 10
```

Find events that change the ternary condition state:

```bash
td1-trace find sum.trace.json --condition-change
```

Find the transition into HALT:

```bash
td1-trace find sum.trace.json --halt-transition
```

## Authority boundary

Trace inspection proves only what the saved logical trace and its digests support.

It does **not**:

- add a new logical instruction;
- define physical instruction encoding;
- claim cycle timing;
- claim a physical board executed the trace;
- add wall-clock state;
- alter parity-wire evidence;
- permit a renderer to override machine truth.

A reconstructed checkpoint is logical machine truth only because every traversed transition reproduces the trace's existing complete machine-state digest chain.

## Design rule

**Time travel is reconstruction, not retroactive execution.**
