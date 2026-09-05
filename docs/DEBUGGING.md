# Deterministic debugging

TD-1 debugging is downstream of the reference machine, not a second execution authority.

The debugger observes ordinary `Machine.step()` transitions through the same incremental `TraceRecorder` used by complete execution tracing. Every instruction that executes becomes an ordinary `ExecutionEvent`; a debugger stop therefore ends at an exact `td1.execution-trace` boundary.

## Stop semantics

`DebugStopSpec` contains two kinds of stop condition:

- instruction-index and opcode **breakpoints** are checked before the next logical instruction executes;
- register and memory **watchpoints** are checked after the event that actually changed the watched state.

A `td1.debug-run` records one of four stop kinds:

- `halted` — the reference machine executed `HALT`;
- `breakpoint` — the next instruction matched a configured pre-execution breakpoint;
- `watchpoint` — the just-recorded event changed configured machine state;
- `event_budget` — the deterministic continuation budget was exhausted while the machine remained live.

Breakpoints and watchpoints do not become machine events. They do not change the instruction pointer, ternary condition state, registers, memory, step counter, or HALT state.

## Trace prefixes

`td1.execution-trace` can represent either a complete halted execution or an exact non-halted prefix. `verify_execution_trace()` replays exactly the recorded event count and requires canonical equality, so debugger prefixes are verified without pretending that a pause is a machine HALT.

This is intentional. The debugger does not synthesize a `BREAK` instruction and does not mutate the TD-1 ISA.

## CLI

Stop before instruction index 4:

```bash
td1-debug run examples/sum.td1 --break-ip 4 --output sum.debug.json
```

Stop before any `ST` instruction:

```bash
td1-debug run examples/sum.td1 --break-op ST --output before-store.debug.json
```

Stop after R1 actually changes:

```bash
td1-debug run examples/sum.td1 --watch-register R1 --output r1.debug.json
```

Stop after memory word 10 changes:

```bash
td1-debug run examples/sum.td1 --watch-memory 10 --output memory10.debug.json
```

Bound a potentially non-terminating continuation:

```bash
td1-debug run program.td1 --max-events 1000 --output bounded.debug.json
```

Verify the entire program/trace/stop decision deterministically:

```bash
td1-debug verify examples/sum.td1 sum.debug.json
```

A `td1.machine-state` checkpoint can be supplied with `--checkpoint`. When resuming from a checkpoint that is already sitting on a configured breakpoint, `--skip-initial-breakpoint` permits one continuation past that initial boundary before ordinary breakpoint evaluation resumes.

## Authority boundary

The following are authoritative machine facts:

- `Machine.step()` semantics;
- the resulting machine state;
- the `ExecutionEvent` generated from that real transition;
- the digest-linked execution-trace prefix.

The following are debugger metadata only:

- breakpoint/watchpoint configuration;
- stop kind;
- matched stop labels;
- event budget;
- `skip_initial_breakpoint` continuation policy.

Debugger metadata may explain why host execution paused. It may not fabricate a machine transition.

## Explicit non-goals

This layer does not define:

- reverse instructions or reverse execution semantics;
- a TD-1 breakpoint opcode;
- wall-clock timing or cycle timing;
- physical instruction encoding;
- physical debug pins, JTAG-like transport, UART commands, or hardware probe behavior;
- asynchronous host interrupts;
- debugger-owned register or memory truth.

If a future physical target gains debug transport, that transport must still reconcile to the same logical machine/trace contracts rather than silently becoming another source of truth.
