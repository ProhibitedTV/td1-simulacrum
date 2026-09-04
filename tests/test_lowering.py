import json

import pytest

from td1_simulacrum import (
    Instruction,
    LoweredWeave,
    LoweringError,
    Machine,
    MemoryEffect,
    Modifier,
    Op,
    OperandBindingError,
    OperandBindings,
    SemanticAction,
    SemanticRoot,
    StateWeave,
    TernaryWord,
    UnsupportedWeaveError,
    lower_state_weave,
    supported_lowerings,
    supports_weave,
)


def test_supported_lowering_registry_is_explicit_and_stable() -> None:
    forms = supported_lowerings()
    assert tuple(form.canonical_weave for form in forms) == (
        "EXECUTION:-",
        "TRANSFORM:-",
        "STATE:0",
        "MEMORY:0",
        "MEMORY:+",
    )
    assert tuple(form.action for form in forms) == (
        SemanticAction.HALT,
        SemanticAction.NEGATE,
        SemanticAction.COMPARE,
        SemanticAction.MEMORY_READ,
        SemanticAction.MEMORY_WRITE,
    )


def test_halt_lowering_requires_no_operands() -> None:
    weave = StateWeave((SemanticRoot.EXECUTION,), Modifier.NEGATIVE)
    lowered = lower_state_weave(weave)
    assert lowered.instructions == (Instruction(Op.HALT),)
    assert lowered.register_reads == ()
    assert lowered.register_writes == ()
    assert lowered.memory_effect is MemoryEffect.NONE

    with pytest.raises(OperandBindingError):
        lower_state_weave(weave, OperandBindings(target_register=0))


def test_negate_lowering_and_machine_behavior() -> None:
    lowered = lower_state_weave(
        StateWeave.parse("TRANSFORM:-"),
        OperandBindings(target_register=2),
    )
    assert lowered.instructions == (Instruction(Op.NEG, a=2),)
    assert lowered.register_reads == (2,)
    assert lowered.register_writes == (2,)

    machine = Machine()
    machine.registers[2] = TernaryWord.from_int(17)
    machine.run((*lowered.instructions, Instruction(Op.HALT)))
    assert machine.registers[2].value == -17


def test_compare_lowering_sets_ternary_condition() -> None:
    lowered = lower_state_weave(
        StateWeave.parse("STATE:0"),
        OperandBindings(left_register=1, right_register=3),
    )
    machine = Machine()
    machine.registers[1] = TernaryWord.from_int(5)
    machine.registers[3] = TernaryWord.from_int(9)
    machine.run((*lowered.instructions, Instruction(Op.HALT)))
    assert machine.cond == -1
    assert lowered.register_reads == (1, 3)
    assert lowered.register_writes == ()


def test_memory_read_write_lowering_compose_without_hidden_state() -> None:
    store = lower_state_weave(
        StateWeave.parse("MEMORY:+"),
        OperandBindings(source_register=1, base_register=0, offset=8),
    )
    load = lower_state_weave(
        StateWeave.parse("MEMORY:0"),
        OperandBindings(target_register=2, base_register=0, offset=8),
    )
    assert store.memory_effect is MemoryEffect.WRITE
    assert load.memory_effect is MemoryEffect.READ
    assert store.instructions == (Instruction(Op.ST, a=1, b=0, imm=8),)
    assert load.instructions == (Instruction(Op.LD, a=2, b=0, imm=8),)

    machine = Machine()
    machine.registers[1] = TernaryWord.from_int(42)
    machine.run((*store.instructions, *load.instructions, Instruction(Op.HALT)))
    assert machine.memory[8].value == 42
    assert machine.registers[2].value == 42


def test_default_memory_offset_is_zero_but_is_not_fabricated_in_bindings() -> None:
    lowered = lower_state_weave(
        StateWeave.parse("MEMORY:0"),
        OperandBindings(target_register=2, base_register=0),
    )
    assert lowered.bindings.as_dict() == {"target_register": 2, "base_register": 0}
    assert lowered.instructions == (Instruction(Op.LD, a=2, b=0, imm=0),)


def test_unsupported_weave_is_distinct_from_bad_operands() -> None:
    unsupported = StateWeave.parse("TIME>REFERENCE:+")
    assert not supports_weave(unsupported)
    with pytest.raises(UnsupportedWeaveError):
        lower_state_weave(unsupported)

    supported = StateWeave.parse("TRANSFORM:-")
    assert supports_weave(supported)
    with pytest.raises(OperandBindingError):
        lower_state_weave(supported)


def test_operand_validation_rejects_out_of_range_and_extraneous_bindings() -> None:
    with pytest.raises(OperandBindingError):
        OperandBindings(target_register=9)

    with pytest.raises(OperandBindingError):
        lower_state_weave(
            StateWeave.parse("STATE:0"),
            OperandBindings(left_register=0, right_register=1, offset=2),
        )


def test_lowering_round_trip_and_digest_are_deterministic() -> None:
    lowered = lower_state_weave(
        StateWeave.parse("MEMORY:+"),
        OperandBindings(source_register=4, base_register=2, offset=-17),
    )
    restored = LoweredWeave.from_json(lowered.canonical_json())
    assert restored == lowered
    assert restored.digest() == lowered.digest()
    assert json.loads(lowered.canonical_json())["action"] == "memory_write"


def test_serialized_lowering_cannot_lie_about_compiler_output() -> None:
    lowered = lower_state_weave(
        StateWeave.parse("TRANSFORM:-"),
        OperandBindings(target_register=1),
    )
    payload = lowered.as_dict()
    payload["instructions"] = [{"op": "NOP", "a": 0, "b": 0, "imm": 0}]
    with pytest.raises(LoweringError):
        LoweredWeave.from_dict(payload)
