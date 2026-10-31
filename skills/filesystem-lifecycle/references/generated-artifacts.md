# Generated artifacts

## Classification

Recognize artifact paths and project markers for inventory:

- Node: `node_modules` plus `package.json` or a package-manager lockfile.
- Cargo: `target` plus `Cargo.toml`.
- Zig: `.zig-cache` or `zig-cache` plus `build.zig` or `build.zig.zon`.
- Python: `.venv` plus `pyproject.toml`, requirements, lockfile, or `Pipfile`.

A marker or lockfile starts qualification. The adapter checks the installed layout, retained recovery inputs and relevant local-source references. Supported Node and Python environments can qualify; Cargo and Zig outputs do not require a dependency-free project or a clean parent checkout. Unsupported formats get a specific missing-evidence reason, not a class-wide prohibition.

Recovery means the useful resource can be installed or built again from retained inputs. Network downloads, native compilation and changed build bytes are costs, not automatic safety failures. Do not require an offline rebuild or perform an installation merely to classify a disposable tree. Missing local/private inputs, ambiguous installed edits or user state still block removal.

Before `safe_now`, prove the subtree has no Git-tracked files, no external process/session reference, no symlink target traversal, no nested mount, and a documented rebuild path.

Current recovery adapters inspect:

| Resource | Retained inputs and owner evidence |
|---|---|
| npm `node_modules` | Matching root/workspace specifications and v2/v3 package-lock, installed package records, package metadata, retained local dependencies |
| Cargo `target` | Cargo manifests and source, local/workspace inputs, Cargo cache tag and compiler records |
| Zig `.zig-cache` / `zig-cache` | Retained build specification, local package inputs, manifest/object cache layout |
| Python `.venv` | Environment configuration, requirements or uv specification, installed distribution metadata and retained local/editable inputs |

Other package-manager formats need their own parser and tests. Report the unsupported format and continue supported resources; do not infer that all dependency environments are ineligible.

For npm workspaces, resolve nested workspace installations through the retained root lock and installed lock; workspace source records such as `apps/mobile` are legitimate owner metadata, not deletion targets. Local source links must resolve outside the dependency installation.

Use repeatable `--npm-package-name <exact-package-or-scope>` with `--npm-package-units` to bound a large installation audit to selected package directories. Scope children can qualify independently when their namespace contains unowned or sensitive siblings. This narrows discovery only; names never confer eligibility or bypass owner/liveness checks. Whole-installation candidates remain independently assessed, and a qualified parent covers its descendants without double counting.

For urgent target-limited `--kind generated_artifact` audits, `--max-artifact-candidates N` bounds qualification work. Remaining candidates are explicitly unassessed; an unmet target stays unmet. This does not relax any selected candidate's checks. Apply a smaller exact safe tranche or continue a fresh bounded audit.

For package units, compare installed versions, sources and integrity against retained lock records for the selected subtree. A stale sibling package does not invalidate an otherwise matching unit; the stale sibling itself remains unqualified. Root/workspace specifications, all local-source recovery inputs and installation-wide liveness still apply to every unit. Preserve retained unique state before an owner reinstall: `npm ci` replaces the installation.

When sensitive or unowned entries block a whole npm installation, `audit --npm-package-units` additionally inventories exact non-symlink top-level package and scope directories. Each unit independently needs installed-lock ownership, version-matching package metadata, content screening, tracked-file absence and recovery qualification. Sensitive/unowned siblings, workspace source, `.bin`, and the installed lock remain. A handle anywhere in the installation or a CWD/task in its owning worktree protects every unit, because a running consumer may import another package later. A retained dirty source checkout does not alone prevent removing its otherwise disposable dependencies. Reinstall with `npm ci` from the retained project root; downloads and native builds may be required.
