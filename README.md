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
- deterministic native geometry, SVG rendering, Relic timelines, morphs, and browser playback;
- transport-neutral physical parity contracts and golden vectors;
- trace-derived parity campaigns tied to real logical workloads;
- canonical `td1.parity-wire` framing beneath the parity API;
- deterministic wire transcripts and replayable bench-run bundles;
- stream-backed `ParityLineIO` over ordinary binary streams;
- **an optional pyserial live-bench adapter that can carry the exact existing parity/wire/transcript stack to a real serial-class device without making serial configuration machine semantics.**

The long-term target is **hardware parity**: physical TD-1 subsystems progressively replace emulated subsystems while preserving identical externally observable behavior.

## Current baseline — v0.18 pre-alpha

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

### Native semantic and visual stack

- State Weave semantic roots and ternary modifiers;
- typed `OperandBindings` separated from semantic identity;
- conservative deterministic lowering for supported semantic forms;
- reversible `3 trits -> 27 microglyph states` mapping;
- WGS-84 geodetic -> ECEF Observer Continuity groundwork;
- UTC Julian Date and explicitly approximate Earth Rotation Angle;
- versioned `td1.render-state` and `td1.geometry-scene`;
- deterministic axial-triangular geometry;
- source-traceable corpus-admitted geometry/morph rules;
- deterministic SVG reference rendering;
- exact Relic timelines and morph plans;
- standalone browser playback that hard-reconciles to authoritative endpoint geometry.

### Physical parity and bench stack

- versioned capability/request/response/report contracts;
- transport-neutral `ParityTransport`;
- deterministic `trit_hold`, `register_load`, `negate`, `add`, and `sub` vectors;
- explicit `ok`, `unsupported`, `fault`, `timeout`, and `error` outcomes;
- workload-derived `td1.parity-campaign` and `td1.parity-campaign-run` artifacts;
- canonical `td1.parity-wire` JSON Lines framing;
- `JsonLineParityTransport` and reference `ParityWireDevice`;
- `InMemoryParityLineIO` for pure-software integration;
- `RecordingParityLineIO` and strict `ReplayParityLineIO`;
- versioned `td1.parity-wire-transcript` and `td1.parity-bench-run` artifacts;
- bench telemetry conventions for voltage, settling, comparator state, samples, board revision, and optional temperature;
- `StreamParityLineIO` over generic binary streams;
- optional `PySerialByteStream` live deployment adapter;
- `td1-parity serial-run` for an explicitly configured serial port;
- no default baud rate, automatic port discovery, connector choice, or pyserial requirement in core installs.

## Quick start

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
```

Install the optional live serial adapter only where required:

```bash
python -m pip install -e '.[serial]'
```

Run the reference program:

```bash
td1-sim run examples/sum.td1
```

## Exact machine checkpoints

```bash
td1-sim machine-state examples/sum.td1 --output final.machine.json

td1-sim machine-state examples/sum.td1 \
  --after-steps 4 \
  --output step4.machine.json

td1-sim machine-state-verify step4.machine.json

td1-sim machine-state-resume examples/sum.td1 step4.machine.json \
  --output resumed.machine.json
```

`td1.machine-state` contains execution truth only. It does not contain glyphs, Observer data, geometry, transport configuration, wire evidence, or physical instruction words.

## Execution traces

```bash
td1-sim trace examples/sum.td1 > trace.json

td1-sim trace-verify examples/sum.td1 trace.json
```

Trace events preserve logical instruction identity, before/after complete machine digests, instruction-pointer/condition changes, and exact register/memory deltas.

## Trace-derived parity campaigns

```bash
td1-parity build examples/sum.td1 --output sum.campaign.json

td1-parity verify sum.campaign.json

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
| `ADDI` | `add` with a fixed-width immediate operand |

This is subsystem parity. It is not evidence that hardware fetched or decoded the original logical instruction.

## Canonical parity wire

`td1.parity-wire` carries existing parity contracts as canonical UTF-8 JSON Lines.

Message kinds are:

