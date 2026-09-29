# Response contract

Present these sections distinctly when their content exists:

1. Facts and deterministic calculations.
2. Sources, value dates, retrieval dates, freshness, and data limitations.
3. Assumptions.
4. Specialist interpretations.
5. Meaningful disagreements.
6. Final synthesis and proposed next action.
7. Execution trace: deterministic tools, review lenses, real agent roles and
   statuses, runtime type, provider calls, live market-data calls, critic passes,
   fallback status, and revisions actually used. Render every critic finding with
   its code, severity, description, affected roles, and evidence references.
8. Private persistence: cache/context records created or reused, their freshness
   basis, and confirmation that no existing private record was overwritten.

Use exact values from structured engine results. Do not introduce opaque scores,
confidence percentages, forecasts, unsourced facts, or arithmetic performed by a
review lens.

State whether user approval is required and whether any mutation occurred. A
proposal is not an execution. A saved review is not a transaction or policy change.

If evidence is insufficient, say which conclusion is unsupported, preserve any
meaningful disagreement, and stop. Do not force a consensus or silently fill gaps.

For a sequential same-thread workflow, include this disclosure or an equally clear
equivalent:

> Review lenses are sequential interpretations, not independent agents or
> verification.

Call a workflow multi-agent only when the runtime records separate subagent
executions. For the strict equity contract this means
`runtime_type=codex_native_subagents`; `in_memory_test_backend` is a synthetic
contract test and runtime `none` is `deterministic_only`. For other routes,
disclose the selected roles and actual host execution status in the answer;
same-thread model lenses use `single_thread_sequential`, not
`deterministic_only`. Do not imply that the equity schema validated a generic
review.
