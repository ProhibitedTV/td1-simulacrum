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
                    PySerialByteStream
                               |
                               v
                    optional serial link
                               |
                               v
                        physical target
                               |
                               v
                        td1.parity-response
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
        exact wire transcript         td1.parity-report
                 |                           |
                 +-------------+-------------+
                               |
                               v
                   td1.parity-campaign-run
                               |
                               v
                     td1.parity-bench-run
```

> Hardware earns authority through parity.

## Transport neutrality

Parity semantics do not specify USB, UART, CAN, Ethernet, GPIO, SWD, SPI, or another physical link.

The existing `ParityTransport` surface remains:

- advertise `ParityCapabilities`;
- exchange a `ParityRequest` for a `ParityResponse`.

Everything below that surface is adapter machinery.

`td1.parity-wire` defines canonical bytes. `StreamParityLineIO` moves/buffers those bytes. `PySerialByteStream` optionally opens a real serial-class host link. None of them redefine ternary arithmetic or conformance.

## Versioned contracts

Current semantic/evidence schemas include:

- `td1.parity-capabilities`;
- `td1.parity-request`;
- `td1.parity-response`;
- `td1.parity-report`;
- `td1.parity-campaign`;
- `td1.parity-campaign-run`;
- `td1.parity-wire`;
- `td1.parity-wire-transcript`;
- `td1.parity-bench-run`.

`StreamParityLineIO`, `SerialConfig`, and `PySerialByteStream` are adapter/runtime implementations rather than new arithmetic schemas.

## Capability negotiation

A target advertises:

- stable target identifier;
- supported parity protocol versions;
- supported operations;
- maximum ternary slice width;
- optional telemetry keys.

Unsupported vectors are rejected before device exchange and recorded as `unsupported` rather than being called hardware faults.

Current parity operations:

- `trit_hold`;
- `register_load`;
- `negate`;
- `add`;
- `sub`.

A target must advertise only capability it has actually demonstrated.

## Fixed golden vectors

### First physical campaign: one trit

The first real target remains deliberately small:

```text
-
0
+
```

Each one-trit state must be driven, held, observed, and returned through the adapter without spontaneous semantic change.

This is the bridge from `TRIT_CELL_REV0` bench measurements into software conformance.

### Later register and ALU campaigns

Register-slice vectors exercise zero, +/-1, representable extrema, and alternating ternary patterns at the requested width.

ALU vectors cover negation, addition/subtraction, and fixed-width wrap behavior.

Those vectors define reference expectations. They do not imply that corresponding hardware exists.

## Trace-derived workload campaigns

`td1.parity-campaign` adds workload-derived values to the fixed edge cases.

Current mappings are deliberately narrow:

- `LDI`, `MOV`, `LD` -> `register_load`;
- `NEG` -> `negate`;
- `ADD` -> `add`;
- `SUB` -> `sub`;
- `ADDI` -> subsystem `add` using a fixed-width immediate operand.

These mappings test represented subsystems only. They do not claim physical instruction decode, physical memory-read semantics, or full-machine execution.

A campaign embeds its complete source trace and exact initial/final machine checkpoints. Saved mappings are re-derived when loaded.

## Canonical parity wire

Wire v1 uses canonical UTF-8 JSON Lines with exactly one LF terminator.

Allowed message kinds:

- `capabilities_request`;
- `capabilities_response`;
- `parity_request`;
- `parity_response`.

The envelope wraps the existing parity payloads instead of duplicating them.

The default maximum frame size is 65,536 bytes including LF. Empty, malformed, oversized, CRLF, multi-line, invalid-UTF-8, and noncanonical frames are rejected.

`JsonLineParityTransport` adapts `ParityLineIO` to `ParityTransport`. `ParityWireDevice` is the reference dispatcher used by software integration tests.

## Stream-backed host I/O

`StreamParityLineIO` implements the line boundary over generic binary reader/writer objects.

It handles:

- partial writes;
- optional flush;
- fragmented reads;
- coalesced later frames;
- bounded buffering;
- explicit empty EOF / partial EOF / oversized frame / read / write failures;
- deterministic bytes/frames/buffered-byte statistics.

Canonical wire validation remains above this layer.

Adapter-specific `ParityStreamError` subclasses are allowed to propagate unchanged so lower transports retain useful diagnostics.

## Optional live serial adapter

v0.18 adds an optional pyserial-backed deployment path:

```text
JsonLineParityTransport
 -> RecordingParityLineIO
 -> StreamParityLineIO
 -> PySerialByteStream
 -> pyserial
 -> UART / USB CDC target
