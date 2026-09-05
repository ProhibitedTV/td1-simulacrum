# TD-1 Hardware Ground Truth

## Why this exists

External builder feedback indicates that at least some electrical numbers in the earlier TD-1 system-spec draft are wrong.

That is useful feedback even before corrected values are available, because it exposes a process failure mode: **a plausible-looking design number must not become machine truth merely because it appeared in a spec.**

The repository therefore treats the earlier `TRIT_CELL_REV0` electrical recipe as **provisional and unverified**. It is not a build authority. In particular, do not infer nominal trit voltages, comparator thresholds, rail topology, resistor-ladder values, hysteresis, loading, or settling requirements from that old draft.

The corrected builder values have not yet been supplied to this repository. This document intentionally does not guess them.

## What is actually normative today

The following are logical/software profile choices:

- balanced-ternary state values `-1`, `0`, `+1`;
- the current reference-machine profile of 12-trit words, 9 registers, and 729 memory words;
- logical arithmetic and ISA behavior;
- deterministic golden vector meanings such as `TRIT-NEG`, `TRIT-ZERO`, and `TRIT-POS`;
- parity request/response semantics and evidence integrity.

Those values define what the current Simulacrum means. They do **not** specify how a board must encode a trit electrically.

The current 12-trit/9-register/729-word profile is also not proof that those are optimal physical-machine dimensions. If real hardware constraints or reviewed external engineering evidence justify a different physical architecture, that becomes an explicit architecture/schema review rather than a silent electrical assumption.

## What is explicitly not normative

Until measurement/review says otherwise, TD-1 has no normative repository default for:

- positive-only versus bipolar supply rails;
- physical voltage assigned to `-1`, `0`, or `+1`;
- comparator switching thresholds;
- hysteresis magnitude;
- voltage-divider or resistor-ladder topology;
- op-amp/comparator part choice;
- common-mode range or output-swing margin;
- source/sink current requirement;
- fan-out;
- load impedance;
- settling time;
- sample cadence;
- analog tolerance bands;
- temperature drift limits;
- PCB stack-up, connector, or pinout.

The software must be capable of recording whatever the real board measures. For that reason, bench voltage telemetry is signed and the characterization schema supports both positive and negative measured rails/outputs.

## Characterization artifact

`td1.trit-cell-characterization` v1 records measured evidence for one physical unit without creating acceptance limits.

It contains:

- board revision, unit ID, and bench ID;
- explicit instrument references;
- measured supply/reference/other node voltages in signed microvolts;
- ordered observations for commanded logical `-1`, `0`, and `+1` states;
- measured output voltage, explicit load identity/resistance, optional settling time, comparator code, and temperature;
- optional rising/falling comparator switching observations in signed microvolts;
- canonical JSON and SHA-256 digest.

At least one observation of each logical state is required. At least one measured supply node is required. The artifact may describe a single-supply, split-supply, shifted-level, or other implementation because no rail topology is assumed by the schema.

`voltage_summary()` reports only count/min/max for each commanded state. It deliberately does not infer a legal threshold or declare the board good.

## First-copper measurement gate

Before the physical cell is allowed to advertise `trit_hold`, perform the following engineering sequence.

1. **Resolve the schematic from evidence.** Review the experienced builder's corrections and component datasheets. Record the actual topology/revision being built. Do not build from the old speculative numeric recipe.
2. **Verify device operating ranges on paper.** For every active part, check supply limits, input common-mode range, output swing, input/output current, propagation/settling behavior, and any open-drain/pull-up requirements against the intended rails and loads.
3. **Power only the reference/rail network first.** Measure every rail and reference node. Stop if the measured nodes do not match the reviewed schematic expectation.
4. **Measure all three generated states unloaded/high-impedance.** Capture repeated samples for commanded `-1`, `0`, and `+1`.
5. **Repeat under explicit loads.** Use the actual next-stage input or representative resistive loads. Record the load rather than assuming fan-out.
6. **Characterize transitions.** Sweep through both directions for each comparator boundary and record rising/falling switching points. This is where real hysteresis becomes evidence rather than a guessed resistor value.
7. **Measure settling.** Determine the time to a stable output under the intended load and measurement bandwidth. Do not promote a single oscilloscope screenshot into a universal limit.
8. **Check temperature sensitivity where practical.** At minimum record ambient/device temperature for characterization runs; broaden testing before defining environmental limits.
9. **Only then run logical parity.** Implement the existing wire endpoint, advertise only `trit_hold`, `max_width=1`, and run the three fixed golden vectors.
10. **Preserve both kinds of evidence.** Save the characterization artifact plus the parity report/transcript/evidence bundle. Electrical evidence and logical parity answer different questions.

## Acceptance criteria come later

A future `td1.electrical-acceptance-profile` must be a separately versioned contract derived from reviewed topology, datasheet constraints, and measured distributions across enough samples/units/loads to justify limits.

It must not be produced automatically from one characterization artifact.

Until that profile exists, a parity result can say the target returned the correct logical state for the tested request. It cannot claim that the analog implementation has sufficient noise margin, fan-out, hysteresis, environmental stability, or production tolerance.

## Repository audit note

The hardware-grounding pass found one concrete latent assumption in the existing software boundary: `BenchTelemetry.voltage_uv` rejected negative voltages, implicitly favoring a single-supply representation. That restriction is removed in the hardware-ground-truth branch. The wire value is now a signed integer measurement relative to the bench/device reference.

The pass also removes old spec-shaped voltage values from test fixtures so tests validate the schema rather than quietly memorializing a disputed electrical design.

## Design rule

**Logical state is normative. Electrical representation is measured. Acceptance is earned from evidence.**
