"""Deterministic live stop/breakpoint debugging for the TD-1 reference machine.

Debugger stops are observations around ordinary ``Machine.step()`` execution.
They do not define alternate execution semantics, reverse instructions, timing,
or physical behavior. Every executed instruction is captured in an ordinary
``td1.execution-trace`` prefix produced by ``TraceRecorder``.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

from .machine import MEMORY_WORDS, REGISTER_COUNT, Instruction, Machine, Op
from .strict_json import require_canonical_mapping
from .trace import ExecutionEvent, ExecutionTrace, TraceError, TraceRecorder, verify_execution_trace

DEBUG_RUN_SCHEMA = "td1.debug-run"
DEBUG_RUN_SCHEMA_VERSION = 1


class DebugError(ValueError):
    """Raised when a deterministic debugger artifact or stop specification is invalid."""


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


class DebugStopKind(str, Enum):
    HALTED = "halted"
    BREAKPOINT = "breakpoint"
    WATCHPOINT = "watchpoint"
    EVENT_BUDGET = "event_budget"


@dataclass(frozen=True, slots=True)
class DebugStopSpec:
    """Deterministic pre-instruction breakpoints and post-instruction watchpoints."""

    instruction_indices: tuple[int, ...] = ()
    operations: tuple[str, ...] = ()
    registers: tuple[int, ...] = ()
    memory_addresses: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        instruction_indices = tuple(sorted(set(self.instruction_indices)))
        if any(type(value) is not int or value < 0 for value in instruction_indices):
            raise DebugError("breakpoint instruction indices must be nonnegative integers")

        operation_names = {op.name for op in Op}
        operations = tuple(sorted({str(value).strip().upper() for value in self.operations}))
        unknown = tuple(value for value in operations if value not in operation_names)
        if unknown:
            raise DebugError(f"unknown logical breakpoint opcode(s): {', '.join(unknown)}")

        registers = tuple(sorted(set(self.registers)))
        if any(type(value) is not int or not 0 <= value < REGISTER_COUNT for value in registers):
            raise DebugError(f"watch register must be within R0..R{REGISTER_COUNT - 1}")

        memory_addresses = tuple(sorted(set(self.memory_addresses)))
        if any(
            type(value) is not int or not 0 <= value < MEMORY_WORDS
            for value in memory_addresses
        ):
            raise DebugError(f"watch memory address must be within 0..{MEMORY_WORDS - 1}")

        object.__setattr__(self, "instruction_indices", instruction_indices)
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "registers", registers)
        object.__setattr__(self, "memory_addresses", memory_addresses)

    def as_dict(self) -> dict[str, object]:
        return {
            "instruction_indices": list(self.instruction_indices),
            "operations": list(self.operations),
            "registers": list(self.registers),
            "memory_addresses": list(self.memory_addresses),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "DebugStopSpec":
        def _ints(key: str) -> tuple[int, ...]:
            values = payload.get(key, [])
            if not isinstance(values, list):
                raise DebugError(f"debug stop spec {key} must be a list")
            return tuple(int(value) for value in values)

        operations = payload.get("operations", [])
        if not isinstance(operations, list):
            raise DebugError("debug stop spec operations must be a list")
        state = cls(
            instruction_indices=_ints("instruction_indices"),
            operations=tuple(str(value) for value in operations),
            registers=_ints("registers"),
            memory_addresses=_ints("memory_addresses"),
        )
        require_canonical_mapping(payload, state.as_dict(), label="debug stop spec")
        return state

    def matches_before(self, recorder: TraceRecorder) -> tuple[str, ...]:
        """Return deterministic breakpoint matches before the next instruction executes."""
        instruction_index, instruction = recorder.next_instruction()
        matches: list[str] = []
        if instruction_index in self.instruction_indices:
            matches.append(f"ip:{instruction_index}")
        if instruction.op.name in self.operations:
            matches.append(f"op:{instruction.op.name}")
        return tuple(matches)

    def matches_after(self, event: ExecutionEvent) -> tuple[str, ...]:
        """Return deterministic watchpoint matches caused by one executed event."""
        touched_registers = {delta.index for delta in event.register_deltas}
        touched_memory = {delta.address for delta in event.memory_deltas}
        matches = [
            *(f"register:R{index}" for index in self.registers if index in touched_registers),
            *(
                f"memory:{address}"
                for address in self.memory_addresses
                if address in touched_memory
            ),
        ]
        return tuple(matches)


@dataclass(frozen=True, slots=True)
class DebugRun:
    """Versioned debugger stop artifact containing an exact execution-trace prefix."""

    trace: ExecutionTrace
    stop_spec: DebugStopSpec
    stop_kind: DebugStopKind
    matches: tuple[str, ...]
    event_budget: int
    skip_initial_breakpoint: bool = False
    schema: str = DEBUG_RUN_SCHEMA
    version: int = DEBUG_RUN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != DEBUG_RUN_SCHEMA:
            raise DebugError(f"unsupported debug run schema {self.schema!r}")
        if self.version != DEBUG_RUN_SCHEMA_VERSION:
            raise DebugError(f"unsupported debug run schema version {self.version}")
        if type(self.event_budget) is not int or self.event_budget <= 0:
            raise DebugError("debug event budget must be a positive integer")
        if tuple(self.matches) != tuple(dict.fromkeys(self.matches)):
            raise DebugError("debug stop matches must be unique and ordered")
        if self.stop_kind is DebugStopKind.HALTED:
            if not self.trace.final_state.halted:
                raise DebugError("halted debug stop requires a halted final trace state")
            if self.matches:
                raise DebugError("halted debug stop may not carry breakpoint/watchpoint matches")
        elif self.stop_kind is DebugStopKind.BREAKPOINT:
            if self.trace.final_state.halted or not self.matches:
                raise DebugError("breakpoint stop requires non-halted state and at least one match")
        elif self.stop_kind is DebugStopKind.WATCHPOINT:
            if not self.trace.events or not self.matches:
                raise DebugError(
                    "watchpoint stop requires an executed event and at least one match"
                )
        elif self.stop_kind is DebugStopKind.EVENT_BUDGET:
            if self.trace.final_state.halted:
                raise DebugError("event-budget stop may not claim a halted final state")
            if len(self.trace.events) != self.event_budget:
                raise DebugError(
                    "event-budget stop must end exactly at the configured event budget"
                )
            if self.matches:
                raise DebugError("event-budget stop may not carry breakpoint/watchpoint matches")

    @property
    def position(self) -> int:
        return len(self.trace.events)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "trace": self.trace.as_dict(),
            "stop_spec": self.stop_spec.as_dict(),
            "stop": {
                "kind": self.stop_kind.value,
                "position": self.position,
                "machine_digest": self.trace.final_state.machine_digest,
                "matches": list(self.matches),
            },
            "event_budget": self.event_budget,
            "skip_initial_breakpoint": self.skip_initial_breakpoint,
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "DebugRun":
        trace_payload = payload.get("trace")
        spec_payload = payload.get("stop_spec")
        stop_payload = payload.get("stop")
        if not isinstance(trace_payload, Mapping):
            raise DebugError("debug run trace must be an object")
        if not isinstance(spec_payload, Mapping):
            raise DebugError("debug run stop_spec must be an object")
        if not isinstance(stop_payload, Mapping):
            raise DebugError("debug run stop must be an object")
        matches = stop_payload.get("matches", [])
        if not isinstance(matches, list):
            raise DebugError("debug run stop matches must be a list")

        trace = ExecutionTrace.from_dict(trace_payload)
        position = int(stop_payload["position"])
        if position != len(trace.events):
            raise DebugError("debug stop position must equal the execution-trace event count")
        if str(stop_payload["machine_digest"]) != trace.final_state.machine_digest:
            raise DebugError("debug stop machine digest must match the trace final state")

        state = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            trace=trace,
            stop_spec=DebugStopSpec.from_dict(spec_payload),
            stop_kind=DebugStopKind(str(stop_payload["kind"])),
            matches=tuple(str(value) for value in matches),
            event_budget=int(payload["event_budget"]),
            skip_initial_breakpoint=bool(payload.get("skip_initial_breakpoint", False)),
        )
        require_canonical_mapping(payload, state.as_dict(), label="debug run")
        return state

    @classmethod
    def from_json(cls, text: str) -> "DebugRun":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise DebugError("debug run JSON root must be an object")
        return cls.from_dict(payload)


def _debug_run(
    recorder: TraceRecorder,
    stop_spec: DebugStopSpec,
    stop_kind: DebugStopKind,
    matches: tuple[str, ...],
    event_budget: int,
    skip_initial_breakpoint: bool,
) -> DebugRun:
    return DebugRun(
        trace=recorder.trace(),
        stop_spec=stop_spec,
        stop_kind=stop_kind,
        matches=matches,
        event_budget=event_budget,
        skip_initial_breakpoint=skip_initial_breakpoint,
    )


def run_debug(
    program: Sequence[Instruction],
    *,
    stop_spec: DebugStopSpec | None = None,
    initial_machine: Machine | None = None,
    max_events: int = 100_000,
    skip_initial_breakpoint: bool = False,
) -> DebugRun:
    """Execute until HALT, breakpoint, watchpoint, or deterministic event budget.

    Breakpoints are evaluated before execution. Watchpoints are evaluated after
    the event that touched the watched state. ``skip_initial_breakpoint`` exists
    for checkpoint-resume workflows that intentionally need to step past the
    breakpoint at the supplied initial boundary.
    """
    if type(max_events) is not int or max_events <= 0:
        raise DebugError("max_events must be a positive integer")
    selected = stop_spec if stop_spec is not None else DebugStopSpec()
    recorder = TraceRecorder(program, initial_machine=initial_machine)

    if recorder.halted:
        return _debug_run(
            recorder,
            selected,
            DebugStopKind.HALTED,
            (),
            max_events,
            skip_initial_breakpoint,
        )

    if not skip_initial_breakpoint:
        matches = selected.matches_before(recorder)
        if matches:
            return _debug_run(
                recorder,
                selected,
                DebugStopKind.BREAKPOINT,
                matches,
                max_events,
                skip_initial_breakpoint,
            )

    while True:
        event = recorder.step()
        matches = selected.matches_after(event)
        if matches:
            return _debug_run(
                recorder,
                selected,
                DebugStopKind.WATCHPOINT,
                matches,
                max_events,
                skip_initial_breakpoint,
            )
        if recorder.halted:
            return _debug_run(
                recorder,
                selected,
                DebugStopKind.HALTED,
                (),
                max_events,
                skip_initial_breakpoint,
            )
        if len(recorder.events) >= max_events:
            return _debug_run(
                recorder,
                selected,
                DebugStopKind.EVENT_BUDGET,
                (),
                max_events,
                skip_initial_breakpoint,
            )

        matches = selected.matches_before(recorder)
        if matches:
            return _debug_run(
                recorder,
                selected,
                DebugStopKind.BREAKPOINT,
                matches,
                max_events,
                skip_initial_breakpoint,
            )


def verify_debug_run(program: Sequence[Instruction], run: DebugRun) -> None:
    """Replay a debugger run from its captured initial state and require exact equality."""
    try:
        verify_execution_trace(program, run.trace)
    except TraceError as exc:
        raise DebugError("debug run execution trace failed replay verification") from exc

    replay = run_debug(
        program,
        stop_spec=run.stop_spec,
        initial_machine=run.trace.initial_state.restore_machine(),
        max_events=run.event_budget,
        skip_initial_breakpoint=run.skip_initial_breakpoint,
    )
    if replay.canonical_json() != run.canonical_json():
        raise DebugError("debug run replay diverged from recorded debugger stop")