# Manifest object model

Use the manifest as frozen evidence, not deletion authority. Record the authorization envelope separately from classification.

## Version and authority

Mutation uses `filesystem-lifecycle/v3` manifests and `filesystem-lifecycle/selection-v3` selections. Older records are reporting inputs only. Regenerate audit evidence instead of upgrading a deletion record in place.

`authorization.envelope` binds `roots`, `kinds`, `exclusions`, `filesystem` (`device`, `filesystem_id`), `volume`, `target_free_delta_bytes` and `risk_ceiling_bytes`. Keep the human scope alongside it. Checksums detect accidental changes; authorization remains the human instruction recorded by the agent.

## Candidate record

```yaml
id: artifact:stable-hash
path: /absolute/original/path
kind: generated_artifact
owner: cargo

evidence:
  observed_at: 2026-08-14T12:00:00+00:00
  scan_complete: true
  errors: []

identity:
  canonical_path: /absolute/resolved/path
  device: 16777234
  filesystem_id: 16777234
  inode: 123456
  link_count: 1
  mount_id: device:16777234:/System/Volumes/Data
  is_symlink: false

boundary:
  approved_root: /absolute/approved/root
  approved_root_device: 16777234
  stay_on_device: true
  unexpected_mounts: []

storage:
  logical_bytes: 8589934592
  allocated_bytes: 4294967296
  estimated_reclaimability: unknown

references:
  cwd_pids: []
  open_handle_pids: []
  codex_session_roots: []

recovery:
  level: regenerable
  method: cargo build

classification: safe_now
reasons: []
covered_by: null
action:
  driver: filesystem
  operation: delete_exact_tree
preconditions: []
```

Worktree records additionally include repository, HEAD, branch, selected protected base, clean/locked state, and representation proof: `exact_ancestor`, `tree_equivalent`, `patch_equivalent`, or `unique`.

## Path and identity rules

Require all of the following at audit and revalidation:

- canonical candidate remains beneath `approved_root`;
- candidate is not the approved root itself;
- original path is not a symlink;
- device and inode match the frozen identity;
- link count is recorded and changes trigger revalidation failure;
- recursive deletion does not cross a different device or follow a symlink;
- no nested mount appeared beneath the candidate.

Hardlinks share one inode. Do not count two hardlinked paths as independent recovery, and do not promise that unlinking one path frees blocks. APFS clones and sparse files introduce separate logical-versus-allocated uncertainty.

## Evidence and recovery

Set `scan_complete: false` and classify `unknown` when a required probe fails, is truncated, or encounters a permission error. Record errors; do not omit them.

Use these reclaimability values:

- `high`: owner semantics support independent deletion and no sharing signal is known;
- `partial`: shared blocks, hardlinks, or overlap make some but not all recovery plausible;
- `unknown`: physical reclaim cannot be estimated reliably.

Treat the post-action free-space measurement as authoritative regardless of the estimate.

## Candidate overlap

Record `covered_by` when a parent candidate includes a child. Prefer safe whole-worktree retirement; otherwise remove only the independently safe generated subtree. Never add overlapping sizes.

## Authorization and budget

Freeze:

- authorization mode and stated scope;
- baseline free bytes;
- exact selected candidate IDs and order at apply time;
- selected allocated-byte total;
- target free-space gain;
- risk ceiling.

Stop after the selected set. Never add a candidate because concurrent writes erased the net gain.

## Target-limited planning

A target-limited audit may omit logical size and defer storage measurement after measured, non-overlapping `safe_now` candidates cover the requested physical target plus headroom. A resource-kind-restricted fast lane may also stop classification and omit deliberately unassessed candidates after recording their count. Record:

- target and headroom;
- included and preferred resource kinds;
- required and measured allocated-byte budgets;
- exact measured candidate IDs;
- discovered, assessed, and deliberately deferred candidate counts;
- whether the budget was met;
- candidates deferred by overlap or budget completion.

This is an intentionally partial inventory, not weaker deletion evidence. Apply still requires complete allocated storage, identity, boundary, recoverability, authorization, and fresh liveness evidence for every selected candidate.

## Selection plan

An integrity-protected selection freezes exact candidate IDs and order, its source manifest path and digest, target, headroom, selected allocated-byte budget, and budget status. It may automate a recorded goal authorization. It never replaces explicit candidate approval under manifest authorization.

Reject a selection when it is stale, edited, empty, references another manifest, contains an unknown ID, or overlaps selected resources.

## Apply report

Persist the final report. Distinguish the free-space change observed during each deletion interval from cumulative net physical recovery since apply began; neither proves exclusive causality when concurrent writers exist. Harmless pre-mutation skips can coexist with a met target; partial or uncertain mutation cannot. Treat report-persistence failure as an incomplete operation record.

The primary receipt path is returned in `report_path`: a digest-bound `.execution-<digest>.json` file beside the manifest, exclusively claimed before mutation. A fresh audit changes the digest; the prior receipt remains preserved. It binds the source manifest digest and filesystem. Persist candidate intent before dispatch and outcomes afterward. Reserve the full candidate allocation at dispatch and retain it for partial/unknown effects. Results distinguish `in_progress`, `removed`, `skipped_before_mutation`, `partially_removed`, `failed_unknown_effect` and `not_attempted`. Operation state is `started`, `complete` or `reconciliation_required`.

An existing execution receipt prevents replay. Inspect its last durable state and current resource identity, reconcile any uncertain effect, then create fresh audit evidence before a new authorized application. Never delete the receipt to bypass this protection. Recovery of deleted contents is a separate owner operation; it is not accomplished by reverting code.

## Workspace leases

Record workspace/repository IDs, canonical path, task/session ID, process group, creation time, heartbeat, intended lifetime, Git ref, and cleanup policy at creation. An expired lease creates an orphan candidate; dirtiness, unique history, live handles, and locks retain veto power.
