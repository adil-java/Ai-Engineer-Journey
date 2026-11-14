# WhoFix: Build Plan

What we are building, for whom, how, and how we will know it works.
For the week-by-week learning order, see [ROADMAP.md](ROADMAP.md).

---

## 1. The problem

When a new issue arrives, a tech lead has to decide **what it is**, **who knows that code**, and
**who has time**. They answer from memory. It is slow, it depends on one person, and the knowledge is lost when
they leave. The repository's history already contains the answer, but nobody reads thousands of old pull requests.

## 2. Users

| User | What they want |
|---|---|
| Tech lead / engineering manager | Assign issues faster and correctly; see progress without asking everyone |
| Developer | Get issues that match what they know; find who to ask about unfamiliar code |
| New team member | Learn who owns which part of the codebase |

## 3. Scope

### Version 1 (what we build)
1. **Issue classifier:** type, code area, priority, skills needed, as validated JSON.
2. **Top-3 assignee suggestions** with evidence (links to the past PRs that touched the same code).
3. **Human approval:** suggestions are posted for approval; nothing is assigned automatically.
4. **Ask the codebase:** *"Who knows the auth module?"*, *"What changed in the router last month?"*
5. **Weekly leadership report:** shipped, stuck, overloaded.

### Not in scope (on purpose)
- **No automatic assignment.** A human always decides.
- **No developer performance scores.** WhoFix measures knowledge and workload, never "who is the best developer".
  It is a routing tool, not a surveillance tool.
- **No private repositories in version 1.** Free-tier LLMs may use input data; private code needs a paid or
  self-hosted model.
- **No code writing.** WhoFix routes work; it does not fix issues.

## 4. Data

**Practice repository:** `nestjs/nest` (public, active, thousands of issues and PRs).

### Sources (GitHub REST API)
| Data | Why we need it |
|---|---|
| Issues (title, body, labels, dates, author) | What needs fixing |
| Pull requests (title, body, author, merged date) | Who did the work |
| Files changed per PR | Which part of the code each person knows |
| Issue timeline / "Fixes #123" links | **Which PR closed which issue: our ground truth** |
| Reviews | Who else knows that code |

> Note: the GitHub issues endpoint also returns pull requests. The pipeline must separate them.

### Data layers
```
data/raw/github/<endpoint>/<YYYY-MM-DD>.json     exactly as GitHub returned it, never edited
            ↓
clean tables (DuckDB/Postgres):
  fact_issue          one row per issue
  fact_pull_request   one row per PR
  fact_pr_file        one row per file changed in a PR
  bridge_issue_fix    issue → PR that fixed it (ground truth)
  dim_developer       one row per person
  dim_file / dim_area one row per file, grouped into code areas
  dim_date
            ↓
search index: embeddings of issues and PRs (pgvector) + keyword index (BM25)
```

## 5. AI components

| Component | Input → output | Key techniques |
|---|---|---|
| Classifier | issue text → `{type, area, priority, skills}` | Structured outputs, Pydantic validation, few-shot |
| Expert finder | new issue → ranked developers + evidence PRs | Embeddings, hybrid search, reranking, metadata filters |
| Agent | question or new issue → suggestion or answer | Tool calling, MCP server, step limit, human in the loop |
| Report writer | week's data → leadership summary | SQL tools, grounded generation, citations |

**WhoFix MCP server tools:** `search_issues`, `who_touched(path)`, `developer_workload`,
`similar_past_issues`, `propose_assignment` (proposes only; never writes).

## 6. How we will know it works

### Evaluation method
1. Take issues that were **already fixed**, and hide who fixed them.
2. Give WhoFix only the data from **before** each issue was opened (no peeking at the future).
3. Compare its top-3 suggestions with the person who actually fixed it.

### Metrics
| Metric | Target |
|---|---|
| Assignee accuracy: correct person in top 3 | Beat every baseline below |
| Classifier accuracy (50 hand-labeled issues) | ≥ 85% on type |
| Report faithfulness (LLM judge + manual check) | No invented facts |
| Cost per issue | Measured and reported |
| Latency per suggestion | Measured and reported |

### Baselines WhoFix must beat
- **Random** developer from the active team
- **Most active** developer last month
- **Last person who edited** the files mentioned in the issue

If AI cannot beat "last person who edited the files", that is an honest result, and we report it.

## 7. Security and privacy

- **Prompt injection:** issue text is written by strangers. An issue can say *"ignore your instructions"*.
  Issue text is treated as data, never as instructions; outputs are validated; tools are read-only.
- **Least privilege:** the token is read-only, public repositories only.
- **Red-team test:** 20 malicious issues, run before and after the fixes, results published.
- **Audit log:** every suggestion and approval is recorded.

## 8. Cost

Everything runs on free tiers: GitHub API, Gemini free tier, local DuckDB/Postgres, GitHub Actions,
Langfuse free tier. Rules: never pay the LLM twice for the same issue (dedupe by content hash + prompt version);
test on 5 items before running on 1,000.

## 9. Milestones

| # | Milestone | Done when |
|---|---|---|
| M1 | Raw ingestion | Closed issues and PRs saved by date; safe to re-run |
| M2 | Issue classifier | 5, then 100 issues classified into validated JSON; tokens and cost printed |
| M3 | Warehouse + ground truth | Clean tables built; issue → fixing PR → developer linked |
| M4 | Expert finder | Top-3 suggestions with evidence; accuracy measured against baselines |
| M5 | Agent + MCP server | Agent answers questions and proposes assignments; human approval step |
| M6 | Evals in CI | Golden datasets, LLM judge, tracing; CI fails when scores drop |
| M7 | GitHub App | New issue → webhook → suggestion comment on a demo repo |
| M8 | Hardening | Model routing, caching, red-team results before and after |
| M9 | Ship | README with real numbers, demo video, CV and LinkedIn updated |

## 10. Risks and open questions

| Risk | Plan |
|---|---|
| Open-source repos rarely use the "assignee" field | Use "who merged the fixing PR" as ground truth instead |
| A few maintainers fix most issues, so "always suggest the top maintainer" scores well | Report the baselines honestly; also measure accuracy for non-maintainers |
| Some issues are never linked to a PR | Use only clearly linked issues for evaluation; report how many |
| New developers have no history (cold start) | Fall back to code area + workload; note it as a known limit |
| GitHub rate limits (5,000 requests/hour with a token) | Incremental loads (`since=`), caching, backoff |
| Free LLM limits | Small batches, dedupe, cheap model for classification |
