# Emulator-to-Hardware Parity

## Purpose

TD-1 hardware is not allowed to become authoritative because it is physical. A physical ternary subsystem replaces an emulated subsystem only after it reproduces the reference model for the same deterministic stimuli.

The v1 parity layer defines that conformance boundary without choosing a physical transport.

```text
reference model
    |
    v
golden parity vector
    |
    v
td1.parity-request
    |
    v
transport adapter
    |
    v
physical target
    |
    v
td1.parity-response
    |
    v
replayable conformance report
```

> Hardware earns authority through parity.

## Transport neutrality

The parity contract does not specify USB, UART, CAN, Ethernet, GPIO, SWD, SPI, or any other wire protocol.

A future adapter implements only two host-side operations:

- advertise `ParityCapabilities`;
- exchange a `ParityRequest` for a `ParityResponse`.

That keeps logical conformance independent from the physical link. Serial framing and voltage sampling belong to adapters and telemetry, not to TD-1 arithmetic semantics.

## Versioned schemas

The v1 layer defines:

- `td1.parity-capabilities`;
- `td1.parity-request`;
- `td1.parity-response`;
- `td1.parity-report`.

Every artifact uses deterministic canonical JSON where applicable and can be fingerprinted with SHA-256.

## Capability negotiation

A target advertises:

- stable target identifier;
- supported parity protocol versions;
- supported operations;
- maximum ternary slice width;
- optional telemetry keys.

The harness rejects unsupported vectors before exchange and records them as `unsupported` rather than pretending the target failed a test it never claimed to implement.

Current operation classes are:

- `trit_hold`;
- `register_load`;
- `negate`;
- `add`;
- `sub`.

## Golden vectors

### First physical campaign: trit/register slice

`golden_register_vectors()` begins with the smallest meaningful physical test:

```text
-
0
+
```

Each one-trit state must be driven, held, observed, and returned through the adapter without spontaneous semantic change.

The same vector set then tests register-slice loads at the requested width using:

- zero;
- +1;
- -1;
- maximum positive value;
- maximum negative value;
- an alternating ternary pattern.

This is the intended bridge from `TRIT_CELL_REV0` bench work into software conformance.

### Later ALU campaign

`golden_alu_vectors()` includes:

- negation;
- basic addition/subtraction;
- positive-to-negative fixed-width wrap;
- negative-to-positive fixed-width wrap.

The ALU vectors exist now so the test oracle is stable before physical ALU design begins. They do not imply that an ALU board already exists.

## Observable state digests

A physical slice result is fingerprinted as:

```text
SHA256({width, ternary_value})
```

This is a deterministic **slice-state digest**, not a security claim.

The response carries both the observed ternary value and its observed-state digest. The harness recomputes the digest and rejects a response whose value and digest disagree.

That gives three distinct failure classes:

1. transport/device status failure;
2. observed ternary value mismatch;
3. observed-state digest mismatch.

## Fault reporting

Responses may report:

- `ok`;
- `unsupported`;
- `fault`;
- `timeout`;
- `error`.

A fault status is preserved in the final report along with the vector identity and optional detail. Later hardware adapters can attach integer/string telemetry such as:

```text
voltage_uv
settle_us
comparator_code
board_revision
```

Scaled integer telemetry is preferable to ambiguous floating-point strings for bench measurements.

## Replayable conformance reports

A `td1.parity-report` stores:

- capability advertisement and digest;
- deterministic vector-set digest;
- every request;
- every response;
- deterministic pass/fail evaluation;
- exact discrepancy text;
- summary counts.

Loading a saved report revalidates the request/response identities, vector semantics, digests, pass flags, discrepancy text, capability digest, vector-set digest, and summary.

A report therefore serves as a bench receipt rather than a screenshot saying “it worked.”

## Reference loopback target

`ReferenceLoopbackTransport` implements the same contract entirely in software. It exists to prove the harness before a physical adapter is written.

It supports:

- deterministic success;
- forced `fault` / `timeout` / `error` states;
- deliberate observed-value corruption;
- restricted maximum width for capability-negotiation tests.

Passing loopback proves the parity infrastructure, not physical ternary hardware.

## CLI

Emit the complete current golden set:

```bash
td1-sim parity-vectors --width 12
```

Emit only the first trit/register campaign:

```bash
td1-sim parity-vectors --width 3 --register-only
```

Run the vectors through the reference loopback target:

```bash
td1-sim parity-loopback --width 12
```

Exercise capability rejection deliberately:

```bash
td1-sim parity-loopback --width 12 --target-max-width 3
```

Validate a saved report:

```bash
td1-sim parity-verify report.json
```

## Physical adapter sequence

The first real hardware integration should remain small:

1. build and measure one physical trit cell;
2. write a tiny adapter that can command/read `-`, `0`, `+`;
3. advertise only `trit_hold`, `max_width=1`;
4. run the three `TRIT-*` golden vectors;
5. preserve raw voltage/settling telemetry in the report;
6. expand capability only after the one-trit report passes;
7. repeat for a multi-trit register slice;
8. only then begin ALU conformance.

A board should not advertise capabilities merely because its schematic intends to support them.

## Deferred work

This revision does not define:

- physical connector pinout;
- serial packet framing;
- analog threshold values;
- sample timing;
- hysteresis policy;
- calibration procedure;
- full-machine state replacement;
- cycle-accurate execution;
- physical 12-trit instruction encoding.

Those decisions belong to later hardware/adaptor revisions and can consume this transport-neutral contract.
