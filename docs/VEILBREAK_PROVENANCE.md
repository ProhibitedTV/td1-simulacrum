# Veilbreak Provenance Model

## Purpose

Veilbreak is a primary design anchor for TD-1's native interface research. The corpus is used to derive recurring phenomenological motifs and convert them into explicit, versioned interface requirements.

The corpus does **not** define arithmetic, machine correctness, or ontology.

## Epistemic policy

TD-1 distinguishes three things that must never be silently collapsed:

1. **Reported observation** — what a participant says they perceived.
2. **Interpretation** — what the participant or researcher believes the observation represents.
3. **Engineering consequence** — a testable design hypothesis derived from the observation.

A report attributed to extraterrestrial, interdimensional, mantid-like, machine-elf, or other non-human sources remains a human-reported observation unless independently established otherwise.

## Normalized motif candidates

The initial corpus-analysis pass should score or annotate motifs such as:

- depth / layered perception
- microglyphs / tiny script-like forms
- lattice / grid / crystalline geometry
- pillars / columns / architectural structures
- multiscale structure
- static symbol fields
- flipping / morphing symbols
- horizontal or vertical motion
- braiding / intertwining
- schematic / blueprint-like forms
- object-like anchoring
- focus-through / stereogram-like depth behavior
- context-dependent persistence
- local interface interaction
- reported technician / maintenance motifs
- reported non-human or entity-mediated instruction

This list is provisional and should change when corpus analysis supports a better model.

## Requirement traceability

Each corpus-derived interface requirement should eventually carry a trace like:

```text
source records
    -> normalized motif
        -> requirement
            -> implementation
                -> validation result
```

Example:

```text
recurring depth/layering reports
    -> DEPTH motif
        -> UI-DEPTH-001
            -> multi-plane state renderer
                -> deterministic state/render tests + sober usability study
```

## Controls against aesthetic drift

TD-1 should not selectively preserve motifs merely because they look alien or visually impressive. Corpus-derived decisions should be revisited when broader analysis changes the weighting or interpretation of a motif.

Aesthetic choices are permitted where the data and computational requirements leave design freedom, but those choices must be identified as aesthetic rather than corpus-derived.

## Anomalous feedback provenance

Future phenomenological user testing may produce design suggestions reportedly attributed to non-human entities. Those reports can enter the research log, but acceptance into TD-1 requires an engineering disposition.

Recommended record fields:

- session ID
- human participant ID
- prior exposure to TD-1 concepts
- reported source/entity classification, if any
- exact observation or recommendation
- confidence / ambiguity notes
- engineering hypothesis generated
- independent test method
- result: confirmed / rejected / inconclusive / cannot reproduce
- revision affected

The working rule is:

> Low threshold for listening. High threshold for believing. Extremely high threshold for merging.

## Corpus versioning

A future ingestion pipeline should freeze explicit corpus snapshots (for example, `VB-TD1-001`) so that each TD-1 interface revision can be reproduced against the same source data.

New corpus snapshots should generate a design-delta report rather than silently mutating the interface model.
