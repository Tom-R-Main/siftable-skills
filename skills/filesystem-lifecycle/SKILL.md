---
name: filesystem-lifecycle
description: Audit, classify, reclaim, and prevent regrowth of local filesystem cruft and agent-workspace storage. Use when asked what consumes disk, what can be safely deleted, to recover a target amount of space, to inspect or retire Git/Codex worktrees, to clean generated artifacts or inactive app caches, or to diagnose recurring storage growth on macOS or Linux. Protect active sessions, processes, dirty or unique Git work, credentials, user documents, databases, and ambiguous paths; default to a read-only manifest unless the user explicitly requested bounded mutation.
---

# Filesystem Lifecycle

Manage filesystem lifecycle as evidence-based resource retirement. Paths identify resources; they do not prove ownership. Age and size are signals, not deletion authority. Preserve the semantics of the owning system during every destructive action.

Resolve bundled paths from the directory containing this `SKILL.md`. Use the standard-library helper at `scripts/fs_lifecycle.py`; it defaults to read-only operation.

## Select the mode

- **AUDIT:** inventory and emit a deletion manifest. Never mutate.
- **RECLAIM:** execute `safe_now` candidates inside a frozen authorization scope and candidate budget; stop at the target or when that set is exhausted.
- **WORKTREE RETIRE:** remove a verified-redundant linked checkout while preserving branch refs and unique history.
- **DOCTOR:** diagnose stale registrations, active references, duplicate artifacts, and recurring growth.
- **PREVENT:** recommend ownership leases, ignore rules, cache budgets, or CoW worktree creation based on the cause.

Default to AUDIT unless the user explicitly requested mutation. Support two authorization patterns:

- **Manifest authorization:** audit first; the user then approves exact IDs or paths.
- **Goal authorization:** a request such as “safely clear 30 GiB from generated cruft and dead worktrees” authorizes mutation only within that stated envelope and the `safe_now` policy.

Do not infer branch deletion, history deletion, container or volume deletion, user-data deletion, or newly discovered out-of-scope candidates from a general cleanup request.

## Run the safety kernel

1. **Discover:** record the target volume, exact roots, registered worktrees, owner metadata, and the observer PID/process group. Keep each recursive root on its starting filesystem.
2. **Quiesce probes:** finish metadata traversal before taking the liveness snapshot.
3. **Observe liveness:** record external process CWDs, open handles, owner processes, and current Codex task roots. Exclude only the known audit/executor PID tree.
4. **Freeze:** write an integrity-protected manifest with path boundaries, identity, storage evidence, recovery, references, classification, action, overlap, and authorization scope.
5. **Classify:** use only `safe_now`, `safe_after_active_thread_closeout`, `retain`, or `unknown`.
6. **Plan:** show exact paths and owner actions. Do not add overlapping or hardlinked apparent sizes.
7. **Authorize:** use the existing bounded goal authorization or obtain manifest authorization. Never expand either one silently.
8. **Revalidate:** rerun every destructive precondition immediately before each action. Treat drift, truncation, permission errors, unavailable tools, or unexpected mounts as `unknown`.
9. **Apply:** use the owning system's operation. Give the generic filesystem adapter the weakest deletion authority.
10. **Verify:** prove target absence, preserved refs/dependencies, healthy active services, and fresh target-volume free bytes.
11. **Prevent:** identify the source of regrowth and recommend the smallest durable fix.

Never skip freeze-and-revalidate. Concurrent agents can create worktrees, acquire handles, or consume newly freed space during the run.

Keep apply-time revalidation candidate-local. Do not rerun broad discovery or storage sizing inside the selected-candidate loop. Complete identity, boundary, and owner-state checks first; then take the fresh liveness snapshot immediately before the owner action. Emit per-candidate progress and phase timings for any batch.

