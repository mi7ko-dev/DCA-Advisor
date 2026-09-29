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
   fallback status, and revisions actually used.

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

For Phase 8 equity review, call the workflow multi-agent only when the runtime is
`codex_native_subagents` and the trace records separate completed executions. The
`in_memory_test_backend` is a synthetic contract test. Runtime `none` is a
deterministic-only fallback.
