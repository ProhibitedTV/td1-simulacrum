# TD-1 Simulacrum

**Executable reference model and native software environment for TD-1 / The Anomaly.**

TD-1 is a human-built experimental computer centered on physical balanced-ternary computation, a non-text semantic interface, and continuous observer-state modeling. Interface research is informed by recurring motifs reported in the Veilbreak phenomenology corpus, while arithmetic, correctness, physical behavior, and validation remain independent engineering concerns.

> The unusual source may generate the hypothesis. The engineering process determines whether it gets merged.

## Project role

`td1-simulacrum` defines the machine before physical ternary hardware earns authority. It currently provides:

- the known-good logical model for the 12-trit TD-1 architecture;
- renderer-independent `td1.machine-state` checkpoints;
- assembler/disassembler and deterministic execution tooling;
- exact execution traces and replay verification;
- native State Weave semantic IR and typed lowering;
- reversible 27-state microglyph encoding;
- Observer Continuity groundwork;
- frozen Veilbreak-derived provenance tooling;
- deterministic Engineering/Relic render state;
- renderer-independent native geometry;
- deterministic SVG reference rendering;
- exact execution-to-geometry Relic timelines;
- source-traceable morph planning;
- a self-contained browser Relic player;
- transport-neutral physical parity contracts and golden vectors;
- trace-derived parity campaigns that turn real logical workloads into reproducible subsystem conformance vectors;
- **a deterministic canonical wire protocol that can carry those parity contracts to first-bench hardware without becoming machine semantics.**

The long-term target is **hardware parity**: physical TD-1 subsystems progressively replace emulated subsystems while preserving identical externally observable behavior.

## Current baseline — v0.15 pre-alpha

### Logical machine

- balanced ternary trits: `-1`, `0`, `+1`;
- engineering text symbols: `-`, `0`, `+`;
- 12-trit fixed-width word;
- signed range: `-265720 .. +265720`;
- 9 general-purpose registers;
- 729-word memory model;
- ternary condition state: negative / zero / positive;
- logical ISA: `NOP`, `LDI`, `MOV`, `ADD`, `SUB`, `NEG`, `ADDI`, `CMP`, `LD`, `ST`, `BRN`, `BRZ`, `BRP`, `JMP`, `HALT`;
- deterministic snapshots and complete machine-state SHA-256 digests.

### Engineering toolchain

- labels and relative branches;
- canonical assembly/disassembly;
- versioned `td1.execution-trace` with one event per executed logical instruction;
- per-event before/after machine digests plus register/memory deltas;
- deterministic trace replay verification;
- versioned `td1.machine-state` checkpoints with exact sparse nonzero memory;
- checkpoint verification, restore, and deterministic resume;
- canonical JSON + artifact digests across major contracts.

### Native semantic and visual stack

- State Weave semantic roots and ternary modifiers;
- typed `OperandBindings` separated from semantic identity;
- conservative deterministic lowering for supported semantic forms;
- reversible `3 trits -> 27 microglyph states` mapping;
- WGS-84 geodetic -> ECEF Observer Continuity groundwork;
- UTC Julian Date and explicitly approximate Earth Rotation Angle;
- versioned `td1.render-state`;
- integer axial-triangular `td1.geometry-scene` with discrete depth;
- deterministic geometry for registers, memory, machine controls, and State Weaves;
- source-traceable corpus-admitted lattice/depth/multiscale/braiding rules;
- versioned `td1.geometry-delta`;
- deterministic `td1.svg-render` reference renderer;
- zero-text Relic SVG by default and geometry-equivalent Engineering labels;
- versioned `td1.relic-timeline` with one exact frame per execution event;
- deterministic `td1.morph-plan` and timeline-wide morph manifests;
- dependency-free standalone Relic browser player;
- browser-side embedded-payload SHA-256 verification;
- hard reconciliation to exact authoritative endpoint geometry after every animation;
- Node syntax gating for the packaged browser runtime.

### Physical parity stack

- versioned capability/request/response/report contracts;
- transport-neutral `ParityTransport` interface;
- deterministic `trit_hold`, `register_load`, `negate`, `add`, and `sub` vectors;
- explicit `ok`, `unsupported`, `fault`, `timeout`, and `error` results;
- replayable conformance reports;
- reference loopback target;
- versioned `td1.parity-campaign` workload-derived vector packages;
- versioned `td1.parity-campaign-run` linking one campaign to one conformance report;
- versioned `td1.parity-wire` canonical JSON Lines envelope;
- deterministic capability and parity request/response correlation;
- host-side `JsonLineParityTransport` over minimal byte-line I/O;
- reference device-side dispatcher plus in-memory end-to-end wire loopback;
- bench telemetry conventions for voltage, settling, comparator state, sample count, board revision, and optional temperature;
- dedicated `td1-parity` CLI including `wire-loopback`.

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

