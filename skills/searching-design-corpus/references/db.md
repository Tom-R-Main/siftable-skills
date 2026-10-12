# Database-systems design corpus (`--collection db`)

Suggested reference sources; this package does not include the books or indexed chunks. **Bimodal**: foundational textbooks (broad principles) and
research papers (specific named techniques). Query the books for principles, the
papers for a method by name.

## Foundational — broad principles

- **Designing Data-Intensive Applications, 2e** — Kleppmann & Riccomini
- **Database Internals** — Alex Petrov

Themes (reference themes to investigate):

- **Storage engines & file layout** — B-trees, pages/cells, mutable vs immutable
  structures, LSM-trees, write amplification, compaction
- **Transactions & isolation** — serializability, snapshot isolation / SSI,
  write-write conflicts, weak isolation anomalies
- **Replication & consistency** — linearizability, causal consistency,
  read-after-write, logical clocks, conflict resolution
- **Consensus & coordination** — Raft, Paxos ("Generals Problem"), failure
  detectors, coordination-freedom
- **Partitioning / sharding** — rebalancing, skew, hot shards, request routing
- **Recovery & durability** — WAL, ARIES-style checkpoints (dirty pages, txn
  table), fault tolerance
- **Encoding & schema evolution** — backward/forward compatibility, rolling upgrades
- **Batch & stream processing** — MapReduce shuffles, event time vs processing
  time, stream-table duality

## Research papers — specific named techniques

- **Looking Back at Postgres** (Hellerstein) — `1901.01973` — Postgres design
  history, extensibility, type system
- **Join Processing for Graph Patterns** — `1503.04169` — worst-case optimal joins
  (LeapFrog TrieJoin, Minesweeper)
- **Fast In-Memory SQL Analytics on Graphs** — `1602.00033` — GQ-Fast, fragment
  compression (RLE / Huffman / bitmaps), code generation
- **FLAT** — `2011.09022` — cardinality estimation (factorized PDFs, Bayesian nets,
  vs histograms / learned models)
- **LIMAO** — `2507.00188` — lifelong modular learned query optimization
  (Balsa/Bao lineage, modular RL, plan search)
- **Linking Graph Entities with Multiplicity and Provenance** — `1908.04464` —
  entity linking / resolution with provenance
- **Insuring Every Action** — `2605.25632` — runtime actuarial control / safety of
  autonomous AI agents (outlier: agent-risk, not classic DB; surfaces on
  agent-safety / risk-budget queries)

## Example questions to validate against your configured backend

- `"B-tree vs LSM-tree write amplification tradeoffs"` → DDIA + Database Internals
- `"serializable snapshot isolation conflict detection"` → DDIA (transactions)
- `"worst-case optimal join algorithms"` → 1503.04169
- `"learned cardinality estimation"` → FLAT + LIMAO papers
