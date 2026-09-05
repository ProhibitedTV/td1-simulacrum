import json

import pytest

from td1_simulacrum import (
    ExecutionTrace,
    GeometryDelta,
    GeometryKind,
    GeometryPrimitive,
    GeometryScene,
    LatticePoint,
    Machine,
    PrimitiveChangeKind,
    RenderState,
    TernaryWord,
    TraceError,
    assemble,
    build_geometry_scene,
    diff_geometry,
    trace_program,
    verify_execution_trace,
)

SUM_PROGRAM = """
; Sum 5 + 4 + 3 + 2 + 1
    LDI R0, 5
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


def test_execution_trace_captures_reference_program_transitions() -> None:
    program = assemble(SUM_PROGRAM)
    trace = trace_program(program)
    final_machine = trace.final_state.restore_machine()

    assert len(trace.events) == 29
    assert trace.events[0].op == "LDI"
    assert trace.events[0].register_deltas[0].index == 0
    assert trace.events[-1].op == "HALT"
    assert trace.events[-1].halted_after
    assert final_machine.registers[1].value == 15
    assert final_machine.memory[10].value == 15


def test_execution_trace_is_deterministic_round_trippable_and_replayable() -> None:
    program = assemble(SUM_PROGRAM)
    first = trace_program(program)
    second = trace_program(program)
    restored = ExecutionTrace.from_json(first.canonical_json())

    assert first.digest() == second.digest()
    assert restored == first
    assert restored.canonical_json() == first.canonical_json()
    verify_execution_trace(program, restored)


def test_execution_trace_program_digest_prevents_wrong_program_replay() -> None:
    program = assemble(SUM_PROGRAM)
    trace = trace_program(program)
    payload = trace.as_dict()
    payload["program_digest"] = "0" * 64
    tampered = ExecutionTrace.from_dict(payload)

    with pytest.raises(TraceError, match="program digest"):
        verify_execution_trace(program, tampered)


def test_execution_trace_rejects_coercive_event_and_schema_values() -> None:
    trace = trace_program(assemble("LDI R0, 1\nHALT"))

    payload = json.loads(trace.canonical_json())
    payload["version"] = "1"
    with pytest.raises(ValueError, match="canonical JSON"):
        ExecutionTrace.from_dict(payload)

    payload = json.loads(trace.canonical_json())
    payload["events"][0]["instruction"]["imm"] = "1"
    with pytest.raises(ValueError, match="canonical JSON"):
        ExecutionTrace.from_dict(payload)

    payload = json.loads(trace.canonical_json())
    payload["events"][0]["halted_before"] = 0
    with pytest.raises(ValueError, match="canonical JSON"):
        ExecutionTrace.from_dict(payload)

    payload = json.loads(trace.canonical_json())
    payload["events"][0]["register_deltas"][0]["index"] = "0"
    with pytest.raises(ValueError, match="canonical JSON"):
        ExecutionTrace.from_dict(payload)


def test_execution_trace_does_not_mutate_supplied_initial_machine() -> None:
    machine = Machine()
    machine.registers[4] = TernaryWord.from_int(12)
    before_digest = machine.state_digest()

    trace = trace_program(assemble("ADDI R4, 1\nHALT"), initial_machine=machine)

    assert machine.state_digest() == before_digest
    assert trace.final_state.restore_machine().registers[4].value == 13


def test_geometry_delta_detects_real_machine_driven_changes() -> None:
    before_machine = Machine()
    after_machine = Machine()
    after_machine.registers[0] = TernaryWord.from_int(5)

    before = build_geometry_scene(RenderState.capture(before_machine))
    after = build_geometry_scene(RenderState.capture(after_machine))
    delta = diff_geometry(before, after)
    restored = GeometryDelta.from_json(delta.canonical_json())

    assert restored == delta
    assert delta.before_scene_digest == before.digest()
    assert delta.after_scene_digest == after.digest()
    assert delta.before_render_digest == before.source_render_digest
    assert delta.after_render_digest == after.source_render_digest
    assert delta.changes
    assert any(change.kind is PrimitiveChangeKind.METADATA for change in delta.changes)
    assert any(change.kind is PrimitiveChangeKind.APPEAR for change in delta.changes)


def test_geometry_delta_rejects_coercive_and_normalized_json() -> None:
    before_machine = Machine()
    after_machine = Machine()
    after_machine.registers[0] = TernaryWord.from_int(5)
    before = build_geometry_scene(RenderState.capture(before_machine))
    after = build_geometry_scene(RenderState.capture(after_machine))
    delta = diff_geometry(before, after)

    payload = json.loads(delta.canonical_json())
    payload["version"] = "1"
    with pytest.raises(ValueError, match="canonical JSON"):
        GeometryDelta.from_dict(payload)

    payload = json.loads(delta.canonical_json())
    payload["changes"][0]["primitive_id"] = 123
    with pytest.raises(ValueError, match="canonical JSON"):
        GeometryDelta.from_dict(payload)


def _single_primitive_scene(primitive: GeometryPrimitive, source: str) -> GeometryScene:
    return GeometryScene(
        source_render_digest=f"render-{source}",
        source_machine_digest=f"machine-{source}",
        primitives=(primitive,),
    )


def test_geometry_delta_classifies_uniform_translation_as_move() -> None:
    before = _single_primitive_scene(
        GeometryPrimitive(
            "p0",
            GeometryKind.NODE,
            "probe",
            (LatticePoint(1, 2, 3),),
        ),
        "before",
    )
    after = _single_primitive_scene(
        GeometryPrimitive(
            "p0",
            GeometryKind.NODE,
            "probe",
            (LatticePoint(5, 8, 10),),
        ),
        "after",
    )

    delta = diff_geometry(before, after)

    assert len(delta.changes) == 1
    assert delta.changes[0].kind is PrimitiveChangeKind.MOVE


def test_geometry_delta_classifies_shape_change_as_topology() -> None:
    before = _single_primitive_scene(
        GeometryPrimitive(
            "p0",
            GeometryKind.SEGMENT,
            "probe",
            (LatticePoint(0, 0), LatticePoint(2, 0)),
        ),
        "before",
    )
    after = _single_primitive_scene(
        GeometryPrimitive(
            "p0",
            GeometryKind.SEGMENT,
            "probe",
            (LatticePoint(0, 0), LatticePoint(0, 2)),
        ),
        "after",
    )

    assert diff_geometry(before, after).changes[0].kind is PrimitiveChangeKind.TOPOLOGY


def test_identical_geometry_scene_has_empty_delta() -> None:
    scene = build_geometry_scene(RenderState.capture(Machine()))
    delta = diff_geometry(scene, scene)

    assert delta.changes == ()
    assert json.loads(delta.canonical_json())["changes"] == []