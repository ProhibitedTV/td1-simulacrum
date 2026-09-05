# ADR 0023 — Separate logical ternary semantics from measured electrical representation

Status: Accepted

## Context

The Simulacrum has deterministic logical balanced-ternary semantics, while the physical TD-1 implementation is still pre-copper.

An earlier system-spec draft contained concrete first-cell electrical values and component/topology assumptions. An experienced external builder subsequently reported that at least some of those numbers were wrong. The corrected design values have not yet been supplied to this repository.

A repository audit also found a related latent assumption in code: `BenchTelemetry.voltage_uv` rejected negative values, which implicitly privileged a nonnegative/single-supply physical representation even though the logical machine does not require one.

The project needs to proceed without either defending stale numbers or replacing them with equally speculative new numbers.

## Decision

TD-1 separates three layers of authority:

1. **Logical semantics** — balanced-ternary `-1 / 0 / +1`, current logical machine profile, arithmetic, ISA, and deterministic parity expectations.
2. **Measured electrical representation** — board-specific rails, references, state voltages, loads, switching points, settling, and temperature captured as evidence.
3. **Electrical acceptance** — future versioned limits justified by reviewed topology, datasheet constraints, and sufficient measured distributions.

The repository will not define default physical trit voltages, thresholds, rail topology, hysteresis, or similar first-cell constants until that evidence exists.

`td1.trit-cell-characterization` v1 is introduced as the canonical measured-evidence artifact. It uses signed integer microvolts and explicit load/instrument identity and may record rising/falling comparator switching observations. Its summaries are descriptive only and cannot synthesize acceptance thresholds.

`BenchTelemetry.voltage_uv` is signed relative to the bench/device reference.

Real hardware must complete characterization before it advertises `trit_hold` and runs the fixed three-state parity suite.

The current 12-trit / 9-register / 729-word configuration remains the logical Simulacrum profile. It is not promoted to an electrical constraint. If physical evidence challenges those architectural dimensions, the change requires an explicit versioned architecture decision.

Issue #2 physical program-image/encoding work remains blocked on corrected design inputs and real hardware constraints.

## Consequences

Positive:
- wrong early electrical numbers cannot silently become protocol or test authority;
- single-supply and bipolar implementations are both representable;
- bench claims become traceable to actual measurements;
- logical parity and analog quality remain separate questions;
- future acceptance limits can cite the evidence that justified them.

Costs:
- first-copper work now requires disciplined characterization before parity claims;
- there is intentionally no turnkey nominal voltage/threshold recipe in the repository;
- corrected external-builder information must be reviewed and translated into a schematic rather than copied as folklore;
- electrical acceptance is deferred until enough evidence exists.

## Rejected alternatives

### Keep the earlier spec values until something better arrives

Rejected. Known doubt is sufficient to remove them from authority. A stale precise number is more dangerous than an explicit unknown.

### Guess replacement values from balanced-ternary symmetry

Rejected. Mathematical symmetry does not choose rail topology, device headroom, loading, hysteresis, common-mode behavior, or noise margin.

### Make parity responses define electrical validity

Rejected. Returning the expected logical state does not establish the analog operating envelope.

### Infer thresholds automatically from one characterization run

Rejected. One unit and three nominal states do not establish production-safe or even bench-robust limits.

## Rule

**Logical state is normative. Electrical representation is measured. Acceptance is earned from evidence.**
