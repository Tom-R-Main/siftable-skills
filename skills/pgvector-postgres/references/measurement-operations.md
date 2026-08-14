# Measurement and operations

## Freeze an evaluation set

Create query cases with stable IDs and include:

- expected tenant/security context;
- query vector generation contract;
- filters and `k`;
- exact result IDs;
- ANN result IDs;
- cold/warm or cache state when relevant;
- PostgreSQL/pgvector version and settings;
- dataset snapshot or content version.

Sample across common, rare, fresh, stale, highly selective, and weakly selective cases. Avoid evaluating only easy semantic duplicates.

## Report retrieval quality

At minimum, report:

- recall@k against exact ordered search;
- returned-count shortfall;
- latency p50, p95, and p99 under representative concurrency;
- results by tenant/filter/query class;
- index and heap size;
- configuration and data snapshot.

Use `scripts/compare_recall.py` for deterministic ID overlap. It does not judge semantic relevance; add labeled relevance metrics when the task requires end-user quality.

## Read plans carefully

Capture JSON plans with actual execution only on safe queries:

```sql
explain (analyze, buffers, verbose, settings, format json)
select id
from items
where tenant_id = $2
order by embedding <=> $1::vector
limit $3;
```

Check:

- selected scan and index name;
- filter placement and rows removed;
- estimated versus actual rows;
- top-N sort or distance ordering;
- shared reads/hits and temporary I/O;
- planning and execution time;
- active non-default settings.

Run `scripts/inspect_plan.py --input plan.json` to produce a compact structural summary. It reports evidence; it does not declare the plan optimal.

## Refresh evidence before tuning

Inspect `pg_stat_user_tables`, `pg_stat_user_indexes`, `pg_statio_user_tables`, `pg_statio_user_indexes`, relation sizes, and `pg_stats`. Run `ANALYZE` after representative bulk loads or distribution changes when safe.

Planner statistics are sampled and approximate. An estimate mismatch can arise from correlated filters, tenant skew, stale data, or expressions not represented in statistics. Consider extended statistics for correlated ordinary columns; validate whether they change the relevant plan.

## Build and maintenance checks

Before an ANN build, record:

- table rows and vector null count;
- selected type, dimensions, metric, and opclass;
- available memory, temporary disk, and maintenance window;
- expected concurrent writes;
- rollback/drop command;
- `pg_stat_progress_create_index` monitoring query.

After build, verify validity, size, plan eligibility, recall, latency, and write impact.

High churn creates dead heap tuples and index maintenance work. Monitor autovacuum progress, dead tuples, transaction age, and index growth. Pgvector's HNSW guidance suggests concurrent reindex before vacuum when HNSW vacuum is slow; treat that as an operational intervention requiring disk, lock, replica, and rollback planning.

## Incident sequence

For a latency, recall, or missing-result incident:

1. freeze the exact query, parameters, tenant, and settings;
2. verify model/dimension/metric lineage;
3. compare returned count and exact results;
4. capture JSON plans and buffer evidence;
5. inspect statistics, dead tuples, index validity, and recent migrations;
6. test one transaction-local change at a time;
7. revert diagnostic settings;
8. document whether the issue was correctness, eligibility, recall, planner cost, storage, or concurrency.

Never normalize a production incident into a generic recommendation without preserving the observed evidence and uncertainty.
