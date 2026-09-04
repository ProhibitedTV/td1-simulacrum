"""Minimal text assembler for the logical TD-1 ISA.

This module assembles human-readable source into ``Instruction`` objects. It
does *not* define the eventual physical 12-trit instruction encoding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .machine import Instruction, Op, REGISTER_COUNT

_LABEL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_REGISTER_RE = re.compile(r"^[Rr](\d+)$")


class AssemblyError(ValueError):
    """Raised for invalid TD-1 assembly source."""


@dataclass(frozen=True, slots=True)
class _ParsedLine:
    line_no: int
    text: str
    op: str
    operands: tuple[str, ...]


_ZERO_OPERAND = {"NOP", "HALT"}
_ONE_REGISTER = {"NEG"}
_TWO_REGISTER = {"MOV", "ADD", "SUB", "CMP"}
_REGISTER_IMMEDIATE = {"LDI", "ADDI"}
_MEMORY = {"LD", "ST"}
_BRANCH = {"BRN", "BRZ", "BRP", "JMP"}


def _strip_comment(line: str) -> str:
    for marker in (";", "#"):
        line = line.split(marker, 1)[0]
    return line.strip()


def _parse_register(token: str, line_no: int) -> int:
    match = _REGISTER_RE.match(token)
    if not match:
        raise AssemblyError(f"line {line_no}: expected register, got {token!r}")
    index = int(match.group(1))
    if not 0 <= index < REGISTER_COUNT:
        raise AssemblyError(f"line {line_no}: register out of range: R{index}")
    return index


def _parse_immediate(token: str, line_no: int) -> int:
    try:
        return int(token, 0)
    except ValueError as exc:
        raise AssemblyError(f"line {line_no}: invalid immediate {token!r}") from exc


def _tokenize(source: str) -> tuple[list[_ParsedLine], dict[str, int]]:
    labels: dict[str, int] = {}
    parsed: list[_ParsedLine] = []
    pc = 0

    for line_no, raw in enumerate(source.splitlines(), start=1):
        text = _strip_comment(raw)
        if not text:
            continue

        while ":" in text:
            maybe_label, remainder = text.split(":", 1)
            label = maybe_label.strip()
            if not _LABEL_RE.match(label):
                break
            if label in labels:
                raise AssemblyError(f"line {line_no}: duplicate label {label!r}")
            labels[label] = pc
            text = remainder.strip()
            if not text:
                break

        if not text:
            continue

        normalized = text.replace(",", " ")
        parts = normalized.split()
        op = parts[0].upper()
        operands = tuple(parts[1:])
        parsed.append(_ParsedLine(line_no, text, op, operands))
        pc += 1

    return parsed, labels


def _relative_target(token: str, labels: dict[str, int], pc: int, line_no: int) -> int:
    if token in labels:
        return labels[token] - (pc + 1)
    return _parse_immediate(token, line_no)


def assemble(source: str) -> list[Instruction]:
    """Assemble TD-1 source into logical instructions.

    Syntax is intentionally small and conventional while the native geometric
    programming layer is still under development.
    """
    lines, labels = _tokenize(source)
    program: list[Instruction] = []

    for pc, line in enumerate(lines):
        op_name = line.op
        try:
            op = Op[op_name]
        except KeyError as exc:
            raise AssemblyError(f"line {line.line_no}: unknown opcode {op_name!r}") from exc

        operands = line.operands

        if op_name in _ZERO_OPERAND:
            if operands:
                raise AssemblyError(f"line {line.line_no}: {op_name} takes no operands")
            program.append(Instruction(op))
        elif op_name in _ONE_REGISTER:
            if len(operands) != 1:
                raise AssemblyError(f"line {line.line_no}: {op_name} expects 1 register")
            program.append(Instruction(op, a=_parse_register(operands[0], line.line_no)))
        elif op_name in _TWO_REGISTER:
            if len(operands) != 2:
                raise AssemblyError(f"line {line.line_no}: {op_name} expects 2 registers")
            program.append(
                Instruction(
                    op,
                    a=_parse_register(operands[0], line.line_no),
                    b=_parse_register(operands[1], line.line_no),
                )
            )
        elif op_name in _REGISTER_IMMEDIATE:
            if len(operands) != 2:
                raise AssemblyError(f"line {line.line_no}: {op_name} expects register, immediate")
            program.append(
                Instruction(
                    op,
                    a=_parse_register(operands[0], line.line_no),
                    imm=_parse_immediate(operands[1], line.line_no),
                )
            )
        elif op_name in _MEMORY:
            if len(operands) != 3:
                raise AssemblyError(
                    f"line {line.line_no}: {op_name} expects register, base register, offset"
                )
            program.append(
                Instruction(
                    op,
                    a=_parse_register(operands[0], line.line_no),
                    b=_parse_register(operands[1], line.line_no),
                    imm=_parse_immediate(operands[2], line.line_no),
                )
            )
        elif op_name in _BRANCH:
            if len(operands) != 1:
                raise AssemblyError(f"line {line.line_no}: {op_name} expects target/offset")
            program.append(
                Instruction(
                    op,
                    imm=_relative_target(operands[0], labels, pc, line.line_no),
                )
            )
        else:
            raise AssemblyError(f"line {line.line_no}: assembler has no rule for {op_name}")

    return program


def disassemble(program: list[Instruction]) -> str:
    """Return canonical human-readable assembly for logical instructions."""
    lines: list[str] = []
    for ins in program:
        op = ins.op.name
        if op in _ZERO_OPERAND:
            lines.append(op)
        elif op in _ONE_REGISTER:
            lines.append(f"{op} R{ins.a}")
        elif op in _TWO_REGISTER:
            lines.append(f"{op} R{ins.a}, R{ins.b}")
        elif op in _REGISTER_IMMEDIATE:
            lines.append(f"{op} R{ins.a}, {ins.imm}")
        elif op in _MEMORY:
            lines.append(f"{op} R{ins.a}, R{ins.b}, {ins.imm}")
        elif op in _BRANCH:
            lines.append(f"{op} {ins.imm}")
        else:
            raise AssemblyError(f"disassembler has no rule for {op}")
    return "\n".join(lines)
