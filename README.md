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
- deterministic Engineering/Relic render state and native geometry;
- deterministic SVG rendering, Relic timelines, morph plans, and browser playback;
- transport-neutral physical parity contracts and golden vectors;
- trace-derived parity campaigns tied to real logical workloads;
- canonical `td1.parity-wire` framing beneath the parity API;
- deterministic wire transcripts and replayable bench-run bundles;
- **stream-backed `ParityLineIO` over ordinary binary streams, allowing real UART/USB-CDC-class links later without making serial-library choices part of TD-1 semantics.**

The long-term target is **hardware parity**: physical TD-1 subsystems progressively replace emulated subsystems while preserving identical externally observable behavior.

## Current baseline — v0.17 pre-alpha

### Logical machine

- balanced ternary trits: `-1`, `0`, `+1`;
- engineering symbols: `-`, `0`, `+`;
- 12-trit fixed-width words;
- signed range: `-265720 .. +265720`;
- 9 general-purpose registers;
- 729-word memory model;
- ternary condition state: negative / zero / positive;
- logical ISA: `NOP`, `LDI`, `MOV`, `ADD`, `SUB`, `NEG`, `ADDI`, `CMP`, `LD`, `ST`, `BRN`, `BRZ`, `BRP`, `JMP`, `HALT`;
- deterministic snapshots and complete machine-state SHA-256 digests.

### Engineering toolchain

- labels and relative branches;
- canonical assembly/disassembly;
- versioned execution traces with one event per logical instruction;
- per-event before/after machine digests plus register/memory deltas;
- deterministic trace replay verification;
- versioned `td1.machine-state` checkpoints;
- checkpoint verify/restore/resume;
- canonical JSON + artifact digests across major contracts.

### Native semantic and visual stack

- State Weave semantic roots and ternary modifiers;
- typed `OperandBindings` separated from semantic identity;
- conservative deterministic lowering for supported semantic forms;
- reversible `3 trits -> 27 microglyph states` mapping;
- WGS-84 geodetic -> ECEF Observer Continuity groundwork;
- UTC Julian Date and explicitly approximate Earth Rotation Angle;
- versioned `td1.render-state` and `td1.geometry-scene`;
- integer axial-triangular geometry with discrete depth;
- deterministic register, memory, control, and State Weave geometry;
- source-traceable corpus-admitted geometry/morph rules;
- deterministic SVG reference rendering;
- exact execution-to-geometry Relic timelines;
- deterministic morph plans and standalone browser player;
- hard reconciliation to exact authoritative endpoint geometry after every animation.

### Physical parity and bench stack

- versioned capability/request/response/report contracts;
- transport-neutral `ParityTransport` interface;
- deterministic `trit_hold`, `register_load`, `negate`, `add`, and `sub` vectors;
- explicit `ok`, `unsupported`, `fault`, `timeout`, and `error` outcomes;
- replayable conformance reports;
- reference loopback target;
- versioned workload-derived parity campaigns and campaign-run artifacts;
- canonical `td1.parity-wire` JSON Lines envelope;
- deterministic capability and request/response correlation;
- `JsonLineParityTransport` over minimal `ParityLineIO`;
- `ParityWireDevice` reference dispatcher;
- `InMemoryParityLineIO` for pure-software integration;
- `RecordingParityLineIO` and strict `ReplayParityLineIO`;
- versioned `td1.parity-wire-transcript` and `td1.parity-bench-run` artifacts;
- bench telemetry conventions for voltage, settling, comparator state, samples, board revision, and optional temperature;
- `BinaryByteReader`, `BinaryByteWriter`, and `BinaryByteStream` protocols;
- `StreamParityLineIO` with partial-write completion, fragmented/coalesced read handling, bounded buffering, explicit EOF/I/O errors, and deterministic stream statistics;
- no required pyserial dependency and no frozen physical-link configuration.

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

Capture final state:

```bash
td1-sim machine-state examples/sum.td1 --output final.machine.json
```

Capture an intermediate checkpoint:

```bash
td1-sim machine-state examples/sum.td1 \
  --after-steps 4 \
  --output step4.machine.json
```

Verify and resume:

```bash
td1-sim machine-state-verify step4.machine.json

td1-sim machine-state-resume examples/sum.td1 step4.machine.json \
  --output resumed.machine.json
```

`td1.machine-state` contains execution truth only. It does not contain glyphs, Observer data, geometry, corpus provenance, browser state, transport framing/evidence, stream diagnostics, or physical instruction words.

## Execution traces

```bash
td1-sim trace examples/sum.td1 > trace.json

td1-sim trace-verify examples/sum.td1 trace.json
```

Trace events preserve logical instruction identity, before/after complete machine digests, instruction-pointer/condition changes, and exact register/memory deltas.

## Trace-derived physical parity campaigns

