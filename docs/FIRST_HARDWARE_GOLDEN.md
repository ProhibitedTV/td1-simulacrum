# First-Hardware Golden-Vector Bench Flow

## Purpose

The first physical TD-1 target is not a workload processor. It is a one-trit experimental subsystem that should advertise only the behavior it has actually demonstrated.

For that reason, fixed first-hardware golden vectors are separate from trace-derived `td1.parity-campaign` workloads.

There are now **two independent first-cell questions**:

1. is the physical cell electrically characterized well enough to make a bounded hardware claim?
2. does that characterized cell reproduce the Simulacrum's logical `-1 / 0 / +1` semantics for the tested stimuli?

The first question is answered by `td1.trit-cell-characterization`; the second is answered by the parity suite. Do not skip the first question because the second one passes.

See [`HARDWARE_GROUND_TRUTH.md`](HARDWARE_GROUND_TRUTH.md).

After characterization, the first target is expected to advertise:

```text
operations = [trit_hold]
max_width  = 1
```

and to run exactly three deterministic one-trit logical stimuli:

```text
TRIT-NEG   -
TRIT-ZERO  0
TRIT-POS   +
```

Those symbols do not prescribe physical voltages, rail topology, or comparator thresholds. No register-load, ALU, instruction-decode, or workload provenance claim is implied by this suite.

## Why this is separate from parity campaigns

`td1.parity-campaign` is intentionally trace-derived. It packages subsystem operations encountered while executing a logical TD-1 program.

That is valuable once physical register slices and ALU functions exist, but it is the wrong abstraction for the first trit cell. The first hardware milestone needs a tiny fixed conformance surface that can be exercised before a useful logical workload can map onto the board.

The physical-evidence path is therefore:

```text
reviewed schematic + datasheets
    -> measured one-trit cell
      -> td1.trit-cell-characterization
        -> fixed golden trit vectors
          -> td1.parity-report
            -> exact wire transcript
              -> td1.parity-wire-evidence
```

Later workload parity remains:

```text
logical workload
    -> execution trace
      -> td1.parity-campaign
        -> campaign run / bench run
```

The parity paths share the same `ParityTransport`, canonical wire protocol, recording layer, stream adapter, serial adapter, response evaluation, and replay machinery.

## Canonical trit suite

`golden_trit_vectors()` is the single source for the three width-1 `trit_hold` vectors.

`golden_register_vectors(width)` remains backward compatible and begins with that exact trit prefix before its register-load vectors. This prevents the first-hardware suite and the register suite from drifting into two definitions of the same logical stimuli.

## Characterization gate

Before `trit_hold` is advertised on real hardware:

1. use the corrected/reviewed schematic rather than the earlier speculative numeric recipe;
2. verify component supply, common-mode, output-swing/current, pull-up/open-drain, load, and timing constraints against datasheets;
3. measure all supply/reference nodes;
4. measure repeated `-1`, `0`, and `+1` outputs with a high-impedance instrument;
5. repeat under explicit representative loads;
6. characterize comparator switching in both directions if comparators are part of the implementation;
7. measure settling and record temperature/context where practical;
8. save the evidence as canonical `td1.trit-cell-characterization`.

Validate a captured artifact with:

```bash
td1-characterize verify cell.characterization.json
```

Inspect descriptive observed voltage ranges without inferring acceptance criteria:

```bash
td1-characterize summary cell.characterization.json
```

A future electrical-acceptance profile must be based on sufficient measurements and reviewed limits. The characterization command intentionally does not invent one.

## Generic wire evidence

`td1.parity-wire-evidence` binds:

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

After the characterization gate, the real-cell parity path is:

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

TD-1 deliberately does not choose a default port, baud rate, timeout, connector, USB identity, physical pinout, rail topology, or trit voltage. Those remain deployment/bench or reviewed hardware-design choices.

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

The first real cell should preserve four classes of evidence:

- `td1.trit-cell-characterization` — measured electrical evidence;
- `td1.parity-report` — logical conformance result;
- `td1.parity-wire-transcript` — exact transport conversation;
- `td1.parity-wire-evidence` — deterministic report/transcript linkage.

Serial deployment settings and deterministic stream counters may appear in the human CLI summary but remain outside the normative parity artifacts.

A successful fake-serial or software-target run proves the host stack and artifact logic only.

A successful real-device parity run proves only that the configured device exchanged responses that satisfy the tested parity contract. It does not independently prove noise margin, fan-out, hysteresis, settling, calibration, or environmental stability; those claims require characterization and eventually versioned acceptance criteria.

## What this does not freeze

This flow does not define:

- rail topology;
- physical `-1`, `0`, or `+1` voltage levels;
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

Issue #2 remains deferred until corrected design inputs and physical constraints justify freezing a program image.

## Design rule

**Characterize the cell. Then prove the smallest logical claim with the smallest honest vector set.**
