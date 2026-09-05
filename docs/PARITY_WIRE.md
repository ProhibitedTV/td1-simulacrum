# TD-1 Parity Wire Protocol

## Purpose

`td1.parity-wire` is the first byte-oriented adapter protocol between the host parity harness and a future physical TD-1 bench target.

It carries the existing parity contracts across a synchronous line channel. It does **not** redefine balanced-ternary arithmetic, hardware capabilities, conformance semantics, analog thresholds, or physical instruction encoding.

```text
parity campaign / golden vectors
          |
          v
   ParityTransport API
          |
          v
 JsonLineParityTransport
          |
          v
 canonical td1.parity-wire frame
          |
          v
      ParityLineIO
          |
          +------> optional RecordingParityLineIO
          |                     |
          |                     v
          |          td1.parity-wire-transcript
          |
          v
   StreamParityLineIO
          |
          v
 binary byte stream
          |
          v
 UART / USB CDC / other link later
          |
          v
      device dispatcher
          |
          v
 existing parity target
```

The rule is simple: **the wire moves parity truth; it does not become parity truth.**

## Schema

Wire v1 uses:

```text
schema  = td1.parity-wire
version = 1
encoding = utf-8-jsonl-canonical/v1
```

Every frame is one canonical JSON object followed by exactly one LF byte.

The envelope contains:

- `schema`;
- `version`;
- `kind`;
- `correlation_id`;
- `payload`.

The allowed v1 message kinds are:

- `capabilities_request`;
- `capabilities_response`;
- `parity_request`;
- `parity_response`.

Payloads wrap the existing `ParityCapabilities`, `ParityRequest`, and `ParityResponse` schemas. The wire layer does not copy their fields into a second semantic model.

## Canonical framing

The canonical JSON representation uses sorted keys, compact separators, ASCII-safe JSON, UTF-8 encoding, and one trailing LF.

The default maximum frame size is 65,536 bytes including the trailing LF.

A decoder rejects:

- empty frames;
- frames above the configured maximum;
- missing LF termination;
- CRLF termination;
- embedded line breaks;
- invalid UTF-8;
- invalid JSON;
- non-object JSON roots;
- unsupported schema/version/kind values;
- JSON that is semantically valid but not byte-for-byte canonical.

This intentionally removes serializer ambiguity from first-bench debugging.

## Nested payload canonicality

v0.22 hardens a distinction that matters at the hardware boundary: **a byte-canonical wire envelope is necessary but not sufficient.** The nested parity object must also already be in the exact canonical form of its own typed schema.

After parsing a `ParityCapabilities`, `ParityRequest`, or `ParityResponse`, the host/device wire adapter re-emits that object through its canonical `as_dict()` representation and requires the received nested payload to match exactly, including JSON value types. The comparison deliberately does not use Python's loose `bool == 1` or other coercive equality behavior.

The following are rejected even when the outer JSON frame is byte-canonical:

- `"sequence":"0"` where the schema requires integer `0`;
- `"max_width":"12"` where the schema requires integer `12`;
- booleans substituted for integer fields;
- omission of canonical default fields such as an empty response `detail`;
- capability operation/version/telemetry lists whose order or duplicates would be silently normalized by the model;
- any other payload that parses only because `int()`, `str()`, default insertion, sorting, or deduplication changes the received representation.

This is intentionally a parser/transport hardening of wire v1, not a wire-schema revision. Existing canonical frames are unchanged. The rule is:

> **Canonical transport bytes may not hide non-canonical parity schema values.**

## Correlation

The capability handshake uses the fixed v1 correlation identifier:

```text
CAPS-v1
```

Parity exchanges derive their correlation ID deterministically from the canonical `ParityRequest` SHA-256:

```text
REQ-<first 24 hex characters>
```

`parity_request_correlation()` is the public reference implementation of that derivation.

The host rejects a response with the wrong kind or wrong correlation ID. The parsed `ParityResponse` must also reproduce the request session ID, sequence, and vector ID.

The device dispatcher performs the corresponding validation on inbound request frames.

## Host-side transport

`JsonLineParityTransport` implements the existing `ParityTransport` protocol.

It performs:

1. a capability request/response handshake;
2. capability caching for the life of the transport;
3. one canonical wire request for each accepted parity exchange;
4. response-kind and correlation validation;
5. exact nested parity-payload canonicality validation;
6. restoration of the ordinary `ParityResponse` object.

Because it implements the existing protocol, `run_conformance()` and trace-derived `ParityCampaign` execution require no wire-specific arithmetic logic.

## Device-side dispatcher

`ParityWireDevice` wraps any existing `ParityTransport` target.

For CI, it wraps `ReferenceLoopbackTransport`. A future microcontroller-side implementation can reproduce the same envelope and parity schemas while replacing the in-memory channel with UART, USB CDC, or another byte stream.

Inbound parity requests must be canonical both as wire envelopes and as nested `ParityRequest` payloads before the target sees them.

The Python reference dispatcher is a protocol oracle, not a requirement that firmware run Python.

## Line I/O boundary

`ParityLineIO` deliberately exposes only:

```text
write_line(frame: bytes)
read_line() -> bytes
```

`InMemoryParityLineIO` exists so CI exercises the exact encode -> device-dispatch -> decode path without physical hardware.

v0.17 adds `StreamParityLineIO`, a concrete implementation over minimal readable/writable binary stream protocols. This is the bridge intended for future UART/USB-CDC libraries.

The stream adapter:

