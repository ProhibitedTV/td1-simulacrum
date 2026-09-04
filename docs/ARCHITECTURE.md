# TD-1 Simulacrum Architecture

## 1. Normative role

The Simulacrum is the executable reference definition of TD-1. It makes logical machine behavior precise before physical ternary subsystems are fabricated.

The emulator is not a visual mockup. It is the **normative machine model** against which later hardware is compared.

## 2. Authority boundaries

```text
                         Veilbreak corpus
                               |
                               v
                     frozen corpus/provenance
                               |
                               v
                    interface design constraints
                               |
                               v
Glyph / State Weave -> semantic IR -> typed lowering
                               |
                               v
                     12-trit reference machine
                        /        |         \
                       /         |          \
                      v          v           v
             td1.machine-state   |    td1.execution-trace
             save/restore/resume |     exact transitions
                                 |
                                 v
                         td1.render-state
                                 |
                                 v
                       td1.geometry-scene
                        /              \
                       v                v
              reference SVG      td1.geometry-delta
                                       |
                                       v
                                 td1.morph-plan
                                       |
                                       v
                               td1.relic-timeline
                                       |
                                       v
                          standalone Relic player

reference machine -> golden vectors -> parity harness -> physical ternary hardware
```

The arithmetic core must remain independent from phenomenology, rendering, playback, and transport. Corpus-derived ideas may shape interface semantics or representation, but they do not redefine arithmetic correctness.

The authority rules are:

1. logical machine semantics are normative;
2. `td1.machine-state` persists execution truth only;
3. render state may describe machine truth plus presentation inputs, but is not the persistence authority;
4. geometry is derived from validated render state;
5. animation consumes exact geometry transitions and may not invent machine endpoints;
6. physical hardware becomes authoritative only after deterministic parity testing.

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

### 3.3 Physical instruction encoding policy

The logical ISA exists before physical encoding is frozen.

The current target layout remains:

```text
[ opcode:3 ][ reg A:2 ][ reg B:2 ][ immediate/relative:5 ]
```

This is a design target, not yet a normative physical encoding table. Issue #2 remains intentionally deferred until semantic-lowering constraints and first-hardware measurements can be reviewed together.

Neither browser maturity nor machine-state persistence relaxes that gate. Saving logical state is not the same thing as defining physical instruction words.

## 4. Standalone machine-state persistence

`td1.machine-state` is the renderer-independent persistence boundary for logical TD-1 execution state.

Schema v1 records:

- schema/version;
- `word_width`, `register_count`, and `memory_words` architecture invariants;
- instruction pointer;
- ternary condition state;
- halted flag;
- executed step count;
- all register words;
- exact sparse nonzero memory;
- the complete existing emulator machine-state digest.

The schema deliberately excludes:

- glyph IDs;
- render planes;
- Observer Continuity fields;
- State Weaves;
- geometry;
- corpus provenance;
- animation/player state;
- physical instruction encoding.

A checkpoint is accepted only if reconstructing a real `Machine` from the serialized fields reproduces the claimed complete machine digest. Architecture mismatches, malformed words, duplicate/out-of-range sparse memory, zero-valued sparse entries, bad condition state, invalid scalar types, and digest tampering are rejected.

Canonical JSON produces a deterministic checkpoint SHA-256 separate from the machine-state digest. The checkpoint digest identifies the serialized artifact; the machine digest identifies reconstructed execution state.

Intermediate checkpoints may be restored and resumed against the same logical program. Tests require checkpoint -> restore -> resume to reach the same final complete machine digest as uninterrupted execution.

`MachineState.from_render_state()` is an explicit bridge for older layers. It restores the underlying machine and recaptures only machine truth. Presentation-only fields never enter the checkpoint schema.

## 5. Engineering toolchain

The text assembler is intentionally conventional. It exists for engineering, test fixtures, and parity work while the native geometric programming language is still evolving.

The toolchain provides:

- assembly/disassembly with labels and relative branches;
- deterministic execution;
- `td1.machine-state` emit, verify, restore, and resume workflows;
- `td1.execution-trace` export and replay verification;
- render-state export;
- native-geometry export and deltas;
- deterministic standalone SVG rendering;
- replayable Relic timelines;
- scene-pair and timeline-wide morph plans;
- self-contained Relic browser artifact compilation and verification;
- frozen corpus validation and comparison;
- State Weave lowering/introspection;
- parity vector export, loopback conformance, and report verification.

