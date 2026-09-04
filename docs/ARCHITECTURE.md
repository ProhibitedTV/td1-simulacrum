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
              +-------------------+-------------------+
              |                                       |
              v                                       v
      td1.machine-state                      td1.execution-trace
                                                      |
                                                      v
                                            td1.parity-campaign
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
                              +-----------------------+-----------------------+
                              |                                               |
                              v                                               v
                     exact wire transcript                           parity response
                              |                                               |
                              +-----------------------+-----------------------+
                                                      |
                                                      v
                                             conformance report
                                                      |
                                                      v
                                         td1.parity-campaign-run
                                                      |
                                                      v
                                           td1.parity-bench-run

reference machine -> render state -> native geometry -> Relic playback
```

Authority rules:

1. logical machine semantics are normative;
2. `td1.machine-state` persists execution truth only;
3. execution traces record exact logical transitions without freezing physical encoding;
4. parity campaigns derive only subsystem operations the parity surface can represent faithfully;
5. `td1.parity-wire` transports existing parity contracts but does not redefine them;
6. `StreamParityLineIO` moves/buffers bytes and does not interpret arithmetic;
7. `PySerialByteStream` is optional deployment plumbing and does not create machine semantics;
8. serial port, baud rate, and host timeout values are deployment configuration, not machine state;
9. wire transcripts preserve exact transport evidence but are not arithmetic truth or hardware signatures;
10. bench-run bundles bind one report to one exact transcript without claiming device authorship;
11. rendering and browser playback remain downstream of machine truth;
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

No amount of host transport maturity substitutes for those measurements.

## 4. Machine-state persistence

`td1.machine-state` is the renderer-independent persistence boundary for logical execution state.

It records architecture invariants, instruction pointer, condition state, halted state, step count, all registers, sparse nonzero memory, and the complete machine digest.

It excludes glyphs, Observer Continuity, geometry, corpus provenance, browser state, parity transport, serial configuration, transcripts, and physical instruction encoding.

Checkpoint restore must reconstruct a `Machine` with the claimed complete digest. Resume tests require the same final state as uninterrupted execution.

## 5. Execution traces and parity campaigns

`td1.execution-trace` records one exact transition per executed logical instruction, including before/after machine digests and register/memory deltas.

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

## 6. Parity semantics

Current parity operations are:

- `trit_hold`;
- `register_load`;
- `negate`;
- `add`;
- `sub`.

Targets advertise supported operations and maximum width. Unsupported vectors are capability-gated rather than misclassified as device faults.

Responses distinguish `ok`, `unsupported`, `fault`, `timeout`, and `error` at the parity-protocol level.

Host adapter failures such as serial timeouts are separate from target `ParityStatus` values.

## 7. Canonical parity wire

`td1.parity-wire` is the deterministic byte-oriented adapter protocol underneath `ParityTransport`.

Wire v1 message kinds:

- `capabilities_request`;
- `capabilities_response`;
- `parity_request`;
- `parity_response`.

Each frame is canonical UTF-8 JSON followed by exactly one LF. The default maximum frame size is 65,536 bytes including that LF.

The envelope wraps existing `ParityCapabilities`, `ParityRequest`, and `ParityResponse` payloads. It does not duplicate their semantics.

`JsonLineParityTransport` adapts `ParityLineIO` to the existing parity interface. `ParityWireDevice` is the Python reference device-side dispatcher used in CI.

## 8. Stream-backed line I/O

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

## 9. Optional serial deployment adapter

v0.18 adds `PySerialByteStream` and `SerialConfig` as an optional deployment layer beneath `StreamParityLineIO`.

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

`SerialConfig` requires explicit:

- port;
- baud rate;
- host read timeout;
- host write timeout.

TD-1 defines no default baud rate and performs no automatic port discovery.

Finite serial read timeouts mean a zero-byte pyserial read is classified as `ParitySerialReadTimeoutError`, not generic EOF.

The serial adapter also distinguishes write timeout, underlying serial read/write failure, closed-port access, and close failure.

`td1-parity serial-run` uses the ordinary campaign/wire/recording/stream stack. Deployment settings and stream counters may be displayed in its CLI summary but are not silently copied into canonical parity artifacts.

See [`SERIAL_ADAPTER.md`](SERIAL_ADAPTER.md) and ADR 0018.

## 10. Wire transcripts and bench evidence

`td1.parity-wire-transcript` records exact canonical frames at the `ParityLineIO` boundary.

Each record preserves:

- contiguous ordinal;
- host/device direction;
- exact frame text including LF;
- frame SHA-256;
- decoded message kind;
- correlation ID;
- envelope digest.

`RecordingParityLineIO` can wrap in-memory, generic stream, or serial-backed line I/O without changing transcript schema.

`ReplayParityLineIO` requires exact host request bytes and returns exact recorded device bytes. Replay must consume the full transcript.

`td1.parity-bench-run` binds one campaign run to the exact transcript implied by its saved report. `replay_bench_run()` must regenerate the same canonical campaign run.

Transcript hashes are integrity fingerprints, not cryptographic hardware-authorship proof.

## 11. Bench telemetry

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

## 12. Semantic and native representation layer

TD-1's native operator model uses semantic roots rather than alphabetic text.

Current roots include:

`OBSERVER`, `ORIGIN`, `TIME`, `REFERENCE`, `MOTION`, `MEMORY`, `LINK`, `STATE`, `FRAME`, `AXIS`, `SIGNAL`, `COGNITION`, `EXECUTION`, `TRANSFORM`, `ISOLATION`, `DOMAIN`.

Balanced-ternary modifiers provide directional semantics:

- `-`: reverse / remove / contract / deny;
- `0`: inspect / hold / neutral / current;
- `+`: forward / acquire / expand / allow.

`OperandBindings` supplies concrete registers/addresses separately from State Weave identity. Unsupported weaves fail explicitly rather than receiving invented executable meanings.

A 12-trit word partitions into four reversible 3-trit microglyph cells (`3^3 = 27` states each).

## 13. Rendering authority

`td1.render-state` is a deterministic projection from machine state plus allowed presentation inputs.

`td1.geometry-scene` uses integer axial triangular coordinates with discrete depth.

SVG and browser renderers consume geometry. They do not own logical state.

Relic timelines join exact execution events to exact geometry frames. Morph plans may animate between authoritative endpoints but cannot invent endpoint state.

## 14. Observer Continuity

Current groundwork includes:

- timezone-aware UTC timestamps;
- WGS-84 geodetic -> ECEF conversion;
- UTC Julian Date;
- explicitly approximate Earth Rotation Angle.

Precision navigation remains future work requiring explicit time scales, Earth-orientation data, ephemerides, sensor covariance, and uncertainty contracts.

## 15. Deterministic provenance chains

Major chains remain separable:

```text
source observation -> motif -> requirement -> implementation -> validation

State Weave -> OperandBindings -> logical instructions -> execution trace

Machine -> td1.machine-state -> restore Machine -> identical digest

execution trace -> parity campaign -> parity wire -> stream/serial adapter -> target
                                                    |
                                                    v
                                             exact transcript
                                                    |
                                                    v
                                             conformance report
                                                    |
                                                    v
                                              bench-run replay

execution trace -> render state -> geometry -> timeline/morph -> browser endpoint
```

Digests support integrity, replay, and regression. They are not authorship signatures unless explicitly stated otherwise.

## 16. Physical replacement gate

A physical subsystem may replace its emulated counterpart only after deterministic conformance against the reference model.

A successful serial connection is not enough. A valid transcript is not enough. A visually convincing board is not enough.

Hardware earns authority through parity.

## 17. Primary engineering rule

**No decorative weirdness, no semantic hand-waving, no persistence exceptionalism, no renderer exceptionalism, no campaign exceptionalism, no wire exceptionalism, no stream/serial exceptionalism, no transcript exceptionalism, and no hardware exceptionalism.**

Every claimed behavior must map to explicit state, a measured event, a documented engineering convention, a versioned rule, or a passing conformance record.
