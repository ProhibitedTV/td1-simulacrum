# TD-1 Machine-State Checkpoints

## Purpose

`td1.machine-state` is the standalone persistence contract for logical TD-1
execution state.

It exists because `td1.render-state` has a different job: render state is the
contract between machine truth and presentation. It contains renderer-facing
redundancy such as microglyph IDs and may carry semantic or Observer state.
Those fields should not be required merely to save and resume the logical
machine.

The checkpoint rule is:

> Machine persistence contains machine truth only.

## Schema

Schema v1 is:

```text
td1.machine-state / v1
```

A checkpoint records the architecture invariants explicitly:

- `word_width = 12`;
- `register_count = 9`;
- `memory_words = 729`.

It then records the complete logical state:

- instruction pointer;
- ternary condition state (`-1`, `0`, `+1`);
- halted flag;
- executed step count;
- all nine 12-trit register words;
- every nonzero memory word using sparse `(address, ternary)` records;
- the existing complete reference-machine `machine_digest`.

Zero memory is implicit. The sparse form is lossless because all omitted cells
are defined to be the 12-trit zero word.

## Integrity and validation

Construction and deserialization reject:

- unsupported schema/version values;
- architecture metadata that differs from the current TD-1 logical machine;
- condition values outside `-1/0/+1`;
- negative step counts;
- the wrong number of registers;
- register or memory words with a width other than 12 trits;
- zero-valued entries in the `nonzero_memory` list;
- duplicate or out-of-range memory addresses;
- malformed claimed SHA-256 machine digests;
- any checkpoint whose reconstructed `Machine` does not reproduce the claimed
  complete machine-state digest.

The checkpoint itself also has a SHA-256 digest over canonical JSON. The two
digests serve different purposes:

- `machine_digest` fingerprints the reference machine's observable state using
  the existing emulator digest contract;
- the checkpoint digest fingerprints the complete versioned serialized
  `td1.machine-state` artifact, including schema and architecture metadata.

Neither digest is an authentication signature.

## Capture and restore

Python:

```python
state = MachineState.capture(machine)
restored = state.restore_machine()
```

The restored machine must reproduce the original complete state digest exactly.

A validated `RenderState` can be reduced back to the standalone persistence
boundary:

```python
checkpoint = MachineState.from_render_state(render_state)
```

This bridge restores the machine truth and captures it again. It intentionally
does **not** copy glyph IDs, render planes, State Weaves, Observer values,
geometry, corpus information, or presentation state into the checkpoint.

## CLI

Capture the final state of a program:

```bash
td1-sim machine-state examples/sum.td1 --output final.machine.json
```

Capture an intermediate checkpoint after exactly four executed instructions, or
earlier if the program has already halted:

```bash
td1-sim machine-state examples/sum.td1 \
  --after-steps 4 \
  --output step4.machine.json
```

Validate and fingerprint a saved checkpoint:

```bash
td1-sim machine-state-verify step4.machine.json
```

Resume the same logical program from that checkpoint:

```bash
td1-sim machine-state-resume examples/sum.td1 step4.machine.json \
  --output resumed.machine.json
```

`--max-additional-steps` is a safety bound on resumed execution. It is added to
the step count already stored in the checkpoint before calling the reference
machine's deterministic run loop.

## Program independence

A machine checkpoint does not contain a program image or program digest.

That separation is deliberate. `td1.machine-state` answers:

> What is the complete logical state of this machine?

It does not answer:

> Which physical instruction words are loaded, and how are they encoded?

The versioned program-image and physical instruction-encoding work remains
Issue #2 and is still gated on first-hardware measurements. Machine-state
serialization does not freeze that encoding by implication.

A caller that resumes a checkpoint against a source program is responsible for
selecting the intended program. Future program-image work can bind program and
machine-state artifacts explicitly once the physical encoding constraints are
known.

## Relationship to other contracts

```text
Machine
  |
  +------> td1.machine-state ------> save / verify / restore / resume
  |
  +------> td1.render-state -------> geometry / Engineering / Relic presentation
  |
  +------> td1.execution-trace ----> deterministic transition history
```

The machine-state checkpoint is not a replacement for either render state or an
execution trace:

- render state includes deterministic presentation inputs;
- execution trace records how state changed over time;
- machine state records one exact logical checkpoint.

## Future use

The checkpoint contract is intended to become a clean handoff point for:

- trace session packaging;
- emulator/hardware differential tests;
- physical-subsystem replacement gates;
- deterministic crash/restart tests;
- future program-image bundles after Issue #2 is ready.

Physical hardware still earns authority through parity. A serialized checkpoint
being valid does not mean any physical ternary board has reproduced it.
