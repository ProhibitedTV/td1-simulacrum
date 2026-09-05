# ADR 0019: First hardware uses fixed golden vectors before workload campaigns

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 already has trace-derived `td1.parity-campaign` artifacts. Those campaigns are excellent for asking whether a physical subsystem reproduces operations encountered in a real logical workload.

The first planned physical target is much smaller: one ternary state cell implementing only `trit_hold` at width 1. Forcing that target into a trace-derived workload campaign would either send irrelevant unsupported vectors or require inventing workload provenance for a fixed electrical bench test.

The serial host path introduced in v0.18 made this mismatch concrete. The host could reach a real port, but the first bench milestone still needed an artifact and CLI path whose semantics matched the actual claim being tested.

## Decision

TD-1 will maintain two distinct parity entry points that share the same transport and evidence layers:

1. **Fixed golden-vector suites** for first-hardware and focused subsystem bring-up.
2. **Trace-derived parity campaigns** for workload-linked subsystem validation.

The canonical first-hardware trit suite contains exactly three width-1 `trit_hold` vectors for `-`, `0`, and `+`.

`golden_register_vectors(width)` remains backward compatible and derives its leading trit vectors from the same canonical trit suite.

A generic `td1.parity-wire-evidence` artifact binds any `td1.parity-report` to the exact `td1.parity-wire-transcript` implied by that report. Campaign-specific `td1.parity-bench-run` keeps its v1 schema and reuses the same report/transcript validation rule.

`td1-parity serial-golden` runs fixed suites through the existing optional serial stack. Port, baud, and host timeout values remain deployment settings and do not enter normative report, transcript, or evidence artifacts.

## Consequences

### Positive

- The first physical board advertises and tests only demonstrated capability.
- A one-trit session is exactly auditable: one capability exchange plus three parity exchanges.
- Fixed bench tests no longer need fake logical-workload provenance.
- Workload campaigns retain their stronger trace-derived provenance where it is meaningful.
- Generic evidence can preserve and replay fixed-vector sessions without adding campaign fields that do not apply.
- Existing parity wire, transcript, stream, and serial layers remain unchanged in authority.
- Existing `td1.parity-bench-run` v1 artifacts remain compatible.

### Negative

- The parity CLI now has two intentionally different live execution workflows (`serial-golden` and `serial-run`).
- Documentation must explain which workflow is appropriate for a given hardware maturity level.
- Generic report/transcript evidence is another versioned artifact to maintain.

## Rejected alternatives

### Manufacture a trace-derived campaign containing only trit holds

Rejected because the provenance would be artificial. The first-cell test is a fixed conformance experiment, not a claim about operations encountered in a logical TD-1 workload.

### Run the full register golden suite against the one-trit target

Rejected because it creates predictable capability rejections and obscures the actual first milestone. Unsupported vectors are valid protocol behavior, but they should not be included merely to make a suite look larger.

### Add a special first-hardware wire protocol

Rejected because framing, correlation, recording, replay, and serial transport are already suitable. The difference is the vector source and evidence root, not the byte protocol.

### Freeze electrical thresholds in the software artifact

Rejected until measured distributions exist. Fixed golden vectors define logical stimuli and expected ternary state only; analog acceptance remains a later measured contract.

## Authority statement

A passing software or fake-serial golden session proves only the host path and deterministic artifact logic.

A passing real-device golden session proves only the exact parity operations represented by the report. It does not by itself prove voltage margin, timing quality, calibration quality, authenticated hardware identity, instruction execution, or the deferred physical instruction encoding in Issue #2.
