# AI + Data Engineering Roadmap (about 20 weeks, 10-12 hrs/week)

**One project throughout: the Job Market Platform.**
Job APIs → data pipeline → warehouse → LLM skill extraction → RAG → agent + MCP server → evals → deployed.

Sources: AI Engineer Roadmap PDF (areas 01-08) + data engineering roadmap (phases 1-3).
Rule: tick a box only when you have **used it in code**, not when you have read about it.

---

## Phase 0 · Days 1-3 · Kickoff (foundations already known, skipped)
- [ ] Repo set up (10 min, no lesson needed)
- [ ] 3 architecture questions answered (raw data, LLM cost, schema change)
- [ ] Mission 1: Remotive API → raw JSON (idempotent) → LLM extracts skills → validated JSON

## Phase 1 · Weeks 2-4 · LLM (Area 01)
- [ ] 01-10: tokenization, transformers, attention, context windows, KV cache, temperature/top-p,
      system prompts, few-shot, chain of thought, reasoning models
- [ ] 11 Structured outputs · 12 Prompt caching · 13 Token pricing · 14 Hallucinations
- **Build:** CLI chatbot with system prompt, streaming, JSON mode, token and cost counter per message
- **Project step:** skill extractor that turns job descriptions into validated JSON (Pydantic)

## Phase 2 · Weeks 5-7 · Data foundations (data engineering phases 1-2)
- [ ] Advanced SQL: window functions, CTEs, EXPLAIN, indexes
- [ ] Data modeling: star schema, grain, facts vs dimensions, SCD Type 2
- [ ] Batch pipeline: pagination, retries with backoff, idempotency, Parquet, partitioning
- **Project step:** daily pipeline raw → clean → `fact_job_post`, `dim_company`, `dim_skill`, `dim_date`
  in DuckDB/Postgres. Never pay the LLM twice for the same job.

## Phase 3 · Weeks 8-10 · RAG (Area 02)
- [ ] 01-10: embeddings, cosine similarity, chunking, vector databases, pgvector, HNSW,
      metadata filtering, BM25, hybrid search, reranking
- [ ] 15 Document parsing · 16 Citations · 19 Recall@k
- **Project step:** "Ask the job market": hybrid search over job descriptions with citations.
  Measure Recall@5 on 30 test questions.

## Phase 4 · Weeks 11-13 · Agents (Area 03) + Security basics (Area 06 01-04)
- [ ] Read first: prompt injection, indirect injection, jailbreaks, OWASP Top 10 for LLMs
- [ ] 01-10: tool calling, agent loop, ReAct, planning, reflection, short- and long-term memory,
      MCP servers, MCP clients, agent skills
- [ ] 16 Human in the loop · 17 Context engineering · 19 Stop conditions
- **Project step:** your own `job-market` MCP server (tools: SQL query, RAG search, live API search).
  Agent with a step limit that drafts a tailored cover letter, with your approval before anything is sent.

## Phase 5 · Weeks 14-15 · Evals (Area 04)
- [ ] 01-10: golden datasets, error analysis, LLM as judge, pairwise, rubrics, faithfulness,
      answer relevance, context precision, tool-call accuracy, trajectory evals
- [ ] 11 Regression evals in CI · 15 Tracing · 16 Langfuse
- **Project step:** 50 golden questions, LLM judge, Langfuse traces, CI fails when scores drop

## Phase 6 · Weeks 16-17 · Orchestration + Deployment (data engineering phase 3, Areas 07-08)
- [ ] Airflow: DAGs, retries, backfills · dbt: staging/marts, tests, docs
- [ ] Backend 11-20: Redis cache, queues, background jobs, rate limiting, idempotency keys, Pydantic
- [ ] Deployment: eval gate in CI, environment configs, health checks, prompt versioning, rollbacks
- **Project step:** daily Airflow run, dbt models with tests, app deployed with an eval gate

## Phase 7 · Weeks 18-19 · AI system design + Security (Areas 05-06)
- [ ] Model routing, fallbacks, semantic cache, token budgets, time to first token, batch inference
- [ ] Guardrails, output validation, PII redaction, least-privilege tools, audit logging, red teaming
- **Project step:** small AI gateway (routing + fallback + cache + per-user budget) and a
  20-prompt red-team test, run again after fixes

## Phase 8 · Week 20 · Ship it
- [ ] README with architecture diagram and the reasons for your decisions
- [ ] Eval scores before and after, cost and latency per request, security measures
- [ ] Live demo link and a 3-minute video
- [ ] CV and LinkedIn updated

---

### Already known (skipped)
Git/GitHub · REST APIs · HTTP status codes · auth (JWT, RBAC) · async/await · SQL basics · SQL vs NoSQL ·
indexing · Docker · CI/CD basics · AWS · Vercel · basic RAG flow (GreenBuddy)

### Later, after landing a job
Spark/Databricks · Kafka/CDC · Snowflake (SnowPro Core) · Kubernetes · vLLM/GPU serving · fine-tuning (LoRA/QLoRA)
