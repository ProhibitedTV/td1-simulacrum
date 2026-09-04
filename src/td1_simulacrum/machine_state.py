"""Versioned renderer-independent persistence for logical TD-1 machine state.

`td1.machine-state` is the persistence boundary for execution truth alone. It
contains no glyph, corpus, geometry, observer, or presentation fields. A saved
checkpoint can be restored into the reference `Machine` and must reproduce the
same complete machine-state digest.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass

from .machine import MEMORY_WORDS, REGISTER_COUNT, WORD_WIDTH, Machine
from .ternary import TernaryWord

MACHINE_STATE_SCHEMA = "td1.machine-state"
MACHINE_STATE_SCHEMA_VERSION = 1


class MachineStateError(ValueError):
    """Raised when a standalone TD-1 machine checkpoint is inconsistent."""


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _require_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if type(value) is not int:
        raise MachineStateError(f"machine-state {key} must be an integer")
    return value


def _require_bool(payload: Mapping[str, object], key: str) -> bool:
    value = payload.get(key)
    if type(value) is not bool:
        raise MachineStateError(f"machine-state {key} must be a boolean")
    return value


def _parse_word(text: str, *, field: str) -> TernaryWord:
    if not isinstance(text, str):
        raise MachineStateError(f"{field} must be a ternary string")
    try:
        word = TernaryWord.parse(text)
    except ValueError as exc:
        raise MachineStateError(f"invalid ternary word for {field}") from exc
    if word.width != WORD_WIDTH:
        raise MachineStateError(
            f"{field} must contain exactly {WORD_WIDTH} trits, got {word.width}"
        )
    return word


@dataclass(frozen=True, slots=True)
class MachineMemoryCell:
    """One nonzero word in sparse checkpoint memory."""

    address: int
    ternary: str

    def __post_init__(self) -> None:
        if type(self.address) is not int or not 0 <= self.address < MEMORY_WORDS:
            raise MachineStateError(f"memory address outside 0..{MEMORY_WORDS - 1}")
        word = _parse_word(self.ternary, field=f"memory[{self.address}]")
        if word.value == 0:
            raise MachineStateError("sparse nonzero memory may not contain zero words")
        object.__setattr__(self, "ternary", str(word))

    @property
    def word(self) -> TernaryWord:
        return TernaryWord.parse(self.ternary)

    def as_dict(self) -> dict[str, object]:
        return {"address": self.address, "ternary": self.ternary}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "MachineMemoryCell":
        address = payload.get("address")
        ternary = payload.get("ternary")
        if type(address) is not int:
            raise MachineStateError("memory address must be an integer")
        if not isinstance(ternary, str):
            raise MachineStateError("memory ternary value must be a string")
        return cls(address=address, ternary=ternary)


@dataclass(frozen=True, slots=True)
class MachineState:
    """Complete logical TD-1 checkpoint with sparse exact memory."""

    machine_digest: str
    ip: int
    cond: int
    halted: bool
    steps: int
    registers: tuple[str, ...]
    nonzero_memory: tuple[MachineMemoryCell, ...] = ()
    word_width: int = WORD_WIDTH
    register_count: int = REGISTER_COUNT
    memory_words: int = MEMORY_WORDS
    schema: str = MACHINE_STATE_SCHEMA
    version: int = MACHINE_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != MACHINE_STATE_SCHEMA:
            raise MachineStateError(f"unsupported machine-state schema {self.schema!r}")
        if self.version != MACHINE_STATE_SCHEMA_VERSION:
            raise MachineStateError(f"unsupported machine-state version {self.version}")
        if type(self.word_width) is not int or self.word_width != WORD_WIDTH:
            raise MachineStateError(f"machine-state word_width must be {WORD_WIDTH}")
        if type(self.register_count) is not int or self.register_count != REGISTER_COUNT:
            raise MachineStateError(f"machine-state register_count must be {REGISTER_COUNT}")
        if type(self.memory_words) is not int or self.memory_words != MEMORY_WORDS:
            raise MachineStateError(f"machine-state memory_words must be {MEMORY_WORDS}")
        if type(self.ip) is not int:
            raise MachineStateError("machine instruction pointer must be an integer")
        if type(self.cond) is not int or self.cond not in (-1, 0, 1):
            raise MachineStateError("machine condition state must be -1, 0, or +1")
        if type(self.halted) is not bool:
            raise MachineStateError("machine halted state must be a boolean")
        if type(self.steps) is not int or self.steps < 0:
            raise MachineStateError("machine step count must be a nonnegative integer")
        if len(self.registers) != REGISTER_COUNT:
            raise MachineStateError(f"machine-state requires exactly {REGISTER_COUNT} registers")
        if not isinstance(self.machine_digest, str) or not _is_sha256(self.machine_digest):
            raise MachineStateError("machine_digest must be a lowercase SHA-256 hex string")

        registers = tuple(
            str(_parse_word(text, field=f"register R{index}"))
            for index, text in enumerate(self.registers)
        )
        object.__setattr__(self, "registers", registers)

        if any(not isinstance(cell, MachineMemoryCell) for cell in self.nonzero_memory):
            raise MachineStateError("nonzero_memory must contain MachineMemoryCell values")
        memory = tuple(sorted(self.nonzero_memory, key=lambda cell: cell.address))
        addresses = tuple(cell.address for cell in memory)
        if len(set(addresses)) != len(addresses):
            raise MachineStateError("sparse memory addresses must be unique")
        object.__setattr__(self, "nonzero_memory", memory)

        machine = self._restore_unchecked()
        if machine.state_digest(include_memory=True) != self.machine_digest:
            raise MachineStateError("checkpoint does not reconstruct its claimed machine digest")

    @classmethod
    def capture(cls, machine: Machine) -> "MachineState":
        return cls(
            machine_digest=machine.state_digest(include_memory=True),
            ip=machine.ip,
            cond=machine.cond,
            halted=machine.halted,
            steps=machine.steps,
            registers=tuple(str(word) for word in machine.registers),
            nonzero_memory=tuple(
                MachineMemoryCell(address, str(word))
                for address, word in enumerate(machine.memory)
                if word.value != 0
            ),
        )

    @classmethod
    def from_render_state(cls, render_state: object) -> "MachineState":
        """Capture machine truth from a validated RenderState without copying UI fields.

        The object is duck-typed deliberately so this persistence module does not
        depend on the rendering layer. A valid RenderState exposes
        `restore_machine()`; other objects are rejected.
        """
        restore = getattr(render_state, "restore_machine", None)
        if restore is None or not callable(restore):
            raise MachineStateError("object does not expose a machine restore boundary")
        machine = restore()
        if not isinstance(machine, Machine):
            raise MachineStateError("restore boundary did not return a TD-1 Machine")
        return cls.capture(machine)

    def _restore_unchecked(self) -> Machine:
        machine = Machine()
        machine.registers = [TernaryWord.parse(text) for text in self.registers]
        machine.memory = [TernaryWord.zero(WORD_WIDTH) for _ in range(MEMORY_WORDS)]
        for cell in self.nonzero_memory:
            machine.memory[cell.address] = cell.word
        machine.ip = self.ip
        machine.cond = self.cond
        machine.halted = self.halted
        machine.steps = self.steps
        return machine

    def restore_machine(self) -> Machine:
        machine = self._restore_unchecked()
        if machine.state_digest(include_memory=True) != self.machine_digest:
            raise MachineStateError("restored machine digest diverged from checkpoint")
        return machine

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "word_width": self.word_width,
            "register_count": self.register_count,
            "memory_words": self.memory_words,
            "machine_digest": self.machine_digest,
            "ip": self.ip,
            "cond": self.cond,
            "halted": self.halted,
            "steps": self.steps,
            "registers": list(self.registers),
            "nonzero_memory": [cell.as_dict() for cell in self.nonzero_memory],
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "MachineState":
        registers = payload.get("registers")
        memory = payload.get("nonzero_memory")
        if not isinstance(registers, list):
            raise MachineStateError("machine-state registers must be a list")
        if not all(isinstance(item, str) for item in registers):
            raise MachineStateError("machine-state registers must contain ternary strings")
        if not isinstance(memory, list):
            raise MachineStateError("machine-state nonzero_memory must be a list")
        if not all(isinstance(item, Mapping) for item in memory):
            raise MachineStateError("machine-state nonzero_memory entries must be objects")

        schema = payload.get("schema")
        machine_digest = payload.get("machine_digest")
        if not isinstance(schema, str):
            raise MachineStateError("machine-state schema must be a string")
        if not isinstance(machine_digest, str):
            raise MachineStateError("machine-state machine_digest must be a string")

        return cls(
            schema=schema,
            version=_require_int(payload, "version"),
            word_width=_require_int(payload, "word_width"),
            register_count=_require_int(payload, "register_count"),
            memory_words=_require_int(payload, "memory_words"),
            machine_digest=machine_digest,
            ip=_require_int(payload, "ip"),
            cond=_require_int(payload, "cond"),
            halted=_require_bool(payload, "halted"),
            steps=_require_int(payload, "steps"),
            registers=tuple(registers),
            nonzero_memory=tuple(MachineMemoryCell.from_dict(item) for item in memory),
        )

    @classmethod
    def from_json(cls, text: str) -> "MachineState":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise MachineStateError("machine-state JSON root must be an object")
        return cls.from_dict(payload)
