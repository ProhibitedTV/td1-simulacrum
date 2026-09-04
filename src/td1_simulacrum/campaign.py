"""Trace-derived subsystem parity campaigns for TD-1.

A parity campaign turns operations encountered during one deterministic logical
execution trace into transport-neutral subsystem vectors. It does not encode or
claim parity for physical instruction words, instruction fetch/decode, branches,
or unsupported memory/control operations.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .machine import REGISTER_COUNT, WORD_WIDTH
from .machine_state import MachineState
from .parity import (
    ConformanceReport,
    ParityError,
    ParityOperation,
    ParityTransport,
    ParityVector,
    run_conformance,
    vector_set_digest,
)
from .ternary import TernaryWord
from .trace import ExecutionEvent, ExecutionTrace

CAMPAIGN_SCHEMA = "td1.parity-campaign"
CAMPAIGN_SCHEMA_VERSION = 1
CAMPAIGN_RUN_SCHEMA = "td1.parity-campaign-run"
CAMPAIGN_RUN_SCHEMA_VERSION = 1


class ParityCampaignError(ValueError):
    """Raised when trace-derived campaign provenance or semantics are inconsistent."""


def _canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _word(value: int) -> str:
    return str(TernaryWord.from_int(value, WORD_WIDTH))


def _event_vector_id(event: ExecutionEvent, mapping: str) -> str:
    return f"TRACE-{event.event_index:06d}-{event.op}-{mapping}-R{event.a}"


def _apply_register_deltas(
    registers: Sequence[str],
    event: ExecutionEvent,
) -> tuple[str, ...]:
    current = list(registers)
    if len(current) != REGISTER_COUNT:
        raise ParityCampaignError("trace register reconstruction requires R0..R8")
    for delta in event.register_deltas:
        if not 0 <= delta.index < REGISTER_COUNT:
            raise ParityCampaignError("trace register delta index is out of range")
        if current[delta.index] != delta.before:
            raise ParityCampaignError(
                f"event {event.event_index} register delta before-value disagrees with trace chain"
            )
        current[delta.index] = delta.after
    return tuple(current)


@dataclass(frozen=True, slots=True)
class TraceParityEntry:
    """One subsystem vector tied to an exact logical execution event."""

    event_index: int
    machine_step: int
    instruction_index: int
    logical_op: str
    target_register: int
    before_machine_digest: str
    after_machine_digest: str
    mapping: str
    rationale: str
    vector: ParityVector

    def __post_init__(self) -> None:
        if self.event_index < 0 or self.machine_step <= 0 or self.instruction_index < 0:
            raise ParityCampaignError("campaign entry event identity is invalid")
        if not 0 <= self.target_register < REGISTER_COUNT:
            raise ParityCampaignError("campaign target register is out of range")
        if not self.logical_op.strip() or not self.mapping.strip() or not self.rationale.strip():
            raise ParityCampaignError("campaign entry strings must not be empty")
        for digest in (self.before_machine_digest, self.after_machine_digest):
            if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
                raise ParityCampaignError("campaign machine digests must be SHA-256 hex")

    def as_dict(self) -> dict[str, object]:
        return {
            "event_index": self.event_index,
            "machine_step": self.machine_step,
            "instruction_index": self.instruction_index,
            "logical_op": self.logical_op,
            "target_register": self.target_register,
            "before_machine_digest": self.before_machine_digest,
            "after_machine_digest": self.after_machine_digest,
            "mapping": self.mapping,
            "rationale": self.rationale,
            "vector": self.vector.as_dict(),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "TraceParityEntry":
        vector_payload = payload.get("vector")
        if not isinstance(vector_payload, Mapping):
            raise ParityCampaignError("campaign entry vector must be an object")
        return cls(
            event_index=int(payload["event_index"]),
            machine_step=int(payload["machine_step"]),
            instruction_index=int(payload["instruction_index"]),
            logical_op=str(payload["logical_op"]),
            target_register=int(payload["target_register"]),
            before_machine_digest=str(payload["before_machine_digest"]),
            after_machine_digest=str(payload["after_machine_digest"]),
            mapping=str(payload["mapping"]),
            rationale=str(payload["rationale"]),
            vector=ParityVector.from_dict(vector_payload),
        )


def _mapped_vector(
    event: ExecutionEvent,
    before: tuple[str, ...],
    after: tuple[str, ...],
) -> tuple[str, str, ParityVector] | None:
    op = event.op
    if not 0 <= event.a < REGISTER_COUNT:
        if op in {"LDI", "MOV", "ADD", "SUB", "NEG", "ADDI", "LD"}:
            raise ParityCampaignError(f"event {event.event_index} target register is invalid")
        return None

    if op == "LDI":
        mapping = "REGISTER-LOAD"
        rationale = "register write value encountered during logical LDI execution"
        vector = ParityVector.create(
            _event_vector_id(event, mapping),
            ParityOperation.REGISTER_LOAD,
            WORD_WIDTH,
            (after[event.a],),
        )
    elif op == "MOV":
        if not 0 <= event.b < REGISTER_COUNT:
            raise ParityCampaignError(f"event {event.event_index} source register is invalid")
        mapping = "REGISTER-LOAD"
        rationale = "register transfer value encountered during logical MOV execution"
        vector = ParityVector.create(
            _event_vector_id(event, mapping),
            ParityOperation.REGISTER_LOAD,
            WORD_WIDTH,
            (before[event.b],),
        )
    elif op == "LD":
        mapping = "REGISTER-LOAD"
        rationale = "register write value encountered during logical LD execution"
        vector = ParityVector.create(
            _event_vector_id(event, mapping),
            ParityOperation.REGISTER_LOAD,
            WORD_WIDTH,
            (after[event.a],),
        )
    elif op == "NEG":
        mapping = "ALU-NEGATE"
        rationale = "negation operands encountered during logical NEG execution"
        vector = ParityVector.create(
            _event_vector_id(event, mapping),
            ParityOperation.NEGATE,
            WORD_WIDTH,
            (before[event.a],),
        )
    elif op == "ADD":
        if not 0 <= event.b < REGISTER_COUNT:
            raise ParityCampaignError(f"event {event.event_index} source register is invalid")
        mapping = "ALU-ADD"
        rationale = "addition operands encountered during logical ADD execution"
        vector = ParityVector.create(
            _event_vector_id(event, mapping),
            ParityOperation.ADD,
            WORD_WIDTH,
            (before[event.a], before[event.b]),
        )
    elif op == "SUB":
        if not 0 <= event.b < REGISTER_COUNT:
            raise ParityCampaignError(f"event {event.event_index} source register is invalid")
        mapping = "ALU-SUB"
        rationale = "subtraction operands encountered during logical SUB execution"
        vector = ParityVector.create(
            _event_vector_id(event, mapping),
            ParityOperation.SUB,
            WORD_WIDTH,
            (before[event.a], before[event.b]),
        )
    elif op == "ADDI":
        mapping = "ALU-ADD-IMMEDIATE-AS-WORD"
        rationale = (
            "logical ADDI represented as subsystem ADD using a fixed-width immediate word; "
            "this does not test instruction decoding"
        )
        vector = ParityVector.create(
            _event_vector_id(event, mapping),
            ParityOperation.ADD,
            WORD_WIDTH,
            (before[event.a], _word(event.imm)),
        )
    else:
        return None

    if vector.expected_value != after[event.a]:
        raise ParityCampaignError(
            f"event {event.event_index} derived {vector.operation.value} result disagrees "
            "with traced register state"
        )
    return mapping, rationale, vector


def _derive_entries(trace: ExecutionTrace) -> tuple[TraceParityEntry, ...]:
    registers = tuple(register.ternary for register in trace.initial_state.registers)
    entries: list[TraceParityEntry] = []

    for event in trace.events:
        before = registers
        after = _apply_register_deltas(before, event)
        mapped = _mapped_vector(event, before, after)
        if mapped is not None:
            mapping, rationale, vector = mapped
            entries.append(
                TraceParityEntry(
                    event_index=event.event_index,
                    machine_step=event.machine_step,
                    instruction_index=event.instruction_index,
                    logical_op=event.op,
                    target_register=event.a,
                    before_machine_digest=event.before_digest,
                    after_machine_digest=event.after_digest,
                    mapping=mapping,
                    rationale=rationale,
                    vector=vector,
                )
            )
        registers = after

    final_registers = tuple(register.ternary for register in trace.final_state.registers)
    if registers != final_registers:
        raise ParityCampaignError("trace register delta chain does not reconstruct final registers")
    return tuple(entries)


@dataclass(frozen=True, slots=True)
class ParityCampaign:
    """Deterministic subsystem conformance vectors extracted from one execution trace."""

    trace: ExecutionTrace
    initial_checkpoint: MachineState
    final_checkpoint: MachineState
    entries: tuple[TraceParityEntry, ...]
    schema: str = CAMPAIGN_SCHEMA
    version: int = CAMPAIGN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != CAMPAIGN_SCHEMA or self.version != CAMPAIGN_SCHEMA_VERSION:
            raise ParityCampaignError("unsupported parity-campaign schema")

        expected_initial = MachineState.from_render_state(self.trace.initial_state)
        expected_final = MachineState.from_render_state(self.trace.final_state)
        if self.initial_checkpoint.canonical_json() != expected_initial.canonical_json():
            raise ParityCampaignError("campaign initial checkpoint disagrees with source trace")
        if self.final_checkpoint.canonical_json() != expected_final.canonical_json():
            raise ParityCampaignError("campaign final checkpoint disagrees with source trace")

        expected_entries = _derive_entries(self.trace)
        if self.entries != expected_entries:
            raise ParityCampaignError("campaign entries disagree with deterministic trace derivation")

    @property
    def vectors(self) -> tuple[ParityVector, ...]:
        return tuple(entry.vector for entry in self.entries)

    @property
    def vector_set_digest(self) -> str:
        return vector_set_digest(self.vectors)

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "trace_digest": self.trace.digest(),
            "trace": self.trace.as_dict(),
            "initial_checkpoint_digest": self.initial_checkpoint.digest(),
            "initial_checkpoint": self.initial_checkpoint.as_dict(),
            "final_checkpoint_digest": self.final_checkpoint.digest(),
            "final_checkpoint": self.final_checkpoint.as_dict(),
            "vector_set_digest": self.vector_set_digest,
            "entry_count": len(self.entries),
            "entries": [entry.as_dict() for entry in self.entries],
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256(self.canonical_json())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityCampaign":
        trace_payload = payload.get("trace")
        initial_payload = payload.get("initial_checkpoint")
        final_payload = payload.get("final_checkpoint")
        entries_payload = payload.get("entries")
        if not isinstance(trace_payload, Mapping):
            raise ParityCampaignError("campaign trace must be an object")
        if not isinstance(initial_payload, Mapping) or not isinstance(final_payload, Mapping):
            raise ParityCampaignError("campaign checkpoints must be objects")
        if not isinstance(entries_payload, list):
            raise ParityCampaignError("campaign entries must be a list")

        campaign = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            trace=ExecutionTrace.from_dict(trace_payload),
            initial_checkpoint=MachineState.from_dict(initial_payload),
            final_checkpoint=MachineState.from_dict(final_payload),
            entries=tuple(TraceParityEntry.from_dict(item) for item in entries_payload),
        )
        claims = {
            "trace_digest": campaign.trace.digest(),
            "initial_checkpoint_digest": campaign.initial_checkpoint.digest(),
            "final_checkpoint_digest": campaign.final_checkpoint.digest(),
            "vector_set_digest": campaign.vector_set_digest,
            "entry_count": len(campaign.entries),
        }
        for key, actual in claims.items():
            claimed = payload.get(key)
            if claimed is not None and claimed != actual:
                raise ParityCampaignError(f"campaign {key} mismatch")
        return campaign

    @classmethod
    def from_json(cls, text: str) -> "ParityCampaign":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ParityCampaignError("parity-campaign JSON root must be an object")
        return cls.from_dict(payload)


def build_parity_campaign(trace: ExecutionTrace) -> ParityCampaign:
    initial = MachineState.from_render_state(trace.initial_state)
    final = MachineState.from_render_state(trace.final_state)
    entries = _derive_entries(trace)
    return ParityCampaign(trace, initial, final, entries)


@dataclass(frozen=True, slots=True)
class ParityCampaignRun:
    """One complete campaign plus the resulting transport-neutral parity report."""

    campaign: ParityCampaign
    report: ConformanceReport
    schema: str = CAMPAIGN_RUN_SCHEMA
    version: int = CAMPAIGN_RUN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema != CAMPAIGN_RUN_SCHEMA or self.version != CAMPAIGN_RUN_SCHEMA_VERSION:
            raise ParityCampaignError("unsupported parity-campaign-run schema")
        if self.report.vector_set_digest != self.campaign.vector_set_digest:
            raise ParityCampaignError("campaign run report vector set disagrees with campaign")
        report_vectors = tuple(record.request.vector for record in self.report.records)
        if report_vectors != self.campaign.vectors:
            raise ParityCampaignError("campaign run report vectors disagree with campaign order")

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "version": self.version,
            "campaign_digest": self.campaign.digest(),
            "campaign": self.campaign.as_dict(),
            "report_digest": self.report.digest(),
            "report": self.report.as_dict(),
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.as_dict())

    def digest(self) -> str:
        return _sha256(self.canonical_json())

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ParityCampaignRun":
        campaign_payload = payload.get("campaign")
        report_payload = payload.get("report")
        if not isinstance(campaign_payload, Mapping) or not isinstance(report_payload, Mapping):
            raise ParityCampaignError("campaign run requires campaign/report objects")
        run = cls(
            schema=str(payload["schema"]),
            version=int(payload["version"]),
            campaign=ParityCampaign.from_dict(campaign_payload),
            report=ConformanceReport.from_dict(report_payload),
        )
        claimed_campaign = payload.get("campaign_digest")
        if claimed_campaign is not None and claimed_campaign != run.campaign.digest():
            raise ParityCampaignError("campaign run campaign_digest mismatch")
        claimed_report = payload.get("report_digest")
        if claimed_report is not None and claimed_report != run.report.digest():
            raise ParityCampaignError("campaign run report_digest mismatch")
        return run

    @classmethod
    def from_json(cls, text: str) -> "ParityCampaignRun":
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ParityCampaignError("parity-campaign-run JSON root must be an object")
        return cls.from_dict(payload)


def run_parity_campaign(
    transport: ParityTransport,
    campaign: ParityCampaign,
    *,
    session_id: str | None = None,
) -> ParityCampaignRun:
    if not campaign.entries:
        raise ParityCampaignError("cannot run a parity campaign with no derived vectors")
    try:
        report = run_conformance(transport, campaign.vectors, session_id=session_id)
    except ParityError as exc:
        raise ParityCampaignError(str(exc)) from exc
    return ParityCampaignRun(campaign, report)
