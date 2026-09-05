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
- transport-neutral physical parity contracts;
- explicit fixed first-hardware golden suites;
- trace-derived parity campaigns tied to real logical workloads;
- canonical `td1.parity-wire` framing beneath the parity API;
- deterministic wire transcripts, generic report/transcript evidence, and replayable campaign bench bundles;
- stream-backed `ParityLineIO` over ordinary binary streams;
- **an optional pyserial live-bench adapter that can carry the exact existing parity/wire/evidence stack to a real serial-class device without making serial configuration machine semantics.**

The long-term target is **hardware parity**: physical TD-1 subsystems progressively replace emulated subsystems while preserving identical externally observable behavior.

## Current baseline — v0.19 pre-alpha

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
- explicit `golden_trit_vectors()` for exactly `-`, `0`, `+` one-trit hold tests;
- backward-compatible register golden vectors derived from that trit prefix;
- deterministic `register_load`, `negate`, `add`, and `sub` vectors;
- explicit `ok`, `unsupported`, `fault`, `timeout`, and `error` outcomes;
- workload-derived `td1.parity-campaign` and `td1.parity-campaign-run` artifacts;
- canonical `td1.parity-wire` JSON Lines framing;
- `JsonLineParityTransport` and reference `ParityWireDevice`;
- `InMemoryParityLineIO` for pure-software integration;
- `RecordingParityLineIO` and strict `ReplayParityLineIO`;
- versioned `td1.parity-wire-transcript`, `td1.parity-wire-evidence`, and `td1.parity-bench-run` artifacts;
- shared deterministic report/transcript validation for generic and campaign evidence;
- replay of generic wire evidence using exact saved vectors/session IDs;
- bench telemetry conventions for voltage, settling, comparator state, samples, board revision, and optional temperature;
- `StreamParityLineIO` over generic binary streams;
- optional `PySerialByteStream` live deployment adapter;
- `td1-parity serial-golden` for fixed first-hardware suites;
- `td1-parity serial-run` for trace-derived workload campaigns;
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

## First-hardware golden vectors

The first planned physical target is deliberately smaller than a workload campaign. It should advertise only:

```text
operations = [trit_hold]
max_width  = 1
```

and run exactly:

```text
TRIT-NEG   -
TRIT-ZERO  0
TRIT-POS   +
```

That suite is fixed bench conformance, not trace-derived workload provenance.

Run it against an explicitly configured serial device:

```bash
td1-parity serial-golden \
  --suite trit \
  --port /dev/ttyACM0 \
  --baud 230400 \
  --read-timeout 2.0 \
  --write-timeout 2.0 \
  --report-output trit.report.json \
  --transcript-output trit.transcript.json \
  --evidence-output trit.evidence.json
```

For a target advertising only `trit_hold`, width 1, the transcript contains exactly one capability exchange plus three parity exchanges.

The `register` fixed suite is available later with `--suite register --width N`.

See [`docs/FIRST_HARDWARE_GOLDEN.md`](docs/FIRST_HARDWARE_GOLDEN.md) and ADR 0019.

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

## Wire transcripts and evidence

`td1.parity-wire-transcript` preserves exact canonical host/device frames.

v0.19 adds generic `td1.parity-wire-evidence`, which binds **any** `td1.parity-report` to the exact transcript implied by that report. This is the evidence root used by fixed first-hardware suites.

Verify and replay generic evidence:

```bash
td1-parity wire-evidence-verify trit.evidence.json

td1-parity wire-evidence-replay trit.evidence.json
```

Trace-derived campaigns still use `td1.parity-bench-run`:

```bash
td1-parity wire-loopback sum.campaign.json \
  --output sum.wire.run.json \
  --transcript-output sum.wire.transcript.json \
  --bench-output sum.bench.json

td1-parity bench-run-replay sum.bench.json
```

Both evidence types use the same deterministic report/transcript reconstruction rule. The campaign-specific bench schema remains v1.

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

The host can open a real serial port through:

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

