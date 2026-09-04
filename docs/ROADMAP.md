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

Status: **trace + checkpoint + workload-parity packaging implemented**

Implemented:
- text assembler/disassembler, labels, relative branches, CLI, and examples;
- versioned `td1.execution-trace` with logical-program fingerprints;
- per-instruction machine digest chain plus register/memory deltas;
- deterministic trace replay verification;
- versioned renderer-independent `td1.machine-state` checkpoints;
- exact register state plus sparse nonzero memory persistence;
- canonical checkpoint JSON and SHA-256 digests;
- intermediate checkpoint/resume with final-state parity to uninterrupted execution;
- explicit `RenderState -> MachineState` machine-truth bridge;
- versioned `td1.parity-campaign` artifacts derived from real execution traces;
- exact initial/final machine checkpoints embedded in each campaign;
- event-indexed subsystem vectors for encountered register-load, negate, add, and subtract work;
- explicit subsystem-level `ADDI -> add` mapping with no instruction-decode claim;
- strict campaign re-derivation from the embedded source trace;
- versioned `td1.parity-campaign-run` artifacts binding campaign oracle to conformance report;
- dedicated `td1-parity` build/verify/loopback/wire-loopback/run-verify CLI;
- deterministic register and ALU golden parity vectors.

Next:
- checkpoint/campaign-aware real hardware differential testing;
- versioned program image only after first-hardware constraints are available;
- optional compact/binary persistence after audit-first JSON schemas stabilize.

`td1.machine-state` and `td1.parity-campaign` are not physical program-image formats and do not freeze Issue #2.

## M2 — Native representation

Status: **native geometry + transitions + reference rendering + standalone browser playback implemented**

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
- zero-text Relic canvas with Engineering/provenance diagnostics;
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
- versioned `VB-TD1-*` snapshots;
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

Status: **conformance + campaigns + wire + evidence + stream host adapter implemented**

Implemented:
- capability advertisement;
- versioned parity request/response/report schemas;
- deterministic ternary slice-state digests;
- register/trit and ALU golden vectors;
- explicit `ok`, `unsupported`, `fault`, `timeout`, and `error` outcomes;
- capability-gated conformance sessions;
- replayable conformance reports;
- reference loopback target;
- deterministic trace-derived parity campaigns and campaign-run artifacts;
- exact workload event provenance preserved through each derived physical test vector;
- strict separation between subsystem-operation parity and future physical instruction-decode parity;
- versioned `td1.parity-wire` envelope around existing parity payloads;
- canonical UTF-8 JSON Lines framing with explicit maximum frame size;
- deterministic capability and parity request/response correlation;
- `JsonLineParityTransport` host adapter over minimal `ParityLineIO`;
- reference device dispatcher around existing parity targets;
- in-memory line channel exercising the exact wire codec in CI;
- first bench telemetry naming conventions for voltage, settling, comparator state, samples, board revision, and optional temperature;
- versioned `td1.parity-wire-transcript` exact byte-level transport receipts;
- deterministic frame/envelope integrity fingerprints plus legal request/response ordering;
- `RecordingParityLineIO` around any existing line channel;
- strict byte-for-byte `ReplayParityLineIO` with complete-consumption checks;
- deterministic transcript reconstruction from saved conformance reports;
- versioned `td1.parity-bench-run` binding one campaign run to its exact wire transcript;
- offline replay requiring the regenerated campaign report to match the saved report exactly;
- `td1-parity wire-loopback` optional transcript/bench sidecar emission;
- transcript verification and bench-run replay CLI workflows;
- minimal `BinaryByteStream` / reader / writer protocols with no serial-library dependency;
- `StreamParityLineIO` over duplex or split binary streams;
- deterministic partial-write completion and optional writer flushing;
- fragmented/coalesced read buffering with preservation of later frame bytes;
- bounded incoming-line buffering using the existing parity-wire frame ceiling;
- explicit empty-EOF, partial-EOF, frame-too-large, read-failure, and write-failure adapter errors;
- deterministic stream byte/frame/buffer counters with no wall-clock state;
- full campaign -> stream adapter -> transcript -> bench bundle -> offline replay proof in CI.

Next:
- first real one-trit hardware adapter using the v1 wire contract;
- select the actual UART/USB-CDC bench interface and add a thin optional serial-library wrapper around `StreamParityLineIO`;
- measured telemetry capture from TRIT_CELL_REV0;
- multi-trit register-slice adapter;
- execute and preserve trace-derived campaigns against real adapters;
- versioned electrical acceptance criteria after measured distributions exist;
- optional authenticated hardware identity only if bench provenance actually requires it;
- ALU-board conformance after register-slice success;
- physical subsystem replacement gate in the emulator runtime.

Exit criterion: at least one physical ternary subsystem replaces its emulated counterpart and passes the same reference/campaign vectors with preserved bench evidence.

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
- claiming trace-derived subsystem parity proves physical instruction decoding;
- treating wire framing, stream counters, transcript hashes, or telemetry as arithmetic semantics;
- treating transcript SHA-256 values as authenticated device signatures;
- adding nondeterministic wall-clock timestamps to normative transcript artifacts;
- choosing baud rate, USB identity, connector, pinout, or serial package before the actual bench interface exists;
- claiming navigation-grade accuracy before the timing/reference stack earns it;
- inventing animation activity not grounded in traced state changes;
- fabricating executable meanings for unsupported State Weaves;
- treating a physical board as authoritative before deterministic parity passes;
- allowing renderer/browser state to become machine truth;
- allowing presentation timing/interpolation to fabricate machine state;
- allowing corpus-derived hints to lose provenance or become arithmetic semantics;
- using `td1.render-state` as the long-term persistence format for logical execution.
