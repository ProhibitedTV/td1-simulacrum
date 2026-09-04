"""Deterministic reference execution model for the TD-1 12-trit machine.

The execution core is intentionally conventional in structure. Unusual interface
layers compile down to this model; they do not redefine arithmetic semantics.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Sequence

from .ternary import TernaryWord

WORD_WIDTH = 12
REGISTER_COUNT = 9
MEMORY_WORDS = 729


class MachineError(RuntimeError):
    """Base exception for TD-1 execution failures."""


class ProgramCounterError(MachineError):
    """Raised when execution leaves the loaded program."""


class StepLimitExceeded(MachineError):
    """Raised when a run exceeds its deterministic safety limit."""


class Op(Enum):
    NOP = auto()
    LDI = auto()
    MOV = auto()
    ADD = auto()
    SUB = auto()
    NEG = auto()
    ADDI = auto()
    CMP = auto()
    LD = auto()
    ST = auto()
    BRN = auto()
    BRZ = auto()
    BRP = auto()
    JMP = auto()
    HALT = auto()


@dataclass(frozen=True, slots=True)
class Instruction:
    """Logical TD-1 instruction.

    This is the semantic instruction representation. A physical 12-trit encoding
    is intentionally not frozen yet.
    """

    op: Op
    a: int = 0
    b: int = 0
    imm: int = 0


@dataclass(frozen=True, slots=True)
class MachineSnapshot:
    """Stable immutable snapshot suitable for tests, tooling, and parity checks."""

    ip: int
    cond: int
    halted: bool
    steps: int
    registers: tuple[str, ...]
    register_values: tuple[int, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "ip": self.ip,
            "cond": self.cond,
            "halted": self.halted,
            "steps": self.steps,
            "registers": list(self.registers),
            "register_values": list(self.register_values),
        }


@dataclass(slots=True)
class Machine:
    """Deterministic TD-1 reference machine.

    Branch immediates are relative to the instruction following the branch.
    Memory addresses are formed from ``R[b] + imm`` and wrap modulo 729.
    """

    registers: list[TernaryWord] = field(
        default_factory=lambda: [TernaryWord.zero(WORD_WIDTH) for _ in range(REGISTER_COUNT)]
    )
    memory: list[TernaryWord] = field(
        default_factory=lambda: [TernaryWord.zero(WORD_WIDTH) for _ in range(MEMORY_WORDS)]
    )
    ip: int = 0
    cond: int = 0
    halted: bool = False
    steps: int = 0

    def reset(self) -> None:
        self.registers = [TernaryWord.zero(WORD_WIDTH) for _ in range(REGISTER_COUNT)]
        self.memory = [TernaryWord.zero(WORD_WIDTH) for _ in range(MEMORY_WORDS)]
        self.ip = 0
        self.cond = 0
        self.halted = False
        self.steps = 0

    @staticmethod
    def _check_reg(index: int) -> None:
        if not 0 <= index < REGISTER_COUNT:
            raise IndexError(f"register index out of range: {index}")

    def _address(self, base_reg: int, offset: int) -> int:
        self._check_reg(base_reg)
        return (self.registers[base_reg].value + int(offset)) % MEMORY_WORDS

    def step(self, program: Sequence[Instruction]) -> None:
        if self.halted:
            return
        if not 0 <= self.ip < len(program):
            raise ProgramCounterError(f"instruction pointer out of program range: {self.ip}")

        ins = program[self.ip]
        self.ip += 1
        self.steps += 1

        if ins.op is Op.NOP:
            return
        if ins.op is Op.HALT:
            self.halted = True
            return

        if ins.op in {Op.LDI, Op.MOV, Op.ADD, Op.SUB, Op.NEG, Op.ADDI, Op.CMP, Op.LD, Op.ST}:
            self._check_reg(ins.a)
        if ins.op in {Op.MOV, Op.ADD, Op.SUB, Op.CMP, Op.LD, Op.ST}:
            self._check_reg(ins.b)

        if ins.op is Op.LDI:
            self.registers[ins.a] = TernaryWord.from_int(ins.imm, WORD_WIDTH)
        elif ins.op is Op.MOV:
            self.registers[ins.a] = self.registers[ins.b]
        elif ins.op is Op.ADD:
            self.registers[ins.a] = self.registers[ins.a] + self.registers[ins.b]
        elif ins.op is Op.SUB:
            self.registers[ins.a] = self.registers[ins.a] - self.registers[ins.b]
        elif ins.op is Op.NEG:
            self.registers[ins.a] = -self.registers[ins.a]
        elif ins.op is Op.ADDI:
            self.registers[ins.a] = self.registers[ins.a] + ins.imm
        elif ins.op is Op.CMP:
            delta = self.registers[ins.a].value - self.registers[ins.b].value
            self.cond = (delta > 0) - (delta < 0)
        elif ins.op is Op.LD:
            self.registers[ins.a] = self.memory[self._address(ins.b, ins.imm)]
        elif ins.op is Op.ST:
            self.memory[self._address(ins.b, ins.imm)] = self.registers[ins.a]
        elif ins.op is Op.BRN:
            if self.cond < 0:
                self.ip += ins.imm
        elif ins.op is Op.BRZ:
            if self.cond == 0:
                self.ip += ins.imm
        elif ins.op is Op.BRP:
            if self.cond > 0:
                self.ip += ins.imm
        elif ins.op is Op.JMP:
            self.ip += ins.imm
        else:
            raise MachineError(f"unimplemented opcode: {ins.op}")

    def run(self, program: Sequence[Instruction], max_steps: int = 100_000) -> "Machine":
        if max_steps <= 0:
            raise ValueError("max_steps must be positive")
        while not self.halted:
            if self.steps >= max_steps:
                raise StepLimitExceeded(f"execution exceeded max_steps={max_steps}")
            self.step(program)
        return self

    def snapshot(self) -> MachineSnapshot:
        return MachineSnapshot(
            ip=self.ip,
            cond=self.cond,
            halted=self.halted,
            steps=self.steps,
            registers=tuple(str(word) for word in self.registers),
            register_values=tuple(word.value for word in self.registers),
        )

    def state_digest(self, *, include_memory: bool = True) -> str:
        """Return a deterministic SHA-256 digest of observable machine state.

        The digest is intended for emulator/hardware parity testing, replay, and
        regression fixtures. It is not an authentication primitive.
        """
        payload: dict[str, object] = self.snapshot().as_dict()
        if include_memory:
            payload["memory"] = [str(word) for word in self.memory]
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()
