# Emulator-to-Hardware Parity

## Purpose

TD-1 hardware is not allowed to become authoritative because it is physical. A physical ternary subsystem replaces an emulated subsystem only after it reproduces the reference model for the same deterministic stimuli.

The parity layer defines that conformance boundary independently from the concrete electrical link used by a bench adapter.

```text
reference model
    |
    +------> fixed golden vectors
    |              |
    |              v
    |        td1.parity-report
    |              |
    |              +----> exact transcript
    |                         |
    |                         v
    |              td1.parity-wire-evidence
    |
    +------> execution trace -> td1.parity-campaign
                               |
                               v
                      td1.parity-campaign-run
                               |
                               +----> exact transcript
                                          |
                                          v
                                td1.parity-bench-run
```

Both paths pass through the same `ParityTransport`, canonical parity wire, recording layer, stream adapter, and optional serial adapter.

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
- `td1.parity-wire-evidence`;
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
TRIT-NEG   -
TRIT-ZERO  0
TRIT-POS   +
```

`golden_trit_vectors()` is the canonical source for those three width-1 `trit_hold` vectors.

`golden_register_vectors(width)` remains backward compatible but derives its leading trit prefix from the same canonical function before adding register-load vectors.

The first trit suite is intentionally **not** represented as a trace-derived `td1.parity-campaign`. It is a fixed bench conformance experiment, not a claim about operations encountered in a logical workload.

For a target advertising only `trit_hold`, `max_width=1`, a successful session produces exactly:

```text
1 capability request/response exchange
3 parity request/response exchanges
```

No register or ALU vectors are sent in the `trit` suite.

### Later register and ALU campaigns

Register-slice vectors exercise zero, +/-1, representable extrema, and alternating ternary patterns at the requested width.

ALU vectors cover negation, addition/subtraction, and fixed-width wrap behavior.

Those vectors define reference expectations. They do not imply that corresponding hardware exists.

## Trace-derived workload campaigns

`td1.parity-campaign` adds workload-derived values to fixed edge-case testing once a physical subsystem is mature enough for logical-workload provenance to be meaningful.

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

The optional pyserial-backed deployment path is:

```text
JsonLineParityTransport
 -> RecordingParityLineIO
 -> StreamParityLineIO
 -> PySerialByteStream
 -> pyserial
 -> UART / USB CDC target
```

Core installs remain free of pyserial. Live hosts install the optional `serial` extra.

`SerialConfig` requires explicit port, baud rate, positive finite read timeout, and positive finite write timeout.

TD-1 does not auto-discover ports and does not define a default baud rate.

A zero-byte pyserial read with the required finite timeout is a host serial timeout, not EOF and not a target-generated `ParityStatus.TIMEOUT`.

Two live CLI paths exist:

- `td1-parity serial-golden` for fixed bring-up suites;
- `td1-parity serial-run` for saved trace-derived campaigns.

Port name, baud rate, host timeout values, and stream counters may appear in CLI diagnostics. They are not silently inserted into canonical parity artifacts.

See [`SERIAL_ADAPTER.md`](SERIAL_ADAPTER.md), ADR 0018, and ADR 0019.

## Wire transcripts and generic evidence

`td1.parity-wire-transcript` records exact canonical traffic at `ParityLineIO`.

`transcript_for_report()` reconstructs the exact wire traffic implied by any saved `td1.parity-report`.

`validate_report_transcript()` is the shared report/transcript linkage rule. It is used by both:

- generic `td1.parity-wire-evidence`;
- campaign-specific `td1.parity-bench-run`.

This shared validation prevents target/session/vector/response/telemetry substitution while keeping `td1.parity-bench-run` v1 unchanged.

`ReplayParityLineIO` requires exact host bytes and returns exact saved device bytes. Replay must consume the entire transcript.

## Generic wire evidence

`td1.parity-wire-evidence` binds any exact `td1.parity-report` to the exact `td1.parity-wire-transcript` implied by that report.

This is the correct evidence artifact for fixed first-hardware golden suites because no trace-derived campaign exists.

`replay_wire_evidence()` reruns the exact saved request vectors and session through the normal wire transport over transcript replay and requires canonical report equivalence.

## Campaign bench bundles

`td1.parity-bench-run` continues to bind one exact `td1.parity-campaign-run` to the exact transcript implied by its report.

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

Fixed first-hardware workflow:

```bash
python -m pip install -e '.[serial]'

td1-parity serial-golden \
  --suite trit \
  --port /dev/ttyACM0 \
  --baud 230400 \
  --read-timeout 2.0 \
  --write-timeout 2.0 \
  --report-output trit.report.json \
  --transcript-output trit.transcript.json \
  --evidence-output trit.evidence.json

td1-parity wire-evidence-verify trit.evidence.json

td1-parity wire-evidence-replay trit.evidence.json
```

Trace-derived campaign workflow:

```bash
td1-parity build examples/sum.td1 --output sum.campaign.json

td1-parity serial-run sum.campaign.json \
  --port /dev/ttyACM0 \
  --baud 230400 \
  --read-timeout 2.0 \
  --write-timeout 2.0 \
  --output sum.serial.run.json \
  --transcript-output sum.serial.transcript.json \
  --bench-output sum.serial.bench.json

td1-parity bench-run-replay sum.serial.bench.json
```

All serial deployment values above are operator-supplied examples, not TD-1 defaults.

## First real adapter sequence

The next physical campaign should remain small and evidence-driven:

1. build and independently measure one `TRIT_CELL_REV0` cell;
2. choose the actual UART/USB-CDC interface presented by the bench controller;
3. install the optional serial dependency on the host;
4. select explicit port/baud/read-timeout/write-timeout values appropriate to that controller;
5. implement the existing `td1.parity-wire` envelope on the device side;
6. advertise only `trit_hold`, `max_width=1`;
7. run exactly the three one-trit vectors with `td1-parity serial-golden --suite trit`;
8. return real voltage/settling/comparator/sample/board telemetry where available;
9. save the conformance report, exact transcript, and generic wire-evidence bundle;
10. replay that evidence bundle offline;
11. inspect measured electrical distributions before defining acceptance thresholds;
12. expand advertised capability only after evidence supports the next subsystem;
13. repeat for a multi-trit register slice;
14. use trace-derived campaigns only once their workload provenance is meaningful;
15. proceed to physical ALU conformance only after register-slice success.

The software stack can now reach the port and express the honest first-cell test. The missing authority is the copper and its measurements.

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
