# Generated artifacts

## Classification

Require a recognized artifact path and project marker:

- Node: `node_modules` plus `package.json` or a package-manager lockfile.
- Cargo: `target` plus `Cargo.toml`.
- Zig: `.zig-cache` or `zig-cache` plus `build.zig` or `build.zig.zon`.
- Python: `.venv` plus `pyproject.toml`, requirements, lockfile, or `Pipfile`.

Before `safe_now`, prove the subtree has no Git-tracked files, no external process/session reference, no symlink target traversal, no nested mount, and a documented rebuild path.

## Dirty worktrees

A dirty or unique worktree remains retained. Its generated subtree may still qualify independently when the subtree is untracked and inactive. Never use generated-artifact cleanup to erase source, migrations, screenshots, fixtures, or design alternatives.

## Recovery and prevention

Classify exact build reproducibility separately from cost: dependency downloads, native builds, and model caches may be expensive even when disposable. State that cost.

If build output is tracked, retain it during cleanup. Fix the repository separately with an exact `git rm --cached` and ignore-rule change after reviewing repository policy.
