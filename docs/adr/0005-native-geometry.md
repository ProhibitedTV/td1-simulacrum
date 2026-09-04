# ADR 0005: Native geometry is deterministic and corpus-traceable

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 now has a normative render-state contract and a frozen phenomenology corpus pipeline. The next risk is allowing a frontend to become an accidental second source of truth by inventing geometry, depth, motion, or semantic structure that cannot be traced back to machine state or explicit design provenance.

The project also wants Veilbreak-derived motifs to remain a real design anchor without allowing subjective source material to silently control arithmetic or become unreviewable aesthetic lore.

## Decision

TD-1 will insert a versioned `td1.geometry-scene` contract between render state and final visual or physical presentation.

Geometry v1 will:

- use integer axial triangular coordinates plus discrete depth;
- define unique reversible topology for all 27 3-trit microglyph states;
- compose four microglyphs into one 12-trit word structure;
- preserve source render-state and machine-state digests;
- admit corpus-derived layout transforms only through a `GeometryProfile` built from one frozen `VB-TD1-*` snapshot and an explicit confidence threshold;
- record every applied corpus rule with its motif and exact supporting source IDs;
- keep project-native geometry choices distinguishable from corpus-derived rules;
- serialize canonically and expose a geometry digest for regression tests.

The first corpus-backed rules are limited to lattice placement, depth-plane separation, multiscale semantic emphasis, and optional State Weave braiding.

## Consequences

Positive:

- frontends can be replaced without changing TD-1 semantics;
- all 27 microglyph states have a testable geometric identity;
- Veilbreak influence becomes auditable instead of aesthetic hand-waving;
- geometry can later target screens, vector art, LEDs, PCB markings, or physical controls from the same source contract;
- deterministic geometry fixtures become possible before an interactive frontend exists.

Costs:

- the geometry layer adds another versioned schema to maintain;
- visual experimentation must preserve normative topology;
- corpus-backed transforms require frozen evidence and cannot be casually toggled as decoration;
- future geometry schema changes will require migration/version discipline.

## Non-decision

This ADR does not freeze final glyph artwork, color, animation, shaders, the ultimate Veilbreak motif interpretation, physical dimensions, or any claim about the ontology of the source reports.
