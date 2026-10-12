# Primary sources

This public skill is an original methodology grounded in redistributable primary sources. It does not include the installed skill's source map, local embeddings, book corpus, private repository material, or source-derived summaries.

Version-specific guidance was refreshed on 2026-10-12 against pgvector
`v0.8.7`, its changelog and access-method handlers, and PostgreSQL 18
documentation. PostgreSQL's current stable documentation is 18; development
documentation is a separate contract. Preserve deployed version pins and
recheck version-matched sources when they differ. This refresh does not qualify
a production workload.

## Pgvector

- [pgvector v0.8.7 README](https://github.com/pgvector/pgvector/blob/v0.8.7/README.md): types, distance operators, exact search, HNSW and IVFFlat behavior, query settings, filtering, iterative scans, partial indexes, partitioning, multitenancy, hybrid search, build guidance, recall monitoring, vacuum guidance, and troubleshooting.
- [HNSW access-method handler](https://github.com/pgvector/pgvector/blob/v0.8.7/src/hnsw.c): confirms ordered-operator support and that HNSW does not support multicolumn or included-column indexes.
- [IVFFlat access-method handler](https://github.com/pgvector/pgvector/blob/v0.8.7/src/ivfflat.c): confirms the same access-method capabilities for IVFFlat.
- [pgvector v0.8.7 changelog](https://github.com/pgvector/pgvector/blob/v0.8.7/CHANGELOG.md): the October 1 release fixes an IVFFlat index-build buffer overflow and an empty-input aggregate error. Evaluate a scoped upgrade when the deployed version is affected; a skill refresh does not upgrade the database.
- [pgvector repository](https://github.com/pgvector/pgvector): authoritative extension source and release tags.

## PostgreSQL

- [SET](https://www.postgresql.org/docs/18/sql-set.html): transaction-local setting lifetime.
- [CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html): concurrent-build semantics, caveats, and transaction-block restriction.
- [Using EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html): planner estimates, actual execution, and interpretation limits.
- [Planner statistics](https://www.postgresql.org/docs/18/planner-stats.html): approximate statistics, `ANALYZE`, and extended statistics.
- [Routine vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html): dead-row cleanup, statistics, visibility maps, and autovacuum.
- [Row security policies](https://www.postgresql.org/docs/18/ddl-rowsecurity.html): policy behavior and security boundaries.
- [Table partitioning](https://www.postgresql.org/docs/18/ddl-partitioning.html): partition pruning and operational tradeoffs.
- [Full-text search controls](https://www.postgresql.org/docs/18/textsearch-controls.html): document/query construction and ranking functions for hybrid retrieval.

## Synthesis boundary

The contract-first workflow, four-question diagnostic split, evidence ladder, migration sequence, evaluation schema, and reporting requirements are original synthesis. Source links establish product behavior; they do not prove that a particular configuration is correct for a workload. Only live schema, plans, data distributions, exact comparisons, and operational measurements can do that.
