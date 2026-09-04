# Deterministic Transition Trace

## Purpose

TD-1 must eventually move, morph, braid, and transition in Relic Mode without turning presentation code into a source of fictional activity.

The transition-trace layer records **what changed**. It deliberately does not specify animation duration, easing, color, sound, camera motion, or visual drama.

> State changes first. Animation follows.

## Logical execution trace

Schema:

```text
td1.execution-trace / v1
```

An execution trace records one complete logical program run using the current reference-machine semantics.

The trace includes:

- a SHA-256 digest of the logical instruction sequence;
- exact initial and final `td1.render-state` snapshots;
- one event per executed logical instruction;
- before/after full machine-state digests;
- instruction pointer and ternary condition transitions;
- halt-state transitions;
- changed registers only;
- changed memory words only.

The program digest fingerprints logical instruction semantics:

```text
(op, a, b, imm)
```

It does **not** assign or freeze a physical 12-trit instruction encoding. Issue #2 remains the authority for that future decision.

## Replay verification

`verify_execution_trace()` restores the captured initial machine state, re-executes the same logical program, and requires the complete canonical trace to match.

This makes the trace useful for:

- regression testing;
- debugging;
- future hardware differential testing;
- proving that a frontend transition came from actual execution;
- preserving deterministic demonstrations.

The first implementation compares the full 729-word reference memory before and after every step. That is intentionally simple and auditable. It can be optimized later without changing the schema contract.

## Geometry delta

Schema:

```text
td1.geometry-delta / v1
```

A geometry delta compares two `td1.geometry-scene` snapshots using stable primitive IDs.

Each changed primitive is classified as:

- `appear` — primitive exists only in the new scene;
- `disappear` — primitive exists only in the old scene;
- `move` — identical primitive metadata and topology translated uniformly in `(q,r,z)`;
- `topology` — points/topology changed in a non-translation way, or geometry and metadata changed together;
- `metadata` — points remained identical but represented metadata changed.

The delta preserves:

- before/after geometry-scene digests;
- before/after source render-state digests;
- complete before/after primitive records for every classified change.

No animation timing is embedded.

## Why stable primitive IDs matter

A frontend can now consume:

```text
execution trace
    -> render states
        -> geometry scenes
            -> geometry deltas
                -> visual transition
```

without guessing whether a shape is the same conceptual object across frames.

For example, `machine.r0.g3.trit1` remains the same primitive identity even when its position changes because a corpus-backed layout rule moves the register plane.

## CLI

Emit a deterministic logical execution trace:

```bash
td1-sim trace examples/sum.td1 > trace.json
```

Verify the trace by replaying it:

```bash
td1-sim trace-verify examples/sum.td1 trace.json
```

Compare two saved geometry scenes:

```bash
td1-sim geometry-delta before.geometry.json after.geometry.json
```

## Relationship to physical hardware

Execution trace v1 records the emulator's logical reference behavior. It is not yet a hardware transport.

When Issue #5 introduces the emulator-to-hardware parity protocol, hardware observations can be compared against these same logical transitions and machine digests. Physical timing, analog voltage behavior, and device faults belong to the parity/conformance layer rather than being silently mixed into logical execution semantics.

## Deferred work

This revision intentionally does not define:

- physical instruction words;
- cycle-accurate timing;
- animation duration or interpolation;
- sound cues;
- corpus-derived morph timing;
- focus-through transitions;
- temporal persistence/ghosting;
- hardware transport packets.

Those can now be designed against a deterministic event source rather than an animation loop.
