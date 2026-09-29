# Equity Review and Portfolio Policy

## Boundary

Phase 7 adds an offline, deterministic individual-equity review and an explicit
portfolio-policy evaluator. Neither component retrieves live data, connects to a
broker, computes tax, changes approved targets, or places or records transactions.

Real evidence, policy thresholds, exemptions, classifications, and generated
reviews belong below the selected workspace's ignored `private/` directory. The
tracked examples are fully synthetic.

## Phase 8 agent envelope

The deterministic equity calculation remains `EquityReviewResult` version `1.0`.
Phase 8 does not redefine that contract. Instead, CommitteeResult version `2.0`
wraps the deterministic result with a version `1.0` multi-agent trace.

`prepare_multi_agent_equity_review` invokes `review_equity` exactly once and builds
immutable role-minimal packets for:

- evidence identity, sources, dates, freshness, and coverage;
- business quality, hard screen, criteria, and owner earnings;
- valuation method, conflicts, and margin of safety; and
- supplied typed aggregate portfolio weights, limits, counts, and overlap facts.

The Codex host starts one isolated thread per specialist and one later critic
thread. Each returns schema `1.0` agent-output JSON with claims and evidence
references. The lead attaches runtime, attempt, isolation, and opaque execution and
result IDs from the actual host spawn; models cannot self-attest them. Unknown
references, extra fields, malformed output, role drift, non-isolated metadata, or
additional attempts are rejected. The critic receives only deterministic facts,
validated claims, and generic execution status, never raw responses.

The lead does not vote. Deterministic calculations override agent interpretation,
and a deterministic `insufficient_evidence` result stays insufficient even if all
agents agree. Business-quality and valuation disagreement remains visible. A
missing runtime returns `deterministic_only`; a partial failure returns
`partial_agent_failure`. Neither is presented as a complete multi-agent review.

Production runtime is `codex_native_subagents`. The network-free
`in_memory_test_backend` exists only for synthetic tests and demonstrations. A real
Codex run sends each minimal packet to the Codex model service, adds token use and
latency, and requires no API key or third-party Python dependency in SteadyFolio.

## Instrument identity

`review_equity` validates the portfolio state before using evidence. It requires a
stock instrument with a recorded ISIN and rejects a reported ISIN or normalized
name that differs from the portfolio record. When listing evidence is present, the
listing ID, MIC, ticker, and trading currency must appear together and match the
recorded listing.

Portfolio validation also rejects the same non-null ISIN assigned to more than one
economic instrument. Separate listings remain attached to one instrument and do
not create duplicate exposure.

Identity is not a tax conclusion. ISIN, domicile, listing, execution venue, and
jurisdiction remain separate facts. Tax and regulatory interpretation still
requires a separately approved, current jurisdiction adapter.

## Evidence contract

`EquityReviewInput` schema version `1.0` contains:

- a review date and strict instrument/listing identity evidence;
- a circle-of-competence declaration;
- sourced quality observations;
- zero or more supported valuation anchors; and
- source provenance, retrieval time, freshness, methodology, limitations, and
  redistribution metadata.

All persisted decimals are canonical strings and calculations use `Decimal`.
Evidence cannot be newer than its source or the review date. Unknown sources,
duplicate methods, mixed valuation currencies, unsupported methods, and
non-positive valuation values fail validation.

Sources are assessed against their declared freshness window. Stale evidence that
supports a quality or valuation decision makes the final conclusion insufficient
until refreshed; it is never silently presented as current.

## Quality model

The version `1.0` model uses eight disclosed criteria with 11 total possible
points. Current positive free cash flow is a hard screen. FCF and Debt/EBITDA are
required for classification. Unavailable criteria are excluded from the
denominator rather than scored as zero; three or more unavailable criteria make
the result incomplete.

Complete scores are classified using percentages of available points:

- `quality`: at least 72%;
- `mid_tier`: at least 55% and below 72%;
- `exit_zone`: below 55%.

The result always exposes points awarded, points available, percentage, criterion
count, per-criterion rationale, source IDs, and the calculation version. The model
is descriptive and evidence-limited; it is not a forecast.

Circle of competence remains separate from numeric quality. A declared external
dependency without an observable event makes the decision evidence insufficient.

## Valuation and owner earnings

Valuation does not change the quality score. Supported anchors are selected in
this order: DCF, reverse DCF, then forward P/E. Consensus price targets are not
accepted. Margin of safety is:

```text
(fair value - current price) / fair value
```

The status is `acceptable` at 20% or more, `limited` from zero to below 20%, and
`premium` below zero. Opposite directions from supported models produce
`conflicting`; the values are not averaged. Missing anchors produce `unavailable`.

When CapEx/revenue is at least 15%, optional owner-earnings evidence can distinguish
maintenance from growth investment. Reported earnings, depreciation and
amortization, and maintenance CapEx must use one reporting date; depreciation and
amortization and maintenance CapEx are non-negative outflows. The engine does not
infer maintenance CapEx, and an explicit funding red flag cannot produce an
`eligible_for_consideration` conclusion.

## Configurable portfolio policy

`PortfolioPolicy` version `1.0` keeps thresholds and classifications outside the
global engine. It supports:

- a maximum direct position weight with explicit instrument exemptions;
- a fragmentation threshold and maximum fragmented-position count;
- an explicit satellite instrument set and aggregate cap; and
- named factor groups with an optional prior reported weight and change alert.

The only supported denominator is currently `invested_positions`. The result
therefore warns that unmodelled cash is excluded. It must not be described as a net
liquidation value or complete account allocation. User-specific policy instances
belong under `private/`; only the schema and synthetic example are public. Before
evaluating policy thresholds, the engine validates the complete analysis and
requires its instrument coverage and base currency to match the current portfolio
state.

## Public examples

Regenerate the synthetic equity review and policy result with:

```powershell
python tools/generate_synthetic_equity.py
```

The generator reads `examples/equity-portfolio.example.json`,
`examples/equity-evidence.example.json`, `examples/portfolio.example.json`, and
`examples/portfolio-policy.example.json`. It writes only synthetic JSON and
Markdown outputs under `examples/`.