```text
capabilities_request
capabilities_response
parity_request
parity_response
```

The default maximum frame size is 65,536 bytes including the trailing LF. Noncanonical, malformed, CRLF, multi-line, oversized, or invalid-UTF-8 frames are rejected.

Exercise the exact wire codec in software:

```bash
td1-parity wire-loopback sum.campaign.json --output sum.wire.run.json
```

## Wire transcripts and bench evidence

```bash
td1-parity wire-loopback sum.campaign.json \
  --output sum.wire.run.json \
  --transcript-output sum.wire.transcript.json \
  --bench-output sum.bench.json

td1-parity wire-transcript-verify sum.wire.transcript.json

td1-parity bench-run-replay sum.bench.json
```

`td1.parity-wire-transcript` preserves exact canonical host/device frames. `td1.parity-bench-run` binds those bytes to the exact campaign report and requires offline replay to regenerate the same run.

SHA-256 values are integrity fingerprints, not device-authentication signatures.

## Stream-backed line I/O

The generic host stack is:

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
```

`StreamParityLineIO` completes partial writes, reassembles fragmented reads, preserves later coalesced frames, enforces the wire frame ceiling, and exposes deterministic byte/frame/buffer counters.

It deliberately does not parse JSON. Wire semantics remain above it.

## Optional serial live-bench path

v0.18 adds the first host path that can open a real serial port:

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
PySerialByteStream
        |
        v
pyserial
        |
        v
UART / USB CDC device
```

Run a saved campaign against an explicitly configured serial device:

```bash
td1-parity serial-run sum.campaign.json \
  --port /dev/ttyACM0 \
  --baud 230400 \
  --read-timeout 2.0 \
  --write-timeout 2.0 \
  --output sum.serial.run.json \
  --transcript-output sum.serial.transcript.json \
  --bench-output sum.serial.bench.json
```

Windows example:

```bash
td1-parity serial-run sum.campaign.json \
  --port COM7 \
  --baud 230400 \
  --read-timeout 2.0 \
  --write-timeout 2.0 \
  --output sum.serial.run.json
```

Port, baud rate, and host timeout values are deployment configuration. They may appear in the CLI summary but are not silently embedded into canonical campaign-run, transcript, or bench-run artifacts.

A serial timeout remains a host adapter diagnostic, not a fabricated `ParityStatus` from the target.

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

Scaled numeric fields use integers. Telemetry remains metadata until a future measured-acceptance contract explicitly promotes defined measurements into pass/fail criteria.

## Native semantic lowering

```bash
td1-sim lowerings

td1-sim lower 'TRANSFORM:-' --target R2

td1-sim lower 'MEMORY:0' --target R2 --base R0 --offset 8
```

Unsupported State Weaves fail explicitly rather than receiving guessed executable meanings.

## Native geometry and Relic playback

```bash
td1-sim glyph '+0--+000-++0'

td1-sim geometry examples/sum.td1 > scene.json

td1-sim svg scene.json > relic.svg

td1-sim timeline examples/sum.td1 --output timeline.json

td1-sim relic-player timeline.json --output relic.html

td1-sim relic-player-verify relic.html
```

Presentation remains downstream of machine truth.

## Physical instruction encoding is still deferred

The target layout remains only a design candidate:

```text
[ opcode:3 ][ reg A:2 ][ reg B:2 ][ immediate/relative:5 ]
```

It is **not frozen**.

Logical execution, semantic lowering, persistence, parity campaigns, wire framing, stream adapters, serial transport, transcripts, and bench replay do not replace the missing input that matters for Issue #2: measurements and constraints from first physical ternary hardware.

Software does not get to vote copper out of the room.

## Authority layering

```text
State Weave -> logical instructions -> reference machine
                                      |
                                      +-> machine-state / execution trace
                                      |
                                      +-> parity campaign
                                             |
                                             v
                                      ParityTransport
                                             |
                                             v
                                      td1.parity-wire
                                             |
                                             v
                                  RecordingParityLineIO
                                             |
                                             v
                                    StreamParityLineIO
                                             |
                                             v
                                    PySerialByteStream
                                             |
                                             v
                                      physical byte link
                                             |
                              +--------------+--------------+
                              |                             |
                              v                             v
                       exact transcript              parity response
                              |                             |
                              +--------------+--------------+
                                             |
                                             v
                                      conformance report
                                             |
                                             v
                                       parity bench run
```