Text assembly is an engineering interface, not the intended final native operator interface.

## 6. Semantic layer

TD-1's native operator model uses semantic roots rather than alphabetic text.

Current roots:

`OBSERVER`, `ORIGIN`, `TIME`, `REFERENCE`, `MOTION`, `MEMORY`, `LINK`, `STATE`, `FRAME`, `AXIS`, `SIGNAL`, `COGNITION`, `EXECUTION`, `TRANSFORM`, `ISOLATION`, `DOMAIN`.

Balanced-ternary modifiers carry directional semantics:

- `-`: reverse / remove / contract / deny;
- `0`: inspect / hold / neutral / current;
- `+`: forward / acquire / expand / allow.

Compound operations are represented as **State Weaves**.

### 6.1 Typed lowering boundary

State Weave identity does not implicitly select registers or addresses.

`OperandBindings` supplies concrete machine resources. `lower_state_weave()` combines a supported weave with those bindings and emits a deterministic versioned lowering artifact containing exact logical instructions and resource effects.

Initial executable forms remain deliberately conservative:

- `EXECUTION:-` -> `HALT`;
- `TRANSFORM:-` -> `NEG`;
- `STATE:0` -> `CMP`;
- `MEMORY:0` -> `LD`;
- `MEMORY:+` -> `ST`.

These are TD-1 engineering conventions, not claimed translations of phenomenology. Unsupported State Weaves fail explicitly.

## 7. Native state representation

### 7.1 Microglyphs

A 12-trit word partitions into four 3-trit cells. Each cell has `3^3 = 27` possible states.

The stable data mapping is:

```text
glyph_id = balanced_ternary_value(triad) + 13
```

producing `G00 .. G26`.

The mapping is reversible and renderer-independent.

### 7.2 Render state

`td1.render-state` is the deterministic bridge from machine state into presentation inputs. It may include machine truth together with Observer Continuity and State Weave data required for display.

It is not the long-term machine persistence boundary. `td1.machine-state` owns that role.

Engineering and Relic projections must derive from the same immutable render-state digest.

### 7.3 Native geometry

`td1.geometry-scene` is the normative boundary between render state and visual presentation.

Schema v1 uses integer axial triangular coordinates `(q, r, z)` and preserves:

- source render-state digest;
- source machine-state digest;
- deterministic primitive IDs and topology;
- optional frozen corpus geometry profile;
- exact source IDs for applied corpus-backed rules.

Current corpus-admitted transforms include lattice arrangement, depth, multiscale, and braiding. No frozen motif support means no corpus-derived rule is claimed.

## 8. Reference SVG renderer

`td1.svg-render` consumes only a validated geometry scene.

Its integer projection is:

```text
x = (2q + r) * unit + z * depth_x
y = 3r * unit - z * depth_y
```

The renderer preserves primitive membership/topology and embeds source scene/render/machine provenance. Relic and Engineering themes share identical projected geometry; Engineering may add labels, while Relic is zero-display-text by default.

Projection, palette, stroke weight, margin, and labels are presentation choices rather than machine semantics.

## 9. Execution traces, timelines, and morphs

### 9.1 Execution trace

`td1.execution-trace` records one exact logical transition per executed instruction, including:

- logical program fingerprint;
- before/after complete machine digests;
- instruction identity;
- instruction pointer and condition transitions;
- halted transition;
- register deltas;
- memory deltas.

Replay must regenerate the canonical trace exactly.

### 9.2 Relic timeline

`td1.relic-timeline` joins execution with exact render/geometry states. Frame zero is the pre-execution state; every subsequent frame corresponds to exactly one execution event.

Each frame preserves exact machine/render/scene digests and the geometry delta from the previous frame.

Timeline v1 does not define frame duration, easing, camera motion, audio, or speculative intermediate machine states.

### 9.3 Morph planning

`td1.morph-plan` maps exact stable-ID geometry changes to presentation intent:

- `appear` -> `enter`;
- `disappear` -> `exit`;
- `move` -> `translate` with exact `(dq, dr, dz)`;
- `topology` -> `reform`;
- `metadata` -> `retag`.

Without admitted temporal corpus support, strategies remain conservative and endpoint-only. Corpus hints may constrain presentation, but never define machine semantics or intermediate state.

