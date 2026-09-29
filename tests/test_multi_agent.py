"""Bounded, network-free tests for Phase 8 equity-review orchestration."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import json
from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.agent_models import (  # noqa: E402
    AGENT_INPUT_PACKET_VERSION,
    IN_MEMORY_TEST_RUNTIME,
    SPECIALIST_RESULT_VERSION,
    AgentExecutionRecord,
    PortfolioRiskContext,
)
from steadyfolio.committee import run_committee_workflow  # noqa: E402
from steadyfolio.committee_models import CommitteeRequest  # noqa: E402
from steadyfolio.committee_reporting import render_committee_report  # noqa: E402
from steadyfolio.equity_validation import equity_review_input_from_dict  # noqa: E402
from steadyfolio.multi_agent import (  # noqa: E402
    AgentBackendResponse,
    AgentTimeoutError,
    AgentUnavailableError,
    build_critic_packet,
    detect_single_lens_equity_defects,
    evaluate_review_modes,
    finalize_multi_agent_equity_review,
    prepare_multi_agent_equity_review,
    run_deterministic_equity_fallback,
    run_multi_agent_equity_review,
    specialist_result_from_dict,
    validate_specialist_result,
)
from steadyfolio.errors import ValidationError  # noqa: E402
from steadyfolio.models import to_json_value  # noqa: E402
from steadyfolio.validation import state_from_dict  # noqa: E402


EXAMPLES = REPOSITORY_ROOT / "examples"
AS_OF = "2026-01-31"
INSTRUMENT_ID = "synthetic-compute-company"


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _inputs():
    return (
        state_from_dict(_read(EXAMPLES / "equity-portfolio.example.json")),
        equity_review_input_from_dict(
            _read(EXAMPLES / "equity-evidence.example.json")
        ),
        CommitteeRequest(
            "phase8-synthetic",
            "Analyze this stock with a bounded multi-agent equity review.",
            AS_OF,
            instrument_id=INSTRUMENT_ID,
        ),
    )


def _portfolio_context() -> PortfolioRiskContext:
    return PortfolioRiskContext(
        direct_weight=Decimal("0.08"),
        max_direct_weight=Decimal("0.15"),
        thematic_exposure=Decimal("0.30"),
        overlap_weight=Decimal("0.04"),
        fragmented_positions=2,
        max_fragmented_positions=6,
        satellite_weight=Decimal("0.24"),
        max_satellite_weight=Decimal("0.30"),
    )


def _result_payload(
    packet,
    *,
    conclusion: str = "supports",
    unsupported_claim: bool = False,
    findings: list[dict[str, object]] | None = None,
    bad_reference: bool = False,
) -> dict[str, object]:
    reference = (
        "missing-source-id"
        if bad_reference
        else packet.allowed_evidence_references[0]
    )
    claims = []
    if packet.role != "critic":
        claims = [
            {
                "claim_id": f"claim.{packet.role}",
                "statement": f"Synthetic bounded conclusion from {packet.role}.",
                "evidence_references": [reference],
            }
        ]
    return {
        "schema_version": SPECIALIST_RESULT_VERSION,
        "packet_id": packet.packet_id,
        "role": packet.role,
        "conclusion": conclusion,
        "claims": claims,
        "evidence_references": [reference],
        "limitations": ["Synthetic in-memory result."],
        "confidence_basis": "Only cited packet evidence was considered.",
        "unsupported_claim": unsupported_claim,
        "findings": findings or [],
    }


def _parse_result(packet, payload, *, host_id: str | None = None):
    return specialist_result_from_dict(
        payload,
        packet=packet,
        runtime_type=IN_MEMORY_TEST_RUNTIME,
        host_execution_id=host_id or f"direct-host-execution:{packet.role}",
        isolated_context=True,
    )


class FakeAgentBackend:
    """Return synthetic structured outputs without models, network, or paid calls."""

    runtime_type = IN_MEMORY_TEST_RUNTIME

    def __init__(self, behaviors: dict[str, object] | None = None) -> None:
        self.behaviors = behaviors or {}
        self.calls: dict[str, int] = {}

    def execute(self, packet):
        self.calls[packet.role] = self.calls.get(packet.role, 0) + 1
        has_behavior = packet.role in self.behaviors
        behavior = self.behaviors.get(packet.role)
        if isinstance(behavior, BaseException):
            raise behavior
        if callable(behavior):
            output = behavior(packet)
        elif has_behavior:
            output = behavior
        else:
            output = _result_payload(packet)
        if isinstance(output, AgentBackendResponse):
            return output
        return AgentBackendResponse(
            output=output,
            host_execution_id=f"fake-host-execution:{packet.role}",
            isolated_context=True,
        )


class MultiAgentEquityReviewTests(unittest.TestCase):
    def test_versioned_schema_roots_match_structured_contracts(self) -> None:
        state, equity_input, request = _inputs()
        prepared = prepare_multi_agent_equity_review(request, state, equity_input)
        packet = prepared.specialist_packets[0]
        payload = _result_payload(packet)
        result = run_multi_agent_equity_review(
            request, state, equity_input, FakeAgentBackend()
        )

        packet_schema = _read(
            REPOSITORY_ROOT / "schemas" / "agent-input-packet.schema.json"
        )
        specialist_schema = _read(
            REPOSITORY_ROOT / "schemas" / "specialist-result.schema.json"
        )
        review_schema = _read(
            REPOSITORY_ROOT / "schemas" / "multi-agent-equity-review.schema.json"
        )
        committee_schema = _read(
            REPOSITORY_ROOT / "schemas" / "committee-result.schema.json"
        )

        self.assertEqual(set(packet_schema["required"]), set(to_json_value(packet)))
        self.assertEqual(
            packet_schema["properties"]["schema_version"]["const"],
            AGENT_INPUT_PACKET_VERSION,
        )
        self.assertEqual(
            specialist_schema["$defs"]["agentOutput"]["properties"]
            ["schema_version"]["const"],
            SPECIALIST_RESULT_VERSION,
        )
        self.assertEqual(
            set(specialist_schema["$defs"]["agentOutput"]["required"]),
            set(payload),
        )
        self.assertEqual(
            set(review_schema["required"]), set(to_json_value(result.agent_review))
        )
        self.assertEqual(
            committee_schema["properties"]["committee_version"]["enum"],
            ["1.1", "2.0"],
        )
        self.assertIn("agent_review", to_json_value(result))

    def test_success_runs_each_specialist_and_critic_once(self) -> None:
        state, equity_input, request = _inputs()
        backend = FakeAgentBackend()

        result = run_multi_agent_equity_review(
            request,
            state,
            equity_input,
            backend,
            portfolio_context=_portfolio_context(),
        )

        self.assertEqual(
            backend.calls,
            {
                "evidence": 1,
                "business_quality": 1,
                "valuation": 1,
                "portfolio_risk": 1,
                "critic": 1,
            },
        )
        self.assertEqual(result.committee_version, "2.0")
        self.assertIsNotNone(result.agent_review)
        self.assertEqual(result.agent_review.fallback_status, "not_used")
        self.assertEqual(result.agent_review.runtime_type, IN_MEMORY_TEST_RUNTIME)
        self.assertEqual(result.trace.deterministic_tools, ("review_equity",))
        self.assertEqual(result.trace.review_lenses, ())
        self.assertEqual(result.trace.critic_passes, 1)
        self.assertFalse(result.mutation_performed)
        prepared = prepare_multi_agent_equity_review(request, state, equity_input)
        self.assertTrue(
            all(
                any("untrusted evidence" in instruction for instruction in packet.instructions)
                for packet in prepared.specialist_packets
            )
        )

    def test_distinct_identity_quality_and_valuation_sources_are_role_minimal(self) -> None:
        state, equity_input, request = _inputs()
        valuation_source = replace(
            equity_input.sources[0],
            id="synthetic-valuation-source",
            provider="Synthetic Valuation Provider",
            reference="synthetic://valuation-source",
            terms_reference="synthetic://valuation-terms",
        )
        valuation_anchor = replace(
            equity_input.valuation_anchors[0],
            source_ids=(valuation_source.id,),
        )
        split_input = replace(
            equity_input,
            sources=(*equity_input.sources, valuation_source),
            valuation_anchors=(valuation_anchor,),
        )

        prepared = prepare_multi_agent_equity_review(request, state, split_input)
        packets = {item.role: item for item in prepared.specialist_packets}

        self.assertEqual(
            {item.source_id for item in packets["business_quality"].sources},
            {"source-ref:001"},
        )
        self.assertEqual(
            {item.source_id for item in packets["valuation"].sources},
            {"source-ref:001"},
        )
        self.assertEqual(
            {item.source_id for item in packets["evidence"].sources},
            {"source-ref:001", "source-ref:002"},
        )
        self.assertFalse(
            hasattr(packets["evidence"].sources[0], "reference")
        )

    def test_source_ids_are_pseudonymized_before_packet_transfer(self) -> None:
        state, _, request = _inputs()
        raw = json.loads(
            json.dumps(_read(EXAMPLES / "equity-evidence.example.json")).replace(
                "synthetic-equity-source", "broker-account-12345"
            )
        )
        private_input = equity_review_input_from_dict(raw)

        prepared = prepare_multi_agent_equity_review(request, state, private_input)
        serialized = json.dumps(
            [to_json_value(packet) for packet in prepared.specialist_packets],
            sort_keys=True,
        )

        self.assertNotIn("broker-account-12345", serialized)
        self.assertIn("source-ref:001", serialized)
        for packet in prepared.specialist_packets:
            source_aliases = {item.source_id for item in packet.sources}
            for fact in packet.facts:
                self.assertFalse(
                    "broker-account-12345" in fact.evidence_references
                )
            self.assertTrue(
                source_aliases <= set(packet.allowed_evidence_references)
            )

    def test_packet_id_is_bound_to_canonical_packet_contents(self) -> None:
        state, equity_input, request = _inputs()
        low_weight = replace(_portfolio_context(), direct_weight=Decimal("0.05"))
        high_weight = replace(_portfolio_context(), direct_weight=Decimal("0.95"))

        first = prepare_multi_agent_equity_review(
            request, state, equity_input, portfolio_context=low_weight
        )
        repeated = prepare_multi_agent_equity_review(
            request, state, equity_input, portfolio_context=low_weight
        )
        changed = prepare_multi_agent_equity_review(
            request, state, equity_input, portfolio_context=high_weight
        )
        first_packets = {item.role: item for item in first.specialist_packets}
        repeated_packets = {item.role: item for item in repeated.specialist_packets}
        changed_packets = {item.role: item for item in changed.specialist_packets}

        self.assertEqual(
            first_packets["portfolio_risk"].packet_id,
            repeated_packets["portfolio_risk"].packet_id,
        )
        self.assertNotEqual(
            first_packets["portfolio_risk"].packet_id,
            changed_packets["portfolio_risk"].packet_id,
        )
        self.assertEqual(
            first_packets["evidence"].packet_id,
            changed_packets["evidence"].packet_id,
        )

    def test_agreement_cannot_override_insufficient_deterministic_evidence(self) -> None:
        state, equity_input, request = _inputs()
        incomplete_quality = replace(
            equity_input.quality,
            institutional_ownership=None,
            benchmark_outperformance=None,
            moat_and_management=None,
        )
        result = run_multi_agent_equity_review(
            request,
            state,
            replace(equity_input, quality=incomplete_quality),
            FakeAgentBackend(),
            portfolio_context=_portfolio_context(),
        )

        self.assertEqual(result.status, "insufficient_evidence")
        self.assertIn("cannot repair", result.final_synthesis)
        self.assertTrue(result.disagreements)

    def test_all_agents_can_agree_evidence_is_insufficient(self) -> None:
        state, equity_input, request = _inputs()
        incomplete_quality = replace(
            equity_input.quality,
            institutional_ownership=None,
            benchmark_outperformance=None,
            moat_and_management=None,
        )

        def insufficient(packet):
            findings = []
            if packet.role == "critic":
                findings = [
                    {
                        "code": "insufficient-evidence-preserved",
                        "severity": "warning",
                        "description": "Every specialist preserved the evidence gap.",
                        "related_roles": [
                            "evidence",
                            "business_quality",
                            "valuation",
                            "portfolio_risk",
                        ],
                        "evidence_references": [
                            packet.allowed_evidence_references[0]
                        ],
                    }
                ]
            return _result_payload(
                packet,
                conclusion="insufficient_evidence",
                findings=findings,
            )

        backend = FakeAgentBackend(
            {role: insufficient for role in (
                "evidence",
                "business_quality",
                "valuation",
                "portfolio_risk",
                "critic",
            )}
        )
        result = run_multi_agent_equity_review(
            request, state, replace(equity_input, quality=incomplete_quality), backend
        )

        self.assertEqual(result.status, "insufficient_evidence")
        self.assertTrue(
            all(
                item.conclusion == "insufficient_evidence"
                for item in result.agent_review.specialist_results
            )
        )
        self.assertEqual(result.agent_review.fallback_status, "not_used")

    def test_quality_and_valuation_disagreement_is_preserved(self) -> None:
        state, equity_input, request = _inputs()
        backend = FakeAgentBackend(
            {
                "valuation": lambda packet: _result_payload(
                    packet, conclusion="limits"
                )
            }
        )
        result = run_multi_agent_equity_review(
            request,
            state,
            equity_input,
            backend,
            portfolio_context=_portfolio_context(),
        )

        self.assertEqual(result.status, "limited")
        self.assertTrue(
            any("Business quality and valuation" in item for item in result.disagreements)
        )

    def test_unknown_source_reference_is_rejected(self) -> None:
        state, equity_input, request = _inputs()
        backend = FakeAgentBackend(
            {
                "evidence": lambda packet: _result_payload(
                    packet, bad_reference=True
                )
            }
        )
        result = run_multi_agent_equity_review(
            request, state, equity_input, backend
        )

        evidence_record = next(
            item for item in result.agent_review.executions if item.role == "evidence"
        )
        self.assertEqual(evidence_record.status, "rejected")
        self.assertEqual(result.agent_review.fallback_status, "partial_agent_failure")

    def test_supporting_specialist_requires_at_least_one_claim(self) -> None:
        state, equity_input, request = _inputs()
        packet = prepare_multi_agent_equity_review(
            request, state, equity_input
        ).specialist_packets[0]
        payload = _result_payload(packet)
        payload["claims"] = []

        parsed = _parse_result(packet, payload)
        with self.assertRaisesRegex(ValidationError, "requires a claim"):
            validate_specialist_result(
                packet, parsed, runtime_type=IN_MEMORY_TEST_RUNTIME
            )

        def empty_support(candidate):
            candidate_payload = _result_payload(candidate)
            if candidate.role != "critic":
                candidate_payload["claims"] = []
            return candidate_payload

        result = run_multi_agent_equity_review(
            request,
            state,
            equity_input,
            FakeAgentBackend(
                {
                    role: empty_support
                    for role in (
                        "evidence",
                        "business_quality",
                        "valuation",
                        "portfolio_risk",
                        "critic",
                    )
                }
            ),
        )
        self.assertNotEqual(result.agent_review.status, "complete")
        self.assertEqual(
            result.agent_review.fallback_status, "partial_agent_failure"
        )
        self.assertTrue(
            all(
                record.status == "rejected"
                for record in result.agent_review.executions
                if record.role != "critic"
            )
        )

    def test_malformed_output_fails_closed(self) -> None:
        state, equity_input, request = _inputs()
        result = run_multi_agent_equity_review(
            request,
            state,
            equity_input,
            FakeAgentBackend({"valuation": {"malformed": True}}),
        )

        record = next(
            item for item in result.agent_review.executions if item.role == "valuation"
        )
        self.assertEqual(record.status, "malformed")
        self.assertEqual(result.status, "limited")

    def test_explicit_unsupported_claim_limits_result(self) -> None:
        state, equity_input, request = _inputs()
        result = run_multi_agent_equity_review(
            request,
            state,
            equity_input,
            FakeAgentBackend(
                {
                    "business_quality": lambda packet: _result_payload(
                        packet, unsupported_claim=True
                    )
                }
            ),
        )

        self.assertEqual(result.status, "limited")
        self.assertTrue(
            next(
                item
                for item in result.agent_review.specialist_results
                if item.role == "business_quality"
            ).unsupported_claim
        )

    def test_timeout_and_unavailable_agent_are_bounded(self) -> None:
        state, equity_input, request = _inputs()
        backend = FakeAgentBackend(
            {
                "evidence": AgentTimeoutError("synthetic timeout"),
                "portfolio_risk": AgentUnavailableError("synthetic unavailable"),
            }
        )
        result = run_multi_agent_equity_review(
            request, state, equity_input, backend
        )
        statuses = {
            item.role: item.status for item in result.agent_review.executions
        }

        self.assertEqual(statuses["evidence"], "timeout")
        self.assertEqual(statuses["portfolio_risk"], "unavailable")
        self.assertTrue(all(count == 1 for count in backend.calls.values()))
        self.assertIn("evidence", result.agent_review.executed_agent_roles)
        self.assertNotIn("portfolio_risk", result.agent_review.executed_agent_roles)
        records = {item.role: item for item in result.agent_review.executions}
        self.assertTrue(records["evidence"].isolated_context)
        self.assertFalse(records["portfolio_risk"].isolated_context)

    def test_critic_detects_an_unflagged_unsupported_specialist_claim(self) -> None:
        state, equity_input, request = _inputs()
        seen_critic_facts: list[str] = []

        def unsupported_quality(packet):
            payload = _result_payload(packet)
            payload["claims"][0]["statement"] = (
                "Unsupported external market forecast was added."
            )
            return payload

        def critic(packet):
            seen_critic_facts.extend(item.statement for item in packet.facts)
            unsupported = any(
                "Unsupported external market forecast" in item
                for item in seen_critic_facts
            )
            return _result_payload(
                packet,
                conclusion="limits" if unsupported else "supports",
                findings=(
                    [
                        {
                            "code": "unsupported-specialist-claim",
                            "severity": "blocking",
                            "description": "A specialist claim is not supported by packet facts.",
                            "related_roles": ["business_quality"],
                            "evidence_references": [
                                packet.allowed_evidence_references[0]
                            ],
                        }
                    ]
                    if unsupported
                    else []
                ),
            )

        result = run_multi_agent_equity_review(
            request,
            state,
            equity_input,
            FakeAgentBackend(
                {"business_quality": unsupported_quality, "critic": critic}
            ),
        )

        self.assertEqual(result.status, "limited")
        self.assertEqual(
            result.agent_review.critic_findings[0].code,
            "unsupported-specialist-claim",
        )
        self.assertTrue(
            any("business_quality conclusion=supports" in item for item in seen_critic_facts)
        )
        self.assertTrue(
            any("Synthetic in-memory result." in item for item in seen_critic_facts)
        )

    def test_critic_blocking_finding_limits_result(self) -> None:
        state, equity_input, request = _inputs()

        def critic(packet):
            return _result_payload(
                packet,
                conclusion="limits",
                findings=[
                    {
                        "code": "unsupported-overstatement",
                        "severity": "blocking",
                        "description": "A specialist conclusion is stronger than its cited fact.",
                        "related_roles": ["business_quality"],
                        "evidence_references": [
                            packet.allowed_evidence_references[0]
                        ],
                    }
                ],
            )

        result = run_multi_agent_equity_review(
            request,
            state,
            equity_input,
            FakeAgentBackend({"critic": critic}),
        )

        self.assertEqual(result.status, "limited")
        self.assertEqual(
            result.agent_review.critic_findings[0].code,
            "unsupported-overstatement",
        )
        report = render_committee_report(result)
        self.assertIn("### Critic findings", report)
        self.assertIn("`unsupported-overstatement`", report)
        self.assertIn("- Severity: `blocking`.", report)
        self.assertIn(
            "A specialist conclusion is stronger than its cited fact.", report
        )
        self.assertIn("- Affected roles: `business_quality`.", report)
        self.assertIn("- Evidence references:", report)

    def test_agent_interpretation_cannot_override_engine(self) -> None:
        state, equity_input, request = _inputs()
        result = run_multi_agent_equity_review(
            request,
            state,
            equity_input,
            FakeAgentBackend(
                {
                    "valuation": lambda packet: _result_payload(
                        packet, conclusion="rejects"
                    )
                }
            ),
        )

        self.assertTrue(
            any("deterministic result governs" in item for item in result.disagreements)
        )
        self.assertIn("deterministic equity engine", result.final_synthesis.lower())

    def test_failure_trace_redacts_private_exception_text(self) -> None:
        state, equity_input, request = _inputs()
        result = run_multi_agent_equity_review(
            request,
            state,
            equity_input,
            FakeAgentBackend(
                {"business_quality": RuntimeError("private-account-123")}
            ),
        )
        serialized = json.dumps(to_json_value(result.agent_review.executions))

        self.assertNotIn("private-account-123", serialized)
        self.assertNotIn(request.message, serialized)

    def test_review_never_mutates_state(self) -> None:
        state, equity_input, request = _inputs()
        original = deepcopy(state)
        run_multi_agent_equity_review(
            request, state, equity_input, FakeAgentBackend()
        )
        self.assertEqual(state, original)

    def test_legacy_equity_route_is_explicit_deterministic_fallback(self) -> None:
        state, equity_input, request = _inputs()
        result = run_committee_workflow(
            request, state, equity_review_input=equity_input
        )

        self.assertEqual(result.committee_version, "2.0")
        self.assertEqual(result.agent_review.runtime_type, "none")
        self.assertEqual(result.agent_review.fallback_status, "deterministic_only")
        self.assertEqual(result.trace.critic_passes, 0)
        self.assertEqual(result.trace.review_lenses, ())

    def test_fallback_helper_starts_no_agent_execution(self) -> None:
        state, equity_input, request = _inputs()
        result = run_deterministic_equity_fallback(request, state, equity_input)
        self.assertTrue(
            all(item.status == "not_started" for item in result.agent_review.executions)
        )
        self.assertTrue(
            all(item.attempt == 0 for item in result.agent_review.executions)
        )

    def test_critic_bound_is_mandatory_and_cannot_be_retried(self) -> None:
        state, equity_input, request = _inputs()
        with self.assertRaisesRegex(ValidationError, "one bounded critic"):
            prepare_multi_agent_equity_review(
                replace(request, max_critic_passes=0), state, equity_input
            )

        backend = FakeAgentBackend()
        run_multi_agent_equity_review(request, state, equity_input, backend)
        self.assertEqual(backend.calls["critic"], 1)

    def test_packet_is_frozen_and_result_parser_rejects_extra_fields(self) -> None:
        state, equity_input, request = _inputs()
        prepared = prepare_multi_agent_equity_review(request, state, equity_input)
        packet = prepared.specialist_packets[0]
        with self.assertRaises(FrozenInstanceError):
            packet.role = "valuation"

        raw = _result_payload(packet)
        raw["raw_response"] = "must not be retained"
        with self.assertRaisesRegex(ValidationError, "missing or unknown"):
            _parse_result(packet, raw)

        injected = _result_payload(packet)
        injected["execution"] = {
            "runtime_type": "codex_native_subagents",
            "execution_id": "model-authored",
        }
        with self.assertRaisesRegex(ValidationError, "missing or unknown"):
            _parse_result(packet, injected)

        parsed = _parse_result(
            packet,
            _result_payload(packet),
            host_id="private-host-path-account-123",
        )
        self.assertNotIn("private-host-path-account-123", parsed.result_id)
        self.assertNotIn(
            "private-host-path-account-123", parsed.execution.execution_id
        )

    def test_portfolio_context_rejects_non_numeric_private_text(self) -> None:
        state, equity_input, request = _inputs()
        context = PortfolioRiskContext(direct_weight="private-account-123")  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValidationError, "between zero and one") as caught:
            prepare_multi_agent_equity_review(
                request, state, equity_input, portfolio_context=context
            )
        self.assertNotIn("private-account-123", str(caught.exception))

    def test_critic_packet_rejects_unvalidated_execution_status(self) -> None:
        state, equity_input, request = _inputs()
        prepared = prepare_multi_agent_equity_review(request, state, equity_input)
        records = tuple(
            AgentExecutionRecord(
                role=role,
                status=("private-account-123" if role == "evidence" else "unavailable"),
                attempt=1,
                isolated_context=False,
            )
            for role in ("evidence", "business_quality", "valuation", "portfolio_risk")
        )
        with self.assertRaisesRegex(ValidationError, "unsupported value") as caught:
            build_critic_packet(prepared, (), records)
        self.assertNotIn("private-account-123", str(caught.exception))

    def test_finalizer_rejects_private_failure_limitation(self) -> None:
        state, equity_input, request = _inputs()
        prepared = prepare_multi_agent_equity_review(request, state, equity_input)
        results = tuple(
            _parse_result(packet, _result_payload(packet))
            for packet in prepared.specialist_packets
        )
        records = tuple(
            AgentExecutionRecord(
                role=result.role,
                status="completed",
                attempt=1,
                isolated_context=True,
                execution_id=result.execution.execution_id,
                result_id=result.result_id,
            )
            for result in results
        )
        critic_packet = build_critic_packet(prepared, results, records)
        critic = _parse_result(critic_packet, _result_payload(critic_packet))
        critic_record = AgentExecutionRecord(
            role="critic",
            status="completed",
            attempt=1,
            isolated_context=True,
            execution_id=critic.execution.execution_id,
            result_id=critic.result_id,
        )
        unsafe_records = (
            replace(
                records[0],
                status="unavailable",
                isolated_context=False,
                execution_id=None,
                result_id=None,
                limitation="private-account-123",
            ),
            *records[1:],
            critic_record,
        )

        with self.assertRaisesRegex(ValidationError, "generic limitation") as caught:
            finalize_multi_agent_equity_review(
                prepared,
                results[1:],
                critic,
                unsafe_records,
                runtime_type=IN_MEMORY_TEST_RUNTIME,
            )
        self.assertNotIn("private-account-123", str(caught.exception))

    def test_eval_compares_concrete_defects_not_agreement(self) -> None:
        state, equity_input, request = _inputs()

        def critic(packet):
            return _result_payload(
                packet,
                conclusion="limits",
                findings=[
                    {
                        "code": "missing-portfolio-coverage",
                        "severity": "warning",
                        "description": "Portfolio coverage was not supplied.",
                        "related_roles": ["portfolio_risk"],
                        "evidence_references": [
                            packet.allowed_evidence_references[0]
                        ],
                    },
                    {
                        "code": "invented-defect",
                        "severity": "warning",
                        "description": "Synthetic unexpected critic finding.",
                        "related_roles": ["critic"],
                        "evidence_references": [
                            packet.allowed_evidence_references[0]
                        ],
                    },
                ],
            )

        result = run_multi_agent_equity_review(
            request,
            state,
            equity_input,
            FakeAgentBackend({"critic": critic}),
        )
        single_lens = detect_single_lens_equity_defects(
            prepare_multi_agent_equity_review(
                request, state, equity_input
            ).deterministic_result
        )
        evaluation = evaluate_review_modes(
            single_lens,
            result.agent_review,
            expected_defects=("missing-portfolio-coverage",),
        )

        self.assertEqual(
            evaluation.newly_detected_defects,
            ("missing-portfolio-coverage",),
        )
        self.assertEqual(evaluation.unexpected_defects, ("invented-defect",))
        self.assertEqual(evaluation.missed_defects, ())
        self.assertIn("not evidence", evaluation.comparison_basis)


if __name__ == "__main__":
    unittest.main()
