# Synthetic Multi-Agent Contract Demo

Request: Analyze this synthetic stock with a bounded multi-agent equity review.
Route: `equity_review`
Status: `limited`
As of: 2026-01-31

## Facts and deterministic calculations

- Instrument identity matched for synthetic-compute-company.
- Free-cash-flow hard screen: passed.
- Quality score: 100% (11 of 11 available points; 8 of 8 criteria).
- Quality classification: quality.
- Valuation status: acceptable using dcf.

## Sources, dates, and data limitations

| Source | Provider | Value time | Retrieved | Freshness | Limitations |
| --- | --- | --- | --- | --- | --- |
| synthetic-equity-source | SteadyFolio Synthetic Equity Provider | 2026-01-31 | 2026-01-31T18:00:00+00:00 | fresh | Synthetic evidence for deterministic examples only. |

- Synthetic evidence for deterministic examples only.

## Assumptions

- The supplied evidence is structured and attributable.
- Agent interpretations are secondary to deterministic calculations.

## Specialist interpretations

### evidence

Conclusion: `supports`

Synthetic evidence interpretation uses only packet evidence.

Evidence references:

- equity-review:synthetic-compute-company:2026-01-31

Lens limitations:

- Synthetic in-memory agent-contract demonstration.

### business_quality

Conclusion: `supports`

Synthetic business_quality interpretation uses only packet evidence.

Evidence references:

- equity-review:synthetic-compute-company:2026-01-31

Lens limitations:

- Synthetic in-memory agent-contract demonstration.

### valuation

Conclusion: `limits`

Synthetic valuation interpretation uses only packet evidence.

Evidence references:

- equity-review:synthetic-compute-company:2026-01-31

Lens limitations:

- Synthetic in-memory agent-contract demonstration.

### portfolio_risk

Conclusion: `supports`

Synthetic portfolio_risk interpretation uses only packet evidence.

Evidence references:

- equity-review:synthetic-compute-company:2026-01-31

Lens limitations:

- Synthetic in-memory agent-contract demonstration.

## Meaningful disagreements

- Business quality and valuation reached different bounded conclusions: business_quality=supports, valuation=limits.
- Deterministic overall stance=supports differs from the bounded valuation conclusion=limits; the deterministic result governs.

## Final synthesis and proposed next action

The deterministic equity engine concluded eligible_for_consideration. Four isolated specialist executions and one critic execution completed; their interpretations do not override the deterministic result. The in-memory backend demonstrates contracts and bounds only; it is not a live Codex subagent execution.

- The evidence supports further consideration, not trade execution.

User approval required: no.
- Any later transaction or policy change requires separate explicit approval.
Mutation performed: no.

## Execution trace

- Deterministic tools: `review_equity`.
- Review lenses: None.
- Provider calls: 0.
- Live external calls: 0.
- Critic passes: 1.
- Revisions: 0.
- Execution mode: in-memory agent-contract test backend.
- Independent agents were used only when runtime is `codex_native_subagents`; `in_memory_test_backend` is a contract test, and `none` is a deterministic fallback.

## Agent workflow

- Runtime: `in_memory_test_backend`.
- Executed agent roles: `evidence`, `business_quality`, `valuation`, `portfolio_risk`, `critic`.
- Agent status: `limited`.
- Fallback: `not_used`.
- Critic findings: 1.
