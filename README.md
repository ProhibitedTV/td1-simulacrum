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
- the renderer-independent native geometry contract used by visual and physical interfaces;
- the replayable transition source for Relic Mode motion and hardware differential testing;
- the deterministic SVG reference renderer for visible native geometry;
- the replayable execution-to-geometry Relic timeline;
- the corpus-traceable morph-planning contract constraining how exact geometry changes may be presented;
- the self-contained browser Relic player that animates exact timeline endpoints without becoming a second machine-state authority;
- the transport-neutral conformance harness that physical ternary hardware must pass before replacing emulation.

The long-term target is **hardware parity**: physical TD-1 subsystems should progressively replace emulated subsystems while preserving identical externally observable state.

## Current capabilities

The v0.12 pre-alpha foundation includes:

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
- deterministic `td1.svg-render` output consuming only validated native geometry;
- integer axial/depth SVG projection with embedded scene/render/machine provenance;
- zero-display-text Relic SVG by default and geometry-equivalent Engineering labels;
- XML-safe stable IDs and byte-deterministic SVG artifact digests;
- versioned `td1.relic-timeline` with frame zero plus one exact frame per execution event;
- per-frame machine/render/scene digests and event identity;
- strict replay against execution-trace machine digests;
- timeline deserialization that rebuilds geometry and recomputes every adjacent delta;
- deterministic multi-frame SVG export with `td1.timeline-svg-manifest`;
- versioned `td1.morph-plan` transition intent for appear/disappear/move/topology/metadata changes;
- exact native `(dq, dr, dz)` translation vectors for true move transitions;
- conservative morph fallbacks when no temporal corpus motif is admitted;
- optional source-traceable morphing, context-persistence, focus-through, horizontal-motion, and vertical-motion presentation hints;
- versioned `td1.timeline-morph-manifest` with one plan per noninitial Relic timeline frame;
- versioned `td1.relic-player-config` for explicitly non-normative playback choices;
- versioned `td1.relic-player-artifact` provenance embedded in standalone player HTML;
- dependency-free browser playback of native geometry using the same axial/depth projection as the SVG reference renderer;
- browser-side SHA-256 verification of embedded canonical timeline/morph payloads before playback;
- Python-side standalone artifact verification that regenerates deterministic morph plans from the embedded timeline;
- descriptor-driven enter/exit/translate/reform/retag presentation with no inferred movement for unchanged primitives;
- hard reconciliation to the exact authoritative target `GeometryScene` after every adjacent animated transition;
- zero-text Relic canvas by default with explicit Engineering and provenance diagnostics;
- transport-neutral hardware capability/request/response/report schemas;
- deterministic trit/register and ALU golden vectors;
- explicit hardware `ok`, `unsupported`, `fault`, `timeout`, and `error` outcomes;
- replayable conformance reports with slice-state digests and discrepancy records;
- a reference loopback hardware target for proving the harness before real boards arrive;
- a CLI, examples, golden fixtures, unit tests, Python-version CI, Ruff linting, and explicit Relic-player JavaScript syntax gating.

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

Create a complete execution-to-geometry Relic timeline:

```bash
td1-sim timeline examples/sum.td1 --output timeline.json
```

Add corpus-backed geometry and a native State Weave to every frame:

```bash
td1-sim timeline examples/sum.td1 \
  --corpus tests/fixtures/corpus_snapshot_v1.json \
  --weave 'TIME>REFERENCE:+' \
  --output timeline.json
```

Validate the saved timeline and all embedded render/geometry/delta relationships:

```bash
td1-sim timeline-verify timeline.json
```

Derive renderer-independent transition intent for every timeline transition:

```bash
td1-sim timeline-morphs timeline.json --output morphs.json
```

Compile the exact timeline into a self-contained Relic Mode browser artifact:

```bash
td1-sim relic-player timeline.json --output relic.html
```

Open `relic.html` directly in a modern browser. The artifact contains its canonical timeline and deterministic morph manifest and verifies those embedded payloads before playback begins.

Verify the standalone artifact offline from the engineering toolchain:

```bash
td1-sim relic-player-verify relic.html
```

Customize presentation timing without changing machine state:

```bash
td1-sim relic-player timeline.json \
  --output relic.html \
  --frame-ms 1100 \
  --transition-ms 620 \
  --persistence-ms 260 \
  --easing ease-in-out
```

Disable automatic playback or looping:

```bash
td1-sim relic-player timeline.json \
  --output relic.html \
  --no-autoplay \
  --no-loop
```

Timing, easing, glow, playback speed, looping, and eligible visual persistence are presentation choices only. Every completed adjacent transition is discarded and rebuilt from the exact target geometry scene.

Render every exact timeline frame to deterministic Relic SVG:

```bash
td1-sim timeline-svgs timeline.json \
  --out-dir relic-frames \
  --theme relic
```

The output directory contains `frame-0000.svg`, one SVG for every later execution frame, and a deterministic `manifest.json` with timeline/scene/SVG digests.

Or derive one exact morph plan between two saved native geometry scenes:

```bash
td1-sim morph before.geometry.json after.geometry.json --output morph.json
```

