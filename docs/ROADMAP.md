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

Status: **trace + checkpoint + deterministic time travel + live stop debugging + workload-parity packaging implemented**

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
- deterministic `trace_state_at()` reconstruction at every exact trace boundary;
- per-event delta validation against complete before/after machine digests during time-travel reconstruction;
- `TraceCursor` with seek, forward, and backward inspection over immutable traces;
- deterministic `TraceQuery` filters for opcode, instruction index, touched registers/memory, condition changes, and halt transitions;
- `td1-trace state` and `td1-trace find` engineering workflows;
- shared incremental `TraceRecorder` used by full tracing and debugger execution;
- exact replay verification for complete halted traces and non-halted execution-trace prefixes;
- versioned `td1.debug-run` artifacts with breakpoint, watchpoint, HALT, and deterministic event-budget stops;
- pre-instruction instruction-index/opcode breakpoints and post-instruction register/memory watchpoints;
- checkpoint-style debugger continuation with an explicit initial-breakpoint skip policy;
- `td1-debug run` and `td1-debug verify` engineering workflows;
- versioned `td1.parity-campaign` artifacts derived from real execution traces;
- exact initial/final machine checkpoints embedded in each campaign;
- event-indexed subsystem vectors for encountered register-load, negate, add, and subtract work;
- explicit subsystem-level `ADDI -> add` mapping with no instruction-decode claim;
- strict campaign re-derivation from the embedded source trace;
- versioned `td1.parity-campaign-run` artifacts binding campaign oracle to conformance report;
- dedicated `td1-parity` campaign/parity workflows;
- deterministic register and ALU golden parity vectors.

Next:
- indexed/cached trace seeking only if real traces make O(N) reconstruction materially expensive;
- debugger continuation-chain packaging only if multi-stop sessions need one canonical history artifact;
- checkpoint/campaign-aware real hardware differential testing;
- versioned program image only after first-hardware constraints are available;
- optional compact/binary persistence after audit-first JSON schemas stabilize.

`td1.machine-state`, `td1.execution-trace`, trace inspection state, `td1.debug-run`, and `td1.parity-campaign` are not physical program-image formats and do not freeze Issue #2.

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

Status: **host software ready for an honest first one-trit live bench session**

Implemented:
- capability advertisement and versioned parity request/response/report schemas;
- deterministic ternary slice-state digests;
- explicit `golden_trit_vectors()` containing exactly `TRIT-NEG`, `TRIT-ZERO`, and `TRIT-POS`;
- backward-compatible register golden vectors derived from that canonical trit prefix;
- deterministic register and ALU golden suites;
- explicit `ok`, `unsupported`, `fault`, `timeout`, and `error` outcomes;
- capability-gated conformance sessions and replayable reports;
- deterministic trace-derived parity campaigns and campaign-run artifacts;
- strict separation between subsystem-operation parity and future physical instruction-decode parity;
- canonical `td1.parity-wire` JSON Lines framing around existing parity payloads;
- deterministic capability and parity request/response correlation;
- `JsonLineParityTransport` over minimal `ParityLineIO`;
- reference `ParityWireDevice` plus in-memory wire integration;
- bench telemetry naming conventions for voltage, settling, comparator state, samples, board revision, and optional temperature;
- versioned `td1.parity-wire-transcript` exact byte-level transport receipts;
- `RecordingParityLineIO`, strict `ReplayParityLineIO`, and deterministic transcript reconstruction;
- shared report/transcript validation reused by generic evidence and campaign bench bundles;
- versioned `td1.parity-wire-evidence` for exact report/transcript linkage independent of workload campaigns;
- deterministic generic wire-evidence replay using saved vectors/session and canonical report equivalence;
- versioned `td1.parity-bench-run` retained unchanged for trace-derived campaign evidence;
- minimal binary reader/writer/duplex stream protocols;
- `StreamParityLineIO` with partial-write completion, fragmented/coalesced read buffering, bounded frame handling, explicit adapter errors, and deterministic counters;
- optional `serial` dependency extra for pyserial while core installs remain dependency-free;
- explicit `SerialConfig` deployment settings for port, baud rate, and finite host read/write timeouts;
- `PySerialByteStream` with lazy pyserial loading, serial timeout/error classification, closed-port protection, and deterministic close/context-manager behavior;
- preservation of serial-specific stream errors through `StreamParityLineIO`;
- `td1-parity serial-golden` for fixed first-hardware suites with optional report/transcript/evidence emission;
- `td1-parity serial-run` retained for saved trace-derived workload campaigns;
- serial deployment settings and stream counters kept in CLI diagnostics rather than silently inserted into normative parity artifacts;
- fake/injected serial test infrastructure so default CI requires neither pyserial nor physical hardware;
- a trit-only fake target proving the first-hardware session shape is one capability exchange plus exactly three parity exchanges.

Next:
- build and independently measure the first real `TRIT_CELL_REV0` cell;
- choose explicit deployment settings for the actual UART/USB-CDC bench device;
- implement the existing parity-wire device side on the bench controller;
- advertise only `trit_hold`, `max_width=1`;
- run `td1-parity serial-golden --suite trit` against the real device;
- capture real `voltage_uv`, `settle_us`, `comparator_code`, `sample_count`, and `board_revision` telemetry;
- preserve the first genuine hardware report, exact transcript, and `td1.parity-wire-evidence` artifact;
- replay that evidence offline;
- inspect measured electrical distributions before defining acceptance thresholds;
- multi-trit register-slice adapter and fixed register-suite bring-up;
- execute trace-derived campaigns against real adapters only once workload provenance is meaningful;
- versioned electrical acceptance criteria after measured distributions exist;
- optional authenticated hardware identity only if bench provenance actually requires it;
- ALU-board conformance after register-slice success;
- physical subsystem replacement gate in the emulator runtime.

Exit criterion: at least one physical ternary subsystem replaces its emulated counterpart and passes the same reference semantics with preserved bench evidence.

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
- creating debugger-owned logical state or synthetic reverse-instruction semantics;
- treating debugger stops, breakpoint/watchpoint metadata, or event budgets as machine events;
- treating trace queries as new execution events;
- claiming fixed first-hardware vectors or trace-derived subsystem parity prove physical instruction decoding;
- manufacturing workload provenance for a fixed electrical bring-up suite;
- treating wire framing, stream counters, serial configuration, transcript hashes, evidence digests, or telemetry as arithmetic semantics;
- treating transcript SHA-256 values as authenticated device signatures;
- adding nondeterministic wall-clock timestamps to normative evidence artifacts;
- auto-discovering a serial port or defining a TD-1 default baud rate;
- defining USB identity, connector, pinout, retry/reconnect policy, or electrical thresholds before the bench hardware earns those choices;
- claiming navigation-grade accuracy before the timing/reference stack earns it;
- inventing animation activity not grounded in traced state changes;
- fabricating executable meanings for unsupported State Weaves;
- treating a physical board as authoritative before deterministic parity passes;
- allowing renderer/browser state to become machine truth;
- allowing presentation timing/interpolation to fabricate machine state;
- allowing corpus-derived hints to lose provenance or become arithmetic semantics;
- using `td1.render-state` as the long-term persistence format for logical execution.
