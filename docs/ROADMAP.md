# TD-1 Simulacrum Roadmap

This roadmap is milestone-driven rather than date-driven. Software maturity does not freeze physical design choices that still require bench evidence.

## M0 — Reference core

Status: **implemented / stabilizing**

Implemented:
- balanced-ternary arithmetic;
- 12-trit words;
- 9-register / 729-word machine;
- logical ISA;
- deterministic snapshots and full machine-state digest;
- tests and CI.

Exit criterion: deterministic execution with no known semantic ambiguity in the logical ISA.

## M1 — Engineering toolchain

Status: **trace + checkpoint foundation implemented**

Implemented:
- text assembler/disassembler, labels, relative branches, CLI, and examples;
- versioned `td1.execution-trace` with logical-program fingerprints;
- per-instruction machine digest chain plus register/memory deltas;
- deterministic trace replay verification;
- versioned renderer-independent `td1.machine-state` checkpoints;
- explicit architecture metadata: word width, register count, and memory size;
- exact register state plus sparse nonzero memory persistence;
- canonical checkpoint JSON and SHA-256 digests;
- strict restore-time validation against the existing complete emulator machine digest;
- intermediate checkpoint/resume with final-state equivalence to uninterrupted execution;
- explicit `RenderState -> MachineState` bridge that copies machine truth only;
- CLI checkpoint emit / verify / resume commands;
- deterministic register and ALU golden parity vectors.

Next:
- trace-to-parity campaign packaging;
- checkpoint-aware physical differential testing;
- versioned program image format after first-hardware constraints are available;
- optional compact/binary persistence only after the audit-first JSON schemas stabilize.

`td1.machine-state` is not a program-image format and does not freeze Issue #2.

## M2 — Native representation

Status: **native geometry + transition + morph planning + reference rendering + standalone browser playback implemented**

Implemented:
- reversible 27-state microglyph mapping;
- State Weave semantic IR and typed operand lowering;
- versioned `td1.render-state` with deterministic Engineering/Relic projections;
- versioned `td1.geometry-scene` on an integer axial triangular lattice plus depth;
- reversible geometry for all 27 microglyph states;
- deterministic register, memory, control, and State Weave geometry;
- corpus-admitted lattice/depth/multiscale/braiding rules with source provenance;
- versioned `td1.geometry-delta` stable-ID transition classification;
- deterministic `td1.svg-render` reference renderer;
- versioned `td1.relic-timeline` with one exact frame per execution event;
- versioned `td1.morph-plan` and timeline-wide morph manifests;
- exact `(dq, dr, dz)` translation vectors for real moves;
- conservative endpoint-only behavior without admitted temporal evidence;
- source-traceable temporal presentation hints where admitted;
- versioned `td1.relic-player-config` and `td1.relic-player-artifact`;
- dependency-free standalone browser player;
- browser-side SHA-256 verification of embedded canonical payloads;
- Python-side artifact verification that regenerates deterministic morph plans;
- projection parity with the SVG reference renderer;
- hard reconciliation to exact authoritative endpoint geometry after every animation;
- zero-text Relic canvas with explicit Engineering/provenance diagnostics;
- Node syntax gating for the packaged browser runtime.

Next:
- first interactive Relic Mode semantic control surface while preserving endpoint authority;
- optional WebGL renderer proven equivalent to native/SVG geometry contracts;
- storage-efficient timeline/morph packaging;
- broader browser compatibility tests as the player surface expands.

## M3 — Corpus pipeline

Status: **frozen snapshot foundation implemented**

Implemented:
- source observation / interpretation separation;
- requirement-trace model;
- versioned `VB-TD1-*` snapshot schema;
- canonical serialization and snapshot digests;
- explicit Veilbreak field mapping;
- motif annotations with annotation-method provenance;
- strict source -> motif -> requirement tracing;
- offline synthetic fixtures.

Next:
- bind the adapter to a reviewed real public Veilbreak export/API schema;
- freeze the first genuine `VB-TD1-*` baseline;
- model-assisted motif candidate extraction with human review;
- corpus-backed interface requirement files and design-delta reports.

## M4 — Observer Continuity

Status: **terrestrial groundwork implemented**

Implemented:
- WGS-84 geodetic -> ECEF;
- UTC Julian Date;
- explicitly approximate Earth Rotation Angle;
- quantized render-state projection.

Next:
- velocity/orientation state;
- ECI transforms;
- explicit time-scale handling;
- Sun/Moon geometry;
- ephemeris backend;
- uncertainty contracts.

## M5 — Physical parity interface

Status: **transport-neutral conformance foundation implemented**

Implemented:
- capability advertisement;
- versioned parity request/response/report schemas;
- deterministic ternary slice-state digests;
- register/trit and ALU golden vectors;
- explicit `ok`, `unsupported`, `fault`, `timeout`, and `error` outcomes;
- capability-gated conformance sessions;
- replayable conformance reports;
- reference loopback target;
- first campaign scoped to `trit_hold` then register-slice loads.

Next:
- first real one-trit hardware adapter;
- voltage/settling/comparator telemetry convention;
- multi-trit register-slice adapter;
- connect execution traces and machine checkpoints to physical conformance sessions;
- ALU-board conformance after register-slice success;
- physical subsystem replacement gate in the emulator runtime.

Exit criterion: at least one physical ternary subsystem replaces its emulated counterpart and passes the same golden vectors.

## M6 — Native TD-1 operation

Status: **typed lowering foundation implemented**

Implemented:
- semantic roots and canonical State Weave identity;
- explicit `OperandBindings` separated from semantic identity;
- versioned semantic-lowering artifacts and digests;
- project-defined v1 lowering forms for halt, negate, compare, memory read, and memory write;
- strict unsupported-weave versus invalid-binding failure modes;
- compiler introspection and CLI lowering commands;
- round-trip recompilation checks.

Next:
- compound multi-root semantic forms;
- temporary allocation and multi-instruction lowering plans;
- Observer Continuity semantic operations;
- branch/control-flow semantic forms;
- geometric control surface;
- sober usability studies;
- corpus-derived versus control-interface A/B tests.

The semantic/compiler prerequisite for Issue #2 is implemented. Physical instruction encoding still waits for first-hardware constraints and explicit encoding review.

## Non-goals for early revisions

- treating phenomenology as proof of ontology;
- hiding conventional compute behind decorative weirdness;
- freezing physical instruction encoding before hardware measurements exist;
- claiming navigation-grade accuracy before the timing/reference stack earns it;
- inventing animation activity not grounded in traced state changes;
- fabricating executable meanings for unsupported State Weaves;
- treating a physical board as authoritative before deterministic parity passes;
- allowing renderer/browser state to become machine truth;
- allowing presentation timing/interpolation to fabricate machine state;
- allowing corpus-derived hints to lose provenance or become arithmetic semantics;
- using `td1.render-state` as the long-term persistence format for logical machine execution.
