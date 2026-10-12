# Owner adapter contract

Implement each resource class through the same lifecycle:

```text
discover()
classify()
recoverability()
liveness()
plan()
revalidate()
apply()
verify()
```

Each adapter must define its authoritative identity, unique-state test, recovery method, liveness evidence, path boundary, supported operations, and verification postcondition. Missing evidence produces `unknown`.

## Adapter authority

Prefer specialized adapters because they preserve owner semantics:

- `git_worktree`
- `generated_node`
- `generated_cargo`
- `generated_zig`
- `docker_images`
- `docker_build_cache`
- `codex_history`
- `known_app_cache`
- `generic_cache`

The generic filesystem adapter has the weakest authority. It may remove only an exact, non-symlink tree beneath a frozen root, on one device, with complete liveness and recoverability evidence. It may not reinterpret app state, Git history, containers, volumes, databases, or task history.

## Extension rule

Add an adapter when an object repeatedly remains `unknown`. Do not teach the generic adapter a growing list of exceptions. Test discovery, classification, drift rejection, apply, and verification on temporary fixtures before enabling mutation.


## Package caches

Before choosing a maintenance executable, identify the owner binaries resolved on PATH and those used by live consumers, with their cache schema or bucket versions. Different versions can share a cache root while using different schemas. A prune command that discards another version's buckets can affect its launchers; the current shell's version alone does not establish compatibility.

Treat cache inspection and mutation as separate operations. Inspect the installed implementation or authoritative versioned contract for every root the command changes, including metadata caches, temporary directories and project registrations. Check the owner's reachability rule against the filesystem: a link-count-based prune can empty a store whose installed copies are APFS clones, even though those installed copies remain intact. A prune without a read-only preview cannot provide an exact deletion list in advance. Its owner-selected scope must fit the approval; otherwise hold it. Never force through an in-use check or remove an owner's lock.

Protect cached environments and the archives they import from. Command-line paths alone miss shared libraries and later imports. Reconcile open and mapped files, working directories and owner-recorded environment links before classification. Finish observation tools such as `du` and `find` before the liveness snapshot, and exclude only the known observer process tree. Whitelist the exact owner-metadata files and formats needed for reachability, exclude credential patterns before opening them, and decode only those formats; searching arbitrary cached file bodies for archive IDs neither proves complete reachability nor respects credential boundaries. Use a neutral working directory when an inspection CLI would otherwise auto-load project environment files.

Recovery must cover the actual cached source. Keep local archives with missing originals, private or foreign sources without a verified recovery path, and malformed or unindexed entries. A successful registry availability check proves availability at check time, not future availability or matching downloaded contents.

For selective pruning, check how index aliases share content. Some exact-key commands remove content still referenced by another key. Preserve retained references and their content, and keep unindexed content unless its removal is separately qualified. A general verification or garbage-collection command may exceed a selective deletion scope.

Credential-shaped files can be packaged fixtures, but a matching filename and size do not prove that. Preserve ambiguous package units without opening their environment or key files. A blocked whole-cache operation does not authorize deleting the remaining packages or moving protected files aside.

Distinguish implementation review, live-plan qualification and post-action readback in the receipt. If a pre-apply review is required, complete it before mutation; later readback cannot stand in for it.