Scope Codex task roots through the resource owner's workspace. A task rooted in one Git worktree protects that worktree's generated artifacts, but it does not automatically claim nested or sibling worktrees merely because their paths share an ancestor. Exact task roots, descendant task roots, CWDs, and open handles remain vetoes.

## Produce the audit manifest

Start with bounded roots. Do not recursively scan `/`, credential stores, user-document bodies, cloud-provider mounts, or backup volumes. Add another mount as its own explicit `--root`; discovery does not cross filesystems beneath a root.

```bash
SKILL_DIR="<directory-containing-this-SKILL.md>"

python3 "$SKILL_DIR/scripts/fs_lifecycle.py" audit \
  --root <projects-root> \
  --repo <repository-root> \
  --include-known-caches \
  --output /tmp/filesystem-lifecycle-manifest.json
```

For a pre-authorized reclaim goal, record its envelope in the manifest:

```bash
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" audit \
  --root <projects-root> \
  --repo <repository-root> \
  --authorization-mode goal_authorized \
  --authorization-scope 'generated artifacts and redundant linked worktrees; target 30 GiB' \
  --output /tmp/filesystem-lifecycle-manifest.json
```

For a target-driven pass, restrict the audit to the safest authorized lane and stop expensive sizing once allocated evidence covers the target plus headroom:

```bash
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" audit \
  --root <projects-root> \
  --repo <repository-root> \
  --authorization-mode goal_authorized \
  --authorization-scope 'generated artifacts only; target 30 GiB' \
  --target-gib 30 \
  --headroom-percent 25 \
  --kind generated_artifact \
  --prefer-kind generated_artifact \
  --output /tmp/filesystem-lifecycle-manifest.json
```

Target-limited audit classifies before measuring and records allocated bytes only. In the generated-artifact-only fast lane, it stops assessment after the budget is satisfied and records how many discovered paths were deliberately deferred; the manifest is intentionally partial. Omit `--target-gib` for a complete inventory with logical and allocated sizes. `--kind` restricts audited resource classes; repeat it to include more than one.

Add each relevant repository with `--repo`. Add explicitly named search roots with `--root`; keep depth bounded with `--max-depth`. Read only metadata and the minimum Codex session metadata needed to identify open task roots. Do not read document contents, environment files, keys, or credentials.

## Load references only when needed

- Before deletion or executor changes, read `references/safety-invariants.md`.
- For manifest fields and extension points, read `references/object-model.md` and `references/owner-adapters.md`.
- For Git worktrees, read `references/git-worktrees.md`.
- For dependency and build output, read `references/generated-artifacts.md`.
- For Docker, read `references/docker.md`.
- For Codex task history, read `references/codex-storage.md`.
- For macOS/APFS, read `references/macos-apfs.md`; for Linux, read `references/linux-filesystems.md`.

## Interpret classifications

- `safe_now`: inactive, recoverable, contains no unique state, stays inside the approved boundary, satisfies owner invariants, and has complete evidence.
- `safe_after_active_thread_closeout`: otherwise disposable but referenced by a live process, open handle, owner, or current Codex task root.
- `retain`: user data, main checkout, dirty/unique/locked Git state, active database or container state, tracked generated output, or a deliberately preserved resource.
- `unknown`: incomplete scan, missing tool, permission error, path/symlink/mount ambiguity, stale evidence, or no reliable owner adapter.

`unknown` never means “probably safe.”

## Prioritize reclaim lanes

Use the approved scope and prefer the lowest-risk candidates:

1. Exact caches with no live owner or handle.
2. Untracked regenerable artifacts such as `.zig-cache`, Cargo `target`, and inactive `node_modules` with project markers.
3. Clean linked worktrees proven `exact_ancestor`, `tree_equivalent`, or `patch_equivalent`, with branch/history retained.
4. Verified unused Docker images and build cache through narrow Docker operations.
5. App state or history only when the user names it and accepts the recovery tradeoff.