Morph plans constrain permitted presentation intent and corpus-backed hints. They do not define timing, easing, interpolation samples, or intermediate machine state.

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
td1-sim geometry examples/sum.td1 > scene.json
```

Admit geometry rules from a frozen corpus snapshot:

```bash
td1-sim geometry examples/sum.td1 \
  --corpus tests/fixtures/corpus_snapshot_v1.json > scene.json
```

Include a State Weave in the geometry scene:

```bash
td1-sim geometry examples/sum.td1 \
  --weave 'TIME>REFERENCE:+' > scene.json
```

Render the native scene into zero-text Relic SVG:

```bash
td1-sim svg scene.json > relic.svg
```

Render the exact same geometry in Engineering presentation:

```bash
td1-sim svg scene.json --theme engineering > engineering.svg
```

Write SVG directly to a file and print artifact/provenance digests:

```bash
td1-sim svg scene.json --output relic.svg
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

The physical instruction encoding is **not frozen yet**. Logical execution semantics, the first native semantic-lowering boundary, and a transport-neutral hardware conformance boundary now exist; the eventual 12-trit opcode/register/immediate layout will be versioned only after compiler constraints and measurements from first hardware are reviewed together.

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
      v
native geometry scene <------ frozen corpus geometry profile
      |
      +------> geometry delta
      |             |
      |             v
      |        td1.morph-plan <------ corpus temporal motifs
      |             |
      v             v
Relic execution timeline ------> timeline morph manifest
      |                              |
      +------------------------------+
      |                              |
      +------> deterministic SVG frame manifest
      |                              |
      v                              v
reference SVG renderer       standalone Relic browser player
      |                              |
      v                              v
exact visible frames          animated endpoint presentation
                                     |
                                     v
                          future interactive control surface
                                     |
                                     v
transport-neutral parity harness <------ golden vectors
      |
      v
physical ternary subsystem
```

The visual branch and physical-conformance branch share machine truth but do not grant each other authority. The browser player consumes exact timeline/morph contracts; it does not define machine behavior. Physical hardware earns authority only through parity.

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
11. **Transitions are traced before they are animated.** A visual effect must consume real execution or geometry change rather than fabricate activity.
12. **Semantic identity does not hide operands.** Native operations bind concrete machine resources explicitly, and unsupported meanings remain unsupported until engineered.
13. **Physicality is not correctness.** A board advertises only capabilities it has actually demonstrated through the parity harness.
14. **Pixels are downstream of truth.** Visible artifacts consume native geometry and preserve its provenance rather than reconstructing state from UI code.
15. **Playback consumes state transitions.** Timeline frames and deltas are exact; timing and interpolation may never fabricate machine state.
16. **Morph planning constrains presentation.** Corpus-inspired transition hints are explicit and source-traceable; they never create intermediate machine state.
17. **Browser animation is presentation.** Every adjacent animation terminates by hard-reconciling to the exact authoritative target scene.

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

Machine truth, semantic lowering, frozen corpus provenance, native geometry, deterministic transitions, replayable Relic timelines, renderer-independent morph intent, deterministic SVG rendering, a self-contained animated browser player, and transport-neutral physical conformance now have explicit contracts.

The next software priorities are standalone machine-state serialization, trace-to-parity campaign packaging, richer but still endpoint-authoritative interactive Relic controls, and optional renderer-parity experiments such as WebGL. The next physical milestone remains the first real one-trit adapter. Issue #2's physical instruction encoding remains intentionally deferred until first-hardware constraints are measured.

See:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/SEMANTIC_LOWERING.md`](docs/SEMANTIC_LOWERING.md)
- [`docs/HARDWARE_PARITY.md`](docs/HARDWARE_PARITY.md)
- [`docs/RENDER_STATE.md`](docs/RENDER_STATE.md)
- [`docs/GEOMETRY.md`](docs/GEOMETRY.md)
- [`docs/SVG_RENDERER.md`](docs/SVG_RENDERER.md)
- [`docs/RELIC_TIMELINE.md`](docs/RELIC_TIMELINE.md)
- [`docs/MORPH_PLANS.md`](docs/MORPH_PLANS.md)
- [`docs/RELIC_PLAYER.md`](docs/RELIC_PLAYER.md)
- [`docs/TRACE.md`](docs/TRACE.md)
- [`docs/CORPUS_PIPELINE.md`](docs/CORPUS_PIPELINE.md)
- [`docs/VEILBREAK_PROVENANCE.md`](docs/VEILBREAK_PROVENANCE.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Epistemic boundary

TD-1 does **not** assume that DMT/Veilbreak reports establish extraterrestrial, interdimensional, or otherwise external intelligences. The project treats those reports as a structured phenomenological corpus capable of generating unconventional interface constraints and testable design hypotheses.

The included corpus fixtures are synthetic test data unless explicitly documented otherwise. State Weave lowering mappings are TD-1 engineering conventions unless explicitly documented otherwise. Loopback conformance proves the host harness only; it is not evidence that physical ternary hardware has passed. SVG styling, projection, browser timing/easing/glow/persistence, morph strategies, and other playback effects are presentation conventions and are not additional evidence or machine semantics. Corpus-backed morph rules preserve source provenance but do not claim that participant reports specify TD-1 animation algorithms. Embedded player hashes provide integrity checks, not authorship signatures.

**Human-built hardware. Exotic design provenance. Bench validation required.**
