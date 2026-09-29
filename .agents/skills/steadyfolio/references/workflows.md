# Workflow routing

Use only the narrow route needed for the request.

| Request | Deterministic tools | Review lenses | Critic | Stop condition |
| --- | --- | --- | --- | --- |
| Monthly contribution | `analyze_portfolio`, `plan_contribution` | None by default | No | Missing amount/currency, price, FX, approved target, or executable constraints |
| Portfolio review | `analyze_portfolio`, optional cached or host-researched evidence, `ResearchProvider.fetch` when structured input exists, `analyze_portfolio_intelligence` | Two or three isolated roles for consequential/uncertain reviews; otherwise allocation/diversification and risk/cost/evidence lenses | One isolated critic after agents; otherwise once when conclusions materially differ or evidence is incomplete | Missing or stale evidence prevents the requested conclusion |
| ETF thesis review | Cached or host-researched evidence, optional `ResearchProvider.fetch`, `review_investment_thesis` | Two or three isolated roles for consequential/uncertain reviews; otherwise thesis-fit and evidence-quality lenses | One isolated critic after agents; otherwise once when conclusions materially differ | No active thesis, no dated evidence, or stale evidence prevents a conclusion |
| Fund overlap | `analyze_portfolio`, cached or host-researched evidence, optional `ResearchProvider.fetch`, `analyze_portfolio_intelligence` | Two isolated roles for consequential/uncertain reviews; otherwise allocation/diversification and evidence-quality lenses | One isolated critic after agents; otherwise once for incomplete coverage | No dated holdings or incompatible coverage |
| Individual equity review | `review_equity` exactly once over supplied `EquityReviewInput` | Four host-native Codex specialists: evidence, business quality, valuation, and portfolio risk | One separate critic execution | Identity mismatch, stale or missing required evidence, invalid agent output, runtime failure, failed FCF hard screen, or unavailable/conflicting valuation |
| Explicit portfolio-policy check | `analyze_portfolio`, `evaluate_portfolio_policy` | None by default | No | Unknown instruments, invalid thresholds, or a denominator other than `invested_positions` |

## Required inputs

Always require an explicit review date and validated portfolio state. Contribution
planning also requires a positive amount, ISO currency, dated prices, required FX,
constraints, and an approved target. Portfolio intelligence requires a structured
snapshot with provider, source, value date, retrieval date, methodology, freshness,
terms, and limitations. Thesis review requires an active thesis and dated evidence.

The Python `ResearchProvider` remains offline. A provider call reads a supplied
structured snapshot and is not a live integration. The Codex lead may separately
use host-native web research under `research-and-context.md`, then convert only
attributable facts into validated dated inputs. Do not claim current market
knowledge from the offline provider or from stale cache.

The deterministic equity engine is offline. The Codex lead may use the bounded
host-research protocol to prepare current public evidence, but must convert it into
a dated, attributable `EquityReviewInput`; never convert unsourced prose or
remembered market values into structured evidence. A portfolio policy instance
contains user-specific thresholds and instrument classifications and therefore
belongs under ignored `private/`.

## Interpretation boundaries

- Positive drift means current weight minus approved target is positive.
- A contribution plan is buy-only and may leave drift that cannot be corrected with
  the available amount and constraints.
- Observed overlap and concentration cover supplied holdings only. Missing holdings
  are unknown, not zero.
- A price decline alone does not invalidate a thesis.
- Tax, legal, regulatory, suitability, and transaction-execution conclusions remain
  outside this workflow.
- An ISIN identifies the economic instrument, while MIC, ticker, and trading
  currency identify a listing. A mismatch stops the equity route.
- Individual-equity quality and valuation are separate conclusions. Do not turn a
  high quality score into a claim that the current price is attractive.
- When a policy-preserving drift action is possible but research is missing or
  stale, distinguish those facts: existing-policy maintenance may be calculable
  while an evidence-dependent target or thesis change is not supported.

## Bounded execution

The equity route permits one execution for each of four specialists, one critic
execution, one final synthesis, and no retries. Other qualifying consequential
routes use the smallest useful set of two or three specialists plus one critic.
The lead may perform one host-native research pass after inspecting the private
cache; specialists never browse. Contribution starts no agents or research unless
a material conflict or uncertainty is explicitly escalated. Do not retry a missing
provider, repeat a failed search, or broaden research silently. Report the missing
evidence and the smallest useful next step.
