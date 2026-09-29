# SteadyFolio Equity Review

Instrument: `synthetic-compute-company`
As of: 2026-01-31
Identity: `matched`
Hard screen: `passed`
Circle of competence: `inside`
Quality model: `equity_quality_v1`

## Quality score

| Criterion | Status | Points | Maximum | Observed | Rationale |
| --- | --- | ---: | ---: | --- | --- |
| free_cash_flow | scored | 2 | 2 | 100, 120, 140 | The supplied positive free-cash-flow series is non-decreasing. |
| debt_to_ebitda | scored | 2 | 2 | 1.5 | Debt/EBITDA is below 2x. |
| revenue_growth | scored | 1.5 | 1.5 | 0.12 | Revenue growth is at least 10%. |
| operating_margin | scored | 1.5 | 1.5 | 0.2 | Operating margin is at least 10%. |
| capex_to_revenue | scored | 1 | 1 | 0.1 | CapEx/revenue is below 15%. |
| institutional_ownership | scored | 1 | 1 | 0.6 | Institutional ownership is at least 50%. |
| benchmark_outperformance | scored | 1 | 1 | true | Synthetic five-year total return exceeded the benchmark. |
| moat_and_management | scored | 1 | 1 | true | Synthetic pricing-power and governance evidence is positive. |

Score: 100% (11 of 11 available points).
Completeness: 8 of 8 criteria.
Classification: `quality`.

## Valuation

Status: `acceptable`.
Selected method: `dcf`.
Current price: 100 EUR
Fair value: 125 EUR
Margin of safety: 20%.

## Owner earnings

Status: `not_required`.
CapEx/revenue is below the adjustment threshold.

## Sources

| Source | Provider | As of | Retrieved | Freshness |
| --- | --- | --- | --- | --- |
| synthetic-equity-source | SteadyFolio Synthetic Equity Provider | 2026-01-31 | 2026-01-31T18:00:00+00:00 | fresh |

## Limitations

- Synthetic evidence for deterministic examples only.

## Conclusion

Conclusion: `eligible_for_consideration`.
- The evidence supports further consideration, not trade execution.
- This review does not execute a transaction or change portfolio policy.
- Mutation performed: no.
