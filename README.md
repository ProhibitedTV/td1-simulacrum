# TD-1 Simulacrum

**Reference emulator and native software environment for TD-1 / The Anomaly.**

TD-1 is a human-built experimental computing project centered on physical balanced-ternary computation, a non-text semantic interface, and continuous observer-state modeling. The interface research is anchored in recurring motifs reported in the Veilbreak phenomenology corpus, but the software and hardware are engineered and validated independently of any claim about the ontology of those reports.

> The unusual source may generate the hypothesis. The engineering process determines whether it gets merged.

## Purpose

`td1-simulacrum` defines the machine before the physical hardware exists. It is intended to become:

- the known-good reference model for the 12-trit TD-1 architecture;
- the assembler/disassembler and deterministic test oracle for physical hardware;
- the semantic State Weave compiler and glyph-state model;
- the Observer Continuity reference implementation;
- the Veilbreak-derived interface-provenance layer;
- the engineering/relic-mode runtime used to validate the native interaction model.

The long-term goal is hardware parity: physical TD-1 subsystems should progressively replace emulated subsystems while preserving identical externally observable machine state.

## Baseline architecture

- Balanced ternary trits: `-1`, `0`, `+1`
- 12-trit machine word
- 9 general-purpose registers
- 729-word initial memory model
- Ternary condition state: negative / zero / positive
- Instruction format target: 3-trit opcode, 2-trit register A, 2-trit register B, 5-trit signed immediate/relative field
- Initial ISA: `NOP`, `LDI`, `MOV`, `ADD`, `SUB`, `NEG`, `ADDI`, `CMP`, `LD`, `ST`, `BRN`, `BRZ`, `BRP`, `JMP`, `HALT`

## Design doctrine

1. **No decorative weirdness.** Every visible state transition must correspond to real machine state.
2. **Veilbreak is an anchor, not an oracle.** Reported phenomenology informs interface requirements; it does not define arithmetic or override testing.
3. **Relic mode and engineering mode represent the same state.** One is native geometric representation; the other exposes human-readable diagnostics.
4. **AI is subordinate.** A cognition layer may propose semantic operations, but TD-1 validates and executes them.
5. **Determinism wins.** Same machine state + same inputs + same corpus revision must produce the same output and geometry.

## Planned layers

```text
Veilbreak corpus -> phenomenology model -> glyph / State Weave layer
                                              |
                                              v
                                     semantic intermediate form
                                              |
                                              v
                                     balanced-ternary machine
                                              |
                                              v
                                     Observer Continuity
                                              |
                                              v
                                      deterministic renderer
```

## Repository status

**Bootstrap / pre-alpha.** The first milestone is a rigorously tested reference implementation of balanced-ternary arithmetic and the 12-trit CPU model. The visual and corpus-derived layers will be built on top rather than baked into the arithmetic core.

## Epistemic boundary

TD-1 does **not** assume that DMT/Veilbreak reports establish extraterrestrial, interdimensional, or otherwise external intelligences. The project treats those reports as a structured phenomenological corpus that can generate unconventional interface constraints and testable design hypotheses.

Human-built hardware. Exotic design provenance. Bench validation required.
