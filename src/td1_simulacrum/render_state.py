"""Versioned, deterministic renderer-independent state for TD-1.

The render-state layer is a contract between machine truth and presentation.
Engineering Mode and Relic Mode must project from the same immutable state
object; neither mode is allowed to invent machine state.

Schema v1 intentionally serializes observer quantities as scaled integers.
That avoids making renderer parity depend on floating-point JSON formatting.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .glyphs import word_to_glyph_ids
from .machine import MEMORY_WORDS, REGISTER_COUNT, Machine
from .observer import ObserverState
from .semantic import SemanticRoot, StateWeave
from .strict_json import require_canonical_mapping
from .ternary import TernaryWord

RENDER_SCHEMA = "td1.render-state"
RENDER_SCHEMA_VERSION = 1

# Stable IDs for Relic Mode. Changing these requires a render-schema version bump.
SEMANTIC_ROOT_IDS: dict[SemanticRoot, int] = {
    SemanticRoot.OBSERVER: 0,
    SemanticRoot.ORIGIN: 1,
    SemanticRoot.TIME: 2,
    SemanticRoot.REFERENCE: 3,
    SemanticRoot.MOTION: 4,
    SemanticRoot.MEMORY: 5,
    SemanticRoot.LINK: 6,
    SemanticRoot.STATE: 7,
    SemanticRoot.FRAME: 8,
    SemanticRoot.AXIS: 9,
    SemanticRoot.SIGNAL: 10,
    SemanticRoot.COGNITION: 11,
    SemanticRoot.EXECUTION: 12,
    SemanticRoot.TRANSFORM: 13,
    SemanticRoot.ISOLATION: 14,
    SemanticRoot.DOMAIN: 15,
}


class RenderMode(str, Enum):
    ENGINEERING = "engineering"
    RELIC = "relic"


class RenderPlane(str, Enum):
    CARRIER = "carrier"
    MACHINE = "machine"
    SEMANTIC = "semantic"
    OBSERVER = "observer"


RENDER_PLANE_IDS: dict[RenderPlane, int] = {
    RenderPlane.CARRIER: 0,
    RenderPlane.MACHINE: 1,
    RenderPlane.SEMANTIC: 2,
    RenderPlane.OBSERVER: 3,
}


@dataclass(frozen=True, slots=True)
class RegisterRenderState:
    index: int
    ternary: str
    value: int
    glyph_ids: tuple[int, ...]

    @classmethod
    def capture(cls, index: int, word: TernaryWord) -> "RegisterRenderState":
        return cls(index, str(word), word.value, word_to_glyph_ids(word))

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "RegisterRenderState":
        word = TernaryWord.parse(str(payload["ternary"]))
        state = cls(
            index=int(payload["index"]),
            ternary=str(word),
            value=int(payload["value"]),
            glyph_ids=tuple(int(value) for value in payload["glyph_ids"]),  # type: ignore[arg-type]
        )
        if state.value != word.value or state.glyph_ids != word_to_glyph_ids(word):
            raise ValueError(f"inconsistent register render state R{state.index}")
        require_canonical_mapping(payload, state.as_dict(), label="register render state")
        return state

    def as_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "ternary": self.ternary,
            "value": self.value,
            "glyph_ids": list(self.glyph_ids),
        }


@dataclass(frozen=True, slots=True)
class MemoryCellRenderState:
    address: int
    ternary: str
    glyph_ids: tuple[int, ...]

    @classmethod
    def capture(cls, address: int, word: TernaryWord) -> "MemoryCellRenderState":
        return cls(address, str(word), word_to_glyph_ids(word))

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "MemoryCellRenderState":
        word = TernaryWord.parse(str(payload["ternary"]))
        state = cls(
            address=int(payload["address"]),
            ternary=str(word),
            glyph_ids=tuple(int(value) for value in payload["glyph_ids"]),  # type: ignore[arg-type]
        )
        if state.glyph_ids != word_to_glyph_ids(word):
            raise ValueError(f"inconsistent memory render state at {state.address}")
        require_canonical_mapping(payload, state.as_dict(), label="memory render state")
        return state

    @property
    def value(self) -> int:
        return TernaryWord.parse(self.ternary).value

    def as_dict(self) -> dict[str, object]:
        return {
            "address": self.address,
            "ternary": self.ternary,
            "glyph_ids": list(self.glyph_ids),
        }


@dataclass(frozen=True, slots=True)
class ObserverRenderState:
    """Quantized observer state used by the renderer contract.

    Scale factors are part of schema v1:
    - geodetic angles: nanodegrees
    - altitude: micrometers
    - ECEF: millimeters
    - Julian Date: microdays
    - Earth Rotation Angle: nanoradians
    """

    timestamp_utc: str
    latitude_nanodeg: int
    longitude_nanodeg: int
    altitude_microm: int
    ecef_mm: tuple[int, int, int]
    julian_date_microday: int
    earth_rotation_nanorad_approx: int

    @classmethod
    def capture(cls, observer: ObserverState) -> "ObserverRenderState":
        x, y, z = observer.ecef_m()
        return cls(
            timestamp_utc=observer.utc.isoformat(),
            latitude_nanodeg=round(observer.latitude_deg * 1_000_000_000),
            longitude_nanodeg=round(observer.longitude_deg * 1_000_000_000),
            altitude_microm=round(observer.altitude_m * 1_000_000),
            ecef_mm=(round(x * 1_000), round(y * 1_000), round(z * 1_000)),
            julian_date_microday=round(observer.julian_date_utc() * 1_000_000),
            earth_rotation_nanorad_approx=round(
                observer.approximate_earth_rotation_angle_rad() * 1_000_000_000
            ),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ObserverRenderState":
        state = cls(
            timestamp_utc=str(payload["timestamp_utc"]),
            latitude_nanodeg=int(payload["latitude_nanodeg"]),
            longitude_nanodeg=int(payload["longitude_nanodeg"]),
            altitude_microm=int(payload["altitude_microm"]),
            ecef_mm=tuple(int(value) for value in payload["ecef_mm"]),  # type: ignore[arg-type]
            julian_date_microday=int(payload["julian_date_microday"]),
            earth_rotation_nanorad_approx=int(payload["earth_rotation_nanorad_approx"]),
        )
        require_canonical_mapping(payload, state.as_dict(), label="observer render state")
        return state

    def as_dict(self) -> dict[str, object]:
        return {
            "timestamp_utc": self.timestamp_utc,
            "latitude_nanodeg": self.latitude_nanodeg,
            "longitude_nanodeg": self.longitude_nanodeg,
            "altitude_microm": self.altitude_microm,
            "ecef_mm": list(self.ecef_mm),
            "julian_date_microday": self.julian_date_microday,
            "earth_rotation_nanorad_approx": self.earth_rotation_nanorad_approx,
        }


@dataclass(frozen=True, slots=True)
class RenderState:
    """Normative renderer input captured from TD-1 machine truth."""

    machine_digest: str
    ip: int
    cond: int
    halted: bool
    steps: int
    registers: tuple[RegisterRenderState, ...]
    memory_size: int
    nonzero_memory: tuple[MemoryCellRenderState, ...]
    weave: StateWeave | None = None
    observer: ObserverRenderState | None = None
    schema: str = RENDER_SCHEMA
    version: int = RENDER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != RENDER_SCHEMA:
            raise ValueError(f"unsupported render schema {self.schema!r}")
        if self.version != RENDER_SCHEMA_VERSION:
            raise ValueError(f"unsupported render schema version {self.version}")
        if self.cond not in (-1, 0, 1):
            raise ValueError("condition state must be -1, 0, or +1")
        if len(self.registers) != REGISTER_COUNT:
            raise ValueError(f"render state requires exactly {REGISTER_COUNT} registers")
        if tuple(register.index for register in self.registers) != tuple(range(REGISTER_COUNT)):
            raise ValueError("register render states must be ordered R0..R8")
        if self.memory_size != MEMORY_WORDS:
            raise ValueError(f"render state memory_size must be {MEMORY_WORDS}")
        addresses = tuple(cell.address for cell in self.nonzero_memory)
        if addresses != tuple(sorted(set(addresses))):
            raise ValueError("nonzero memory cells must have unique ascending addresses")
        if any(not 0 <= address < self.memory_size for address in addresses):
            raise ValueError("memory address outside render-state memory range")
        if any(cell.value == 0 for cell in self.nonzero_memory):
            raise ValueError("nonzero memory section may not contain zero-valued words")

    @classmethod
    def capture(
        cls,
        machine: Machine,
        *,
        weave: StateWeave | None = None,
        observer: ObserverState | None = None,
    ) -> "RenderState":
        registers = tuple(
            RegisterRenderState.capture(index, word)
            for index, word in enumerate(machine.registers)
        )
        nonzero_memory = tuple(
            MemoryCellRenderState.capture(address, word)
            for address, word in enumerate(machine.memory)
            if word.value != 0
        )
        return cls(
            machine_digest=machine.state_digest(include_memory=True),
            ip=machine.ip,
            cond=machine.cond,
            halted=machine.halted,
            steps=machine.steps,
            registers=registers,
            memory_size=len(machine.memory),
            nonzero_memory=nonzero_memory,
            weave=weave,
            observer=ObserverRenderState.capture(observer) if observer else None,
        )

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "RenderState":
        weave_payload = payload.get("weave")
        observer_payload = payload.get("observer")
        state = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            machine_digest=str(payload["machine_digest"]),
            ip=int(payload["ip"]),
            cond=int(payload["cond"]),
            halted=bool(payload["halted"]),
            steps=int(payload["steps"]),
            registers=tuple(
                RegisterRenderState.from_dict(item)
                for item in payload["registers"]  # type: ignore[union-attr]
            ),
            memory_size=int(payload["memory_size"]),
            nonzero_memory=tuple(
                MemoryCellRenderState.from_dict(item)
                for item in payload["nonzero_memory"]  # type: ignore[union-attr]
            ),
            weave=(
                StateWeave.parse(str(weave_payload["canonical"]))  # type: ignore[index]
                if weave_payload is not None
                else None
            ),
            observer=(
                ObserverRenderState.from_dict(observer_payload)  # type: ignore[arg-type]
                if observer_payload is not None
                else None
            ),
        )
        # Validate redundant ternary/glyph data, planes/weave metadata, and full machine parity.
        require_canonical_mapping(payload, state.as_dict(), label="render state")
        state.restore_machine()
        return state

    @classmethod
    def from_json(cls, text: str) -> "RenderState":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("render-state JSON root must be an object")
        return cls.from_dict(payload)

    @property
    def active_planes(self) -> tuple[RenderPlane, ...]:
        planes = [RenderPlane.CARRIER, RenderPlane.MACHINE]
        if self.weave is not None:
            planes.append(RenderPlane.SEMANTIC)
        if self.observer is not None:
            planes.append(RenderPlane.OBSERVER)
        return tuple(planes)

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema": self.schema,
            "version": self.version,
            "machine_digest": self.machine_digest,
            "ip": self.ip,
            "cond": self.cond,
            "halted": self.halted,
            "steps": self.steps,
            "registers": [register.as_dict() for register in self.registers],
            "memory_size": self.memory_size,
            "nonzero_memory": [cell.as_dict() for cell in self.nonzero_memory],
            "planes": [plane.value for plane in self.active_planes],
        }
        if self.weave is not None:
            payload["weave"] = {
                "canonical": self.weave.canonical,
                "version": self.weave.lower().version,
            }
        if self.observer is not None:
            payload["observer"] = self.observer.as_dict()
        return payload

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def restore_machine(self) -> Machine:
        """Reconstruct the exact emulated machine state captured by this schema."""
        machine = Machine()
        machine.registers = [TernaryWord.parse(register.ternary) for register in self.registers]
        machine.memory = [TernaryWord.zero() for _ in range(self.memory_size)]
        for cell in self.nonzero_memory:
            word = TernaryWord.parse(cell.ternary)
            if tuple(word_to_glyph_ids(word)) != cell.glyph_ids:
                raise ValueError(f"memory glyph mismatch at address {cell.address}")
            machine.memory[cell.address] = word
        machine.ip = self.ip
        machine.cond = self.cond
        machine.halted = self.halted
        machine.steps = self.steps
        if machine.state_digest(include_memory=True) != self.machine_digest:
            raise ValueError("render state does not reconstruct its machine digest")
        return machine


def _engineering_projection(state: RenderState) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "td1.render-projection",
        "version": 1,
        "mode": RenderMode.ENGINEERING.value,
        "source_digest": state.digest(),
        "planes": [plane.value for plane in state.active_planes],
        "machine": {
            "digest": state.machine_digest,
            "ip": state.ip,
            "cond": state.cond,
            "halted": state.halted,
            "steps": state.steps,
            "registers": [
                {
                    "name": f"R{register.index}",
                    "ternary": register.ternary,
                    "value": register.value,
                    "glyph_ids": list(register.glyph_ids),
                }
                for register in state.registers
            ],
            "memory": [
                {
                    "address": cell.address,
                    "ternary": cell.ternary,
                    "value": cell.value,
                    "glyph_ids": list(cell.glyph_ids),
                }
                for cell in state.nonzero_memory
            ],
        },
    }
    if state.weave is not None:
        payload["semantic"] = {
            "weave": state.weave.canonical,
            "ir": state.weave.lower().as_dict(),
        }
    if state.observer is not None:
        payload["observer"] = state.observer.as_dict()
    return payload


def _relic_projection(state: RenderState) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema": "td1.render-projection",
        "version": 1,
        "mode": RenderMode.RELIC.value,
        "source_digest": state.digest(),
        "planes": [RENDER_PLANE_IDS[plane] for plane in state.active_planes],
        "machine": {
            "digest": state.machine_digest,
            "ip_glyphs": list(word_to_glyph_ids(TernaryWord.from_int(state.ip))),
            "condition": state.cond,
            "halted": state.halted,
            "step_glyphs": list(word_to_glyph_ids(TernaryWord.from_int(state.steps))),
            "registers": [
                {
                    "slot": register.index,
                    "glyphs": list(register.glyph_ids),
                }
                for register in state.registers
            ],
            "memory": [
                {
                    "address_glyphs": list(
                        word_to_glyph_ids(TernaryWord.from_int(cell.address))
                    ),
                    "glyphs": list(cell.glyph_ids),
                }
                for cell in state.nonzero_memory
            ],
        },
    }
    if state.weave is not None:
        payload["semantic"] = {
            "roots": [SEMANTIC_ROOT_IDS[root] for root in state.weave.roots],
            "modifier": int(state.weave.modifier),
            "version": state.weave.lower().version,
        }
    if state.observer is not None:
        payload["observer"] = state.observer.as_dict()
    return payload


def project_render_state(state: RenderState, mode: RenderMode | str) -> dict[str, Any]:
    """Project one normative RenderState into Engineering or Relic representation."""
    selected = RenderMode(mode)
    if selected is RenderMode.ENGINEERING:
        return _engineering_projection(state)
    return _relic_projection(state)