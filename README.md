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
- deterministic trace time-travel reconstruction and event queries;
- deterministic live breakpoints/watchpoints over the same trace authority;
- native State Weave semantic IR and typed lowering;
- reversible 27-state microglyph encoding;
- Observer Continuity groundwork;
- frozen Veilbreak-derived provenance tooling;
- deterministic native geometry, SVG rendering, Relic timelines, morphs, and browser playback;
- transport-neutral physical parity contracts;
- explicit fixed first-hardware golden suites;
- trace-derived parity campaigns tied to real logical workloads;
- canonical `td1.parity-wire` framing beneath the parity API;
- strict nested parity-payload canonicality at the live wire boundary;
- deterministic wire transcripts, generic report/transcript evidence, and replayable campaign bench bundles;
- stream-backed `ParityLineIO` over ordinary binary streams;
- **an optional pyserial live-bench adapter that can carry the exact existing parity/wire/evidence stack to a real serial-class device without making serial configuration machine semantics.**

The long-term target is **hardware parity**: physical TD-1 subsystems progressively replace emulated subsystems while preserving identical externally observable behavior.

## Current baseline — v0.22 pre-alpha

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

### Engineering inspection stack

- versioned `td1.execution-trace` with exact before/after complete machine digests;
- exact register/memory/control deltas per logical instruction;
- deterministic trace replay verification against source programs;
- shared incremental `TraceRecorder` for complete runs and exact non-halted prefixes;
- `trace_state_at()` reconstruction of any trace boundary as ordinary `td1.machine-state` truth;
- digest-validated delta application that rejects corrupted or incomplete state changes;
- seek/forward/backward `TraceCursor` over immutable trace boundaries;
- deterministic event queries for logical opcode, instruction index, register/memory touches, condition changes, and halt transitions;
- `td1-trace` CLI for trace-state extraction and event search;
- versioned `td1.debug-run` artifacts that embed exact trace prefixes and deterministic stop metadata;
- pre-instruction instruction-index/opcode breakpoints;
- post-instruction register/memory watchpoints;
- explicit HALT, breakpoint, watchpoint, and event-budget stop reasons;
- `td1-debug` CLI for deterministic stop runs and replay verification.

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
- exact nested `ParityCapabilities`, `ParityRequest`, and `ParityResponse` payload checks that reject receiver coercion/default/list normalization;
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
- no default baud rate, automatic port discovery, connector choice, or pyserial requirement in core installs;
- warning-clean pytest policy: Python warnings are test failures.

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

A `td1.execution-trace` may represent a complete halted execution or an exact non-halted prefix. Replay verification executes exactly the recorded event count and requires canonical equality.

## Deterministic trace time travel

v0.20 made exact traces directly inspectable without creating a second execution engine.

A trace containing `N` events has `N + 1` exact boundaries. Position `0` is the initial machine state; position `N` is the final state after all events. Every traversed delta must reproduce the existing before/after complete machine digest chain.

Reconstruct an exact checkpoint after five events:

```bash
td1-trace state trace.json --position 5
```

Write that checkpoint as ordinary `td1.machine-state`:

```bash
td1-trace state trace.json \
  --position 5 \
  --output step5.machine.json
```

Find every `ADD` that changes R1:

```bash
td1-trace find trace.json --op ADD --register R1
```

Find writes touching memory word 10, condition changes, or the transition into HALT:

```bash
td1-trace find trace.json --memory 10

td1-trace find trace.json --condition-change

td1-trace find trace.json --halt-transition
```

`TraceCursor` can seek, step forward, and step backward across immutable trace boundaries. Backward movement reconstructs an earlier state from trace truth; it does not reverse-execute synthetic inverse instructions.

See [`docs/TRACE_INSPECTION.md`](docs/TRACE_INSPECTION.md) and ADR 0020.

## Deterministic live debugging

v0.21 adds host-side live stopping without adding debugger instructions or debugger-owned machine state.

Breakpoints are checked **before** execution:

```bash
td1-debug run examples/sum.td1 --break-ip 4 --output before-ip4.debug.json

td1-debug run examples/sum.td1 --break-op ST --output before-store.debug.json
```

Watchpoints are checked **after** the real instruction event that changed the watched state:

```bash
td1-debug run examples/sum.td1 --watch-register R1 --output r1.debug.json

td1-debug run examples/sum.td1 --watch-memory 10 --output memory10.debug.json
```

A deterministic event budget can stop non-terminating execution without pretending the machine executed `HALT`:

```bash
td1-debug run program.td1 --max-events 1000 --output bounded.debug.json
```

Replay the program, embedded trace prefix, and stop decision exactly:

```bash
td1-debug verify examples/sum.td1 before-store.debug.json
```

`td1.debug-run` stop metadata explains why the host paused. It does not change registers, memory, the instruction pointer, condition state, step count, or HALT state.

See [`docs/DEBUGGING.md`](docs/DEBUGGING.md) and ADR 0021.

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