## 10. Standalone Relic browser player

The browser player is compiled from a validated Relic timeline and deterministic morph manifest into one dependency-free HTML artifact.

It embeds canonical timeline/morph payload bytes plus versioned provenance metadata. Browser WebCrypto verifies embedded payload digests before playback; the Python verifier performs a stronger offline check by rebuilding the timeline and deterministic morph manifest.

The browser draws exact `GeometryScene` primitives using the same projection as the SVG reference renderer.

The player freezes three authority rules:

```text
endpoint_policy = hard-reconcile-authoritative-scene-after-transition/v1
unchanged_primitive_policy = no-animation-without-morph-descriptor/v1
state_interpolation_policy = forbidden/v1
```

After every adjacent transition, transient browser animation state is discarded and the exact target scene is rebuilt. Timing, easing, speed, loop state, glow, persistence, and diagnostics are presentation configuration only.

## 11. Observer Continuity

Observer Continuity is TD-1's permanent background reference model.

Current groundwork includes:

- timezone-aware timestamp;
- WGS-84 latitude/longitude/altitude;
- geodetic -> ECEF conversion;
- UTC Julian Date;
- explicitly approximate Earth Rotation Angle using UTC as a proxy for UT1.

Precision navigation will require explicit time scales, Earth-orientation data, ephemerides, sensor covariance, and uncertainty contracts.

## 12. Provenance and determinism

Corpus-derived requirements preserve:

```text
source record
  -> reported observation
    -> normalized motif
      -> engineering requirement
        -> implementation
          -> validation result
```

Executable semantics preserve a separate engineering chain:

```text
State Weave
  -> OperandBindings
    -> deterministic lowering
      -> logical instructions
        -> execution trace
```

Persistence preserves:

```text
Machine
  -> td1.machine-state
    -> canonical checkpoint bytes
      -> restore Machine
        -> identical complete machine digest
```

Visible temporal presentation preserves:

```text
execution trace
  -> render states
    -> geometry scenes
      -> geometry deltas
        -> Relic timeline
          -> deterministic morph plans
            -> verified browser payloads
              -> presentation animation
                -> hard reconcile exact target scene
```

The reference machine, machine checkpoints, semantic lowerings, corpus snapshots, geometry profiles/scenes, traces, timelines, morph artifacts, SVG artifacts, Relic player artifacts, parity vectors, and parity reports all expose deterministic serialization/digests where applicable.

These digests support regression, replay, checkpoint integrity, frontend equivalence, physical parity, and differential testing. They are not digital signatures unless explicitly stated otherwise.

## 13. Physical parity boundary

Physical hardware enters through a transport-neutral conformance layer.

Current contracts:

- `td1.parity-capabilities`;
- `td1.parity-request`;
- `td1.parity-response`;
- `td1.parity-report`.

Initial operations:

- `trit_hold`;
- `register_load`;
- `negate`;
- `add`;
- `sub`.

The first real campaign remains one-trit hold followed by register-slice loads. ALU vectors are future oracles, not claims that ALU hardware exists.

The harness distinguishes capability rejection, transport/device fault, timeout, protocol error, value mismatch, and observed-state digest mismatch.

UART, USB, GPIO, Ethernet, or another physical link may be implemented later without changing parity semantics.

A physical subsystem may replace an emulated one only after conformance demonstrates parity against the reference model.

## 14. Operating modes

### Engineering Mode

Human-readable diagnostics: machine/checkpoint digests, registers, instruction pointer, semantic IR, lowering artifacts, corpus provenance, observer state, geometry provenance, timeline/morph identity, player verification, renderer provenance, and hardware parity status.

### Relic Mode

The exact same underlying machine-derived state expressed using native TD-1 geometry and interaction semantics. The Relic surface must not become a second machine-state authority.

### Corpus Mode

Traceability view explaining which versioned source observations contributed to interface requirements, geometry rules, or eligible temporal presentation hints.

## 15. Primary engineering rule

**No decorative weirdness, no semantic hand-waving, no persistence exceptionalism, no renderer exceptionalism, no playback exceptionalism, and no hardware exceptionalism.**

Every glyph, transition, braid, depth change, executable semantic mapping, checkpoint, visible primitive, timeline frame, morph descriptor, browser animation, or claimed hardware capability must map to explicit state, a measured event, a documented engineering convention, a versioned rule, or a passing conformance record.
