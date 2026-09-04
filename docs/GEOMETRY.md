# Native Geometry Contract

## Purpose

`td1.geometry-scene` is the boundary between deterministic TD-1 state and any visual frontend. It describes topology, placement, depth, and corpus-backed transforms without choosing color, materials, shaders, animation timing, camera motion, or final artistic styling.

The geometry scene is downstream of `td1.render-state` and preserves both the source render-state digest and source machine-state digest.

> Geometry may encode truth. It may not invent truth.

## Coordinate system

Schema v1 uses an integer axial triangular lattice:

```text
axial-triangular-int/v1
```

Every point is `(q, r, z)`:

- `q` and `r` are integer axial lattice coordinates;
- `z` is a discrete depth coordinate;
- no floating-point geometry is required by the normative contract.

A frontend may map this lattice into pixels, vectors, meshes, LEDs, PCB silkscreen, or physical control surfaces. That mapping is presentation, not machine state.

## 27-state microglyph topology

Each 3-trit cell has 27 states. Schema v1 assigns three non-collinear axial directions to the three trit positions.

For each trit:

- `+1` emits a spoke along the assigned axis;
- `0` emits no spoke;
- `-1` emits a spoke along the reversed axis.

All glyphs share a center node. This produces 27 unique topologies and is reversible without using text labels. `glyph_id_from_geometry()` reconstructs the original glyph ID from spoke orientation alone.

This topology is a **reference substrate**, not a claim that the final physical glyph artwork is finished. Future stylization may bend, taper, extrude, or ornament a spoke as long as the normative topology remains recoverable.

## 12-trit word geometry

A TD-1 word is four 3-trit cells. Geometry v1 emits:

- one word anchor;
- four deterministic microglyph origins around that anchor;
- the exact glyph topology for each cell.

Registers, sparse memory words, machine-control values, and selected Observer Continuity values use the same substrate. This prevents the UI from inventing a separate visual language for every subsystem.

## State Weave geometry

Semantic roots use stable root IDs from the render-state contract. Schema v1 maps the 16 roots into a reserved 16-state window of the 27-state microglyph substrate and places them as an ordered chain.

The State Weave modifier is topological:

- `+` extends the terminal forward;
- `-` extends it backward;
- `0` extends it along the neutral axis.

The final artistic form is intentionally not frozen.

## Corpus-backed geometry profile

A `GeometryProfile` is built from one frozen `VB-TD1-*` corpus snapshot and a declared confidence threshold. Only annotations at or above that threshold are admitted.

The profile records:

- snapshot ID and snapshot digest;
- confidence threshold;
- supported motifs;
- exact source IDs supporting each motif;
- annotation methods;
- mean admitted confidence.

A geometry scene embeds the profile and its digest. Corpus-backed transforms therefore remain reproducible.

## Current corpus-backed rules

Schema v1 supports four explicit transforms:

| Rule | Motif | Effect |
| --- | --- | --- |
| `VB-GEO-LATTICE-001` | `lattice` | place the nine registers on a triangular 3x3 axial lattice |
| `VB-GEO-DEPTH-001` | `depth` | separate machine, semantic, and observer planes on discrete `z` layers |
| `VB-GEO-MULTISCALE-001` | `multiscale` | increase semantic-root scale relative to machine microglyphs |
| `VB-GEO-BRAID-001` | `braiding` | route State Weave links through alternating depth offsets |

Each applied rule stores the exact source IDs admitted by the profile. A scene cannot claim a corpus-backed rule if the profile does not contain the matching motif evidence.

No profile means no corpus-derived rule is claimed. The fallback layout is deliberately plain and flat.

## What is project-native versus corpus-derived

Project-native schema choices:

- balanced-ternary microglyph encoding;
- three axial trit directions;
- four microglyphs per 12-trit word;
- integer-only geometry serialization;
- stable semantic root IDs;
- deterministic fallback placement.

Corpus-derived transforms are limited to rules that appear in `applied_rules` with source IDs.

This distinction matters. A reviewer should be able to ask whether a visual feature came from the machine architecture, an explicit TD-1 design choice, or a frozen phenomenology motif.

## Determinism and digests

`GeometryScene` canonicalizes primitive ordering and rule ordering before serialization. It then computes SHA-256 over canonical JSON.

Given the same:

- render-state digest;
- machine-state digest;
- geometry schema version;
- frozen corpus snapshot;
- confidence threshold;

TD-1 must produce the same geometry scene and geometry digest.

## CLI

Emit project-native fallback geometry:

```bash
td1-sim geometry examples/sum.td1
```

Admit rules from a frozen corpus snapshot:

```bash
td1-sim geometry examples/sum.td1 \
  --corpus tests/fixtures/corpus_snapshot_v1.json
```

Include a State Weave:

```bash
td1-sim geometry examples/sum.td1 \
  --weave 'TIME>REFERENCE:+'
```

The current repository fixture is synthetic and exists only to validate the pipeline. It must not be represented as real Veilbreak evidence.

## Deferred work

Geometry v1 deliberately does not freeze:

- final glyph silhouettes;
- typography or colors;
- shader effects;
- transition timing;
- corpus-derived morphing rules;
- focus-through behavior;
- context persistence;
- interactive hit regions;
- physical control-surface dimensions.

Those should build on this contract rather than bypass it.
