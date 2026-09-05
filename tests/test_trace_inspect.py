import dataclasses
import json
import sys

import pytest

from td1_simulacrum import (
    ExecutionTrace,
    Machine,
    MachineState,
    RegisterDelta,
    TraceCursor,
    TraceInspectionError,
    TraceQuery,
    assemble,
    find_trace_events,
    trace_program,
    trace_state_at,
)
from td1_simulacrum.trace_cli import main


SOURCE = """
LDI R0, 2
LDI R1, 0
loop:
ADD R1, R0
ADDI R0, -1
LDI R2, 0
CMP R0, R2
BRP loop
ST R1, R2, 10
HALT
"""


def _program():
    return assemble(SOURCE)


def test_trace_state_at_every_boundary_matches_direct_execution() -> None:
    program = _program()
    trace = trace_program(program)
    machine = Machine()

    assert trace_state_at(trace, 0) == MachineState.capture(machine)
    for position, event in enumerate(trace.events, start=1):
        machine.step(program)
        reconstructed = trace_state_at(trace, position)
        assert reconstructed == MachineState.capture(machine)
        assert reconstructed.machine_digest == event.after_digest

    final_state = trace_state_at(trace, len(trace.events))
    assert final_state.machine_digest == trace.final_state.machine_digest


def test_trace_cursor_seek_forward_backward_round_trip() -> None:
    trace = trace_program(_program())
    cursor = TraceCursor(trace)
    initial = cursor.state()

    first = cursor.step_forward()
    assert cursor.position == 1
    assert first.machine_digest == trace.events[0].after_digest

    cursor.seek(len(trace.events))
    final = cursor.state()
    assert cursor.at_end
    assert final.machine_digest == trace.final_state.machine_digest

    cursor.step_backward()
    assert cursor.position == len(trace.events) - 1
    cursor.seek(0)
    assert cursor.at_start
    assert cursor.state() == initial

    with pytest.raises(TraceInspectionError, match="initial boundary"):
        cursor.step_backward()


def test_trace_reconstruction_rejects_tampered_register_delta() -> None:
    trace = trace_program(_program())
    event = trace.events[0]
    assert event.register_deltas
    delta = event.register_deltas[0]
    tampered_delta = RegisterDelta(delta.index, delta.before, "000000000000")
    tampered_event = dataclasses.replace(event, register_deltas=(tampered_delta,))
    tampered_trace = ExecutionTrace(
        program_digest=trace.program_digest,
        initial_state=trace.initial_state,
        final_state=trace.final_state,
        events=(tampered_event,) + trace.events[1:],
    )

    with pytest.raises(TraceInspectionError, match="claimed after digest"):
        trace_state_at(tampered_trace, 1)


def test_trace_queries_filter_by_machine_effects_and_control_state() -> None:
    trace = trace_program(_program())

    r1_adds = find_trace_events(trace, TraceQuery(operations=("ADD",), registers=(1,)))
    assert len(r1_adds) == 2
    assert all(event.op == "ADD" for event in r1_adds)
    assert all(any(delta.index == 1 for delta in event.register_deltas) for event in r1_adds)

    memory_hits = find_trace_events(trace, TraceQuery(memory_addresses=(10,)))
    assert len(memory_hits) == 1
    assert memory_hits[0].op == "ST"

    condition_changes = find_trace_events(trace, TraceQuery(condition_change=True))
    assert condition_changes
    assert all(event.cond_before != event.cond_after for event in condition_changes)

    halt_hits = find_trace_events(trace, TraceQuery(halt_transition=True))
    assert len(halt_hits) == 1
    assert halt_hits[0].op == "HALT"


def test_trace_cli_state_and_find(tmp_path, monkeypatch, capsys) -> None:
    trace = trace_program(_program())
    trace_path = tmp_path / "run.trace.json"
    trace_path.write_text(trace.canonical_json() + "\n", encoding="utf-8")
    state_path = tmp_path / "step3.machine.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "td1-trace",
            "state",
            str(trace_path),
            "--position",
            "3",
            "--output",
            str(state_path),
        ],
    )
    assert main() == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["position"] == 3
    assert summary["event_count"] == len(trace.events)
    restored = MachineState.from_json(state_path.read_text(encoding="utf-8"))
    assert restored == trace_state_at(trace, 3)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "td1-trace",
            "find",
            str(trace_path),
            "--op",
            "ADD",
            "--register",
            "R1",
        ],
    )
    assert main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["schema"] == "td1.trace-query-result"
    assert result["match_count"] == 2
    assert all(event["instruction"]["op"] == "ADD" for event in result["events"])
