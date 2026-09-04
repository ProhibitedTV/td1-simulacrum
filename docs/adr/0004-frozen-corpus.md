# ADR 0004: Freeze external phenomenology before deriving requirements

- Status: Accepted
- Date: 2026-09-04

## Context

TD-1 treats the Veilbreak phenomenology corpus as a primary native-interface design anchor. External source material changes over time, and subjective reports often contain both an observation and an interpretation of that observation.

If TD-1 derives requirements directly from a live corpus without freezing inputs, later reviewers cannot reproduce which records produced a design decision. If observation and interpretation are merged, the project can also accidentally convert a participant's explanation into an engineering premise.

## Decision

TD-1 will freeze external phenomenology into versioned `VB-TD1-*` snapshots before deriving corpus-backed requirements.

Each snapshot will:

- use deterministic canonical serialization and a content digest;
- preserve reported observation separately from interpretation;
- require an explicit mapping to any upstream Veilbreak export schema;
- carry explicit motif annotations with annotation-method provenance;
- reject requirement traces whose cited sources do not actually carry the claimed motif annotation;
- remain immutable once used as a TD-1 design input.

A later source update creates a new snapshot and a corpus-delta report. Historical TD-1 revisions continue to reference their original snapshot.

## Consequences

Positive:

- corpus-backed requirements become reproducible;
- upstream schema changes fail visibly rather than being guessed;
- observation and ontology remain separated in data structures;
- reviewers can trace source -> motif -> requirement -> implementation;
- future model-assisted motif extraction can be audited independently of raw reports.

Costs:

- freezing a corpus requires explicit review and curation;
- snapshot IDs and annotation changes require version discipline;
- live data cannot silently change an existing interface revision;
- a larger provenance archive must be maintained over time.

## Non-decision

This ADR does not establish the ontology of Veilbreak reports, define the final live Veilbreak transport/API integration, or make model-generated motif annotations authoritative.
