# Local toolchain contract

The scripts use Python's standard library. SQLite must include FTS5 (checked by `doctor`); Git supplies revision/dirty metadata when available. No network, dependency installation, embedding provider, daemon, source execution or automatic global writes. Presence of an optional tool in `doctor` does not prove its runtime works.

Set an absolute store outside every source checkout. The store is a private local evidence library, not Codex's global memory. Source text is copied only by explicit bounded `read` requests. Evidence and cards may still contain sensitive application text; filename exclusions are not a comprehensive secret scanner.

```sh
python3 /path/to/repo-learn/scripts/repo_learn.py --store /approved/project/repo-knowledge COMMAND
```

| Command | Result |
|---|---|
| `doctor` | Python/SQLite/FTS5 and optional executable presence; does not run/install adapters. |
| `catalog REPO...` | Actual HEAD, limited dirty status, filtered file metadata, manifests and directories. Full inventory persisted; display lists capped. |
| `find REPO QUERY --glob 'src/*.ts' --limit 12 --max-files 2000 --offset 0` | Case-sensitive literal search; matched line numbers, display omissions, scan scope/failures, and a membership-bound continuation token. Narrow paths before widening budget. |
| `read REPO PATH --start 20 --end 70 --question 'What owns the commit?'` | Exact snippet with evidence ID, HEAD/dirty state, file/slice hashes and timestamp. Paths are relative to REPO. |
| `add-pattern /absolute/card.json` | Validate card and evidence references, persist, index. Identical replays preserve identity and repair JSON; conflicting content requires a new version. |
| `query 'problem vocabulary' --limit 5` | FTS5/BM25 retrieval across human card fields, with source freshness. Lexical OR matching, not semantic embeddings or a correctness score. |
| `verify` | Rehash captured files and report `fresh`, `revision-advanced`, `stale`, `missing`, or `unavailable`. Does not rewrite historical evidence. |
| `export` | Rebuild `patterns.md` with card content and provenance. |
| `status` | Evidence/card/catalog/journal counts. |

Reads are capped at 160 lines and 24,000 characters; source files over 1 MiB are refused. These are helper output defaults, not universal coding rules. Search scans at most its file budget per page. Counts are for the selected eligible scope, not all repo semantics. Catalogs are filesystem metadata and intentionally report that Git ignore rules are not applied. Conservative path exclusions can omit legitimate files; inspect the reported scope before concluding absence. Use a separately authorized exact-file tool if the helper cannot inspect necessary evidence.

The tool excludes generated/dependency directories, `data/`, `.env*`, key/credential names, unsupported extensions, symlinks and binary/non-UTF8 files. Git metadata calls disable fsmonitor and clean/process filters and ignore submodule dirty state. Their purpose is read-only identity, not complete working-tree analysis. Source path hashes remain authoritative for captured bytes.

## Pattern record

The agent writes the semantic content. The helper checks shape, source references and freshness; it cannot decide whether a pattern is true, whether a counterexample is strong, or whether a claimed test ran.

```json
{
  "id": "checkpoint-after-effect-v1",
  "title": "Keep checkpoints behind completed effects",
  "problem": "A retry can skip work if progress advances before the effect commits.",
  "mechanism": "Commit the effect before advancing its checkpoint, or make both atomic.",
  "when_to_use": "Retryable work with a resumable progress marker.",
  "when_not_to_use": "A marker that is merely advisory and never controls work selection.",
  "tradeoffs": "Atomicity may need shared storage; idempotency can be a cheaper alternative.",
  "counterexample": "A failed effect followed by a successful checkpoint write can lose the effect.",
  "transfer": {
    "target": "Name the actual project/seam, or say candidate target not inspected.",
    "application": "Describe the proposed change and adoption status.",
    "compatibility_checks": "Inspect transaction ownership and replay semantics first."
  },
  "validation": {
    "level": "source",
    "result": "Source inspected; target runtime not exercised."
  },
  "evidence_ids": ["ev-actual-id-returned-by-read"],
  "tags": ["retry", "checkpoint", "alternate work-item alias"]
}
```

This is a schema example, not a seeded finding. Replace its evidence ID and content before adding. `validation.level` accepts `source`, `model`, or `integration`; each is an author assertion. For executed checks add exact command, exit/result, artifact and target revision in `validation`. Additional fields such as `aliases`, `decision`, `supersedes` and `unknowns` can retain useful context. A new version is a distinct card; the tool does not automatically hide superseded records.

## Persistence and recovery

`library.sqlite3` is canonical; `patterns/`, `evidence/`, `catalogs/` JSON and `patterns.md` make records inspectable. SQLite transactions protect records; JSON exports are individually atomic but are not a second transactional database. Back up the whole store while no writer is active. `export` reconstructs the Markdown view. There is no automatic cross-store import, relocation, retention, or purge. Preserve the durable store path in the owning project's handoff; installing the skill does not move its library.

Repeat source reads retain the original evidence identity and append a journal entry; freshness distinguishes later revisions. File-level hashes deliberately flag unrelated edits in the same file for review. File freshness does not validate dependency state, runtime behavior or interpretation. Semantic card quality remains an agent/human responsibility.

## Continuation and replay (v1.1.0)

Pass `next.cursor` as `--cursor TOKEN` with the same repo, query, glob, limit and max-files values. Nonzero raw offsets are rejected without a matching token. The token binds sorted eligible path membership and query geometry; insertion/deletion or query changes require restart. Incomplete inventories cannot paginate. Membership is checked before and after a page, but this is not a filesystem transaction: transient changes can escape detection. File contents are read live; same-path content edits do not invalidate the token. For content-consistent analysis use a stable checkout or snapshot. Tokens are local consistency hints, not authentication credentials.

A pattern projection failure returns exit 2 with `canonical_committed: true`, `pattern_id`, and `projection_written: false`. Retry the identical payload under that ID to rebuild JSON. Successful identical retries return `repeated: true` and retain creation metadata; conflicting payloads remain rejected. SQLite serializes concurrent creation/replay. `created_at` and `schema_version` are tool-owned metadata excluded from payload comparison. Markdown export remains a separate derived view.
