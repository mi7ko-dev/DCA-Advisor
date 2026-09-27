# Synthetic Committee Demo: demo-monthly-contribution

Request: I have EUR 400 to invest this month.
Route: `contribution`
Status: `complete`
As of: 2026-01-31

## Facts and deterministic calculations

- Portfolio value is 1000.00 EUR on 2026-01-31.
- Weighted annual fee rate is 0.19%.
- instrument-global: current 80.00%, approved target 50.00%, signed drift 30.00%.
- instrument-bond: current 20.00%, approved target 50.00%, signed drift -30.00%.
- Proposed purchases total 398.60 EUR.
- Estimated costs total 1.40 EUR.
- Residual cash is 0.00 EUR.
- Proposed buy for instrument-bond: quantity 7.972, value 398.60 EUR, remaining drift -7.20%.

## Sources, dates, and data limitations

| Source | Provider | Value time | Retrieved | Freshness | Limitations |
| --- | --- | --- | --- | --- | --- |
| synthetic-prices-2026-01-31 | Synthetic Fixture Provider | 2026-01-31T16:30:00+00:00 | 2026-01-31T18:00:00+00:00 | fresh | None |

- No additional limitations reported.

## Assumptions

- The approved target remains policy and the method is drift_aware.
- Prices, FX, fees, and trading constraints are supplied inputs, not forecasts.

## Specialist interpretations

No specialist lens was needed for this routine deterministic request.

## Meaningful disagreements

- None.

## Final synthesis and proposed next action

The buy-only plan uses the available contribution without selling or mutating portfolio state. Any remaining drift stays visible.

- Review the proposal and its source dates.
- Approve separately before placing or recording any real transaction.

User approval required: yes.
- Executing or recording a real transaction requires explicit user approval.
Mutation performed: no.

## Execution trace

- Deterministic tools: `analyze_portfolio`, `plan_contribution`.
- Review lenses: None.
- Provider calls: 0.
- Live external calls: 0.
- Critic passes: 0.
- Revisions: 0.
- Execution mode: deterministic engine with sequential review lenses; no independent agents.
- Review lenses are sequential interpretations, not independent agents or verification.

---

# Synthetic Committee Demo: demo-portfolio-review

Request: Review my portfolio.
Route: `portfolio_review`
Status: `limited`
As of: 2026-01-31

## Facts and deterministic calculations

- Portfolio value is 1000.00 EUR on 2026-01-31.
- Weighted annual fee rate is 0.19%.
- instrument-global: current 80.00%, approved target 50.00%, signed drift 30.00%.
- instrument-bond: current 20.00%, approved target 50.00%, signed drift -30.00%.
- Observed company look-through covers 20.40% of portfolio weight.
- Unclassified company look-through is 79.60%.

## Sources, dates, and data limitations

| Source | Provider | Value time | Retrieved | Freshness | Limitations |
| --- | --- | --- | --- | --- | --- |
| synthetic-classified-exposures | SteadyFolio Synthetic Research Provider | 2025-12-31 | 2026-01-31T18:07:00+00:00 | stale | Unclassified fund weight is intentionally retained as unknown. |
| synthetic-fund-facts | SteadyFolio Synthetic Research Provider | 2026-01-15 | 2026-01-31T18:05:00+00:00 | fresh | The facts do not describe a real fund. |
| synthetic-fund-holdings | SteadyFolio Synthetic Research Provider | 2025-12-31 | 2026-01-31T18:06:00+00:00 | stale | Only selected holdings are supplied; coverage is intentionally incomplete. |
| synthetic-prices-2026-01-31 | Synthetic Fixture Provider | 2026-01-31T16:30:00+00:00 | 2026-01-31T18:00:00+00:00 | fresh | None |
| synthetic-total-return-history | SteadyFolio Synthetic Research Provider | 2026-01-31 | 2026-01-31T18:08:00+00:00 | fresh | Five observations are insufficient for investment forecasting. |

