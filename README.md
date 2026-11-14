# WhoFix

**Who should fix this issue?** WhoFix reads a repository's history (issues, pull requests and the files they
changed), learns who knows which part of the code, and suggests the best people for each new issue,
with evidence. A human always makes the final call.

> **Status: early development.** Built step by step in public. See [PLAN.md](PLAN.md) for the design,
> [ARCHITECTURE.md](ARCHITECTURE.md) for diagrams and data flow, and [ROADMAP.md](ROADMAP.md) for the build order.

---

## The problem

On a growing team, every new issue raises the same questions:

- *What kind of issue is this, and how urgent is it?*
- *Who has worked on this part of the code before?*
- *Who has time to take it?*

Tech leads answer these from memory. That is slow, it does not scale, and new team members have no way to know.
The answer is already in the repository's history. Nobody has time to read it.

## What WhoFix does

1. **Classifies** each new issue: type (bug, feature, docs, question), area of the code, priority.
2. **Suggests the top 3 people** to fix it, and shows *why*: the past pull requests that touched the same code.
3. **Waits for approval.** A human approves or changes the suggestion before anything is written to GitHub.
4. **Answers questions** about the codebase, such as *"Who knows the authentication module?"*
5. **Writes a weekly report** for leadership: what shipped, what is stuck, where the team is overloaded.

## How it works

```
                 ┌──────────────────────── daily pipeline ─────────────────────────┐
 GitHub API ──>  │  raw JSON (by date) ──> clean tables ──> embeddings + search index │
                 └──────────────────────────────────┬──────────────────────────────┘
                                                    │
 new issue ──> webhook ──> LLM classifier ──> "who knows this code?" retrieval
                                                    │
                                     agent (WhoFix MCP server tools)
                                                    │
                          top-3 suggestion with evidence ──> human approves ──> GitHub
```

**How we know it works:** the repository's history already shows who actually fixed each past issue.
WhoFix is tested on old issues it has never seen, and its suggestions are compared with what really happened.
It must beat simple non-AI baselines (for example, "the last person who edited these files") to be worth using.

## Tech stack

| Layer | Tools |
|---|---|
| Language | Python 3.11 |
| Data | GitHub REST API, DuckDB / PostgreSQL, pgvector |
| AI | Gemini API, Pydantic structured outputs, embeddings, hybrid search (BM25 + vectors) |
| Agents | MCP server and tool calling, human-in-the-loop approval |
| Quality | Golden datasets, LLM-as-judge, Langfuse tracing, eval gate in CI |
| Delivery | GitHub App (webhooks), GitHub Actions, Docker |

## Getting started

```powershell
git clone https://github.com/adil-java/Ai-Engineer-Journey.git
cd Ai-Engineer-Journey
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS/Linux: cp .env.example .env
```

Fill in `.env`:
- `GITHUB_TOKEN`: a fine-grained token with **read-only access to public repositories** and nothing else
- `GEMINI_API_KEY`: from Google AI Studio

Run each step **from the project root** as a module:

```powershell
python -m ingest.github_issues
```

## Project layout

| Folder | Purpose |
|---|---|
| `ingest/` | Fetch raw data from GitHub |
| `transform/` | Turn raw data into clean tables |
| `llm/` | LLM calls, schemas, token and cost tracking |
| `rag/` | Embeddings and search |
| `agent/` | Agent loop and WhoFix MCP server |
| `evals/` | Test datasets and accuracy measurement |
| `app/` | GitHub App webhook server |
| `tests/` | Unit tests |
| `data/` | Local data (never committed) |

## Principles

- **Suggest, never act alone.** Nothing is written to GitHub without human approval.
- **Measure, don't guess.** Every AI feature has an evaluation with real numbers.
- **Raw data is never edited.** Every table can be rebuilt from it.
- **Safe to re-run.** Every pipeline step is idempotent.
- **Least privilege.** Tokens get only the permissions they need.

## Author

**Adil Javed**: Software Engineering, NED University · [GitHub](https://github.com/adil-java)
