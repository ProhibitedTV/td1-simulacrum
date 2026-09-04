# Relic Browser Player

## Purpose

The Relic browser player is the first animated frontend for TD-1 native geometry.
It is intentionally downstream of the already-validated machine, execution trace,
render state, geometry, Relic timeline, and morph-plan layers.

The player is **not** a machine-state simulator. It is a presentation engine.
Authoritative state exists only at exact `td1.relic-timeline` frames.

The core rule is:

> The browser may animate between known endpoints, but it may never invent a machine endpoint.

## Artifact format

`td1-sim relic-player` compiles one saved `td1.relic-timeline` into a single,
self-contained HTML file. The artifact has no network dependency and can be
opened directly from disk in a modern browser.

The HTML embeds three exact canonical payloads as base64:

- the `td1.relic-player-artifact` manifest;
- the exact canonical `td1.relic-timeline` bytes;
- the exact canonical `td1.timeline-morph-manifest` bytes derived from that timeline.

Base64 is transport encoding only. The decoded timeline and morph bytes are the
same canonical bytes used by the Python reference implementation for SHA-256
fingerprinting.

## Verification

Before playback begins, the browser uses WebCrypto SHA-256 to verify:

1. the embedded player manifest against its declared manifest digest;
2. the embedded timeline bytes against `timeline_bytes_sha256`;
3. the embedded morph-manifest bytes against `morph_manifest_bytes_sha256`;
4. timeline/morph linkage through the exact `timeline_digest`;
5. frame/morph cardinality.

Playback is blocked when verification fails.

The Python verifier performs the stronger offline check:

```bash
td1-sim relic-player-verify relic.html
```

It decodes the embedded payloads, reconstructs the `RelicTimeline`, regenerates
the deterministic timeline morph manifest, and requires byte-for-byte canonical
agreement.

The complete HTML file is fingerprinted externally. The embedded manifest uses:

```text
html_digest_strategy = external-sha256/full-html
```

The full HTML digest cannot be embedded inside the same HTML while also being a
simple hash of the entire file without creating a self-reference problem. The
compiler therefore prints the full-file SHA-256 alongside the output path.

## Projection parity

The browser uses the same integer axial/depth projection as the SVG reference
renderer:

```text
x = (2q + r) * unit + z * depth_x
y = 3r * unit - z * depth_y
```

The default values are also the SVG renderer defaults:

```text
unit = 3
depth_x = 2
depth_y = 1
margin = 36
```

The player computes one stable view box across every exact scene in the timeline.
It does not perform camera flights or per-frame auto-framing in v1.

## Transition behavior

The player does not compare pixels and does not infer motion from endpoint
coordinates. It consumes the exact `MorphDescriptor` records already derived by
`td1.morph-plan`.

### `enter`

The exact after-primitive is instantiated at its authoritative endpoint and may
change opacity from hidden to visible.

### `exit`

The exact before-primitive may change opacity toward hidden. If the descriptor
contains `context-persistence-eligible`, non-state visual persistence may extend
the fade using the player-only `persistence_ms` setting.

### `translate`

The browser projects the exact integer `(dq, dr, dz)` translation carried by the
morph descriptor. No additional movement is added.

### `reform`

The browser crossfades the exact before and after endpoint shapes. A
`continuous_reform_eligible` strategy may alter presentation emphasis, but v1
still does not generate speculative topology samples between endpoints.

### `retag`

Only presentation metadata emphasis changes. No geometric movement is allowed.

### unchanged primitives

A primitive with no morph descriptor receives no transition animation.

## Endpoint reconciliation

After every animated adjacent transition, the browser discards transient
presentation elements and rebuilds the canvas from the exact target
`GeometryScene`.

The manifest freezes this behavior as:

```text
hard-reconcile-authoritative-scene-after-transition/v1
```

This is deliberately stronger than trusting the accumulated result of browser
animations. Presentation drift cannot become the next machine state.

## Non-normative configuration

`td1.relic-player-config` v1 contains presentation choices only:

- frame dwell time;
- transition duration;
- optional visual persistence duration;
- CSS/Web Animations easing;
- autoplay;
- looping;
- diagnostic panels initially open or closed;
- projection scale/depth/margin.

These values do not alter the timeline, native geometry, morph plan, machine
state, corpus evidence, or semantic meaning.

Example:

```bash
td1-sim relic-player timeline.json \
  --output relic.html \
  --frame-ms 1100 \
  --transition-ms 620 \
  --persistence-ms 260 \
  --easing ease-in-out
```

Disable automatic playback and looping:

```bash
td1-sim relic-player timeline.json \
  --output relic.html \
  --no-autoplay \
  --no-loop
```

## Controls

The standalone artifact supports:

- play / pause;
- previous exact frame;
- next exact frame;
- restart;
- playback speed cycling;
- Engineering overlay;
- provenance panel.

Keyboard controls:

- `Space`: play/pause;
- `Left` / `Right`: previous/next exact frame;
- `Home`: restart;
- `E`: Engineering overlay;
- `P`: provenance panel;
- `+` / `-`: speed.

Relic canvas geometry contains no display text by default. Human-readable state
and provenance live in explicit diagnostic panels outside the native geometry
canvas.

## Corpus hints

Corpus-backed morph rules remain hints, not animation commands and not ontology
claims. The player only reacts to hints already present in validated morph
descriptors.

It never queries corpus data itself and never promotes a corpus motif into a new
machine event.

## Security and integrity boundary

The WebCrypto checks detect payload corruption and inconsistent embedded data.
They are not a digital signature and do not establish who produced an artifact.
A malicious editor who rewrites all payloads and all hashes can create a new
internally consistent artifact.

For engineering review, retain the compiler-reported full HTML SHA-256 and the
source repository revision alongside the artifact.

## Deliberately deferred

v1 does not include:

- WebGL;
- audio;
- camera flight paths;
- speculative state interpolation;
- topology spline generation;
- live machine control;
- physical hardware input;
- networking;
- external JavaScript frameworks.

Those layers may be added later only if they continue to consume the existing
truth-bearing contracts rather than replacing them.
