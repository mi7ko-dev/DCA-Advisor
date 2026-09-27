# Portfolio Intelligence and Research Contract

## Provider boundary

Phase 4 defines a replaceable `ResearchProvider` protocol. A request contains only
explicit public instrument IDs, listing IDs, and an as-of date. It does not contain
holdings quantities, balances, account identifiers, goals, theses, or personal
context.

The implemented `StaticResearchProvider` reads structured synthetic snapshots for
offline examples and deterministic tests. No live provider or network integration
is implemented. Consequently there are no live integration tests in Phase 4.

Every source record retains:

- provider and source reference;
- source as-of date and retrieval timestamp;
- freshness threshold and calculated freshness status;
- methodology and limitations;
- terms reference and explicit cache/redistribution permissions.

The public example uses only project-authored synthetic data whose caching and
redistribution are allowed. A future live adapter must review and encode the actual
provider terms before caching or redistributing any response. Raw live responses
must not become public fixtures.

## Fund facts and identity

Fund profiles can provide domicile, distribution policy, tracked index,
replication method, TER, fund size, fund-size currency, source date, and source ID.
Instrument identity, ISIN, economic currency, and exchange listings remain in the
portfolio model. Provider facts do not overwrite the approved portfolio record;
conflicting TER values produce an explicit warning.

## Holdings overlap and concentration

For two funds `A` and `B`, observed overlap is calculated only from constituents
present in both supplied snapshots:

```text
observed overlap = sum(min(weight[A, company], weight[B, company]))
```

Each fund's holdings coverage is the sum of its supplied constituent weights. The
algorithm does not scale top holdings to 100%, infer omitted constituents, or treat
missing holdings as zero exposure.

Observed portfolio company or issuer exposure is:

```text
ETF contribution = portfolio weight * supplied constituent weight
direct stock contribution = portfolio weight
```

The result reports covered and unclassified portfolio weight. Company
concentration is therefore a lower-bound observation over supplied coverage, not a
complete look-through result.

## Sector, geography, and currency exposure

Classified exposures use the same weighted aggregation:

```text
observed classification weight =
    sum(portfolio weight * supplied classification weight)
```

Every dimension reports coverage and unclassified weight. Currency exposure is
returned only when an explicit provider classification and methodology exist. It
is never inferred from a listing currency, ticker, domicile, or fund name.

## Historical metrics

The Phase 4 MVP accepts positive index levels with an explicit:

- currency;
- frequency (`daily`, `weekly`, or `monthly`);
- return convention (`price_index` or `total_return_index`);
- distribution treatment;
- corporate-action treatment;
- observation period, as-of date, and source.

Portfolio series used together must have identical observation dates, currency,
frequency, return convention, distribution treatment, and corporate-action
treatment. The MVP requires the portfolio base currency and does not perform a
second implicit historical FX conversion.

Simple periodic return is `current / previous - 1`. Cumulative return is
`last / first - 1`. Annualized volatility is sample standard deviation multiplied
by the square root of 252, 52, or 12 for daily, weekly, or monthly data. Maximum
drawdown is the largest percentage decline from a prior index peak. Correlation is
Pearson correlation over aligned periodic returns; it is omitted when either
series has zero variance or too few returns.

Benchmark comparison requires the same compatibility rules and reports simple
cumulative-return difference over the shared period. Stress analysis uses supplied
observations inside an explicit date window and reports the actual covered dates.
These metrics describe historical inputs and are not predictions.

## Thesis review

An active holding thesis can record its role, rationale, approved target reference,
target range, benchmark, risks, configured review triggers, last review, and next
review. The approved target allocation remains authoritative; a thesis target must
match it.

Review output separates attributable evidence facts from deterministic
interpretation. Configured trigger hits or non-price contradictory evidence propose
`review`; missing evidence proposes `investigate`; otherwise the proposal is
`retain`. A price change alone is not treated as thesis failure.

All actions are proposals for user review. The review function does not mutate the
thesis, holdings, transactions, or approved policy.

## Privacy and known limitations

Real provider responses, query history, caches, analysis results, thesis reviews,
and reports belong under ignored `private/`. Public examples are synthetic and may
be regenerated with `tools/generate_synthetic_intelligence.py`.

Phase 4 does not implement live providers, web research, tax or regulatory advice,
look-through beyond supplied records, factor models, forecasts, optimization,
corporate-action processing, or automatic policy changes. Tax and regulatory
questions remain unresolved unless a later authorized operation uses current
jurisdiction-specific primary sources.
