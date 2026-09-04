# Relic Morph Plans

## Purpose

`td1.morph-plan` is the renderer-independent transition-intent contract between exact native geometry changes and future animation.

The input is already established truth:

```text
GeometryScene A
    +
GeometryScene B
    |
    v
exact td1.geometry-delta
    |
    v
td1.morph-plan
    |
    v
future browser / WebGL / physical display
```

A morph plan answers a narrow question:

> Given these exact endpoint scenes, what kind of presentation change is permitted for each changed primitive?

It does **not** answer how long the transition takes or fabricate any machine state between endpoints.

## Schema

```text
td1.morph-plan / v1
```

Every plan contains:

- the complete before and after `td1.geometry-scene` endpoints;
- their exact scene digests;
- the deterministic `td1.geometry-delta` and delta digest;
- one `MorphDescriptor` for every changed primitive;
- any corpus-admitted presentation rules and exact source IDs.

Deserialization recomputes the delta, all descriptors, translation vectors, and corpus rules. Saved morph data is rejected if it disagrees with deterministic derivation.

## Primitive intents

Geometry delta kinds map to presentation intent as follows:

| Geometry change | Morph intent | Conservative strategy |
| --- | --- | --- |
| `appear` | `enter` | `endpoint_appear` |
| `disappear` | `exit` | `endpoint_disappear` |
| `move` | `translate` | `endpoint_translation` |
| `topology` | `reform` | `discrete_reform` |
| `metadata` | `retag` | `metadata_update` |

For a true `move` delta, the plan records the exact integer `(dq, dr, dz)` translation vector derived from native lattice coordinates.

No timing or interpolation samples are implied by the word `translate`.

## Corpus-admitted temporal hints

Morph planning can consume the same frozen `GeometryProfile` attached to both endpoint scenes.

The endpoints must use the same profile revision in v1. A change in corpus revision is treated as a design/configuration transition, not machine animation.

The following provisional motifs may admit presentation hints:

### `morphing`

Rule:

```text
VB-MORPH-REFORM-001
```

A topology change may be marked `continuous_reform_eligible` instead of the conservative `discrete_reform` fallback.

This does not define a spline, duration, correspondence algorithm, or intermediate state.

### `context_persistence`

Rule:

```text
VB-MORPH-PERSIST-001
```

A disappearing primitive may be marked `context-persistence-eligible` for a non-state visual trail or afterimage between exact endpoints.

The primitive is still absent from the after scene. Persistence may never change endpoint membership.

### `focus_through`

Rule:

```text
VB-MORPH-FOCUS-001
```

A translation with nonzero native depth displacement `dz` may be marked `focus-through-eligible`.

### `horizontal_motion`

Rule:

```text
VB-MORPH-HORIZONTAL-001
```

TD-1 v1 uses a **project-defined interface convention**: a pure `q` translation (`dq != 0`, `dr == 0`) may be marked for horizontal-motion emphasis when the motif is admitted.

This is not claimed as a translation of participant phenomenology into axial coordinates.

### `vertical_motion`

Rule:

```text
VB-MORPH-VERTICAL-001
```

TD-1 v1 similarly treats a pure `r` translation (`dr != 0`, `dq == 0`) as eligible for vertical-motion emphasis when the motif is admitted.

Again, this is an engineering convention for using the motif, not an ontological or linguistic claim.

## Provenance rule

Every corpus-backed presentation rule stores:

```text
rule_id
motif
source_ids
effect
```

A rule cannot be admitted unless the frozen geometry profile contains evidence for its motif.

Therefore:

```text
no frozen motif support
    -> no corpus-backed morph rule
```

The fallback morph plan remains fully functional without any corpus evidence.

## Timeline integration

A `td1.relic-timeline` has one exact scene transition for every noninitial frame.

`build_timeline_morph_manifest()` creates:

```text
td1.timeline-morph-manifest / v1
```

with exactly one `MorphPlan` per timeline transition.

CLI:

```bash
td1-sim timeline-morphs timeline.json --output morphs.json
```

For a direct pair of scenes:

```bash
td1-sim morph before.geometry.json after.geometry.json --output morph.json
```

A future player should consume the timeline and morph manifest together. The timeline defines exact discrete truth. The morph plan defines permitted transition intent. The player supplies timing and visual execution.

## Explicit non-semantics

Morph-plan v1 does not define:

- duration;
- frame rate;
- easing curves;
- interpolation sample count;
- intermediate machine state;
- camera position;
- zoom;
- motion blur;
- particle effects;
- audio;
- color changes;
- final visual style.

A renderer may generate intermediate pixels between two exact endpoints, but those pixels are presentation interpolation and must never be serialized back as TD-1 machine truth.

## Engineering boundary

The chain is now:

```text
machine transition
    -> execution trace
        -> exact timeline frames
            -> geometry delta
                -> morph plan
                    -> animation
```

This keeps the weirdness auditable.

A future frontend is allowed to look alien.

It is not allowed to hallucinate why something moved.