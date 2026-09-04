# TD-1 Simulacrum Architecture

## 1. Normative role

The Simulacrum is the executable reference definition of TD-1. It makes logical machine behavior precise before physical ternary subsystems are fabricated.

The emulator is not a visual mockup. It is the **normative machine model** against which later hardware is compared.

## 2. Authority boundaries

```text
                         Veilbreak corpus
                               |
                               v
                     frozen corpus/provenance
                               |
                               v
                    interface design constraints
                               |
                               v
Glyph / State Weave -> semantic IR -> typed lowering
                               |
                               v
                     12-trit reference machine
                        /        |         \
                       /         |          \
                      v          v           v
             td1.machine-state   |    td1.execution-trace
             save/restore/resume |     exact transitions
                                 |           |
                                 |           +------> td1.parity-campaign
                                 |                       |
                                 |                       v
                                 |                 parity harness
                                 |                       |
                                 |                       v
                                 |              ParityTransport
                                 |                       |
                                 |                       v
                                 |                td1.parity-wire
                                 |                       |
                                 |                       v
                                 |            RecordingParityLineIO
                                 |                       |
                                 |                       v
                                 |              StreamParityLineIO
                                 |                       |
                                 |                       v
                                 |               binary byte stream
                                 |                       |
                                 |                       v
                                 |                physical adapter
                                 |                       |
                                 |             +---------+---------+
                                 |             |                   |
                                 |             v                   v
                                 |      wire transcript   td1.parity-response
                                 |             |                   |
                                 |             +---------+---------+
                                 |                       |
                                 |                       v
                                 |            td1.parity-campaign-run
                                 |                       |
                                 |                       v
                                 |              td1.parity-bench-run
                                 |
                                 v
                         td1.render-state
                                 |
                                 v
                       td1.geometry-scene
                        /              \
                       v                v
              reference SVG      td1.geometry-delta
                                       |
                                       v
                                 td1.morph-plan
                                       |
                                       v
                               td1.relic-timeline
                                       |
                                       v
                          standalone Relic player
```

The arithmetic core remains independent from phenomenology, rendering, playback, transport framing, byte movement, and transport evidence. Corpus-derived ideas may shape interface semantics or representation, but they do not redefine arithmetic correctness.

The authority rules are:

1. logical machine semantics are normative;
2. `td1.machine-state` persists execution truth only;
3. execution traces record logical transitions without freezing physical encoding;
4. parity campaigns derive only subsystem operations faithfully representable by the parity surface;
5. `td1.parity-wire` transports existing parity contracts but does not redefine them;
6. `StreamParityLineIO` moves and buffers bytes but does not interpret parity semantics;
7. wire transcripts preserve exact transport evidence but do not become arithmetic or machine truth;
8. bench-run bundles bind campaign/report truth to exact wire evidence without claiming device authorship;
9. render state may describe machine truth plus presentation inputs, but is not persistence authority;
10. geometry is derived from validated render state;
11. animation consumes exact geometry transitions and may not invent machine endpoints;
12. physical hardware becomes authoritative only after deterministic parity testing.

## 3. Reference machine

Baseline parameters:

- radix: balanced ternary;
- trit values: `-1`, `0`, `+1`;
- word width: 12 trits;
- signed range: `-265720 .. +265720`;
- general-purpose registers: 9;
- initial memory: 729 words;
- condition state: negative / zero / positive.

### 3.1 Fixed-width arithmetic

Arithmetic wraps modulo `3^12`, mapped back into the symmetric balanced-ternary interval. Negation is exact tritwise sign inversion.

### 3.2 Logical ISA

Current operations:

`NOP`, `LDI`, `MOV`, `ADD`, `SUB`, `NEG`, `ADDI`, `CMP`, `LD`, `ST`, `BRN`, `BRZ`, `BRP`, `JMP`, `HALT`.

Branches use offsets relative to the instruction following the branch. Memory addresses are formed from a base register plus immediate offset and wrap modulo 729.

### 3.3 Physical instruction encoding policy

The logical ISA exists before physical encoding is frozen.

The current target layout remains:

```text
[ opcode:3 ][ reg A:2 ][ reg B:2 ][ immediate/relative:5 ]
```

This is a design target, not a normative physical encoding table. Issue #2 remains intentionally deferred until semantic-lowering constraints and first-hardware measurements can be reviewed together.

Neither browser maturity, checkpoint persistence, trace-derived parity campaigns, parity wire framing, stream transport, nor wire transcripts relax that gate. Campaigns and wire artifacts contain subsystem operands/results and transport evidence, not physical instruction words.

## 4. Standalone machine-state persistence

`td1.machine-state` is the renderer-independent persistence boundary for logical execution state.

