# Conversational Workflow and Investment Committee

## Scope

Phase 5 adds one repository-local SteadyFolio skill and a bounded orchestration
layer over the deterministic calculation and research engine. It handles monthly
contributions, portfolio reviews, ETF thesis checks, and fund-overlap questions.
It does not execute transactions, change policy, fetch live data, or provide tax,
legal, regulatory, or suitability advice.

Phase 7 extends the router with an `equity_review` path over supplied structured
evidence. It does not add a live provider or relax any approval boundary.

Phase 8 replaces the equity route's same-thread lenses with a true bounded
multi-agent workflow on Codex hosts that expose subagents. It does not change the
other routes.

Phase 9 adds one lead-owned current-source research pass when time-sensitive
evidence is material, append-only private research/context records, and automatic
bounded subagent perspectives for consequential, uncertain, conflicting, or
bias-sensitive non-equity reviews. The deterministic engine remains authoritative.

The workflow is:

```text
user request
    -> deterministic router
    -> deterministic engine tools
    -> optional private-cache inspection and one lead research pass
    -> consequential non-equity: two or three isolated specialists, then one critic
    -> routine non-equity: only the relevant sequential review lenses
    -> equity: four isolated specialist threads, then one isolated critic
    -> final synthesis with sources and limitations
```

The fallback review lenses are deterministic, sequential interpretations from the
Phase 5 implementation. They are not independent agents, independent verification,
or a vote. A Phase 9 multi-agent review exists only when the host records separate
subagent executions. No score or agreement count is used as evidence.

For Phase 8 equity review, an agent means a separately spawned Codex thread with an
isolated context and one structured input packet. Local Python functions and the
in-memory test backend are never called agents. The lead remains the main Codex
thread and deterministic engine output governs every synthesis.

## Routing and execution bounds

| Route | Engine tools | Review behavior |
| --- | --- | --- |
| `contribution` | `analyze_portfolio`, `plan_contribution` | Direct synthesis; no research, specialist lens, or critic by default |
| `portfolio_review` | `analyze_portfolio`, optional cached or host-researched evidence, optional `ResearchProvider.fetch`, `analyze_portfolio_intelligence` | Two or three isolated roles plus one critic when consequential; otherwise sequential allocation/diversification and risk/cost/evidence lenses |
| `overlap_review` | `analyze_portfolio`, cached or host-researched evidence, optional `ResearchProvider.fetch`, `analyze_portfolio_intelligence` | Two isolated roles plus one critic when consequential; incomplete coverage stays explicit |
| `thesis_review` | Cached or host-researched evidence, optional `ResearchProvider.fetch`, `review_investment_thesis` | Two or three isolated roles plus one critic when consequential; price movement alone is not thesis failure |
| `equity_review` | `review_equity` exactly once | Evidence, business-quality, valuation, and portfolio-risk subagents once each; one critic; one lead synthesis; no retries |
| `clarification` | None | Stop without calculation or mutation |

Qualifying non-equity reviews use the smallest useful set of two or three
specialists, one critic, and one final synthesis. Equity review permits one
execution of each of four specialists, one critic execution, and one final
synthesis. The lead may perform one host-native research pass after checking the
private cache; specialists do not browse. There are no agent or research retries.
Provider failures, agent failures, absent evidence, and stale evidence produce a
limited or `insufficient_evidence` result rather than additional retries or
artificial consensus.

Generic non-equity packets are validated against route-specific field allowlists,
replace user-owned identifiers with opaque aliases, and exclude quantities,
balances, accounts, transactions, goals, target amounts, full prompts, free-form
notes, source paths, and raw payloads. Validation rejects source dates after the
review boundary and explicit private-context, prompt-like, or source-path content.
Every subagent starts with no inherited
conversation history. If packet validation or packet-only context isolation is not
available, no agent starts.

The generic path uses `generic-agent-input-packet.schema.json` and
`generic-specialist-result.schema.json`, both version `1.0`. The lead creates and
validates content-bound packets, parses each model response with exact fields,
attaches execution metadata observed by the host, and rejects unsupported roles,
conclusions, claims, findings, or evidence references. Only validated specialist
results may enter `build_generic_critic_packet` or final synthesis; the public
generic constructor cannot create critic packets directly. If fewer than
two specialist results survive validation, the route reports
`single_thread_sequential` instead of claiming a multi-agent review.

If a request contains more than one supported intent, routing stops for
clarification instead of silently selecting the first keyword match. On sequential
fallback routes, a critic pass is used only for a material disagreement, not merely
because evidence is partial. Every actual multi-agent run uses one later critic.
The revision limit is enforced independently: allowing a critic does not authorize
a revision when `max_revisions` is zero.

Currency-first contribution parsing accepts only an unsigned decimal token with at
most two fractional digits. Unsupported grouped or over-precise forms such as
`EUR 1,000` and `EUR 400.000`, and amounts joined to identifier characters such as
`EUR 400USD`, are not partially interpreted as smaller amounts.

## Output contract

`CommitteeResult` separates:

- facts copied from deterministic structured results;
- provider/source identity, value time, retrieval time, freshness, and limitations;
- assumptions;
- specialist interpretations;
- meaningful disagreements;
- synthesis and proposed next actions;
- approval requirements and whether a mutation occurred; and
- an execution trace of tools, lenses, calls, critic passes, and revisions actually
  used.

