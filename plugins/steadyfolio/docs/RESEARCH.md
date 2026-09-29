# Portfolio Intelligence and Research Contract

## Provider boundary

Phase 4 defines a replaceable `ResearchProvider` protocol. A request contains only
explicit public instrument IDs, listing IDs, evidence source IDs, and an as-of
date. Evidence source IDs are included only when supplied thesis evidence needs its
public provenance retained. The request does not contain holdings quantities,
balances, account identifiers, goals, theses, or personal context.

The implemented `StaticResearchProvider` reads structured synthetic snapshots for
offline examples and deterministic tests. No live provider or network integration
is implemented. Consequently there are no live provider integration tests.

Phase 9 adds a separate Codex host-native research layer. When a requested
conclusion materially depends on time-sensitive facts, the lead first inspects
compatible immutable records below `private/research/` and performs at most one
foreground web research pass when the cache is absent, stale, contradictory, or
inadequate. This does not implement or impersonate the Python `ResearchProvider`.
The lead prefers primary sources and converts only attributable dated facts into
validated engine inputs. Specialists never browse independently.

Every source record retains:

- provider and source reference;
- source as-of date and retrieval timestamp;
- freshness threshold and calculated freshness status;
- methodology and limitations;
- terms reference and explicit cache/redistribution permissions.

The public example uses only project-authored synthetic data whose caching and
redistribution are allowed. Host-native research records the source terms and
caches only what those terms permit. When content caching is not permitted, the
private record retains only the minimum allowed citation and freshness metadata.
A future live adapter must separately review and encode the actual provider terms
before caching or redistributing any response. Raw live responses must not become
public fixtures.

The offline provider first selects records referenced by the request, then enforces
the as-of boundary on those selected records. Unrelated future-dated records do not
invalidate an otherwise valid request, while any selected future-dated record is
rejected.

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

An overlap comparison requires both funds' supplied holdings to use the same as-of
date. Zero coverage is absence of overlap evidence, not observed zero overlap.

Observed portfolio company or issuer exposure is:

```text
ETF contribution = portfolio weight * supplied constituent weight
direct stock contribution = portfolio weight
```

Contributions with the same company or issuer ID are aggregated across direct and
look-through holdings before ranking. The result reports covered and unclassified
portfolio weight. Company concentration is therefore a lower-bound observation
over supplied coverage, not a complete look-through result.

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
second implicit historical FX conversion. Current research snapshots use schema
`1.1`, which requires at least three levels so volatility is based on at least two
returns rather than reporting a misleading zero from one return.

Legacy schema `1.0` remains readable with its original two-observation minimum. A
legacy series containing only two levels is retained as sourced evidence, but no
historical volatility metric is emitted from its single return; the intelligence
result records an explicit limitation. Unknown schema versions are rejected.

Simple periodic return is `current / previous - 1`. Cumulative return is
`last / first - 1`. Annualized volatility is sample standard deviation multiplied
by the square root of 252, 52, or 12 for daily, weekly, or monthly data. Maximum
drawdown is the largest percentage decline from a prior index peak. Correlation is
Pearson correlation over aligned periodic returns; it is omitted when either
series has zero variance or too few returns.

Benchmark comparison requires the same compatibility rules and reports simple
cumulative-return difference over the shared period. Stress analysis uses supplied
observations inside an explicit date window and reports the actual covered dates.
Stress-window IDs are stable public identifiers and must be unique. These metrics
describe historical inputs and are not predictions.

## Thesis review

Only an active holding thesis can be reviewed. It can record its role, rationale,
approved target reference, target range, benchmark, risks, configured review
triggers, last review, and next review. The approved target allocation remains
authoritative; a thesis target must match it.

Review output separates attributable evidence facts from deterministic
interpretation. Configured trigger hits or non-price contradictory evidence propose
`review`; missing evidence proposes `investigate`; otherwise the proposal is
`retain`. A price change alone is not treated as thesis failure.

Evidence kinds are a closed vocabulary: `benchmark_change`, `cost_change`,
`fund_structure`, `fundamental_change`, `price_change`, and `risk_event`. Unknown
kinds are rejected for both parsed and directly constructed evidence.

All actions are proposals for user review. The review function does not mutate the
thesis, holdings, transactions, or approved policy.

## Privacy and known limitations

Real provider responses, query history, caches, analysis results, thesis reviews,
and reports belong under ignored `private/`. New host-research records are
append-only and retain public instrument identity, currency, data kind, source and
retrieval dates, methodology, coverage, limitations, freshness basis, assumptions,
and cache permissions. A compatible record is reused only when it remains adequate
for the current conclusion; material events and higher-consequence decisions can
require an earlier refresh. Public examples are synthetic and may be regenerated
with `tools/generate_synthetic_intelligence.py`.

The deterministic package still does not implement live providers, real-time
feeds, tax or regulatory advice, look-through beyond supplied records, factor
models, forecasts, optimization, corporate-action processing, or automatic policy
changes. Phase 9 host research is bounded foreground evidence gathering, not a
background monitor or promise of real-time data. Tax and regulatory questions
remain unresolved unless a later authorized operation uses current
jurisdiction-specific primary sources.
