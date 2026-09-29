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
when all required dated inputs are already present and adequate.

Before browsing, inspect compatible records under the selected workspace's ignored
`private/research/` directory. Reuse a record only when its identity, currency,
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

Create a new JSON or Markdown record under `private/research/`; never edit or
replace an earlier record. Use a timestamped, collision-resistant filename. Before
writing, apply the storage-layer path, symlink, ignored/untracked-target, and
exclusive-create checks. If those checks are unavailable or fail, do not persist.

Each record must include:

- asset or public instrument identity, ticker when applicable, and currency;
- data kind and the conclusion for which it was collected;
- source title, publisher, direct reference, and whether it is primary;
- source value/as-of date and timezone-aware retrieval time;
- methodology, coverage, limitations, and explicit assumptions;
- freshness or refresh-after basis and any known material-event trigger;
- cache and redistribution permission or the terms basis used to determine them;
- whether source content, a derived summary, or citation metadata was cached.

If terms do not permit caching, store only the minimum allowed citation and
freshness metadata and retrieve the source again when needed. Unknown or ambiguous
cache terms fail closed to citation metadata only; if even that retention is not
clearly permitted, persist nothing. Record the terms reference or evidence used for
the decision. Do not store raw pages merely because they were retrieved. Provider
content and derived records remain private and never become fixtures, logs, prompts
in tracked files, or public examples.

## Durable context records

Create a new append-only record under `private/context/` when the conversation
establishes a durable fact that is likely to affect later portfolio work. Suitable
records include confirmed investment preferences, explicit constraints, user
decisions, approved methodology, approved assumptions, and approved portfolio
rules. Do not wait for a separate save request.

Apply the same storage-layer path, symlink, ignored/untracked-target,
collision-resistant-name, and exclusive-create checks used for research records.
If they are unavailable or fail, do not persist the context record.

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
insufficient, contradictory, inaccessible, or cannot be cached safely, name the
unsupported conclusion and stop at `insufficient_evidence`. Never fill the gap
from memory or turn the cache into a claim of current knowledge.
