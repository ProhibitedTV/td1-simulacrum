# ADR 0007: Separate semantic identity from executable operand binding

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1's native interface uses State Weaves to identify semantic operations. A State Weave such as `MEMORY:0` can express the class of operation without specifying which register receives data, which register supplies an address base, or which offset is used.

If register and address choices are hidden inside semantic glyph identity, the native interface becomes ambiguous and future compiler changes can silently alter machine behavior. If every semantic root is forced into the current 15-op ISA, the project also risks inventing misleading one-instruction translations for concepts such as `TIME`, `OBSERVER`, `REFERENCE`, or `COGNITION`.

Issue #2 should not freeze physical instruction words until this compiler boundary is explicit.

## Decision

TD-1 will treat State Weave identity and executable machine operands as separate versioned concerns.

A `StateWeave` describes semantic identity. `OperandBindings` provides concrete machine resources. `lower_state_weave()` combines them into a deterministic `td1.semantic-lowering` artifact containing:

- canonical source weave;
- project-defined semantic action;
- exact logical instruction sequence;
- explicit bindings;
- register read/write metadata;
- memory-effect metadata;
- deterministic canonical serialization and digest.

The v1 compiler supports only a small set of deliberately unambiguous project-defined conventions:

- `EXECUTION:-` -> `HALT`;
- `TRANSFORM:-` -> `NEG`;
- `STATE:0` -> `CMP`;
- `MEMORY:0` -> `LD`;
- `MEMORY:+` -> `ST`.

All other State Weaves remain explicitly unsupported until a real semantic contract exists.

These mappings are TD-1 engineering conventions. They are not claimed translations of the Veilbreak corpus.

## Consequences

Positive:

- native semantic identity no longer hides register/address choices;
- unsupported semantics fail visibly instead of receiving fake implementations;
- compiler artifacts are deterministic and auditable;
- saved lowerings can be recompiled and checked for semantic drift;
- future multi-instruction lowering can evolve without changing State Weave identity;
- Issue #2 can evaluate physical encoding against an actual compiler boundary.

Costs:

- the initial executable State Weave surface is intentionally small;
- callers must supply typed operand bindings;
- future semantic additions require explicit compiler design rather than ad-hoc opcode aliases;
- some native interface operations will remain representational until supporting subsystems exist.

## Non-decision

This ADR does not freeze physical instruction encoding, define a complete native programming language, assign corpus-derived semantics to every root, allocate compiler temporaries, define Observer Continuity opcodes, or specify a hardware transport.
