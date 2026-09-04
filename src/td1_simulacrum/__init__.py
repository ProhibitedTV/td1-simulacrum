"""TD-1 Simulacrum reference emulator."""

from .assembler import AssemblyError, assemble, disassemble
from .glyphs import (
    glyph_id_to_triad,
    glyph_ids_to_word,
    triad_to_glyph_id,
    word_to_glyph_ids,
)
from .machine import (
    Instruction,
    Machine,
    MachineError,
    MachineSnapshot,
    Op,
    ProgramCounterError,
    StepLimitExceeded,
)
from .observer import ObserverState, geodetic_to_ecef, julian_date_utc
from .render_state import (
    RENDER_SCHEMA,
    RENDER_SCHEMA_VERSION,
    MemoryCellRenderState,
    ObserverRenderState,
    RegisterRenderState,
    RenderMode,
    RenderPlane,
    RenderState,
    project_render_state,
)
from .semantic import Modifier, SemanticIR, SemanticRoot, StateWeave
from .ternary import (
    TernaryWord,
    int_to_trits,
    representable_range,
    trits_to_int,
    wrap_int,
)

__all__ = [
    "AssemblyError",
    "Instruction",
    "Machine",
    "MachineError",
    "MachineSnapshot",
    "MemoryCellRenderState",
    "Modifier",
    "ObserverRenderState",
    "ObserverState",
    "Op",
    "ProgramCounterError",
    "RENDER_SCHEMA",
    "RENDER_SCHEMA_VERSION",
    "RegisterRenderState",
    "RenderMode",
    "RenderPlane",
    "RenderState",
    "SemanticIR",
    "SemanticRoot",
    "StateWeave",
    "StepLimitExceeded",
    "TernaryWord",
    "assemble",
    "disassemble",
    "geodetic_to_ecef",
    "glyph_id_to_triad",
    "glyph_ids_to_word",
    "int_to_trits",
    "julian_date_utc",
    "project_render_state",
    "representable_range",
    "triad_to_glyph_id",
    "trits_to_int",
    "word_to_glyph_ids",
    "wrap_int",
]

__version__ = "0.3.0a0"
