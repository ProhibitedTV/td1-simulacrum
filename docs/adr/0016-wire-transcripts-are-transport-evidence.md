# ADR 0016: Wire transcripts are transport evidence

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 now has deterministic parity campaigns and a canonical parity wire protocol. Once real hardware is attached, a conformance report alone proves what requests and responses were evaluated, but it does not preserve the exact byte conversation that crossed the adapter boundary.

First-hardware bring-up benefits from keeping exact transport receipts that can be inspected and replayed later. That evidence must remain subordinate to machine semantics and parity evaluation rather than becoming another authority layer.

## Decision

Introduce versioned `td1.parity-wire-transcript` v1 and `td1.parity-bench-run` v1.

A transcript records every successful line write/read as an ordered `WireTranscriptRecord` containing:

- contiguous ordinal;
- host/device direction;
- exact canonical UTF-8 frame text including LF;
- SHA-256 of exact frame bytes;
- decoded wire kind;
- correlation ID;
- envelope digest.

Every stored frame is revalidated through the existing v1 wire decoder. Completed transcripts require alternating host request/device response pairs and matching request/response kinds and correlation IDs.

No normative wall-clock timestamp is stored in transcript v1. Device timing remains optional telemetry until measured timing requirements exist.

`RecordingParityLineIO` wraps any `ParityLineIO` and records exact successful traffic without modifying parity semantics.

`ReplayParityLineIO` requires live host writes to match the next saved request bytes exactly and returns saved response bytes in order. Replay must consume the entire transcript.

`td1.parity-bench-run` binds one exact `ParityCampaignRun` to one exact transcript. Validation reconstructs the canonical wire traffic implied by the saved conformance report and requires exact equality with the transcript.

## Consequences

### Positive

- Real bench sessions can produce deterministic byte-level receipts.
- Hardware conversations can be reproduced without the original device.
- Report telemetry is preserved as exact response bytes.
- A transcript from a different target/session/vector sequence cannot be silently attached to a campaign run.
- CI can validate record/replay behavior before any serial adapter exists.

### Costs

- Bench bundles duplicate information already present in parity reports.
- JSON transcript artifacts are intentionally verbose.
- Exact replay is brittle by design: any request-byte change invalidates replay compatibility.

These costs are acceptable because the goal is auditability and regression evidence, not compact storage.

## Rejected alternatives

### Record only decoded request/response objects

Rejected because that would lose proof of the exact canonical bytes seen at the line boundary.

### Add timestamps to every normative record

Rejected because wall-clock timing would make otherwise identical transcripts nondeterministic. Timing belongs in measured telemetry or a later versioned timing contract.

### Treat transcript SHA-256 values as device signatures

Rejected. SHA-256 here is an integrity fingerprint only. Authenticated hardware identity would require a separate cryptographic attestation design.

### Let replay accept semantically equivalent JSON

Rejected. The wire contract is canonical; replay should require exact request bytes so framing regressions remain visible.

## Governing rule

**Transport evidence may prove what crossed the boundary. It may not redefine what the machine means.**
