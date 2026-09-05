"""CLI for deterministic TD-1 execution-trace inspection and time travel."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .machine import MEMORY_WORDS, REGISTER_COUNT, Op
from .trace import ExecutionTrace
from .trace_inspect import TraceQuery, find_trace_events, trace_state_at


def _parse_register(text: str) -> int:
    normalized = text.strip().upper()
    if normalized.startswith("R"):
        normalized = normalized[1:]
    try:
        value = int(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("register must look like R0..R8 or 0..8") from exc
    if not 0 <= value < REGISTER_COUNT:
        raise argparse.ArgumentTypeError(f"register must be within R0..R{REGISTER_COUNT - 1}")
    return value


def _parse_memory(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("memory address must be an integer") from exc
    if not 0 <= value < MEMORY_WORDS:
        raise argparse.ArgumentTypeError(f"memory address must be within 0..{MEMORY_WORDS - 1}")
    return value


def _load_trace(path: Path) -> ExecutionTrace:
    return ExecutionTrace.from_json(path.read_text(encoding="utf-8"))


def _state(path: Path, position: int, output: Path | None) -> int:
    trace = _load_trace(path)
    state = trace_state_at(trace, position)
    text = json.dumps(state.as_dict(), indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "output": str(output),
                "trace_digest": trace.digest(),
                "position": position,
                "event_count": len(trace.events),
                "checkpoint_digest": state.digest(),
                "machine_digest": state.machine_digest,
                "steps": state.steps,
                "halted": state.halted,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _find(
    path: Path,
    operations: list[str] | None,
    instruction_indices: list[int] | None,
    registers: list[int] | None,
    memory_addresses: list[int] | None,
    condition_change: bool,
    halt_transition: bool,
) -> int:
    trace = _load_trace(path)
    query = TraceQuery(
        operations=tuple(operations or ()),
        instruction_indices=tuple(instruction_indices or ()),
        registers=tuple(registers or ()),
        memory_addresses=tuple(memory_addresses or ()),
        condition_change=condition_change,
        halt_transition=halt_transition,
    )
    matches = find_trace_events(trace, query)
    payload = {
        "schema": "td1.trace-query-result",
        "version": 1,
        "trace_digest": trace.digest(),
        "query": query.as_dict(),
        "match_count": len(matches),
        "events": [event.as_dict() for event in matches],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="td1-trace",
        description="Deterministic time-travel inspection for td1.execution-trace artifacts",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    state_parser = subparsers.add_parser(
        "state",
        help="reconstruct an exact td1.machine-state at one trace boundary",
    )
    state_parser.add_argument("trace", type=Path)
    state_parser.add_argument(
        "--position",
        type=int,
        required=True,
        help="trace boundary: 0 is initial state; N is state after N events",
    )
    state_parser.add_argument("--output", type=Path)

    find_parser = subparsers.add_parser(
        "find",
        help="find trace events by logical opcode, instruction, or touched machine state",
    )
    find_parser.add_argument("trace", type=Path)
    find_parser.add_argument(
        "--op",
        action="append",
        choices=[op.name for op in Op],
        help="logical opcode to match; may be repeated",
    )
    find_parser.add_argument(
        "--ip",
        action="append",
        type=int,
        dest="instruction_indices",
        help="logical instruction index to match; may be repeated",
    )
    find_parser.add_argument(
        "--register",
        action="append",
        type=_parse_register,
        help="register touched by the event; may be repeated",
    )
    find_parser.add_argument(
        "--memory",
        action="append",
        type=_parse_memory,
        help="memory address touched by the event; may be repeated",
    )
    find_parser.add_argument(
        "--condition-change",
        action="store_true",
        help="require the event to change the ternary condition state",
    )
    find_parser.add_argument(
        "--halt-transition",
        action="store_true",
        help="require the event to transition the machine into HALT",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "state":
        return _state(args.trace, args.position, args.output)
    if args.command == "find":
        return _find(
            args.trace,
            args.op,
            args.instruction_indices,
            args.register,
            args.memory,
            args.condition_change,
            args.halt_transition,
        )
    raise RuntimeError(f"unknown command {args.command!r}")


if __name__ == "__main__":
    raise SystemExit(main())
