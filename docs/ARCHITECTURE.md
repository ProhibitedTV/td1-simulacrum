# TD-1 Simulacrum Architecture

## 1. Normative role

The Simulacrum is the executable reference definition of TD-1. It makes the machine's behavior precise before physical ternary subsystems are fabricated.

The emulator is not a visual mockup. It is the **normative machine model** against which later hardware is compared.

## 2. Architectural boundary

```text
Veilbreak corpus
      |
      v
Frozen corpus / provenance model
      |
      v
Motif-backed interface requirements
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
Deterministic render state
      |
      +------> Engineering projection
      |
      +------> Relic projection
      |
      v
Deterministic native geometry <------ frozen corpus geometry profile
      |
      v
Frontend / physical control surface
      |
      v
Physical hardware parity boundary
```

The arithmetic core must remain independent from phenomenology, geometry, and rendering. Corpus-derived ideas are allowed to shape interface semantics and representation, but not redefine arithmetic correctness.

## 3. Reference machine

Baseline parameters:

- radix: balanced ternary;
- trit values: `-1`, `0`, `+1`;
- word width: 12 trits;
- signed range: `-265720 .. +265720`;
- general-purpose registers: 9;
- initial memory: 729 words;
- condition state: negative / zero / positive.

### 3.1 Fixed-width arithmetic

Arithmetic wraps modulo `3^12`, mapped back into the symmetric balanced-ternary interval. Negation is exact tritwise sign inversion.

### 3.2 Logical ISA

Current operations:

`NOP`, `LDI`, `MOV`, `ADD`, `SUB`, `NEG`, `ADDI`, `CMP`, `LD`, `ST`, `BRN`, `BRZ`, `BRP`, `JMP`, `HALT`.

Branches use offsets relative to the instruction following the branch. Memory addresses are formed from a base register plus immediate offset and wrap modulo 729.

### 3.3 Instruction encoding policy

The logical ISA is implemented before physical encoding is frozen.

The target 12-trit format remains:

```text
[ opcode:3 ][ reg A:2 ][ reg B:2 ][ immediate/relative:5 ]
```

but this is still a target, not yet a normative encoding table. Freezing opcodes too early would couple hardware to unresolved semantic/compiler requirements.

## 4. Toolchain layer

The text assembler is intentionally conventional. It exists for engineering, test fixtures, and parity work while the native geometric programming language is still being designed.

The toolchain currently provides:

- labels;
- relative branches;
- register and immediate validation;
- canonical disassembly;
- CLI execution;
- deterministic render-state export;
- deterministic native-geometry export;
- frozen corpus validation and delta inspection.

Text assembly is an engineering interface, not the intended final native operator interface.

## 5. Semantic layer

TD-1's native operator model uses semantic roots rather than alphabetic text. v1 roots are:

`OBSERVER`, `ORIGIN`, `TIME`, `REFERENCE`, `MOTION`, `MEMORY`, `LINK`, `STATE`, `FRAME`, `AXIS`, `SIGNAL`, `COGNITION`, `EXECUTION`, `TRANSFORM`, `ISOLATION`, `DOMAIN`.

Balanced-ternary modifiers carry directional semantics:

- `-`: reverse / remove / contract / deny;
- `0`: inspect / hold / neutral / current;
- `+`: forward / acquire / expand / allow.

Compound operations are represented as **State Weaves**. v1 freezes ordering, identity, modifier state, canonical serialization, and semantic IR. Geometry v1 now gives these structures a deterministic topology, while semantic lowering into the ISA remains open.

## 6. Microglyph state encoding

A 12-trit word partitions into four 3-trit cells. Each cell has `3^3 = 27` states.

The stable data mapping is:

```text
glyph_id = balanced_ternary_value(triad) + 13
```

yielding `G00 .. G26`.

This mapping is reversible and renderer-independent.

Geometry schema v1 assigns each trit position a non-collinear axial direction. Positive and negative trits emit opposite spokes; zero emits no spoke. The resulting 27 topologies are unique and reversible. Final artistic glyph styling may evolve, but the normative state topology must remain recoverable or undergo an explicit schema migration.

## 7. Native geometry

`td1.geometry-scene` is the normative boundary between render state and presentation.

Schema v1 uses integer axial triangular coordinates `(q, r, z)`. Geometry scenes preserve:

- source render-state digest;
- source machine-state digest;
- deterministic primitive IDs and topology;
- optional frozen corpus geometry profile and profile digest;
- exact source IDs for every applied corpus-backed geometry rule.

Project-native choices such as the microglyph substrate are kept distinct from corpus-derived transforms.

Current corpus-admitted transforms are:

- `lattice` -> triangular register placement;
- `depth` -> discrete machine/semantic/observer depth planes;
- `multiscale` -> larger semantic-root topology;
- `braiding` -> alternating depth offsets in State Weave links.

No frozen motif support means no corpus-derived rule is claimed.

## 8. Observer Continuity

Observer Continuity is TD-1's permanent background state model.

The initial implementation supports:

- timezone-aware timestamp;
- WGS-84 latitude / longitude / altitude;
- geodetic-to-ECEF conversion;
- UTC-based Julian Date;
- explicitly approximate Earth Rotation Angle using UTC as a proxy for UT1.

The approximation is intentional and labeled. Precision navigation will require explicit treatment of UT1-UTC, TT/TDB, leap seconds, Earth orientation parameters, ephemerides, uncertainty, and sensor covariance.

Rendered deep-field motion must ultimately be driven by observer-state changes rather than arbitrary animation.

## 9. Provenance model

Corpus-derived requirements must preserve the chain:

```text
source record
  -> reported observation
    -> normalized motif
      -> engineering requirement
        -> implementation
          -> validation result
```

Geometry extends that chain when a motif changes presentation:

```text
frozen motif annotation
  -> admitted GeometryProfile support
    -> AppliedGeometryRule
      -> deterministic geometry scene
```

The system must never silently collapse a participant's interpretation into an established external cause.

## 10. Determinism and parity

The reference machine exposes deterministic snapshots and a SHA-256 state digest. Render state, corpus snapshots, geometry profiles, and geometry scenes also expose deterministic canonical serialization and content digests.

These digests are intended for:

- regression fixtures;
- deterministic replay;
- frontend equivalence testing;
- emulator-versus-hardware parity;
- differential testing across implementations.

A physical subsystem is conformant only if it reproduces the reference model's externally observable state for the same inputs and test vectors.

## 11. Operating modes

### Engineering Mode

Human-readable diagnostics: registers, instruction pointer, semantic IR, corpus provenance, observer state, geometry provenance, hardware parity status.

### Relic Mode

The exact same underlying state expressed using native TD-1 geometry and interaction semantics.

### Corpus Mode

Traceability view explaining which versioned source observations contributed to a requirement or corpus-backed geometry rule.

## 12. Primary engineering rule

**No decorative weirdness.**

Every glyph, transition, braid, pulse, depth change, topology change, or apparent motion must eventually map to explicit state, a measured event, or a documented interface affordance.
