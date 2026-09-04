# Frozen Corpus Pipeline

## Purpose

Veilbreak is a primary design anchor for TD-1's native interface. That makes reproducibility mandatory: a TD-1 revision must be able to identify exactly which corpus snapshot and annotations informed it.

The corpus pipeline freezes external phenomenology into versioned `VB-TD1-*` snapshots before design requirements are derived.

## Epistemic separation

Every source record preserves two fields as separate concerns:

1. **reported observation** — what the participant says they perceived;
2. **interpretation** — what the participant or researcher believes the observation represents.

The adapter must never silently merge those fields. A report such as "layered geometric symbols were perceived" is not the same claim as "an external intelligence showed layered geometric symbols."

TD-1 may retain both when they are present. Engineering requirements are derived from normalized motifs, not from silently promoting interpretation into observation.

## Snapshot contract

Schema:

```text
td1.corpus-snapshot / v1
```

Snapshot IDs use:

```text
VB-TD1-001
VB-TD1-002
...
```

A snapshot contains:

- source name and reviewed source-schema identifier;
- optional upstream source revision;
- deterministic source records;
- versioned motif annotations;
- annotation method and confidence;
- canonical JSON serialization;
- SHA-256 snapshot digest.

Historical snapshots are immutable inputs. New source material produces a new snapshot and a delta report rather than mutating old provenance.

## Veilbreak export adapter

`VeilbreakExportAdapter` consumes caller-supplied exported records through an explicit `VeilbreakFieldMap`.

The adapter deliberately **does not guess field names**.

Example:

```python
fields = VeilbreakFieldMap(
    source_id="experiment_id",
    observation="observation",
    interpretation="interpretation",
)
```

If the upstream export schema changes, ingestion fails until the mapping is reviewed. That is intentional. Quietly guessing an upstream field would be worse than refusing to ingest it.

The current repository includes only synthetic Veilbreak-shaped fixtures. A real public corpus snapshot should be frozen only after the live/export schema has been explicitly reviewed.

## Motif annotations

The provisional normalized motif vocabulary includes concepts such as:

- depth;
- microglyphs;
- lattices;
- architectural structure;
- multiscale structure;
- morphing;
- braiding;
- schematic forms;
- focus-through behavior;
- interaction;
- technician motifs;
- reported entity-mediated instruction.

Annotations record their method:

- `manual` — human researcher annotation;
- `rule` — deterministic rule-based annotation;
- `model` — model-generated candidate annotation;
- `participant` — participant-supplied categorization.

Model output should initially be treated as a candidate for review, not as an authoritative motif assignment.

## Source -> motif -> requirement trace

A corpus-derived requirement must have a strict trace:

```text
source record
    -> explicit motif annotation
        -> RequirementTrace
            -> implementation
                -> validation method / disposition
```

`export_requirement_traces()` rejects a requirement if:

- one of its source IDs is absent from the frozen snapshot; or
- a cited source lacks the motif annotation claimed by the requirement.

This prevents a requirement from citing a dramatic report while quietly deriving a property that was never actually annotated in that report.

## Corpus deltas

`compare_snapshots()` reports:

- added and removed source IDs;
- added and removed annotation identities;
- motif-count deltas.

The delta is not itself a design decision. It tells TD-1 maintainers what changed in the research input so they can decide whether interface requirements need review.

## Offline fixtures

Tests use synthetic fixtures under `tests/fixtures/`.

They are deliberately fictional and must not be represented as actual Veilbreak observations. Their purpose is to prove schema, provenance, and deterministic behavior without depending on live network access or changing external content.

## CLI

Validate and fingerprint a frozen snapshot:

```bash
td1-sim corpus-validate tests/fixtures/corpus_snapshot_v1.json
```

Compare two snapshots:

```bash
td1-sim corpus-delta VB-TD1-001.json VB-TD1-002.json
```

## First real snapshot procedure

Before freezing the first real public Veilbreak baseline:

1. review the live/public export or API schema;
2. define an explicit `VeilbreakFieldMap`;
3. ingest without motif inference;
4. preserve raw reported observation separately from interpretation;
5. assign or review motif annotations;
6. serialize the snapshot and record its digest;
7. publish the `VB-TD1-*` identifier used by the TD-1 revision;
8. derive requirements only through explicit trace records.

## Rule

> The corpus may change what questions TD-1 asks. It does not change what arithmetic means.