Use `serial-golden` for fixed bring-up suites and `serial-run` for saved trace-derived campaigns.

A workload campaign example:

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

Port, baud rate, and host timeout values are deployment configuration. They may appear in the CLI summary but are not silently embedded into canonical report, campaign-run, transcript, evidence, or bench-run artifacts.

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

Logical execution, semantic lowering, persistence, fixed golden suites, parity campaigns, wire framing, stream adapters, serial transport, transcripts, and evidence replay do not replace the missing input that matters for Issue #2: measurements and constraints from first physical ternary hardware.

Software does not get to vote copper out of the room.

## Authority layering

```text
reference semantics
      |
      +----> fixed golden suites ----------+
      |                                    |
      +----> execution trace -> campaign --+
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
                                      /          \
                                     v            v
                            generic evidence   campaign run
                                                  |
                                                  v
                                              bench run
```

The deployment link and vector source may change. The semantic contracts above them do not.

## Design doctrine

1. **No decorative weirdness.** Visible behavior maps to real state, event, or documented presentation rule.
2. **Veilbreak is an anchor, not an oracle.** Phenomenology may generate interface hypotheses; it does not define arithmetic or ontology.
3. **Logical machine semantics are normative.**
4. **Machine persistence contains machine truth only.**
5. **Semantic identity does not hide operands.**
6. **Transitions are traced before they are animated.**
7. **Pixels are downstream of truth.**
8. **Fixed golden suites test explicit focused subsystem claims without fake workload provenance.**
9. **Trace-derived campaigns test subsystems, not imaginary instruction decoders.**
10. **Wire framing transports parity semantics; it does not create them.**
11. **Stream adapters move bytes; they do not interpret arithmetic.**
12. **Serial configuration is deployment state, not machine state.**
13. **Wire transcripts and evidence preserve exact receipts; they do not authenticate hardware.**
14. **Physicality is not correctness.**
15. **Hardware earns authority through parity.**
16. **Determinism wins.**
17. **Accuracy contracts are explicit.**
18. **Corpus inputs are frozen before they influence a revision.**
19. **Physical instruction encoding waits for physical evidence.**

## Repository status

**Pre-alpha / first-hardware host-path ready.**

The host software can now express the smallest honest first-copper test: a target advertising only `trit_hold`, width 1, receiving exactly three fixed golden vectors over the same canonical serial/wire/evidence stack used by later subsystems.

That does **not** mean TD-1 hardware exists or has passed. The next milestone is physical: build and measure `TRIT_CELL_REV0`, implement the device-side wire endpoint, run `serial-golden --suite trit`, preserve the evidence, and inspect the actual analog distributions before defining electrical acceptance limits.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/MACHINE_STATE.md`](docs/MACHINE_STATE.md)
- [`docs/TRACE.md`](docs/TRACE.md)
- [`docs/PARITY_CAMPAIGNS.md`](docs/PARITY_CAMPAIGNS.md)
- [`docs/PARITY_WIRE.md`](docs/PARITY_WIRE.md)
- [`docs/STREAM_LINE_IO.md`](docs/STREAM_LINE_IO.md)
- [`docs/SERIAL_ADAPTER.md`](docs/SERIAL_ADAPTER.md)
- [`docs/FIRST_HARDWARE_GOLDEN.md`](docs/FIRST_HARDWARE_GOLDEN.md)
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

A valid machine checkpoint proves only reference-state reconstruction. A valid fixed golden report proves only the explicit vectors it evaluated. A valid campaign proves deterministic vector derivation from its logical trace. A valid transcript proves only the canonical byte conversation it contains. A valid wire-evidence bundle proves report/transcript linkage and replay equivalence. A campaign bench bundle additionally binds that relationship to one exact trace-derived campaign. A successful serial run proves the configured host byte path exchanged and evaluated those frames; it does not independently prove electrical quality, hardware authorship, or physical instruction execution.

**Human-built hardware. Exotic design provenance. Bench validation required.**
