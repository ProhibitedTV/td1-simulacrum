import json
import sys

import pytest

from td1_simulacrum.assembler import assemble
from td1_simulacrum.debug import (
    DebugError,
    DebugRun,
    DebugStopKind,
    DebugStopSpec,
    run_debug,
    verify_debug_run,
)
from td1_simulacrum.debug_cli import main
from td1_simulacrum.trace import TraceRecorder, trace_program, verify_execution_trace

PROGRAM = """
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
    return assemble(PROGRAM)


def test_trace_recorder_matches_full_trace_and_supports_partial_verification() -> None:
    program = _program()
    expected = trace_program(program)
    recorder = TraceRecorder(program)

    for _ in range(3):
        recorder.step()
    prefix = recorder.trace()
    assert not prefix.final_state.halted
    assert len(prefix.events) == 3
    verify_execution_trace(program, prefix)

    while not recorder.halted:
        recorder.step()
    assert recorder.trace().canonical_json() == expected.canonical_json()


def test_breakpoint_stops_before_instruction_execution() -> None:
    run = run_debug(_program(), stop_spec=DebugStopSpec(instruction_indices=(2,)))

    assert run.stop_kind is DebugStopKind.BREAKPOINT
    assert run.matches == ("ip:2",)
    assert run.position == 2
    assert run.trace.final_state.ip == 2
    assert run.trace.events[-1].instruction_index == 1
    assert run.trace.final_state.restore_machine().registers[1].value == 0
    verify_debug_run(_program(), run)


def test_opcode_breakpoint_can_stop_at_initial_boundary() -> None:
    run = run_debug(_program(), stop_spec=DebugStopSpec(operations=("LDI",)))

    assert run.stop_kind is DebugStopKind.BREAKPOINT
    assert run.position == 0
    assert run.matches == ("op:LDI",)
    assert run.trace.final_state.machine_digest == run.trace.initial_state.machine_digest


def test_watchpoint_stops_after_real_register_change() -> None:
    run = run_debug(_program(), stop_spec=DebugStopSpec(registers=(1,)))

    assert run.stop_kind is DebugStopKind.WATCHPOINT
    assert run.matches == ("register:R1",)
    assert run.position == 3
    assert run.trace.events[-1].op == "ADD"
    assert run.trace.final_state.restore_machine().registers[1].value == 2
    verify_debug_run(_program(), run)


def test_memory_watchpoint_stops_after_store() -> None:
    run = run_debug(_program(), stop_spec=DebugStopSpec(memory_addresses=(10,)))

    assert run.stop_kind is DebugStopKind.WATCHPOINT
    assert run.matches == ("memory:10",)
    assert run.trace.events[-1].op == "ST"
    assert run.trace.final_state.restore_machine().memory[10].value == 3


def test_event_budget_stops_nonterminating_execution_without_step_limit_exception() -> None:
    program = assemble(
        """
LDI R0, 1
LDI R1, 0
loop:
CMP R0, R1
BRP loop
"""
    )
    run = run_debug(program, max_events=7)

    assert run.stop_kind is DebugStopKind.EVENT_BUDGET
    assert run.position == 7
    assert not run.trace.final_state.halted
    verify_debug_run(program, run)


def test_skip_initial_breakpoint_allows_checkpoint_style_continuation() -> None:
    program = _program()
    stopped = run_debug(program, stop_spec=DebugStopSpec(instruction_indices=(2,)))
    resumed = run_debug(
        program,
        stop_spec=stopped.stop_spec,
        initial_machine=stopped.trace.final_state.restore_machine(),
        max_events=2,
        skip_initial_breakpoint=True,
    )

    assert resumed.position >= 1
    assert resumed.trace.events[0].instruction_index == 2


def test_debug_run_round_trip_and_tamper_rejection() -> None:
    run = run_debug(_program(), stop_spec=DebugStopSpec(registers=(1,)))
    restored = DebugRun.from_json(run.canonical_json())
    assert restored == run
    assert restored.digest() == run.digest()

    payload = json.loads(run.canonical_json())
    payload["stop"]["position"] += 1
    with pytest.raises(DebugError, match="position"):
        DebugRun.from_dict(payload)

    payload = json.loads(run.canonical_json())
    payload["stop"]["machine_digest"] = "0" * 64
    with pytest.raises(DebugError, match="machine digest"):
        DebugRun.from_dict(payload)


def test_debug_artifacts_reject_coercion_and_normalized_stop_specs() -> None:
    run = run_debug(_program(), stop_spec=DebugStopSpec(registers=(1,)))

    payload = json.loads(run.canonical_json())
    payload["event_budget"] = str(payload["event_budget"])
    with pytest.raises(ValueError, match="canonical JSON"):
        DebugRun.from_dict(payload)

    payload = json.loads(run.canonical_json())
    payload["skip_initial_breakpoint"] = 0
    with pytest.raises(ValueError, match="canonical JSON"):
        DebugRun.from_dict(payload)

    payload = json.loads(run.canonical_json())
    payload["stop_spec"]["registers"] = ["1"]
    with pytest.raises(ValueError, match="canonical JSON"):
        DebugRun.from_dict(payload)

    payload = json.loads(run.canonical_json())
    payload["stop_spec"]["operations"] = ["ldi", "LDI"]
    with pytest.raises(ValueError, match="canonical JSON"):
        DebugRun.from_dict(payload)


def test_debug_artifact_rejects_omitted_canonical_stop_metadata() -> None:
    run = run_debug(_program(), stop_spec=DebugStopSpec(registers=(1,)))
    payload = json.loads(run.canonical_json())
    del payload["skip_initial_breakpoint"]

    with pytest.raises(ValueError, match="canonical JSON"):
        DebugRun.from_dict(payload)


def test_debug_cli_writes_and_verifies_artifact(tmp_path, monkeypatch, capsys) -> None:
    program_path = tmp_path / "program.td1"
    program_path.write_text(PROGRAM, encoding="utf-8")
    output = tmp_path / "debug.json"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "td1-debug",
            "run",
            str(program_path),
            "--break-ip",
            "2",
            "--output",
            str(output),
        ],
    )
    assert main() == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["stop_kind"] == "breakpoint"
    assert summary["position"] == 2
    assert output.exists()

    monkeypatch.setattr(
        sys,
        "argv",
        ["td1-debug", "verify", str(program_path), str(output)],
    )
    assert main() == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["verified"] is True
    assert verified["stop_kind"] == "breakpoint"