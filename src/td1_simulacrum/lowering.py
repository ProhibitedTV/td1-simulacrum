"""Typed State Weave lowering into the TD-1 logical ISA.

This module is intentionally conservative. A State Weave identifies a native
semantic operation, while OperandBindings provide the concrete machine resources
needed to execute that operation. The separation prevents interface semantics
from silently inheriting register/address choices.

The v1 mappings are TD-1 engineering conventions, not translations of the
Veilbreak corpus and not claims about external ontology.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from .machine import REGISTER_COUNT, Instruction, Op
from .semantic import Modifier, SemanticRoot, StateWeave

LOWERING_SCHEMA = "td1.semantic-lowering"
LOWERING_SCHEMA_VERSION = 1


class LoweringError(ValueError):
    """Base exception for semantic-lowering failures."""


class UnsupportedWeaveError(LoweringError):
    """Raised when no executable v1 mapping exists for a State Weave."""


class OperandBindingError(LoweringError):
    """Raised when concrete machine operands do not satisfy a lowering form."""


class SemanticAction(str, Enum):
    HALT = "halt"
    NEGATE = "negate"
    COMPARE = "compare"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"


class MemoryEffect(str, Enum):
    NONE = "none"
    READ = "read"
    WRITE = "write"


@dataclass(frozen=True, slots=True)
class OperandBindings:
    """Concrete machine resources bound to an otherwise abstract State Weave."""

    target_register: int | None = None
    source_register: int | None = None
    left_register: int | None = None
    right_register: int | None = None
    base_register: int | None = None
    offset: int | None = None

    def __post_init__(self) -> None:
        for name in (
            "target_register",
            "source_register",
            "left_register",
            "right_register",
            "base_register",
        ):
            value = getattr(self, name)
            if value is not None and not 0 <= value < REGISTER_COUNT:
                raise OperandBindingError(
                    f"{name} must be a TD-1 register index in 0..{REGISTER_COUNT - 1}"
                )

    def provided_names(self) -> tuple[str, ...]:
        names: list[str] = []
        for name in (
            "target_register",
            "source_register",
            "left_register",
            "right_register",
            "base_register",
            "offset",
        ):
            if getattr(self, name) is not None:
                names.append(name)
        return tuple(names)

    def as_dict(self) -> dict[str, int]:
        return {
            name: int(getattr(self, name))
            for name in self.provided_names()
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "OperandBindings":
        allowed = {
            "target_register",
            "source_register",
            "left_register",
            "right_register",
            "base_register",
            "offset",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise OperandBindingError(
                "unknown operand binding fields: " + ", ".join(sorted(unknown))
            )
        values = {
            name: int(payload[name]) if name in payload else None
            for name in allowed
        }
        return cls(**values)


@dataclass(frozen=True, slots=True)
class LoweringForm:
    """Introspection record for one supported v1 State Weave form."""

    canonical_weave: str
    action: SemanticAction
    required_operands: tuple[str, ...]
    optional_operands: tuple[str, ...] = ()
    note: str = ""

    @property
    def allowed_operands(self) -> tuple[str, ...]:
        return self.required_operands + self.optional_operands

    def as_dict(self) -> dict[str, object]:
        return {
            "weave": self.canonical_weave,
            "action": self.action.value,
            "required_operands": list(self.required_operands),
            "optional_operands": list(self.optional_operands),
            "note": self.note,
        }


_SUPPORTED_FORMS: tuple[LoweringForm, ...] = (
    LoweringForm(
        "EXECUTION:-",
        SemanticAction.HALT,
        (),
        note="Project-defined halt convention.",
    ),
    LoweringForm(
        "TRANSFORM:-",
        SemanticAction.NEGATE,
        ("target_register",),
        note="Project-defined arithmetic sign inversion.",
    ),
    LoweringForm(
        "STATE:0",
        SemanticAction.COMPARE,
        ("left_register", "right_register"),
        note="Project-defined neutral state inspection via ternary comparison.",
    ),
    LoweringForm(
        "MEMORY:0",
        SemanticAction.MEMORY_READ,
        ("target_register", "base_register"),
        ("offset",),
        note="Project-defined neutral memory inspection/read.",
    ),
    LoweringForm(
        "MEMORY:+",
        SemanticAction.MEMORY_WRITE,
        ("source_register", "base_register"),
        ("offset",),
        note="Project-defined positive memory acquisition/store.",
    ),
)

_FORMS_BY_WEAVE = {form.canonical_weave: form for form in _SUPPORTED_FORMS}


def supported_lowerings() -> tuple[LoweringForm, ...]:
    """Return the complete, stable v1 executable lowering surface."""
    return _SUPPORTED_FORMS


def supports_weave(weave: StateWeave) -> bool:
    return weave.canonical in _FORMS_BY_WEAVE


def _instruction_as_dict(instruction: Instruction) -> dict[str, object]:
    return {
        "op": instruction.op.name,
        "a": instruction.a,
        "b": instruction.b,
        "imm": instruction.imm,
    }


def _instruction_from_dict(payload: Mapping[str, object]) -> Instruction:
    try:
        op = Op[str(payload["op"])]
    except KeyError as exc:
        raise LoweringError(f"unknown logical opcode {payload.get('op')!r}") from exc
    return Instruction(
        op=op,
        a=int(payload.get("a", 0)),
        b=int(payload.get("b", 0)),
        imm=int(payload.get("imm", 0)),
    )


@dataclass(frozen=True, slots=True)
class LoweredWeave:
    """Versioned deterministic compiler result for one bound State Weave."""

    weave: StateWeave
    action: SemanticAction
    bindings: OperandBindings
    instructions: tuple[Instruction, ...]
    register_reads: tuple[int, ...]
    register_writes: tuple[int, ...]
    memory_effect: MemoryEffect = MemoryEffect.NONE
    schema: str = LOWERING_SCHEMA
    version: int = LOWERING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != LOWERING_SCHEMA:
            raise LoweringError(f"unsupported lowering schema {self.schema!r}")
        if self.version != LOWERING_SCHEMA_VERSION:
            raise LoweringError(f"unsupported lowering schema version {self.version}")
        if not self.instructions:
            raise LoweringError("a lowered weave must contain at least one logical instruction")
        reads = tuple(sorted(set(self.register_reads)))
        writes = tuple(sorted(set(self.register_writes)))
        for index in reads + writes:
            if not 0 <= index < REGISTER_COUNT:
                raise LoweringError(f"lowered register index out of range: {index}")
        object.__setattr__(self, "register_reads", reads)
        object.__setattr__(self, "register_writes", writes)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "weave": self.weave.canonical,
            "action": self.action.value,
            "bindings": self.bindings.as_dict(),
            "instructions": [_instruction_as_dict(item) for item in self.instructions],
            "register_reads": list(self.register_reads),
            "register_writes": list(self.register_writes),
            "memory_effect": self.memory_effect.value,
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

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "LoweredWeave":
        raw_instructions = payload.get("instructions")
        raw_reads = payload.get("register_reads")
        raw_writes = payload.get("register_writes")
        raw_bindings = payload.get("bindings")
        if not isinstance(raw_instructions, list):
            raise LoweringError("lowering instructions must be a list")
        if not isinstance(raw_reads, list) or not isinstance(raw_writes, list):
            raise LoweringError("lowering register metadata must be lists")
        if not isinstance(raw_bindings, Mapping):
            raise LoweringError("lowering bindings must be an object")
        lowered = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            weave=StateWeave.parse(str(payload["weave"])),
            action=SemanticAction(str(payload["action"])),
            bindings=OperandBindings.from_dict(raw_bindings),
            instructions=tuple(_instruction_from_dict(item) for item in raw_instructions),
            register_reads=tuple(int(item) for item in raw_reads),
            register_writes=tuple(int(item) for item in raw_writes),
            memory_effect=MemoryEffect(str(payload["memory_effect"])),
        )
        expected = lower_state_weave(lowered.weave, lowered.bindings)
        if expected.canonical_json() != lowered.canonical_json():
            raise LoweringError("serialized lowering does not match the v1 compiler result")
        return lowered

    @classmethod
    def from_json(cls, text: str) -> "LoweredWeave":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise LoweringError("semantic lowering JSON root must be an object")
        return cls.from_dict(payload)


def _require_operands(form: LoweringForm, bindings: OperandBindings) -> None:
    provided = set(bindings.provided_names())
    required = set(form.required_operands)
    allowed = set(form.allowed_operands)
    missing = sorted(required - provided)
    extra = sorted(provided - allowed)
    if missing:
        raise OperandBindingError(
            f"{form.canonical_weave} missing operands: " + ", ".join(missing)
        )
    if extra:
        raise OperandBindingError(
            f"{form.canonical_weave} does not accept operands: " + ", ".join(extra)
        )


def lower_state_weave(
    weave: StateWeave,
    bindings: OperandBindings | None = None,
) -> LoweredWeave:
    """Lower one supported bound State Weave into logical TD-1 instructions."""
    form = _FORMS_BY_WEAVE.get(weave.canonical)
    if form is None:
        raise UnsupportedWeaveError(
            f"State Weave {weave.canonical} has no executable lowering in schema v1"
        )
    bindings = bindings or OperandBindings()
    _require_operands(form, bindings)

    if form.action is SemanticAction.HALT:
        return LoweredWeave(
            weave,
            form.action,
            bindings,
            (Instruction(Op.HALT),),
            (),
            (),
        )

    if form.action is SemanticAction.NEGATE:
        target = bindings.target_register
        assert target is not None
        return LoweredWeave(
            weave,
            form.action,
            bindings,
            (Instruction(Op.NEG, a=target),),
            (target,),
            (target,),
        )

    if form.action is SemanticAction.COMPARE:
        left = bindings.left_register
        right = bindings.right_register
        assert left is not None and right is not None
        return LoweredWeave(
            weave,
            form.action,
            bindings,
            (Instruction(Op.CMP, a=left, b=right),),
            (left, right),
            (),
        )

    if form.action is SemanticAction.MEMORY_READ:
        target = bindings.target_register
        base = bindings.base_register
        assert target is not None and base is not None
        offset = bindings.offset or 0
        return LoweredWeave(
            weave,
            form.action,
            bindings,
            (Instruction(Op.LD, a=target, b=base, imm=offset),),
            (base,),
            (target,),
            MemoryEffect.READ,
        )

    if form.action is SemanticAction.MEMORY_WRITE:
        source = bindings.source_register
        base = bindings.base_register
        assert source is not None and base is not None
        offset = bindings.offset or 0
        return LoweredWeave(
            weave,
            form.action,
            bindings,
            (Instruction(Op.ST, a=source, b=base, imm=offset),),
            (source, base),
            (),
            MemoryEffect.WRITE,
        )

    raise LoweringError(f"unimplemented semantic action {form.action.value}")


# Guard the v1 registry against accidental drift between declared forms and
# compiler branches. These are intentionally single-root operations for now.
assert _FORMS_BY_WEAVE["EXECUTION:-"].action is SemanticAction.HALT
assert StateWeave((SemanticRoot.EXECUTION,), Modifier.NEGATIVE).canonical == "EXECUTION:-"
