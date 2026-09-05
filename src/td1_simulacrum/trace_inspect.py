"""Deterministic time-travel inspection for TD-1 execution traces.

This layer consumes existing ``td1.execution-trace`` truth. It reconstructs
exact logical machine checkpoints from recorded deltas and offers deterministic
queries over those events. It does not add execution semantics, timing, or
physical instruction claims.
"""

from __future__ import annotations

from dataclasses import dataclass

from .machine import MEMORY_WORDS, REGISTER_COUNT, Machine, Op
from .machine_state import MachineState
from .ternary import TernaryWord
from .trace import ExecutionEvent, ExecutionTrace


class TraceInspectionError(ValueError):
    """Raised when trace inspection cannot reconstruct or validate machine state."""


def _validate_position(trace: ExecutionTrace, position: int) -> None:
    if type(position) is not int:
        raise TraceInspectionError("trace position must be an integer")
    if not 0 <= position <= len(trace.events):
        raise TraceInspectionError(
            f"trace position must be within 0..{len(trace.events)}, got {position}"
        )


def _apply_event(machine: Machine, event: ExecutionEvent) -> None:
    before_digest = machine.state_digest(include_memory=True)
    if before_digest != event.before_digest:
        raise TraceInspectionError(
            f"event {event.event_index} before digest does not match reconstructed machine"
        )
    if machine.ip != event.ip_before:
        raise TraceInspectionError(f"event {event.event_index} ip_before mismatch")
    if machine.cond != event.cond_before:
        raise TraceInspectionError(f"event {event.event_index} cond_before mismatch")
    if machine.halted != event.halted_before:
        raise TraceInspectionError(f"event {event.event_index} halted_before mismatch")
    if machine.steps + 1 != event.machine_step:
        raise TraceInspectionError(f"event {event.event_index} machine_step mismatch")

    for delta in event.register_deltas:
        if not 0 <= delta.index < REGISTER_COUNT:
            raise TraceInspectionError(
                f"event {event.event_index} register delta outside machine range"
            )
        if str(machine.registers[delta.index]) != delta.before:
            raise TraceInspectionError(
                f"event {event.event_index} register R{delta.index} before value mismatch"
            )
        try:
            machine.registers[delta.index] = TernaryWord.parse(delta.after)
        except ValueError as exc:
            raise TraceInspectionError(
                f"event {event.event_index} register R{delta.index} has invalid ternary value"
            ) from exc

    for delta in event.memory_deltas:
        if not 0 <= delta.address < MEMORY_WORDS:
            raise TraceInspectionError(
                f"event {event.event_index} memory delta outside machine range"
            )
        if str(machine.memory[delta.address]) != delta.before:
            raise TraceInspectionError(
                f"event {event.event_index} memory[{delta.address}] before value mismatch"
            )
        try:
            machine.memory[delta.address] = TernaryWord.parse(delta.after)
        except ValueError as exc:
            raise TraceInspectionError(
                f"event {event.event_index} memory[{delta.address}] has invalid ternary value"
            ) from exc

    machine.ip = event.ip_after
    machine.cond = event.cond_after
    machine.halted = event.halted_after
    machine.steps = event.machine_step

    after_digest = machine.state_digest(include_memory=True)
    if after_digest != event.after_digest:
        raise TraceInspectionError(
            f"event {event.event_index} deltas do not reconstruct the claimed after digest"
        )


def trace_state_at(trace: ExecutionTrace, position: int) -> MachineState:
    """Reconstruct exact machine truth at one trace boundary.

    ``position=0`` returns the trace initial state. ``position=N`` returns the
    state after the first N events. Every traversed delta is checked against its
    recorded before/after digest chain.
    """
    _validate_position(trace, position)
    machine = trace.initial_state.restore_machine()
    if machine.state_digest(include_memory=True) != trace.initial_state.machine_digest:
        raise TraceInspectionError("trace initial state failed machine reconstruction")

    for event in trace.events[:position]:
        _apply_event(machine, event)

    if position == len(trace.events):
        final_digest = machine.state_digest(include_memory=True)
        if final_digest != trace.final_state.machine_digest:
            raise TraceInspectionError("reconstructed final state disagrees with trace final state")

    return MachineState.capture(machine)


