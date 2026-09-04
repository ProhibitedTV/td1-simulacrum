# Emulator-to-Hardware Parity

## Purpose

TD-1 hardware is not allowed to become authoritative because it is physical. A physical ternary subsystem replaces an emulated subsystem only after it reproduces the reference model for the same deterministic stimuli.

The parity layer defines that conformance boundary without choosing a physical transport.

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
                        transport adapter
                               |
                               v
                        physical target
                               |
                               v
                        td1.parity-response
                               |
                               v
                        td1.parity-report
```

> Hardware earns authority through parity.

## Transport neutrality

The parity contract does not specify USB, UART, CAN, Ethernet, GPIO, SWD, SPI, or another wire protocol.

A future adapter implements two host-side operations:

- advertise `ParityCapabilities`;
- exchange a `ParityRequest` for a `ParityResponse`.

Serial framing, analog sampling, and board-specific details belong to adapters/telemetry, not TD-1 arithmetic semantics.

## Versioned schemas

The base layer defines:

- `td1.parity-capabilities`;
- `td1.parity-request`;
- `td1.parity-response`;
- `td1.parity-report`.

The workload-derived layer adds:

- `td1.parity-campaign`;
- `td1.parity-campaign-run`.

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

## Fault reporting and telemetry

Responses may report:

- `ok`;
- `unsupported`;
- `fault`;
- `timeout`;
- `error`.

Later adapters may attach integer/string telemetry such as:

```text
voltage_uv
settle_us
comparator_code
board_revision
```

Scaled integer telemetry is preferable to ambiguous floating-point strings for bench measurements.

## Replayable conformance reports

A `td1.parity-report` stores capability advertisement/digest, vector-set digest, every request/response, deterministic pass/fail evaluation, exact discrepancy text, and summary counts.

Loading a report revalidates identities, vector semantics, digests, pass flags, discrepancies, capability digest, vector-set digest, and summary.

A report is a bench receipt rather than a screenshot saying “it worked.”

## Reference loopback target

`ReferenceLoopbackTransport` implements the contract entirely in software. It can return deterministic success, forced fault/timeout/error states, deliberate observed-value corruption, and restricted maximum width.

Passing loopback proves the host parity infrastructure, not physical ternary hardware.

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

td1-parity run-verify sum.run.json
```

Capability rejection can be exercised deliberately with `--target-max-width`.

## Physical adapter sequence

The first real integration remains intentionally small:

1. build and measure one physical trit cell;
2. write a tiny adapter that commands/reads `-`, `0`, `+`;
3. advertise only `trit_hold`, `max_width=1`;
4. run the three `TRIT-*` fixed golden vectors;
5. preserve voltage/settling/comparator telemetry;
6. expand capability only after the one-trit report passes;
7. repeat for a multi-trit register slice;
8. run workload-derived register campaigns where capabilities allow;
9. only then begin physical ALU conformance and ALU workload campaigns.

A board must not advertise capabilities merely because its schematic intends to support them.

## Deferred work

This revision does not define:

- physical connector pinout;
- serial packet framing;
- analog threshold values;
- sample timing;
- hysteresis/calibration policy;
- full-machine state replacement;
- cycle-accurate execution;
- physical instruction fetch/decode;
- physical 12-trit instruction encoding.

Those decisions belong to later hardware/adaptor revisions and can consume the transport-neutral parity and campaign contracts without redefining them.