Build and verify a workload-derived campaign:

```bash
td1-parity build examples/sum.td1 --output sum.campaign.json

td1-parity verify sum.campaign.json
```

Run through the reference target:

```bash
td1-parity loopback sum.campaign.json --output sum.run.json

td1-parity run-verify sum.run.json
```

Campaign v1 maps only subsystem operations the current parity surface can represent faithfully:

| Logical event | Derived parity operation |
| --- | --- |
| `LDI` | `register_load` of traced destination value |
| `MOV` | `register_load` of traced source value |
| `LD` | `register_load` of traced destination value |
| `NEG` | `negate` of traced pre-event operand |
| `ADD` | `add` of traced pre-event operands |
| `SUB` | `sub` of traced pre-event operands |
| `ADDI` | `add` with the immediate as a fixed-width 12-trit operand |

The `ADDI` mapping is a subsystem ALU test, not a claim that hardware decoded an `ADDI` instruction. `NOP`, `CMP`, `ST`, branches, `JMP`, and `HALT` remain unclaimed at the physical instruction level.

## Parity wire

`td1.parity-wire` is a canonical byte-oriented adapter layer beneath `ParityTransport`.

Message kinds:

```text
capabilities_request
capabilities_response
parity_request
parity_response
```

Frames are canonical UTF-8 JSON followed by exactly one LF. The default maximum frame size is 65,536 bytes including that LF. Empty, malformed, oversized, CRLF, multi-line, invalid-UTF-8, or noncanonical frames are rejected.

Run a complete campaign through the exact wire codec and reference target:

```bash
td1-parity wire-loopback sum.campaign.json --output sum.wire.run.json
```

The in-memory path is:

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

That proves host framing/correlation/integration only. It does not prove physical ternary hardware.

## Wire transcripts and bench evidence

Record exact line evidence and bind it to the campaign report:

```bash
td1-parity wire-loopback sum.campaign.json \
  --output sum.wire.run.json \
  --transcript-output sum.wire.transcript.json \
  --bench-output sum.bench.json
```

Verify and replay:

```bash
td1-parity wire-transcript-verify sum.wire.transcript.json

td1-parity bench-run-replay sum.bench.json
```

`td1.parity-wire-transcript` preserves direction, ordinal, exact frame text, frame SHA-256, decoded message kind/correlation, and envelope digest. `td1.parity-bench-run` requires that transcript to be exactly the wire conversation implied by its saved report.

Transcript hashes are integrity fingerprints, not device signatures.

## Stream-backed line I/O

v0.17 adds the first concrete host adapter beneath `ParityLineIO`:

```text
JsonLineParityTransport
        |
        v
RecordingParityLineIO
        |
        v
StreamParityLineIO
        |
        v
binary reader / writer
        |
        v
future UART / USB CDC / other byte stream
```

`StreamParityLineIO` supports one duplex stream or separate reader/writer objects. It:

- retries partial writes until the supplied frame is fully sent;
- buffers fragmented reads until one LF-terminated frame exists;
- preserves bytes belonging to later coalesced frames;
- enforces the existing wire maximum frame size while buffering;
- distinguishes empty EOF from EOF after a partial frame;
- rejects invalid stream return types and zero-progress writes;
- wraps underlying read/write/flush failures in adapter-specific errors;
- reports deterministic byte/frame/buffer counters with no wall-clock state.

It does **not** parse or canonicalize JSON. Meaning remains with `td1.parity-wire` above it.

A complete CI fixture drives a real trace-derived campaign through:

```text
JsonLineParityTransport
 -> RecordingParityLineIO
 -> StreamParityLineIO
 -> deliberately fragmented scripted device stream
 -> ParityWireDevice
 -> ReferenceLoopbackTransport
```

The resulting transcript and bench bundle must replay identically.

No pyserial dependency, COM/tty naming, baud rate, USB VID/PID, connector, or timeout policy is frozen yet.

## Bench telemetry conventions

Wire v1 standardizes optional response telemetry keys:

```text
voltage_uv
settle_us
comparator_code
sample_count
board_revision
temperature_millic
```

Scaled numeric fields use integers. Telemetry remains metadata until a future measured-acceptance contract explicitly says otherwise.

## Base hardware parity vectors

```bash
td1-sim parity-vectors --width 12

td1-sim parity-loopback --width 12

td1-sim parity-verify report.json
```

Loopback proves host infrastructure only.

## Native semantic lowering

```bash
td1-sim lowerings

td1-sim lower 'TRANSFORM:-' --target R2

td1-sim lower 'MEMORY:0' --target R2 --base R0 --offset 8
```

Unsupported State Weaves fail explicitly rather than receiving guessed executable meanings.

## Native geometry and Relic presentation

