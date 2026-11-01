---
name: swift
description: Implement, review, debug, test, migrate, or optimize Swift code and builds. Use for .swift files, SwiftPM and Xcode targets, Swift concurrency, SwiftUI/UIKit/AppKit, Foundation services and CLIs, public SDKs, and C/Objective-C/C++ interop.
---

# Swift

Work from the project's selected compiler, language mode, SDK, build driver,
and consumers. A recent compiler, a package's tools version, and Swift 6 language
mode are different facts. Reference code supplies mechanisms to evaluate, not
permission to replace the target project's architecture or toolchain.

## Establish the project contract

Read repository guidance, affected code and callers, tests, manifests and CI
before editing or executing project build logic. Identify:

- Application, package, SDK, command-line tool, server, or native bridge; affected
  products, targets, extensions, generated sources, and supported consumers.
- SwiftPM, Xcode workspace/project, or repository wrapper; schemes, test plans,
  configurations, platform destinations, resources and build plugins.
- Selected Swift/Xcode version, language mode per target, strict concurrency,
  default actor isolation, upcoming features, SDK and deployment minimums.
- Dependency locks, local packages, macro/plugin toolchains, native libraries,
  signing/entitlement requirements, and CI's actual verification commands.

Start with a focused inventory; include hidden CI files and project bundles:

```sh
git rev-parse --show-toplevel
rg --files --hidden -g 'AGENTS.md' -g 'Package*.swift' -g 'Package.resolved' \
  -g '*.pbxproj' -g '*.xcworkspacedata' -g '*.xcscheme' -g '*.xctestplan' \
  -g '*.xcconfig' -g '.swift*' -g '.xcode-version' -g '.tool-versions' \
  -g '.github/workflows/*' -g '!**/.git/**' -g '!**/.build/**' \
  -g '!**/DerivedData/**' -g '!**/Pods/**' -g '!**/node_modules/**'
```

Read configuration selectively; avoid credentials and signing keys. A global
`swift --version` does not identify an Xcode build's selected compiler. Build
scripts, package manifests, plugins and macros can execute code; dependency
resolution can fetch even when versions are locked. Respect session permissions.
For toolchain selection, build failures or migrations, read
[builds and toolchains](references/builds-toolchains.md).

## Select focused guidance

| Concern | Reference |
| --- | --- |
| Value/reference semantics, optionals, protocols, errors, Codable, SDK compatibility | [Language and API design](references/language-api.md) |
| Actors, task owners, cancellation, continuations, streams, Swift 6 migration | [Concurrency](references/concurrency.md) |
| State lifetime, view identity, observation, platform adapters, accessibility | [Apple UI](references/apple-ui.md) |
| SwiftData/Core Data contexts, save acknowledgements, schema migration and sync | [Persistence](references/persistence.md) |
| ARC, native handles, unsafe memory, Objective-C and C++ boundaries | [Ownership and interop](references/ownership-interop.md) |
| XCTest/Swift Testing, real artifacts, sanitizers, profiling | [Testing and performance](references/testing-performance.md) |
| Transferable mechanisms and counterexamples from reference code | [Production patterns](references/production-patterns.md) |
| Research scope, pinned source identities and official technical authorities | [Sources](references/sources.md) |

## Implement against the contract

- Express meaningful states with types, validate external input at the boundary,
  and judge API clarity at call sites. Match repository conventions; do not
  introduce a protocol, dependency, macro, state framework or migration by default.
- Separate value semantics, immutability, ownership and safe concurrent access.
  A `let` binding to a class, or a struct containing references, does not make its
  reachable state immutable. `Sendable` is not permission to call any native API
  on any thread.
- Attach asynchronous work to its real owner. Prefer a suspending operation
  when the caller owns completion. Unstructured tasks need explicit cancellation,
  error observation and shutdown semantics; `Task {}` is not a child task merely
  because it appears inside another task.
- Revalidate state after suspension. Actor isolation prevents overlapping
  isolated execution, but does not make a multi-`await` workflow atomic or keep
  old results current. Preserve cancellation rather than silently converting it
  into success, a user-facing error, or a retry.
- For callbacks, define exactly-once completion, cancellation-before-registration,
  late results, underlying operation cleanup, and delegate/resource lifetime.
  Checked continuations diagnose some misuse; they do not provide this policy.
- Keep native borrows within their valid scope, pair retained ownership and
  destruction correctly, and honor execution affinity through teardown. Audit
  `@unchecked Sendable`, `nonisolated(unsafe)` and `assumeIsolated` against an
  actual invariant instead of adding them to quiet the compiler.
- Preserve source, binary, Objective-C, wire, persistence and behavior contracts
  separately. Avoid incidental dependency upgrades, generated-file edits, unsafe
  escape hatches, or snapshot re-recording that hide a failed gate.

For defects, use a focused reproducer or regression test when practical. For
reviews, trace input through the state/resource owner to the actual consumer,
including failure, cancellation and teardown. Keep read-only review harnesses
outside the target checkout and label source reasoning, model execution, and
original application execution separately.

## Verify the changed behavior

Use repository commands first, starting with the affected target and destination.
SwiftPM's `swift test` is appropriate only when its manifest owns those tests;
an iOS package or Xcode app may require a simulator, host app and test plan.
Run configured formatting/lint in check mode, appropriate consumer/API gates,
and affected platform lanes. Examples and selection details are in
[testing and performance](references/testing-performance.md).

Confirm the intended tests executed. Zero selected tests, skipped tests,
`build-for-testing`, previews and compilation alone do not prove runtime behavior.
Drive a bounded real CLI, service, UI or native consumer flow when that is the
changed contract. Report toolchain/destination, commands and observed results,
plus missing caches, tools, signing, devices or host support. Claim performance
improvements only from comparable measurements with correctness checks.
