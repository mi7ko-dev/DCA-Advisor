# Workflow routing

Use only the narrow route needed for the request.

| Request | Deterministic tools | Review lenses | Critic | Stop condition |
| --- | --- | --- | --- | --- |
| Monthly contribution | `analyze_portfolio`, `plan_contribution` | None by default | No | Missing amount/currency, price, FX, approved target, or executable constraints |
| Portfolio review | `analyze_portfolio`, optional `ResearchProvider.fetch`, `analyze_portfolio_intelligence` | Allocation/diversification and risk/cost/evidence | Once when conclusions materially differ or evidence is incomplete | Missing or stale evidence prevents the requested conclusion |
| ETF thesis review | `ResearchProvider.fetch`, `review_investment_thesis` | Thesis-fit and evidence-quality | Once when conclusions materially differ | No active thesis, no dated evidence, or stale evidence prevents a conclusion |
| Fund overlap | `analyze_portfolio`, `ResearchProvider.fetch`, `analyze_portfolio_intelligence` | Allocation/diversification and evidence-quality | Once for incomplete coverage | No dated holdings or incompatible coverage |

## Required inputs

Always require an explicit review date and validated portfolio state. Contribution
planning also requires a positive amount, ISO currency, dated prices, required FX,
constraints, and an approved target. Portfolio intelligence requires a structured
snapshot with provider, source, value date, retrieval date, methodology, freshness,
terms, and limitations. Thesis review requires an active thesis and dated evidence.

The Phase 5 provider is offline. A provider call reads a supplied structured
snapshot and is not a live integration. Do not claim current market knowledge from
it.

## Interpretation boundaries

- Positive drift means current weight minus approved target is positive.
- A contribution plan is buy-only and may leave drift that cannot be corrected with
  the available amount and constraints.
- Observed overlap and concentration cover supplied holdings only. Missing holdings
  are unknown, not zero.
- A price decline alone does not invalidate a thesis.
- Tax, legal, regulatory, suitability, and transaction-execution conclusions remain
  outside this workflow.
- When a policy-preserving drift action is possible but research is missing or
  stale, distinguish those facts: existing-policy maintenance may be calculable
  while an evidence-dependent target or thesis change is not supported.

## Bounded execution

The default and maximum Phase 5 bounds are one research pass, one critic pass, one
revision, and zero live external calls. Do not retry a missing provider or broaden
research silently. Report the missing evidence and the smallest useful next step.