- completes partial writes until all supplied frame bytes are accepted;
- optionally flushes writers that expose `flush()`;
- reassembles fragmented reads;
- returns exactly one LF-terminated frame at a time;
- preserves coalesced bytes belonging to later frames;
- bounds incoming buffering using the existing wire frame ceiling;
- distinguishes empty EOF, partial EOF, oversized input, invalid read/write results, and underlying I/O failure;
- reports deterministic byte/frame/buffer counters without wall-clock state.

It does not parse or repair JSON. Canonical wire validation remains here in the wire layer rather than moving down into stream mechanics.

No serial library is required. A later pyserial or USB integration may wrap/configure a compatible binary stream without changing the wire schema.

See [`STREAM_LINE_IO.md`](STREAM_LINE_IO.md) and ADR 0017.

## Recording and replay

v0.16 added deterministic transport evidence without changing wire v1 itself.

`RecordingParityLineIO` may wrap any line channel, including `StreamParityLineIO`. It records each successful canonical host write and device read as an exact `td1.parity-wire-transcript` record containing direction, ordinal, full frame text, frame SHA-256, decoded kind/correlation, and envelope digest.

`ReplayParityLineIO` then requires host request bytes to match the saved transcript exactly and returns the saved response bytes in sequence.

A completed transcript enforces alternating request/response order, matching correlation IDs, and matching request/response message classes.

`td1.parity-bench-run` binds a saved campaign run to the exact transcript implied by its conformance report. The bundle rejects a transcript from a different target, session, vector order, response set, or telemetry set.

Because recording sits above `ParityLineIO`, moving from in-memory line I/O to stream-backed line I/O requires no transcript schema change.

See [`WIRE_TRANSCRIPTS.md`](WIRE_TRANSCRIPTS.md) and ADR 0016.

## Bench telemetry conventions

Parity responses already permit optional integer/string telemetry. Wire v1 standardizes the first bench key names:

| key | type | convention |
|---|---|---|
| `voltage_uv` | signed integer | sampled node voltage in microvolts relative to the bench/device reference |
| `settle_us` | integer | measured settling time in microseconds |
| `comparator_code` | string | adapter-defined comparator/decode code; no project-wide electrical code mapping is assumed |
| `sample_count` | integer | number of samples contributing to the reported observation |
| `board_revision` | string | stable human engineering board identifier |
| `temperature_millic` | integer | optional temperature in milli-degrees Celsius |

`BenchTelemetry` validates and round-trips these conventions. `voltage_uv` is deliberately signed: wire v1 does not assume single-supply, split-supply, shifted-level, or any other physical ternary encoding.

These values are **metadata only** in v1. They do not alter the existing parity pass/fail evaluation. A future measured-acceptance schema may add explicit electrical criteria, but that must be a versioned engineering decision based on reviewed topology and characterization evidence rather than a hidden side effect of telemetry.

Tests use synthetic signed values only to exercise serialization. They are not recommended TD-1 rail, state, threshold, or comparator values. See [`HARDWARE_GROUND_TRUTH.md`](HARDWARE_GROUND_TRUTH.md).

## CLI

A saved trace-derived campaign can traverse the exact wire codec while still using the deterministic reference target:

```bash
td1-parity wire-loopback campaign.json --output wire-run.json
```

The same command can preserve exact line evidence and the linked bench bundle:

```bash
td1-parity wire-loopback campaign.json \
  --output wire-run.json \
  --transcript-output wire-transcript.json \
  --bench-output bench-run.json
```

Verify exact transcript framing/integrity:

```bash
td1-parity wire-transcript-verify wire-transcript.json
```

Replay a complete bench bundle through the normal wire transport:

```bash
td1-parity bench-run-replay bench-run.json
```

Capability rejection can be exercised through the same framing path:

```bash
td1-parity wire-loopback campaign.json --target-max-width 3
```

The ordinary campaign-run artifact remains the conformance result. Transcript and bench-run artifacts add transport evidence; they are not new sources of arithmetic authority.

## First physical adapter sequence

The intended next hardware path is:

1. resolve the first-cell schematic from reviewed builder feedback, component datasheets, and actual intended topology; do not build from the earlier speculative numeric recipe;
2. power and characterize one physical trit cell according to [`HARDWARE_GROUND_TRUTH.md`](HARDWARE_GROUND_TRUTH.md), preserving signed rail/reference/output/load/switching measurements in `td1.trit-cell-characterization`;
3. select the actual UART/USB-CDC byte interface and expose it as a compatible binary stream;
4. wrap that stream with `StreamParityLineIO`;
5. wrap the line adapter with `RecordingParityLineIO`;
6. use `JsonLineParityTransport` unchanged above it;
7. advertise only `trit_hold`, width 1 after the cell has been electrically characterized;
8. run the existing three one-trit parity vectors;
9. report real `voltage_uv`, `settle_us`, `comparator_code`, `sample_count`, and `board_revision` telemetry where available;
10. save characterization evidence plus the parity report, exact wire transcript, and generic wire-evidence bundle;
11. replay the wire evidence offline;
12. define electrical acceptance criteria only after measurements justify them;
13. expand capabilities only after measured evidence supports the next subsystem.

## Explicit non-goals

Wire/transcript/stream v1 does not define:

- pyserial or another required serial package;
- USB VID/PID;
- UART baud rate;
- connector type;
- PCB pinout;
- read/write timeout or reconnect policy;
- supply topology;
- physical trit voltages;
- analog thresholds;
- ADC resolution;
- comparator hysteresis;
- sample cadence;
- electrical acceptance limits;
- authenticated hardware identity;
- instruction fetch/decode;
- physical instruction words;
- Issue #2 encoding.

Those belong to later adapter/hardware revisions backed by actual constraints and evidence.