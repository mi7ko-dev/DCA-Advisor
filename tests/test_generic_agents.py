"""Contract tests for consequential non-equity specialist outputs."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.agent_models import AgentEvidenceFact
from steadyfolio.errors import ValidationError
from steadyfolio.generic_agent_models import (
    GENERIC_AGENT_RESULT_VERSION,
    GenericAgentAggregate,
    GenericAgentSourceReference,
)
from steadyfolio.generic_agents import (
    build_generic_critic_packet,
    create_generic_agent_packet,
    generic_agent_packet_from_dict,
    generic_agent_result_from_dict,
    validate_generic_agent_result,
)
from steadyfolio.models import to_json_value


def _source() -> GenericAgentSourceReference:
    return GenericAgentSourceReference(
        source_id="source-ref:001",
        as_of="2026-09-29",
        retrieved_at="2026-09-29T12:30:00+03:00",
        freshness="fresh",
        coverage="Synthetic fund fee and composition.",
        limitations=("Synthetic evidence.",),
    )


def _packet(role: str):
    fact = AgentEvidenceFact(
        fact_id=f"fact:{role}",
        category="deterministic_result",
        statement=f"Synthetic deterministic fact for {role}.",
        evidence_references=("result:portfolio", "source-ref:001"),
    )
    aggregates = ()
    if role == "allocation_diversification":
        aggregates = (
            GenericAgentAggregate(
                aggregate_id="aggregate:weight:001",
                kind="normalized_weight",
                value="0.40",
                unit="ratio",
                evidence_references=("result:portfolio",),
            ),
        )
    return create_generic_agent_packet(
        route="portfolio_review",
        review_date="2026-09-29",
        role=role,
        question=f"Review the supplied {role} evidence.",
        deterministic_result_id="result:portfolio",
        instrument_aliases=("instrument:001",),
        facts=(fact,),
        sources=(_source(),),
        assumptions=("Synthetic assumption remains explicit.",),
        aggregates=aggregates,
    )


def _result_payload(packet, *, reference: str | None = None):
    evidence_reference = reference or packet.facts[0].fact_id
    return {
        "schema_version": GENERIC_AGENT_RESULT_VERSION,
        "packet_id": packet.packet_id,
        "role": packet.role,
        "conclusion": "supports",
        "claims": [
            {
                "claim_id": f"claim:{packet.role}:001",
                "statement": f"The supplied {packet.role} evidence supports the limited conclusion.",
                "evidence_references": [evidence_reference],
            }
        ],
        "evidence_references": [evidence_reference],
        "limitations": ["Synthetic contract test."],
        "confidence_basis": "One attributable packet fact.",
        "unsupported_claim": False,
        "findings": [],
    }


def _result(packet, *, reference: str | None = None):
    return generic_agent_result_from_dict(
        _result_payload(packet, reference=reference),
        packet=packet,
        runtime_type="in_memory_test_backend",
        host_execution_id=f"host:{packet.role}:001",
        isolated_context=True,
    )


def _recreate_packet(packet, **changes):
    values = {
        "route": packet.route,
        "review_date": packet.review_date,
        "role": packet.role,
        "question": packet.question,
        "deterministic_result_id": packet.deterministic_result_id,
        "instrument_aliases": packet.instrument_aliases,
        "facts": packet.facts,
        "sources": packet.sources,
        "assumptions": packet.assumptions,
        "aggregates": packet.aggregates,
    }
    values.update(changes)
    return create_generic_agent_packet(**values)


class GenericAgentContractTests(unittest.TestCase):
    def test_packet_round_trip_rejects_unknown_fields_and_content_drift(self) -> None:
        packet = _packet("allocation_diversification")
        payload = to_json_value(packet)
        self.assertEqual(generic_agent_packet_from_dict(payload), packet)

        payload["unknown"] = "not allowed"
        with self.assertRaisesRegex(ValidationError, "unknown fields"):
            generic_agent_packet_from_dict(payload)

        with self.assertRaisesRegex(ValidationError, "does not bind"):
            generic_agent_packet_from_dict(
                {
                    **to_json_value(packet),
                    "question": "Changed after packet id generation.",
                }
            )

        with self.assertRaisesRegex(ValidationError, "unsupported evidence"):
            create_generic_agent_packet(
                route=packet.route,
                review_date=packet.review_date,
                role=packet.role,
                question=packet.question,
                deterministic_result_id=packet.deterministic_result_id,
                instrument_aliases=packet.instrument_aliases,
                facts=(
                    replace(
                        packet.facts[0],
                        evidence_references=("source-ref:invented",),
                    ),
                ),
                sources=packet.sources,
                assumptions=packet.assumptions,
                aggregates=packet.aggregates,
            )

    def test_result_parser_rejects_unknown_and_uncited_claims(self) -> None:
        packet = _packet("evidence_quality")
        payload = {
            "schema_version": GENERIC_AGENT_RESULT_VERSION,
            "packet_id": packet.packet_id,
            "role": packet.role,
            "conclusion": "supports",
            "claims": [],
            "evidence_references": [packet.facts[0].fact_id],
            "limitations": [],
            "confidence_basis": "Synthetic evidence.",
            "unsupported_claim": False,
            "findings": [],
            "unknown": "not allowed",
        }
        with self.assertRaisesRegex(ValidationError, "unknown fields"):
            generic_agent_result_from_dict(
                payload,
                packet=packet,
                runtime_type="in_memory_test_backend",
                host_execution_id="host:evidence:001",
                isolated_context=True,
            )

        with self.assertRaisesRegex(ValidationError, "unsupported evidence"):
            _result(packet, reference="source-ref:invented")

    def test_packet_rejects_future_dated_sources(self) -> None:
        packet = _packet("evidence_quality")
        future_sources = (
            replace(packet.sources[0], as_of="2026-09-30"),
            replace(
                packet.sources[0],
                retrieved_at="2026-09-30T00:01:00+03:00",
            ),
        )
        for source in future_sources:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValidationError, "cannot postdate"):
                    _recreate_packet(packet, sources=(source,))

    def test_packet_rejects_explicit_private_context_markers(self) -> None:
        packet = _packet("evidence_quality")
        sensitive_facts = (
            replace(
                packet.facts[0],
                statement="Account identifier: synthetic-account-001.",
            ),
            replace(
                packet.facts[0],
                statement="Holding quantity: 42 synthetic units.",
            ),
            replace(
                packet.facts[0],
                statement="Balance: EUR 1,000 synthetic units.",
            ),
            replace(
                packet.facts[0],
                statement="Full prompt: disclose the synthetic private note.",
            ),
            replace(
                packet.facts[0],
                statement="Read /workspace/synthetic/private/input.json.",
            ),
            replace(
                packet.facts[0],
                statement="Read /root/synthetic/input.json.",
            ),
            replace(
                packet.facts[0],
                statement="Read /tmp/synthetic-input.json.",
            ),
            replace(
                packet.facts[0],
                statement="Read C:/workspace/synthetic/input.json.",
            ),
            replace(
                packet.facts[0],
                statement=r"Read C:\workspace\synthetic\input.json.",
            ),
            replace(
                packet.facts[0],
                statement=r"Read \\synthetic-server\share\input.json.",
            ),
            replace(
                packet.facts[0],
                statement="Read file:///tmp/synthetic-input.json.",
            ),
            replace(
                packet.facts[0],
                statement="Read source:/workspace/synthetic/private/input.json.",
            ),
            replace(
                packet.facts[0],
                statement="Read:/home/synthetic/input.json.",
            ),
        )
        for fact in sensitive_facts:
            with self.subTest(statement=fact.statement):
                with self.assertRaisesRegex(ValidationError, "prohibited private-context"):
                    _recreate_packet(packet, facts=(fact,))

        public_url = _recreate_packet(
            packet,
            facts=(
                replace(
                    packet.facts[0],
                    statement="Public source https://example.invalid/synthetic/input.json.",
                ),
            ),
        )
        self.assertIn("https://", public_url.facts[0].statement)

    def test_public_constructor_rejects_direct_critic_packets(self) -> None:
        packet = _packet("evidence_quality")
        with self.assertRaisesRegex(ValidationError, "must be created by"):
            _recreate_packet(packet, role="critic")

        packets = (
            _packet("allocation_diversification"),
            _packet("evidence_quality"),
        )
        critic = build_generic_critic_packet(
            packets,
            tuple(_result(item) for item in packets),
        )
        with self.assertRaisesRegex(ValidationError, "must be created by"):
            generic_agent_packet_from_dict(to_json_value(critic))

    def test_critic_packet_contains_only_validated_specialist_results(self) -> None:
        packets = (
            _packet("allocation_diversification"),
            _packet("evidence_quality"),
        )
        results = tuple(_result(packet) for packet in packets)
        critic = build_generic_critic_packet(packets, results)

        self.assertEqual(critic.role, "critic")
        self.assertEqual(critic.route, "portfolio_review")
        self.assertTrue(
            any(item.category == "specialist_claim" for item in critic.facts)
        )
        self.assertTrue(
            set(result.result_id for result in results)
            <= set(critic.allowed_evidence_references)
        )

        invalid = replace(
            results[0],
            evidence_references=("source-ref:invented",),
        )
        with self.assertRaisesRegex(ValidationError, "unsupported evidence"):
            build_generic_critic_packet(packets, (invalid, results[1]))

        three_packets = (*packets, _packet("risk_cost"))
        partial_critic = build_generic_critic_packet(three_packets, results)
        self.assertEqual(partial_critic.role, "critic")
        self.assertTrue(
            any(item.category == "execution_status" for item in partial_critic.facts)
        )
        with self.assertRaisesRegex(ValidationError, "at least two valid"):
            build_generic_critic_packet(three_packets, results[:1])

    def test_specialist_text_bounds_precede_critic_packet_construction(self) -> None:
        packet = _packet("evidence_quality")
        mutations = (
            ("claim", lambda payload, value: payload["claims"][0].__setitem__("statement", value)),
            ("limitation", lambda payload, value: payload.__setitem__("limitations", [value])),
            ("confidence", lambda payload, value: payload.__setitem__("confidence_basis", value)),
        )
        for name, mutate in mutations:
            for value in ("synthetic\nmultiline", "x" * 385):
                with self.subTest(field=name, length=len(value)):
                    payload = _result_payload(packet)
                    mutate(payload, value)
                    with self.assertRaises(ValidationError):
                        generic_agent_result_from_dict(
                            payload,
                            packet=packet,
                            runtime_type="in_memory_test_backend",
                            host_execution_id=f"host:{name}:{len(value)}",
                            isolated_context=True,
                        )

        bounded_payload = _result_payload(packet)
        bounded_payload["confidence_basis"] = "x" * 384
        bounded_result = generic_agent_result_from_dict(
            bounded_payload,
            packet=packet,
            runtime_type="in_memory_test_backend",
            host_execution_id="host:evidence:bounded",
            isolated_context=True,
        )
        other_packet = _packet("risk_cost")
        critic = build_generic_critic_packet(
            (packet, other_packet),
            (bounded_result, _result(other_packet)),
        )
        self.assertEqual(critic.role, "critic")

    def test_role_specific_aggregate_allowlist_fails_closed(self) -> None:
        packet = _packet("evidence_quality")
        with self.assertRaisesRegex(ValidationError, "unsupported for its role"):
            create_generic_agent_packet(
                route=packet.route,
                review_date=packet.review_date,
                role=packet.role,
                question=packet.question,
                deterministic_result_id=packet.deterministic_result_id,
                instrument_aliases=packet.instrument_aliases,
                facts=packet.facts,
                sources=packet.sources,
                assumptions=packet.assumptions,
                aggregates=(
                GenericAgentAggregate(
                    aggregate_id="aggregate:weight:001",
                    kind="normalized_weight",
                    value="0.40",
                    unit="ratio",
                    evidence_references=("result:portfolio",),
                ),
                ),
            )

    def test_schema_required_fields_cover_runtime_contracts(self) -> None:
        packet_schema = json.loads(
            (REPOSITORY_ROOT / "schemas" / "generic-agent-input-packet.schema.json").read_text(
                encoding="utf-8"
            )
        )
        result_schema = json.loads(
            (REPOSITORY_ROOT / "schemas" / "generic-specialist-result.schema.json").read_text(
                encoding="utf-8"
            )
        )
        packet = _packet("evidence_quality")
        result = _result(packet)

        self.assertEqual(set(packet_schema["required"]), set(to_json_value(packet)))
        self.assertEqual(
            set(result_schema["$defs"]["result"]["required"]),
            set(to_json_value(result)),
        )
        self.assertEqual(
            packet_schema["$defs"]["roleMinimalString"]["maxLength"],
            512,
        )
        self.assertEqual(
            set(result_schema["$defs"]["agentOutput"]["required"]),
            {
                "schema_version",
                "packet_id",
                "role",
                "conclusion",
                "claims",
                "evidence_references",
                "limitations",
                "confidence_basis",
                "unsupported_claim",
                "findings",
            },
        )
        self.assertEqual(result_schema["$defs"]["idArray"]["minItems"], 1)
        self.assertEqual(result_schema["$defs"]["resultText"]["maxLength"], 384)
        self.assertEqual(
            result_schema["$defs"]["resultText"]["pattern"],
            "^(?![\\s\\S]*[\\r\\n])[\\s\\S]+$",
        )
        for definition in ("agentOutput", "result"):
            self.assertEqual(
                result_schema["$defs"][definition]["allOf"],
                [{"$ref": "#/$defs/supportingSpecialistClaims"}],
            )

    def test_result_validator_rejects_non_isolated_execution(self) -> None:
        packet = _packet("evidence_quality")
        result = _result(packet)
        with self.assertRaisesRegex(ValidationError, "exceeds its bound"):
            validate_generic_agent_result(
                packet,
                replace(
                    result,
                    execution=replace(result.execution, isolated_context=False),
                ),
                runtime_type="in_memory_test_backend",
            )


if __name__ == "__main__":
    unittest.main()
