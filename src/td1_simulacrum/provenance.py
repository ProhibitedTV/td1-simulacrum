"""Traceability data structures for corpus-derived TD-1 requirements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvidenceStatus(str, Enum):
    REPORTED = "reported"
    REPLICATED = "replicated"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"
    CANNOT_REPRODUCE = "cannot_reproduce"


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """Reference to an external or internal source observation."""

    source_id: str
    corpus_revision: str
    summary: str
    interpretation: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")
        if not self.corpus_revision.strip():
            raise ValueError("corpus_revision must not be empty")
        if not self.summary.strip():
            raise ValueError("summary must not be empty")


@dataclass(frozen=True, slots=True)
class RequirementTrace:
    """End-to-end provenance for a corpus-derived engineering requirement."""

    requirement_id: str
    motif: str
    source_ids: tuple[str, ...]
    implementation: str
    validation_method: str
    status: EvidenceStatus = EvidenceStatus.REPORTED

    def __post_init__(self) -> None:
        if not self.requirement_id.strip():
            raise ValueError("requirement_id must not be empty")
        if not self.motif.strip():
            raise ValueError("motif must not be empty")
        if not self.source_ids:
            raise ValueError("at least one source_id is required")
        if not self.implementation.strip():
            raise ValueError("implementation must not be empty")
        if not self.validation_method.strip():
            raise ValueError("validation_method must not be empty")

    def as_dict(self) -> dict[str, object]:
        return {
            "requirement_id": self.requirement_id,
            "motif": self.motif,
            "source_ids": list(self.source_ids),
            "implementation": self.implementation,
            "validation_method": self.validation_method,
            "status": self.status.value,
        }
