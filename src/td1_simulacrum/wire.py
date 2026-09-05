"""Deterministic JSON Lines transport for TD-1 parity contracts.

The wire layer carries existing parity schemas across a byte-oriented line link.
It defines framing and correlation only; it does not redefine arithmetic,
capabilities, conformance, physical voltages, or TD-1 instruction encoding.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .parity import (
    ParityCapabilities,
    ParityRequest,
    ParityResponse,
    ParityTransport,
)

WIRE_SCHEMA = "td1.parity-wire"
WIRE_SCHEMA_VERSION = 1
WIRE_MAX_FRAME_BYTES = 65_536
WIRE_ENCODING = "utf-8-jsonl-canonical/v1"

BENCH_TELEMETRY_KEYS = (
    "board_revision",
    "comparator_code",
    "sample_count",
    "settle_us",
    "temperature_millic",
    "voltage_uv",
)


class ParityWireError(ValueError):
    """Raised when a parity wire frame or exchange violates the v1 contract."""


class WireKind(str, Enum):
    CAPABILITIES_REQUEST = "capabilities_request"
    CAPABILITIES_RESPONSE = "capabilities_response"
    PARITY_REQUEST = "parity_request"
    PARITY_RESPONSE = "parity_response"


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _json_exact(actual: object, expected: object) -> bool:
    """Compare JSON values without Python's bool/int coercion semantics."""
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        if not isinstance(expected, dict) or actual.keys() != expected.keys():
            return False
        return all(_json_exact(actual[key], expected[key]) for key in actual)
    if isinstance(actual, list):
        if not isinstance(expected, list) or len(actual) != len(expected):
            return False
        return all(
            _json_exact(left, right)
            for left, right in zip(actual, expected, strict=True)
        )
    return actual == expected


def _require_canonical_payload(
    raw: Mapping[str, object],
    canonical: Mapping[str, object],
    *,
    label: str,
) -> None:
    """Reject nested parity payloads that rely on parser normalization.

    Frame canonicality alone is insufficient because a byte-canonical JSON object
    can still encode a schema integer as a string, a boolean as an integer, omit a
    canonical default field, or provide a list that the parity model normalizes.
    The wire contract therefore requires the parsed parity object to reproduce the
    exact same JSON values *and JSON types* as the received nested payload.
    """
    if not _json_exact(dict(raw), dict(canonical)):
        raise ParityWireError(
            f"{label} payload must use canonical parity schema values and JSON types"
        )


def parity_request_correlation(request: ParityRequest) -> str:
    """Return the deterministic v1 correlation ID for one parity request."""
    digest = hashlib.sha256(request.canonical_json().encode("utf-8")).hexdigest()
    return f"REQ-{digest[:24]}"


CAPABILITIES_CORRELATION = "CAPS-v1"


