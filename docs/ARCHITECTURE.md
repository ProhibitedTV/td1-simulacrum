# TD-1 Simulacrum Architecture

## 1. Normative role

The Simulacrum is the executable reference definition of TD-1. It makes logical machine behavior precise before physical ternary subsystems are fabricated.

The emulator is not a visual mockup. It is the **normative machine model** against which later hardware is compared.

## 2. Authority boundaries

```text
Veilbreak corpus
      |
      v
frozen provenance / interface constraints
      |
      v
State Weave -> typed lowering -> 12-trit reference machine
                                  |
                                  v
                             TraceRecorder
                                  |
              +-------------------+-------------------+
              |                                       |
              v                                       v
      td1.machine-state                      td1.execution-trace
                                                      |
                           +--------------------------+-------------------------+
                           |                          |                         |
                           v                          v                         v
                deterministic inspection       td1.debug-run        td1.parity-campaign
                           |                                                |
                           v                                                v
                   td1.machine-state                               campaign parity run

fixed golden vectors ---------------------> fixed parity run
              |                                       |
              +-------------------+-------------------+
                                  |
                                  v
                           ParityTransport
                                  |
                                  v
                           td1.parity-wire
                                  |
                                  v
                      RecordingParityLineIO
                                  |
                                  v
                        StreamParityLineIO
                                  |
                                  v
                        PySerialByteStream
                                  |
                                  v
                     optional physical byte link
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
           exact wire transcript          parity response
                    |                           |
                    +-------------+-------------+
                                  |
                                  v
                         td1.parity-report
                           /              \
                          /                \
                         v                  v
             td1.parity-wire-evidence   td1.parity-campaign-run
                                              |
                                              v
                                    td1.parity-bench-run

reference machine -> render state -> native geometry -> Relic playback
```

Authority rules:

1. logical machine semantics are normative;
2. `td1.machine-state` persists execution truth only;
3. `TraceRecorder` observes real `Machine.step()` transitions and is shared by complete tracing and live debugging;
4. `td1.execution-trace` records exact logical transitions without freezing physical encoding and may represent a complete execution or an exact non-halted prefix;
5. trace inspection may reconstruct and query existing trace truth but may not create execution semantics or synthetic reverse instructions;
6. debugger stops may pause host execution but may not mutate machine truth, add breakpoint instructions, or become trace events;
7. fixed golden suites represent explicit focused subsystem stimuli and do not manufacture workload provenance;
8. parity campaigns derive only subsystem operations the parity surface can represent faithfully from real logical traces;
9. `td1.parity-wire` transports existing parity contracts but does not redefine them;
10. `StreamParityLineIO` moves and buffers bytes and does not interpret arithmetic;
11. `PySerialByteStream` is optional deployment plumbing and does not create machine semantics;
12. serial port, baud rate, and host timeout values are deployment configuration, not machine state;
13. wire transcripts preserve exact transport evidence but are not arithmetic truth or hardware signatures;
14. generic wire-evidence bundles bind any report to its exact implied transcript without inventing campaign provenance;
15. campaign bench-run bundles bind one trace-derived campaign run to the same report/transcript relationship;
16. rendering and browser playback remain downstream of machine truth;
17. physical hardware becomes authoritative only after deterministic parity testing.

## 3. Reference machine

Baseline parameters:

- radix: balanced ternary;
- trit values: `-1`, `0`, `+1`;
- word width: 12 trits;
- signed range: `-265720 .. +265720`;
- general-purpose registers: 9;
- initial memory: 729 words;
- condition state: negative / zero / positive.

Fixed-width arithmetic wraps modulo `3^12`, mapped back into the symmetric balanced-ternary interval. Negation is exact tritwise sign inversion.

Current logical operations:

`NOP`, `LDI`, `MOV`, `ADD`, `SUB`, `NEG`, `ADDI`, `CMP`, `LD`, `ST`, `BRN`, `BRZ`, `BRP`, `JMP`, `HALT`.

Branches use offsets relative to the instruction following the branch. Memory addressing wraps modulo 729.

### Physical instruction encoding policy

The current target shape remains:

```text
[ opcode:3 ][ reg A:2 ][ reg B:2 ][ immediate/relative:5 ]
```

This is not a normative physical encoding table. Issue #2 remains deferred until first-hardware measurements and semantic-lowering constraints can be reviewed together.

No amount of host tooling, debugging, transport, or evidence maturity substitutes for those measurements.

## 4. Machine-state persistence

`td1.machine-state` is the renderer-independent persistence boundary for logical execution state.

It records architecture invariants, instruction pointer, condition state, halted state, step count, all registers, sparse nonzero memory, and the complete machine digest.

