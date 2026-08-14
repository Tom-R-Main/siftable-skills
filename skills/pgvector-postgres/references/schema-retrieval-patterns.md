# Schema and retrieval patterns

## Record embedding lineage

An embedding is not self-describing. Preserve enough lineage to reproduce or invalidate it:

- provider and model identifier;
- model revision when available;
- dimensions;
- normalization behavior;
- distance metric;
- source-content version or hash;
- embedding timestamp and status;
- error/retry state for incomplete backfills.

Do not silently mix incompatible models in one indexed search space. If a generic `vector` column stores multiple dimensions, expression and partial indexes must scope a single compatible dimension/model contract.

## Prefer an explicit chunk model

A common starting point is one row per retrievable unit:

```sql
create table retrieval_chunks (
  id bigint generated always as identity primary key,
  tenant_id bigint not null,
  source_id text not null,
  chunk_ordinal integer not null,
  content text not null,
  embedding_model text not null,
  embedding vector(1536),
  embedded_at timestamptz,
  unique (tenant_id, source_id, chunk_ordinal)
);
```

Choose dimensions and types from the actual model contract; the example is not a default recommendation. Keep source identity and chunk order independent of vector identity so content can be re-embedded without losing provenance.

## Tenant and authorization boundaries

Keep authorization predicates in the SQL query even when the application prefilters IDs. PostgreSQL row-level security can enforce which rows are returnable, but it does not automatically create an efficient ANN search space.

Measure per-tenant candidate counts and filter selectivity. Choose among:

- shared table plus ordinary filter index;
- partial ANN indexes for a small stable tenant/category set;
- list/range partitioning for durable boundaries;
- separate tables/databases for stronger lifecycle or isolation requirements.

Partition count, migrations, autovacuum, connection behavior, and cross-tenant operations are part of the cost. Do not partition solely because ANN filtering is inconvenient.

## Hybrid retrieval

Store a generated `tsvector` or maintained search vector beside the embedding when PostgreSQL full-text search is appropriate:

```sql
alter table retrieval_chunks
add column textsearch tsvector
generated always as (to_tsvector('english', content)) stored;

create index retrieval_chunks_textsearch_idx
on retrieval_chunks using gin (textsearch);
```

Retrieve lexical and vector candidates independently under the same authorization filters. Combine ranks in application code or reviewed SQL using a declared method such as reciprocal-rank fusion. Keep component scores and ranks for evaluation; cosine distance and text rank are not directly comparable calibrated probabilities.

Use a reranker only after candidate recall is measured. A reranker cannot recover documents absent from both candidate sets.

## Model and dimension migrations

Prefer side-by-side representations:

```sql
alter table retrieval_chunks
add column embedding_v2 vector(3072);
```

Backfill in bounded batches. Track nulls, failures, stale source versions, and the exact model contract. Build the new index after representative data exists, validate exact and ANN behavior, switch reads behind an explicit configuration boundary, and retain rollback until coverage and retrieval quality are verified.

Avoid in-place dimension changes that destroy the old retrieval surface before the new one is measurable.

## Online index changes

Use a distinct index name, observe build progress, and budget temporary disk and write amplification. `CREATE INDEX CONCURRENTLY` reduces write blocking but takes more work and cannot run inside a transaction block. After interruption, inspect `pg_index.indisvalid` and remove invalid artifacts deliberately.

For partitioned tables, follow the deployed PostgreSQL version's supported concurrent-build procedure rather than assuming the parent index can be built concurrently in one command.
