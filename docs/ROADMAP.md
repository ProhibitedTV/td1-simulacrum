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

Status: **initial implementation**

- text assembler/disassembler;
- labels and relative branches;
- CLI;
- executable examples;
- expanded negative-path tests.

Next:
- program image format;
- versioned machine-state serialization;
- trace/event stream;
- hardware-oriented golden vectors.

## M2 — Native representation

Status: **native geometry contract implemented**

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
- CLI geometry export and golden microglyph geometry fixture.

Next:
- renderer-independent morph/transition descriptors;
- corpus-derived morphing/focus/context constraints;
- geometry-scene delta/event stream;
- first SVG/WebGL reference renderer that consumes geometry without inventing state;
- first interactive Relic Mode frontend.

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

Status: **not started**

- hardware transport abstraction;
- register/ALU differential test harness;
- deterministic parity packets;
- fault injection;
- physical subsystem conformance reports.

Exit criterion: at least one physical ternary subsystem replaces its emulated counterpart and passes the same golden vectors.

## M6 — Native TD-1 operation

Status: **not started**

- State Weave -> semantic compiler;
- semantic IR -> logical ISA lowering;
- geometric control surface;
- zero-text Relic Mode;
- sober usability studies;
- corpus-derived versus control-interface A/B tests.

## Non-goals for early revisions

- pretending phenomenology establishes ontology;
- hiding conventional compute behind a decorative UI;
- freezing exotic hardware before the reference model is stable;
- claiming navigation-grade accuracy before the timing/reference stack earns it.
