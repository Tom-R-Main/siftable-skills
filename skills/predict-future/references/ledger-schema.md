# Personal Siftable Forecast Ledger v1

Use one flat dataset first. This is a personal, opt-in persistence adapter for `predict-future`, not a prerequisite for forecasting and not yet a multi-dataset ontology.

The authoritative machine-readable contract is emitted by:

```bash
python3 scripts/forecast.py ledger-contract
```

## Dataset contract

- **Title:** `Personal Forecast Ledger`
- **Contract identifier:** `predict-future-ledger-v1`
- **Record kinds:** `question`, `version`, `evidence`, `resolution`
- **Mutation rule:** clients may append and query; they never update or delete historical records.
- **Enforcement in v1:** client and skill contract. Server-enforced immutability can be added after real usage warrants it.

| field | Siftable field type | contract |
|---|---|---|
| `record_id` | text | unique immutable record identifier |
| `record_kind` | select | question / version / evidence / resolution |
| `question_id` | text | stable forecast object identifier |
| `version_id` | text | forecast version identifier when applicable |
| `issued_at` | date | append or issue time |
| `information_cutoff` | date | latest permissible evidence |
| `resolution_date` | date | frozen resolution date or window end |
| `probability` | number | binary probability from 0 to 1 when applicable |
| `distribution_json` | text | categorical distribution or numeric quantiles |
| `source_uri` | url | principal evidence or resolution source |
| `skill_hash` | text | content hash from `fingerprint` |
| `model_ids_json` | text | exact model identifiers and roles |
| `supersedes_id` | text | prior immutable version; never an update target |
| `payload_json` | text | complete kind-specific record |

JSON is stored as canonical compact text because the current portable dataset field contract has no JSON field type. Promote frequently queried payload keys to typed fields only after usage proves the need.

## Write contract

1. Run `ledger-init` without `--execute` and inspect the dry-run contract.
2. Obtain explicit user authorization before the first `ledger-init --execute`. Initialization reuses an exact-title ledger only when both its metadata contract and live field contract match; schema drift fails closed.
3. Capture the returned dataset ID in `PREDICT_FUTURE_LEDGER_ID` or pass `--dataset-id` explicitly.
4. Validate each row with `ledger-append` in dry-run mode.
5. Append only with `ledger-append --execute`, which maps to `sift datasets add`.
6. Express forecast changes as a new `version` record linked by `supersedes_id`.
7. Express adjudication amendments as a new question or an explicit pre-resolution rule version in `payload_json`; never silently rewrite the original.
8. Express resolution as a new `resolution` record, preserving source and ambiguity notes.

The helper exposes no update or delete subcommand. It must not call `sift datasets update-record`, `delete-record`, or dataset deletion.

## Read contract

Read one forecast history by exact `question_id`:

```bash
python3 scripts/forecast.py ledger-read \
  --dataset-id DATASET_ID \
  --question-id QUESTION_ID
```

This maps to `sift datasets query` with an equality filter. Sort the returned records by `issued_at` in the consumer when chronological presentation matters. A missing Sift CLI or dataset ID disables persistence, not forecasting.

## Kind-specific payloads

### `question`

Preserve the complete validated question specification: original wording, forecast type, outcomes or metric, resolution rule and sources, assumptions, exclusions, void conditions, conditional status, and adjudicated terms.

### `version`

Preserve raw members, mechanical aggregate, reconciled value, calibrated value or null, aggregation method, preflight, model identifiers, skill hash, evidence snapshot references, mechanisms, baselines, cruxes, signposts, rationale summary, previous value, delta, and update reason.

### `evidence`

Preserve source, publication date, observed window, observation/source-claim/inference classification, direction, mechanism, directness, reliability, independence notes, and limitations. The report shows 4–8 decisive items; the ledger may retain the full snapshot.

### `resolution`

Preserve observed outcome, resolution evidence, resolver, ambiguity or void rationale, applicable scores, comparator scores, and the exact forecast version being scored.

## Lifecycle boundary

The dataset is the durable forecast history. It is not a scheduler or task queue.

- Use a scheduler for recurring review and resolution checks.
- Use `sift work` only when a review, research refresh, or adjudication is executable work with an owner and acceptance criteria.
- Do not turn every signpost into a work item; create work only when action is intended.

## Promotion path

After enough personal use reveals stable query patterns, promote the flat ledger through ordinary Siftable primitives:

1. inspect the live dataset contract;
2. propose typed fields or linked datasets as a reviewable diff;
3. validate and review the diff;
4. apply it only with explicit authorization;
5. preserve every existing immutable row.

Do not begin with a four-dataset schema, scheduler service, calibration service, or marketplace dependency graph. Let resolved forecasts reveal the next primitive.
