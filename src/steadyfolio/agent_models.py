"""Immutable contracts for bounded equity-review agent orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


AGENT_INPUT_PACKET_VERSION = "1.0"
SPECIALIST_RESULT_VERSION = "1.0"
MULTI_AGENT_REVIEW_VERSION = "1.0"

SPECIALIST_AGENT_ROLES = (
    "evidence",
    "business_quality",
    "valuation",
    "portfolio_risk",
)
CRITIC_AGENT_ROLE = "critic"
ALL_AGENT_ROLES = (*SPECIALIST_AGENT_ROLES, CRITIC_AGENT_ROLE)

CODEX_NATIVE_RUNTIME = "codex_native_subagents"
IN_MEMORY_TEST_RUNTIME = "in_memory_test_backend"
NO_AGENT_RUNTIME = "none"
SUPPORTED_AGENT_RUNTIMES = (
    CODEX_NATIVE_RUNTIME,
    IN_MEMORY_TEST_RUNTIME,
    NO_AGENT_RUNTIME,
)


@dataclass(frozen=True)
class AgentEvidenceFact:
    fact_id: str
    category: str
    statement: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class AgentSourceReference:
    source_id: str
    as_of: str
    retrieved_at: str
    freshness: str


@dataclass(frozen=True)
class AgentInputPacket:
    schema_version: str
    packet_id: str
    role: str
    instrument_id: str
    as_of: str
    deterministic_result_id: str
    facts: tuple[AgentEvidenceFact, ...]
    sources: tuple[AgentSourceReference, ...]
    allowed_evidence_references: tuple[str, ...]
    instructions: tuple[str, ...]
    mutation_allowed: bool = False
    external_research_allowed: bool = False


@dataclass(frozen=True)
class PortfolioRiskContext:
    """Role-minimal portfolio aggregates; never account or holding records."""

    direct_weight: Decimal | None = None
    max_direct_weight: Decimal | None = None
    thematic_exposure: Decimal | None = None
    overlap_weight: Decimal | None = None
    fragmented_positions: int | None = None
    max_fragmented_positions: int | None = None
    satellite_weight: Decimal | None = None
    max_satellite_weight: Decimal | None = None


@dataclass(frozen=True)
class AgentClaim:
    claim_id: str
    statement: str
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class AgentFinding:
    code: str
    severity: str
    description: str
    related_roles: tuple[str, ...]
    evidence_references: tuple[str, ...]


@dataclass(frozen=True)
class AgentExecutionMetadata:
    runtime_type: str
    execution_id: str
    status: str
    attempt: int
    isolated_context: bool


@dataclass(frozen=True)
class SpecialistResult:
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


@dataclass(frozen=True)
class AgentExecutionRecord:
    role: str
    status: str
    attempt: int
    isolated_context: bool
    execution_id: str | None = None
    result_id: str | None = None
    limitation: str | None = None


@dataclass(frozen=True)
class MultiAgentReviewResult:
    schema_version: str
    runtime_type: str
    status: str
    deterministic_result_id: str
    requested_agent_roles: tuple[str, ...]
    executed_agent_roles: tuple[str, ...]
    executions: tuple[AgentExecutionRecord, ...]
    specialist_results: tuple[SpecialistResult, ...]
    disagreements: tuple[str, ...]
    critic_findings: tuple[AgentFinding, ...]
    fallback_status: str
    final_synthesis: str
    mutation_performed: bool


@dataclass(frozen=True)
class ReviewModeEvaluation:
    schema_version: str
    single_lens_detected_defects: tuple[str, ...]
    multi_agent_detected_defects: tuple[str, ...]
    newly_detected_defects: tuple[str, ...]
    missed_defects: tuple[str, ...]
    comparison_basis: str
