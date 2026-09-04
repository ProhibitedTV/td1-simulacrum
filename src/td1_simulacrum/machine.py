"""Reference execution model for the TD-1 12-trit machine.

This module intentionally keeps the execution semantics explicit and boring.
The unusual interface layers should compile down to this model, not redefine it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from .ternary import TernaryWord

WORD_WIDTH = 12
REGISTER_COUNT = 9
MEMORY_WORDS = 729


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
    op: Op
    a: int = 0
    b: int = 0
    imm: int = 0


@dataclass(slots=True)
class Machine:
    """Deterministic TD-1 reference machine.

    Branch immediates are relative to the instruction following the branch.
    Memory addresses are formed from R[b] + imm and wrapped modulo 729.
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

    def _check_reg(self, index: int) -> None:
        if not 0 <= index < REGISTER_COUNT:
            raise IndexError(f"register index out of range: {index}")

    def _address(self, base_reg: int, offset: int) -> int:
        self._check_reg(base_reg)
        return (self.registers[base_reg].value + int(offset)) % MEMORY_WORDS

    def step(self, program: list[Instruction]) -> None:
        if self.halted:
            return
        if not 0 <= self.ip < len(program):
            raise IndexError(f"instruction pointer out of program range: {self.ip}")

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
        if ins.op in {Op.MOV, Op.ADD, Op.SUB, Op.CMP, Op.LD}:
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
            raise ValueError(f"unimplemented opcode: {ins.op}")

    def run(self, program: list[Instruction], max_steps: int = 100_000) -> "Machine":
        while not self.halted:
            if self.steps >= max_steps:
                raise RuntimeError(f"execution exceeded max_steps={max_steps}")
            self.step(program)
        return self

    def snapshot(self) -> dict[str, object]:
        """Return a stable human-readable state snapshot for tests and tooling."""
        return {
            "ip": self.ip,
            "cond": self.cond,
            "halted": self.halted,
            "steps": self.steps,
            "registers": [str(word) for word in self.registers],
            "register_values": [word.value for word in self.registers],
        }
