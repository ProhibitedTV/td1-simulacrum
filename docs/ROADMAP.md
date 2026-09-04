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
- golden test vectors.

## M2 — Native representation

Status: **foundation implemented**

- 27-state microglyph IDs;
- reversible word-to-microglyph mapping;
- semantic roots;
- State Weave v1 IR.

Next:
- renderer-independent geometry schema;
- deterministic morph/topology rules;
- render-state serialization;
- Engineering/Relic equivalence tests.

## M3 — Corpus pipeline

Status: **data model only**

- source-record model;
- requirement-trace model;
- corpus revision identifiers.

Next:
- Veilbreak ingestion adapter;
- frozen corpus snapshot format (`VB-TD1-*`);
- motif extraction;
- design-delta report;
- source-to-requirement trace export.

## M4 — Observer Continuity

Status: **terrestrial groundwork implemented**

- WGS-84 geodetic -> ECEF;
- UTC Julian Date;
- approximate Earth Rotation Angle.

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