- Research source synthetic-classified-exposures is stale at 31 days old.
- Research source synthetic-fund-holdings is stale at 31 days old.
- Company concentration is partial; unclassified portfolio weight is not zero exposure.
- Sector exposure is partial; unclassified weight remains.
- Geography exposure is partial; unclassified weight remains.
- Currency exposure is partial; unclassified weight remains.

## Assumptions

- The approved target is the policy baseline.
- Missing research is unknown and is never treated as zero exposure.

## Specialist interpretations

### allocation-diversification

Conclusion: `act_within_approved_policy`

The largest signed drift is instrument-global at 30.00%; policy-preserving new contributions can reduce drift without selling.

Evidence references:

- analysis:synthetic-investor:2026-01-31

Lens limitations:

- This lens does not authorize a target change or transaction.

### risk-cost-evidence

Conclusion: `limited_evidence`

Look-through coverage is incomplete, so observed concentration is a lower-bound view and not a complete diversification conclusion.

Evidence references:

- intelligence:synthetic-investor:2026-01-31
- synthetic-classified-exposures
- synthetic-fund-facts
- synthetic-fund-holdings
- synthetic-total-return-history

Lens limitations:

- Research source synthetic-classified-exposures is stale at 31 days old.
- Research source synthetic-fund-holdings is stale at 31 days old.
- Company concentration is partial; unclassified portfolio weight is not zero exposure.
- Sector exposure is partial; unclassified weight remains.
- Geography exposure is partial; unclassified weight remains.
- Currency exposure is partial; unclassified weight remains.

### committee-critic

Conclusion: `preserve_boundary`

Keep the policy-preserving drift fact separate from the evidence-dependent conclusion; do not turn missing evidence into a target change.

Evidence references:

- analysis:synthetic-investor:2026-01-31
- intelligence:synthetic-investor:2026-01-31
- synthetic-classified-exposures
- synthetic-fund-facts
- synthetic-fund-holdings
- synthetic-total-return-history

Lens limitations:

- The critic adds no new source evidence.

## Meaningful disagreements

- The allocation lens supports policy-preserving drift correction, while the evidence lens limits or defers evidence-dependent conclusions.

## Final synthesis and proposed next action

The portfolio can be reviewed against its approved policy, but partial look-through remains a limitation rather than evidence of zero exposure.

- Refresh missing or stale sources when the conclusion depends on them.
- Request explicit approval before persisting a target or policy change.

User approval required: no.
- A future target or policy change would require explicit user approval.
Mutation performed: no.

## Execution trace

- Deterministic tools: `analyze_portfolio`, `ResearchProvider.fetch`, `analyze_portfolio_intelligence`.
- Review lenses: `allocation-diversification`, `risk-cost-evidence`, `committee-critic`.
- Provider calls: 1.
- Live external calls: 0.
- Critic passes: 1.
- Revisions: 1.
- Execution mode: deterministic engine with sequential review lenses; no independent agents.
- Review lenses are sequential interpretations, not independent agents or verification.

---

# Synthetic Committee Demo: demo-etf-thesis

Request: Should this ETF still be in my portfolio?
Route: `thesis_review`
Status: `complete`
As of: 2026-01-31

## Facts and deterministic calculations

- Thesis thesis-global has role growth and deterministic proposed action retain.
- Target weight is 50.00%.
- Evidence facts supplied: 2; triggered review conditions: 0.

## Sources, dates, and data limitations

| Source | Provider | Value time | Retrieved | Freshness | Limitations |
| --- | --- | --- | --- | --- | --- |
| synthetic-fund-facts | SteadyFolio Synthetic Research Provider | 2026-01-15 | 2026-01-31T18:05:00+00:00 | fresh | The facts do not describe a real fund. |
| synthetic-total-return-history | SteadyFolio Synthetic Research Provider | 2026-01-31 | 2026-01-31T18:08:00+00:00 | fresh | Five observations are insufficient for investment forecasting. |

- This is a synthetic demonstration fact.
- The facts do not describe a real fund.
- A single price move does not test the long-term rationale.
- Five observations are insufficient for investment forecasting.

## Assumptions

- The active thesis and approved target remain unchanged unless separately approved.

