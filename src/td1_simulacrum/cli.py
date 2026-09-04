"""Command-line interface for the TD-1 Simulacrum."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assembler import assemble
from .glyphs import word_to_glyph_ids
from .machine import Machine
from .ternary import TernaryWord


def _run_program(path: Path, max_steps: int) -> int:
    program = assemble(path.read_text(encoding="utf-8"))
    machine = Machine().run(program, max_steps=max_steps)
    print(json.dumps(machine.snapshot().as_dict(), indent=2))
    print(f"state_digest={machine.state_digest()}")
    return 0


def _show_glyphs(text: str) -> int:
    word = TernaryWord.parse(text)
    print(" ".join(f"G{glyph_id:02d}" for glyph_id in word_to_glyph_ids(word)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="td1-sim",
        description="TD-1 Simulacrum reference emulator",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="assemble and execute a TD-1 source file")
    run_parser.add_argument("path", type=Path)
    run_parser.add_argument("--max-steps", type=int, default=100_000)

    glyph_parser = subparsers.add_parser("glyph", help="map a ternary word to microglyph IDs")
    glyph_parser.add_argument("word")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "run":
        return _run_program(args.path, args.max_steps)
    if args.command == "glyph":
        return _show_glyphs(args.word)
    raise RuntimeError(f"unknown command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
