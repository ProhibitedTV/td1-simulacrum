"""Deterministic recording and replay artifacts for TD-1 parity wire traffic.

Wire transcripts preserve exact canonical request/response frames as transport
evidence. They do not become arithmetic truth, machine state, or proof of
hardware authorship.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from .campaign import ParityCampaignRun, run_parity_campaign
from .parity import ConformanceReport
from .wire import (
    CAPABILITIES_CORRELATION,
    JsonLineParityTransport,
    ParityLineIO,
    ParityWireEnvelope,
    WireKind,
    decode_wire_frame,
    encode_wire_frame,
    parity_request_correlation,
)

WIRE_TRANSCRIPT_SCHEMA = "td1.parity-wire-transcript"
WIRE_TRANSCRIPT_SCHEMA_VERSION = 1
BENCH_RUN_SCHEMA = "td1.parity-bench-run"
BENCH_RUN_SCHEMA_VERSION = 1


class ParityTranscriptError(ValueError):
    """Raised when recorded wire evidence is inconsistent or cannot be replayed."""


class WireDirection(str, Enum):
    HOST_TO_DEVICE = "host_to_device"
    DEVICE_TO_HOST = "device_to_host"


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_text(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


@dataclass(frozen=True, slots=True)
class WireTranscriptRecord:
    """One exact canonical line frame observed at the parity line-I/O boundary."""

    ordinal: int
    direction: WireDirection
    frame_text: str
    frame_sha256: str
    kind: WireKind
    correlation_id: str
    envelope_digest: str

    def __post_init__(self) -> None:
        if self.ordinal < 0:
            raise ParityTranscriptError("wire transcript ordinal must be nonnegative")
        try:
            frame = self.frame_text.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ParityTranscriptError("wire transcript frame must be UTF-8 encodable") from exc
        try:
            envelope = decode_wire_frame(frame)
        except ValueError as exc:
            raise ParityTranscriptError(
                f"invalid canonical frame at ordinal {self.ordinal}"
            ) from exc
        if not _is_sha256(self.frame_sha256) or self.frame_sha256 != _sha256_bytes(frame):
            raise ParityTranscriptError("wire transcript frame SHA-256 mismatch")
        if self.kind is not envelope.kind:
            raise ParityTranscriptError("wire transcript kind disagrees with decoded frame")
        if self.correlation_id != envelope.correlation_id:
            raise ParityTranscriptError("wire transcript correlation disagrees with decoded frame")
        if not _is_sha256(self.envelope_digest) or self.envelope_digest != envelope.digest():
            raise ParityTranscriptError("wire transcript envelope digest mismatch")

    @classmethod
    def capture(
        cls,
        ordinal: int,
        direction: WireDirection,
        frame: bytes,
    ) -> "WireTranscriptRecord":
        envelope = decode_wire_frame(frame)
        try:
            text = frame.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ParityTranscriptError("wire transcript frame must be valid UTF-8") from exc
        return cls(
            ordinal=ordinal,
            direction=direction,
            frame_text=text,
            frame_sha256=_sha256_bytes(frame),
            kind=envelope.kind,
            correlation_id=envelope.correlation_id,
            envelope_digest=envelope.digest(),
        )

    @property
    def frame_bytes(self) -> bytes:
        return self.frame_text.encode("utf-8")

    def as_dict(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "direction": self.direction.value,
            "frame_text": self.frame_text,
            "frame_sha256": self.frame_sha256,
            "kind": self.kind.value,
            "correlation_id": self.correlation_id,
            "envelope_digest": self.envelope_digest,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "WireTranscriptRecord":
        try:
            return cls(
                ordinal=int(payload["ordinal"]),
                direction=WireDirection(str(payload["direction"])),
                frame_text=str(payload["frame_text"]),
                frame_sha256=str(payload["frame_sha256"]),
                kind=WireKind(str(payload["kind"])),
                correlation_id=str(payload["correlation_id"]),
                envelope_digest=str(payload["envelope_digest"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, ParityTranscriptError):
                raise
            raise ParityTranscriptError("malformed wire transcript record") from exc


@dataclass(frozen=True, slots=True)
class ParityWireTranscript:
    """Complete deterministic ordered transcript of line writes and reads."""

    records: tuple[WireTranscriptRecord, ...]
    schema: str = WIRE_TRANSCRIPT_SCHEMA
    version: int = WIRE_TRANSCRIPT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != WIRE_TRANSCRIPT_SCHEMA or self.version != WIRE_TRANSCRIPT_SCHEMA_VERSION:
            raise ParityTranscriptError("unsupported parity-wire-transcript schema")
        if not self.records:
            raise ParityTranscriptError("wire transcript must contain at least one exchange")
        if len(self.records) % 2:
            raise ParityTranscriptError("wire transcript must end after a device response")
        ordinals = tuple(record.ordinal for record in self.records)
        if ordinals != tuple(range(len(self.records))):
            raise ParityTranscriptError("wire transcript ordinals must be contiguous from zero")

        for index in range(0, len(self.records), 2):
            request = self.records[index]
            response = self.records[index + 1]
            if request.direction is not WireDirection.HOST_TO_DEVICE:
                raise ParityTranscriptError("wire transcript exchange must begin host_to_device")
            if response.direction is not WireDirection.DEVICE_TO_HOST:
                raise ParityTranscriptError("wire transcript exchange must end device_to_host")
            if request.correlation_id != response.correlation_id:
                raise ParityTranscriptError("wire transcript response correlation mismatch")
            if request.kind is WireKind.CAPABILITIES_REQUEST:
                expected = WireKind.CAPABILITIES_RESPONSE
            elif request.kind is WireKind.PARITY_REQUEST:
                expected = WireKind.PARITY_RESPONSE
            else:
                raise ParityTranscriptError("wire transcript host record is not a request kind")
            if response.kind is not expected:
                raise ParityTranscriptError("wire transcript response kind disagrees with request")

    @property
    def exchange_count(self) -> int:
        return len(self.records) // 2

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "record_count": len(self.records),
            "exchange_count": self.exchange_count,
            "records": [record.as_dict() for record in self.records],
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256_text(self.canonical_json())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityWireTranscript":
        raw_records = payload.get("records")
        if not isinstance(raw_records, list):
            raise ParityTranscriptError("wire transcript records must be a list")
        transcript = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            records=tuple(WireTranscriptRecord.from_dict(item) for item in raw_records),
        )
        claimed_records = payload.get("record_count")
        if claimed_records is not None and int(claimed_records) != len(transcript.records):
            raise ParityTranscriptError("wire transcript record_count mismatch")
        claimed_exchanges = payload.get("exchange_count")
        if claimed_exchanges is not None and int(claimed_exchanges) != transcript.exchange_count:
            raise ParityTranscriptError("wire transcript exchange_count mismatch")
        return transcript

    @classmethod
    def from_json(cls, text: str) -> "ParityWireTranscript":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParityTranscriptError("wire transcript is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ParityTranscriptError("wire transcript JSON root must be an object")
        return cls.from_dict(payload)


class RecordingParityLineIO:
    """Record exact successful line traffic while delegating to another line channel."""

    def __init__(self, line_io: ParityLineIO) -> None:
        self._line_io = line_io
        self._records: list[WireTranscriptRecord] = []
        self._expect_write = True

    def _append(self, direction: WireDirection, frame: bytes) -> None:
        self._records.append(
            WireTranscriptRecord.capture(len(self._records), direction, frame)
        )

    def write_line(self, frame: bytes) -> None:
        if not self._expect_write:
            raise ParityTranscriptError("recording line channel requires read after write")
        decode_wire_frame(frame)
        self._line_io.write_line(frame)
        self._append(WireDirection.HOST_TO_DEVICE, frame)
        self._expect_write = False

    def read_line(self) -> bytes:
        if self._expect_write:
            raise ParityTranscriptError("recording line channel requires write before read")
        frame = self._line_io.read_line()
        decode_wire_frame(frame)
        self._append(WireDirection.DEVICE_TO_HOST, frame)
        self._expect_write = True
        return frame

    def transcript(self) -> ParityWireTranscript:
        if not self._expect_write:
            raise ParityTranscriptError("cannot finalize transcript with unread device response")
        return ParityWireTranscript(tuple(self._records))


class ReplayParityLineIO:
    """Replay a saved transcript while requiring exact host request bytes."""

    def __init__(self, transcript: ParityWireTranscript) -> None:
        self._transcript = transcript
        self._cursor = 0

    @property
    def consumed_records(self) -> int:
        return self._cursor

    def _next_record(self) -> WireTranscriptRecord:
        if self._cursor >= len(self._transcript.records):
            raise ParityTranscriptError("wire replay received traffic after transcript end")
        return self._transcript.records[self._cursor]

    def write_line(self, frame: bytes) -> None:
        record = self._next_record()
        if record.direction is not WireDirection.HOST_TO_DEVICE:
            raise ParityTranscriptError(
                "wire replay expected device read before another host write"
            )
        if frame != record.frame_bytes:
            raise ParityTranscriptError("wire replay host request bytes disagree with transcript")
        self._cursor += 1

    def read_line(self) -> bytes:
        record = self._next_record()
        if record.direction is not WireDirection.DEVICE_TO_HOST:
            raise ParityTranscriptError("wire replay expected host write before device read")
        self._cursor += 1
        return record.frame_bytes

    def assert_consumed(self) -> None:
        if self._cursor != len(self._transcript.records):
            raise ParityTranscriptError(
                f"wire replay consumed {self._cursor} of {len(self._transcript.records)} records"
            )


def transcript_for_report(report: ConformanceReport) -> ParityWireTranscript:
    """Reconstruct the exact canonical wire traffic implied by a conformance report."""
    frames: list[tuple[WireDirection, bytes]] = []

    capability_request = ParityWireEnvelope(
        kind=WireKind.CAPABILITIES_REQUEST,
        correlation_id=CAPABILITIES_CORRELATION,
        payload={},
    )
    capability_response = ParityWireEnvelope(
        kind=WireKind.CAPABILITIES_RESPONSE,
        correlation_id=CAPABILITIES_CORRELATION,
        payload=report.capabilities.as_dict(),
    )
    frames.extend(
        (
            (WireDirection.HOST_TO_DEVICE, encode_wire_frame(capability_request)),
            (WireDirection.DEVICE_TO_HOST, encode_wire_frame(capability_response)),
        )
    )

    for record in report.records:
        if not report.capabilities.supports(record.request.vector):
            continue
        correlation = parity_request_correlation(record.request)
        request = ParityWireEnvelope(
            kind=WireKind.PARITY_REQUEST,
            correlation_id=correlation,
            payload=record.request.as_dict(),
        )
        response = ParityWireEnvelope(
            kind=WireKind.PARITY_RESPONSE,
            correlation_id=correlation,
            payload=record.response.as_dict(),
        )
        frames.extend(
            (
                (WireDirection.HOST_TO_DEVICE, encode_wire_frame(request)),
                (WireDirection.DEVICE_TO_HOST, encode_wire_frame(response)),
            )
        )

    return ParityWireTranscript(
        tuple(
            WireTranscriptRecord.capture(index, direction, frame)
            for index, (direction, frame) in enumerate(frames)
        )
    )


def validate_report_transcript(
    report: ConformanceReport,
    transcript: ParityWireTranscript,
    *,
    context: str = "wire evidence",
    report_name: str = "conformance report",
) -> None:
    """Require a transcript to equal the canonical wire traffic implied by a report."""
    expected = transcript_for_report(report)
    if transcript.canonical_json() != expected.canonical_json():
        raise ParityTranscriptError(
            f"{context} transcript disagrees with {report_name} wire traffic"
        )


@dataclass(frozen=True, slots=True)
class ParityBenchRun:
    """One campaign run plus the exact wire transcript that produced its report."""

    campaign_run: ParityCampaignRun
    transcript: ParityWireTranscript
    schema: str = BENCH_RUN_SCHEMA
    version: int = BENCH_RUN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != BENCH_RUN_SCHEMA or self.version != BENCH_RUN_SCHEMA_VERSION:
            raise ParityTranscriptError("unsupported parity-bench-run schema")
        validate_report_transcript(
            self.campaign_run.report,
            self.transcript,
            context="bench run",
            report_name="campaign report",
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "campaign_run_digest": self.campaign_run.digest(),
            "campaign_run": self.campaign_run.as_dict(),
            "transcript_digest": self.transcript.digest(),
            "transcript": self.transcript.as_dict(),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256_text(self.canonical_json())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityBenchRun":
        run_payload = payload.get("campaign_run")
        transcript_payload = payload.get("transcript")
        if not isinstance(run_payload, Mapping) or not isinstance(transcript_payload, Mapping):
            raise ParityTranscriptError("bench run requires campaign_run and transcript objects")
        bench = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            campaign_run=ParityCampaignRun.from_dict(run_payload),
            transcript=ParityWireTranscript.from_dict(transcript_payload),
        )
        claimed_run = payload.get("campaign_run_digest")
        if claimed_run is not None and claimed_run != bench.campaign_run.digest():
            raise ParityTranscriptError("bench run campaign_run_digest mismatch")
        claimed_transcript = payload.get("transcript_digest")
        if claimed_transcript is not None and claimed_transcript != bench.transcript.digest():
            raise ParityTranscriptError("bench run transcript_digest mismatch")
        return bench

    @classmethod
    def from_json(cls, text: str) -> "ParityBenchRun":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParityTranscriptError("bench run is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ParityTranscriptError("bench run JSON root must be an object")
        return cls.from_dict(payload)


def replay_bench_run(bench: ParityBenchRun) -> ParityCampaignRun:
    """Replay a bench bundle through the normal wire transport and require report identity."""
    line_io = ReplayParityLineIO(bench.transcript)
    transport = JsonLineParityTransport(line_io)
    replayed = run_parity_campaign(
        transport,
        bench.campaign_run.campaign,
        session_id=bench.campaign_run.report.session_id,
    )
    line_io.assert_consumed()
    if replayed.canonical_json() != bench.campaign_run.canonical_json():
        raise ParityTranscriptError("wire replay campaign report disagrees with saved bench run")
    return replayed
