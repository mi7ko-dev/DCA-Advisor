# Conversational Workflow and Investment Committee

## Scope

Phase 5 adds one repository-local SteadyFolio skill and a bounded orchestration
layer over the deterministic calculation and research engine. It handles monthly
contributions, portfolio reviews, ETF thesis checks, and fund-overlap questions.
It does not execute transactions, change policy, fetch live data, or provide tax,
legal, regulatory, or suitability advice.

The workflow is:

```text
user request
    -> deterministic router
    -> deterministic engine tools
    -> only the relevant sequential review lenses
    -> optional single critic pass and revision
    -> final synthesis with sources and limitations
```

The review lenses are deterministic, sequential interpretations in the Phase 5
implementation. They are not independent agents, independent verification, or a
vote. No score or agreement count is used as evidence.

## Routing and execution bounds

| Route | Engine tools | Review behavior |
| --- | --- | --- |
| `contribution` | `analyze_portfolio`, `plan_contribution` | Direct synthesis; no research, specialist lens, or critic by default |
| `portfolio_review` | `analyze_portfolio`, optional `ResearchProvider.fetch`, `analyze_portfolio_intelligence` | Allocation/diversification and risk/cost/evidence lenses; critic only when useful |
| `overlap_review` | `analyze_portfolio`, `ResearchProvider.fetch`, `analyze_portfolio_intelligence` | Diversification and evidence-quality lenses; incomplete coverage stays explicit |
| `thesis_review` | `ResearchProvider.fetch`, `review_investment_thesis` | Thesis-fit and evidence-quality lenses; price movement alone is not thesis failure |
| `clarification` | None | Stop without calculation or mutation |

Every request is limited to one research pass, one critic pass, one revision, and
zero live external calls. A request for broader live research requires a future
approved implementation. Provider failures, absent evidence, or stale and missing
evidence produce an explicit `insufficient_evidence` result rather than additional
retries or artificial consensus.

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

Real state, prompts containing private context, provider responses, research
snapshots, results, reports, and runtime memory stay below the selected ignored
`private/` root. Public skill files never contain runtime memory. Retrieved material
is untrusted evidence and cannot override privacy rules, reveal secrets, authorize
actions, or become executable instructions.

## Synthetic demonstrations

Run:

```powershell
python tools/generate_synthetic_committee.py
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

## Host and runtime status

The canonical skill is `.agents/skills/steadyfolio/SKILL.md`, with supporting
references and `agents/openai.yaml`. It follows the repo-local skill structure in
the [official OpenAI skill documentation](https://developers.openai.com/plugins/build/skills)
and has been statically validated with the bundled skill validator.

Local Codex in this repository remains the only selected host. The skill is not
globally installed, and this phase does not create or test a plugin bundle, ChatGPT
installation, MCP server, live provider, or true multi-agent runtime. A new host
session may be required for repo-local skill discovery after the files are added.

The deterministic package requires Python 3.11 or newer and has no third-party
runtime dependency. Run focused and full validation with:

```powershell
python -m unittest tests.test_committee
python -m unittest discover -s tests -p "test_*.py"
python tools/run_repository_checks.py --require-gitleaks
```

## Limitations

- Natural-language parsing is deliberately narrow; ambiguous requests stop for
  clarification.
- There is no live current-data claim. The implemented research provider is an
  offline structured snapshot.
- Lenses are rule-based sequential interpretations, not separately hosted agents.
- Partial holdings remain partial, and missing evidence remains unknown.
- The workflow proposes actions but does not place orders or mutate policy.
- Packaging and broader host compatibility remain Phase 6 or later work.