v0.22 also requires nested parity payloads to reproduce their typed canonical representation exactly after parsing. A byte-canonical envelope carrying `"sequence":"0"` instead of integer `0`, an omitted canonical default field, or a capability list that only becomes canonical after sorting/deduplication is rejected. Canonical framing cannot hide receiver coercion.

See [`docs/PARITY_WIRE.md`](docs/PARITY_WIRE.md) and ADR 0022.

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

Logical execution, semantic lowering, persistence, trace inspection, deterministic debugging, fixed golden suites, parity campaigns, wire framing, stream adapters, serial transport, transcripts, and evidence replay do not replace the missing input that matters for Issue #2: measurements and constraints from first physical ternary hardware.

Software does not get to vote copper out of the room.

## Authority layering

```text
reference machine
      |
      +----> td1.machine-state
      |
      +----> TraceRecorder ----> td1.execution-trace ----> deterministic time travel
      |                              |                              |
      |                              |                              v
      |                              |                      td1.machine-state
      |                              |
      |                              +----> td1.debug-run
      |                              |
      |                              +----> trace-derived campaigns --------+
      |                                                                   |
      +----> fixed golden suites ------------------------------------------+
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

Trace inspection cannot alter the trace it consumes. Debugger stops cannot alter machine truth. The deployment link and vector source may change. The semantic contracts above them do not.

## Design doctrine

1. **No decorative weirdness.** Visible behavior maps to real state, event, or documented presentation rule.
2. **Veilbreak is an anchor, not an oracle.** Phenomenology may generate interface hypotheses; it does not define arithmetic or ontology.
3. **Logical machine semantics are normative.**
4. **Machine persistence contains machine truth only.**
5. **Semantic identity does not hide operands.**
6. **Transitions are traced before they are animated.**
7. **Time travel reconstructs trace truth; it does not reverse-invent execution.**
8. **Debugger stops observe execution; they do not become execution.**
9. **Pixels are downstream of truth.**
10. **Fixed golden suites test explicit focused subsystem claims without fake workload provenance.**
11. **Trace-derived campaigns test subsystems, not imaginary instruction decoders.**
12. **Wire framing transports parity semantics; it does not create them.**
13. **Canonical envelope bytes do not excuse non-canonical nested parity values.**
14. **Stream adapters move bytes; they do not interpret arithmetic.**
15. **Serial configuration is deployment state, not machine state.**
16. **Wire transcripts and evidence preserve exact receipts; they do not authenticate hardware.**
17. **Physicality is not correctness.**
18. **Hardware earns authority through parity.**
19. **Determinism wins.**
20. **Accuracy contracts are explicit.**
21. **Corpus inputs are frozen before they influence a revision.**
22. **Physical instruction encoding waits for physical evidence.**

## Repository status

**Pre-alpha / audit-hardened live wire boundary + deterministic trace debugging + first-hardware host path ready.**

The logical emulator can be inspected backward and forward at exact trace boundaries and can stop live execution on deterministic breakpoints/watchpoints without creating a second execution authority. Separately, the host software can express the smallest honest first-copper test: a target advertising only `trit_hold`, width 1, receiving exactly three fixed golden vectors over the canonical serial/wire/evidence stack. v0.22 additionally rejects nested wire payloads that would become valid only through receiver coercion and makes Python warnings fail the test run.

Neither capability means physical TD-1 hardware exists or has passed. The next hardware milestone remains physical: build and measure `TRIT_CELL_REV0`, implement the device-side wire endpoint, run `serial-golden --suite trit`, preserve the evidence, and inspect the actual analog distributions before defining electrical acceptance limits.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/MACHINE_STATE.md`](docs/MACHINE_STATE.md)
- [`docs/TRACE.md`](docs/TRACE.md)
- [`docs/TRACE_INSPECTION.md`](docs/TRACE_INSPECTION.md)
- [`docs/DEBUGGING.md`](docs/DEBUGGING.md)
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
- [`docs/AUDIT_2026-09.md`](docs/AUDIT_2026-09.md)
- [`docs/ROADMAP.md`](docs/ROADMAP.md)
- [`docs/adr/`](docs/adr/)

## Epistemic boundary

TD-1 does **not** assume that DMT/Veilbreak reports establish extraterrestrial, interdimensional, or otherwise external intelligences. The project treats those reports as a structured phenomenological corpus capable of generating unconventional interface constraints and testable design hypotheses.

A valid machine checkpoint proves only reference-state reconstruction. A trace-time-travel checkpoint proves only deterministic reconstruction of the saved logical trace boundary and its complete digest chain. A valid debug run proves only deterministic reference execution to the recorded host-side stop condition and exact embedded trace prefix. A valid fixed golden report proves only the explicit vectors it evaluated. A valid campaign proves deterministic vector derivation from its logical trace. A valid transcript proves only the canonical byte conversation it contains. A valid wire-evidence bundle proves report/transcript linkage and replay equivalence. A campaign bench bundle additionally binds that relationship to one exact trace-derived campaign. A successful serial run proves the configured host byte path exchanged and evaluated those frames; it does not independently prove electrical quality, hardware authorship, or physical instruction execution.

**Human-built hardware. Exotic design provenance. Bench validation required.**