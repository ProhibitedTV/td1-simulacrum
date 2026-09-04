# Relic Execution Timeline

## Purpose

`td1.relic-timeline` is the first end-to-end playback contract for TD-1.

It joins the already normative layers:

```text
logical execution
    -> td1.execution-trace
        -> td1.render-state
            -> td1.geometry-scene
                -> td1.geometry-delta
                    -> td1.relic-timeline
                        -> SVG / future frontend
```

The timeline records **discrete truth-bearing states**. It does not define how long a frame remains visible, how a primitive eases between positions, how a camera moves, what sound is played, or what visual persistence is applied.

> Playback consumes state transitions. It does not create them.

## Schema

```text
td1.relic-timeline / v1
```

A timeline contains:

- the logical program digest;
- the exact execution-trace digest used as its machine-transition authority;
- frame 0 representing the initial machine state before any instruction executes;
- exactly one later frame for each execution event;
- the complete validated `td1.render-state` for every frame;
- the complete deterministic `td1.geometry-scene` for every frame;
- machine/render/scene digests for explicit auditability;
- instruction/event identity for every noninitial frame;
- one deterministically recomputed `td1.geometry-delta` from each prior scene.

For a trace containing `N` logical execution events, the timeline contains exactly `N + 1` frames.

## Frame zero

Frame zero is special.

It represents the exact machine, semantic, observer, and geometry state immediately before the first logical instruction. It does not claim an event or geometry delta.

That gives playback a real origin rather than beginning with an already-mutated screen.

## Event frames

Every later frame maps one-to-one to an actual `ExecutionEvent`.

A frame records:

```text
frame_index
execution event_index
instruction_index
logical op
machine digest
render-state digest
geometry-scene digest
render state
geometry scene
geometry delta from previous frame
```

The timeline constructor replays the normative execution trace and checks the complete machine digest after each step. A mismatch aborts timeline construction.

## Geometry validation

A saved timeline does not get to lie about its own geometry.

During deserialization each frame:

1. reconstructs and validates its `RenderState`;
2. reconstructs its `GeometryScene`;
3. rebuilds geometry from the saved render state and frozen geometry profile;
4. requires canonical equality with the saved scene;
5. verifies all claimed digests;
6. recomputes the geometry delta against the previous frame and requires exact equality.

This makes a timeline a derived artifact, not another authority.

## Corpus and State Weave behavior

`build_relic_timeline()` can receive an optional frozen `GeometryProfile` and `StateWeave`.

The same geometry profile is used for every frame. Its digest, corpus snapshot identity, and source provenance continue to flow through the embedded geometry scenes.

State Weaves remain part of render state and therefore participate in deterministic geometry generation. A frontend never needs to infer semantic intent from SVG pixels.

## SVG frame export

The CLI can render every exact frame into deterministic standalone SVG:

```bash
td1-sim timeline examples/sum.td1 --output timeline.json

td1-sim timeline-svgs timeline.json \
  --out-dir relic-frames \
  --theme relic
```

The directory contains:

```text
frame-0000.svg
frame-0001.svg
frame-0002.svg
...
manifest.json
```

`manifest.json` is a deterministic `td1.timeline-svg-manifest` artifact containing:

- the timeline digest;
- exact renderer options;
- one entry per frame;
- scene digest;
- SVG artifact digest;
- SVG metadata digest;
- deterministic filename.

The manifest allows a future player, video renderer, browser frontend, or regression test to prove exactly which scene produced each visible frame.

## Verification

Validate a saved timeline:

```bash
td1-sim timeline-verify timeline.json
```

The verifier reconstructs every embedded render state, geometry scene, and inter-frame delta before returning the timeline digest.

## Non-normative presentation

The following remain deliberately outside timeline v1:

- milliseconds per frame;
- easing curves;
- interpolation between lattice points;
- ghosting/persistence;
- motion blur;
- camera position;
- zoom;
- sound;
- color animation;
- particle effects;
- speculative in-between machine states.

Those are legitimate future presentation choices only when they preserve the exact endpoints in this timeline.

If future Veilbreak-derived research motivates temporal presentation rules, those rules must be represented as explicit versioned presentation constraints rather than silently changing machine execution.

## Why this matters

Without this layer a frontend could animate directly from whichever state it happened to receive and quietly invent causality between frames.

With it, TD-1 can eventually display complex morphing Relic Mode behavior while retaining the chain:

```text
visible change
    -> exact geometry delta
        -> exact geometry scenes
            -> exact render states
                -> exact execution event
                    -> logical machine transition
```

That is the boundary between an alien-looking animation and an auditable native computer interface.