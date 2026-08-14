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
