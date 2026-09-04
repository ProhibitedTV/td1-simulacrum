# TD-1 Simulacrum

**Executable reference model and native software environment for TD-1 / The Anomaly.**

TD-1 is a human-built experimental computer centered on physical balanced-ternary computation, a non-text semantic interface, and continuous observer-state modeling. Its interface research is anchored in recurring motifs reported in the Veilbreak phenomenology corpus, while arithmetic, correctness, hardware behavior, and validation remain independent engineering concerns.

> The unusual source may generate the hypothesis. The engineering process determines whether it gets merged.

## What this repository is

`td1-simulacrum` defines the machine before the physical hardware exists. It is intended to become:

- the known-good reference model for the 12-trit TD-1 architecture;
- the assembler/disassembler and deterministic test oracle for physical hardware;
- the semantic State Weave intermediate representation;
- the reversible 27-state microglyph encoding layer;
- the Observer Continuity reference implementation;
- the Veilbreak-derived requirement-provenance model;
- the engineering/relic-mode runtime used to validate the native interaction model.

The long-term target is **hardware parity**: physical TD-1 subsystems should progressively replace emulated subsystems while preserving identical externally observable state.

## Current capabilities

The v0.2 foundation includes:

- balanced ternary conversion and fixed-width arithmetic;
- a deterministic 12-trit, 9-register, 729-word logical machine;
- the initial 15-operation ISA;
- labels, relative branches, assembly and disassembly;
- deterministic machine-state digests for replay and hardware parity;
- reversible `3 trits -> 27 microglyph states` encoding;
- versioned State Weave semantic IR;
- WGS-84 geodetic -> ECEF Observer Continuity groundwork;
- UTC Julian Date and explicitly approximate Earth Rotation Angle;
- corpus/requirement provenance data structures;
- a CLI, examples, unit tests, linting, coverage reporting, and Python-version CI.

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

Inspect the deterministic microglyph IDs for a 12-trit word:

```bash
td1-sim glyph '+0--+000-++0'
```

## Baseline architecture

- Balanced ternary trits: `-1`, `0`, `+1`
- 12-trit machine word
- Signed range: `-265720 .. +265720`
- 9 general-purpose registers
- 729-word initial memory model
- Ternary condition state: negative / zero / positive
- Initial ISA: `NOP`, `LDI`, `MOV`, `ADD`, `SUB`, `NEG`, `ADDI`, `CMP`, `LD`, `ST`, `BRN`, `BRZ`, `BRP`, `JMP`, `HALT`

The physical instruction encoding is **not frozen yet**. Logical execution semantics come first; a 12-trit opcode/register/immediate layout will be versioned once assembler, State Weave, and hardware constraints converge.

## Layering

```text
Veilbreak corpus
      |
      v
phenomenology / provenance model
      |
      v
glyph + State Weave system
      |
      v
semantic IR
      |
      v
12-trit reference machine
      |
      +------> Observer Continuity
      |
      v
deterministic renderer
      |
      v
physical-hardware parity boundary
```

## Design doctrine

1. **No decorative weirdness.** Every visible transition must correspond to real state or a real event.
2. **Veilbreak is an anchor, not an oracle.** Reported phenomenology can generate requirements; it does not define arithmetic or ontology.
3. **Relic and Engineering modes represent the same state.** One is native geometry; one exposes diagnostics.
4. **AI is subordinate.** A cognition layer may propose operations; TD-1 validates and executes them.
5. **Determinism wins.** Same state + same inputs + same corpus revision must produce the same output and geometry.
6. **Accuracy contracts must be explicit.** Approximate calculations are labeled approximate rather than silently promoted to navigation-grade truth.
7. **Hardware earns authority through parity.** A physical subsystem replaces an emulated one only after conformance against the reference model.

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

The next major milestone is to freeze the first semantic and glyph schemas, add deterministic render-state serialization, and define a versioned 12-trit instruction encoding only after those constraints are understood.

See:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/VEILBREAK_PROVENANCE.md`](docs/VEILBREAK_PROVENANCE.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Epistemic boundary

TD-1 does **not** assume that DMT/Veilbreak reports establish extraterrestrial, interdimensional, or otherwise external intelligences. The project treats those reports as a structured phenomenological corpus capable of generating unconventional interface constraints and testable design hypotheses.

**Human-built hardware. Exotic design provenance. Bench validation required.**
