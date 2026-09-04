# ADR-0002: Do not freeze the physical 12-trit instruction encoding yet

- Status: Accepted
- Date: 2026-09-04

## Context

The logical ISA exists, but the final balance among opcode space, register fields, immediates, State Weave lowering, and physical implementation is unresolved.

## Decision

Freeze logical instruction semantics before assigning permanent physical ternary opcodes.

The target format remains 3 trits opcode + 2 trits register A + 2 trits register B + 5 trits immediate/relative, but the actual encoding table is deferred.

## Consequences

- assembler source targets logical instructions rather than raw machine words;
- hardware design is protected from premature opcode commitments;
- a future encoding specification must be separately versioned and tested.
