# Safety invariants

Read this before executing a deletion manifest.

## Hard vetoes

Never delete or mutate a candidate when any of these holds:

- candidate is outside the authorized goal or manifest scope;
- canonical path is outside its approved root or equals the approved root;
- canonical path, device, inode, link count, mount identity, or expected kind changed;
- scan was truncated, interrupted, permission-denied, or missing a required tool;
- recursive traversal would cross a device, descend into a mount, or follow a symlink;
- external process CWD, open handle, current Codex task root, or owner process references it;
- Git worktree is main, dirty, locked, missing, unique, or lacks rigorous representation proof;
- path contains credentials, environment secrets, browser authentication, mail, photos, documents, database/container writable state, or unknown app state;
- recovery is speculative or depends on an unavailable source;
- candidate was discovered after the authorization scope was frozen.

## Observer-induced liveness

Record the audit/executor PID, process group, and exact instrumentation PID set before discovery. Finish metadata probes, then take the liveness snapshot. Exclude only those known observer PIDs from evidence. Never ignore a process merely because its name resembles the checker.

Repeat the snapshot immediately before each action. A new external reference changes the candidate to `safe_after_active_thread_closeout` or `unknown`.

## Authorization boundary

An audit-only request never authorizes deletion. A manifest approval authorizes only the named IDs or paths. A mutation goal authorizes only `safe_now` candidates within its explicit resource classes, roots/repositories, target, and exclusions.

Do not require a redundant user confirmation when a current explicit goal already authorizes the exact action. Do not stretch that goal to branches, history, containers, volumes, user state, or newly discovered paths.

## Safe executor properties

- Accept exact IDs only; provide no wildcard or implicit-all switch.
- Verify manifest integrity and freshness.
- Freeze selected order, allocated-byte total, target, and risk ceiling before mutation.
- Reject changed identity, boundaries, liveness, owner state, or incomplete evidence.
- Use owner operations when available; give generic recursion the weakest authority.
- Preserve Git refs when retiring a checkout.
- Stop at target, risk ceiling, or approved-set exhaustion.
- Verify absence and fresh free bytes after each lane.
- Leave failures in place; never escalate to force or a riskier adapter automatically.

## Recovery levels

- `exact`: retained Git ref, immutable source, or supported owner restore operation reproduces the resource.
- `regenerable`: deterministic source and a documented build/install command exist; rebuild may cost time or network.
- `recreated_by_owner`: the application recreates the cache, but not exact user history.
- `none_or_unknown`: retain.

Recoverability never overrides liveness, unique state, or an authorization boundary.
