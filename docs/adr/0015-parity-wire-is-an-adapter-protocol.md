# ADR 0015: Parity wire is an adapter protocol

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 now has a transport-neutral hardware parity contract and trace-derived parity campaigns, but first physical bench integration still needs an actual byte-oriented link between the host harness and a trit/register adapter.

Choosing UART, USB CDC, or another concrete library directly inside parity semantics would couple the conformance model to one transport implementation. It would also create a risk that framing details, telemetry, or future serial behavior quietly become part of the logical machine definition.

The first bench protocol needs to be deterministic enough for CI and hardware debugging while remaining subordinate to the existing `ParityTransport`, `ParityCapabilities`, `ParityRequest`, `ParityResponse`, and conformance report contracts.

## Decision

Introduce versioned `td1.parity-wire` v1 as a canonical JSON Lines envelope around the existing parity payload schemas.

The wire layer owns only:

- canonical UTF-8 JSON Lines framing;
- message kind;
- request/response correlation;
- frame-size limits;
- host/device envelope validation;
- a minimal synchronous byte-line I/O boundary;
- optional bench telemetry naming conventions.

It does **not** redefine:

- arithmetic results;
- parity vector semantics;
- capability negotiation semantics;
- pass/fail evaluation;
- machine state;
- physical instruction encoding.

`JsonLineParityTransport` adapts `ParityLineIO` to the existing `ParityTransport` protocol. `ParityWireDevice` provides a deterministic reference dispatcher around any existing parity target. `InMemoryParityLineIO` allows CI to exercise the complete codec and dispatcher path without serial hardware.

Wire v1 uses a fixed 65,536-byte maximum frame by default and requires canonical JSON followed by exactly one LF. Noncanonical, malformed, oversized, CRLF, multi-line, or invalid-UTF-8 frames are rejected.

Capability requests use a fixed v1 correlation token. Parity exchange correlation IDs are derived deterministically from the canonical request digest, and host-side validation additionally checks parity session, sequence, and vector identity.

The initial bench telemetry vocabulary is:

- `voltage_uv`;
- `settle_us`;
- `comparator_code`;
- `sample_count`;
- `board_revision`;
- optional `temperature_millic`.

These are metadata only in wire v1. They cannot alter arithmetic conformance results.

## Consequences

### Positive

- The exact bytes crossing the first bench link are deterministic and testable in CI.
- UART/USB/other adapters can be added without modifying parity semantics.
- Physical telemetry can travel with a conformance response while remaining explicitly non-normative for arithmetic.
- The loopback target can validate the wire stack before real boards exist.
- First-hardware debugging has a small, inspectable text protocol rather than an opaque binary format.

### Costs

- JSON Lines is not bandwidth-optimal.
- Canonical serialization rules must be reproduced correctly by non-Python firmware.
- Real serial transports will still require timeouts, buffering, reconnect behavior, and device discovery in later revisions.

These costs are acceptable for the first bench adapter, where auditability and deterministic diagnosis matter more than throughput.

## Rejected alternatives

### Make pyserial part of the parity core

Rejected because the semantic interface should not depend on one host transport library.

### Define a compact binary protocol immediately

Rejected because early hardware bring-up benefits from human-readable, deterministic frames and because the parity schema is still pre-alpha.

### Put voltage thresholds into the wire protocol

Rejected because analog acceptance criteria belong to measured hardware specifications and future versioned acceptance contracts, not message framing.

### Freeze physical instruction encoding while defining the wire

Rejected. The wire transports subsystem parity requests only. Issue #2 remains deferred until hardware measurements and encoding review justify a physical instruction format.

## Governing rule

**The wire transports parity truth; it does not define parity truth.**
