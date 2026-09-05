# ADR 0022 — Canonical wire payloads must survive parsing unchanged

## Status

Accepted for v0.22 pre-alpha.

## Context

`td1.parity-wire` v1 already requires every envelope to use byte-for-byte canonical JSON Lines framing. That protects framing, correlation, transcript replay, and byte-level evidence from serializer ambiguity.

The audit after v0.21 found a separate ambiguity inside the envelope. Several parity-schema loaders intentionally construct typed objects with operations such as `int()`, `str()`, default insertion, sorting, and deduplication. A received payload such as `{"sequence":"0"}` can therefore parse into the same in-memory value as canonical `{"sequence":0}` even though the sender did not follow the schema. Likewise, omitted default fields or non-canonical list ordering can be normalized before the host notices.

That is unacceptable at the live hardware boundary. A transcript should not be considered a canonical TD-1 protocol conversation merely because the outer envelope bytes are canonical while nested parity values depend on receiver coercion.

## Decision

Wire v1 keeps its existing schema and byte encoding. After parsing each nested parity object, the wire adapter must require the received payload to equal the object's canonical `as_dict()` representation exactly, including JSON value types.

The comparison is deliberately type-strict. In particular, Python equality such as `True == 1` must not make a boolean interchangeable with an integer.

The device-side dispatcher applies this rule to inbound `ParityRequest` payloads before handing them to a target.

The host-side transport applies this rule to inbound `ParityCapabilities` and `ParityResponse` payloads before caching or returning them.

Canonical payloads emitted by the existing reference implementation remain byte-identical. This is parser hardening, not a protocol redesign and not a wire-schema version bump.

## Consequences

The live boundary now rejects payloads that rely on:

- numeric strings being converted to integers;
- booleans standing in for integers;
- omitted fields being restored by defaults;
- duplicate or reordered capability lists being silently normalized;
- other typed-model normalization that changes the received JSON representation.

This makes transcript bytes a stronger engineering receipt: if a frame passes wire validation, its nested parity contract was already canonical before the receiver interpreted it.

The broader repository still contains older persisted-artifact loaders that use coercive parsing. They are downstream/offline surfaces and should receive a separate hardening pass rather than being silently folded into this wire decision.

## Rejected alternatives

### Rely on outer canonical JSON only

Rejected. Canonical key order and whitespace do not enforce schema value types or canonical nested representations.

### Make every parity loader globally strict in this revision

Rejected for v0.22. That would broaden the change across saved artifact compatibility at the same time as hardening the first physical I/O boundary. The live wire path gets the narrow, high-value fix first.

### Bump wire schema to v2

Rejected. Canonical senders already satisfy the strengthened rule and no on-wire field or semantic meaning changes.

## Authority boundary

This decision changes neither balanced-ternary arithmetic nor parity pass/fail semantics. It does not define analog thresholds, transport timing, physical instruction encoding, or Issue #2.

**Canonical transport bytes may not hide non-canonical parity schema values.**