It excludes glyphs, Observer Continuity, geometry, corpus provenance, browser state, parity transport, serial configuration, transcripts, debugger stop metadata, and physical instruction encoding.

Checkpoint restore must reconstruct a `Machine` with the claimed complete digest. Resume tests require the same final state as uninterrupted execution.

## 5. Execution traces, inspection, debugging, and workload parity

`td1.execution-trace` records one exact transition per executed logical instruction, including before/after machine digests, control state, and register/memory deltas.

The trace schema is permitted to represent either:

- a complete execution ending in machine HALT; or
- an exact prefix ending at any ordinary non-halted machine boundary.

A host-side pause is not encoded as HALT.

### 5.1 Shared incremental trace recording

`TraceRecorder` is the single event-construction path for both complete tracing and debugger execution.

For every step it:

1. validates the current instruction pointer against the logical program;
2. captures the complete before-state digest and exact register/memory/control state needed for deltas;
3. invokes the normative `Machine.step()` implementation;
4. derives the canonical `ExecutionEvent` from that real transition;
5. appends the event to an immutable-order trace prefix.

`trace_program()` is therefore a policy around `TraceRecorder`: continue stepping until HALT or the caller's deterministic step ceiling is exceeded.

`verify_execution_trace()` replays exactly the number of events present in the artifact and requires canonical equality. This verifies both complete traces and non-halted prefixes without giving a pause machine semantics.

### 5.2 Deterministic trace inspection

v0.20 added a downstream time-travel inspection layer over the trace contract.

For a trace containing `N` events, inspection exposes `N + 1` exact boundaries:

```text
position 0  = trace initial state
position 1  = state after event 0
...
position N  = trace final state
```

`trace_state_at()` reconstructs a requested boundary from the validated initial state plus recorded register, memory, instruction-pointer, condition, halt, and step changes. Every traversed event must reproduce its existing `before_digest` and `after_digest` complete machine-state chain. The output is an ordinary `td1.machine-state` checkpoint rather than an inspection-specific persistence schema.

`TraceCursor` supplies seek, forward, and backward movement over immutable trace boundaries. Backward movement reconstructs an earlier boundary from trace truth; it does not reverse-execute a synthetic inverse opcode.

`TraceQuery` selects existing events by logical instruction index, logical opcode, touched register, touched memory address, condition-state change, and halt transition. Querying does not insert derived execution events.

See [`TRACE_INSPECTION.md`](TRACE_INSPECTION.md) and ADR 0020.

### 5.3 Deterministic live debugging

v0.21 adds live stop conditions without creating a second execution authority.

`DebugStopSpec` separates two classes of host observation:

- instruction-index and opcode **breakpoints** are evaluated before the next logical instruction executes;
- register and memory **watchpoints** are evaluated after the real event that changed the watched state.

`td1.debug-run` embeds the exact execution-trace prefix plus deterministic stop metadata. Stop kinds are:

- `halted` — the machine really executed HALT;
- `breakpoint` — host execution paused before a matching instruction;
- `watchpoint` — host execution paused after a matching state change;
- `event_budget` — host execution paused after a deterministic number of events while the machine remained live.

Breakpoint/watchpoint matches and event budgets are metadata. They cannot alter instruction pointer, condition state, registers, memory, step count, or halted state.

`verify_debug_run()` first verifies the embedded trace prefix, then re-runs the same debugger configuration from the captured initial state and requires canonical artifact equality. This proves the stop decision is deterministic for the supplied program and initial machine state.

Checkpoint-style continuation may explicitly skip breakpoint evaluation at the supplied initial boundary once. That policy is recorded in the debug artifact; it does not modify the machine.

The debugger does **not** define a BREAK opcode, reverse execution semantics, wall-clock timing, physical debug pins, JTAG/UART debug commands, or hardware breakpoint circuitry.

See [`DEBUGGING.md`](DEBUGGING.md) and ADR 0021.

### 5.4 Workload parity campaigns

`td1.parity-campaign` converts trace events into deterministic subsystem conformance vectors only when the current parity surface has a faithful equivalent.

Current v1 mappings:

| Logical event | Subsystem parity operation |
| --- | --- |
| `LDI` | `register_load` |
| `MOV` | `register_load` |
| `LD` | `register_load` of the traced destination value |
| `NEG` | `negate` |
| `ADD` | `add` |
| `SUB` | `sub` |
| `ADDI` | subsystem `add` with fixed-width immediate operand |

`NOP`, `CMP`, `ST`, branches, `JMP`, and `HALT` do not emit v1 campaign vectors.

A campaign embeds its source trace plus exact initial/final machine checkpoints. Loading a campaign re-derives the entries rather than trusting saved claims.

