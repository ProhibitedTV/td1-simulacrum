# TD-1 Simulacrum Architecture

## 1. Scope

The Simulacrum is the executable reference definition of TD-1. It exists to make the machine's behavior precise before physical ternary subsystems are fabricated.

The emulator is not a visual mockup. It is the normative machine model against which later hardware is compared.

## 2. Layering

```text
Veilbreak corpus
      |
      v
Phenomenology model
      |
      v
Glyph + State Weave system
      |
      v
Semantic intermediate representation
      |
      v
12-trit reference machine
      |
      +------> Observer Continuity
      |
      v
Deterministic renderer
```

The arithmetic core must remain independent from the phenomenology and rendering layers.

## 3. Reference machine

Baseline machine parameters:

- radix: balanced ternary
- trit values: `-1`, `0`, `+1`
- machine word: 12 trits
- signed representable range: `-265720` through `+265720`
- general-purpose registers: 9
- initial memory: 729 words
- condition state: negative / zero / positive

### 3.1 Fixed-width arithmetic

Arithmetic wraps modulo `3^12`, mapped back into the symmetric balanced-ternary interval. Negation is exact tritwise sign inversion.

### 3.2 Initial instruction semantics

The first executable model exposes:

`NOP`, `LDI`, `MOV`, `ADD`, `SUB`, `NEG`, `ADDI`, `CMP`, `LD`, `ST`, `BRN`, `BRZ`, `BRP`, `JMP`, `HALT`.

Instruction encoding into a physical 12-trit word is deliberately not frozen by the first software implementation. Execution semantics are frozen first; bit/trit-level encoding will be versioned separately once assembler and hardware requirements converge.

## 4. Semantic layer

TD-1's native operator model is intended to use semantic roots rather than alphabetic text. Candidate roots include:

- OBSERVER
- ORIGIN
- TIME
- REFERENCE
- MOTION
- MEMORY
- LINK
- STATE
- FRAME
- AXIS
- SIGNAL
- COGNITION
- EXECUTION
- TRANSFORM
- ISOLATION
- DOMAIN

Balanced-ternary modifiers alter topology and semantics:

- `-`: reverse / remove / contract / deny
- `0`: inspect / hold / neutral / current
- `+`: forward / acquire / expand / allow

Compound semantic operations are represented as **State Weaves**. The State Weave compiler will lower validated geometric/semantic structures into a stable intermediate representation before translation into machine instructions.

## 5. Glyph encoding

A 12-trit word is naturally partitioned into four 3-trit cells. Each cell has `3^3 = 27` possible states.

TD-1 will therefore define a deterministic 27-form microglyph vocabulary. Four microglyphs reconstruct one complete 12-trit word. Relic Mode may hide the human-readable ternary symbols, but no information may be lost.

## 6. Observer Continuity

Observer Continuity is the permanent background process of TD-1. The software model begins with explicit observer inputs such as:

- timestamp / time standard
- latitude / longitude / altitude
- orientation
- velocity

The subsystem will progress from terrestrial reference frames toward solar-system and astronomical reference frames as the implementation matures.

Rendered motion in the deep field must be driven by actual observer-state changes, not arbitrary animation.

## 7. Operating modes

### Engineering Mode

Exposes registers, machine state, instruction pointer, semantic IR, corpus provenance, diagnostics, and human-readable labels.

### Relic Mode

Displays the same underlying state using only the native TD-1 representation. It must not invent state or hide errors behind decorative behavior.

### Corpus Mode

Explains which versioned phenomenological observations contributed to interface requirements. This mode exists for provenance and research review, not for asserting an external origin for the source reports.

## 8. Hardware replacement model

The emulator should support progressive substitution of physical hardware for emulated components.

Example progression:

```text
emulated register -> physical ternary register
emulated ALU      -> physical ternary arithmetic slice
emulated control  -> physical ternary control board
```

A hardware-backed subsystem is considered conformant only if it reproduces the reference machine's observable state under the same inputs and test vectors.

## 9. Primary engineering rule

**No decorative weirdness.**

Every glyph, transition, braid, pulse, depth change, and topology change should eventually map to an explicit state or event in the system.
