# First-Hardware Golden-Vector Bench Flow

## Purpose

The first physical TD-1 target is not a workload processor. It is a one-trit experimental subsystem that should advertise only the behavior it has actually demonstrated.

For that reason, v0.19 separates **fixed first-hardware golden vectors** from trace-derived `td1.parity-campaign` workloads.

The first target is expected to advertise:

```text
operations = [trit_hold]
max_width  = 1
```

and to run exactly three deterministic one-trit stimuli:

```text
TRIT-NEG   -
TRIT-ZERO  0
TRIT-POS   +
```

No register-load, ALU, instruction-decode, or workload provenance claim is implied by this suite.

## Why this is separate from parity campaigns

`td1.parity-campaign` is intentionally trace-derived. It packages subsystem operations encountered while executing a logical TD-1 program.

That is valuable once physical register slices and ALU functions exist, but it is the wrong abstraction for the first trit cell. The first hardware milestone needs a tiny fixed conformance surface that can be exercised before a useful logical workload can map onto the board.

The two paths therefore coexist:

```text
logical workload
    -> execution trace
      -> td1.parity-campaign
        -> campaign run / bench run

first physical cell
    -> fixed golden trit vectors
      -> td1.parity-report
        -> exact wire transcript
          -> td1.parity-wire-evidence
```

They share the same `ParityTransport`, canonical wire protocol, recording layer, stream adapter, serial adapter, response evaluation, and replay machinery.

## Canonical trit suite

`golden_trit_vectors()` is the single source for the three width-1 `trit_hold` vectors.

`golden_register_vectors(width)` remains backward compatible and begins with that exact trit prefix before its register-load vectors. This prevents the first-hardware suite and the legacy register suite from drifting into two definitions of the same stimuli.

## Generic wire evidence

v0.19 introduces:

```text
schema  = td1.parity-wire-evidence
version = 1
```

A `ParityWireEvidence` artifact binds:

- one exact `td1.parity-report`;
- one exact `td1.parity-wire-transcript`.

Validation reconstructs the canonical wire conversation implied by the report and requires byte-for-byte canonical equality with the saved transcript.

That reconstruction covers:

1. capability request;
2. capability response with the exact saved capabilities;
3. one parity request/response exchange for every vector the target capabilities accepted.

Host-side capability rejections produce report records but no fabricated device exchange, exactly as in normal parity execution.

Because report payloads include target capabilities, session ID, ordered vectors, responses, and telemetry, substituting any of those changes the expected wire traffic and invalidates the evidence bundle.

## Replay

Generic evidence replays through the ordinary stack:

```text
saved td1.parity-wire-evidence
          |
          v
  ReplayParityLineIO
          |
          v
 JsonLineParityTransport
          |
          v
   run_conformance()
```

Replay uses the exact saved request vectors and session ID and requires the regenerated canonical `td1.parity-report` to equal the saved report.

The generic evidence linkage is also the same report/transcript validation rule used by campaign-specific `td1.parity-bench-run`; the v1 bench-run schema remains unchanged.

## Live serial command

The first real-cell path is:

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

Windows uses the same command with an explicit COM port, for example `--port COM7`.

TD-1 deliberately does not choose a default port, baud rate, timeout, connector, USB identity, or physical pinout. Those remain deployment and bench configuration.

The `trit` suite always sends exactly the three one-trit hold vectors regardless of the `--width` argument. The `register` suite accepts an explicit width and retains the existing register golden-vector ordering.

## Session shape

For a target advertising only `trit_hold`, width 1, the successful trit session contains exactly:

```text
1 capabilities request/response exchange
3 parity request/response exchanges
```

That means eight canonical line records in the transcript.

No unsupported register/ALU requests are sent in the trit suite because those vectors are not part of the suite at all.

## Artifact boundary

`serial-golden` may emit:

- `td1.parity-report`;
- `td1.parity-wire-transcript`;
- `td1.parity-wire-evidence`.

Serial deployment settings and deterministic stream counters may appear in the human CLI summary but remain outside all three normative artifacts.

A successful fake-serial or software-target run proves the host stack and artifact logic only.

A successful real-device run proves only that the configured device exchanged responses that satisfy the tested parity contract. Electrical quality, voltage margin, settling, comparator behavior, calibration, and environmental stability require measured telemetry and bench records.

## What this does not freeze

v0.19 does not define:

- electrical acceptance thresholds;
- comparator hysteresis requirements;
- analog trit voltage distributions;
- UART baud rate as a machine property;
- USB VID/PID;
- connector or pinout;
- retry/reconnect policy;
- register implementation;
- ALU implementation;
- instruction fetch/decode;
- physical instruction encoding.

Issue #2 remains deferred until physical constraints justify freezing a program image.

## Design rule

**Prove the smallest physical claim with the smallest honest vector set.**