Schema v1 records architecture invariants, instruction pointer, ternary condition, halted state, step count, all registers, exact sparse nonzero memory, and the complete existing emulator machine-state digest.

It deliberately excludes glyphs, Observer Continuity, State Weaves, geometry, corpus provenance, browser state, transport framing/evidence, stream diagnostics, and physical instruction encoding.

A checkpoint is accepted only if reconstructing a real `Machine` reproduces the claimed complete machine digest. Canonical checkpoint JSON has its own SHA-256 distinct from the reconstructed machine digest.

Intermediate checkpoints may be restored and resumed. Tests require checkpoint -> restore -> resume to reach the same final complete machine digest as uninterrupted execution.

## 5. Engineering toolchain

The conventional text toolchain exists for engineering, fixtures, and parity while the native geometric operator language evolves.

Current surfaces include:

- `td1-sim` for execution, traces, checkpoints, semantic lowering, geometry, timelines, rendering, browser artifacts, and base parity tooling;
- `td1-parity` for trace-derived campaign build/verify, direct loopback, wire-loopback, run verification, wire-transcript verification, and bench-run replay;
- deterministic execution and trace replay;
- machine checkpoint emit/verify/resume;
- frozen corpus validation/comparison;
- transport-neutral conformance reports;
- canonical parity wire framing and in-memory wire integration tests;
- exact wire recording/replay and linked bench-evidence bundles;
- stream-backed `ParityLineIO` over ordinary binary reader/writer objects;
- standalone Relic artifact verification.

Text assembly is an engineering interface, not the intended final native operator interface.

## 6. Semantic layer

TD-1's native operator model uses semantic roots rather than alphabetic text.

Current roots:

`OBSERVER`, `ORIGIN`, `TIME`, `REFERENCE`, `MOTION`, `MEMORY`, `LINK`, `STATE`, `FRAME`, `AXIS`, `SIGNAL`, `COGNITION`, `EXECUTION`, `TRANSFORM`, `ISOLATION`, `DOMAIN`.

Balanced-ternary modifiers carry directional semantics:

- `-`: reverse / remove / contract / deny;
- `0`: inspect / hold / neutral / current;
- `+`: forward / acquire / expand / allow.

### 6.1 Typed lowering boundary

State Weave identity does not implicitly select registers or addresses. `OperandBindings` supplies concrete resources, and supported semantic forms lower into deterministic logical instructions.

Initial executable forms remain deliberately conservative:

- `EXECUTION:-` -> `HALT`;
- `TRANSFORM:-` -> `NEG`;
- `STATE:0` -> `CMP`;
- `MEMORY:0` -> `LD`;
- `MEMORY:+` -> `ST`.

These are TD-1 engineering conventions, not claimed phenomenological translations. Unsupported State Weaves fail explicitly.

## 7. Native representation and rendering

### 7.1 Microglyphs

A 12-trit word partitions into four 3-trit cells. Each cell has `3^3 = 27` states.

```text
glyph_id = balanced_ternary_value(triad) + 13
```

produces reversible `G00 .. G26` identities.

### 7.2 Render state

`td1.render-state` is the deterministic bridge from machine state into presentation inputs. It may include machine truth together with Observer Continuity and State Weave data required for display.

It is not the long-term machine persistence boundary; `td1.machine-state` owns that role.

### 7.3 Native geometry

`td1.geometry-scene` uses integer axial triangular coordinates `(q, r, z)` and preserves source machine/render digests, stable primitive identity/topology, and optional source-traceable corpus geometry rules.

### 7.4 Reference SVG renderer

`td1.svg-render` consumes only validated geometry.

```text
x = (2q + r) * unit + z * depth_x
y = 3r * unit - z * depth_y
```

Relic and Engineering themes share identical projected geometry. Presentation styling does not create state.

## 8. Execution traces

`td1.execution-trace` records one exact logical transition per executed instruction:

- logical program fingerprint;
- before/after complete machine digests;
- instruction identity;
- instruction-pointer and condition transitions;
- halted transition;
- exact register and memory deltas.

Replay against the original logical program must regenerate the canonical trace exactly.

Trace artifacts intentionally contain logical instructions rather than physical instruction words.

## 9. Trace-derived parity campaigns

`td1.parity-campaign` converts operations encountered during one exact execution trace into reproducible subsystem conformance vectors.

The campaign layer does **not** assert that hardware executed the original logical instruction. It asks whether a target can perform the corresponding low-level ternary operation on values encountered in the workload.

### 9.1 v1 mappings

| Logical event | Subsystem parity operation |
| --- | --- |
| `LDI` | `register_load` of traced destination value |
| `MOV` | `register_load` of traced source value |
| `LD` | `register_load` of traced destination value |
| `NEG` | `negate` of traced pre-event operand |
| `ADD` | `add` of traced pre-event operands |
| `SUB` | `sub` of traced pre-event operands |
| `ADDI` | `add` using a fixed-width 12-trit immediate operand |

