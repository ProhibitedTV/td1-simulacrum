# TD-1 Simulacrum

**Executable reference model and native software environment for TD-1 / The Anomaly.**

TD-1 is a human-built experimental computer centered on physical balanced-ternary computation, a non-text semantic interface, and continuous observer-state modeling. Its interface research is anchored in recurring motifs reported in the Veilbreak phenomenology corpus, while arithmetic, correctness, hardware behavior, and validation remain independent engineering concerns.

> The unusual source may generate the hypothesis. The engineering process determines whether it gets merged.

## What this repository is

`td1-simulacrum` defines the machine before the physical hardware exists. It is intended to become:

- the known-good reference model for the 12-trit TD-1 architecture;
- the assembler/disassembler and deterministic test oracle for physical hardware;
- the semantic State Weave intermediate representation;
- the typed compiler boundary from native semantic intent into logical TD-1 instructions;
- the reversible 27-state microglyph encoding layer;
- the Observer Continuity reference implementation;
- the frozen Veilbreak-derived requirement-provenance pipeline;
- the deterministic Engineering/Relic render-state runtime;
- the renderer-independent native geometry contract used by future visual and physical interfaces;
- the replayable transition source for future Relic Mode motion and hardware differential testing;
- the transport-neutral conformance harness that physical ternary hardware must pass before replacing emulation.

The long-term target is **hardware parity**: physical TD-1 subsystems should progressively replace emulated subsystems while preserving identical externally observable state.

## Current capabilities

The v0.8 pre-alpha foundation includes:

- balanced ternary conversion and fixed-width arithmetic;
- a deterministic 12-trit, 9-register, 729-word logical machine;
- the initial 15-operation ISA;
- labels, relative branches, assembly and disassembly;
- deterministic machine-state digests for replay and hardware parity;
- reversible `3 trits -> 27 microglyph states` encoding;
- versioned State Weave semantic IR;
- typed `OperandBindings` separated from semantic identity;
- versioned `td1.semantic-lowering` artifacts with deterministic recompilation checks;
- conservative v1 lowering forms for halt, negate, compare, memory read, and memory write;
- WGS-84 geodetic -> ECEF Observer Continuity groundwork;
- UTC Julian Date and explicitly approximate Earth Rotation Angle;
- versioned, round-trippable `td1.render-state` serialization;
- deterministic Engineering and Relic projections with one shared source digest;
- sparse memory reconstruction and golden render-state fixtures;
- frozen `VB-TD1-*` corpus snapshots with canonical serialization and digests;
- explicit Veilbreak export field mapping that preserves observation vs interpretation;
- versioned motif annotations, snapshot deltas, and strict source-to-requirement traces;
- versioned `td1.geometry-scene` serialization on an integer triangular lattice;
- unique reversible geometry for all 27 microglyph states;
- deterministic 12-trit word, register, memory, machine-control, and State Weave geometry;
- corpus-admitted lattice/depth/multiscale/braiding rules with exact source provenance;
- versioned `td1.execution-trace` with logical program fingerprints and digest-chained events;
- deterministic trace replay with exact register and memory deltas;
- versioned `td1.geometry-delta` with stable-ID transition classifications;
- transport-neutral hardware capability/request/response/report schemas;
- deterministic trit/register and ALU golden vectors;
- explicit hardware `ok`, `unsupported`, `fault`, `timeout`, and `error` outcomes;
- replayable conformance reports with slice-state digests and discrepancy records;
- a reference loopback hardware target for proving the harness before real boards arrive;
- a CLI, examples, golden fixtures, unit tests, linting, coverage reporting, and Python-version CI.

## Quick start

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```

Run the reference program:

```bash
td1-sim run examples/sum.td1
```

Trace every logical instruction transition:

```bash
td1-sim trace examples/sum.td1 > trace.json
```

Replay and verify the saved trace:

```bash
td1-sim trace-verify examples/sum.td1 trace.json
```

List the complete executable State Weave lowering surface:

```bash
td1-sim lowerings
```

Lower native semantic intent into logical TD-1 instructions:

```bash
td1-sim lower 'TRANSFORM:-' --target R2

td1-sim lower 'MEMORY:0' --target R2 --base R0 --offset 8
```

Unsupported State Weaves fail explicitly rather than receiving guessed executable meanings.

Emit the first physical trit/register conformance campaign:

```bash
td1-sim parity-vectors --width 3 --register-only
```

Run the complete parity suite through the reference loopback target:

```bash
td1-sim parity-loopback --width 12
```

Force capability negotiation to reject widths above a simulated 3-trit target:

```bash
td1-sim parity-loopback --width 12 --target-max-width 3
```

Validate and fingerprint a saved conformance report:

```bash
td1-sim parity-verify report.json
```

Inspect the deterministic microglyph IDs for a 12-trit word:

```bash
td1-sim glyph '+0--+000-++0'
```

Emit Engineering Mode state:

```bash
td1-sim render examples/sum.td1 --mode engineering
```

Emit Relic Mode state:

```bash
td1-sim render examples/sum.td1 --mode relic
```

The two render modes must derive from the same immutable render-state digest.

Emit project-native fallback geometry:

```bash
td1-sim geometry examples/sum.td1
```

Admit geometry rules from a frozen corpus snapshot:

```bash
td1-sim geometry examples/sum.td1 \
  --corpus tests/fixtures/corpus_snapshot_v1.json
