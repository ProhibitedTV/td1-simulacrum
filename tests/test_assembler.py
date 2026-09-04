import pytest

from td1_simulacrum import AssemblyError, Machine, assemble, disassemble

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


def test_assembler_labels_and_execution() -> None:
    program = assemble(SUM_PROGRAM)
    assert program[6].imm == -5

    machine = Machine().run(program)
    assert machine.registers[1].value == 15
    assert machine.memory[10].value == 15


def test_disassembly_round_trip() -> None:
    program = assemble("LDI R0, 4\nADDI R0, -1\nNEG R0\nHALT")
    assert assemble(disassemble(program)) == program


@pytest.mark.parametrize(
    "source",
    [
        "BOGUS R0",
        "LDI R9, 1",
        "ADD R0",
        "loop: NOP\nloop: HALT",
        "BRP nowhere",
    ],
)
def test_assembly_errors(source: str) -> None:
    with pytest.raises(AssemblyError):
        assemble(source)