The `ADDI` mapping is explicitly subsystem-level and does not test instruction decoding.

`NOP`, `CMP`, `ST`, branches, `JMP`, and `HALT` do not emit v1 vectors because the current parity surface has no faithful equivalent for those complete semantics.

### 9.2 Campaign provenance

Each `TraceParityEntry` preserves event index, machine step, instruction index, logical operation, target register, before/after complete machine digests, mapping/rationale, and exact `ParityVector`.

Campaign construction walks the source trace's register-delta chain. Every `RegisterDelta.before` must agree with reconstructed state, and mapped vector results must equal the traced destination register after the event.

A campaign embeds the complete trace plus exact initial/final `td1.machine-state` checkpoints. Deserialization recomputes checkpoints and all entries; saved artifacts cannot redefine their mappings.

### 9.3 Campaign runs

`td1.parity-campaign-run` binds one exact campaign to one `td1.parity-report`.

Validation requires the report vector-set digest and ordered request vectors to equal the campaign. Passing a run proves only those advertised subsystem operations represented by the campaign vectors.

## 10. Parity wire adapter boundary

`td1.parity-wire` is a byte-oriented adapter protocol layered underneath the existing `ParityTransport` interface.

Wire v1 uses canonical UTF-8 JSON Lines with four message kinds:

- `capabilities_request`;
- `capabilities_response`;
- `parity_request`;
- `parity_response`.

The wire envelope wraps existing `ParityCapabilities`, `ParityRequest`, and `ParityResponse` payloads rather than duplicating their semantics.

The default frame ceiling is 65,536 bytes including the trailing LF. Frames must be canonical, single-line UTF-8 JSON ending in exactly one LF. Empty, malformed, noncanonical, oversized, CRLF, multi-line, or invalid-UTF-8 frames are rejected.

`JsonLineParityTransport` adapts a minimal `ParityLineIO` byte channel to `ParityTransport`. `ParityWireDevice` supplies a reference device-side dispatcher around an existing target, and `InMemoryParityLineIO` allows the complete byte codec to run in CI.

Capability exchange uses a fixed v1 correlation token; parity exchanges derive deterministic correlation from canonical request bytes. Host validation also requires session, sequence, and vector identity to match the original request.

The v1 bench telemetry conventions are `voltage_uv`, `settle_us`, `comparator_code`, `sample_count`, `board_revision`, and optional `temperature_millic`. These are metadata only and do not alter arithmetic pass/fail evaluation.

The wire protocol does not define connector pinout, baud rate, voltage thresholds, sample cadence, hysteresis, calibration, or instruction encoding.

## 11. Stream-backed line-I/O boundary

`StreamParityLineIO` implements `ParityLineIO` over ordinary binary streams while remaining below canonical wire semantics.

Its structural interfaces are intentionally small:

```text
BinaryByteReader.read(size) -> bytes
BinaryByteWriter.write(data) -> int | None
BinaryByteStream = reader + writer
```

The adapter may receive one duplex stream or separate reader/writer objects. It completes partial writes, buffers fragmented reads, preserves bytes from coalesced later frames, and enforces the existing parity-wire maximum frame size before unbounded buffering can occur.

It distinguishes empty EOF, partial-frame EOF, invalid stream return values, zero write progress, oversized lines, and underlying read/write/flush failures with adapter-specific exceptions.

`StreamParityStats` exposes deterministic bytes-read, bytes-written, frames-read, frames-written, and buffered-byte counters. It intentionally contains no wall-clock timestamps, throughput estimates, or latency semantics.

`StreamParityLineIO` does not parse JSON or validate canonical framing. `JsonLineParityTransport` / `decode_wire_frame()` continue to own those rules.