## Specialist interpretations

### thesis-fit

Conclusion: `retain`

The deterministic thesis review proposes retain; price movement alone is not treated as thesis failure.

Evidence references:

- thesis-review:thesis-global:2026-01-31
- synthetic-fund-facts
- synthetic-total-return-history

Lens limitations:

- This is a synthetic demonstration fact.
- The facts do not describe a real fund.
- A single price move does not test the long-term rationale.
- Five observations are insufficient for investment forecasting.

### evidence-quality

Conclusion: `usable_with_limits`

The dated evidence can inform review within its explicit limitations.

Evidence references:

- evidence-fund-structure
- evidence-price-decline

Lens limitations:

- This is a synthetic demonstration fact.
- The facts do not describe a real fund.
- A single price move does not test the long-term rationale.
- Five observations are insufficient for investment forecasting.

## Meaningful disagreements

- None.

## Final synthesis and proposed next action

The bounded review supports the deterministic retain proposal, subject to source dates and limitations.

- Retain the current thesis pending its next review; no portfolio mutation is proposed.

User approval required: no.
- No approval-gated mutation is proposed.
Mutation performed: no.

## Execution trace

- Deterministic tools: `ResearchProvider.fetch`, `review_investment_thesis`.
- Review lenses: `thesis-fit`, `evidence-quality`.
- Provider calls: 1.
- Live external calls: 0.
- Critic passes: 0.
- Revisions: 0.
- Execution mode: deterministic engine with sequential review lenses; no independent agents.
- Review lenses are sequential interpretations, not independent agents or verification.

---

# Synthetic Committee Demo: demo-overlap

Request: Review overlapping funds with incomplete holdings coverage.
Route: `overlap_review`
Status: `limited`
As of: 2026-01-31

## Facts and deterministic calculations

- Portfolio value is 1000.00 EUR on 2026-01-31.
- Weighted annual fee rate is 0.19%.
- instrument-global: current 80.00%, approved target 50.00%, signed drift 30.00%.
- instrument-bond: current 20.00%, approved target 50.00%, signed drift -30.00%.
- Observed overlap between instrument-global and instrument-bond is 5.00%; holdings coverage is 23.00% and 10.00%.

## Sources, dates, and data limitations

| Source | Provider | Value time | Retrieved | Freshness | Limitations |
| --- | --- | --- | --- | --- | --- |
| synthetic-classified-exposures | SteadyFolio Synthetic Research Provider | 2025-12-31 | 2026-01-31T18:07:00+00:00 | stale | Unclassified fund weight is intentionally retained as unknown. |
| synthetic-fund-facts | SteadyFolio Synthetic Research Provider | 2026-01-15 | 2026-01-31T18:05:00+00:00 | fresh | The facts do not describe a real fund. |
| synthetic-fund-holdings | SteadyFolio Synthetic Research Provider | 2025-12-31 | 2026-01-31T18:06:00+00:00 | stale | Only selected holdings are supplied; coverage is intentionally incomplete. |
| synthetic-prices-2026-01-31 | Synthetic Fixture Provider | 2026-01-31T16:30:00+00:00 | 2026-01-31T18:00:00+00:00 | fresh | None |
| synthetic-total-return-history | SteadyFolio Synthetic Research Provider | 2026-01-31 | 2026-01-31T18:08:00+00:00 | fresh | Five observations are insufficient for investment forecasting. |

- Research source synthetic-classified-exposures is stale at 31 days old.
- Research source synthetic-fund-holdings is stale at 31 days old.
- Company concentration is partial; unclassified portfolio weight is not zero exposure.
- Sector exposure is partial; unclassified weight remains.
- Geography exposure is partial; unclassified weight remains.
- Currency exposure is partial; unclassified weight remains.

## Assumptions

- Only supplied holdings contribute to observed overlap.

## Specialist interpretations

### allocation-diversification

Conclusion: `partial_overlap`

Observed overlap describes supplied holdings only; uncovered holdings could increase or decrease the complete-fund overlap.

Evidence references:

- intelligence:synthetic-investor:2026-01-31
- synthetic-classified-exposures
- synthetic-fund-facts
- synthetic-fund-holdings
- synthetic-total-return-history

Lens limitations:

- Research source synthetic-classified-exposures is stale at 31 days old.
- Research source synthetic-fund-holdings is stale at 31 days old.
- Company concentration is partial; unclassified portfolio weight is not zero exposure.
- Sector exposure is partial; unclassified weight remains.
- Geography exposure is partial; unclassified weight remains.
- Currency exposure is partial; unclassified weight remains.

### evidence-quality

Conclusion: `refresh`

Refresh complete, same-date holdings before making a complete overlap claim.

Evidence references:

- synthetic-classified-exposures
- synthetic-fund-facts
- synthetic-fund-holdings
- synthetic-total-return-history

Lens limitations:

- Missing holdings are not treated as zero.

### committee-critic

Conclusion: `reject_complete_overlap_claim`

The observed overlap must not be presented as complete while either holdings coverage value is below 100%.

Evidence references:

- intelligence:synthetic-investor:2026-01-31

Lens limitations:

- The critic adds no new holdings data.

## Meaningful disagreements

- None.

## Final synthesis and proposed next action

The observed overlap is useful as a covered-slice measurement, not as a complete-fund overlap estimate.

- Obtain complete, compatible, same-date holdings before a complete overlap conclusion.

User approval required: no.
- No approval-gated mutation is proposed.
Mutation performed: no.

## Execution trace

- Deterministic tools: `analyze_portfolio`, `ResearchProvider.fetch`, `analyze_portfolio_intelligence`.
- Review lenses: `allocation-diversification`, `evidence-quality`, `committee-critic`.
- Provider calls: 1.
- Live external calls: 0.
- Critic passes: 1.
- Revisions: 1.
- Execution mode: deterministic engine with sequential review lenses; no independent agents.
- Review lenses are sequential interpretations, not independent agents or verification.

---

# Synthetic Committee Demo: demo-incomplete-drift

Request: I have EUR 400 to invest this month; show any drift that cannot be corrected.
Route: `contribution`
Status: `complete`
As of: 2026-01-31

## Facts and deterministic calculations

- Portfolio value is 1000.00 EUR on 2026-01-31.
- Weighted annual fee rate is 0.19%.
- instrument-global: current 80.00%, approved target 50.00%, signed drift 30.00%.
- instrument-bond: current 20.00%, approved target 50.00%, signed drift -30.00%.
- Proposed purchases total 398.60 EUR.
- Estimated costs total 1.40 EUR.
- Residual cash is 0.00 EUR.
- Proposed buy for instrument-bond: quantity 7.972, value 398.60 EUR, remaining drift -7.20%.

## Sources, dates, and data limitations

| Source | Provider | Value time | Retrieved | Freshness | Limitations |
| --- | --- | --- | --- | --- | --- |
| synthetic-prices-2026-01-31 | Synthetic Fixture Provider | 2026-01-31T16:30:00+00:00 | 2026-01-31T18:00:00+00:00 | fresh | None |

- No additional limitations reported.

## Assumptions

- The approved target remains policy and the method is drift_aware.
- Prices, FX, fees, and trading constraints are supplied inputs, not forecasts.

## Specialist interpretations

No specialist lens was needed for this routine deterministic request.

## Meaningful disagreements

- None.

## Final synthesis and proposed next action

The buy-only plan uses the available contribution without selling or mutating portfolio state. Any remaining drift stays visible.

- Review the proposal and its source dates.
- Approve separately before placing or recording any real transaction.

User approval required: yes.
- Executing or recording a real transaction requires explicit user approval.
Mutation performed: no.

## Execution trace

- Deterministic tools: `analyze_portfolio`, `plan_contribution`.
- Review lenses: None.
- Provider calls: 0.
- Live external calls: 0.
- Critic passes: 0.
- Revisions: 0.
- Execution mode: deterministic engine with sequential review lenses; no independent agents.
- Review lenses are sequential interpretations, not independent agents or verification.

---

# Synthetic Committee Demo: demo-stale-missing