`td1.parity-campaign-run` binds one exact campaign to one exact conformance report.

## 6. Fixed first-hardware golden suites

The first planned physical target is smaller than a workload campaign: one ternary state cell advertising only `trit_hold`, width 1.

`golden_trit_vectors()` contains exactly:

```text
TRIT-NEG   -
TRIT-ZERO  0
TRIT-POS   +
```

Those vectors are a fixed bench conformance suite, not trace-derived workload evidence.

`golden_register_vectors(width)` remains backward compatible and derives its first three vectors from that canonical trit suite before adding register-load stimuli.

`td1-parity serial-golden --suite trit` therefore expresses the honest first-cell claim without fabricating logical-workload provenance. A trit-only target produces one capability exchange plus exactly three parity exchanges.

See [`FIRST_HARDWARE_GOLDEN.md`](FIRST_HARDWARE_GOLDEN.md) and ADR 0019.

## 7. Parity semantics

Current parity operations are:

- `trit_hold`;
- `register_load`;
- `negate`;
- `add`;
- `sub`.

Targets advertise supported operations and maximum width. Unsupported vectors are capability-gated rather than misclassified as device faults.

Responses distinguish `ok`, `unsupported`, `fault`, `timeout`, and `error` at the parity-protocol level.

Host adapter failures such as serial timeouts are separate from target `ParityStatus` values.

## 8. Canonical parity wire

`td1.parity-wire` is the deterministic byte-oriented adapter protocol underneath `ParityTransport`.

Wire v1 message kinds:

- `capabilities_request`;
- `capabilities_response`;
- `parity_request`;
- `parity_response`.

Each frame is canonical UTF-8 JSON followed by exactly one LF. The default maximum frame size is 65,536 bytes including that LF.

The envelope wraps existing `ParityCapabilities`, `ParityRequest`, and `ParityResponse` payloads. It does not duplicate their semantics.

`JsonLineParityTransport` adapts `ParityLineIO` to the existing parity interface. `ParityWireDevice` is the Python reference device-side dispatcher used in CI.

## 9. Stream-backed line I/O

`StreamParityLineIO` implements `ParityLineIO` over generic binary reader/writer streams.

It owns:

- deterministic partial-write completion;
- optional writer flushing;
- fragmented-read buffering;
- extraction of one LF-terminated frame;
- preservation of later coalesced frame bytes;
- enforcement of the wire frame ceiling;
- explicit EOF, oversized-frame, read, and write failures;
- deterministic byte/frame/buffer counters.

It does not parse JSON or decide parity meaning.

Lower-layer `ParityStreamError` subclasses are preserved so deployment adapters can retain specific diagnostics.

## 10. Optional serial deployment adapter

`PySerialByteStream` and `SerialConfig` form an optional deployment layer beneath `StreamParityLineIO`.

```text
JsonLineParityTransport
        |
        v
RecordingParityLineIO
        |
        v
StreamParityLineIO
        |
        v
PySerialByteStream
        |
        v
pyserial
        |
        v
UART / USB CDC device
```

Core installs remain dependency-free. Pyserial is loaded lazily only when live serial use is requested.

`SerialConfig` requires explicit port, baud rate, host read timeout, and host write timeout.

TD-1 defines no default baud rate and performs no automatic port discovery.

Finite serial read timeouts mean a zero-byte pyserial read is classified as `ParitySerialReadTimeoutError`, not generic EOF.

Two live execution surfaces sit above the same adapter:

- `td1-parity serial-golden` for fixed focused suites;
- `td1-parity serial-run` for saved trace-derived campaigns.

Deployment settings and stream counters may be displayed in CLI summaries but are not silently copied into canonical parity artifacts.

See [`SERIAL_ADAPTER.md`](SERIAL_ADAPTER.md), ADR 0018, and ADR 0019.

## 11. Wire transcripts and report linkage

`td1.parity-wire-transcript` records exact canonical frames at the `ParityLineIO` boundary.

Each record preserves contiguous ordinal, host/device direction, exact frame text including LF, frame SHA-256, decoded message kind, correlation ID, and envelope digest.

`RecordingParityLineIO` can wrap in-memory, generic stream, or serial-backed line I/O without changing transcript schema.

`ReplayParityLineIO` requires exact host request bytes and returns exact recorded device bytes. Replay must consume the full transcript.

`transcript_for_report()` reconstructs the exact canonical wire conversation implied by any `td1.parity-report`.

`validate_report_transcript()` is the single linkage rule used by both generic wire evidence and campaign bench runs. It rejects substitution of target capabilities, session, vectors, responses, telemetry, or canonical frames.

