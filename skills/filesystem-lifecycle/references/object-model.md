# Manifest object model

Use the manifest as frozen evidence, not deletion authority. Record the authorization envelope separately from classification.

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

## Workspace leases

Record workspace/repository IDs, canonical path, task/session ID, process group, creation time, heartbeat, intended lifetime, Git ref, and cleanup policy at creation. An expired lease creates an orphan candidate; dirtiness, unique history, live handles, and locks retain veto power.
