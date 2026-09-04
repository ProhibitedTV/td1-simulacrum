# Deterministic Render-State Contract

## Purpose

The renderer must never become a second source of truth.

`td1.render-state` is the versioned boundary between TD-1 machine state and any visual presentation. Engineering Mode and Relic Mode are projections of the same immutable source object.

If the two modes disagree about the machine, the renderer is wrong.

## Schema v1

Schema identifier:

```text
td1.render-state
```

Version:

```text
1
```

The state contains:

- complete register words in ternary and reversible 27-state microglyph IDs;
- instruction pointer, condition state, halt state, and step count;
- a digest of full machine state;
- sparse non-zero memory plus fixed memory size, sufficient to reconstruct all memory;
- optional State Weave state;
- optional Observer Continuity state;
- the set of active render planes.

The schema is deterministic and round-trippable. Loading a serialized state validates redundant ternary/glyph data and reconstructs the machine to verify its original full-state digest.

## Render planes

Stable conceptual planes are:

| ID | Plane | Meaning |
|---:|---|---|
| 0 | carrier | persistent substrate / context plane |
| 1 | machine | registers, memory, control state |
| 2 | semantic | active State Weave / semantic state |
| 3 | observer | Observer Continuity state |

The existence of a plane is state-driven. A semantic plane is not active when no State Weave exists. An observer plane is not active when no observer state exists.

A renderer may choose perspective, spacing, line width, typography in Engineering Mode, or geometry in Relic Mode, but it may not invent an active state merely to create motion.

## Engineering projection

Engineering Mode exposes human-readable diagnostics:

- `R0..R8`;
- ternary words;
- decimal values;
- microglyph IDs;
- sparse memory addresses and values;
- canonical State Weave text and semantic IR;
- quantized observer quantities.

It exists for debugging, validation, hardware parity, and review.

## Relic projection

Relic Mode removes human semantic labels from the state payload where practical:

- register words become microglyph ID sequences;
- semantic roots become stable numeric root IDs;
- modifiers remain ternary `-1 / 0 / +1`;
- instruction pointer and step state are represented through microglyph IDs;
- active planes use stable numeric IDs.

The JSON field names are an implementation transport and are not intended to be visible on the physical/native interface.

The important rule is that Relic Mode contains no alternative machine truth. It carries the same `source_digest` as Engineering Mode.

## Observer quantization

Floating-point formatting must not become part of renderer parity. Schema v1 therefore quantizes Observer Continuity values into scaled integers:

- latitude / longitude: nanodegrees;
- altitude: micrometers;
- ECEF position: millimeters;
- Julian Date: microdays;
- approximate Earth Rotation Angle: nanoradians.

These scales are a renderer contract, not a claim of physical measurement accuracy. Precision and uncertainty are governed by the Observer Continuity subsystem.

Changing scale factors requires a schema version bump.

## Microglyph contract

The current microglyph layer maps each 3-trit cell reversibly into `G00..G26`.

This layer defines **identity**, not final shape.

Corpus-derived geometry may later determine how a particular ID is drawn, morphs, nests, or participates in a State Weave. Any such geometry must preserve the reversible state mapping.

## Corpus-derived versus aesthetic

The renderer must distinguish:

### Corpus-derived

Properties justified by versioned phenomenology requirements, such as a future decision to use:

- depth hierarchy;
- multiscale structure;
- lattice context;
- braiding / intertwining;
- morphing / flipping;
- embedded microglyph fields.

These require provenance traces.

### Computationally derived

Properties directly required by TD-1 state:

- glyph identity;
- active plane membership;
- ternary modifier state;
- register/memory contents;
- observer-derived transformations;
- semantic composition.

### Aesthetic

Choices left free by the first two categories:

- exact stroke thickness;
- presentation color;
- material finish;
- non-semantic spacing;
- camera framing.

Aesthetic choices may not masquerade as corpus findings.

## Golden fixture

`tests/fixtures/render_state_v1.json` is the first schema-v1 golden fixture.

It exists to detect accidental contract drift. Any intentional modification that changes the fixture or its digest requires explicit review and, if semantics change, a schema-version decision.

## CLI

Engineering projection:

```bash
td1-sim render examples/sum.td1 --mode engineering
```

Relic projection:

```bash
td1-sim render examples/sum.td1 --mode relic
```

Both must report the same source render-state digest for the same execution.

## Rule

> The renderer may decide how truth is shown. It may not decide what truth is.