## 12. Generic wire evidence and campaign bench evidence

`td1.parity-wire-evidence` binds any exact `td1.parity-report` to the exact transcript implied by that report. It is independent from workload campaigns and is therefore suitable for fixed first-hardware suites.

`replay_wire_evidence()` replays the exact saved vectors and session through `JsonLineParityTransport -> ReplayParityLineIO` and requires canonical report equivalence.

`td1.parity-bench-run` keeps its v1 schema. It binds a trace-derived `td1.parity-campaign-run` to the same exact report/transcript relationship and reuses the shared validation rule.

`replay_bench_run()` must regenerate the same canonical campaign run.

Transcript/evidence hashes are integrity fingerprints, not cryptographic hardware-authorship proof.

## 13. Bench telemetry

Wire/parity responses may include optional first-bench telemetry keys:

```text
voltage_uv
settle_us
comparator_code
sample_count
board_revision
temperature_millic
```

These remain metadata in the current contract. They do not alter arithmetic pass/fail evaluation.

Electrical acceptance limits require a separate versioned contract after real measured distributions exist.

## 14. Semantic and native representation layer

TD-1's native operator model uses semantic roots rather than alphabetic text.

Current roots include:

`OBSERVER`, `ORIGIN`, `TIME`, `REFERENCE`, `MOTION`, `MEMORY`, `LINK`, `STATE`, `FRAME`, `AXIS`, `SIGNAL`, `COGNITION`, `EXECUTION`, `TRANSFORM`, `ISOLATION`, `DOMAIN`.

Balanced-ternary modifiers provide directional semantics:

- `-`: reverse / remove / contract / deny;
- `0`: inspect / hold / neutral / current;
- `+`: forward / acquire / expand / allow.

`OperandBindings` supplies concrete registers/addresses separately from State Weave identity. Unsupported weaves fail explicitly rather than receiving invented executable meanings.

A 12-trit word partitions into four reversible 3-trit microglyph cells (`3^3 = 27` states each).

## 15. Rendering authority

`td1.render-state` is a deterministic projection from machine state plus allowed presentation inputs.

`td1.geometry-scene` uses integer axial triangular coordinates with discrete depth.

SVG and browser renderers consume geometry. They do not own logical state.

Relic timelines join exact execution events to exact geometry frames. Morph plans may animate between authoritative endpoints but cannot invent endpoint state.

## 16. Observer Continuity

Current groundwork includes timezone-aware UTC timestamps, WGS-84 geodetic -> ECEF conversion, UTC Julian Date, and explicitly approximate Earth Rotation Angle.

Precision navigation remains future work requiring explicit time scales, Earth-orientation data, ephemerides, sensor covariance, and uncertainty contracts.

## 17. Deterministic provenance chains

Major chains remain separable:

```text
source observation -> motif -> requirement -> implementation -> validation

State Weave -> OperandBindings -> logical instructions -> reference machine

Machine -> td1.machine-state -> restore Machine -> identical digest

reference machine -> TraceRecorder -> execution trace
                                      |          |
                                      |          +-> deterministic inspection
                                      |                    |
                                      |                    +-> exact boundary state/query
                                      |
                                      +-> td1.debug-run
                                            |
                                            +-> deterministic host stop metadata

fixed golden vectors -> parity wire -> stream/serial adapter -> target
                                                |
                                                v
                                         exact transcript
                                                |
                                                v
                                         parity report
                                                |
                                                v
                                  td1.parity-wire-evidence

execution trace -> parity campaign -> parity wire -> stream/serial adapter -> target
                                                    |
                                                    v
                                             exact transcript
                                                    |
                                                    v
                                             conformance report
                                                    |
                                                    v
                                          campaign-run / bench-run

execution trace -> render state -> geometry -> timeline/morph -> browser endpoint
```

Digests support integrity, replay, regression, trace-boundary reconstruction, and deterministic debugger-stop verification. They are not authorship signatures unless explicitly stated otherwise.

## 18. Physical replacement gate

A physical subsystem may replace its emulated counterpart only after deterministic conformance against the reference model.

A successful serial connection is not enough. A valid transcript is not enough. A valid evidence bundle is not enough. A visually convincing board is not enough.

Hardware earns authority through parity, and electrical claims require electrical measurements.

## 19. Primary engineering rule

**No decorative weirdness, no semantic hand-waving, no persistence exceptionalism, no debugger exceptionalism, no renderer exceptionalism, no campaign exceptionalism, no wire exceptionalism, no stream/serial exceptionalism, no evidence exceptionalism, and no hardware exceptionalism.**

Every claimed behavior must map to explicit state, a measured event, a documented engineering convention, a versioned rule, or a passing conformance record.
