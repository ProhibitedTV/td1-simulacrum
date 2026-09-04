# Stream-backed Parity Line I/O

## Purpose

`StreamParityLineIO` is the concrete host adapter beneath `td1.parity-wire` that can sit on ordinary binary byte streams.

It allows UART, USB CDC, socket, pipe, file-like, or injected test transports to carry the existing canonical parity wire without making a specific serial library part of TD-1 semantics.

```text
ParityCampaign
      |
      v
JsonLineParityTransport
      |
      v
RecordingParityLineIO     optional evidence wrapper
      |
      v
StreamParityLineIO
      |
      v
binary reader / writer
      |
      +------> PySerialByteStream -> optional pyserial -> UART / USB CDC
      |
      +------> scripted/test stream
```

The stream adapter owns byte movement and buffering. `decode_wire_frame()` remains the authority for canonical JSON Lines framing and parity-wire semantics.

## Binary stream surface

The adapter defines tiny structural protocols:

```text
BinaryByteReader.read(size) -> bytes
BinaryByteWriter.write(data) -> int | None
BinaryByteStream = reader + writer
```

A `StreamParityLineIO` may receive one duplex stream or separate reader/writer objects.

The core package does not require pyserial. v0.18 adds an optional serial wrapper that presents the same binary stream behavior without changing this contract.

## Writes

`write_line()` sends the exact supplied frame bytes and supports partial writes.

The adapter loops until the entire frame has been accepted by the writer. It rejects:

- non-byte frames;
- empty frames;
- frames above the configured maximum;
- non-integer write results;
- zero/negative progress;
- a write count larger than the requested slice;
- underlying write failures;
- optional `flush()` failures when a writer exposes `flush()`.

Adapter-specific `ParityStreamError` subclasses raised by a lower stream are preserved rather than wrapped into generic error text. This allows the optional serial layer to retain explicit timeout/closed-port diagnostics.

The adapter intentionally does not parse or canonicalize outgoing JSON. That remains the responsibility of the parity-wire layer above it.

## Reads

`read_line()` buffers binary chunks until exactly one LF-terminated line is available.

It supports both fragmented and coalesced reads:

```text
read #1: {"sche
read #2: ma":...
read #3: }\n{"next"
```

The first returned frame ends at the first LF. Remaining bytes stay buffered for the next call.

The existing wire maximum-frame ceiling is enforced while buffering. An unterminated line that reaches the maximum cannot become a legal frame because a legal frame must still contain its terminating LF, so it is rejected before buffering can grow without bound.

## EOF and I/O failure classes

The generic adapter distinguishes:

- `ParityStreamEmptyEOFError`: EOF before any byte of the next line;
- `ParityStreamPartialEOFError`: EOF after a partial unterminated line;
- `ParityStreamFrameTooLargeError`: incoming line cannot fit under the configured ceiling;
- `ParityStreamReadError`: invalid read result or underlying read failure;
- `ParityStreamWriteError`: invalid write progress or underlying write/flush failure.

All derive from `ParityStreamError`.

Lower adapters may provide more specific subclasses. v0.18 serial integration uses this to distinguish serial read timeout, serial write timeout, closed-port access, and serial I/O failures.

These are host adapter failures, not ternary arithmetic outcomes and not `ParityStatus` values.

## Deterministic statistics

`StreamParityStats` reports:

- bytes read;
- bytes written;
- frames read;
- frames written;
- currently buffered unread bytes.

No wall-clock timestamp, throughput calculation, or latency measurement is included. The counters describe adapter activity deterministically. Actual device settling/timing measurements remain parity response telemetry.

## Transcript composition

The stream adapter is intentionally below the existing recording layer:

```text
JsonLineParityTransport
        |
        v
RecordingParityLineIO
        |
        v
StreamParityLineIO
```

Therefore the existing `td1.parity-wire-transcript` and `td1.parity-bench-run` schemas require no changes when the in-memory line channel is replaced with a real stream.

CI proves a complete trace-derived campaign through a deliberately fragmenting scripted device stream, records the resulting transcript, creates a bench bundle, and replays that bundle through the ordinary wire transport.

## Optional pyserial live adapter

v0.18 adds `PySerialByteStream`, which wraps a configured pyserial port and presents the existing binary stream surface.

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

The serial package is an optional extra. Serial configuration requires explicit port, baud rate, read timeout, and write timeout values.

A finite serial read timeout means pyserial's zero-byte read is classified by `PySerialByteStream` as a serial timeout before `StreamParityLineIO` sees it. This prevents a live serial timeout from being mislabeled as generic EOF.

Port names, baud rate, and host timeout settings are deployment state only. They may appear in CLI diagnostics but do not silently enter canonical parity, transcript, or bench-run artifacts.

See [`SERIAL_ADAPTER.md`](SERIAL_ADAPTER.md) and ADR 0018.

## Non-goals

The stream layer does not define:

- COM/tty auto-discovery;
- a default baud rate;
- USB VID/PID;
- connector/pinout;
- retry/reconnect policy;
- analog thresholds;
- electrical acceptance limits;
- hardware instruction encoding.

## Design rule

**Move exact bytes reliably; leave meaning to the layers that already own it.**
