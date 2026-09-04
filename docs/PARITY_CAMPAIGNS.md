# Trace-Derived Parity Campaigns

`td1.parity-campaign` packages subsystem conformance vectors encountered during one deterministic TD-1 logical execution.

The campaign layer exists between execution tracing and the transport-neutral parity harness:

```text
TD-1 program
   |
   v
logical execution trace
   |
   +----> initial/final td1.machine-state checkpoints
   |
   v
trace-derived subsystem mappings
   |
   v
td1.parity-campaign
   |
   v
ParityTransport / capability negotiation
   |
   v
td1.parity-report
   |
   v
td1.parity-campaign-run
```

## What a campaign proves

A campaign answers a narrow engineering question:

> Can a physical subsystem correctly perform the same low-level ternary operation on values that the logical machine actually encountered during this execution?

It does **not** prove:

- physical instruction fetch or decode;
- physical branch/control-flow behavior;
- a frozen 12-trit instruction encoding;
- memory-board parity for `LD`/`ST`;
- that unsupported hardware capabilities exist.

## Deterministic mappings

Campaign v1 derives vectors only where the existing parity surface has a faithful subsystem-level operation.

| Logical event | Parity operation | Meaning |
| --- | --- | --- |
| `LDI` | `register_load` | reproduce the register value written by the event |
| `MOV` | `register_load` | reproduce the transferred source-register value |
| `LD` | `register_load` | reproduce the value written into the destination register |
| `NEG` | `negate` | apply ternary negation to the traced pre-event operand |
| `ADD` | `add` | add the two traced pre-event register operands |
| `SUB` | `sub` | subtract the two traced pre-event register operands |
| `ADDI` | `add` | represent the immediate as a fixed-width 12-trit word and test ALU addition |

The `ADDI` mapping is explicitly **subsystem-level**. It does not claim that physical hardware decoded an `ADDI` instruction.

`NOP`, `CMP`, `ST`, branch operations, `JMP`, and `HALT` do not generate v1 campaign vectors because the current parity operation surface has no faithful equivalent for those semantics.

## Entry provenance

Every `TraceParityEntry` preserves:

- execution event index;
- machine step;
- executed instruction index;
- logical operation name;
- destination register;
- before/after complete machine digests;
- deterministic mapping label;
- rationale;
- exact `ParityVector`.

Vector IDs include the execution event index, so repeated loop iterations remain distinct even when they exercise identical values.

## Trace reconstruction

Campaign derivation walks the trace's register deltas from the exact initial render-state register values.

For each event it requires every recorded `RegisterDelta.before` to equal the currently reconstructed value before applying the delta. At the end, reconstructed registers must equal the trace's final register state.

For mapped operations, the parity vector's deterministic expected result must equal the traced destination register after the event. A mismatch fails campaign construction.

## Checkpoint linkage

A campaign embeds exact initial and final `td1.machine-state` checkpoints derived from the source trace.

Campaign validation rebuilds those checkpoints from the embedded trace and requires canonical equality. This prevents presentation fields from leaking into parity packaging and prevents checkpoint drift from being hidden behind matching metadata.

## Canonical artifact

`td1.parity-campaign` includes:

- complete source `td1.execution-trace`;
- trace digest;
- initial/final machine checkpoints and checkpoint digests;
- all deterministic trace-derived entries;
- entry count;
- vector-set digest.

Loading a saved campaign recomputes the deterministic entries from the embedded trace. A serialized campaign cannot redefine its own mapping rules.

## Campaign runs

`td1.parity-campaign-run` joins one complete campaign with one `td1.parity-report`.

Validation requires:

- report vector-set digest equals campaign vector-set digest;
- report request vectors exactly equal campaign vectors in order;
- claimed campaign/report digests match reconstructed artifacts.

A campaign run therefore preserves both sides of the experiment: the exact logical workload-derived oracle and the observed target response.

## CLI

Build a campaign from a real logical program execution:

```bash
td1-parity build examples/sum.td1 --output sum.campaign.json
```

Verify/reconstruct the saved campaign:

```bash
td1-parity verify sum.campaign.json
```

Run it through the reference loopback target:

```bash
td1-parity loopback sum.campaign.json --output sum.run.json
```

Exercise capability rejection deliberately:

```bash
td1-parity loopback sum.campaign.json --target-max-width 3
```

Verify a saved campaign-run artifact:

```bash
td1-parity run-verify sum.run.json
```

The loopback target proves the host campaign/harness path. It is not evidence that physical ternary hardware has passed.

## Issue #2 boundary

Campaigns contain logical operations, ternary operands, expected subsystem results, and machine-state provenance. They contain **no physical instruction words**.

The target `[opcode:3][A:2][B:2][imm:5]` layout remains unfrozen until first hardware constraints are measured and reviewed.
