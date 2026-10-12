# Install personal skills in a cloud environment

Keep this library in its own repository. Install complete skill directories into the cloud agent's user skill directory, without adding personal skills to the application repository.

The installer uses Python 3's standard library, reads the local checkout, and performs no network access. The checkout step below needs Git, network access to GitHub, and a writable source directory. Skill dependencies such as compilers, browser engines, MCP servers, corpus backends, or provider CLIs need separate setup.

## Pin and save the setup

Publish or merge the library changes first. Select the full 40-character Git commit you reviewed. Configure `SIFTABLE_SKILLS_COMMIT` with that exact commit in the environment settings; a branch name or `HEAD` will be rejected. Do not put credentials in the script.

Append the following block to your existing **setup script**. Keep the existing build, dependency, Zig, and OCR settings. Add the same block to the environment's **maintenance script** so a task restored from a cached environment also checks and restores the skills. This block works with both an existing pinned source cache and an empty cache.

```bash
set -euo pipefail

: "${SIFTABLE_SKILLS_COMMIT:?Set this to the full reviewed 40-character commit}"
if [[ ! "$SIFTABLE_SKILLS_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  printf '%s\n' 'The skill library requires a full immutable Git commit.' >&2
  exit 1
fi

skills_repo_url='https://github.com/Tom-R-Main/siftable-skills.git'
skills_cache_root="${SIFTABLE_SKILLS_CACHE_ROOT:-$HOME/.cache/siftable-skills}"
skills_checkout="$skills_cache_root/$SIFTABLE_SKILLS_COMMIT"
skills_destination="${SIFTABLE_SKILLS_DESTINATION:-$HOME/.agents/skills}"

if [[ ! -e "$skills_checkout" ]]; then
  mkdir -p "$(dirname "$skills_checkout")"
  git clone "$skills_repo_url" "$skills_checkout"
fi

[[ ! -L "$skills_checkout" ]] || exit 1
[[ "$(git -C "$skills_checkout" remote get-url origin)" == "$skills_repo_url" ]] || exit 1
skills_checkout_status="$(git -C "$skills_checkout" status --porcelain)" || exit 1
[[ -z "$skills_checkout_status" ]] || exit 1
if ! git -C "$skills_checkout" cat-file -e "$SIFTABLE_SKILLS_COMMIT^{commit}" 2>/dev/null; then
  git -C "$skills_checkout" fetch --no-tags origin "$SIFTABLE_SKILLS_COMMIT"
fi
if [[ "$(git -C "$skills_checkout" rev-parse HEAD 2>/dev/null || true)" != "$SIFTABLE_SKILLS_COMMIT" ]]; then
  git -C "$skills_checkout" checkout --detach "$SIFTABLE_SKILLS_COMMIT"
fi
[[ "$(git -C "$skills_checkout" rev-parse HEAD)" == "$SIFTABLE_SKILLS_COMMIT" ]] || exit 1
skills_checkout_status="$(git -C "$skills_checkout" status --porcelain)" || exit 1
[[ -z "$skills_checkout_status" ]] || exit 1

python3 "$skills_checkout/scripts/validate_repo.py"
python3 "$skills_checkout/scripts/install_skills.py" \
  --destination "$skills_destination" --apply --update
python3 "$skills_checkout/scripts/validate_repo.py" \
  --skills-root "$skills_destination"
```

Run the block under Bash. If the environment runs another shell, wrap it in `bash` or save it as a Bash script. The repository URL contains no authentication material; if GitHub access requires login, configure that access separately through the environment's supported credential mechanism.

The optional `SIFTABLE_SKILLS_CACHE_ROOT` and `SIFTABLE_SKILLS_DESTINATION` settings override the source cache and installed skill directories. Their defaults are shown above. Configure the harness to discover the selected destination.

The installer defaults to all skills. To use a smaller library, add `--profile engineering`, `--profile languages`, or repeated `--skill NAME` arguments to the installation command in both scripts. Explicit sibling resource links determine the complete dependency closure. Changing a selection does not remove skills installed by an earlier selection.

## Migrate the earlier ZIP installation

Skills copied by the earlier ZIP installer do not have this installer's management manifest. This installer refuses to adopt or replace them, even when a directory has identical contents. It also refuses to overwrite any managed skill changed after installation.

Use a fresh environment whose user skill directory is empty, or configure the harness to discover a new, empty user skill directory and pass that exact path as `--destination`. If the harness requires the existing directory, review and relocate the conflicting directories under your normal approval process before installing. Keep any local changes. Do not delete the whole skills directory or replace its contents in bulk.

The manifest `.siftable-skills.json` stores package hashes in the destination root. Preserve it along with the skill directories when caching the environment. The installer hashes complete package contents and executable bits, verifies installed files, and applies `--update` only when the previous installed hash still matches. Cache files such as `__pycache__` are excluded.

## Recover an interrupted update

Complete skill directories are staged before replacement. If an ordinary error occurs during replacement, the installer rolls the changes back. If a process is killed, the next installation stops when it finds `.siftable-skills-transaction`.

Inspect that directory and ensure no installer is still running. Use the reviewed checkout's installer to recover:

```bash
python3 "$skills_checkout/scripts/install_skills.py" \
  --destination "$skills_destination" --recover --apply
```

Recovery checks current package and backup hashes, then restores the previous version, or finishes cleanup after a verified commit. If files changed after interruption, it stops and preserves the transaction for manual review. Do not run concurrent installers or recovery commands against one destination.

## Verify a fresh task

Save the updated setup and maintenance scripts, then publish the environment through its settings UI. Start a fresh cloud task and verify:

1. The cached checkout's `git rev-parse HEAD` equals the selected commit.
2. The installed user directory contains `tometo-mode/SKILL.md`, `zig/SKILL.md`, `typescript/SKILL.md`, and `rust/SKILL.md`.
3. `validate_repo.py --skills-root` passes for the installed tree.
4. The harness discovers the skills: explicitly invoke `$tometo-mode` and a language skill in a bounded task, and check which instructions it reads.
5. A second fresh task restored from cache repeats the maintenance check successfully.

Filesystem installation does not prove discovery by a particular harness. This repository does not publish cloud environments or change your saved settings. Publication, fresh-task discovery, and cache restoration must be checked in the selected cloud environment.
