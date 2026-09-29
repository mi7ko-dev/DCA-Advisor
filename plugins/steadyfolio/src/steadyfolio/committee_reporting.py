"""Human-readable rendering for bounded committee workflow results."""

from __future__ import annotations

from .committee_models import CommitteeResult


def _items(values: tuple[str, ...], *, empty: str = "None.") -> list[str]:
    return [f"- {value}" for value in values] if values else [f"- {empty}"]


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_committee_report(
    result: CommitteeResult,
    *,
    title: str = "SteadyFolio Review",
) -> str:
    """Render facts and interpretations in visibly separate sections."""

    source_rows = [
        "| Source | Provider | Value time | Retrieved | Freshness | Limitations |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    source_rows.extend(
        "| {source} | {provider} | {value_time} | {retrieved} | {freshness} | {limitations} |".format(
            source=_cell(item.source_id),
            provider=_cell(item.provider),
            value_time=_cell(item.value_time),
            retrieved=_cell(item.retrieved_at),
            freshness=_cell(item.freshness),
            limitations=_cell("; ".join(item.limitations) or "None"),
        )
        for item in result.sources
    )
    if not result.sources:
        source_rows.append("| None | None | None | None | unavailable | No source supplied |")

    specialist_rows: list[str] = []
    for item in result.specialist_interpretations:
        specialist_rows.extend(
            (
                f"### {item.role}",
                "",
                f"Conclusion: `{item.conclusion}`",
                "",
                item.interpretation,
                "",
                "Evidence references:",
                "",
                *_items(item.evidence_references),
                "",
                "Lens limitations:",
                "",
                *_items(item.limitations),
                "",
            )
        )
    if not specialist_rows:
        specialist_rows = [
            "No specialist lens was needed for this routine deterministic request.",
            "",
        ]

    tools = ", ".join(f"`{item}`" for item in result.trace.deterministic_tools) or "None"
    roles = ", ".join(f"`{item}`" for item in result.trace.review_lenses) or "None"
    return "\n".join(
        [
            f"# {title}",
            "",
            f"Request: {result.request_text}",
            f"Route: `{result.route}`",
            f"Status: `{result.status}`",
            f"As of: {result.as_of}",
            "",
            "## Facts and deterministic calculations",
            "",
            *_items(result.deterministic_facts),
            "",
            "## Sources, dates, and data limitations",
            "",
            *source_rows,
            "",
            *_items(result.data_limitations, empty="No additional limitations reported."),
            "",
            "## Assumptions",
            "",
            *_items(result.assumptions),
            "",
            "## Specialist interpretations",
            "",
            *specialist_rows,
            "## Meaningful disagreements",
            "",
            *_items(result.disagreements),
            "",
            "## Final synthesis and proposed next action",
            "",
            result.final_synthesis,
            "",
            *_items(result.proposed_next_actions),
            "",
            f"User approval required: {'yes' if result.requires_user_approval else 'no'}.",
            *_items(result.approval_reasons, empty="No approval-gated mutation is proposed."),
            f"Mutation performed: {'yes' if result.mutation_performed else 'no'}.",
            "",
            "## Execution trace",
            "",
            f"- Deterministic tools: {tools}.",
            f"- Review lenses: {roles}.",
            f"- Provider calls: {result.trace.provider_calls}.",
            f"- Live external calls: {result.trace.external_calls}.",
            f"- Critic passes: {result.trace.critic_passes}.",
            f"- Revisions: {result.trace.revisions}.",
            f"- Execution mode: {result.trace.execution_mode}.",
            "- Review lenses are sequential interpretations, not independent agents or verification.",
        ]
    )
