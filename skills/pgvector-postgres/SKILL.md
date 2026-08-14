---
name: pgvector-postgres
description: Design, review, migrate, measure, or debug PostgreSQL vector retrieval with pgvector. Use for vector, halfvec, bit, or sparsevec columns; exact nearest-neighbor queries; HNSW or IVFFlat indexes; cosine, L2, inner-product, L1, Hamming, or Jaccard distance; filtered or multi-tenant ANN; hybrid full-text/vector search; embedding-model or dimension changes; recall/latency evaluation; EXPLAIN plans; index builds; planner statistics; vacuum and churn; or retrieval incidents. Prefer live schema, query, plan, and workload evidence over generic tuning advice.
---

# Pgvector Postgres

Treat vector retrieval as a measurable PostgreSQL workload, not as an index-selection exercise. Establish correctness and an exact baseline first; add approximation only when the workload demonstrates a need.

Resolve bundled paths from this `SKILL.md`. Read `references/primary-sources.md` before making version-specific claims. The public skill is grounded only in PostgreSQL documentation and pgvector's official documentation and source.

## Establish the contract

Freeze these inputs before proposing schema or index changes:

- PostgreSQL and pgvector versions;
- embedding model, version, dimensions, normalization, and distance metric;
- authoritative row identity and tenant/security boundary;
- update, delete, and re-embedding rates;
- query shape, filters, requested `k`, and minimum acceptable result count;
- latency target and concurrency;
- recall target and exact comparison set;
- migration, lock, disk, memory, and rollback constraints.

If the metric or embedding lineage is unknown, stop before choosing an opclass. If production access is unavailable, label conclusions as design guidance rather than observed behavior.

## Inspect before changing

Collect the extension version, vector columns, index definitions, table/index sizes, row estimates, statistics freshness, representative parameterized SQL, and plans.

```sql
select extversion from pg_extension where extname = 'vector';

select schemaname, tablename, indexname, indexdef
from pg_indexes
where indexdef ilike '% using hnsw %'
   or indexdef ilike '% using ivfflat %';

explain (analyze, buffers, verbose, settings, format json)
select id
from items
where tenant_id = $2
order by embedding <=> $1::vector
limit 20;
```

`EXPLAIN ANALYZE` executes the query. Use a read-only transaction or a safe replica for queries with side effects. Summarize JSON plans with `scripts/inspect_plan.py`; never infer health from index existence alone.

## Separate four questions

1. **Correctness:** Are model, dimensions, metric, opclass, casts, filters, RLS, and ordering aligned?
2. **Eligibility:** Does the SQL expose an ascending distance operator directly in `ORDER BY` with `LIMIT`?
3. **Quality:** What is recall@k, result-count shortfall, and ranking stability against exact search?
4. **Cost:** What do latency distributions, buffers, plan estimates, index size, build time, and write/vacuum behavior show?

A fast query with poor recall is not healthy. A sequential scan on a small or highly selective relation is not automatically unhealthy.

## Choose the smallest justified path

- Start with exact ordered search when the candidate set is bounded or the latency target is already met.
- Prefer HNSW when measured speed/recall is the priority and build time, memory, and write cost are acceptable.
- Prefer IVFFlat only with representative training data and an explicit lists/probes evaluation.
- Keep the distance operator and index opclass aligned.
- For filtered ANN, measure result shortfall and recall before changing search breadth. Read `references/query-index-design.md` for iterative scans, partial indexes, and partitioning.
- Do not propose a composite tenant/vector ANN index: pgvector's HNSW and IVFFlat access methods are single-column. Scope the search with an ordinary filter index, a partial ANN index, partitioning, or a separate table when evidence supports it.

## Measure exact versus approximate

Run the same frozen query set against:

- an exact baseline with approximate index scans disabled in a transaction; and
- the candidate ANN configuration with identical filters and `k`.

Record returned IDs and compare them with:

```bash
python3 scripts/compare_recall.py \
  --exact exact-results.json \
  --approx approximate-results.json \
  --k 20
```

Measure recall across representative tenants, filter selectivities, data ages, and query classes. Report distributions and worst cases, not only a global mean. Read `references/measurement-operations.md` before tuning `hnsw.ef_search`, `ivfflat.probes`, list counts, or planner switches.

## Keep session state bounded

Use transaction-local settings with pooled connections:

```sql
begin;
set local hnsw.ef_search = 100;
select ... order by embedding <=> $1::vector limit 20;
commit;
```

Do not use planner-disable settings as permanent tuning. They are diagnostic controls for comparing paths.

## Design migrations around retrieval identity

Treat embedding model, dimensions, normalization, and metric as a versioned contract. For an incompatible model or dimension change:

1. add a new column or table;
2. backfill with observable progress and failure accounting;
3. validate coverage and exact-query correctness;
4. build the matching index;
5. compare recall and latency;
6. switch reads explicitly;
7. retain a rollback window;
8. remove the old representation only after verification.

Run `CREATE INDEX CONCURRENTLY` outside transaction blocks. Inspect invalid indexes after interrupted builds. Read `references/schema-retrieval-patterns.md` for tenant, RLS, hybrid retrieval, and model-version patterns.

## Apply an evidence ladder

Prefer changes in this order:

1. repair query, metric, cast, or opclass correctness;
2. refresh statistics and verify the real plan;
3. establish exact quality and latency;
4. tune query-local ANN breadth;
5. add or revise one index;
6. consider partial indexes or partitioning for stable, material filter boundaries;
7. consider precision reduction, quantization, or reranking;
8. change topology only after simpler interventions fail.

Every recommendation must name the evidence, expected effect, validation query, rollback, and remaining uncertainty.

## Supporting references

- `references/query-index-design.md`: types, metrics, exact/ANN choice, HNSW, IVFFlat, query eligibility, filtering, and iterative scans.
- `references/schema-retrieval-patterns.md`: embedding lineage, tenants, RLS, model migrations, and hybrid retrieval.
- `references/measurement-operations.md`: exact baselines, recall harnesses, plans, statistics, builds, vacuum, and incident checks.
- `references/primary-sources.md`: current primary sources and the boundary between documented facts and original synthesis.
- `tests/fixtures/integration.sql`: destructive only to its own schema; run solely against a disposable pgvector database.

Do not access a production database, private corpus, credentials, or embedding store without explicit authorization. Do not claim a production improvement from synthetic data alone.