Protect active main dependencies even when they are regenerable. Remove a generated subtree from a retained dirty worktree only when that subtree independently passes every check.

## Select and apply a frozen candidate set

Under a recorded goal authorization, generate a read-only selection file instead of manually post-processing the manifest:

```bash
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" select \
  --manifest /tmp/filesystem-lifecycle-manifest.json \
  --output /tmp/filesystem-lifecycle-selection.json
```

Selection uses the audit target, headroom, kind restriction, and preference unless overridden. It includes only measured `safe_now` candidates, removes path/worktree overlap, freezes exact IDs and order, and fails nonzero when the safe budget is insufficient.

For manifest authorization, pass each user-approved candidate ID explicitly. The command has no wildcard or “delete everything” mode.

```bash
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" apply \
  --manifest /tmp/filesystem-lifecycle-manifest.json \
  --id artifact:abc123 \
  --id worktree:def456 \
  --authorization-source manifest_approval \
  --execute \
  --ack 'DELETE EXACT SAFE-NOW PATHS'
```

For a recorded goal authorization, apply the integrity-protected selection directly:

```bash
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" apply \
  --manifest /tmp/filesystem-lifecycle-manifest.json \
  --selection /tmp/filesystem-lifecycle-selection.json \
  --authorization-source goal_authorization \
  --execute \
  --ack 'DELETE EXACT SAFE-NOW PATHS'
```

The selection target is authoritative; an explicit `--target-gib` must match it. Optionally lower the frozen selected-set budget with `--risk-ceiling-gib`; never increase it beyond the selected candidates. A generated selection cannot stand in for explicit manifest approval.

The executor stops when the target is met, the risk ceiling is reached, or the approved set is exhausted. Concurrent writes may cause a shortfall; report it instead of escalating to new candidates or risk classes.

Apply writes a timestamped JSON report beside the manifest by default; override with `--report-output`. It reports interval and cumulative physical free-space deltas separately. Skipped candidates remain warnings, and exit status is success when the physical target was met with zero shortfall.

Do not hand-edit a candidate into `safe_now`. Regenerate the manifest.

## Owner rules

- **Git:** use `git worktree list --porcelain -z`. Separate checkout retirement from branch deletion. Never delete a branch during cleanup.
- **Generated artifacts:** require a recognized basename, project marker, no tracked files, no live reference, and a rebuild method.
- **Docker:** prefer `docker image prune` and `docker builder prune`. Never use `docker system prune`, `docker container prune`, `--volumes`, or manual `Docker.raw` deletion under generic RECLAIM.
- **Codex history:** prefer a supported Codex archive/delete/retention operation. Treat rollout files and database metadata as one logical resource; raw exact-file deletion is a last-resort, separately authorized operation.
- **Credentials and documents:** exclude them from discovery and mutation. Never open `.env`, key, vault, browser-authentication, mail, photo, or document contents to decide whether they are cruft.
- **App caches:** require an exact known path and a closed/no-handle owner. Treat snapshots and recovery state as user state unless explicitly authorized.

## Report the outcome

Lead with fresh target-volume free-space change. Then report exact actions and skips, candidate storage evidence, shortfall, preserved resources, failures or unknowns, and the likely cause of regrowth.

Never report the sum of candidate sizes as reclaimed disk space.

## Prevent regrowth

- Remove repeatedly tracked build output from the Git index in a separate repository change and add the exact ignore rule.
- Record workspace/task ownership, process group, heartbeat, lifetime, Git ref, and cleanup policy at creation. An expired lease creates a candidate, not deletion authority.
- Consider same-volume CoW worktree materialization only when it produces semantics equivalent to ordinary `git worktree add` and cleans untracked carry-over.
- Use shared package caches or explicit hydration policies for repeated dependency installs. Do not introduce mutable cross-worktree symlink coupling without project approval.
- Add a specialized owner adapter for persistent unknowns instead of broadening generic deletion rules.
