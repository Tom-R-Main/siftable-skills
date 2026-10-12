---
name: go
description: Implement, review, debug, test, migrate, and optimize Go. Use for Go code, modules, and workspaces with the selected toolchain and repository build contract.
---

# Go

Resolve `GO_SKILL_DIR` to the absolute directory containing this loaded `SKILL.md`.
Run its scripts from the target repository root.

Work from the repository's actual Go contract. The selected toolchain, active
workspace, build driver, generated-code policy, target matrix, nearby code, and
diagnostics outrank remembered APIs and generic style rules.

## Workflow

### 1. Establish the build contract

Inspect before editing or running broad commands:

```sh
git rev-parse --show-toplevel
GOTOOLCHAIN=local go version
GOTOOLCHAIN=local go env GOVERSION GOROOT GOMOD GOWORK GOOS GOARCH CGO_ENABLED GOEXPERIMENT
rg -n '^(go|toolchain|module|use|replace|exclude|retract)[[:space:](]' -g 'go.mod' -g 'go.work' .
rg -n '^//go:build|^//go:generate' -g '*.go' .
```

Read relevant `AGENTS.md` and contributor guidance, then inspect `go.mod`,
`go.work`, `.go-version`, build scripts, lint configuration, generation rules,
and CI. Determine:

- module and workspace scope;
- minimum, preferred, and CI Go versions;
- the repository's focused test and verification commands;
- build tags, GOOS/GOARCH, CGO, experiments, and privileged requirements;
- generated or vendored artifacts and their supported update procedure.

Keep these distinctions explicit:

- A `go` directive sets a minimum toolchain and package language version; a
  `toolchain` directive names a preferred toolchain. `.go-version`, CI, and
  containers may select stricter development or release versions.
- `GOTOOLCHAIN=auto` may download a toolchain. Use `GOTOOLCHAIN=local` for
  discovery until network access is permitted, and use `go list -m` to force a
  module/workspace compatibility check.
- `GOWORK` is directory-sensitive and may include modules outside the
  repository. Do not edit or test external modules unless they are in scope.
- Make, Task, Just, Mage, Bazel, repository scripts, and the Go source tree's
  own scripts may encode tags, generation, tools, and target selection. Inspect
  recipes before running them; a benign target name does not prove it is
  read-only.
- Do not run `go mod tidy`, `go work sync`, `go generate`, `go fix`, vendoring,
  code generation, tool installation, or formatter write mode without scope
  and mutation authority.

For module resolution, toolchains, workspaces, dependencies, build tags, and
generators, read [references/go-modules-toolchains-builds.md](references/go-modules-toolchains-builds.md).

### 2. Load only the relevant guidance

- Package/API design, interfaces, zero values, ownership, generics, and errors:
  [references/go-design-packages-errors.md](references/go-design-packages-errors.md)
- Context, goroutine lifecycle, channels, locks, atomics, the memory model,
  race testing, and `testing/synctest`:
  [references/go-concurrency-context-memory.md](references/go-concurrency-context-memory.md)
- Regression tests, subtests, parallelism, integration tests, fuzzing,
  coverage, caching, and flakes:
  [references/go-testing-fuzzing.md](references/go-testing-fuzzing.md)
- Unsafe pointers, CGO, ABI, cross-compilation, OS/architecture behavior,
  eBPF, and privileged testing:
  [references/go-unsafe-cgo-platforms.md](references/go-unsafe-cgo-platforms.md)
- Benchmarks, `benchstat`, pprof, trace, allocations, GC, and PGO:
  [references/go-performance-profiling.md](references/go-performance-profiling.md)
- Go-version changes and modernization:
  [references/go-version-migrations.md](references/go-version-migrations.md)

Open only the references needed for the task. Verify version-gated claims
against the selected toolchain's documentation, release notes, and source.
Effective Go is useful for core idioms, but it does not cover modules, generics,
or all newer library and tooling behavior.

### 3. Make the narrow change

- Read the relevant implementation, tests, callers, interfaces, and recent
  history. Search all consumers before changing public or shared behavior.
- For a bug, first add or identify a focused regression test and observe the
  failure when reproducible; then implement the smallest correction and observe
  the test pass. State when the original failure cannot be reproduced locally.
- Do not bundle dependency updates, modernization, renames, or cleanup with an
  unrelated fix.
- Use `gopls` for semantic navigation, diagnostics, and refactors when
  available. Prefer compiler, analyzer, race, fuzz, benchmark, or repository
  evidence to model-only reasoning.
- Comments should preserve contracts, invariants, ownership, cancellation,
  compatibility constraints, and non-obvious causality—not narrate syntax.
- Keep independently correct changes reviewable. Each logical commit should
  compile and pass its relevant gates unless an explicitly reviewed failing
  regression-test commit precedes the fix.

At boundaries, make these decisions explicit:

- who may mutate, retain, copy, concurrently access, close, or reuse values and
  resources;
- whether zero values are useful or constructors enforce required invariants;
- whether errors remain inspectable through wrapping or are translated at the
  boundary;
- who owns each goroutine and channel, how work is bounded, how cancellation is
  observed, and how completion is joined;
- which exported behavior, error identity, wire format, CLI output, metric, or
  ordering property is a compatibility commitment.

### 4. Validate in a feedback loop

Use the repository's narrowest applicable validation command after inspecting
its recipe. For ordinary module-native repositories without a custom driver,
run the bundled helper from the target package or module:

```sh
"$GO_SKILL_DIR/scripts/go-gates.sh"
```

The helper requires POSIX `sh`, Python 3, Git, `go`, and `gofmt`; a configured
`golangci-lint` is optional but must already be installed. It defaults to no
network and no mutation, blocks automatic toolchain downloads, ignores external
workspace modules, and refuses direct gates when it detects a repository build
driver. Run it with `--help` to inspect focused-package, race, network, module,
and driver options. Use `--force-direct` only after deciding the repository's
driver is not the right validation path.

Run a focused test first, then broaden only as required. Depending on the
change, add the relevant lanes:

- `-count=1`, repeated runs, or `-shuffle=on` for cache, order, or flake issues;
- `go test -race` on supported targets for exercised concurrent behavior;
- one bounded fuzz target, with its seed corpus still covered by normal tests;
- integration, service, CLI, CGO, privileged, or target-specific checks;
- repeated comparable benchmarks and `benchstat` for performance claims;
- vulnerability analysis when repository policy requires it and its database
  and network requirements are permitted.

When a gate fails, distinguish code failure from missing cache, unavailable
toolchain, unsupported target, absent service, permission, or network policy.
Fix in-scope code failures and rerun the focused gate until it passes; then run
the broader required gate. Stop and report environmental or authorization
limits rather than weakening the check or silently changing scope.

### 5. Report evidence

For behavioral work, report:

- observed behavior and root cause;
- the smallest correction and preserved invariants;
- focused and broad validation performed;
- behavior intentionally unchanged;
- required lanes not run and why;
- remaining uncertainty.

Concurrency changes also need a lifecycle and happens-before argument.
Performance changes need comparable measurements, workload details, toolchain
and target information, sample counts, and correctness evidence.
