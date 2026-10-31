---
name: filesystem-lifecycle
description: Identify and reclaim inactive, recoverable filesystem resources on macOS and Linux to relieve disk pressure and keep development running. Use code-backed ownership, recovery and liveness checks for caches, generated artifacts and Git worktrees; diagnose accounting gaps and recurring growth while preserving active work and unique state.
---

# Filesystem lifecycle

The purpose is useful storage recovery: investigate what occupies space, establish what can be cleared, and execute authorized reclamation. Combine owner metadata, retained recovery inputs, content checks and liveness evidence; a path name or age alone is insufficient. Use Python 3.11+ and the standard-library CLI at `scripts/fs_lifecycle.py`, resolving paths relative to this skill directory.

## Choose the entry point

| Need | Command / mode | Authority |
|---|---|---|
| Explain disk or inode pressure | `doctor` | Bounded observation |
| Inventory removal candidates | `audit` | Read-only metadata; explicit output only |
| Review saved evidence | `report` | Reads the supplied record |
| Explain growth since a prior run | `compare` | Reads supplied inventories and receipts |
| Inspect installed Mole observations | `observe` | Optional, explicit observation operation |
| Freeze a bounded candidate set | `select` | Produces a plan, never deletes |
| Reclaim or retire a worktree | `apply` | Explicit authorized IDs/selection plus fresh checks |
| Diagnose recurring growth / PREVENT | `doctor`, `compare`, owner references | Recommend a cause-specific change; never activate it silently |

Default to observation. A current explicit bounded reclamation goal can authorize its exact safe set; otherwise obtain approval of the manifest's exact IDs or paths. Do not ask again for already-authorized actions. General cleanup does not authorize branches, history, containers, volumes, snapshots, user data, software installation, service restarts or newly discovered candidates.

Passive means user-invoked: no scheduler, background monitor, machine guard, global admission rule or automatic settings change. It does not mean audit-only when the user has authorized cleanup. A lease expiry or catalog match alone does not create deletion authority.

## Start bounded

```bash
SKILL_DIR="<directory-containing-this-SKILL.md>"
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" doctor \
  --root /absolute/project --volume /absolute/project --format markdown
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" audit \
  --root /absolute/project --repo /absolute/repository \
  --volume /absolute/project --output /explicit/output/manifest.json
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" report \
  --input /explicit/output/manifest.json --format markdown
```

Use explicitly named roots; a capacity volume is not permission to recurse through it. Never recursively scan `/`, credential stores, user-document bodies, cloud mounts or backups. Add a separate mount only as a separately authorized root. Do not read `.env`, keys, vault data, browser authentication, mail, photos or document contents. Inspect only the minimum allowlisted owner metadata. Preserve partial, inaccessible and deferred coverage; missing evidence is not zero usage.

Read [diagnostics](references/diagnostics.md) for bounded traversal, accounting and the catalog/report contract. Read [macOS/APFS](references/macos-apfs.md) or [Linux](references/linux-filesystems.md) for platform limits.

## Classify before selecting

- `safe_now`: complete evidence establishes inactivity, recovery, no unique state, owner invariants and the authorized boundary.
- `safe_after_active_thread_closeout`: otherwise disposable but referenced by a live process, open handle, owner or current task root.
- `retain`: source, user state, main checkout, dirty/unique/locked Git state, tracked outputs or a deliberately preserved resource.
- `unknown`: unavailable recovery, inspection failure, incomplete visibility, drift, ambiguity or unsupported adapter.

Discovery is broader than mutation. New catalog entries are inventory-only until qualified; existing recovery adapters can establish removal eligibility. Known-cache names, dependency lockfiles and project markers are inputs to those checks, not blanket permission or blanket exclusions. Recovery can require downloads or rebuilding; offline or bit-for-bit reproduction is not required for disposable artifacts.

Treat `unknown` as an investigation result with a concrete reason and next bounded check. Inspect the relevant owner metadata, qualify a smaller resource where supported, or identify the missing adapter. Continue other qualified candidates toward the user's target. Do not turn one unsupported cache into a ban on caches or dependency environments, and do not hand-edit classifications or bypass the executor.

Load [owner adapters](references/owner-adapters.md) before changing eligibility, [generated artifacts](references/generated-artifacts.md) for build output, [Git worktrees](references/git-worktrees.md) before retirement, [Docker](references/docker.md) for container storage, and [Codex storage](references/codex-storage.md) for task history. Prefer the resource owner's supported archive/retirement operation where one manages the checkout; do not bypass owner metadata with generic recursion.

## Freeze, revalidate, apply

Before any deletion or executor change, read [safety invariants](references/safety-invariants.md) and [object model](references/object-model.md).

1. Discover within the authorized roots and filesystem. Finish traversal before the liveness observation.
2. Freeze identity, evidence, recoverability and the machine-checkable authorization envelope. Record exact IDs, order, target and allocated-byte ceiling. Checksums detect changes; they do not authenticate human consent.
3. Select measured `safe_now` candidates without overlap. Allocated totals guide selection; they do not promise physical recovery.
4. Immediately before each action, recheck identity, mount boundary, owner/recovery state and liveness. Recheck owner-process vetoes as well as handles and CWDs. Incomplete evidence fails closed.
5. Persist operation intent before mutation. Reserve the candidate budget when dispatch starts. Use the owning operation or qualified descriptor-relative executor.
6. Persist the result, including partial or uncertain effects. Stop and reconcile uncertainty before retry. Never force through an owner lock, permission failure or unsupported primitive.
7. Verify absence, preserved owner state and fresh free bytes on the bound filesystem. Stop at target, ceiling or approved-set exhaustion.

A task in one worktree protects that workspace's generated artifacts, not every nested or sibling worktree merely sharing an ancestor. Exact/descendant task roots, CWDs, handles and owner checks still veto deletion. Protect active main dependencies even when reproducible.

For a separately authorized writer pause, identify the initial process set and detect new/changed writers; do not silently refresh the baseline to accept them. This is a scoped procedure, never a reintroduced machine guard.

Examples, only after the stated authorization exists:

```bash
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" select \
  --manifest /explicit/output/manifest.json --output /explicit/output/selection.json
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" apply \
  --manifest /explicit/output/manifest.json --id artifact:approved-id \
  --authorization-source manifest_approval --execute --ack 'DELETE EXACT SAFE-NOW PATHS'
```

A recorded goal authorization can use `--selection` with `--authorization-source goal_authorization`. A selection cannot substitute for manifest approval. Old mutation schemas require a fresh audit, not silent migration. Do not hand-edit a candidate into `safe_now`.

## Explain recurrence

```bash
python3 "$SKILL_DIR/scripts/fs_lifecycle.py" compare \
  --before /explicit/output/before.json --after /explicit/output/after.json \
  --receipt /explicit/output/apply.json --format markdown
```

Read [recurrence and observation](references/recurrence-and-observation.md) before comparison or optional Mole use. Recreated requires a successful prior removal receipt; missing from partial coverage means not assessed. Recommend the smallest evidence-supported prevention change. Do not automatically re-delete a resource or modify the skill from run history.

## Report and finish

Lead an apply report with fresh filesystem free-space change, then actions, skips, partial effects, uncertainty and shortfall. Present the compact resource table and coverage gaps for diagnosis. Never call candidate-size sums reclaimed space. Keep recoverability, recovery cost and physical reclaim confidence separate. Concurrent writes and shared blocks limit causal attribution.

When the user changes priority, stop expanding discovery, reconcile any in-flight action and record unresolved work. Validation and maintenance follow [verification](references/verification.md); tests use owned temporary fixtures, never live cleanup targets.
