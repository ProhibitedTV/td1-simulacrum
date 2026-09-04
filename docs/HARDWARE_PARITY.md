# Emulator-to-Hardware Parity

## Purpose

TD-1 hardware is not allowed to become authoritative because it is physical. A physical ternary subsystem replaces an emulated subsystem only after it reproduces the reference model for the same deterministic stimuli.

The parity layer defines that conformance boundary independently from the concrete electrical link used by a bench adapter.

```text
reference model
    |
    +------> fixed golden vectors
    |
    +------> execution trace -> td1.parity-campaign
                               |
                               v
                        td1.parity-request
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
                     binary byte stream
                               |
                               v
                        physical target
                               |
                               v
                        td1.parity-response
                               |
                               v
                        td1.parity-report
                               |
                               v
                   td1.parity-campaign-run
                               |
                transcript ----+
                               |
                               v
                     td1.parity-bench-run
```

> Hardware earns authority through parity.

## Transport neutrality

The parity semantics do not specify USB, UART, CAN, Ethernet, GPIO, SWD, SPI, or another physical link.

A host adapter implements two parity operations:

- advertise `ParityCapabilities`;
- exchange a `ParityRequest` for a `ParityResponse`.

`td1.parity-wire` gives those existing contracts a deterministic byte-line representation for first-bench integration. `StreamParityLineIO` now gives that line contract a concrete implementation over ordinary binary reader/writer streams without making pyserial, baud rate, USB identity, connector choices, analog sampling, or board-specific behavior part of TD-1 arithmetic semantics.

The transcript layer records the exact canonical bytes observed at the line boundary but likewise remains downstream of parity truth.

## Versioned schemas

The base layer defines:

- `td1.parity-capabilities`;
- `td1.parity-request`;
- `td1.parity-response`;
- `td1.parity-report`.

The workload-derived layer adds:

- `td1.parity-campaign`;
- `td1.parity-campaign-run`.

The byte-oriented adapter layer adds:

- `td1.parity-wire`.

The transport-evidence layer adds:

- `td1.parity-wire-transcript`;
- `td1.parity-bench-run`.

`StreamParityLineIO` is intentionally an adapter implementation rather than a new semantic artifact schema.

Artifacts use deterministic canonical serialization and SHA-256 fingerprints where applicable.

## Capability negotiation

A target advertises:

- stable target identifier;
- supported parity protocol versions;
- supported operations;
- maximum ternary slice width;
- optional telemetry keys.

Unsupported vectors are rejected before exchange and recorded as `unsupported` rather than being misclassified as a target malfunction.

Current operation classes are:

- `trit_hold`;
- `register_load`;
- `negate`;
- `add`;
- `sub`.

## Fixed golden vectors

### First physical campaign: trit/register slice

`golden_register_vectors()` begins with the smallest meaningful physical test:

```text
-
0
+
```

Each one-trit state must be driven, held, observed, and returned through the adapter without spontaneous semantic change.

The same vector set then tests register-slice loads at the requested width using zero, +/-1, maximum/minimum representable values, and an alternating ternary pattern.

This is the intended bridge from `TRIT_CELL_REV0` bench work into software conformance.

### Later ALU campaign

`golden_alu_vectors()` includes negation, basic addition/subtraction, and fixed-width wrap cases.

Those vectors exist so the reference oracle is stable before physical ALU design begins. They do not imply that an ALU board exists.

## Trace-derived workload campaigns

Fixed golden vectors answer “does this subsystem handle the reference edge cases?”

`td1.parity-campaign` adds a second question:

> Does this subsystem handle the exact ternary values encountered during a real TD-1 logical workload?

A campaign embeds its complete source `td1.execution-trace`, exact initial/final `td1.machine-state` checkpoints, event provenance, and deterministic subsystem vectors.

Current mappings are deliberately narrow:

- `LDI`, `MOV`, `LD` -> `register_load`;
- `NEG` -> `negate`;
- `ADD` -> `add`;
- `SUB` -> `sub`;
- `ADDI` -> subsystem `add` with the immediate represented as a fixed-width 12-trit operand.

The `ADDI` mapping does **not** test physical `ADDI` instruction decoding. Likewise, mapping `LD` to a register-load vector tests the destination register value path represented by the current parity surface; it does not claim physical memory-read parity.

Control-flow, compare, store, no-op, and halt semantics remain unclaimed until the parity operation surface gains faithful tests for them.

