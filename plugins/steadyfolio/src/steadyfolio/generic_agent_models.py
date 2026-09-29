"""Immutable contracts for consequential non-equity specialist reviews."""

from __future__ import annotations

from dataclasses import dataclass

from .agent_models import (
    AgentClaim,
    AgentEvidenceFact,
    AgentExecutionMetadata,
    AgentFinding,
)


GENERIC_AGENT_PACKET_VERSION = "1.0"
GENERIC_AGENT_RESULT_VERSION = "1.0"
GENERIC_CRITIC_ROLE = "critic"
GENERIC_SPECIALIST_ROLES = (
    "allocation_diversification",
    "risk_cost",
    "evidence_quality",
    "thesis_fit",
)
GENERIC_AGENT_ROLES = (*GENERIC_SPECIALIST_ROLES, GENERIC_CRITIC_ROLE)
GENERIC_ROUTE_ROLES = {
    "portfolio_review": (
        "allocation_diversification",
        "risk_cost",
        "evidence_quality",
    ),
    "overlap_review": (
        "allocation_diversification",
        "evidence_quality",
    ),
    "thesis_review": (
        "thesis_fit",
        "evidence_quality",
        "risk_cost",
    ),
}


@dataclass(frozen=True)
class GenericAgentSourceReference:
    source_id: str
    as_of: str
    retrieved_at: str
    freshness: str
    coverage: str
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class GenericAgentAggregate:
    aggregate_id: str
    kind: str
    value: str
    unit: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class GenericAgentInputPacket:
    schema_version: str
    packet_id: str
    route: str
    review_date: str
    role: str
    question: str
    deterministic_result_id: str
    instrument_aliases: tuple[str, ...]
    facts: tuple[AgentEvidenceFact, ...]
    sources: tuple[GenericAgentSourceReference, ...]
    assumptions: tuple[str, ...]
    aggregates: tuple[GenericAgentAggregate, ...]
    allowed_evidence_references: tuple[str, ...]
    instructions: tuple[str, ...]
    mutation_allowed: bool = False
    external_research_allowed: bool = False


@dataclass(frozen=True)
class GenericAgentResult:
    schema_version: str
    result_id: str
    packet_id: str
    role: str
    conclusion: str
    claims: tuple[AgentClaim, ...]
    evidence_references: tuple[str, ...]
    limitations: tuple[str, ...]
    confidence_basis: str
    unsupported_claim: bool
    findings: tuple[AgentFinding, ...]
    execution: AgentExecutionMetadata
