# Go modules, toolchains, workspaces, and build contracts

Toolchain and module behavior changes. Consult `go help`, the selected release
notes, and https://go.dev/doc/toolchain.

## Contents

- Active build and version authorities
- Workspaces and module graph
- Dependency changes and offline/vendor behavior
- Build constraints and targets
- Generators, tools, and build-driver audit

## Resolve the active build

From the directory where work will run:

```sh
GOTOOLCHAIN=local go env GOVERSION GOROOT GOMOD GOWORK GOFLAGS GOEXPERIMENT
GOTOOLCHAIN=local go version
GOTOOLCHAIN=local go list -m
```

Use specific `go env` keys rather than dumping the entire environment, which can
include private proxy configuration. `go env GOMOD` and `GOWORK` identify the
active files but do not necessarily reject an insufficient local toolchain;
`go list -m` loads module/workspace requirements and performs that check.

## Version authorities

Keep these concepts separate:

| Source | Meaning |
| --- | --- |
| `go` in `go.mod` | minimum toolchain for the module and language version for its packages |
| `go` in `go.work` | minimum toolchain for the workspace |
| `toolchain` | suggested toolchain for work in that module/workspace |
| `.go-version` or equivalent | repository/tool-manager convention, often exact development version |
| CI/container/build script | tested or required execution version(s) |
| host `go version` | bundled local toolchain before automatic selection |

Since Go 1.21, startup toolchain selection can find or download a newer
toolchain when `GOTOOLCHAIN` allows it. For read-only discovery or environments
requiring network approval, set `GOTOOLCHAIN=local` or `path` and report the
mismatch. Do not update `go` or `toolchain` directives merely to make the host
toolchain run.

The `go` directive is also a language-version boundary. New syntax or changed
language semantics must be supported by the module's `go` line, not merely the
installed compiler. Build constraints implying `go1.N` can select a newer
per-file language version under documented rules; use deliberately.

## Workspaces

`go.work` makes each listed module a main module for workspace commands. It may
contain relative or absolute paths, including paths outside the repository.

- Check `GOWORK`; `GOWORK=off` disables workspace discovery.
- Run package patterns from each intended module when complete workspace
  coverage matters. `./...` is relative to the current directory and does not
  automatically mean every module in every layout.
- Do not include external workspace modules in a task merely because `go.work`
  references them.
- `go work sync`, `go work use`, and workspace vendoring mutate files or module
  requirements. Use the repository's update command and review the diff.
- A committed workspace is project policy. An uncommitted personal workspace
  can change resolution unexpectedly; report it before relying on results.

Read a workspace without rewriting it:

```sh
go work edit -json
```

## Module graph and MVS

Go uses Minimal Version Selection: the selected version of a module is the
maximum required version in the build list, not a general SAT solver result.

Useful read-oriented commands:

```sh
go list -m all
go list -m -json module/path
go mod graph
go mod why -m module/path
go mod why package/path
go mod edit -json
```

These may need module metadata or downloads. Honor network policy and prefer the
existing cache when offline.

`replace` changes what is actually built and may point to:

- another module version;
- a fork under a different path;
- a local directory; or
- several local modules in a monorepo.

Inspect the resolved source rather than trusting public docs for the unreplaced
module. `exclude` and `retract` also affect selection and release behavior.

## Dependency changes

Adding, upgrading, downgrading, or removing a dependency is an API, supply-chain,
license, binary-size, maintenance, and reproducibility decision.

Before changing dependencies:

- ask whether the standard library or an existing dependency already provides
  the capability;
- inspect the repository's dependency policy and update tooling;
- check the selected source, license, maintenance, supported Go versions,
  platform/CGO requirements, advisories, and transitive graph;
- distinguish module versions from package import paths and major-version
  suffixes;
- avoid `@latest` for committed tool dependencies unless repository policy
  explicitly uses it.

`go get`, `go mod tidy`, `go mod vendor`, `go work sync`, and toolchain directive
updates mutate files. A dependency-change request normally authorizes the
necessary scoped module edits, but not unrelated upgrades across a workspace.
Review `go.mod`, `go.sum`, workspace, vendor, generated output, and binary/API
effects.

`go mod tidy -diff` can provide a read-only tidy check on toolchains that support
it, but it still loads packages across tags according to tidy's rules and may
need downloads. Prefer a repository verification target when present.

## Vendoring and offline work

When vendor mode applies, builds may resolve from `vendor/` instead of the
module cache. Determine whether the repository commits and verifies vendor
content.

- Do not edit vendored code directly unless the repository explicitly patches
  it that way.
- Do not run `go mod vendor` or workspace vendoring as a harmless check; it
  rewrites a large tree.
- `GOPROXY=off` prevents module network access while allowing cached modules.
  It fails if required content is absent; report that as an unchecked gate, not
  a code failure.
- `go mod verify` checks downloaded module content against recorded hashes. It
  does not perform vulnerability, reachability, license, or maintenance review.

## Build constraints and targets

File selection can depend on:

- `//go:build` expressions;
- `_GOOS.go`, `_GOARCH.go`, and combined suffixes;
- CGO and custom tags;
- filename/package conventions for tests;
- environment such as `GOEXPERIMENT` or repository flags.

Build constraints must appear near the file header in the form required by the
selected Go version. Use `go list -json` to see selected, ignored, C, and CGO
files for the actual configuration:

```sh
go list -json ./path/to/pkg
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go test ./path/to/pkg
```

Cross-compiling a package does not execute its tests. Use compile-only checks or
the repository's target runner, then run on the target where behavior matters.

## Generators and tools

`go generate` is an explicit source-generation mechanism; it is not run by
`go build` or `go test` automatically. Repositories often wrap it to pin tools,
set tags, post-process output, and verify clean diffs.

- Read `//go:generate` directives and the wrapper before running them.
- Generated headers identify outputs but do not prove regeneration is safe.
- Tool binaries may be tracked through a tools module, Go 1.24+ `tool`
  directives, vendor content, containers, or scripts. Use the pinned mechanism.
- Generators execute code and may access the network or external programs.
- After authorized generation, inspect the full diff and run the repository's
  stale-generated-file check.

## Build-driver audit

Before running a Make/Task/Just/Mage/script target, inspect:

- prerequisites and recursive targets;
- formatting or generation in test/build prerequisites;
- tool installation or `go run ...@version`;
- container pulls, services, or privileged commands;
- environment resets, tags, and CGO;
- cleanup targets that delete artifacts;
- whether a narrow package selector exists.

Use the driver because it is the contract, but do not infer mutation authority
from a benign target name.