Request: Review my portfolio with missing and stale research and show specialist disagreements.
Route: `portfolio_review`
Status: `insufficient_evidence`
As of: 2026-03-31

## Facts and deterministic calculations

- Portfolio value is 1000.00 EUR on 2026-03-31.
- Weighted annual fee rate is 0.19%.
- instrument-global: current 80.00%, approved target 50.00%, signed drift 30.00%.
- instrument-bond: current 20.00%, approved target 50.00%, signed drift -30.00%.
- Observed company look-through covers 0.00% of portfolio weight.
- Unclassified company look-through is 100.00%.

## Sources, dates, and data limitations

| Source | Provider | Value time | Retrieved | Freshness | Limitations |
| --- | --- | --- | --- | --- | --- |
| synthetic-fund-facts | SteadyFolio Synthetic Research Provider | 2026-01-15 | 2026-01-31T18:05:00+00:00 | stale | The facts do not describe a real fund. |
| synthetic-prices-2026-01-31 | Synthetic Fixture Provider | 2026-01-31T16:30:00+00:00 | 2026-01-31T18:00:00+00:00 | stale | The market source is 59 days old at review time. |

- Sector exposure is unavailable; missing data was not treated as zero.
- Geography exposure is unavailable; missing data was not treated as zero.
- Currency exposure is unavailable; missing data was not treated as zero.
- Historical data is unavailable for instrument-global.
- Historical data is unavailable for instrument-bond.
- Research source synthetic-fund-facts is stale at 75 days old.
- Company concentration is partial; unclassified portfolio weight is not zero exposure.

## Assumptions

- The approved target is the policy baseline.
- Missing research is unknown and is never treated as zero exposure.

## Specialist interpretations

### allocation-diversification

Conclusion: `act_within_approved_policy`

The largest signed drift is instrument-global at 30.00%; policy-preserving new contributions can reduce drift without selling.

Evidence references:

- analysis:synthetic-investor:2026-03-31

Lens limitations:

- This lens does not authorize a target change or transaction.

### risk-cost-evidence

Conclusion: `wait_for_data`

Research is stale and major look-through or historical evidence is missing; do not infer a target or thesis change from the gaps.

Evidence references:

- intelligence:synthetic-investor:2026-03-31
- synthetic-fund-facts

Lens limitations:

- Sector exposure is unavailable; missing data was not treated as zero.
- Geography exposure is unavailable; missing data was not treated as zero.
- Currency exposure is unavailable; missing data was not treated as zero.
- Historical data is unavailable for instrument-global.
- Historical data is unavailable for instrument-bond.
- Research source synthetic-fund-facts is stale at 75 days old.
- Company concentration is partial; unclassified portfolio weight is not zero exposure.

### committee-critic

Conclusion: `preserve_boundary`

Keep the policy-preserving drift fact separate from the evidence-dependent conclusion; do not turn missing evidence into a target change.

Evidence references:

- analysis:synthetic-investor:2026-03-31
- intelligence:synthetic-investor:2026-03-31
- synthetic-fund-facts

Lens limitations:

- The critic adds no new source evidence.

## Meaningful disagreements

- The allocation lens supports policy-preserving drift correction, while the evidence lens limits or defers evidence-dependent conclusions.

## Final synthesis and proposed next action

Use deterministic drift only within the approved policy; refresh missing or stale evidence before changing a target or thesis.

- Refresh missing or stale sources when the conclusion depends on them.
- Request explicit approval before persisting a target or policy change.

User approval required: no.
- A future target or policy change would require explicit user approval.
Mutation performed: no.

## Execution trace

- Deterministic tools: `analyze_portfolio`, `ResearchProvider.fetch`, `analyze_portfolio_intelligence`.
- Review lenses: `allocation-diversification`, `risk-cost-evidence`, `committee-critic`.
- Provider calls: 1.
- Live external calls: 0.
- Critic passes: 1.
- Revisions: 1.
- Execution mode: deterministic engine with sequential review lenses; no independent agents.
- Review lenses are sequential interpretations, not independent agents or verification.
