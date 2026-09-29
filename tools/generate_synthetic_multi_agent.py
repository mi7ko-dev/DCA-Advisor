#!/usr/bin/env python3
"""Generate a deterministic Phase 8 agent-contract demonstration."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from decimal import Decimal


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from steadyfolio.agent_models import (  # noqa: E402
    IN_MEMORY_TEST_RUNTIME,
    PortfolioRiskContext,
)
from steadyfolio.committee_models import CommitteeRequest  # noqa: E402
from steadyfolio.committee_reporting import render_committee_report  # noqa: E402
from steadyfolio.equity_validation import equity_review_input_from_dict  # noqa: E402
from steadyfolio.equity import review_equity  # noqa: E402
from steadyfolio.models import to_json_value  # noqa: E402
from steadyfolio.multi_agent import (  # noqa: E402
    AgentBackendResponse,
    detect_single_lens_equity_defects,
    evaluate_review_modes,
    run_multi_agent_equity_review,
)
from steadyfolio.validation import state_from_dict  # noqa: E402


EXAMPLES = REPOSITORY_ROOT / "examples"


def _read(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)


def _write_json(path: Path, value: object) -> None:
    _write_text(
        path,
        json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
    )


def _payload(packet) -> dict[str, object]:
    conclusion = "limits" if packet.role == "valuation" else "supports"
    claims = []
    findings = []
    if packet.role != "critic":
        claims.append(
            {
                "claim_id": f"synthetic.{packet.role}",
                "statement": f"Synthetic {packet.role} interpretation uses only packet evidence.",
                "evidence_references": [packet.allowed_evidence_references[0]],
            }
        )
    else:
        statements = tuple(item.statement for item in packet.facts)
        quality_supports = any(
            "business_quality conclusion=supports" in item for item in statements
        )
        valuation_limits = any(
            "valuation conclusion=limits" in item for item in statements
        )
        if quality_supports and valuation_limits:
            conclusion = "limits"
            findings.append(
                {
                    "code": "quality-valuation-disagreement",
                    "severity": "warning",
                    "description": "Business quality and valuation support different bounded actions.",
                    "related_roles": ["business_quality", "valuation"],
                    "evidence_references": [packet.allowed_evidence_references[0]],
                }
            )
    return {
        "schema_version": "1.0",
        "packet_id": packet.packet_id,
        "role": packet.role,
        "conclusion": conclusion,
        "claims": claims,
        "evidence_references": [packet.allowed_evidence_references[0]],
        "limitations": ["Synthetic in-memory agent-contract demonstration."],
        "confidence_basis": "Cited synthetic packet evidence only.",
        "unsupported_claim": False,
        "findings": findings,
    }


class SyntheticBackend:
    runtime_type = IN_MEMORY_TEST_RUNTIME

    def execute(self, packet):
        return AgentBackendResponse(
            output=_payload(packet),
            host_execution_id=f"synthetic-host-execution:{packet.role}",
            isolated_context=True,
        )


def main() -> int:
    state = state_from_dict(_read(EXAMPLES / "equity-portfolio.example.json"))
    evidence = equity_review_input_from_dict(
        _read(EXAMPLES / "equity-evidence.example.json")
    )
    request = CommitteeRequest(
        id="synthetic-phase8-review",
        message="Analyze this synthetic stock with a bounded multi-agent equity review.",
        as_of=evidence.as_of,
        instrument_id=evidence.identity.instrument_id,
    )
    portfolio_context = PortfolioRiskContext(
        direct_weight=Decimal("0.08"),
        max_direct_weight=Decimal("0.15"),
        thematic_exposure=Decimal("0.30"),
        overlap_weight=Decimal("0.04"),
        fragmented_positions=2,
        max_fragmented_positions=6,
        satellite_weight=Decimal("0.24"),
        max_satellite_weight=Decimal("0.30"),
    )
    result = run_multi_agent_equity_review(
        request,
        state,
        evidence,
        SyntheticBackend(),
        portfolio_context=portfolio_context,
    )
    single_lens_defects = detect_single_lens_equity_defects(
        review_equity(state, evidence)
    )
    evaluation = evaluate_review_modes(
        single_lens_defects,
        result.agent_review,
        expected_defects=("quality-valuation-disagreement",),
    )
    _write_json(
        EXAMPLES / "results" / "multi-agent-equity-review.example.json",
        {"synthetic": True, "runtime_disclosure": "in_memory_test_backend", "result": to_json_value(result)},
    )
    _write_json(
        EXAMPLES / "results" / "multi-agent-eval.example.json",
        {"synthetic": True, "evaluation": to_json_value(evaluation)},
    )
    _write_text(
        EXAMPLES / "reports" / "multi-agent-equity-review.md",
        render_committee_report(result, title="Synthetic Multi-Agent Contract Demo") + "\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
