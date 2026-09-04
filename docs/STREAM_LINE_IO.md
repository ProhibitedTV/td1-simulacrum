# Stream-backed Parity Line I/O

## Purpose

`StreamParityLineIO` is the first concrete host adapter beneath `td1.parity-wire` that can sit on ordinary binary byte streams.

It exists so a future UART, USB CDC, socket, pipe, or file-like transport can carry the existing canonical parity wire without importing a specific serial library into TD-1 semantics.

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
      v
future UART / USB CDC / other byte stream
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

No pyserial dependency is required. A later serial integration only needs to present compatible binary read/write methods.

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

The adapter distinguishes:

- `ParityStreamEmptyEOFError`: EOF before any byte of the next line;
- `ParityStreamPartialEOFError`: EOF after a partial unterminated line;
- `ParityStreamFrameTooLargeError`: incoming line cannot fit under the configured ceiling;
- `ParityStreamReadError`: invalid read result or underlying read failure;
- `ParityStreamWriteError`: invalid write progress or underlying write/flush failure.

All derive from `ParityStreamError`.

These are adapter failures, not ternary arithmetic outcomes and not `ParityStatus` values.

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

## Future pyserial integration

A future serial adapter may be as small as constructing a configured serial object and passing it to `StreamParityLineIO` if its binary read/write behavior satisfies the contract.

That later integration may choose:

- port/device discovery;
- baud rate;
- read/write timeouts;
- USB identifiers;
- reconnect behavior;
- operating-system-specific setup.

Those are deployment/bench choices, not changes to the parity wire or machine semantics.

## Non-goals

This revision does not define:

- a serial package dependency;
- COM/tty device naming;
- baud rate;
- USB VID/PID;
- connector/pinout;
- timeout policy;
- retry/reconnect policy;
- analog thresholds;
- electrical acceptance limits;
- hardware instruction encoding.

## Design rule

**Move exact bytes reliably; leave meaning to the layers that already own it.**