@dataclass(frozen=True, slots=True)
class ParityWireEnvelope:
    """One canonical request or response frame on the parity wire."""

    kind: WireKind
    correlation_id: str
    payload: Mapping[str, object]
    schema: str = WIRE_SCHEMA
    version: int = WIRE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != WIRE_SCHEMA or self.version != WIRE_SCHEMA_VERSION:
            raise ParityWireError("unsupported parity-wire schema")
        if not self.correlation_id.strip():
            raise ParityWireError("wire correlation_id must not be empty")
        if not isinstance(self.payload, Mapping):
            raise ParityWireError("wire payload must be an object")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "kind": self.kind.value,
            "correlation_id": self.correlation_id,
            "payload": dict(self.payload),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityWireEnvelope":
        raw_payload = payload.get("payload")
        if not isinstance(raw_payload, Mapping):
            raise ParityWireError("wire payload must be an object")
        try:
            schema = str(payload["schema"])
            version = int(payload["version"])
            kind = WireKind(str(payload["kind"]))
            correlation_id = str(payload["correlation_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ParityWireError("malformed parity-wire envelope fields") from exc
        return cls(
            schema=schema,
            version=version,
            kind=kind,
            correlation_id=correlation_id,
            payload=raw_payload,
        )


def encode_wire_frame(
    envelope: ParityWireEnvelope,
    *,
    max_frame_bytes: int = WIRE_MAX_FRAME_BYTES,
) -> bytes:
    """Encode one envelope as canonical UTF-8 JSON followed by exactly one LF."""
    if max_frame_bytes <= 1:
        raise ParityWireError("max_frame_bytes must allow payload plus newline")
    frame = (envelope.canonical_json() + "\n").encode("utf-8")
    if len(frame) > max_frame_bytes:
        raise ParityWireError("parity-wire frame exceeds maximum size")
    return frame


def decode_wire_frame(
    frame: bytes,
    *,
    max_frame_bytes: int = WIRE_MAX_FRAME_BYTES,
) -> ParityWireEnvelope:
    """Decode and require canonical JSON Lines framing."""
    if not isinstance(frame, bytes):
        raise ParityWireError("parity-wire frame must be bytes")
    if not frame:
        raise ParityWireError("parity-wire frame must not be empty")
    if len(frame) > max_frame_bytes:
        raise ParityWireError("parity-wire frame exceeds maximum size")
    if not frame.endswith(b"\n") or frame.endswith(b"\r\n"):
        raise ParityWireError("parity-wire frame must end with exactly one LF")
    body = frame[:-1]
    if not body or b"\n" in body or b"\r" in body:
        raise ParityWireError("parity-wire frame must contain exactly one JSON line")
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ParityWireError("parity-wire frame must be valid UTF-8") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ParityWireError("parity-wire frame is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ParityWireError("parity-wire JSON root must be an object")
    envelope = ParityWireEnvelope.from_dict(payload)
    if text != envelope.canonical_json():
        raise ParityWireError("parity-wire frame must use canonical JSON serialization")
    return envelope


class ParityLineIO(Protocol):
    """Minimal synchronous byte-line channel implemented by future serial adapters."""

    def write_line(self, frame: bytes) -> None: ...

    def read_line(self) -> bytes: ...


@dataclass(frozen=True, slots=True)
class BenchTelemetry:
    """Optional convention for first-bench measurement telemetry.

    These fields are metadata only in wire v1. They do not alter arithmetic
    pass/fail evaluation in the parity harness. `voltage_uv` is signed relative to
    the bench/device reference; wire v1 assumes neither single-supply nor bipolar
    physical ternary levels.
    """

    voltage_uv: int | None = None
    settle_us: int | None = None
    comparator_code: str | None = None
    sample_count: int | None = None
    board_revision: str | None = None
    temperature_millic: int | None = None

    def __post_init__(self) -> None:
        if self.settle_us is not None and self.settle_us < 0:
            raise ParityWireError("settle_us must be nonnegative")
        if self.sample_count is not None and self.sample_count <= 0:
            raise ParityWireError("sample_count must be positive")
        if self.comparator_code is not None and not self.comparator_code.strip():
            raise ParityWireError("comparator_code must not be empty")
        if self.board_revision is not None and not self.board_revision.strip():
            raise ParityWireError("board_revision must not be empty")

    def as_pairs(self) -> tuple[tuple[str, int | str], ...]:
        values: dict[str, int | str] = {}
        if self.voltage_uv is not None:
            values["voltage_uv"] = self.voltage_uv
        if self.settle_us is not None:
            values["settle_us"] = self.settle_us
        if self.comparator_code is not None:
            values["comparator_code"] = self.comparator_code
        if self.sample_count is not None:
            values["sample_count"] = self.sample_count
        if self.board_revision is not None:
            values["board_revision"] = self.board_revision
        if self.temperature_millic is not None:
            values["temperature_millic"] = self.temperature_millic
        return tuple(sorted(values.items()))

    @classmethod
    def from_pairs(cls, pairs: tuple[tuple[str, int | str], ...]) -> "BenchTelemetry":
        keys = tuple(key for key, _ in pairs)
        if len(set(keys)) != len(keys):
            raise ParityWireError("bench telemetry keys must be unique")
        values = dict(pairs)
        unknown = set(values) - set(BENCH_TELEMETRY_KEYS)
        if unknown:
            raise ParityWireError(f"unknown bench telemetry key(s): {sorted(unknown)!r}")

        def integer(key: str) -> int | None:
            value = values.get(key)
            if value is None:
                return None
            if type(value) is not int:
                raise ParityWireError(f"bench telemetry {key} must be an integer")
            return value

        def text(key: str) -> str | None:
            value = values.get(key)
            if value is None:
                return None
            if not isinstance(value, str):
                raise ParityWireError(f"bench telemetry {key} must be a string")
            return value

        return cls(
            voltage_uv=integer("voltage_uv"),
            settle_us=integer("settle_us"),
            comparator_code=text("comparator_code"),
            sample_count=integer("sample_count"),
            board_revision=text("board_revision"),
            temperature_millic=integer("temperature_millic"),
        )


class ParityWireDevice:
    """Reference device-side dispatcher around an existing parity target."""

    def __init__(self, target: ParityTransport) -> None:
        self._target = target

    def handle_frame(self, frame: bytes) -> bytes:
        envelope = decode_wire_frame(frame)
        if envelope.kind is WireKind.CAPABILITIES_REQUEST:
            if envelope.correlation_id != CAPABILITIES_CORRELATION:
                raise ParityWireError("capabilities request correlation mismatch")
            if dict(envelope.payload):
                raise ParityWireError("capabilities request payload must be empty")
            response = ParityWireEnvelope(
                kind=WireKind.CAPABILITIES_RESPONSE,
                correlation_id=envelope.correlation_id,
                payload=self._target.capabilities().as_dict(),
            )
            return encode_wire_frame(response)

        if envelope.kind is WireKind.PARITY_REQUEST:
            try:
                request = ParityRequest.from_dict(envelope.payload)
            except (KeyError, TypeError, ValueError) as exc:
                raise ParityWireError(
                    "parity request payload violates canonical parity schema"
                ) from exc
            _require_canonical_payload(
                envelope.payload,
                request.as_dict(),
                label="parity request",
            )
            expected = parity_request_correlation(request)
            if envelope.correlation_id != expected:
                raise ParityWireError("parity request correlation mismatch")
            response_payload = self._target.exchange(request)
            response = ParityWireEnvelope(
                kind=WireKind.PARITY_RESPONSE,
                correlation_id=envelope.correlation_id,
                payload=response_payload.as_dict(),
            )
            return encode_wire_frame(response)

        raise ParityWireError(f"device cannot consume wire message kind {envelope.kind.value!r}")


class InMemoryParityLineIO:
    """Synchronous in-memory line channel exercising the exact wire codec in CI."""

    def __init__(self, device: ParityWireDevice) -> None:
        self._device = device
        self._pending: bytes | None = None

    def write_line(self, frame: bytes) -> None:
        if self._pending is not None:
            raise ParityWireError("in-memory wire channel already has an unread response")
        self._pending = self._device.handle_frame(frame)

    def read_line(self) -> bytes:
        if self._pending is None:
            raise ParityWireError("in-memory wire channel has no pending response")
        response = self._pending
        self._pending = None
        return response


class JsonLineParityTransport:
    """Host-side `ParityTransport` over canonical byte-oriented JSON Lines."""

    def __init__(self, line_io: ParityLineIO) -> None:
        self._line_io = line_io
        self._cached_capabilities: ParityCapabilities | None = None

    def _exchange_envelope(
        self,
        request: ParityWireEnvelope,
        *,
        expected_kind: WireKind,
    ) -> ParityWireEnvelope:
        self._line_io.write_line(encode_wire_frame(request))
        response = decode_wire_frame(self._line_io.read_line())
        if response.kind is not expected_kind:
            raise ParityWireError(
                f"expected wire kind {expected_kind.value!r}, got {response.kind.value!r}"
            )
        if response.correlation_id != request.correlation_id:
            raise ParityWireError("wire response correlation_id does not match request")
        return response

    def capabilities(self) -> ParityCapabilities:
        if self._cached_capabilities is None:
            request = ParityWireEnvelope(
                kind=WireKind.CAPABILITIES_REQUEST,
                correlation_id=CAPABILITIES_CORRELATION,
                payload={},
            )
            response = self._exchange_envelope(
                request,
                expected_kind=WireKind.CAPABILITIES_RESPONSE,
            )
            try:
                capabilities = ParityCapabilities.from_dict(response.payload)
            except (KeyError, TypeError, ValueError) as exc:
                raise ParityWireError(
                    "capabilities response payload violates canonical parity schema"
                ) from exc
            _require_canonical_payload(
                response.payload,
                capabilities.as_dict(),
                label="capabilities response",
            )
            self._cached_capabilities = capabilities
        return self._cached_capabilities

    def exchange(self, request: ParityRequest) -> ParityResponse:
        correlation = parity_request_correlation(request)
        envelope = ParityWireEnvelope(
            kind=WireKind.PARITY_REQUEST,
            correlation_id=correlation,
            payload=request.as_dict(),
        )
        response_envelope = self._exchange_envelope(
            envelope,
            expected_kind=WireKind.PARITY_RESPONSE,
        )
        try:
            response = ParityResponse.from_dict(response_envelope.payload)
        except (KeyError, TypeError, ValueError) as exc:
            raise ParityWireError(
                "parity response payload violates canonical parity schema"
            ) from exc
        _require_canonical_payload(
            response_envelope.payload,
            response.as_dict(),
            label="parity response",
        )
        if response.session_id != request.session_id:
            raise ParityWireError("wire parity response session_id mismatch")
        if response.sequence != request.sequence:
            raise ParityWireError("wire parity response sequence mismatch")
        if response.vector_id != request.vector.vector_id:
            raise ParityWireError("wire parity response vector_id mismatch")
        return response