Every saved campaign is re-derived from its embedded trace at load time. `td1.parity-campaign-run` then binds the exact campaign vector set to one exact `td1.parity-report`.

See [`PARITY_CAMPAIGNS.md`](PARITY_CAMPAIGNS.md) and ADR 0014.

## Observable state digests

A physical slice result is fingerprinted from width and normalized ternary value.

The response carries the observed value and observed-state digest. The harness recomputes the digest and distinguishes:

1. transport/device status failure;
2. observed ternary value mismatch;
3. observed-state digest mismatch.

These are deterministic integrity fingerprints, not cryptographic authorship claims.

## Parity wire framing

Wire v1 uses canonical UTF-8 JSON Lines. Each frame is one canonical JSON object followed by exactly one LF.

Allowed message kinds are:

- `capabilities_request`;
- `capabilities_response`;
- `parity_request`;
- `parity_response`.

The envelope wraps the existing parity payload schemas. It does not duplicate or reinterpret their fields.

The default maximum frame size is 65,536 bytes including the LF. Decoding rejects empty, malformed, oversized, CRLF, multi-line, invalid-UTF-8, or noncanonical frames.

`JsonLineParityTransport` adapts a minimal `ParityLineIO` byte channel to the existing `ParityTransport` interface. `ParityWireDevice` is the reference device-side dispatcher. `InMemoryParityLineIO` lets CI exercise the exact byte codec without a serial device.

See [`PARITY_WIRE.md`](PARITY_WIRE.md) and ADR 0015.

## Stream-backed host line I/O

`StreamParityLineIO` implements the existing `ParityLineIO` boundary over one duplex binary stream or explicit reader/writer streams.

It owns only byte transport concerns:

- deterministic partial-write completion;
- optional writer `flush()`;
- fragmented-read buffering;
- extraction of exactly one LF-terminated frame;
- preservation of bytes belonging to later frames;
- enforcement of the existing wire frame ceiling while buffering;
- distinct empty-EOF and partial-frame EOF failures;
- explicit invalid return-type, zero-progress, and underlying I/O errors;
- deterministic bytes/frames/buffered-byte statistics with no wall-clock state.

It deliberately does **not** duplicate canonical JSON validation. `JsonLineParityTransport` and `decode_wire_frame()` remain responsible for wire semantics.

The adapter therefore composes as:

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
binary stream
```

A future pyserial-backed UART/USB-CDC path can wrap or directly satisfy the binary stream protocol without changing parity, wire, transcript, or bench-run schemas.

See [`STREAM_LINE_IO.md`](STREAM_LINE_IO.md) and ADR 0017.

## Exact wire transcripts

`td1.parity-wire-transcript` records the exact canonical traffic successfully observed at `ParityLineIO`.

Each ordered record preserves:

- host/device direction;
- contiguous ordinal;
- exact frame text including LF;
- frame-byte SHA-256;
- decoded message kind;
- correlation ID;
- envelope digest.

Every frame is revalidated with the same canonical wire decoder used for live transport. A completed transcript requires alternating host request/device response pairs and matching message classes/correlations.

`RecordingParityLineIO` can wrap the in-memory channel or the stream-backed channel. It does not alter `ParityTransport` semantics.

`ReplayParityLineIO` is deliberately strict: host request bytes must match the transcript exactly, responses are returned exactly as recorded, and the entire transcript must be consumed.

A report may contain capability-rejected `unsupported` records that produced no device traffic. `transcript_for_report()` preserves that distinction by reconstructing wire exchanges only for requests the advertised capabilities accepted.

See [`WIRE_TRANSCRIPTS.md`](WIRE_TRANSCRIPTS.md) and ADR 0016.

## Bench-run bundles

`td1.parity-bench-run` binds:

- one exact `td1.parity-campaign-run`;
- one exact `td1.parity-wire-transcript`.

Validation regenerates the canonical wire conversation implied by the saved report and requires exact transcript equality. A transcript from another target, session, vector order, response set, or telemetry set therefore cannot be silently substituted.

`replay_bench_run()` then runs the saved campaign through normal `JsonLineParityTransport` over `ReplayParityLineIO`, reuses the saved parity session ID, consumes every transcript record, and requires the regenerated campaign run to match canonically.

This is transport evidence, not authenticated hardware identity. SHA-256 values are integrity fingerprints only.

## Fault reporting and telemetry

Responses may report:

- `ok`;
- `unsupported`;
- `fault`;
- `timeout`;
- `error`.

The v1 bench telemetry vocabulary is:

```text
voltage_uv
settle_us
comparator_code
sample_count
board_revision
temperature_millic
```

`voltage_uv`, `settle_us`, `sample_count`, and `temperature_millic` use scaled integers. `comparator_code` and `board_revision` are strings.

These values are metadata only in wire v1. They do not alter arithmetic pass/fail evaluation. Measured electrical acceptance limits require a separate future versioned contract after actual bench distributions exist.

When telemetry appears in a real device response, the transcript preserves the exact response bytes containing it and the bench bundle links those bytes to the conformance report.

## Replayable conformance reports

A `td1.parity-report` stores capability advertisement/digest, vector-set digest, every request/response, deterministic pass/fail evaluation, exact discrepancy text, and summary counts.

Loading a report revalidates identities, vector semantics, digests, pass flags, discrepancies, capability digest, vector-set digest, and summary.

A report is the evaluated conformance receipt. A transcript is the wire receipt. A bench run binds the two.

## Reference and stream integration targets

`ReferenceLoopbackTransport` implements the parity contract entirely in software. It can return deterministic success, forced fault/timeout/error states, deliberate observed-value corruption, and restricted maximum width.

Passing direct loopback proves the host parity infrastructure, not physical ternary hardware.

The in-memory wire path wraps the same target with `ParityWireDevice`, `InMemoryParityLineIO`, and `JsonLineParityTransport`. Passing that path additionally proves the canonical wire codec and request/response correlation logic.

The v0.17 stream integration replaces the in-memory line channel with a deliberately fragmenting scripted binary stream under `StreamParityLineIO`, while keeping `RecordingParityLineIO` above it. A complete trace-derived campaign must still produce a valid bench bundle and replay identically. That proves stream buffering/composition, not physical hardware.

## CLI

Base fixed-vector workflows:

```bash
td1-sim parity-vectors --width 12