The preferred composition is:

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
binary UART / USB CDC / other stream later
```

See [`STREAM_LINE_IO.md`](STREAM_LINE_IO.md) and ADR 0017.

## 12. Wire transcripts and bench evidence

`td1.parity-wire-transcript` preserves the exact canonical line traffic observed at `ParityLineIO`.

Each `WireTranscriptRecord` contains:

- contiguous ordinal;
- `host_to_device` or `device_to_host` direction;
- exact UTF-8 frame text including LF;
- SHA-256 of the exact frame bytes;
- decoded wire kind;
- correlation ID;
- envelope digest.

Every saved frame is revalidated through `decode_wire_frame()`. Completed transcripts require alternating request/response pairs, matching correlations, and matching request/response message classes.

`RecordingParityLineIO` wraps any line channel, including `StreamParityLineIO`, and captures successful traffic without changing wire semantics. `ReplayParityLineIO` requires future host writes to match the saved request bytes exactly and returns the saved response bytes in order; replay must consume the complete transcript.

`transcript_for_report()` deterministically reconstructs the canonical wire conversation implied by a `td1.parity-report`. Capability-rejected vectors correctly produce no device exchange because they never reached `ParityTransport.exchange()`.

`td1.parity-bench-run` binds one exact `ParityCampaignRun` to the exact transcript implied by its saved report. `replay_bench_run()` reruns the campaign through the normal `JsonLineParityTransport` over transcript replay and requires the regenerated campaign run to match canonically.

Transcript SHA-256 values are integrity fingerprints, not hardware signatures. No normative wall-clock timestamp is included in transcript v1.

## 13. Relic timelines, morphs, and browser playback

`td1.relic-timeline` joins execution events to exact render/geometry frames. Frame zero is pre-execution state; each later frame corresponds to one logical event.

`td1.morph-plan` maps stable geometry changes to explicit presentation intent (`enter`, `exit`, `translate`, `reform`, `retag`). Corpus hints may constrain presentation but never define machine semantics or intermediate state.

The standalone browser player consumes exact timeline/morph payloads, verifies them, and renders geometry with the reference projection.

Its authority rules remain:

```text
endpoint_policy = hard-reconcile-authoritative-scene-after-transition/v1
unchanged_primitive_policy = no-animation-without-morph-descriptor/v1
state_interpolation_policy = forbidden/v1
```

Transient browser animation state is discarded at every completed transition and the exact target geometry scene is rebuilt.

## 14. Observer Continuity

Current groundwork includes timezone-aware UTC timestamp, WGS-84 geodetic -> ECEF conversion, UTC Julian Date, and explicitly approximate Earth Rotation Angle.

Precision navigation will require explicit time scales, Earth-orientation data, ephemerides, sensor covariance, and uncertainty contracts.

## 15. Provenance and determinism

Major provenance chains remain separate:

```text
source observation -> motif -> requirement -> implementation -> validation

State Weave -> OperandBindings -> logical instructions -> execution trace

Machine -> td1.machine-state -> restore Machine -> identical machine digest

execution trace -> td1.parity-campaign -> ParityTransport -> td1.parity-wire
                                           |                   |
                                           |                   v
                                           |          StreamParityLineIO
                                           |                   |
                                           |                   v
                                           |                 target
                                           |                   |
                                           |                   v
                                           |          exact wire transcript
                                           |                   |
                                           v                   v
                                    parity report ------> parity bench run
                                           |
                                           v
                                    parity campaign run

execution trace -> render -> geometry -> timeline/morphs -> browser -> exact endpoint
```

Reference artifacts expose canonical serialization and digests where applicable. Those digests support regression, replay, integrity, differential testing, and emulator/hardware comparison. They are not authorship signatures unless explicitly stated otherwise.

## 16. Physical parity boundary

Current parity operations are:

- `trit_hold`;
- `register_load`;
- `negate`;
- `add`;
- `sub`.

Targets advertise supported operations and maximum width before testing. The harness distinguishes unsupported capability, fault, timeout, protocol error, value mismatch, and observed-state digest mismatch.

The v1 wire gives those transport-neutral semantics a deterministic line-framed byte representation. The stream adapter gives that line interface a concrete binary-stream implementation without choosing pyserial or physical link parameters. The transcript layer can preserve and replay the resulting exact conversation without changing those semantics.

A physical subsystem may replace an emulated counterpart only after conformance demonstrates parity against the reference model. A transcript strengthens the audit trail; stream statistics help debug transport; neither lowers that bar.

## 17. Operating modes

### Engineering Mode

Human-readable diagnostics include machine/checkpoint digests, execution/campaign provenance, semantic lowering, corpus provenance, geometry/timeline/morph identity, player verification, wire/telemetry/transcript diagnostics, stream adapter counters, bench-bundle identity, and hardware parity status.

### Relic Mode

The same underlying machine-derived state expressed with native TD-1 geometry and interaction semantics. The Relic surface never becomes a second machine-state authority.

### Corpus Mode

Traceability view explaining which versioned observations contributed to interface requirements, geometry rules, or eligible temporal presentation hints.

## 18. Primary engineering rule

**No decorative weirdness, no semantic hand-waving, no persistence exceptionalism, no renderer exceptionalism, no playback exceptionalism, no campaign exceptionalism, no wire exceptionalism, no stream-adapter exceptionalism, no transcript exceptionalism, and no hardware exceptionalism.**

Every glyph, semantic mapping, checkpoint, execution transition, campaign vector, wire frame, stream adapter claim, transcript record, visible primitive, browser animation, or claimed hardware capability must map to explicit state, a measured event, a documented engineering convention, a versioned rule, or a passing conformance record.
