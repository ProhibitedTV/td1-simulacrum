"""Transport-neutral emulator-to-hardware parity contracts for TD-1.

The parity layer defines what a physical ternary subsystem must prove before it
can replace an emulated subsystem. It deliberately does not choose USB, serial,
CAN, GPIO, Ethernet, or any other physical transport.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .ternary import TernaryWord, representable_range

CAPABILITY_SCHEMA = "td1.parity-capabilities"
CAPABILITY_SCHEMA_VERSION = 1
REQUEST_SCHEMA = "td1.parity-request"
REQUEST_SCHEMA_VERSION = 1
RESPONSE_SCHEMA = "td1.parity-response"
RESPONSE_SCHEMA_VERSION = 1
REPORT_SCHEMA = "td1.parity-report"
REPORT_SCHEMA_VERSION = 1


class ParityError(ValueError):
    """Base exception for parity schema and conformance failures."""


class ParityProtocolError(ParityError):
    """Raised when a transport violates the request/response contract."""


class ParityOperation(str, Enum):
    TRIT_HOLD = "trit_hold"
    REGISTER_LOAD = "register_load"
    NEGATE = "negate"
    ADD = "add"
    SUB = "sub"


class ParityStatus(str, Enum):
    OK = "ok"
    UNSUPPORTED = "unsupported"
    FAULT = "fault"
    TIMEOUT = "timeout"
    ERROR = "error"


_OPERAND_COUNTS: dict[ParityOperation, int] = {
    ParityOperation.TRIT_HOLD: 1,
    ParityOperation.REGISTER_LOAD: 1,
    ParityOperation.NEGATE: 1,
    ParityOperation.ADD: 2,
    ParityOperation.SUB: 2,
}


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_payload(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _normalize_value(text: str, width: int) -> str:
    if width <= 0:
        raise ParityError("parity width must be positive")
    word = TernaryWord.parse(text)
    if word.width != width:
        raise ParityError(f"expected {width} trits, got {word.width}")
    return str(word)


def ternary_state_digest(width: int, value: str) -> str:
    """Digest one observable ternary slice state independent of transport."""
    normalized = _normalize_value(value, width)
    return _sha256_payload({"width": width, "value": normalized})


def _expected_value(
    operation: ParityOperation,
    width: int,
    operands: Sequence[str],
) -> str:
    normalized = tuple(_normalize_value(value, width) for value in operands)
    expected_count = _OPERAND_COUNTS[operation]
    if len(normalized) != expected_count:
        raise ParityError(
            f"{operation.value} requires {expected_count} operand(s), got {len(normalized)}"
        )

    left = TernaryWord.parse(normalized[0])
    if operation in {ParityOperation.TRIT_HOLD, ParityOperation.REGISTER_LOAD}:
        return str(left)
    if operation is ParityOperation.NEGATE:
        return str(-left)

    right = TernaryWord.parse(normalized[1])
    if operation is ParityOperation.ADD:
        return str(left + right)
    if operation is ParityOperation.SUB:
        return str(left - right)
    raise ParityError(f"unimplemented parity operation {operation.value}")


@dataclass(frozen=True, slots=True)
class ParityVector:
    """One deterministic conformance stimulus and expected ternary result."""

    vector_id: str
    operation: ParityOperation
    width: int
    operands: tuple[str, ...]
    expected_value: str
    note: str = ""

    def __post_init__(self) -> None:
        if not self.vector_id.strip():
            raise ParityError("vector_id must not be empty")
        if self.operation is ParityOperation.TRIT_HOLD and self.width != 1:
            raise ParityError("trit_hold vectors must have width 1")
        normalized = tuple(_normalize_value(value, self.width) for value in self.operands)
        expected = _normalize_value(self.expected_value, self.width)
        reference_expected = _expected_value(self.operation, self.width, normalized)
        if expected != reference_expected:
            raise ParityError(
                f"vector {self.vector_id} expected value disagrees with reference semantics"
            )
        object.__setattr__(self, "operands", normalized)
        object.__setattr__(self, "expected_value", expected)

    @classmethod
    def create(
        cls,
        vector_id: str,
        operation: ParityOperation,
        width: int,
        operands: Sequence[str],
        *,
        note: str = "",
    ) -> "ParityVector":
        normalized = tuple(_normalize_value(value, width) for value in operands)
        return cls(
            vector_id=vector_id,
            operation=operation,
            width=width,
            operands=normalized,
            expected_value=_expected_value(operation, width, normalized),
            note=note,
        )

    @property
    def expected_state_digest(self) -> str:
        return ternary_state_digest(self.width, self.expected_value)

    def as_dict(self) -> dict[str, object]:
        return {
            "vector_id": self.vector_id,
            "operation": self.operation.value,
            "width": self.width,
            "operands": list(self.operands),
            "expected_value": self.expected_value,
            "expected_state_digest": self.expected_state_digest,
            "note": self.note,
        }

    def digest(self) -> str:
        return _sha256_payload(self.as_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityVector":
        raw_operands = payload.get("operands")
        if not isinstance(raw_operands, list):
            raise ParityError("parity vector operands must be a list")
        vector = cls(
            vector_id=str(payload["vector_id"]),
            operation=ParityOperation(str(payload["operation"])),
            width=int(payload["width"]),
            operands=tuple(str(item) for item in raw_operands),
            expected_value=str(payload["expected_value"]),
            note=str(payload.get("note", "")),
        )
        claimed_digest = payload.get("expected_state_digest")
        if claimed_digest is not None and str(claimed_digest) != vector.expected_state_digest:
            raise ParityError(f"vector {vector.vector_id} expected-state digest mismatch")
        return vector


@dataclass(frozen=True, slots=True)
class ParityCapabilities:
    """Transport-neutral hardware capability advertisement."""

    target_id: str
    operations: tuple[ParityOperation, ...]
    max_width: int
    protocol_versions: tuple[int, ...] = (1,)
    telemetry_keys: tuple[str, ...] = ()
    schema: str = CAPABILITY_SCHEMA
    version: int = CAPABILITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != CAPABILITY_SCHEMA or self.version != CAPABILITY_SCHEMA_VERSION:
            raise ParityError("unsupported parity capability schema")
        if not self.target_id.strip():
            raise ParityError("parity target_id must not be empty")
        if self.max_width <= 0:
            raise ParityError("parity target max_width must be positive")
        if self.version not in self.protocol_versions:
            raise ParityError("target does not advertise the current parity protocol version")
        operations = tuple(sorted(set(self.operations), key=lambda item: item.value))
        versions = tuple(sorted(set(int(item) for item in self.protocol_versions)))
        telemetry = tuple(sorted(set(str(item) for item in self.telemetry_keys)))
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "protocol_versions", versions)
        object.__setattr__(self, "telemetry_keys", telemetry)

    def supports(self, vector: ParityVector) -> bool:
        return vector.operation in self.operations and vector.width <= self.max_width

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "target_id": self.target_id,
            "operations": [item.value for item in self.operations],
            "max_width": self.max_width,
            "protocol_versions": list(self.protocol_versions),
            "telemetry_keys": list(self.telemetry_keys),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256_payload(self.as_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityCapabilities":
        operations = payload.get("operations")
        versions = payload.get("protocol_versions")
        telemetry = payload.get("telemetry_keys", [])
        if not isinstance(operations, list) or not isinstance(versions, list):
            raise ParityError("capability operations/protocol_versions must be lists")
        if not isinstance(telemetry, list):
            raise ParityError("capability telemetry_keys must be a list")
        return cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            target_id=str(payload["target_id"]),
            operations=tuple(ParityOperation(str(item)) for item in operations),
            max_width=int(payload["max_width"]),
            protocol_versions=tuple(int(item) for item in versions),
            telemetry_keys=tuple(str(item) for item in telemetry),
        )


@dataclass(frozen=True, slots=True)
class ParityRequest:
    session_id: str
    sequence: int
    vector: ParityVector
    schema: str = REQUEST_SCHEMA
    version: int = REQUEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != REQUEST_SCHEMA or self.version != REQUEST_SCHEMA_VERSION:
            raise ParityError("unsupported parity request schema")
        if not self.session_id.strip() or self.sequence < 0:
            raise ParityError("parity request requires session_id and nonnegative sequence")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "session_id": self.session_id,
            "sequence": self.sequence,
            "vector": self.vector.as_dict(),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256_payload(self.as_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityRequest":
        vector = payload.get("vector")
        if not isinstance(vector, Mapping):
            raise ParityError("parity request vector must be an object")
        return cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            session_id=str(payload["session_id"]),
            sequence=int(payload["sequence"]),
            vector=ParityVector.from_dict(vector),
        )


@dataclass(frozen=True, slots=True)
class ParityResponse:
    session_id: str
    sequence: int
    vector_id: str
    status: ParityStatus
    observed_value: str | None = None
    observed_state_digest: str | None = None
    detail: str = ""
    telemetry: tuple[tuple[str, int | str], ...] = ()
    schema: str = RESPONSE_SCHEMA
    version: int = RESPONSE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != RESPONSE_SCHEMA or self.version != RESPONSE_SCHEMA_VERSION:
            raise ParityError("unsupported parity response schema")
        if not self.session_id.strip() or self.sequence < 0 or not self.vector_id.strip():
            raise ParityError("invalid parity response identity")
        telemetry = tuple(sorted(self.telemetry, key=lambda item: item[0]))
        if len({key for key, _ in telemetry}) != len(telemetry):
            raise ParityError("parity telemetry keys must be unique")
        object.__setattr__(self, "telemetry", telemetry)
        if self.status is ParityStatus.OK:
            if self.observed_value is None or self.observed_state_digest is None:
                raise ParityError("OK parity response requires observed value and state digest")
        elif self.observed_value is not None and self.observed_state_digest is None:
            raise ParityError("observed value requires observed_state_digest")

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": self.schema,
            "version": self.version,
            "session_id": self.session_id,
            "sequence": self.sequence,
            "vector_id": self.vector_id,
            "status": self.status.value,
            "detail": self.detail,
            "telemetry": {key: value for key, value in self.telemetry},
        }
        if self.observed_value is not None:
            payload["observed_value"] = self.observed_value
        if self.observed_state_digest is not None:
            payload["observed_state_digest"] = self.observed_state_digest
        return payload

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256_payload(self.as_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityResponse":
        telemetry_payload = payload.get("telemetry", {})
        if not isinstance(telemetry_payload, Mapping):
            raise ParityError("parity response telemetry must be an object")
        telemetry: list[tuple[str, int | str]] = []
        for key, value in telemetry_payload.items():
            if not isinstance(value, (int, str)):
                raise ParityError("parity telemetry values must be integers or strings")
            telemetry.append((str(key), value))
        return cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            session_id=str(payload["session_id"]),
            sequence=int(payload["sequence"]),
            vector_id=str(payload["vector_id"]),
            status=ParityStatus(str(payload["status"])),
            observed_value=(
                str(payload["observed_value"])
                if payload.get("observed_value") is not None
                else None
            ),
            observed_state_digest=(
                str(payload["observed_state_digest"])
                if payload.get("observed_state_digest") is not None
                else None
            ),
            detail=str(payload.get("detail", "")),
            telemetry=tuple(telemetry),
        )


class ParityTransport(Protocol):
    """Minimal interface implemented by serial/USB/GPIO/etc. adapters later."""

    def capabilities(self) -> ParityCapabilities: ...

    def exchange(self, request: ParityRequest) -> ParityResponse: ...


@dataclass(frozen=True, slots=True)
class ParityExchangeRecord:
    request: ParityRequest
    response: ParityResponse
    passed: bool
    discrepancy: str = ""

    def __post_init__(self) -> None:
        vector = self.request.vector
        response = self.response
        if response.session_id != self.request.session_id:
            raise ParityProtocolError("response session_id does not match request")
        if response.sequence != self.request.sequence:
            raise ParityProtocolError("response sequence does not match request")
        if response.vector_id != vector.vector_id:
            raise ParityProtocolError("response vector_id does not match request")

        expected_pass = False
        expected_discrepancy = ""
        if response.status is not ParityStatus.OK:
            expected_discrepancy = f"transport status: {response.status.value}"
            if response.detail:
                expected_discrepancy += f" ({response.detail})"
        elif response.observed_value is None or response.observed_state_digest is None:
            expected_discrepancy = "OK response omitted observable state"
        else:
            try:
                observed = _normalize_value(response.observed_value, vector.width)
            except ParityError as exc:
                expected_discrepancy = f"invalid observed ternary value: {exc}"
            else:
                actual_digest = ternary_state_digest(vector.width, observed)
                if response.observed_state_digest != actual_digest:
                    expected_discrepancy = "observed-state digest does not match observed value"
                elif observed != vector.expected_value:
                    expected_discrepancy = (
                        f"value mismatch: expected {vector.expected_value}, observed {observed}"
                    )
                elif actual_digest != vector.expected_state_digest:
                    expected_discrepancy = "state digest mismatch against reference"
                else:
                    expected_pass = True

        if self.passed != expected_pass:
            raise ParityProtocolError(
                "record pass/fail flag disagrees with deterministic evaluation"
            )
        if self.discrepancy != expected_discrepancy:
            raise ParityProtocolError(
                "record discrepancy text disagrees with deterministic evaluation"
            )

    @classmethod
    def evaluate(
        cls,
        request: ParityRequest,
        response: ParityResponse,
    ) -> "ParityExchangeRecord":
        vector = request.vector
        if response.status is not ParityStatus.OK:
            discrepancy = f"transport status: {response.status.value}"
            if response.detail:
                discrepancy += f" ({response.detail})"
            return cls(request, response, False, discrepancy)

        if response.observed_value is None or response.observed_state_digest is None:
            return cls(request, response, False, "OK response omitted observable state")

        try:
            observed = _normalize_value(response.observed_value, vector.width)
        except ParityError as exc:
            return cls(
                request,
                response,
                False,
                f"invalid observed ternary value: {exc}",
            )

        actual_digest = ternary_state_digest(vector.width, observed)
        if response.observed_state_digest != actual_digest:
            return cls(
                request,
                response,
                False,
                "observed-state digest does not match observed value",
            )
        if observed != vector.expected_value:
            return cls(
                request,
                response,
                False,
                f"value mismatch: expected {vector.expected_value}, observed {observed}",
            )
        if actual_digest != vector.expected_state_digest:
            return cls(request, response, False, "state digest mismatch against reference")
        return cls(request, response, True, "")

    def as_dict(self) -> dict[str, object]:
        return {
            "request": self.request.as_dict(),
            "response": self.response.as_dict(),
            "passed": self.passed,
            "discrepancy": self.discrepancy,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityExchangeRecord":
        request = payload.get("request")
        response = payload.get("response")
        if not isinstance(request, Mapping) or not isinstance(response, Mapping):
            raise ParityError("parity exchange record requires request/response objects")
        return cls(
            request=ParityRequest.from_dict(request),
            response=ParityResponse.from_dict(response),
            passed=bool(payload["passed"]),
            discrepancy=str(payload.get("discrepancy", "")),
        )


def vector_set_digest(vectors: Sequence[ParityVector]) -> str:
    return hashlib.sha256(
        json.dumps(
            [vector.as_dict() for vector in vectors],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True, slots=True)
class ConformanceReport:
    session_id: str
    capabilities: ParityCapabilities
    vector_set_digest: str
    records: tuple[ParityExchangeRecord, ...]
    schema: str = REPORT_SCHEMA
    version: int = REPORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != REPORT_SCHEMA or self.version != REPORT_SCHEMA_VERSION:
            raise ParityError("unsupported parity report schema")
        if not self.session_id.strip():
            raise ParityError("parity report session_id must not be empty")
        sequences = tuple(record.request.sequence for record in self.records)
        if sequences != tuple(range(len(self.records))):
            raise ParityError("parity report request sequences must be contiguous from zero")
        if any(record.request.session_id != self.session_id for record in self.records):
            raise ParityError("parity report contains a foreign session")
        computed_vector_digest = vector_set_digest(
            tuple(record.request.vector for record in self.records)
        )
        if self.vector_set_digest != computed_vector_digest:
            raise ParityError("parity report vector-set digest mismatch")

    @property
    def passed(self) -> bool:
        return bool(self.records) and all(record.passed for record in self.records)

    @property
    def passed_count(self) -> int:
        return sum(1 for record in self.records if record.passed)

    @property
    def failed_count(self) -> int:
        return len(self.records) - self.passed_count

    def summary(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "target_id": self.capabilities.target_id,
            "passed": self.passed,
            "vectors": len(self.records),
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
        }

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "session_id": self.session_id,
            "capabilities": self.capabilities.as_dict(),
            "capabilities_digest": self.capabilities.digest(),
            "vector_set_digest": self.vector_set_digest,
            "records": [record.as_dict() for record in self.records],
            "summary": self.summary(),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256_payload(self.as_dict())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ConformanceReport":
        raw_capabilities = payload.get("capabilities")
        raw_records = payload.get("records")
        if not isinstance(raw_capabilities, Mapping) or not isinstance(raw_records, list):
            raise ParityError("parity report requires capabilities object and records list")
        report = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            session_id=str(payload["session_id"]),
            capabilities=ParityCapabilities.from_dict(raw_capabilities),
            vector_set_digest=str(payload["vector_set_digest"]),
            records=tuple(ParityExchangeRecord.from_dict(item) for item in raw_records),
        )
        claimed_capabilities_digest = payload.get("capabilities_digest")
        if (
            claimed_capabilities_digest is not None
            and str(claimed_capabilities_digest) != report.capabilities.digest()
        ):
            raise ParityError("parity report capabilities digest mismatch")
        claimed_summary = payload.get("summary")
        if claimed_summary is not None and claimed_summary != report.summary():
            raise ParityError("parity report summary mismatch")
        return report

    @classmethod
    def from_json(cls, text: str) -> "ConformanceReport":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ParityError("parity report JSON root must be an object")
        return cls.from_dict(payload)


class ReferenceLoopbackTransport:
    """Deterministic host-side target used to prove the harness before hardware."""

    def __init__(
        self,
        *,
        target_id: str = "simulacrum.loopback",
        max_width: int = 12,
        forced_status: Mapping[str, ParityStatus] | None = None,
        observed_overrides: Mapping[str, str] | None = None,
    ) -> None:
        self._capabilities = ParityCapabilities(
            target_id=target_id,
            operations=tuple(ParityOperation),
            max_width=max_width,
            telemetry_keys=("reference",),
        )
        self._forced_status = dict(forced_status or {})
        self._observed_overrides = dict(observed_overrides or {})

    def capabilities(self) -> ParityCapabilities:
        return self._capabilities

    def exchange(self, request: ParityRequest) -> ParityResponse:
        vector = request.vector
        forced = self._forced_status.get(vector.vector_id)
        if forced is not None and forced is not ParityStatus.OK:
            return ParityResponse(
                session_id=request.session_id,
                sequence=request.sequence,
                vector_id=vector.vector_id,
                status=forced,
                detail="forced loopback status",
                telemetry=(("reference", "loopback"),),
            )
        observed = self._observed_overrides.get(vector.vector_id, vector.expected_value)
        observed = _normalize_value(observed, vector.width)
        return ParityResponse(
            session_id=request.session_id,
            sequence=request.sequence,
            vector_id=vector.vector_id,
            status=ParityStatus.OK,
            observed_value=observed,
            observed_state_digest=ternary_state_digest(vector.width, observed),
            telemetry=(("reference", "loopback"),),
        )


def run_conformance(
    transport: ParityTransport,
    vectors: Sequence[ParityVector],
    *,
    session_id: str | None = None,
) -> ConformanceReport:
    """Run deterministic golden vectors through any parity transport adapter."""
    vectors = tuple(vectors)
    if not vectors:
        raise ParityError("conformance requires at least one vector")
    capabilities = transport.capabilities()
    set_digest = vector_set_digest(vectors)
    if session_id is None:
        seed = f"{capabilities.digest()}:{set_digest}".encode("utf-8")
        session_id = "TD1-" + hashlib.sha256(seed).hexdigest()[:16]

    records: list[ParityExchangeRecord] = []
    for sequence, vector in enumerate(vectors):
        request = ParityRequest(session_id=session_id, sequence=sequence, vector=vector)
        if not capabilities.supports(vector):
            response = ParityResponse(
                session_id=session_id,
                sequence=sequence,
                vector_id=vector.vector_id,
                status=ParityStatus.UNSUPPORTED,
                detail="rejected by capability negotiation",
            )
        else:
            response = transport.exchange(request)
        records.append(ParityExchangeRecord.evaluate(request, response))

    return ConformanceReport(
        session_id=session_id,
        capabilities=capabilities,
        vector_set_digest=set_digest,
        records=tuple(records),
    )


def _word(value: int, width: int) -> str:
    return str(TernaryWord.from_int(value, width))


def golden_trit_vectors() -> tuple[ParityVector, ...]:
    """Return exactly the three deterministic one-trit hold vectors."""
    return (
        ParityVector.create("TRIT-NEG", ParityOperation.TRIT_HOLD, 1, ("-",)),
        ParityVector.create("TRIT-ZERO", ParityOperation.TRIT_HOLD, 1, ("0",)),
        ParityVector.create("TRIT-POS", ParityOperation.TRIT_HOLD, 1, ("+",)),
    )


def golden_register_vectors(width: int = 12) -> tuple[ParityVector, ...]:
    """Golden vectors for the first physical trit/register-slice campaign."""
    if width <= 0:
        raise ParityError("golden register width must be positive")
    low, high = representable_range(width)
    alternating = "".join("+0-"[index % 3] for index in range(width))
    return golden_trit_vectors() + (
        ParityVector.create(
            "REG-ZERO", ParityOperation.REGISTER_LOAD, width, (_word(0, width),)
        ),
        ParityVector.create(
            "REG-ONE", ParityOperation.REGISTER_LOAD, width, (_word(1, width),)
        ),
        ParityVector.create(
            "REG-NEG-ONE", ParityOperation.REGISTER_LOAD, width, (_word(-1, width),)
        ),
        ParityVector.create(
            "REG-MAX", ParityOperation.REGISTER_LOAD, width, (_word(high, width),)
        ),
        ParityVector.create(
            "REG-MIN", ParityOperation.REGISTER_LOAD, width, (_word(low, width),)
        ),
        ParityVector.create(
            "REG-ALT", ParityOperation.REGISTER_LOAD, width, (alternating,)
        ),
    )


def golden_alu_vectors(width: int = 12) -> tuple[ParityVector, ...]:
    """Logical ALU vectors reserved for later physical ALU conformance."""
    if width <= 0:
        raise ParityError("golden ALU width must be positive")
    low, high = representable_range(width)
    return (
        ParityVector.create(
            "ALU-NEG-ONE", ParityOperation.NEGATE, width, (_word(1, width),)
        ),
        ParityVector.create(
            "ALU-NEG-MAX", ParityOperation.NEGATE, width, (_word(high, width),)
        ),
        ParityVector.create(
            "ALU-ADD-BASIC",
            ParityOperation.ADD,
            width,
            (_word(5, width), _word(7, width)),
        ),
        ParityVector.create(
            "ALU-ADD-WRAP",
            ParityOperation.ADD,
            width,
            (_word(high, width), _word(1, width)),
        ),
        ParityVector.create(
            "ALU-SUB-BASIC",
            ParityOperation.SUB,
            width,
            (_word(5, width), _word(7, width)),
        ),
        ParityVector.create(
            "ALU-SUB-WRAP",
            ParityOperation.SUB,
            width,
            (_word(low, width), _word(1, width)),
        ),
    )


def golden_parity_vectors(width: int = 12) -> tuple[ParityVector, ...]:
    return golden_register_vectors(width) + golden_alu_vectors(width)