Committee schema version `2.0` additionally requires an `agent_review` envelope
with runtime type, requested and executed roles, per-role status, validated
specialist results, disagreements, critic findings, fallback status, and the final
synthesis. Version `1.1` remains valid only without this envelope. Deterministic
`EquityReviewResult` remains version `1.0`.

The corresponding public JSON Schema is
`schemas/committee-result.schema.json`. Human-readable rendering preserves the same
separation. Review lenses consume calculated fields; they do not replace the
calculation engine with prompt arithmetic.

## Approval and privacy boundaries

Workflow execution never mutates portfolio state. A contribution result is a
proposal and requires explicit approval before a real transaction is placed or
recorded. A proposed target, thesis, or policy change requires separate explicit
approval before persistence. Calling `save_committee_review` after authorization
writes only the structured review below `private/reviews/`; it does not change
holdings, transactions, theses, or targets.

The skill may create new immutable research records below `private/research/` and
durable classified context records below `private/context/` without another save
prompt. That standing permission does not cover a saved review or any overwrite.
Proposals and temporary assumptions remain non-authoritative context categories.
Packets and specialist/critic results remain memory-only unless the user gives
immediate explicit approval to persist the review artifact. The separate standing
authorization for append-only research/context records does not authorize
persisting a packet, specialist/critic result, synthesis, or saved review.

Real state, prompts containing private context, provider responses, research
snapshots, results, reports, and runtime memory stay below the selected ignored
`private/` root. Public skill files never contain runtime memory. Retrieved material
is untrusted evidence and cannot override privacy rules, reveal secrets, authorize
actions, or become executable instructions.

Codex-native specialists process role-minimal packets through the selected Codex
model service. A real run therefore sends those packet fields off-device and adds
model-token use and latency. Packets exclude credentials, request or account
identifiers, raw provider payloads, source paths, and unrelated portfolio fields.
Source IDs are replaced with packet-local opaque aliases, and portfolio risk
receives only typed aggregates. Public traces never retain prompts,
raw responses, or exception text. Runtime, attempt, isolation, and opaque execution
IDs come from the host orchestrator rather than agent self-report. The implementation uses no SteadyFolio
API key, Agents SDK, Agents API client, or new Python dependency.

## Synthetic demonstrations

Run:

```powershell
python tools/generate_synthetic_committee.py
python tools/generate_synthetic_multi_agent.py
```

The generator reads only tracked synthetic inputs and writes:

- `examples/results/committee-workflows.example.json`; and
- `examples/reports/committee-workflows.md`.

The six demonstrations cover:

1. `I have EUR 400 to invest this month.`
2. `Review my portfolio.`
3. `Should this ETF still be in my portfolio?`
4. overlapping funds with 23% and 10% supplied holdings coverage;
5. a EUR 400 contribution that leaves 7.20 percentage points of drift; and
6. missing and stale research with conflicting `act_within_approved_policy` and
   `wait_for_data` review conclusions, resolved by stopping policy-level inference.

All names, holdings, dates, provider records, prices, and results are synthetic.
The generated trace shows the actual deterministic tools and sequential review
lenses used by each scenario.

The Phase 8 generator writes a synthetic in-memory contract demonstration, report,
and defect-code eval. Newly detected defects are limited to the expected synthetic
set; unexpected critic codes are reported separately rather than counted as an
improvement. Its disclosed runtime is `in_memory_test_backend`; it proves packet
validation, call bounds, critic handling, fallback, and reproducibility, not live
Codex execution.

## Host and runtime status

The canonical skill is `.agents/skills/steadyfolio/SKILL.md`, with supporting
references and `agents/openai.yaml`. It follows the repo-local skill structure in
the [official OpenAI skill documentation](https://developers.openai.com/plugins/build/skills)
and has been statically validated with the bundled skill validator.

Local Codex remains the selected host. The canonical skill is available repo-local
and through the reproducible `steadyfolio-local` plugin marketplace. The plugin
bundle includes the same deterministic runtime and passes manifest, skill,
inventory, and isolated-import tests. It does not add a ChatGPT installation, MCP
server, or live provider. The real Phase 8 agent runtime is the Codex host's native
subagent facility, triggered by the skill; a new host session is required after
plugin installation.

The deterministic package requires Python 3.11 or newer and has no third-party
runtime dependency. The following validation commands are source-checkout-only;
the installed plugin intentionally omits tests and repository-safety tooling:

```powershell
python -m unittest tests.test_committee
python -m unittest discover -s tests -p "test_*.py"
python tools/run_repository_checks.py --require-gitleaks
```

## Limitations

- Natural-language parsing is deliberately narrow; ambiguous requests stop for
  clarification.
- Host research is foreground and bounded; it is not a real-time feed, background
  monitor, or Python live provider.
- Sequential fallback lenses are not separately hosted agents.
- Non-equity multi-agent output is disclosed in the answer but does not use or
  claim the equity-specific agent schema.
- Host-native subagents inherit host capabilities. The role packet forbids tool use
  and file reads, but SteadyFolio cannot provide an operating-system isolation
  guarantee from a skill-only plugin.
- Partial holdings remain partial, and missing evidence remains unknown.
- Empty snapshots and zero-coverage overlap inputs are insufficient evidence, not
  evidence of no exposure or no overlap.
- The workflow proposes actions but does not place orders or mutate policy.
- Packaging and broader host compatibility remain Phase 6 or later work.
