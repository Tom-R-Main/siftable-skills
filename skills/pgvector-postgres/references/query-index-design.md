# Query and index design

## Preserve retrieval semantics

Bind the following choices together:

| Contract element | Examples | Failure when mismatched |
| --- | --- | --- |
| Stored type | `vector`, `halfvec`, `bit`, `sparsevec` | unsupported dimension, precision, or operator class |
| Metric | L2, inner product, cosine, L1, Hamming, Jaccard | ranking differs from model/evaluation assumptions |
| Operator | `<->`, `<#>`, `<=>`, `<+>`, `<~>`, `<%>` | index ineligible or results ordered under the wrong distance |
| Opclass | `vector_l2_ops`, `vector_ip_ops`, `vector_cosine_ops`, etc. | index cannot serve the intended operator |
| Query direction | ascending distance | descending similarity expressions hide the indexable distance order |

For cosine similarity presentation, keep cosine distance in the indexable order and compute similarity only in the projection:

```sql
select id, 1 - (embedding <=> $1::vector) as similarity
from items
order by embedding <=> $1::vector
limit $2;
```

Do not order by the derived similarity expression when ANN eligibility matters.

## Exact search first

Exact search is the correctness oracle. It is often sufficient when an ordinary predicate sharply bounds the candidate set, the table is modest, or the latency objective is already met.

Create an exact baseline in a transaction:

```sql
begin;
set local enable_indexscan = off;
set local enable_bitmapscan = off;
select id
from items
where tenant_id = $2
order by embedding <=> $1::vector
limit $3;
commit;
```

Verify the plan. Disabling planner methods discourages or removes paths but does not substitute for inspecting the resulting plan.

## HNSW versus IVFFlat

| Question | HNSW | IVFFlat |
| --- | --- | --- |
| Training step | none | requires representative rows before build |
| Typical speed/recall | stronger | lower at comparable tuning in pgvector guidance |
| Build time and memory | higher | lower |
| Primary query knob | `hnsw.ef_search` | `ivfflat.probes` |
| Primary build knobs | `m`, `ef_construction` | `lists` |
| Empty-table build | meaningful | not meaningful for trained centroids |

Treat these as candidate properties, not a verdict. Benchmark with the deployed PostgreSQL/pgvector versions, data distribution, filters, concurrency, and storage.

## Query eligibility

For an ANN index to be considered, preserve:

```sql
order by embedding <=> $1::vector
limit $2
```

The distance operator must be visible directly in ascending order. Check casts and expression indexes: the indexed expression and query expression must match.

Small tables, selective filters, stale estimates, out-of-line vector storage, or cost settings may still lead the planner to choose another path. Use `EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON)` before deciding that the planner is wrong.

## Filtered ANN

Approximate scans visit vector candidates and then apply ordinary filters. A selective tenant, category, timestamp, or authorization predicate can therefore return fewer than `k` rows or lower recall.

Evaluate in this order:

1. index the ordinary filter column when it enables a fast exact candidate scan;
2. enable and measure iterative scans when the installed pgvector version supports them;
3. tune query-local scan breadth;
4. use a partial ANN index for a small, stable set of important predicate values;
5. partition when the boundary is durable and operationally justified;
6. use separate tables only when isolation or lifecycle requirements warrant them.

Do not infer that a global ANN index isolates tenants. Vectors from other tenants can affect graph/list traversal, speed, and recall even when SQL and RLS prevent them from being returned.

## Iterative scans

Pgvector 0.8.0 introduced iterative scans for filtered ANN. Strict ordering preserves distance order. Relaxed ordering can improve recall but may require an outer reorder through a materialized CTE. Bound scan expansion with the matching pgvector settings and measure both result count and recall.

Use `SET LOCAL` so pool sessions do not retain experimental settings.

## Precision reduction and reranking

`halfvec`, binary quantization, and subvector indexing can reduce working-set or candidate cost. They also change the candidate representation. Use them as two-stage retrieval:

1. retrieve a larger candidate set with the reduced representation;
2. rerank by the original vector and metric;
3. compare end-to-end recall and latency against the exact baseline.

Do not describe a smaller index as a quality-neutral optimization without measurement.
