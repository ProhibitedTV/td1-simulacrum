"""Measured first-copper characterization for TD-1 ternary hardware.

This module deliberately contains no nominal trit voltages or comparator thresholds.
Physical numbers enter TD-1 only as measured observations or as separately reviewed
acceptance criteria. Logical `-1/0/+1` state is therefore kept distinct from the
analog representation chosen by a particular board revision.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum, IntEnum

from .strict_json import require_canonical_mapping

CHARACTERIZATION_SCHEMA = "td1.trit-cell-characterization"
CHARACTERIZATION_SCHEMA_VERSION = 1


class HardwareCharacterizationError(ValueError):
    """Raised when measured hardware characterization evidence is invalid."""


class TritStimulus(IntEnum):
    NEGATIVE = -1
    ZERO = 0
    POSITIVE = 1


class BenchNodeRole(str, Enum):
    SUPPLY = "supply"
    REFERENCE = "reference"
    OTHER = "other"


class SwitchingDirection(str, Enum):
    RISING = "rising"
    FALLING = "falling"


def _require_text(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HardwareCharacterizationError(f"{label} must be a nonempty string")
    return value


def _require_int(value: object, *, label: str) -> int:
    if type(value) is not int:
        raise HardwareCharacterizationError(f"{label} must be an integer")
    return value


@dataclass(frozen=True, slots=True)
class InstrumentRef:
    role: str
    identifier: str

    def __post_init__(self) -> None:
        _require_text(self.role, label="instrument role")
        _require_text(self.identifier, label="instrument identifier")

    def as_dict(self) -> dict[str, object]:
        return {"role": self.role, "identifier": self.identifier}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "InstrumentRef":
        state = cls(
            role=_require_text(payload.get("role"), label="instrument role"),
            identifier=_require_text(
                payload.get("identifier"), label="instrument identifier"
            ),
        )
        require_canonical_mapping(payload, state.as_dict(), label="instrument reference")
        return state


@dataclass(frozen=True, slots=True)
class BenchNodeVoltage:
    name: str
    role: BenchNodeRole
    voltage_uv: int

    def __post_init__(self) -> None:
        _require_text(self.name, label="bench node name")
        _require_int(self.voltage_uv, label="bench node voltage_uv")

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "role": self.role.value,
            "voltage_uv": self.voltage_uv,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "BenchNodeVoltage":
        try:
            role = BenchNodeRole(payload["role"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HardwareCharacterizationError("invalid bench node role") from exc
        state = cls(
            name=_require_text(payload.get("name"), label="bench node name"),
            role=role,
            voltage_uv=_require_int(
                payload.get("voltage_uv"), label="bench node voltage_uv"
            ),
        )
        require_canonical_mapping(payload, state.as_dict(), label="bench node voltage")
        return state


@dataclass(frozen=True, slots=True)
class TritBenchObservation:
    ordinal: int
    stimulus: TritStimulus
    output_uv: int
    load_id: str
    load_ohms: int | None = None
    settle_us: int | None = None
    comparator_code: str | None = None
    temperature_millic: int | None = None

    def __post_init__(self) -> None:
        ordinal = _require_int(self.ordinal, label="observation ordinal")
        if ordinal < 0:
            raise HardwareCharacterizationError("observation ordinal must be nonnegative")
        _require_int(self.output_uv, label="observation output_uv")
        _require_text(self.load_id, label="observation load_id")
        if self.load_ohms is not None:
            load_ohms = _require_int(self.load_ohms, label="observation load_ohms")
            if load_ohms <= 0:
                raise HardwareCharacterizationError("observation load_ohms must be positive")
        if self.settle_us is not None:
            settle_us = _require_int(self.settle_us, label="observation settle_us")
            if settle_us < 0:
                raise HardwareCharacterizationError(
                    "observation settle_us must be nonnegative"
                )
        if self.comparator_code is not None:
            _require_text(self.comparator_code, label="observation comparator_code")
        if self.temperature_millic is not None:
            _require_int(
                self.temperature_millic,
                label="observation temperature_millic",
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "stimulus": int(self.stimulus),
            "output_uv": self.output_uv,
            "load_id": self.load_id,
            "load_ohms": self.load_ohms,
            "settle_us": self.settle_us,
            "comparator_code": self.comparator_code,
            "temperature_millic": self.temperature_millic,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "TritBenchObservation":
        try:
            stimulus = TritStimulus(payload["stimulus"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HardwareCharacterizationError("invalid ternary bench stimulus") from exc
        state = cls(
            ordinal=_require_int(payload.get("ordinal"), label="observation ordinal"),
            stimulus=stimulus,
            output_uv=_require_int(payload.get("output_uv"), label="observation output_uv"),
            load_id=_require_text(payload.get("load_id"), label="observation load_id"),
            load_ohms=(
                None
                if payload.get("load_ohms") is None
                else _require_int(payload.get("load_ohms"), label="observation load_ohms")
            ),
            settle_us=(
                None
                if payload.get("settle_us") is None
                else _require_int(payload.get("settle_us"), label="observation settle_us")
            ),
            comparator_code=(
                None
                if payload.get("comparator_code") is None
                else _require_text(
                    payload.get("comparator_code"),
                    label="observation comparator_code",
                )
            ),
            temperature_millic=(
                None
                if payload.get("temperature_millic") is None
                else _require_int(
                    payload.get("temperature_millic"),
                    label="observation temperature_millic",
                )
            ),
        )
        require_canonical_mapping(payload, state.as_dict(), label="trit bench observation")
        return state


@dataclass(frozen=True, slots=True)
class SwitchingObservation:
    ordinal: int
    comparator_id: str
    direction: SwitchingDirection
    threshold_uv: int
    code_before: str
    code_after: str

    def __post_init__(self) -> None:
        ordinal = _require_int(self.ordinal, label="switching ordinal")
        if ordinal < 0:
            raise HardwareCharacterizationError("switching ordinal must be nonnegative")
        _require_text(self.comparator_id, label="switching comparator_id")
        _require_int(self.threshold_uv, label="switching threshold_uv")
        _require_text(self.code_before, label="switching code_before")
        _require_text(self.code_after, label="switching code_after")
        if self.code_before == self.code_after:
            raise HardwareCharacterizationError(
                "switching observation must change comparator code"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "comparator_id": self.comparator_id,
            "direction": self.direction.value,
            "threshold_uv": self.threshold_uv,
            "code_before": self.code_before,
            "code_after": self.code_after,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "SwitchingObservation":
        try:
            direction = SwitchingDirection(payload["direction"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HardwareCharacterizationError("invalid switching direction") from exc
        state = cls(
            ordinal=_require_int(payload.get("ordinal"), label="switching ordinal"),
            comparator_id=_require_text(
                payload.get("comparator_id"), label="switching comparator_id"
            ),
            direction=direction,
            threshold_uv=_require_int(
                payload.get("threshold_uv"), label="switching threshold_uv"
            ),
            code_before=_require_text(
                payload.get("code_before"), label="switching code_before"
            ),
            code_after=_require_text(
                payload.get("code_after"), label="switching code_after"
            ),
        )
        require_canonical_mapping(payload, state.as_dict(), label="switching observation")
        return state


@dataclass(frozen=True, slots=True)
class TritCellCharacterization:
    """Canonical measured evidence for one physical ternary cell/unit.

    The artifact records observations only. It does not decide whether any measured
    voltage is a valid TD-1 logic level and it does not synthesize comparator or
    acceptance thresholds.
    """

    board_revision: str
    unit_id: str
    bench_id: str
    instruments: tuple[InstrumentRef, ...]
    node_voltages: tuple[BenchNodeVoltage, ...]
    observations: tuple[TritBenchObservation, ...]
    switching_observations: tuple[SwitchingObservation, ...] = ()
    schema: str = CHARACTERIZATION_SCHEMA
    version: int = CHARACTERIZATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_text(self.board_revision, label="board_revision")
        _require_text(self.unit_id, label="unit_id")
        _require_text(self.bench_id, label="bench_id")
        if self.schema != CHARACTERIZATION_SCHEMA:
            raise HardwareCharacterizationError(
                f"unsupported characterization schema {self.schema!r}"
            )
        if self.version != CHARACTERIZATION_SCHEMA_VERSION:
            raise HardwareCharacterizationError(
                f"unsupported characterization schema version {self.version}"
            )

        instrument_roles = tuple(item.role for item in self.instruments)
        if instrument_roles != tuple(sorted(set(instrument_roles))):
            raise HardwareCharacterizationError(
                "instrument references must have unique ascending roles"
            )
        node_names = tuple(item.name for item in self.node_voltages)
        if node_names != tuple(sorted(set(node_names))):
            raise HardwareCharacterizationError(
                "bench node voltages must have unique ascending names"
            )
        if not any(item.role is BenchNodeRole.SUPPLY for item in self.node_voltages):
            raise HardwareCharacterizationError(
                "characterization requires at least one measured supply node"
            )

        observation_ordinals = tuple(item.ordinal for item in self.observations)
        if observation_ordinals != tuple(range(len(self.observations))):
            raise HardwareCharacterizationError(
                "bench observation ordinals must be contiguous from zero"
            )
        observed_stimuli = {item.stimulus for item in self.observations}
        if observed_stimuli != set(TritStimulus):
            raise HardwareCharacterizationError(
                "characterization requires at least one observation of -1, 0, and +1"
            )

        switching_ordinals = tuple(item.ordinal for item in self.switching_observations)
        if switching_ordinals != tuple(range(len(self.switching_observations))):
            raise HardwareCharacterizationError(
                "switching observation ordinals must be contiguous from zero"
            )

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "board_revision": self.board_revision,
            "unit_id": self.unit_id,
            "bench_id": self.bench_id,
            "instruments": [item.as_dict() for item in self.instruments],
            "node_voltages": [item.as_dict() for item in self.node_voltages],
            "observations": [item.as_dict() for item in self.observations],
            "switching_observations": [
                item.as_dict() for item in self.switching_observations
            ],
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def voltage_summary(self) -> tuple[dict[str, int], ...]:
        """Return descriptive state ranges without inventing acceptance limits."""
        summaries: list[dict[str, int]] = []
        for stimulus in TritStimulus:
            values = [
                item.output_uv
                for item in self.observations
                if item.stimulus is stimulus
            ]
            summaries.append(
                {
                    "stimulus": int(stimulus),
                    "count": len(values),
                    "min_uv": min(values),
                    "max_uv": max(values),
                }
            )
        return tuple(summaries)

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "TritCellCharacterization":
        instruments = payload.get("instruments")
        node_voltages = payload.get("node_voltages")
        observations = payload.get("observations")
        switching = payload.get("switching_observations")
        if not isinstance(instruments, list):
            raise HardwareCharacterizationError("instruments must be a list")
        if not isinstance(node_voltages, list):
            raise HardwareCharacterizationError("node_voltages must be a list")
        if not isinstance(observations, list):
            raise HardwareCharacterizationError("observations must be a list")
        if not isinstance(switching, list):
            raise HardwareCharacterizationError("switching_observations must be a list")
        if not all(isinstance(item, Mapping) for item in instruments):
            raise HardwareCharacterizationError("instrument entries must be objects")
        if not all(isinstance(item, Mapping) for item in node_voltages):
            raise HardwareCharacterizationError("node voltage entries must be objects")
        if not all(isinstance(item, Mapping) for item in observations):
            raise HardwareCharacterizationError("observation entries must be objects")
        if not all(isinstance(item, Mapping) for item in switching):
            raise HardwareCharacterizationError("switching entries must be objects")

        try:
            schema = payload["schema"]
            version = payload["version"]
        except KeyError as exc:
            raise HardwareCharacterizationError(
                "characterization schema/version are required"
            ) from exc
        if not isinstance(schema, str):
            raise HardwareCharacterizationError("characterization schema must be a string")
        if type(version) is not int:
            raise HardwareCharacterizationError("characterization version must be an integer")

        state = cls(
            schema=schema,
            version=version,
            board_revision=_require_text(
                payload.get("board_revision"), label="board_revision"
            ),
            unit_id=_require_text(payload.get("unit_id"), label="unit_id"),
            bench_id=_require_text(payload.get("bench_id"), label="bench_id"),
            instruments=tuple(InstrumentRef.from_dict(item) for item in instruments),
            node_voltages=tuple(BenchNodeVoltage.from_dict(item) for item in node_voltages),
            observations=tuple(
                TritBenchObservation.from_dict(item) for item in observations
            ),
            switching_observations=tuple(
                SwitchingObservation.from_dict(item) for item in switching
            ),
        )
        require_canonical_mapping(
            payload,
            state.as_dict(),
            label="trit-cell characterization",
        )
        return state

    @classmethod
    def from_json(cls, text: str) -> "TritCellCharacterization":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise HardwareCharacterizationError(
                "characterization is not valid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise HardwareCharacterizationError(
                "characterization JSON root must be an object"
            )
        return cls.from_dict(payload)
