"""Deterministic execution and geometry-transition traces for TD-1.

The trace layer records what changed without introducing physical instruction
encoding, animation timing, or visual effects. Future Relic Mode motion should
consume this event stream rather than invent state transitions in a frontend.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

from .geometry import GeometryPrimitive, GeometryScene
from .machine import Instruction, Machine, ProgramCounterError, StepLimitExceeded
from .render_state import RenderState

TRACE_SCHEMA = "td1.execution-trace"
TRACE_SCHEMA_VERSION = 1
GEOMETRY_DELTA_SCHEMA = "td1.geometry-delta"
GEOMETRY_DELTA_SCHEMA_VERSION = 1


class TraceError(ValueError):
    """Raised when a deterministic TD-1 trace cannot be validated or replayed."""


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True, slots=True)
class RegisterDelta:
    index: int
    before: str
    after: str

    def as_dict(self) -> dict[str, object]:
        return {"index": self.index, "before": self.before, "after": self.after}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "RegisterDelta":
        return cls(int(payload["index"]), str(payload["before"]), str(payload["after"]))


@dataclass(frozen=True, slots=True)
class MemoryDelta:
    address: int
    before: str
    after: str

    def as_dict(self) -> dict[str, object]:
        return {"address": self.address, "before": self.before, "after": self.after}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "MemoryDelta":
        return cls(int(payload["address"]), str(payload["before"]), str(payload["after"]))


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    """One logical instruction transition in the reference machine."""

    event_index: int
    machine_step: int
    instruction_index: int
    op: str
    a: int
    b: int
    imm: int
    before_digest: str
    after_digest: str
    ip_before: int
    ip_after: int
    cond_before: int
    cond_after: int
    halted_before: bool
    halted_after: bool
    register_deltas: tuple[RegisterDelta, ...] = ()
    memory_deltas: tuple[MemoryDelta, ...] = ()

    def __post_init__(self) -> None:
        if self.event_index < 0 or self.machine_step <= 0:
            raise TraceError("event_index must be nonnegative and machine_step must be positive")
        if self.cond_before not in (-1, 0, 1) or self.cond_after not in (-1, 0, 1):
            raise TraceError("event condition states must be -1, 0, or +1")
        register_indices = tuple(item.index for item in self.register_deltas)
        if register_indices != tuple(sorted(set(register_indices))):
            raise TraceError("register deltas must have unique ascending indices")
        memory_addresses = tuple(item.address for item in self.memory_deltas)
        if memory_addresses != tuple(sorted(set(memory_addresses))):
            raise TraceError("memory deltas must have unique ascending addresses")

    def as_dict(self) -> dict[str, object]:
        return {
            "event_index": self.event_index,
            "machine_step": self.machine_step,
            "instruction_index": self.instruction_index,
            "instruction": {
                "op": self.op,
                "a": self.a,
                "b": self.b,
                "imm": self.imm,
            },
            "before_digest": self.before_digest,
            "after_digest": self.after_digest,
            "ip_before": self.ip_before,
            "ip_after": self.ip_after,
            "cond_before": self.cond_before,
            "cond_after": self.cond_after,
            "halted_before": self.halted_before,
            "halted_after": self.halted_after,
            "register_deltas": [item.as_dict() for item in self.register_deltas],
            "memory_deltas": [item.as_dict() for item in self.memory_deltas],
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ExecutionEvent":
        instruction = payload.get("instruction")
        register_deltas = payload.get("register_deltas", [])
        memory_deltas = payload.get("memory_deltas", [])
        if not isinstance(instruction, Mapping):
            raise TraceError("execution event instruction must be an object")
        if not isinstance(register_deltas, list) or not isinstance(memory_deltas, list):
            raise TraceError("execution event deltas must be lists")
        return cls(
            event_index=int(payload["event_index"]),
            machine_step=int(payload["machine_step"]),
            instruction_index=int(payload["instruction_index"]),
            op=str(instruction["op"]),
            a=int(instruction["a"]),
            b=int(instruction["b"]),
            imm=int(instruction["imm"]),
            before_digest=str(payload["before_digest"]),
            after_digest=str(payload["after_digest"]),
            ip_before=int(payload["ip_before"]),
            ip_after=int(payload["ip_after"]),
            cond_before=int(payload["cond_before"]),
            cond_after=int(payload["cond_after"]),
            halted_before=bool(payload["halted_before"]),
            halted_after=bool(payload["halted_after"]),
            register_deltas=tuple(RegisterDelta.from_dict(item) for item in register_deltas),
            memory_deltas=tuple(MemoryDelta.from_dict(item) for item in memory_deltas),
        )


@dataclass(frozen=True, slots=True)
class ExecutionTrace:
    """Versioned deterministic trace for a complete execution or exact prefix."""

    program_digest: str
    initial_state: RenderState
    final_state: RenderState
    events: tuple[ExecutionEvent, ...]
    schema: str = TRACE_SCHEMA
    version: int = TRACE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != TRACE_SCHEMA:
            raise TraceError(f"unsupported execution trace schema {self.schema!r}")
        if self.version != TRACE_SCHEMA_VERSION:
            raise TraceError(f"unsupported execution trace schema version {self.version}")
        indices = tuple(event.event_index for event in self.events)
        if indices != tuple(range(len(self.events))):
            raise TraceError("execution event indices must be contiguous from zero")
        if not self.events:
            if self.initial_state.machine_digest != self.final_state.machine_digest:
                raise TraceError("empty trace must preserve the initial machine state")
            return
        if self.events[0].before_digest != self.initial_state.machine_digest:
            raise TraceError("first event does not begin at the initial machine digest")
        if self.events[-1].after_digest != self.final_state.machine_digest:
            raise TraceError("last event does not end at the final machine digest")
        for left, right in zip(self.events, self.events[1:], strict=False):
            if left.after_digest != right.before_digest:
                raise TraceError("execution event digest chain is broken")
            if left.machine_step + 1 != right.machine_step:
                raise TraceError("execution machine steps are not contiguous")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "program_digest": self.program_digest,
            "initial_state": self.initial_state.as_dict(),
            "final_state": self.final_state.as_dict(),
            "events": [event.as_dict() for event in self.events],
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ExecutionTrace":
        initial_state = payload.get("initial_state")
        final_state = payload.get("final_state")
        events = payload.get("events")
        if not isinstance(initial_state, dict) or not isinstance(final_state, dict):
            raise TraceError("execution trace states must be objects")
        if not isinstance(events, list):
            raise TraceError("execution trace events must be a list")
        return cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            program_digest=str(payload["program_digest"]),
            initial_state=RenderState.from_dict(initial_state),
            final_state=RenderState.from_dict(final_state),
            events=tuple(ExecutionEvent.from_dict(item) for item in events),
        )

    @classmethod
    def from_json(cls, text: str) -> "ExecutionTrace":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise TraceError("execution trace JSON root must be an object")
        return cls.from_dict(payload)


def logical_program_digest(program: Sequence[Instruction]) -> str:
    """Fingerprint logical instruction semantics without freezing physical encoding."""
    payload = [
        {
            "op": instruction.op.name,
            "a": instruction.a,
            "b": instruction.b,
            "imm": instruction.imm,
        }
        for instruction in program
    ]
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


class TraceRecorder:
    """Incrementally execute the reference machine while recording canonical events.

    The recorder owns no alternate machine semantics. Every transition is produced
    by ``Machine.step()`` and captured in the same ``ExecutionEvent`` format used by
    full traces. A recorder may therefore expose a complete halted trace or an exact
    non-halted prefix for debugger and inspection workflows.
    """

    def __init__(
        self,
        program: Sequence[Instruction],
        *,
        initial_machine: Machine | None = None,
    ) -> None:
        self.program = tuple(program)
        self.program_digest = logical_program_digest(self.program)
        self._machine = (
            Machine()
            if initial_machine is None
            else RenderState.capture(initial_machine).restore_machine()
        )
        self.initial_state = RenderState.capture(self._machine)
        self._events: list[ExecutionEvent] = []

    @property
    def events(self) -> tuple[ExecutionEvent, ...]:
        return tuple(self._events)

    @property
    def halted(self) -> bool:
        return self._machine.halted

    @property
    def machine_steps(self) -> int:
        return self._machine.steps

    def current_state(self) -> RenderState:
        return RenderState.capture(self._machine)

    def next_instruction(self) -> tuple[int, Instruction]:
        if self._machine.halted:
            raise TraceError("halted machine has no next instruction")
        instruction_index = self._machine.ip
        if not 0 <= instruction_index < len(self.program):
            raise ProgramCounterError(
                f"instruction pointer out of program range: {instruction_index}"
            )
        return instruction_index, self.program[instruction_index]

    def step(self) -> ExecutionEvent:
        if self._machine.halted:
            raise TraceError("cannot record a step after HALT")

        instruction_index, instruction = self.next_instruction()
        before_digest = self._machine.state_digest(include_memory=True)
        before_registers = tuple(str(word) for word in self._machine.registers)
        before_memory = tuple(str(word) for word in self._machine.memory)
        ip_before = self._machine.ip
        cond_before = self._machine.cond
        halted_before = self._machine.halted

        self._machine.step(self.program)

        after_registers = tuple(str(word) for word in self._machine.registers)
        after_memory = tuple(str(word) for word in self._machine.memory)
        register_deltas = tuple(
            RegisterDelta(index, before, after)
            for index, (before, after) in enumerate(
                zip(before_registers, after_registers, strict=True)
            )
            if before != after
        )
        memory_deltas = tuple(
            MemoryDelta(address, before, after)
            for address, (before, after) in enumerate(
                zip(before_memory, after_memory, strict=True)
            )
            if before != after
        )
        event = ExecutionEvent(
            event_index=len(self._events),
            machine_step=self._machine.steps,
            instruction_index=instruction_index,
            op=instruction.op.name,
            a=instruction.a,
            b=instruction.b,
            imm=instruction.imm,
            before_digest=before_digest,
            after_digest=self._machine.state_digest(include_memory=True),
            ip_before=ip_before,
            ip_after=self._machine.ip,
            cond_before=cond_before,
            cond_after=self._machine.cond,
            halted_before=halted_before,
            halted_after=self._machine.halted,
            register_deltas=register_deltas,
            memory_deltas=memory_deltas,
        )
        self._events.append(event)
        return event

    def trace(self) -> ExecutionTrace:
        return ExecutionTrace(
            program_digest=self.program_digest,
            initial_state=self.initial_state,
            final_state=self.current_state(),
            events=self.events,
        )


def trace_program(
    program: Sequence[Instruction],
    *,
    initial_machine: Machine | None = None,
    max_steps: int = 100_000,
) -> ExecutionTrace:
    """Execute a logical program to HALT while recording replayable transitions."""
    if max_steps <= 0:
        raise ValueError("max_steps must be positive")
    recorder = TraceRecorder(program, initial_machine=initial_machine)

    while not recorder.halted:
        if recorder.machine_steps >= max_steps:
            raise StepLimitExceeded(f"execution exceeded max_steps={max_steps}")
        recorder.step()

    return recorder.trace()


def verify_execution_trace(program: Sequence[Instruction], trace: ExecutionTrace) -> None:
    """Replay a complete trace or exact trace prefix and require canonical equality."""
    if logical_program_digest(program) != trace.program_digest:
        raise TraceError("logical program digest does not match execution trace")

    recorder = TraceRecorder(
        program,
        initial_machine=trace.initial_state.restore_machine(),
    )
    for _ in trace.events:
        if recorder.halted:
            raise TraceError("execution trace records events after the replay machine halted")
        recorder.step()
    replay = recorder.trace()
    if replay.canonical_json() != trace.canonical_json():
        raise TraceError("execution trace replay diverged from recorded trace")


class PrimitiveChangeKind(str, Enum):
    APPEAR = "appear"
    DISAPPEAR = "disappear"
    MOVE = "move"
    TOPOLOGY = "topology"
    METADATA = "metadata"


@dataclass(frozen=True, slots=True)
class PrimitiveChange:
    primitive_id: str
    kind: PrimitiveChangeKind
    before: GeometryPrimitive | None
    after: GeometryPrimitive | None

    def __post_init__(self) -> None:
        if not self.primitive_id.strip():
            raise TraceError("primitive change ID must not be empty")
        if self.kind is PrimitiveChangeKind.APPEAR and (
            self.before is not None or self.after is None
        ):
            raise TraceError("appear change requires only an after primitive")
        if self.kind is PrimitiveChangeKind.DISAPPEAR and (
            self.before is None or self.after is not None
        ):
            raise TraceError("disappear change requires only a before primitive")
        terminal = {PrimitiveChangeKind.APPEAR, PrimitiveChangeKind.DISAPPEAR}
        if self.kind not in terminal and (self.before is None or self.after is None):
            raise TraceError("primitive mutation requires both before and after primitives")

    def as_dict(self) -> dict[str, object]:
        return {
            "primitive_id": self.primitive_id,
            "kind": self.kind.value,
            "before": self.before.as_dict() if self.before is not None else None,
            "after": self.after.as_dict() if self.after is not None else None,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "PrimitiveChange":
        before = payload.get("before")
        after = payload.get("after")
        return cls(
            primitive_id=str(payload["primitive_id"]),
            kind=PrimitiveChangeKind(str(payload["kind"])),
            before=GeometryPrimitive.from_dict(before) if isinstance(before, Mapping) else None,
            after=GeometryPrimitive.from_dict(after) if isinstance(after, Mapping) else None,
        )


@dataclass(frozen=True, slots=True)
class GeometryDelta:
    """Deterministic difference between two geometry scenes."""

    before_scene_digest: str
    after_scene_digest: str
    before_render_digest: str
    after_render_digest: str
    changes: tuple[PrimitiveChange, ...]
    schema: str = GEOMETRY_DELTA_SCHEMA
    version: int = GEOMETRY_DELTA_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != GEOMETRY_DELTA_SCHEMA:
            raise TraceError(f"unsupported geometry delta schema {self.schema!r}")
        if self.version != GEOMETRY_DELTA_SCHEMA_VERSION:
            raise TraceError(f"unsupported geometry delta schema version {self.version}")
        ordered = tuple(sorted(self.changes, key=lambda item: item.primitive_id))
        if len({item.primitive_id for item in ordered}) != len(ordered):
            raise TraceError("geometry delta may change each primitive ID at most once")
        object.__setattr__(self, "changes", ordered)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "before_scene_digest": self.before_scene_digest,
            "after_scene_digest": self.after_scene_digest,
            "before_render_digest": self.before_render_digest,
            "after_render_digest": self.after_render_digest,
            "changes": [change.as_dict() for change in self.changes],
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "GeometryDelta":
        changes = payload.get("changes")
        if not isinstance(changes, list):
            raise TraceError("geometry delta changes must be a list")
        return cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            before_scene_digest=str(payload["before_scene_digest"]),
            after_scene_digest=str(payload["after_scene_digest"]),
            before_render_digest=str(payload["before_render_digest"]),
            after_render_digest=str(payload["after_render_digest"]),
            changes=tuple(PrimitiveChange.from_dict(item) for item in changes),
        )

    @classmethod
    def from_json(cls, text: str) -> "GeometryDelta":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise TraceError("geometry delta JSON root must be an object")
        return cls.from_dict(payload)


def _primitive_metadata(primitive: GeometryPrimitive) -> tuple[object, ...]:
    return (
        primitive.kind,
        primitive.role,
        primitive.scale_milli,
        primitive.glyph_id,
        primitive.semantic_root_id,
        primitive.state_value,
        primitive.motifs,
    )


def _is_translation(before: GeometryPrimitive, after: GeometryPrimitive) -> bool:
    if len(before.points) != len(after.points) or not before.points:
        return False
    old = before.points[0]
    new = after.points[0]
    delta = (new.q - old.q, new.r - old.r, new.z - old.z)
    if delta == (0, 0, 0):
        return False
    return all(
        (
            new_point.q - old_point.q,
            new_point.r - old_point.r,
            new_point.z - old_point.z,
        )
        == delta
        for old_point, new_point in zip(before.points, after.points, strict=True)
    )


def diff_geometry(before: GeometryScene, after: GeometryScene) -> GeometryDelta:
    """Classify stable-ID geometry changes without assigning animation timing."""
    before_by_id = {item.primitive_id: item for item in before.primitives}
    after_by_id = {item.primitive_id: item for item in after.primitives}
    changes: list[PrimitiveChange] = []

    for primitive_id in sorted(set(before_by_id) | set(after_by_id)):
        old = before_by_id.get(primitive_id)
        new = after_by_id.get(primitive_id)
        if old is None and new is not None:
            changes.append(PrimitiveChange(primitive_id, PrimitiveChangeKind.APPEAR, None, new))
            continue
        if old is not None and new is None:
            changes.append(
                PrimitiveChange(primitive_id, PrimitiveChangeKind.DISAPPEAR, old, None)
            )
            continue
        if old is None or new is None or old == new:
            continue
        if old.points == new.points:
            kind = PrimitiveChangeKind.METADATA
        elif _primitive_metadata(old) == _primitive_metadata(new) and _is_translation(old, new):
            kind = PrimitiveChangeKind.MOVE
        else:
            kind = PrimitiveChangeKind.TOPOLOGY
        changes.append(PrimitiveChange(primitive_id, kind, old, new))

    return GeometryDelta(
        before_scene_digest=before.digest(),
        after_scene_digest=after.digest(),
        before_render_digest=before.source_render_digest,
        after_render_digest=after.source_render_digest,
        changes=tuple(changes),
    )