The deployment link may change. The semantic contracts above it do not.

## Design doctrine

1. **No decorative weirdness.** Visible behavior maps to real state, event, or documented presentation rule.
2. **Veilbreak is an anchor, not an oracle.** Phenomenology may generate interface hypotheses; it does not define arithmetic or ontology.
3. **Logical machine semantics are normative.**
4. **Machine persistence contains machine truth only.**
5. **Semantic identity does not hide operands.**
6. **Transitions are traced before they are animated.**
7. **Pixels are downstream of truth.**
8. **Trace-derived campaigns test subsystems, not imaginary instruction decoders.**
9. **Wire framing transports parity semantics; it does not create them.**
10. **Stream adapters move bytes; they do not interpret arithmetic.**
11. **Serial configuration is deployment state, not machine state.**
12. **Wire transcripts preserve evidence; they do not authenticate hardware.**
13. **Physicality is not correctness.**
14. **Hardware earns authority through parity.**
15. **Determinism wins.**
16. **Accuracy contracts are explicit.**
17. **Corpus inputs are frozen before they influence a revision.**
18. **Physical instruction encoding waits for physical evidence.**

## Repository status

**Pre-alpha / architecture stabilization.**

The host software path now reaches all the way to an optional explicitly configured serial port while preserving the existing parity/wire/transcript authority boundaries.

That does **not** mean TD-1 hardware exists or has passed. The next physical milestone remains the first real one-trit adapter advertising only demonstrated capability and returning measured bench telemetry.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/MACHINE_STATE.md`](docs/MACHINE_STATE.md)
- [`docs/TRACE.md`](docs/TRACE.md)
- [`docs/PARITY_CAMPAIGNS.md`](docs/PARITY_CAMPAIGNS.md)
- [`docs/PARITY_WIRE.md`](docs/PARITY_WIRE.md)
- [`docs/STREAM_LINE_IO.md`](docs/STREAM_LINE_IO.md)
- [`docs/SERIAL_ADAPTER.md`](docs/SERIAL_ADAPTER.md)
- [`docs/WIRE_TRANSCRIPTS.md`](docs/WIRE_TRANSCRIPTS.md)
- [`docs/HARDWARE_PARITY.md`](docs/HARDWARE_PARITY.md)
- [`docs/SEMANTIC_LOWERING.md`](docs/SEMANTIC_LOWERING.md)
- [`docs/RENDER_STATE.md`](docs/RENDER_STATE.md)
- [`docs/GEOMETRY.md`](docs/GEOMETRY.md)
- [`docs/RELIC_TIMELINE.md`](docs/RELIC_TIMELINE.md)
- [`docs/RELIC_PLAYER.md`](docs/RELIC_PLAYER.md)
- [`docs/CORPUS_PIPELINE.md`](docs/CORPUS_PIPELINE.md)
- [`docs/VEILBREAK_PROVENANCE.md`](docs/VEILBREAK_PROVENANCE.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/adr/`](docs/adr/)

## Epistemic boundary

TD-1 does **not** assume that DMT/Veilbreak reports establish extraterrestrial, interdimensional, or otherwise external intelligences. The project treats those reports as a structured phenomenological corpus capable of generating unconventional interface constraints and testable design hypotheses.

A valid machine checkpoint proves only reference-state reconstruction. A valid campaign proves deterministic vector derivation. A passing report proves only the tested operations represented by that report. A valid transcript proves only the canonical byte conversation it contains. A bench bundle proves transcript/report linkage and replay equivalence. A successful serial run proves the configured host byte path exchanged and evaluated those frames; it does not independently prove electrical quality, hardware authorship, or physical instruction execution.

**Human-built hardware. Exotic design provenance. Bench validation required.**
