# Git worktree lifecycle

Use Git as the authority for worktree identity and administration.

## Discovery

```bash
git -C <repo> worktree list --porcelain -z
```

The porcelain format is stable for scripts and `-z` safely represents unusual paths. Record path, HEAD, branch/detached state, locked state, and prunable/missing state. Do not infer worktrees from directory names or remote branch lists.

## Representation evidence

Classify the checked-out HEAD against a protected base with deterministic Git operations:

- `exact_ancestor`: `git merge-base --is-ancestor <head> <base>` succeeds.
- `tree_equivalent`: `git diff --quiet <base> <head>` proves identical tracked trees.
- `patch_equivalent`: `git cherry <base> <head>` returns no unique `+` patch.
- `unique`: none of the above was proved.

Accept only the first three for automatic `safe_now`. Treat failed commands or uncertain equivalence as `unknown`; treat a proved unique patch as `retain`. Ancestry alone misses squash merges, while cleanliness alone says nothing about unique commits.

## Safe retirement test

Require all of the following:

1. Linked checkout, not the main worktree.
2. Existing, canonical, non-symlink path beneath the frozen boundary.
3. Not locked and no nested mount or cross-device traversal.
4. No external CWD, open handle, owner session, or current Codex task root.
5. Empty `git status --porcelain=v1 -z --untracked-files=all`.
6. Recoverable HEAD and deterministic representation evidence.
7. Unchanged path, identity, HEAD, status, liveness, and representation immediately before removal.

Apply-time revalidation must inspect only the selected worktree plus the repository's lightweight registration metadata. Do not rescan or resize sibling worktrees. Run identity, boundary, registration, HEAD, status, and representation checks first; take the liveness snapshot last, immediately before removal.

Treat a Codex task root as a reference when that root is the selected worktree or lies beneath it. A task rooted at an ancestor checkout does not by itself reference a nested linked worktree; require the nested worktree's own task root, CWD, or open handle.

## Mutation

```bash
git -C <repo> worktree remove -- <exact-path>
```

Do not fall back to `--force`. Do not delete the local branch. For a missing path, inspect `git worktree prune --dry-run --verbose`; prune stale administration separately and never treat it as meaningful disk recovery.

Use `git worktree lock --reason <reason> <path>` for intentionally retained worktrees. A lock is a veto.

## Creation and prevention

Let ordinary `git worktree add` own Git semantics. A same-volume APFS CoW adapter may optimize materialization through `git worktree add --no-checkout`, `clonefile(2)`, index reconciliation, Git reset, and untracked cleanup only when its result is equivalent to ordinary creation.

CoW does not prevent per-worktree `node_modules`, Cargo `target`, Zig cache, or other generated growth. Track task ownership and retirement independently.

## Sources

- Git worktree manual: https://git-scm.com/docs/git-worktree
- Grovr: https://github.com/j1king/grovr
- APFS CoW worktree hook: https://github.com/palmin/claude-cow-worktree