```

Include a State Weave in the geometry scene:

```bash
td1-sim geometry examples/sum.td1 \
  --weave 'TIME>REFERENCE:+'
```

Compare two saved geometry scenes:

```bash
td1-sim geometry-delta before.geometry.json after.geometry.json
```

Validate a frozen corpus snapshot:

```bash
td1-sim corpus-validate tests/fixtures/corpus_snapshot_v1.json
```

Compare two corpus revisions:

```bash
td1-sim corpus-delta VB-TD1-001.json VB-TD1-002.json
```

## Baseline architecture

- Balanced ternary trits: `-1`, `0`, `+1`
- 12-trit machine word
- Signed range: `-265720 .. +265720`
- 9 general-purpose registers
- 729-word initial memory model
- Ternary condition state: negative / zero / positive
- Initial ISA: `NOP`, `LDI`, `MOV`, `ADD`, `SUB`, `NEG`, `ADDI`, `CMP`, `LD`, `ST`, `BRN`, `BRZ`, `BRP`, `JMP`, `HALT`

The physical instruction encoding is **not frozen yet**. Logical execution semantics, the first native semantic-lowering boundary, and a transport-neutral hardware conformance boundary now exist; the eventual 12-trit opcode/register/immediate layout will be versioned only after compiler and first-hardware constraints are reviewed together.

## Layering

```text
Veilbreak corpus
      |
      v
frozen corpus snapshot / provenance
      |
      v
motif-backed interface requirements
      |
      v
glyph + State Weave system
      |
      v
semantic IR
      |
      v
typed operand binding + lowering
      |
      v
12-trit reference machine ------> execution trace
      |
      +------> Observer Continuity
      |
      v
normative render state
      |
      +------> Engineering projection
      |
      +------> Relic projection
      |
      v
native geometry scene <------ frozen corpus geometry profile
      |
      +------> geometry delta
      |
      v
frontend / physical control surface
      |
      v
transport-neutral parity harness <------ golden vectors
      |
      v
physical ternary subsystem
```

## Design doctrine

1. **No decorative weirdness.** Every visible transition must correspond to real state or a real event.
2. **Veilbreak is an anchor, not an oracle.** Reported phenomenology can generate requirements; it does not define arithmetic or ontology.
3. **Relic and Engineering modes represent the same state.** One is native geometry; one exposes diagnostics.
4. **AI is subordinate.** A cognition layer may propose operations; TD-1 validates and executes them.
5. **Determinism wins.** Same state + same inputs + same corpus revision must produce the same output and geometry.
6. **Accuracy contracts must be explicit.** Approximate calculations are labeled approximate rather than silently promoted to navigation-grade truth.
7. **Hardware earns authority through parity.** A physical subsystem replaces an emulated one only after conformance against the reference model.
8. **The renderer is not a source of truth.** It may decide how state is shown, never what state exists.
9. **Corpus inputs are frozen before use.** A TD-1 revision must be able to identify and reproduce the exact external research input that informed it.
10. **Geometry is a contract, not decoration.** Corpus-derived topology changes require explicit frozen motif evidence and source provenance.
11. **Transitions are traced before they are animated.** A future visual effect must consume real execution or geometry change rather than fabricate activity.
12. **Semantic identity does not hide operands.** Native operations bind concrete machine resources explicitly, and unsupported meanings remain unsupported until engineered.
13. **Physicality is not correctness.** A board advertises only capabilities it has actually demonstrated through the parity harness.

## Assembly example

```asm
LDI R0, 5
LDI R1, 0

loop:
ADD R1, R0
ADDI R0, -1
LDI R2, 0
CMP R0, R2
BRP loop

ST R1, R2, 10
HALT
```

## Repository status

**Pre-alpha / architecture stabilization.**

Machine truth, semantic lowering, frozen corpus provenance, native geometry, deterministic transitions, and transport-neutral physical conformance now have explicit contracts. The next major milestones are the first real one-trit hardware adapter, review of the physical program image/instruction encoding, compound State Weave lowering, corpus-backed morph descriptors, and a reference Relic Mode frontend.

See:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/SEMANTIC_LOWERING.md`](docs/SEMANTIC_LOWERING.md)
- [`docs/HARDWARE_PARITY.md`](docs/HARDWARE_PARITY.md)
- [`docs/RENDER_STATE.md`](docs/RENDER_STATE.md)
- [`docs/GEOMETRY.md`](docs/GEOMETRY.md)
- [`docs/TRACE.md`](docs/TRACE.md)
- [`docs/CORPUS_PIPELINE.md`](docs/CORPUS_PIPELINE.md)
- [`docs/VEILBREAK_PROVENANCE.md`](docs/VEILBREAK_PROVENANCE.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Epistemic boundary

TD-1 does **not** assume that DMT/Veilbreak reports establish extraterrestrial, interdimensional, or otherwise external intelligences. The project treats those reports as a structured phenomenological corpus capable of generating unconventional interface constraints and testable design hypotheses.

The included corpus fixtures are synthetic test data unless explicitly documented otherwise. State Weave lowering mappings are TD-1 engineering conventions unless explicitly documented otherwise. Loopback conformance proves the host harness only; it is not evidence that physical ternary hardware has passed.

**Human-built hardware. Exotic design provenance. Bench validation required.**