```

Core installs remain free of pyserial. Live hosts install the optional `serial` extra.

`SerialConfig` requires explicit:

- port;
- baud rate;
- positive finite read timeout;
- positive finite write timeout.

TD-1 does not auto-discover ports and does not define a default baud rate.

`PySerialByteStream` distinguishes:

- read timeout;
- write timeout;
- underlying serial read failure;
- underlying serial write/flush failure;
- use after close;
- close failure;
- missing optional dependency.

A zero-byte pyserial read with the required finite timeout is a host serial timeout, not EOF and not a target-generated `ParityStatus.TIMEOUT`.

`td1-parity serial-run` executes an existing saved campaign through this exact stack and may emit the same campaign-run, transcript, and bench-run artifacts used by in-memory testing.

Port name, baud rate, host timeout values, and stream counters may appear in CLI diagnostics. They are not silently inserted into canonical parity artifacts.

See [`SERIAL_ADAPTER.md`](SERIAL_ADAPTER.md) and ADR 0018.

## Wire transcripts

`td1.parity-wire-transcript` records exact canonical traffic at `ParityLineIO`.

Each record preserves:

- direction;
- contiguous ordinal;
- exact frame bytes represented as canonical frame text;
- frame SHA-256;
- message kind;
- correlation ID;
- envelope digest.

`RecordingParityLineIO` composes unchanged above in-memory, generic stream, or serial-backed adapters.

`ReplayParityLineIO` requires exact host bytes and returns exact saved device bytes. Replay must consume the entire transcript.

## Bench-run bundles

`td1.parity-bench-run` binds one exact campaign run to the exact transcript implied by its report.

Validation prevents substitution of a transcript from a different target, session, vector ordering, response set, or telemetry set.

`replay_bench_run()` reruns the campaign through the ordinary wire transport over replayed bytes and requires the canonical campaign run to match the saved run.

This is transport evidence, not authenticated device identity.

## Bench telemetry

Current optional telemetry vocabulary:

```text
voltage_uv
settle_us
comparator_code
sample_count
board_revision
temperature_millic
```

Scaled numeric values use integers. These values are metadata under the current contract and do not alter arithmetic pass/fail evaluation.

A future electrical-acceptance contract must be based on actual measured distributions and versioned explicitly.

## Reports versus adapter failures

A `td1.parity-report` records target capability, request/response records, deterministic pass/fail evaluation, and discrepancies.

Host adapter errors are different. For example, a pyserial read timeout before a valid response is received means the live session failed at the host transport layer; it is not evidence that the target returned `ParityStatus.TIMEOUT`.

This distinction prevents host plumbing from fabricating device claims.

## CLI workflows

Reference/software workflows:

```bash
td1-sim parity-vectors --width 12

td1-sim parity-loopback --width 12

td1-parity build examples/sum.td1 --output sum.campaign.json

td1-parity wire-loopback sum.campaign.json \
  --output sum.wire.run.json \
  --transcript-output sum.wire.transcript.json \
  --bench-output sum.bench.json

td1-parity bench-run-replay sum.bench.json
```

Optional live serial workflow:

```bash
python -m pip install -e '.[serial]'

td1-parity serial-run sum.campaign.json \
  --port /dev/ttyACM0 \
  --baud 230400 \
  --read-timeout 2.0 \
  --write-timeout 2.0 \
  --output sum.serial.run.json \
  --transcript-output sum.serial.transcript.json \
  --bench-output sum.serial.bench.json
```

All serial deployment values above are examples supplied by the operator, not TD-1 defaults.

## First real adapter sequence

The next physical campaign should remain small and evidence-driven:

1. build and independently measure one `TRIT_CELL_REV0` cell;
2. choose the actual UART/USB-CDC interface presented by the bench controller;
3. install the optional serial dependency on the host;
4. select explicit port/baud/read-timeout/write-timeout values appropriate to that controller;
5. implement the existing `td1.parity-wire` envelope on the device side;
6. advertise only `trit_hold`, `max_width=1`;
7. run the three one-trit golden vectors through `serial-run`;
8. return real voltage/settling/comparator/sample/board telemetry where available;
9. save the conformance report, exact transcript, and linked bench-run bundle;
10. replay that bundle offline;
11. inspect measured electrical distributions before defining acceptance thresholds;
12. expand advertised capability only after evidence supports the next subsystem;
13. repeat for a multi-trit register slice;
14. proceed to physical ALU conformance only after register-slice success.

The software stack is now capable of reaching the port. The missing authority is the copper and its measurements.

## Deferred work

This revision does not define:

- serial port auto-discovery;
- a TD-1 default baud rate;
- USB VID/PID;
- connector/pinout;
- retry/reconnect policy;
- analog thresholds;
- sample cadence;
- hysteresis/calibration policy;
- electrical acceptance limits;
- authenticated hardware identity;
- cycle-accurate full-machine replacement;
- physical instruction fetch/decode;
- physical 12-trit instruction encoding.

Those decisions remain downstream of first-hardware evidence.
