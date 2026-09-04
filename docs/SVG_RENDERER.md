# Deterministic Reference SVG Renderer

## Purpose

`td1.geometry-scene` is the normative presentation-independent geometry contract. The SVG renderer is the first visible reference implementation of that contract.

It deliberately sits **after** geometry:

```text
machine truth
    -> render state
        -> native geometry scene
            -> SVG reference renderer
```

The renderer cannot inspect registers, execute State Weaves, query a corpus, or infer missing state. Its only normative input is a validated `GeometryScene`.

> Pixels are downstream of truth.

## What is normative

The geometry scene already fixes:

- primitive identity;
- primitive kind (`node`, `segment`, `polyline`);
- primitive point topology;
- integer axial `(q,r,z)` coordinates;
- explicit geometry scale;
- glyph/root/state metadata already attached to primitives;
- source render and machine digests;
- optional corpus geometry profile and applied-rule provenance.

The renderer must preserve those items rather than reconstructing them from visual appearance.

## What is presentation only

SVG v1 chooses:

- an integer 2-D projection;
- viewport margin;
- stroke/fill palette;
- node radius;
- line weight derived from explicit geometry scale;
- optional engineering labels;
- output theme.

Changing one of those choices does not change TD-1 state.

The v1 projection is identified as:

```text
axial-int-oblique/v1
```

For a lattice point `(q,r,z)`:

```text
x = (2q + r) * unit + z * depth_x
y = 3r * unit - z * depth_y
```

All projection arithmetic is integer-only. This is a renderer contract, not a claim that this is the only correct geometric projection of TD-1's native lattice.

## Themes

### Relic

Relic is zero-display-text by default. Primitive meaning is carried through geometry and machine-readable `data-*` attributes rather than visible English labels.

Its palette is a presentation choice only. Color does not currently encode ternary state or semantic meaning.

### Engineering

Engineering uses the exact same projected primitive geometry but displays labels derived directly from:

```text
primitive_id | role
```

Those labels expose existing geometry metadata; they do not invent a translation layer.

The theme changes styling and default label visibility. It must not change primitive membership or coordinates.

## Stable IDs and escaping

Geometry primitive IDs are preserved in `data-primitive-id` exactly as supplied by the validated scene.

SVG element `id` values use a deterministic byte escape so arbitrary UTF-8 identifiers cannot break XML syntax or inject markup. Attribute values and engineering label text are XML escaped.

This makes SVG a safe serialization target even when a future external geometry producer supplies unusual identifiers.

## Provenance metadata

Every SVG embeds canonical JSON in its `<metadata>` element containing:

- `td1.svg-render` schema/version;
- projection identifier;
- geometry scene digest;
- source render digest;
- source machine digest;
- primitive count;
- renderer options;
- optional geometry profile digest;
- optional corpus snapshot ID/digest;
- optional applied corpus geometry-rule IDs.

The metadata JSON has its own SHA-256 digest in the in-memory `SVGRenderArtifact`. The complete SVG bytes can also be fingerprinted.

The SVG root repeats the geometry scene digest and renderer version as attributes for cheap inspection.

## Determinism

For identical:

- `GeometryScene`;
- `SVGRenderOptions`;
- renderer schema/version;

the SVG output must be byte-identical.

No current timestamp, random value, environment path, browser feature detection, or network resource is permitted in the output.

## CLI

First save a native geometry scene:

```bash
td1-sim geometry examples/sum.td1 > scene.json
```

Render zero-text Relic SVG to stdout:

```bash
td1-sim svg scene.json > relic.svg
```

Render Engineering SVG with derived labels:

```bash
td1-sim svg scene.json --theme engineering > engineering.svg
```

Write directly to a file and print its digests:

```bash
td1-sim svg scene.json --output relic.svg
```

Override the default label policy explicitly:

```bash
td1-sim svg scene.json --theme engineering --no-labels
```

Projection parameters are exposed for engineering experiments:

```bash
td1-sim svg scene.json --unit 4 --depth-x 3 --depth-y 2 --margin 48
```

Those options affect only SVG presentation. They do not alter the input geometry scene.

## Non-goals for v1

- animation;
- shaders;
- camera movement;
- audio;
- interaction/hit testing;
- corpus motif inference;
- glyph recognition from rendered pixels;
- editing machine state through SVG;
- WebGL acceleration;
- claiming final industrial design styling.

Future animated frontends should consume `td1.geometry-delta` / execution traces rather than comparing SVG pixels.
