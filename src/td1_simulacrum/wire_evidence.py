"""Generic report/transcript evidence for TD-1 parity-wire sessions.

This artifact is intentionally independent from trace-derived campaigns so fixed
golden-vector hardware sessions can preserve and replay the same exact wire
conversation without pretending they originated from a logical workload.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

from .parity import ConformanceReport, run_conformance
from .wire import JsonLineParityTransport
from .wire_transcript import (
    ParityTranscriptError,
    ParityWireTranscript,
    ReplayParityLineIO,
    transcript_for_report,
)

WIRE_EVIDENCE_SCHEMA = "td1.parity-wire-evidence"
WIRE_EVIDENCE_SCHEMA_VERSION = 1


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ParityWireEvidence:
    """One exact conformance report bound to its exact canonical wire transcript."""

    report: ConformanceReport
    transcript: ParityWireTranscript
    schema: str = WIRE_EVIDENCE_SCHEMA
    version: int = WIRE_EVIDENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != WIRE_EVIDENCE_SCHEMA or self.version != WIRE_EVIDENCE_SCHEMA_VERSION:
            raise ParityTranscriptError("unsupported parity-wire-evidence schema")
        expected = transcript_for_report(self.report)
        if self.transcript.canonical_json() != expected.canonical_json():
            raise ParityTranscriptError(
                "wire evidence transcript disagrees with conformance report traffic"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "report_digest": self.report.digest(),
            "report": self.report.as_dict(),
            "transcript_digest": self.transcript.digest(),
            "transcript": self.transcript.as_dict(),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256_text(self.canonical_json())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityWireEvidence":
        report_payload = payload.get("report")
        transcript_payload = payload.get("transcript")
        if not isinstance(report_payload, Mapping) or not isinstance(
            transcript_payload, Mapping
        ):
            raise ParityTranscriptError("wire evidence requires report and transcript objects")
        evidence = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            report=ConformanceReport.from_dict(report_payload),
            transcript=ParityWireTranscript.from_dict(transcript_payload),
        )
        claimed_report = payload.get("report_digest")
        if claimed_report is not None and claimed_report != evidence.report.digest():
            raise ParityTranscriptError("wire evidence report_digest mismatch")
        claimed_transcript = payload.get("transcript_digest")
        if claimed_transcript is not None and claimed_transcript != evidence.transcript.digest():
            raise ParityTranscriptError("wire evidence transcript_digest mismatch")
        return evidence

    @classmethod
    def from_json(cls, text: str) -> "ParityWireEvidence":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParityTranscriptError("wire evidence is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ParityTranscriptError("wire evidence JSON root must be an object")
        return cls.from_dict(payload)


def replay_wire_evidence(evidence: ParityWireEvidence) -> ConformanceReport:
    """Replay exact report vectors/session through saved wire bytes and require identity."""
    line_io = ReplayParityLineIO(evidence.transcript)
    transport = JsonLineParityTransport(line_io)
    vectors = tuple(record.request.vector for record in evidence.report.records)
    replayed = run_conformance(
        transport,
        vectors,
        session_id=evidence.report.session_id,
    )
    line_io.assert_consumed()
    if replayed.canonical_json() != evidence.report.canonical_json():
        raise ParityTranscriptError("wire evidence replay disagrees with saved report")
    return replayed
