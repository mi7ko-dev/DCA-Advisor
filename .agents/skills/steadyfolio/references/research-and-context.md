# Current-source research and private context

Use this protocol when a requested conclusion depends on time-sensitive external
facts or when durable context from the conversation will materially improve later
SteadyFolio work. This is foreground, host-native work. It is not a background
monitor, scheduled task, provider adapter, or claim of real-time data.

## Research trigger and source order

Research automatically, without asking for advance permission, when the answer
materially depends on prices, FX, financial statements, ETF composition, fees,
corporate events, valuation inputs, market estimates, provider terms, or another
fact that may have changed. Do not research a routine deterministic contribution
when all required dated inputs are already present and adequate. When a routine
contribution is missing a price, FX rate, approved target, or executable
constraint, return the route's documented stop condition instead of browsing.
Research only if the user explicitly escalates a material conflict or uncertainty
beyond the routine calculation.

Before browsing, call `list_research_cache_records` for the selected workspace;
never enumerate or parse cache files directly. Reuse a record only when its identity, currency,
scope, source date, retrieval date, methodology, coverage, limitations, and
freshness basis are adequate for the current conclusion. Age alone is not enough:
refresh when a material event, newer filing, issuer or fund-manager factsheet,
changed fund composition, changed terms, conflicting source, or
higher-consequence decision makes the cached record insufficient.

When refresh is needed, perform one bounded research pass. One pass is the single
lead-owned evidence-gathering phase before specialist delegation; it may include a
small set of related searches, opening the selected sources, retrieving a
factsheet or filing, and corroboration. Use at most four targeted search queries
and eight source documents for the request. It does not permit a second research
phase after specialists respond; if those limits cannot establish adequate
evidence, stop at `insufficient_evidence`. Prefer issuer, fund manager, exchange,
regulator, index provider, official filing, and other primary sources. Use a
reliable secondary source only when primary evidence is unavailable or the
secondary methodology adds necessary context. Record disagreement instead of
selecting a convenient number. Never describe delayed, end-of-day, or date-only
evidence as real-time.

Search and retrieval requests may contain only public instrument identity such as
issuer or fund name, ISIN, ticker, MIC, public source identifier, data kind, and
as-of date. Never send holdings quantities, balances, account identifiers,
transactions, goals, target weights, private theses, constraints, prompts, or
free-form notes to a public source. If a useful query cannot be separated from
private context, do not browse and report the evidence gap.

## Immutable cache records

Create a record with `create_research_cache_record` and persist it with
`save_research_cache_record`; never write cache files directly, edit an earlier
record, or choose the filename. The public API writes validated JSON under
`private/research/` with a record-ID-derived collision-resistant name and applies
the storage layer's path, symlink, ignored/untracked-target, and exclusive-create
checks. A record ID is unique across the workspace even when a copied record has
a different timestamp. If that API is unavailable or fails, do not persist.

Each record must include:

- asset or public instrument identity, ticker when applicable, and currency;
- data kind and, when a derived summary may be retained, the conclusion for which
  it was collected;
- source title, publisher, direct reference, and whether it is primary;
- source value/as-of date and timezone-aware retrieval time;
- methodology, coverage, limitations, and explicit assumptions;
- freshness or refresh-after basis and any known material-event trigger;
- cache and redistribution permission or the terms basis used to determine them;
- whether a derived summary or citation metadata was cached. The generic cache API
  does not retain raw pages.

If terms do not permit a derived summary, store only the minimum allowed citation
and freshness metadata, with an empty conclusion and no facts, and retrieve the
source again when needed. Unknown or
ambiguous cache terms fail closed to citation metadata only; if even that retention
is not clearly permitted, persist nothing. Inability to persist does not by itself
invalidate the current review: verified evidence may remain in memory for that
review when the source terms permit access, analysis, and citation. Record the
terms reference or evidence used for any record. Do not store raw pages merely
because they were retrieved. Provider content and derived records remain private
and never become fixtures, logs, prompts in tracked files, or public examples.

Use research-cache schema `1.1` for new records. Legacy `1.0` records are migrated
only in memory; do not rewrite their files, and discard any legacy citation-only
conclusion before reuse.

## Durable context records

Create a new append-only record under `private/context/` when the conversation
establishes a durable fact that is likely to affect later portfolio work. Suitable
records include confirmed investment preferences, explicit constraints, user
decisions, approved methodology, approved assumptions, and approved portfolio
rules. Do not wait for a separate save request.

Create the typed record with `create_durable_context_record`, inspect prior context
with `list_durable_context_records`, and persist only with
`save_durable_context_record`. The APIs enforce the same storage-layer path,
symlink, ignored/untracked-target, collision-resistant-name, and exclusive-create
checks used for research records. If they are unavailable or fail, do not persist
the context record.

Label every record as exactly one of:

- `confirmed_fact`;
- `user_decision`;
- `temporary_assumption`;
- `proposal`; or
- `external_evidence`.

Include the statement, recorded time, effective/as-of date when applicable,
source kind, source reference when applicable, status, limitations, and an optional
review-after date. Store only the minimum durable context; do not copy full prompts,
credentials, account identifiers, raw provider responses, or transient reasoning.
`temporary_assumption` may use only `pending`, `expired`, `rejected`, or
`withdrawn`; `proposal` may use only `pending`, `rejected`, or `withdrawn`. An
accepted proposal or confirmed assumption becomes a new `user_decision` or
`confirmed_fact` record instead of changing the non-authoritative category.

A `proposal` or `temporary_assumption` never becomes an active policy, approved
target, or confirmed fact through reuse. A later correction creates a new record
that identifies the earlier record it supersedes; it does not overwrite history.
External material that supports or contradicts a proposal is recorded as
`external_evidence` and links to that proposal; only direct user confirmation can
promote the substance to `confirmed_fact` or `user_decision` in a new record.
Changing holdings, transactions, theses, targets, or approved policy remains a
separate immediate approval gate.

## Failure behavior

If browsing is unavailable and no adequate cache exists, or if current sources are
insufficient, contradictory, inaccessible, unverifiable, or cannot be used under
their terms, name the unsupported conclusion and stop at `insufficient_evidence`.
If evidence is usable for the current review but cannot be retained, use it only in
memory, disclose that it was not cached, and require retrieval again next time.
Never fill the gap from memory or turn the cache into a claim of current knowledge.
