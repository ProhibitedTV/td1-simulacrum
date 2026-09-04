"""Versioned corpus snapshots and provenance-preserving ingestion for TD-1.

This module defines the deterministic data model used to freeze external
phenomenology inputs before they influence interface requirements. It does not
perform ontology claims or automatic motif discovery.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

from .provenance import RequirementTrace, SourceRecord

CORPUS_SCHEMA = "td1.corpus-snapshot"
CORPUS_SCHEMA_VERSION = 1
SNAPSHOT_ID_RE = re.compile(r"^VB-TD1-\d{3,}$")


class CorpusError(ValueError):
    """Raised for invalid corpus snapshots or ingestion inputs."""


class AnnotationMethod(str, Enum):
    MANUAL = "manual"
    RULE = "rule"
    MODEL = "model"
    PARTICIPANT = "participant"


class Motif(str, Enum):
    """Provisional normalized motifs used by early TD-1 corpus analysis."""

    DEPTH = "depth"
    MICROGLYPH = "microglyph"
    LATTICE = "lattice"
    ARCHITECTURE = "architecture"
    MULTISCALE = "multiscale"
    STATIC_FIELD = "static_field"
    MORPHING = "morphing"
    HORIZONTAL_MOTION = "horizontal_motion"
    VERTICAL_MOTION = "vertical_motion"
    BRAIDING = "braiding"
    SCHEMATIC = "schematic"
    OBJECT_ANCHORED = "object_anchored"
    FOCUS_THROUGH = "focus_through"
    CONTEXT_PERSISTENCE = "context_persistence"
    INTERACTION = "interaction"
    TECHNICIAN = "technician"
    ENTITY_INSTRUCTION = "entity_instruction"


@dataclass(frozen=True, slots=True)
class MotifAnnotation:
    source_id: str
    motif: Motif
    method: AnnotationMethod
    confidence_milli: int = 1000
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise CorpusError("annotation source_id must not be empty")
        if not 0 <= self.confidence_milli <= 1000:
            raise CorpusError("confidence_milli must be in 0..1000")

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_id": self.source_id,
            "motif": self.motif.value,
            "method": self.method.value,
            "confidence_milli": self.confidence_milli,
        }
        if self.note is not None:
            payload["note"] = self.note
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "MotifAnnotation":
        return cls(
            source_id=str(payload["source_id"]),
            motif=Motif(str(payload["motif"])),
            method=AnnotationMethod(str(payload["method"])),
            confidence_milli=int(payload.get("confidence_milli", 1000)),
            note=str(payload["note"]) if payload.get("note") is not None else None,
        )


@dataclass(frozen=True, slots=True)
class CorpusSnapshot:
    """Frozen corpus input for one reproducible TD-1 design revision."""

    snapshot_id: str
    created_at_utc: str
    source_schema: str
    records: tuple[SourceRecord, ...]
    annotations: tuple[MotifAnnotation, ...] = ()
    source_name: str = "Veilbreak"
    source_revision: str | None = None
    schema: str = CORPUS_SCHEMA
    version: int = CORPUS_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != CORPUS_SCHEMA:
            raise CorpusError(f"unsupported corpus schema {self.schema!r}")
        if self.version != CORPUS_SCHEMA_VERSION:
            raise CorpusError(f"unsupported corpus schema version {self.version}")
        if not SNAPSHOT_ID_RE.match(self.snapshot_id):
            raise CorpusError("snapshot_id must match VB-TD1-###")
        if not self.created_at_utc.strip():
            raise CorpusError("created_at_utc must not be empty")
        if not self.source_schema.strip():
            raise CorpusError("source_schema must not be empty")

        records = tuple(sorted(self.records, key=lambda record: record.source_id))
        annotations = tuple(
            sorted(self.annotations, key=lambda item: (item.source_id, item.motif.value))
        )
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "annotations", annotations)

        source_ids = tuple(record.source_id for record in records)
        if len(set(source_ids)) != len(source_ids):
            raise CorpusError("snapshot source IDs must be unique")
        if any(record.corpus_revision != self.snapshot_id for record in records):
            raise CorpusError("every SourceRecord corpus_revision must equal snapshot_id")

        known_sources = set(source_ids)
        annotation_keys: set[tuple[str, Motif]] = set()
        for annotation in annotations:
            if annotation.source_id not in known_sources:
                raise CorpusError(
                    f"annotation references unknown source {annotation.source_id!r}"
                )
            key = (annotation.source_id, annotation.motif)
            if key in annotation_keys:
                raise CorpusError(
                    f"duplicate annotation for {annotation.source_id}/{annotation.motif.value}"
                )
            annotation_keys.add(key)

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": self.schema,
            "version": self.version,
            "snapshot_id": self.snapshot_id,
            "created_at_utc": self.created_at_utc,
            "source_name": self.source_name,
            "source_schema": self.source_schema,
            "records": [record.as_dict() for record in self.records],
            "annotations": [annotation.as_dict() for annotation in self.annotations],
        }
        if self.source_revision is not None:
            payload["source_revision"] = self.source_revision
        return payload

    def canonical_json(self) -> str:
        return json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def motif_counts(self) -> dict[str, int]:
        counts = Counter(annotation.motif.value for annotation in self.annotations)
        return dict(sorted(counts.items()))

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "CorpusSnapshot":
        records_payload = payload.get("records")
        annotations_payload = payload.get("annotations", [])
        if not isinstance(records_payload, list):
            raise CorpusError("snapshot records must be a list")
        if not isinstance(annotations_payload, list):
            raise CorpusError("snapshot annotations must be a list")
        return cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            snapshot_id=str(payload["snapshot_id"]),
            created_at_utc=str(payload["created_at_utc"]),
            source_name=str(payload.get("source_name", "Veilbreak")),
            source_schema=str(payload["source_schema"]),
            source_revision=(
                str(payload["source_revision"])
                if payload.get("source_revision") is not None
                else None
            ),
            records=tuple(SourceRecord.from_dict(item) for item in records_payload),
            annotations=tuple(
                MotifAnnotation.from_dict(item) for item in annotations_payload
            ),
        )

    @classmethod
    def from_json(cls, text: str) -> "CorpusSnapshot":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise CorpusError("corpus snapshot JSON root must be an object")
        return cls.from_dict(payload)


@dataclass(frozen=True, slots=True)
class CorpusDelta:
    before_id: str
    after_id: str
    added_sources: tuple[str, ...]
    removed_sources: tuple[str, ...]
    added_annotations: tuple[str, ...]
    removed_annotations: tuple[str, ...]
    motif_count_delta: tuple[tuple[str, int], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "before_id": self.before_id,
            "after_id": self.after_id,
            "added_sources": list(self.added_sources),
            "removed_sources": list(self.removed_sources),
            "added_annotations": list(self.added_annotations),
            "removed_annotations": list(self.removed_annotations),
            "motif_count_delta": {
                motif: delta for motif, delta in self.motif_count_delta
            },
        }


def compare_snapshots(before: CorpusSnapshot, after: CorpusSnapshot) -> CorpusDelta:
    before_sources = {record.source_id for record in before.records}
    after_sources = {record.source_id for record in after.records}

    def annotation_key(annotation: MotifAnnotation) -> str:
        return (
            f"{annotation.source_id}:{annotation.motif.value}:"
            f"{annotation.method.value}:{annotation.confidence_milli}"
        )

    before_annotations = {annotation_key(item) for item in before.annotations}
    after_annotations = {annotation_key(item) for item in after.annotations}
    before_counts = before.motif_counts()
    after_counts = after.motif_counts()
    all_motifs = sorted(set(before_counts) | set(after_counts))

    return CorpusDelta(
        before_id=before.snapshot_id,
        after_id=after.snapshot_id,
        added_sources=tuple(sorted(after_sources - before_sources)),
        removed_sources=tuple(sorted(before_sources - after_sources)),
        added_annotations=tuple(sorted(after_annotations - before_annotations)),
        removed_annotations=tuple(sorted(before_annotations - after_annotations)),
        motif_count_delta=tuple(
            (motif, after_counts.get(motif, 0) - before_counts.get(motif, 0))
            for motif in all_motifs
            if after_counts.get(motif, 0) != before_counts.get(motif, 0)
        ),
    )


@dataclass(frozen=True, slots=True)
class VeilbreakFieldMap:
    """Explicit mapping from an exported Veilbreak record into TD-1 fields.

    The adapter deliberately refuses to guess schema field names. A changing
    upstream export must therefore be acknowledged in code or configuration.
    """

    source_id: str
    observation: str
    interpretation: str | None = None


class VeilbreakExportAdapter:
    """Normalize caller-supplied Veilbreak export rows into a frozen snapshot."""

    @staticmethod
    def ingest(
        rows: Sequence[Mapping[str, object]],
        *,
        snapshot_id: str,
        created_at_utc: str,
        source_schema: str,
        fields: VeilbreakFieldMap,
        source_revision: str | None = None,
    ) -> CorpusSnapshot:
        records: list[SourceRecord] = []
        for index, row in enumerate(rows):
            try:
                source_id = str(row[fields.source_id]).strip()
                observation = str(row[fields.observation]).strip()
            except KeyError as exc:
                raise CorpusError(
                    f"row {index}: missing required Veilbreak export field {exc.args[0]!r}"
                ) from exc

            if not source_id:
                raise CorpusError(f"row {index}: empty source ID")
            if not observation:
                raise CorpusError(f"row {index}: empty reported observation")

            interpretation: str | None = None
            if fields.interpretation is not None:
                raw = row.get(fields.interpretation)
                if raw is not None and str(raw).strip():
                    interpretation = str(raw).strip()

            records.append(
                SourceRecord(
                    source_id=source_id,
                    corpus_revision=snapshot_id,
                    summary=observation,
                    interpretation=interpretation,
                )
            )

        return CorpusSnapshot(
            snapshot_id=snapshot_id,
            created_at_utc=created_at_utc,
            source_schema=source_schema,
            source_revision=source_revision,
            records=tuple(records),
        )


def export_requirement_traces(
    snapshot: CorpusSnapshot,
    requirements: Sequence[RequirementTrace],
) -> dict[str, object]:
    """Export source -> motif -> requirement provenance with strict validation."""
    sources = {record.source_id: record for record in snapshot.records}
    annotations = {
        (annotation.source_id, annotation.motif.value): annotation
        for annotation in snapshot.annotations
    }
    traces: list[dict[str, object]] = []

    for requirement in sorted(requirements, key=lambda item: item.requirement_id):
        missing_sources = [
            source_id for source_id in requirement.source_ids if source_id not in sources
        ]
        if missing_sources:
            raise CorpusError(
                f"{requirement.requirement_id} references unknown sources: "
                + ", ".join(missing_sources)
            )

        source_links: list[dict[str, object]] = []
        for source_id in sorted(requirement.source_ids):
            annotation = annotations.get((source_id, requirement.motif))
            if annotation is None:
                raise CorpusError(
                    f"{requirement.requirement_id} lacks motif annotation "
                    f"{source_id}/{requirement.motif}"
                )
            source_links.append(
                {
                    "source_id": source_id,
                    "motif_annotation": annotation.as_dict(),
                }
            )

        traces.append(
            {
                "requirement": requirement.as_dict(),
                "sources": source_links,
            }
        )

    return {
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_digest": snapshot.digest(),
        "traces": traces,
    }
