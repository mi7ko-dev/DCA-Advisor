# Synthetic Portfolio Intelligence Report

Analysis date: 2026-01-31
Base currency: EUR

## Instrument facts

| Instrument | Type | Domicile | Distribution | Index | Replication | TER | Fund size | Facts as of |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- |
| Synthetic Global Equity ETF | etf | IE | accumulating | Synthetic Global Index | physical sampled | 0.20% | 1,250,000,000.00 EUR | 2026-01-15 |
| Synthetic Aggregate Bond ETF | etf | IE | accumulating | Synthetic Aggregate Bond Index | physical sampled | 0.15% | 620,000,000.00 EUR | 2026-01-15 |

## Observed holdings overlap

| Pair | Observed overlap | Left coverage | Right coverage | Holdings as of |
| --- | ---: | ---: | ---: | --- |
| Synthetic Global Equity ETF / Synthetic Aggregate Bond ETF | 5.00% | 23.00% | 10.00% | 2025-12-31 |

## Observed company or issuer concentration

Covered portfolio weight: 20.40%
Unclassified portfolio weight: 79.60%

| Entity | Observed portfolio weight |
| --- | ---: |
| Synthetic Alpha Company | 7.00% |
| Synthetic Beta Company | 5.20% |
| Synthetic Gamma Company | 4.00% |
| Synthetic Delta Company | 3.20% |
| Synthetic Epsilon Issuer | 1.00% |

## Classified exposures

### Sector

Coverage: 20.40%; unclassified: 79.60%

| Classification | Observed portfolio weight |
| --- | ---: |
| Technology | 8.00% |
| Health Care | 6.40% |
| Industrials | 4.00% |
| Corporate | 1.00% |
| Government | 1.00% |

### Geography

Coverage: 20.40%; unclassified: 79.60%

| Classification | Observed portfolio weight |
| --- | ---: |
| Europe | 8.40% |
| North America | 8.00% |
| Asia | 4.00% |

### Currency

Coverage: 20.40%; unclassified: 79.60%

| Classification | Observed portfolio weight |
| --- | ---: |
| USD | 12.00% |
| EUR | 8.40% |

## Historical metrics

| Instrument | Period | Total return | Annualized volatility | Maximum drawdown | Benchmark excess | Convention |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Synthetic Global Equity ETF | 2025-09-30 to 2026-01-31 | 20.00% | 36.73% | 10.00% | 2.00% | monthly total_return_index, distributions included, corporate actions included in synthetic index levels |
| Synthetic Aggregate Bond ETF | 2025-09-30 to 2026-01-31 | 4.00% | 4.85% | 0.98% | -14.00% | monthly total_return_index, distributions included, corporate actions included in synthetic index levels |

## Correlation

- Synthetic Global Equity ETF / Synthetic Aggregate Bond ETF: 0.7964 over 4 aligned returns.

## Stress windows

- Synthetic Autumn Drawdown — Synthetic Global Equity ETF: return -4.55%, maximum drawdown 10.00% (2025-10-31 to 2025-12-31).
- Synthetic Autumn Drawdown — Synthetic Aggregate Bond ETF: return 0.98%, maximum drawdown 0.98% (2025-10-31 to 2025-12-31).

## Source freshness and permissions

- `synthetic-classified-exposures`: SteadyFolio Synthetic Research Provider; as of 2025-12-31; retrieved 2026-01-31T18:07:00+00:00; stale (31 days); cache permitted=true; redistribution permitted=true; terms `project-generated-synthetic-data`.
- `synthetic-fund-facts`: SteadyFolio Synthetic Research Provider; as of 2026-01-15; retrieved 2026-01-31T18:05:00+00:00; fresh (16 days); cache permitted=true; redistribution permitted=true; terms `project-generated-synthetic-data`.
- `synthetic-fund-holdings`: SteadyFolio Synthetic Research Provider; as of 2025-12-31; retrieved 2026-01-31T18:06:00+00:00; stale (31 days); cache permitted=true; redistribution permitted=true; terms `project-generated-synthetic-data`.
- `synthetic-total-return-history`: SteadyFolio Synthetic Research Provider; as of 2026-01-31; retrieved 2026-01-31T18:08:00+00:00; fresh (0 days); cache permitted=true; redistribution permitted=true; terms `project-generated-synthetic-data`.

## Warnings and limitations

- Research source synthetic-classified-exposures is stale at 31 days old.
- Research source synthetic-fund-holdings is stale at 31 days old.
- Company concentration is partial; unclassified portfolio weight is not zero exposure.
- Sector exposure is partial; unclassified weight remains.
- Geography exposure is partial; unclassified weight remains.
- Currency exposure is partial; unclassified weight remains.
- Top-holdings data is partial and is not presented as complete look-through coverage.
- Historical metrics and stress windows describe synthetic past observations; they are not forecasts.
- No policy, holding, or transaction was changed by this analysis.
- This synthetic report is not financial advice.