## Exact machine checkpoints

Capture final logical state:

```bash
td1-sim machine-state examples/sum.td1 --output final.machine.json
```

Capture an intermediate checkpoint:

```bash
td1-sim machine-state examples/sum.td1 \
  --after-steps 4 \
  --output step4.machine.json
```

Verify it:

```bash
td1-sim machine-state-verify step4.machine.json
```

Resume the same logical program:

```bash
td1-sim machine-state-resume examples/sum.td1 step4.machine.json \
  --output resumed.machine.json
```

`td1.machine-state` contains execution truth only. It does not contain glyphs, Observer data, State Weaves, geometry, corpus provenance, browser state, wire framing, or physical instruction words.

## Execution traces

Create an exact logical transition trace:

```bash
td1-sim trace examples/sum.td1 > trace.json
```

Replay and verify it:

```bash
td1-sim trace-verify examples/sum.td1 trace.json
```

Trace events preserve logical instruction identity, before/after complete machine digests, instruction-pointer/condition changes, and exact register/memory deltas.

## Trace-derived physical parity campaigns

The campaign layer converts **subsystem operations encountered during a real logical execution** into deterministic parity vectors.

Build a campaign directly from a source workload:

```bash
td1-parity build examples/sum.td1 --output sum.campaign.json
```

Verify/reconstruct it:

```bash
td1-parity verify sum.campaign.json
```

Run the campaign through the reference loopback target:

```bash
td1-parity loopback sum.campaign.json --output sum.run.json
```

Verify the complete campaign/report artifact:

```bash
td1-parity run-verify sum.run.json
```

Deliberately exercise capability rejection:

```bash
td1-parity loopback sum.campaign.json --target-max-width 3
```

### What a campaign means

Campaign v1 maps logical events only where the current parity surface has a faithful subsystem-level equivalent:

| Logical event | Derived parity operation |
| --- | --- |
| `LDI` | `register_load` of traced destination value |
| `MOV` | `register_load` of traced source value |
| `LD` | `register_load` of traced destination value |
| `NEG` | `negate` of traced pre-event operand |
| `ADD` | `add` of traced pre-event operands |
| `SUB` | `sub` of traced pre-event operands |
| `ADDI` | `add` with the immediate represented as a fixed-width 12-trit word |

The `ADDI` mapping is deliberately labeled as a subsystem-level ALU test. It does **not** claim that physical hardware decoded or executed an `ADDI` instruction.

`NOP`, `CMP`, `ST`, branches, `JMP`, and `HALT` produce no v1 campaign vector because the existing parity operation surface cannot faithfully represent their complete semantics.

Each campaign preserves the complete source trace, exact initial/final machine checkpoints, event identity, before/after machine digests, mapping rationale, exact vectors, and vector-set digest. Loading a saved campaign re-derives all entries from the embedded trace and rejects drift.

A passing campaign therefore means:

> The target passed the advertised low-level ternary subsystem operations represented by these exact workload-derived vectors.

It does **not** mean:

> The target physically fetched, decoded, and executed the original TD-1 program.

That distinction remains central until the physical instruction layer exists.

## Parity wire protocol

v0.15 adds `td1.parity-wire`: a canonical byte-oriented adapter layer beneath the existing `ParityTransport` contract.

The message kinds are:

```text
capabilities_request
capabilities_response
parity_request
parity_response
```

Frames are canonical UTF-8 JSON followed by exactly one LF. The default maximum frame size is 65,536 bytes including that LF. Empty, malformed, oversized, CRLF, multi-line, invalid-UTF-8, or noncanonical frames are rejected.

The envelope **wraps** the existing parity payload schemas. It does not define new arithmetic semantics.

Run a complete saved workload campaign through the exact wire codec and reference target:

```bash
td1-parity wire-loopback sum.campaign.json --output sum.wire.run.json
```

Exercise capability rejection through the wire path:

```bash
td1-parity wire-loopback sum.campaign.json --target-max-width 3
```

The in-memory wire path is:

