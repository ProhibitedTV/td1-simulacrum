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
          v
 UART / USB serial / other byte link later
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

## Correlation

The capability handshake uses the fixed v1 correlation identifier:

```text
CAPS-v1
```

Parity exchanges derive their correlation ID deterministically from the canonical `ParityRequest` SHA-256:

```text
REQ-<first 24 hex characters>
```

The host rejects a response with the wrong kind or wrong correlation ID. The parsed `ParityResponse` must also reproduce the request session ID, sequence, and vector ID.

The device dispatcher performs the corresponding validation on inbound request frames.

## Host-side transport

`JsonLineParityTransport` implements the existing `ParityTransport` protocol.

It performs:

1. a capability request/response handshake;
2. capability caching for the life of the transport;
3. one canonical wire request for each accepted parity exchange;
4. response-kind and correlation validation;
5. restoration of the ordinary `ParityResponse` object.

Because it implements the existing protocol, `run_conformance()` and trace-derived `ParityCampaign` execution require no wire-specific arithmetic logic.

## Device-side dispatcher

`ParityWireDevice` wraps any existing `ParityTransport` target.

For CI, it wraps `ReferenceLoopbackTransport`. A future microcontroller-side implementation can reproduce the same envelope and parity schemas while replacing the in-memory channel with UART, USB CDC, or another byte stream.

The Python reference dispatcher is a protocol oracle, not a requirement that firmware run Python.

## Line I/O boundary

`ParityLineIO` deliberately exposes only:

```text
write_line(frame: bytes)
read_line() -> bytes
```

No serial library is part of the core package in v0.15. A later adapter may use `pyserial`, USB APIs, or another transport without changing the wire schema or the parity semantics above it.

`InMemoryParityLineIO` exists so CI exercises the exact encode -> device-dispatch -> decode path without physical hardware.

## Bench telemetry conventions

Parity responses already permit optional integer/string telemetry. Wire v1 standardizes the first bench key names:

| key | type | convention |
|---|---|---|
| `voltage_uv` | integer | sampled node voltage in microvolts |
| `settle_us` | integer | measured settling time in microseconds |
| `comparator_code` | string | adapter-defined comparator/decode code such as `00`, `10`, `11` |
| `sample_count` | integer | number of samples contributing to the reported observation |
| `board_revision` | string | stable human engineering board identifier |
| `temperature_millic` | integer | optional temperature in milli-degrees Celsius |

`BenchTelemetry` validates and round-trips these conventions.

These values are **metadata only** in v1. They do not alter the existing parity pass/fail evaluation. A future measured-acceptance schema may add explicit electrical criteria, but that must be a versioned engineering decision rather than a hidden side effect of telemetry.

For the planned TRIT_CELL_REV0 adapter, a plausible successful response may eventually resemble:

```json
{
  "voltage_uv": 2750000,
  "settle_us": 43,
  "comparator_code": "11",
  "sample_count": 16,
  "board_revision": "TRIT-REV0"
}
```

The numbers above are illustrative transport metadata, not a claim that a physical board has produced them.

## CLI

A saved trace-derived campaign can now traverse the exact wire codec while still using the deterministic reference target:

```bash
td1-parity wire-loopback campaign.json --output wire-run.json
```

Capability rejection can be exercised through the same framing path:

```bash
td1-parity wire-loopback campaign.json --target-max-width 3
```

The resulting artifact remains an ordinary `td1.parity-campaign-run`. The wire transport is not embedded as a new source of arithmetic authority.

## First physical adapter sequence

The intended next hardware path is:

1. validate one real trit cell on the bench;
2. implement the wire envelope on a tiny host/device adapter;
3. advertise only `trit_hold`, width 1;
4. run the existing three one-trit parity vectors;
5. report `voltage_uv`, `settle_us`, `comparator_code`, `sample_count`, and `board_revision` where available;
6. preserve the resulting parity report as the bench receipt;
7. expand capabilities only after measured evidence supports the next subsystem.

## Explicit non-goals

Wire v1 does not define:

- USB VID/PID;
- UART baud rate;
- connector type;
- PCB pinout;
- analog thresholds;
- ADC resolution;
- comparator hysteresis;
- sample cadence;
- retry/time-out policy for a real serial driver;
- electrical acceptance limits;
- instruction fetch/decode;
- physical instruction words;
- Issue #2 encoding.

Those belong to later adapter/hardware revisions.