td1-sim parity-vectors --width 3 --register-only

td1-sim parity-loopback --width 12

td1-sim parity-verify report.json
```

Trace-derived workload workflows:

```bash
td1-parity build examples/sum.td1 --output sum.campaign.json

td1-parity verify sum.campaign.json

td1-parity loopback sum.campaign.json --output sum.run.json

td1-parity wire-loopback sum.campaign.json \
  --output sum.wire.run.json \
  --transcript-output sum.wire.transcript.json \
  --bench-output sum.bench.json

td1-parity wire-transcript-verify sum.wire.transcript.json

td1-parity bench-run-replay sum.bench.json

td1-parity run-verify sum.wire.run.json
```

Capability rejection can be exercised deliberately with `--target-max-width` in both direct and wire-loopback modes.

`StreamParityLineIO` is a library adapter rather than a new CLI transport selector in v0.17. A real serial CLI belongs after the actual bench interface is selected.

## Physical adapter sequence

The first real integration remains intentionally small:

1. build and measure one physical trit cell;
2. choose the actual UART/USB-CDC/other byte link;
3. expose that link as a compatible binary reader/writer;
4. wrap it with `StreamParityLineIO`;
5. wrap that with `RecordingParityLineIO`;
6. speak the existing `td1.parity-wire` envelope on the device side;
7. advertise only `trit_hold`, `max_width=1`;
8. run the three `TRIT-*` fixed golden vectors;
9. preserve voltage/settling/comparator/sample/board telemetry;
10. save the conformance report, exact transcript, and linked bench-run bundle;
11. replay that bundle offline as a regression receipt;
12. expand capability only after the one-trit report passes;
13. repeat for a multi-trit register slice;
14. run workload-derived register campaigns where capabilities allow;
15. only then begin physical ALU conformance and ALU workload campaigns.

A board must not advertise capabilities merely because its schematic intends to support them.

## Deferred work

This revision does not define:

- physical connector pinout;
- UART baud rate or USB device identity;
- pyserial or another concrete host serial dependency;
- COM/tty discovery;
- retry/reconnect policy;
- analog threshold values;
- sample timing;
- hysteresis/calibration policy;
- electrical acceptance thresholds;
- authenticated hardware identity;
- full-machine state replacement;
- cycle-accurate execution;
- physical instruction fetch/decode;
- physical 12-trit instruction encoding.

Those decisions belong to later hardware/adapter revisions and can consume the transport-neutral parity, campaign, wire, stream, and transcript contracts without redefining them.
