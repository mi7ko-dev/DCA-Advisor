# Bounded multi-agent review

Use this protocol automatically when a supported request is consequential,
uncertain, evidence-conflicted, or materially exposed to one-perspective bias. A
multi-agent review requires separately spawned Codex subagent threads. Same-thread
lenses and local Python functions are fallbacks, not agents.

## Trigger

Start a bounded multi-agent review when at least one condition is true:

- the request is an individual-equity review or valuation;
- it tests an investment thesis against current evidence;
- material sources or conclusions conflict;
- it could support a significant allocation or policy proposal; or
- independent evidence, risk, and portfolio-fit perspectives could expose a
  consequential omission or bias.

Do not start agents for a routine contribution, a direct deterministic calculation,
or a short dependent task that cannot be split into independent perspectives.
When a routine request reveals a material conflict or uncertainty, finish the safe
deterministic portion and escalate only the disputed conclusion.

## Lead protocol

1. Validate the route, private state, dated inputs, and deterministic engine output.
2. Complete the single lead-owned research pass, when needed, before spawning any
   specialist. Specialists do not browse independently.
3. Select the smallest useful set of at least two independent Codex subagent roles:
   - portfolio review: allocation/diversification, risk/cost, evidence quality;
   - ETF thesis: thesis fit, evidence quality, risk/cost;
   - fund overlap: diversification and evidence quality;
   - significant allocation proposal: allocation fit, downside risk, evidence;
   - individual equity: use the strict four-role equity protocol.
4. Give each role one clear question, the expected output, and an immutable
   role-minimal packet. Validate the packet against the route allowlist below and
   reject every unknown field before spawning.
5. Spawn each selected role once with no inherited conversation history
   (`fork_turns=none` or an equivalent packet-only context). If the host cannot
   guarantee that boundary, treat the runtime as unavailable and use the fallback.
   Tell the specialist not to browse, use tools, read files, recalculate values,
   add facts, authorize actions, persist output, or contact external systems.
6. Wait once for the specialists, preserve their meaningful disagreements, and
   send only deterministic facts plus validated specialist conclusions to one new
   isolated critic. The critic checks unsupported claims, contradictions, missing
   evidence, and overstatement; it does not add facts.
7. Perform one lead synthesis. Deterministic results and cited evidence govern.
   Agreement, voting, and confidence percentages are not proof.

Use one execution per selected specialist, one critic execution, one final
synthesis, and no retries or debate loop. The user's standing request authorizes
the bounded extra model use and latency for qualifying analyses; it does not
authorize broader data disclosure or any portfolio mutation.

## Generic packet allowlists

Every generic packet may contain only `route`, `review_date`, `role`, one explicit
question, deterministic fact strings, opaque public-instrument aliases, source
aliases with dates/freshness/coverage/limitations, assumptions, and the following
role-specific aggregates:

- allocation/diversification: normalized weights, drift, and approved aggregate
  limits;
- risk/cost: aggregate exposure, fee, constraint, downside, and coverage facts;
- evidence quality: public-source metadata and attributable public facts;
- thesis fit: normalized approved thesis claims and triggers needed for the review,
  without free-form rationale, goals, or personal notes.

Packets must not contain credentials, account or request identifiers, balances,
holding quantities, transaction history, goals, target amounts, raw target weights
or identifiers, full prompts, free-form notes, source paths, raw provider payloads,
or unrelated portfolio facts.
Use opaque aliases for user-owned identifiers. Any field outside the allowlist,
failed redaction, or packet-validation uncertainty requires fallback before spawn.
Generic packets and specialist/critic results remain memory-only by default;
persisting any review-derived artifact requires immediate explicit approval.
The standing authorization for append-only research-cache and classified context
records under `research-and-context.md` is separate and does not persist a packet,
specialist result, critic result, synthesis, or saved review.

## Equity specialization

For `equity_review`, follow
[multi-agent-equity-review.md](multi-agent-equity-review.md) in addition to this
protocol. Its packet schemas, four roles, validation, trace, and deterministic
fallback are mandatory and take precedence over the generic role guidance here.

## Fallback

If host-native subagents are unavailable, disclose that no true multi-agent run
occurred. Use `run_deterministic_equity_fallback` for equity review and the existing
sequential route lenses for other analyses. Report equity as
`deterministic_only` and non-equity same-thread review as
`single_thread_sequential`. Preserve all disagreements and evidence gaps; never
manufacture several voices in one thread, call it multi-agent, or call model
synthesis deterministic.
