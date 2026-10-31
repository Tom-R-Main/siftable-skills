# Verification and maintenance

Maintain this package in its reviewed source checkout and preserve a recoverable baseline before editing. Do not modify plugin caches or global policy to activate it.

## Commands

Use Python 3.11 or newer and Git for the fixture suite. No package installation is required.

```bash
python3 -B scripts/fs_lifecycle.py self-test
python3 -B scripts/fs_lifecycle.py --help
```

Run these from the skill directory. `self-test` discovers the bundled standard-library tests. Tests create and remove their own temporary fixtures; they never run a live cleanup. Optional platform/tool tests use controlled probe fixtures unless specifically recorded as live observations.

## Safety qualification

Use standard-library tests and temporary fixtures. Never exercise deletion against live project dependencies, caches, worktrees or personal data to prove executor correctness.

Required cases include wrong filesystem; authorization expansion; invalid/stale/future records; incomplete liveness; owner appearing after audit; Git inspection failure; missing recovery evidence; overlapping candidates; symlink replacement; injected failure after a successful unlink; unavailable receipt storage; and interruption before an outcome record. Assert preservation of outside sentinel files and honest partial/unknown result states.

Qualification also requires successful reclamation cases. Exercise ordinary supported dependency environments, builds with dependencies and dirty retained source, and disposable owner cache layouts. At least one generated-output fixture must pass audit, selection, revalidation and apply, with the output absent and source unchanged afterward. A suite containing only refusals does not demonstrate a working cleanup skill. Keep platform liveness mocks explicit.

Exercise the public CLI for doctor, reports, comparison and observation. Verify missing tools, partial coverage, explicit output, malformed inputs and observation-only command allowlists. A mocked platform probe proves parsing and control flow, not live platform support.

## Performance and evidence

Benchmark fixed temporary trees with explicit entry/time/depth limits. Record wall time, peak memory when available, visited entries and subprocess counts. Establish the baseline before setting regression thresholds. Cancellation and partial output are correctness cases.

Bind evidence to a digest of the checked source files. Record the exact commands, result and remaining limitations. A macOS run does not qualify Linux mount behavior; Linux fixtures do not prove live APFS accounting. Report platform qualification separately.

## Migration

Older records may be read for reporting and comparison. Mutation requires the current manifest and selection schemas and a fresh audit; do not add authority or missing evidence by silently migrating an old deletion manifest. New diagnostics and catalog entries are inventory-only until their mutation adapter has independent qualification.

On interrupted mutation, inspect the durable receipt and current resource state before any retry. Restoring an older executable does not reverse a deletion. Rebuild/owner recovery is separate from code rollback.