@dataclass(slots=True)
class TraceCursor:
    """Seekable deterministic cursor over immutable execution-trace boundaries."""

    trace: ExecutionTrace
    position: int = 0

    def __post_init__(self) -> None:
        _validate_position(self.trace, self.position)

    @property
    def at_start(self) -> bool:
        return self.position == 0

    @property
    def at_end(self) -> bool:
        return self.position == len(self.trace.events)

    def state(self) -> MachineState:
        return trace_state_at(self.trace, self.position)

    def seek(self, position: int) -> MachineState:
        _validate_position(self.trace, position)
        self.position = position
        return self.state()

    def step_forward(self) -> MachineState:
        if self.at_end:
            raise TraceInspectionError("trace cursor is already at the final boundary")
        self.position += 1
        return self.state()

    def step_backward(self) -> MachineState:
        if self.at_start:
            raise TraceInspectionError("trace cursor is already at the initial boundary")
        self.position -= 1
        return self.state()


@dataclass(frozen=True, slots=True)
class TraceQuery:
    """Deterministic AND-of-groups query over execution events.

    Values within one group are ORed. For example, ``operations=("ADD", "SUB")``
    matches either opcode, while also supplying ``registers=(1,)`` requires the
    matching event to touch R1.
    """

    instruction_indices: tuple[int, ...] = ()
    operations: tuple[str, ...] = ()
    registers: tuple[int, ...] = ()
    memory_addresses: tuple[int, ...] = ()
    condition_change: bool = False
    halt_transition: bool = False

    def __post_init__(self) -> None:
        indices = tuple(sorted(set(self.instruction_indices)))
        if any(type(value) is not int or value < 0 for value in indices):
            raise TraceInspectionError("instruction query indices must be nonnegative integers")

        operation_names = {op.name for op in Op}
        operations = tuple(sorted({str(value).strip().upper() for value in self.operations}))
        unknown = tuple(value for value in operations if value not in operation_names)
        if unknown:
            raise TraceInspectionError(f"unknown logical opcode(s): {', '.join(unknown)}")

        registers = tuple(sorted(set(self.registers)))
        if any(type(value) is not int or not 0 <= value < REGISTER_COUNT for value in registers):
            raise TraceInspectionError(f"register query must be within R0..R{REGISTER_COUNT - 1}")

        memory = tuple(sorted(set(self.memory_addresses)))
        if any(type(value) is not int or not 0 <= value < MEMORY_WORDS for value in memory):
            raise TraceInspectionError(
                f"memory query address must be within 0..{MEMORY_WORDS - 1}"
            )

        object.__setattr__(self, "instruction_indices", indices)
        object.__setattr__(self, "operations", operations)
        object.__setattr__(self, "registers", registers)
        object.__setattr__(self, "memory_addresses", memory)

    def as_dict(self) -> dict[str, object]:
        return {
            "instruction_indices": list(self.instruction_indices),
            "operations": list(self.operations),
            "registers": list(self.registers),
            "memory_addresses": list(self.memory_addresses),
            "condition_change": self.condition_change,
            "halt_transition": self.halt_transition,
        }

    def matches(self, event: ExecutionEvent) -> bool:
        if self.instruction_indices and event.instruction_index not in self.instruction_indices:
            return False
        if self.operations and event.op not in self.operations:
            return False
        if self.registers:
            touched = {delta.index for delta in event.register_deltas}
            if not touched.intersection(self.registers):
                return False
        if self.memory_addresses:
            touched = {delta.address for delta in event.memory_deltas}
            if not touched.intersection(self.memory_addresses):
                return False
        if self.condition_change and event.cond_before == event.cond_after:
            return False
        if self.halt_transition and (event.halted_before or not event.halted_after):
            return False
        return True


def find_trace_events(
    trace: ExecutionTrace,
    query: TraceQuery | None = None,
) -> tuple[ExecutionEvent, ...]:
    """Return trace events matching a deterministic query, preserving trace order."""
    selected = query if query is not None else TraceQuery()
    return tuple(event for event in trace.events if selected.matches(event))