```text
ParityCampaign
    |
    v
run_conformance()
    |
    v
JsonLineParityTransport
    |
    v
canonical td1.parity-wire bytes
    |
    v
InMemoryParityLineIO
    |
    v
ParityWireDevice
    |
    v
ReferenceLoopbackTransport
```

That proves framing, correlation, codec behavior, and parity integration in CI. It still does not prove physical ternary hardware.

### Bench telemetry conventions

Wire v1 standardizes optional response telemetry keys:

```text
voltage_uv
settle_us
comparator_code
sample_count
board_revision
temperature_millic
```

The scaled numeric fields use integers. Telemetry remains metadata only in v1 and cannot change arithmetic pass/fail evaluation. Electrical acceptance criteria will be versioned later after real bench measurements exist.

## Base hardware parity vectors

Emit deterministic register/ALU reference vectors:

```bash
td1-sim parity-vectors --width 12
```

Run the complete base suite through the reference loopback:

```bash
td1-sim parity-loopback --width 12
```

Validate a saved conformance report:

```bash
td1-sim parity-verify report.json
```

The loopback proves the host harness only. It is not evidence that physical ternary hardware exists or has passed.

## Native semantic lowering

List supported State Weave lowering forms:

```bash
td1-sim lowerings
```

Lower supported semantic intent:

```bash
td1-sim lower 'TRANSFORM:-' --target R2

td1-sim lower 'MEMORY:0' --target R2 --base R0 --offset 8
```

Unsupported State Weaves fail explicitly rather than receiving guessed executable meanings.

## Native geometry and Relic presentation

Inspect microglyph IDs for a 12-trit word:

```bash
td1-sim glyph '+0--+000-++0'
```

Emit native geometry:

```bash
td1-sim geometry examples/sum.td1 > scene.json
```

Include a State Weave:

```bash
td1-sim geometry examples/sum.td1 \
  --weave 'TIME>REFERENCE:+' > scene.json
```

Admit geometry rules from a frozen corpus snapshot:

```bash
td1-sim geometry examples/sum.td1 \
  --corpus tests/fixtures/corpus_snapshot_v1.json > scene.json
```

Render Relic or Engineering SVG from the exact same geometry:

```bash
td1-sim svg scene.json > relic.svg

td1-sim svg scene.json --theme engineering > engineering.svg
```

## Relic timeline and standalone player

Build an exact execution-to-geometry timeline:

```bash
td1-sim timeline examples/sum.td1 --output timeline.json
```

Derive deterministic transition intent:

```bash
td1-sim timeline-morphs timeline.json --output morphs.json
```

Compile one dependency-free browser artifact:

```bash
td1-sim relic-player timeline.json --output relic.html
```

Verify the embedded canonical payloads from the engineering toolchain:

```bash
td1-sim relic-player-verify relic.html
```

Playback timing, easing, speed, glow, looping, and eligible persistence are presentation choices only. Every completed transition is hard-reconciled to the exact authoritative target `GeometryScene`.

## Corpus provenance

Validate a frozen TD-1 corpus snapshot:

```bash
td1-sim corpus-validate tests/fixtures/corpus_snapshot_v1.json
```

Compare two corpus revisions:

```bash
td1-sim corpus-delta VB-TD1-001.json VB-TD1-002.json
```

The checked-in corpus fixtures are synthetic unless explicitly documented otherwise.

## Physical instruction encoding is still deferred

The target 12-trit layout remains a design candidate:

```text
[ opcode:3 ][ reg A:2 ][ reg B:2 ][ immediate/relative:5 ]
```

It is **not frozen**.

The project now has logical execution, semantic lowering, exact checkpoints, execution traces, workload-derived parity campaigns, a transport-neutral hardware conformance boundary, and deterministic wire framing for the first adapter. None of those replace the missing input that matters for Issue #2: measurements and constraints from first physical ternary hardware.

Software does not get to vote copper out of the room.

## Layering

```text
Veilbreak corpus
      |
      v
frozen provenance / motif-backed interface constraints
      |
      v
State Weave semantic IR -> typed lowering
      |
      v
12-trit reference machine
      |
      +------> td1.machine-state ------> save / verify / restore / resume
      |
      +------> td1.execution-trace
      |                  |
      |                  +------> td1.parity-campaign
      |                                |
      |                                v
      |                         parity harness
      |                                |
      |                                v
      |                         ParityTransport
      |                                |
      |                                v
      |                         td1.parity-wire
      |                                |
      |                                v
      |                     physical ternary subsystem
      |                                |
      |                                v
      |                     td1.parity-campaign-run
      |
      v
render state -> native geometry -> delta/morph -> Relic timeline
                                               |
                        +----------------------+----------------+
                        |                                       |
                        v                                       v
                reference SVG                         standalone browser player
```