```bash
td1-sim glyph '+0--+000-++0'

td1-sim geometry examples/sum.td1 > scene.json

td1-sim svg scene.json > relic.svg

td1-sim svg scene.json --theme engineering > engineering.svg
```

Include a State Weave or frozen corpus snapshot when desired:

```bash
td1-sim geometry examples/sum.td1 \
  --weave 'TIME>REFERENCE:+' > scene.json

td1-sim geometry examples/sum.td1 \
  --corpus tests/fixtures/corpus_snapshot_v1.json > scene.json
```

## Relic timeline and browser player

```bash
td1-sim timeline examples/sum.td1 --output timeline.json

td1-sim timeline-morphs timeline.json --output morphs.json

td1-sim relic-player timeline.json --output relic.html

td1-sim relic-player-verify relic.html
```

Playback timing/easing/glow/looping are presentation only. Every completed transition hard-reconciles to authoritative geometry.

## Corpus provenance

```bash
td1-sim corpus-validate tests/fixtures/corpus_snapshot_v1.json

td1-sim corpus-delta VB-TD1-001.json VB-TD1-002.json
```

Checked-in corpus fixtures are synthetic unless explicitly documented otherwise.

## Physical instruction encoding is still deferred

The target layout remains a design candidate:

```text
[ opcode:3 ][ reg A:2 ][ reg B:2 ][ immediate/relative:5 ]
```

It is **not frozen**.

Logical execution, semantic lowering, checkpoints, traces, parity campaigns, deterministic wire framing, stream I/O, transcripts, and replayable bench evidence do not replace the missing input that matters for Issue #2: measurements and constraints from first physical ternary hardware.

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
      |                     RecordingParityLineIO
      |                                |
      |                                v
      |                       StreamParityLineIO
      |                                |
      |                                v
      |                      physical byte stream
      |                                |
      |                         +------+------+
      |                         |             |
      |                         v             v
      |                wire transcript   parity response
      |                         |             |
      |                         +------+------+
      |                                |
      |                     td1.parity-campaign-run
      |                                |
      |                                v
      |                       td1.parity-bench-run
      |
      v
render state -> native geometry -> delta/morph -> Relic timeline
                                               |
                        +----------------------+----------------+
                        |                                       |
                        v                                       v
                reference SVG                         standalone browser player
```

Machine persistence, physical conformance, transport framing, byte movement, transport evidence, and presentation remain separate contracts.

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
11. **Stream adapters move bytes; they do not interpret arithmetic.**
12. **Wire transcripts preserve evidence; they do not authenticate hardware or define arithmetic.**
13. **Physicality is not correctness.** A board advertises only capabilities it has demonstrated.
14. **Hardware earns authority through parity.**
15. **Determinism wins.** Equivalent inputs and versioned contracts must reproduce equivalent artifacts.
16. **Accuracy contracts are explicit.** Approximation is labeled rather than promoted silently.
17. **Corpus inputs are frozen before they influence a revision.**
18. **Physical instruction encoding waits for physical evidence.**

## Repository status

**Pre-alpha / architecture stabilization.**

The software stack now reaches from semantic intent through logical execution, exact persistence, workload-derived subsystem conformance, canonical wire framing, deterministic transport evidence, and a real binary-stream line adapter suitable for future serial-class hardware.

The next physical milestone remains the first real one-trit adapter speaking the v1 parity wire and returning measured bench telemetry. The next software step should be a thin optional serial integration or adapter diagnostics only after the actual bench link is chosen. Issue #2 remains intentionally deferred.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/MACHINE_STATE.md`](docs/MACHINE_STATE.md)
- [`docs/TRACE.md`](docs/TRACE.md)
- [`docs/PARITY_CAMPAIGNS.md`](docs/PARITY_CAMPAIGNS.md)
- [`docs/PARITY_WIRE.md`](docs/PARITY_WIRE.md)
- [`docs/STREAM_LINE_IO.md`](docs/STREAM_LINE_IO.md)
- [`docs/WIRE_TRANSCRIPTS.md`](docs/WIRE_TRANSCRIPTS.md)
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

A valid machine checkpoint proves only that it reconstructs the logical reference state it claims. A valid campaign proves only that its vectors were deterministically derived from the embedded logical trace. A passing conformance report proves only the tested operations represented by that report. A valid transcript proves only the canonical byte conversation it contains. A valid bench bundle proves that the transcript matches the wire conversation implied by its saved campaign report and can replay to the same result. A passing stream integration proves only the host byte-movement/buffering path. None of those prove physical ternary hardware or authenticated device identity.

State Weave lowering mappings, glyph geometry, axial projection, corpus-to-interface mappings, wire transport choices, stream adapter conventions, and transcript conventions are TD-1 engineering choices unless explicitly documented otherwise.

**Human-built hardware. Exotic design provenance. Bench validation required.**
