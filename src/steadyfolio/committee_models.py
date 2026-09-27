"""Structured records for the bounded conversational review workflow."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


COMMITTEE_VERSION = "1.0"


@dataclass(frozen=True)
class CommitteeRequest:
    id: str
    message: str
    as_of: str
    contribution_amount: Decimal | None = None
    contribution_currency: str | None = None
    contribution_method: str = "drift_aware"
    instrument_id: str | None = None
    thesis_id: str | None = None
    max_research_passes: int = 1
    max_critic_passes: int = 1
    max_revisions: int = 1
    max_external_calls: int = 0


@dataclass(frozen=True)
class SourceDisclosure:
    source_id: str
    provider: str
    reference: str
    value_time: str
    retrieved_at: str
    freshness: str
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class SpecialistInterpretation:
    role: str
    conclusion: str
    interpretation: str
    evidence_references: tuple[str, ...]
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkflowTrace:
    route: str
    deterministic_tools: tuple[str, ...]
    review_lenses: tuple[str, ...]
    provider_calls: int
    external_calls: int
    critic_passes: int
    revisions: int
    execution_mode: str


@dataclass(frozen=True)
class CommitteeResult:
    id: str
    committee_version: str
    request_id: str
    request_text: str
    route: str
    status: str
    as_of: str
    deterministic_facts: tuple[str, ...]
    sources: tuple[SourceDisclosure, ...]
    data_limitations: tuple[str, ...]
    assumptions: tuple[str, ...]
    specialist_interpretations: tuple[SpecialistInterpretation, ...]
    disagreements: tuple[str, ...]
    final_synthesis: str
    proposed_next_actions: tuple[str, ...]
    requires_user_approval: bool
    approval_reasons: tuple[str, ...]
    mutation_performed: bool
    trace: WorkflowTrace