Machine persistence, physical conformance, transport framing, and presentation remain separate contracts.

## Design doctrine

1. **No decorative weirdness.** Visible behavior maps to real state, event, or documented presentation rule.
2. **Veilbreak is an anchor, not an oracle.** Phenomenology may generate interface hypotheses; it does not define arithmetic or ontology.
3. **Logical machine semantics are normative.**
4. **Machine persistence contains machine truth only.**
5. **Semantic identity does not hide operands.** Concrete machine resources are bound explicitly.
6. **Transitions are traced before they are animated.**
7. **Pixels are downstream of truth.** Renderers consume native geometry.
8. **Browser animation is presentation.** It cannot create machine endpoints.
9. **Trace-derived campaigns test subsystems, not imaginary instruction decoders.**
10. **Wire framing transports parity semantics; it does not create them.**
11. **Physicality is not correctness.** A board advertises only capabilities it has demonstrated.
12. **Hardware earns authority through parity.**
13. **Determinism wins.** Equivalent inputs and versioned contracts must reproduce equivalent artifacts.
14. **Accuracy contracts are explicit.** Approximation is labeled rather than promoted silently.
15. **Corpus inputs are frozen before they influence a revision.**
16. **Physical instruction encoding waits for physical evidence.**

## Repository status

**Pre-alpha / architecture stabilization.**

The software stack now has explicit contracts from semantic intent through logical execution, checkpoint persistence, workload-derived subsystem conformance, deterministic wire framing, native geometry, deterministic playback, and physical parity reporting.

The next physical milestone is the first real one-trit adapter speaking the v1 parity wire over a concrete byte link and returning measured bench telemetry. The next software work should therefore stay close to copper: a real serial `ParityLineIO`, adapter diagnostics, and measured acceptance tooling. Issue #2 remains intentionally deferred until first-hardware constraints are measured.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/MACHINE_STATE.md`](docs/MACHINE_STATE.md)
- [`docs/TRACE.md`](docs/TRACE.md)
- [`docs/PARITY_CAMPAIGNS.md`](docs/PARITY_CAMPAIGNS.md)
- [`docs/PARITY_WIRE.md`](docs/PARITY_WIRE.md)
- [`docs/HARDWARE_PARITY.md`](docs/HARDWARE_PARITY.md)
- [`docs/SEMANTIC_LOWERING.md`](docs/SEMANTIC_LOWERING.md)
- [`docs/RENDER_STATE.md`](docs/RENDER_STATE.md)
- [`docs/GEOMETRY.md`](docs/GEOMETRY.md)
- [`docs/SVG_RENDERER.md`](docs/SVG_RENDERER.md)
- [`docs/RELIC_TIMELINE.md`](docs/RELIC_TIMELINE.md)
- [`docs/MORPH_PLANS.md`](docs/MORPH_PLANS.md)
- [`docs/RELIC_PLAYER.md`](docs/RELIC_PLAYER.md)
- [`docs/CORPUS_PIPELINE.md`](docs/CORPUS_PIPELINE.md)
- [`docs/VEILBREAK_PROVENANCE.md`](docs/VEILBREAK_PROVENANCE.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/adr/`](docs/adr/)
- [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Epistemic boundary

TD-1 does **not** assume that DMT/Veilbreak reports establish extraterrestrial, interdimensional, or otherwise external intelligences. The project treats those reports as a structured phenomenological corpus capable of generating unconventional interface constraints and testable design hypotheses.

A valid machine checkpoint proves only that it reconstructs the logical reference state it claims. A valid campaign proves only that its subsystem vectors were deterministically derived from the embedded logical trace. A passing conformance report proves only the tested operations against the target and capabilities represented by that report. Passing wire-loopback proves only the host parity + framing + correlation stack. None of those prove physical ternary hardware.

State Weave lowering mappings, glyph geometry, axial projection, corpus-to-interface mappings, and wire transport choices are TD-1 engineering conventions unless explicitly documented otherwise.

**Human-built hardware. Exotic design provenance. Bench validation required.**
