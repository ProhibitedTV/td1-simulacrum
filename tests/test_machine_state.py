import json

import pytest

from td1_simulacrum import Machine, RenderState, TernaryWord, assemble
from td1_simulacrum.machine_state import (
    MachineMemoryCell,
    MachineState,
    MachineStateError,
)


PROGRAM = assemble(
    """
LDI R0, 4
LDI R1, 1
ADD R1, R0
ADDI R0, -1
ST R1, R0, 12
NEG R1
HALT
"""
)


def _intermediate_machine(steps: int = 5) -> Machine:
    machine = Machine()
    for _ in range(steps):
        machine.step(PROGRAM)
    return machine


def test_machine_state_round_trip_is_deterministic_and_restores_sparse_memory() -> None:
    machine = _intermediate_machine()
    state = MachineState.capture(machine)
    second = MachineState.capture(machine)

    assert state.canonical_json() == second.canonical_json()
    assert state.digest() == second.digest()
    assert state.machine_digest == machine.state_digest(include_memory=True)
    assert len(state.nonzero_memory) == 1
    assert state.nonzero_memory[0].address == 15

    restored = MachineState.from_json(state.canonical_json())
    machine2 = restored.restore_machine()
    assert restored == state
    assert machine2.state_digest(include_memory=True) == machine.state_digest(include_memory=True)
    assert [str(word) for word in machine2.memory] == [str(word) for word in machine.memory]


def test_intermediate_checkpoint_resumes_to_same_final_machine_as_uninterrupted_run() -> None:
    uninterrupted = Machine().run(PROGRAM)
    intermediate = _intermediate_machine(3)
    checkpoint = MachineState.capture(intermediate)

    resumed = checkpoint.restore_machine()
    resumed.run(PROGRAM, max_steps=checkpoint.steps + 100)

    assert resumed.snapshot() == uninterrupted.snapshot()
    assert resumed.state_digest(include_memory=True) == uninterrupted.state_digest(include_memory=True)


def test_render_state_bridge_copies_only_exact_machine_truth() -> None:
    machine = _intermediate_machine(4)
    render = RenderState.capture(machine)
    checkpoint = MachineState.from_render_state(render)

    assert checkpoint.machine_digest == render.machine_digest
    assert checkpoint.restore_machine().state_digest(include_memory=True) == render.machine_digest
    assert "glyph" not in checkpoint.canonical_json()
    assert "planes" not in checkpoint.canonical_json()
    assert "observer" not in checkpoint.canonical_json()


def test_machine_state_rejects_claimed_digest_and_register_tampering() -> None:
    state = MachineState.capture(_intermediate_machine())

    digest_payload = json.loads(state.canonical_json())
    digest_payload["machine_digest"] = "0" * 64
    with pytest.raises(MachineStateError, match="claimed machine digest"):
        MachineState.from_dict(digest_payload)

    register_payload = json.loads(state.canonical_json())
    register_payload["registers"][0] = "+" * 12
    with pytest.raises(MachineStateError, match="claimed machine digest"):
        MachineState.from_dict(register_payload)


def test_machine_state_rejects_wrong_architecture_and_word_width() -> None:
    state = MachineState.capture(_intermediate_machine())

    architecture_payload = json.loads(state.canonical_json())
    architecture_payload["memory_words"] = 728
    with pytest.raises(MachineStateError, match="memory_words"):
        MachineState.from_dict(architecture_payload)

    word_payload = json.loads(state.canonical_json())
    word_payload["registers"][0] = "0" * 11
    with pytest.raises(MachineStateError, match="exactly 12 trits"):
        MachineState.from_dict(word_payload)


def test_sparse_memory_rejects_zero_duplicate_and_out_of_range_cells() -> None:
    with pytest.raises(MachineStateError, match="may not contain zero"):
        MachineMemoryCell(0, "0" * 12)
    with pytest.raises(MachineStateError, match="outside"):
        MachineMemoryCell(729, "+" + "0" * 11)

    machine = Machine()
    machine.memory[2] = TernaryWord.from_int(1)
    state = MachineState.capture(machine)
    payload = json.loads(state.canonical_json())
    payload["nonzero_memory"].append(dict(payload["nonzero_memory"][0]))
    with pytest.raises(MachineStateError, match="unique"):
        MachineState.from_dict(payload)


def test_machine_state_rejects_bad_condition_steps_and_render_bridge_object() -> None:
    state = MachineState.capture(Machine())

    condition_payload = json.loads(state.canonical_json())
    condition_payload["cond"] = 2
    with pytest.raises(MachineStateError, match="condition"):
        MachineState.from_dict(condition_payload)

    steps_payload = json.loads(state.canonical_json())
    steps_payload["steps"] = -1
    with pytest.raises(MachineStateError, match="step count"):
        MachineState.from_dict(steps_payload)

    with pytest.raises(MachineStateError, match="restore boundary"):
        MachineState.from_render_state(object())


def test_machine_state_rejects_schema_type_coercion() -> None:
    state = MachineState.capture(_intermediate_machine())

    halted_payload = json.loads(state.canonical_json())
    halted_payload["halted"] = "false"
    with pytest.raises(MachineStateError, match="halted must be a boolean"):
        MachineState.from_dict(halted_payload)

    integer_payload = json.loads(state.canonical_json())
    integer_payload["steps"] = "5"
    with pytest.raises(MachineStateError, match="steps must be an integer"):
        MachineState.from_dict(integer_payload)

    register_payload = json.loads(state.canonical_json())
    register_payload["registers"][0] = 0
    with pytest.raises(MachineStateError, match="registers must contain"):
        MachineState.from_dict(register_payload)

    memory_payload = json.loads(state.canonical_json())
    memory_payload["nonzero_memory"] = ["not-an-object"]
    with pytest.raises(MachineStateError, match="entries must be objects"):
        MachineState.from_dict(memory_payload)
