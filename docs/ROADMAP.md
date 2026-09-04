# TD-1 Simulacrum Roadmap

This roadmap is deliberately milestone-driven rather than date-driven.

## M0 — Reference core

Status: **implemented / stabilizing**

- balanced-ternary arithmetic;
- 12-trit words;
- 9-register / 729-word machine;
- logical ISA;
- deterministic snapshots;
- state digest;
- tests and CI.

Exit criterion: repeated deterministic execution with no known semantic ambiguity in the logical ISA.

## M1 — Engineering toolchain

Status: **deterministic trace foundation implemented**

Implemented:
- text assembler/disassembler;
- labels and relative branches;
- CLI;
- executable examples;
- expanded negative-path tests;
- versioned `td1.execution-trace` schema;
- logical-program semantic fingerprints;
- per-instruction machine digest chain;
- register and memory deltas;
- deterministic trace replay verification;
- deterministic register and ALU golden parity vectors.

Next:
- versioned program image format;
- versioned standalone machine-state serialization;
- trace export suitable for physical parity sessions.

## M2 — Native representation

Status: **native geometry + transition + reference rendering + replay timeline implemented**

Implemented:
- 27-state microglyph IDs;
- reversible word-to-microglyph mapping;
- semantic roots;
- State Weave v1 IR;
- versioned `td1.render-state` schema;
- deterministic Engineering/Relic projections;
- exact register and sparse-memory reconstruction;
- shared source digest across modes;
- golden render-state fixture;
- quantized Observer Continuity render contract;
- versioned `td1.geometry-scene` schema;
- integer axial triangular lattice coordinates plus discrete depth;
- unique reversible geometry for all 27 microglyph states;
- deterministic four-glyph 12-trit word structures;
- State Weave topology with ternary terminal semantics;
- corpus-backed lattice/depth/multiscale/braiding admission rules;
- per-rule source provenance and geometry-profile digests;
- CLI geometry export and golden microglyph geometry fixture;
- versioned `td1.geometry-delta` schema;
- stable-ID appear/disappear/move/topology/metadata classifications;
- source scene/render digest preservation across geometry deltas;
- deterministic `td1.svg-render` reference renderer consuming only geometry scenes;
- integer axial/depth projection with stable SVG primitive IDs;
- Relic and Engineering themes with geometry-equivalence tests;
- zero-display-text Relic output by default;
- embedded scene/render/machine/profile provenance metadata;
- XML-safe identifiers/labels and deterministic SVG byte digests;
- CLI SVG output to stdout or files;
- versioned `td1.relic-timeline` joining execution events to exact render/geometry frames;
- frame zero plus one deterministic frame per real execution event;
- per-frame machine/render/scene digests and event identity;
- deterministic geometry delta on every noninitial frame;
- replay-time machine-digest verification against `td1.execution-trace`;
- timeline deserialization that rebuilds geometry and revalidates every adjacent delta;
- deterministic `td1.timeline-svg-manifest` plus exact SVG frame sequence export.

Next:
- renderer-independent morph/transition descriptors driven by timeline geometry deltas;
- corpus-derived morphing/focus/context constraints;
- animated browser frontend consuming `td1.relic-timeline` rather than pixel diffs;
- first interactive Relic Mode control surface;
- optional WebGL renderer tested against the SVG reference topology;
- storage-efficient timeline/event packaging after the audit-first schema stabilizes.

## M3 — Corpus pipeline

Status: **frozen snapshot foundation implemented**

Implemented:
- source-record observation/interpretation separation;
- requirement-trace model;
- versioned `VB-TD1-*` snapshot schema;
- deterministic canonical serialization and snapshot digests;
- explicit Veilbreak export field mapping;
- versioned motif annotations with annotation-method provenance;
- strict source -> motif -> requirement trace export;
- source/annotation/motif snapshot deltas;
- offline synthetic fixtures independent of live network content.

Next:
- bind the adapter to a reviewed real public Veilbreak export/API schema;
- freeze the first real `VB-TD1-*` corpus baseline;
- model-assisted motif candidate extraction with human review;
- corpus-backed interface requirement files;
- design-delta reports linked to TD-1 interface revisions.

## M4 — Observer Continuity

Status: **terrestrial groundwork implemented**

- WGS-84 geodetic -> ECEF;
- UTC Julian Date;
- approximate Earth Rotation Angle;
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
- transport-neutral capability advertisement;
- versioned parity request/response schemas;
- deterministic ternary slice-state digests;
- register/trit and ALU golden vectors;
- explicit `ok`, `unsupported`, `fault`, `timeout`, and `error` statuses;
- capability-gated conformance sessions;
- replayable `td1.parity-report` logs with deterministic pass/fail evaluation;
- reference loopback target with fault, width, and observed-value injection;
- CLI vector export, loopback conformance, and report verification;
- first campaign scoped to `trit_hold` followed by register-slice loads.

Next:
- first real one-trit hardware adapter;
- voltage/settling/comparator telemetry schema convention;
- multi-trit register-slice adapter;
- connect execution traces to physical conformance sessions;
- ALU-board conformance after register-slice success;
- physical subsystem replacement gate in the emulator runtime.

Exit criterion: at least one physical ternary subsystem replaces its emulated counterpart and passes the same golden vectors.

## M6 — Native TD-1 operation

Status: **typed lowering foundation implemented**

Implemented:
- semantic roots and canonical State Weave identity;
- State Weave v1 semantic IR;
- explicit `OperandBindings` separated from semantic identity;
- versioned `td1.semantic-lowering` artifacts and digests;
- project-defined v1 lowering forms for halt, negate, compare, memory read, and memory write;
- strict unsupported-weave versus invalid-binding failure modes;
- compiler introspection and CLI lowering commands;
- round-trip recompilation checks that reject serialized lowering drift.

Next:
- compound multi-root semantic forms;
- multi-instruction lowering plans and temporary allocation;
- Observer Continuity semantic operations;
- branch/control-flow semantic forms;
- geometric control surface;
- zero-text Relic Mode;
- sober usability studies;
- corpus-derived versus control-interface A/B tests.

The first semantic/compiler prerequisite for Issue #2 is now implemented. Physical instruction encoding still waits for first-hardware constraints and explicit encoding review.

## Non-goals for early revisions

- pretending phenomenology establishes ontology;
- hiding conventional compute behind a decorative UI;
- freezing exotic hardware before the reference model is stable;
- claiming navigation-grade accuracy before the timing/reference stack earns it;
- inventing animation activity that is not grounded in traced state changes;
- assigning fake executable meanings to unsupported State Weaves for the sake of completeness;
- treating a physical board as authoritative before deterministic parity passes;
- allowing a renderer to infer state that is absent from the native geometry scene;
- allowing playback timing or interpolation to fabricate intermediate machine states.