# ADR 0017: Stream line I/O is a host adapter

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 has transport-neutral parity semantics, canonical parity-wire framing, and deterministic wire transcripts, but the host side still needs a concrete bridge from line frames to the binary stream interfaces exposed by eventual UART/USB-CDC libraries.

Adding pyserial directly to parity or wire semantics would prematurely couple the architecture to one library and to bench choices that have not yet been made. The adapter also needs to handle ordinary stream realities such as partial writes, fragmented reads, coalesced frames, EOF, and bounded buffering.

## Decision

Introduce `StreamParityLineIO` as a concrete implementation of the existing `ParityLineIO` boundary over minimal readable/writable binary stream protocols.

The adapter owns only:

- complete delivery across partial writes;
- optional writer flushing when available;
- chunked reads and LF-oriented buffering;
- preservation of bytes following the first complete frame;
- enforcement of the existing maximum-frame ceiling during buffering;
- explicit stream/EOF/progress error classes;
- deterministic byte/frame/buffer counters.

It does not parse, canonicalize, or reinterpret parity-wire JSON. `JsonLineParityTransport`, `encode_wire_frame()`, and `decode_wire_frame()` continue to own wire semantics.

The adapter contains no wall-clock timing fields. Measured hardware timing remains optional response telemetry until a separate measured-acceptance contract exists.

`RecordingParityLineIO` remains above the stream adapter. Existing transcript and bench-run schemas therefore require no migration when a real stream replaces the in-memory line channel.

## Consequences

### Positive

- First serial-class hardware can reuse the exact existing parity/wire/transcript stack.
- Partial and coalesced stream behavior is deterministic and covered by tests before hardware exists.
- No pyserial dependency is imposed on the reference package.
- A later UART/USB implementation can remain a thin configuration/discovery layer.
- Stream statistics aid debugging without contaminating normative artifacts with timestamps.

### Costs

- The adapter is synchronous and does not define timeout/reconnect policy.
- A concrete serial library must still be chosen and configured later.
- Flush behavior depends on whether the supplied writer exposes a callable `flush()`.

These are appropriate limits for a pre-hardware adapter boundary.

## Rejected alternatives

### Add pyserial as a required dependency now

Rejected because port naming, baud rate, timeout behavior, and actual bench connectivity have not been selected.

### Put stream buffering inside `JsonLineParityTransport`

Rejected because JSON/wire semantics and byte-stream mechanics are separate responsibilities.

### Record timestamps/latency in stream statistics

Rejected because those values would be nondeterministic host observations and could be confused with measured device timing. Hardware timing belongs in explicit telemetry/acceptance contracts.

### Let the stream adapter repair malformed framing

Rejected. The adapter moves bytes; the canonical wire decoder decides whether those bytes are a valid TD-1 wire frame.

## Governing rule

**The stream adapter moves exact bytes. It does not decide what those bytes mean.**
