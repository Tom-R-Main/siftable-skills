# Go version and modernization workflow

This is a routing checklist, not a substitute for the selected target's release
notes and source.

## Contents

- Authority order and migration sequence
- Version-scoped feature landmarks
- Modernization decisions
- Validation matrix

## Authority order

For a version migration, use:

1. repository support policy, selected `.go-version`/CI/container, and release
   process;
2. the target version's official release notes and compatibility notes;
3. `go`, `toolchain`, and workspace directives;
4. selected toolchain diagnostics, `go fix`, vet/analyzers, and standard-library
   docs/source;
5. nearby code and dependency minimum-Go requirements.

Do not suggest "upgrade to latest" during unrelated work. A version migration
changes developer environments, CI, containers, module selection, generated
output, dependencies, and supported users.

## Migration sequence

1. Inventory every module/workspace, toolchain file, CI image/action, container,
   release builder, generator, linter, and target matrix.
2. Determine the current minimum supported Go version separately from the
   preferred development and release versions.
3. Read every intervening official release note, especially language changes,
   standard-library behavior, toolchain/module changes, runtime changes, and
   ports removed or added.
4. Check direct dependencies' `go` requirements and tool compatibility.
5. Update the repository's canonical version source through its supported
   script; synchronize derived files rather than hand-editing them.
6. Run formatting/generation only when required and review generated diffs.
7. Run focused tests, all module/workspace gates, minimum-version CI, race and
   target lanes, integration/e2e, and representative runtime flows.
8. Apply optional modernizations separately from the minimum version bump unless
   they are required for compatibility.
9. Document user/developer impact, rollback, and release/backport policy.

## Version-scoped feature landmarks

Verify each against the exact target release notes before use.

### Go 1.21

- `min`, `max`, and `clear` built-ins.
- standard `slices`, `maps`, and `cmp` packages; structured `log/slog`.
- `sync.OnceFunc`, `OnceValue`, and `OnceValues`.
- toolchain selection through `go`/`toolchain` directives became part of normal
  Go command operation.
- PGO became ready for broader production use, but remains workload-dependent.

### Go 1.22

- Each iteration of an ordinary `for` range in modules using Go 1.22+ gets new
  iteration variables, changing the classic closure-capture trap.
- Range over integers.
- `math/rand/v2` and other library additions.

Do not delete compatibility copies in code whose module language version remains
older merely because the host compiler is newer.

### Go 1.23

- Range-over-function iterator support and iterator helpers in standard
  collection packages.
- Timer/ticker channel and GC behavior changed; re-read `time.Timer` docs before
  preserving older stop/drain/reset recipes mechanically.
- New standard packages/APIs may replace local helpers, but adoption is a
  separate review decision.

### Go 1.24

- `testing.B.Loop` for benchmark loops.
- `testing.T.Context`/`B.Context` for test-scoped cancellation.
- `runtime.AddCleanup` and `weak` support for specialized lifetime work.
- module `tool` directives for tracking executable tool dependencies.

### Go 1.25

- `sync.WaitGroup.Go` for tracked tasks whose functions do not panic.
- stable `testing/synctest` support for deterministic concurrent/time tests.
- Use official notes for compiler/runtime/tool behavior and supported ports.

### Go 1.26

- `errors.AsType` provides generic typed error-chain inspection where its type
  constraints fit.
- Benchmark/compiler behavior around `B.Loop` and tooling continued to evolve.
- Some diagnostics remain experimental, including features gated by
  `GOEXPERIMENT`; do not encode experiments as stable defaults.

### Later releases

Read the target's official release notes and selected source. Do not infer
stable behavior from a development checkout, proposal, experiment, or tip
documentation.

## Modernization decisions

Prefer modernizations that remove a concrete bug, deprecated/removed API, local
helper made obsolete by the supported standard library, or measurable cost.

Review before applying:

- Does the module's `go` line enable the syntax and semantics?
- Is the old form intentionally retained for minimum-version consumers?
- Does replacement change allocation, ordering, nil behavior, error identity,
  randomness, serialization, or concurrency?
- Will `go fix` or an analyzer rewrite generated/vendor code or unrelated files?
- Does a dependency update carry a higher Go minimum or platform change?
- Can the change be isolated from the version bump for easier review/rollback?

Avoid proactive sweeping rewrites during feature or bug work. Mention relevant
opportunities without modifying unrelated files.

## Validation matrix

At minimum record:

- old minimum and new minimum;
- preferred and release toolchains;
- every module/workspace directive changed;
- dependency/tool upgrades forced by the move;
- OS/arch/CGO and minimum-version test coverage;
- generated/vendor changes;
- behavioral/runtime smoke tests;
- race/fuzz/benchmark evidence where relevant;
- known unsupported local lanes and CI coverage.
