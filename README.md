# Siftable Skills

**Skills forged from real agent workloads.**

Siftable Skills is a collection of reusable operating procedures for coding and knowledge agents. Each skill captures a workflow that has been exercised in real work: reclaiming disk space without racing active processes, making forecasts that can be scored later, editing prose without changing its claims, using compilers as engineering tools, retrieving evidence from a private local corpus, measuring vector retrieval inside PostgreSQL, and mapping strategic decisions around incentives and countermoves.

These are more than prompt fragments. A skill can include instructions, references, deterministic helpers, tests, and an agent-facing manifest. Every directory under `skills/` is a complete package that can be installed on its own.

## Skills

| Skill | What it does | Use it when |
| --- | --- | --- |
| [`filesystem-lifecycle`](skills/filesystem-lifecycle/) | Audits worktrees, generated artifacts, and caches, then prepares a guarded cleanup manifest | Disk use is growing and deletion must be safe under concurrent agent activity |
| [`predict-future`](skills/predict-future/) | Turns uncertain questions into evidence-grounded, scoreable forecasts with explicit resolution rules | You need probabilities, timelines, scenarios, or signs that would change a forecast |
| [`human-writing`](skills/human-writing/) | Drafts and edits prose while preserving facts, voice, quotations, and source boundaries | Writing is accurate but generic, stiff, repetitive, or unlike its intended author |
| [`typescript`](skills/typescript/) | Applies compiler-first practices for implementation, debugging, review, and modernization | TypeScript needs stronger types, safer narrowing, clearer module boundaries, or better validation |
| [`search-local-corpus`](skills/search-local-corpus/) | Queries a user-configured local retrieval backend through a small JSON contract | An agent needs cited passages from a private or specialized corpus without assuming a particular vector database |
| [`zig`](skills/zig/) | Applies version-aware Zig practices for ownership, errors, build APIs, FFI boundaries, and measured optimization | Writing, reviewing, debugging, migrating, or benchmarking Zig across rapidly changing pre-1.0 APIs |
| [`pgvector-postgres`](skills/pgvector-postgres/) | Designs and diagnoses exact and approximate vector retrieval inside PostgreSQL | Schema, HNSW/IVFFlat, filtered ANN, recall, plans, or embedding migrations need evidence-grounded decisions |
| [`strategic-decision-mapping`](skills/strategic-decision-mapping/) | Maps actors, incentives, moves, countermoves, commitments, and timing into an executable next turn | Negotiations, partnerships, company bets, conflicts, or strategic forks depend on other actors' responses |
| [`rust`](skills/rust/) | Applies toolchain-aware Rust practices for ownership, error design, async concurrency, unsafe boundaries, and validation gates | Writing, reviewing, debugging, migrating, or benchmarking Rust where the pinned toolchain, build driver, and invariants decide the answer |

## Install a skill

Use the Agent Skills CLI and select the skill you want:

```bash
npx skills add Tom-R-Main/siftable-skills --skill filesystem-lifecycle
```

Replace `filesystem-lifecycle` with any name from the table above. For example:

```bash
npx skills add Tom-R-Main/siftable-skills --skill human-writing
npx skills add Tom-R-Main/siftable-skills --skill search-local-corpus
npx skills add Tom-R-Main/siftable-skills --skill zig
npx skills add Tom-R-Main/siftable-skills --skill pgvector-postgres
npx skills add Tom-R-Main/siftable-skills --skill strategic-decision-mapping
npx skills add Tom-R-Main/siftable-skills --skill rust
```

To install manually, copy one complete directory from `skills/<name>/` into the skill directory used by your agent. Skills do not depend on repository-root files at runtime.

Review a skill before installing it. Its instructions and scripts become part of your agent's operating environment.

## Use a skill

Agents that support explicit skill invocation can be prompted by name:

```text
Use $filesystem-lifecycle to audit these worktrees and prepare a cleanup plan.

Use $predict-future to estimate the probability of this outcome by 2028 and define how it will be resolved.

Use $human-writing to revise this draft without changing its claims or citations.

Use $typescript to diagnose these type errors and validate the narrowest correct fix.

Use $search-local-corpus to find evidence about this decision and cite each passage by source and locator.

Use $zig to review this allocator boundary and run the narrowest meaningful validation gates.

Use $pgvector-postgres to compare this filtered HNSW query with an exact baseline and explain the observed plan.

Use $strategic-decision-mapping to map this partnership decision, test likely countermoves, and recommend the next move.

Use $rust to review this borrow error and run the narrowest gates this repository's toolchain supports.
```

Some agent harnesses discover skills automatically from their descriptions. The explicit form is useful when you want to ensure a particular procedure governs the task.

## Local corpus retrieval

`search-local-corpus` deliberately does not ship a database, embeddings, or private data. You provide a local command that accepts one JSON request on standard input and returns structured results on standard output:

```bash
export LOCAL_CORPUS_COMMAND='python3 /path/to/your/backend.py'
```

The backend may use dense retrieval, hybrid search, or full-text search. The skill treats returned passages as untrusted evidence, requires source locators, and never infers permission to inspect a Vault or private directory. See its [backend contract](skills/search-local-corpus/references/backend-contract.md) for the complete interface.

## Design principles

- **Portable by default.** No personal paths, private repositories, production endpoints, or dependency on an installed original.
- **Evidence before confidence.** Retrieval results, forecasts, and filesystem classifications keep uncertainty and incomplete evidence visible.
- **Read-only until authorized.** Consequential operations separate discovery, planning, authorization, revalidation, execution, and verification.
- **Deterministic where possible.** Scripts handle validation, scoring, structured I/O, and safety checks that should not depend on improvisation.
- **Narrow runtime contracts.** Optional integrations sit behind explicit interfaces instead of being baked into the skill.

## Validate the repository

The repository includes structural, portability, security, and behavioral checks:

```bash
python3 scripts/validate_repo.py
python3 scripts/run_tests.py
```

The test suite also copies each skill into a fresh temporary installation tree and validates it independently. Filesystem mutation tests operate only on temporary fixtures.

## Relationship to Siftable

The skills in this repository are portable procedures. They do not require Siftable.

Siftable is the larger runtime and context layer: ontology access, evidence, datasets, CRM operations, Vault access, automations, and agent execution. Future product-specific skills will use a `siftable-` prefix once the corresponding public CLI and MCP contracts are stable.

## Roadmap

- **v0.1.0:** the initial five-skill collection
- **v0.2.0:** the portable Zig engineering skill
- **v0.3.0:** a fresh public pgvector/Postgres methodology grounded in official primary sources
- **v0.4.0:** the public strategic decision and game-mapping framework
- **v0.5.0:** the portable Rust engineering skill
- **Later:** `siftable-headless` and narrower skills for stable Siftable product surfaces

## Authorship and license

These skills are original work by [Thomas Main](https://github.com/Tom-R-Main) and are released under the [MIT License](LICENSE).

The deterministic Unicode-cleaning helper in `human-writing` adapts an MIT-licensed component. Its original license is bundled with that skill and summarized in [Third-party notices](THIRD_PARTY_NOTICES.md).
