# Host-native multi-agent equity review

Use this strict specialization only for `equity_review`, after applying the common
trigger and lead rules in `multi-agent-review.md`. It relies on Codex host-native
subagents: separate agent threads with isolated contexts, coordinated by the main
Codex thread. It does not use the OpenAI Agents API or Agents SDK, does not require
an API key in SteadyFolio, and adds no Python runtime dependency.

## Data and cost disclosure

Each specialist packet is processed by the Codex model service. Real equity and
minimal portfolio facts therefore leave the local machine through the selected
Codex host, and four specialists plus one critic consume more tokens and add
latency compared with the deterministic-only path. Never send credentials,
account identifiers, transaction history, free-form private notes, raw provider
payloads, source paths, request IDs, or fields a role does not need. Source IDs are
replaced with packet-local opaque aliases, and portfolio risk receives only typed
aggregate weights, limits, and counts.

Keep real packets, validated results, and derived reports in memory by default.
New immutable research and context records follow the standing protocol in
`research-and-context.md`; persisting any review artifact still requires immediate
explicit approval and may then occur only below the active project's ignored
`private/` workspace. A research/context record is not permission to persist a
packet, specialist result, critic result, synthesis, or saved review. Public traces
contain role, status, execution ID, bounds,
runtime type, and generic limitations only. They never contain prompts or raw
model responses.

## LeadOrchestrator protocol

1. Confirm the route is exactly `equity_review`, the request and evidence dates
   match, and structured evidence is present. Other routes use the generic bounded
   multi-agent protocol rather than this equity packet contract.
2. Call `prepare_multi_agent_equity_review` once. It invokes deterministic
   `review_equity` exactly once and returns four immutable schema `1.1` packets:
   `evidence`, `business_quality`, `valuation`, and `portfolio_risk`.
3. Spawn one separate Codex subagent for each packet. Require a fresh packet-only
   context without inherited conversation history (`fork_turns=none` or an
   equivalent host guarantee); otherwise use deterministic fallback. Send
   only the packet and its included instructions. Tell the agent not to use tools,
   browse, read files, recalculate values, or add facts. Require exactly one JSON
   object matching `schemas/specialist-result.schema.json#/$defs/agentOutput`.
   The agent must not self-report a result ID, runtime, attempt count, execution
   ID, or isolation status.
4. Wait for all four once. Do not retry. Parse with
   `specialist_result_from_dict`, supplying the actual packet, runtime, host
   execution ID, and isolation flag from the spawn operation. The parser replaces
   the raw host ID with an opaque digest. Validate with
   `validate_specialist_result`. Record malformed, rejected, timed-out, or
   unavailable executions generically, without retaining raw output or exception
   text.
5. Call `build_critic_packet` with only the deterministic result, validated
   specialist claims, and generic execution statuses. Spawn exactly one new
   isolated `critic` subagent. It may identify unsupported claims,
   contradictions, missing evidence references, and overstatement. It may not add
   market facts.
6. Attach the critic's host-owned execution metadata, validate its output once,
   and call
   `finalize_multi_agent_equity_review` once with
   `runtime_type=codex_native_subagents`. Preserve disagreements and critic
   findings. Deterministic calculations and validation always govern.
7. Render the returned `CommitteeResult`. Do not vote, count agreement as proof,
   hide a disagreement, or strengthen the deterministic conclusion.

## Role boundaries

- `evidence`: identity, ISIN, listing, packet-local source aliases, dates,
  freshness, and coverage.
- `business_quality`: FCF hard screen, criteria, debt, margins, moat, and owner
  earnings already calculated by the engine.
- `valuation`: supported valuation anchor, method conflict, and margin of safety;
  analyst targets are never fair-value anchors.
- `portfolio_risk`: only supplied portfolio-fit, concentration, thematic,
  overlap, and policy facts. Missing context means `insufficient_evidence`.
- `critic`: deterministic result plus validated specialist outputs only; no new
  evidence collection.

No role may execute or record a transaction, change holdings, thesis, targets, or
policy, write private output, publish, commit, push, or read any file. The role
receives all permitted evidence in its packet. Packets and specialist/critic
results remain memory-only unless the user gives immediate explicit approval to
persist the review artifact.

## Failure behavior

If host-native subagents are unavailable before execution, call
`run_deterministic_equity_fallback`. Report `runtime_type=none` and
`fallback_status=deterministic_only`; this is not a multi-agent review.

If any execution starts but times out, is unavailable, returns malformed JSON,
cites an unknown evidence reference, or violates the contract, do not retry.
Preserve valid results only, run the single critic if possible, and return
`partial_agent_failure` with a limited or insufficient result. A deterministic
`insufficient_evidence` result cannot be repaired by agent agreement.
