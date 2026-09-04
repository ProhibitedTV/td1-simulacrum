from td1_simulacrum import Instruction, Machine, Op, TernaryWord, int_to_trits, trits_to_int


def test_balanced_ternary_round_trip() -> None:
    for value in range(-500, 501):
        trits = int_to_trits(value, 12)
        assert trits_to_int(trits) == value


def test_balanced_ternary_negation_is_trit_inversion() -> None:
    word = TernaryWord.parse("+0--+0")
    assert str(-word) == "-0++-0"
    assert (-word).value == -word.value


def test_fixed_width_wrap() -> None:
    # Three trits represent -13..+13; +14 wraps to -13.
    assert TernaryWord.from_int(14, 3).value == -13


def test_reference_sum_program() -> None:
    # Compute 5 + 4 + 3 + 2 + 1 = 15, then store it at memory[10].
    program = [
        Instruction(Op.LDI, a=0, imm=5),
        Instruction(Op.LDI, a=1, imm=0),
        Instruction(Op.ADD, a=1, b=0),
        Instruction(Op.ADDI, a=0, imm=-1),
        Instruction(Op.LDI, a=2, imm=0),
        Instruction(Op.CMP, a=0, b=2),
        Instruction(Op.BRP, imm=-5),
        Instruction(Op.ST, a=1, b=2, imm=10),
        Instruction(Op.HALT),
    ]

    machine = Machine().run(program)

    assert machine.registers[1].value == 15
    assert machine.memory[10].value == 15
    assert machine.halted
    assert machine.steps == 24


def test_memory_address_wrap() -> None:
    machine = Machine()
    program = [
        Instruction(Op.LDI, a=0, imm=-1),
        Instruction(Op.LDI, a=1, imm=42),
        Instruction(Op.ST, a=1, b=0, imm=0),
        Instruction(Op.HALT),
    ]
    machine.run(program)
    assert machine.memory[728].value == 42
