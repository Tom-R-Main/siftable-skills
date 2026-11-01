# Builds and toolchains

## Resolve distinct version contracts

Read `Package.swift` as text before asking SwiftPM to evaluate it. Its
`swift-tools-version` sets the minimum tools/manifest API contract and affects
defaults; it is neither a precise compiler pin nor proof of Swift 6 language mode.
Inspect `swiftLanguageModes`, older `swiftLanguageVersions`, per-target settings,
upcoming features, and CI. Stripe's inspected manifest uses tools 6.1 with
`.v5` language mode: [source receipt](production-patterns.md#build-drivers-and-wire-contracts).

For Xcode, follow `.xcconfig` includes, project/target overrides, configuration
and scheme actions. Search narrowly for `SWIFT_VERSION`,
`SWIFT_STRICT_CONCURRENCY`, `SWIFT_DEFAULT_ACTOR_ISOLATION`, `SWIFT_UPCOMING_FEATURE_`,
`SDKROOT`, deployment targets and `OTHER_SWIFT_FLAGS`. Do not dump expanded build
settings or process environments indiscriminately; they can include secrets.

For an already selected local Apple toolchain, metadata probes include:

```sh
xcode-select -p
xcrun --find swift
xcrun swift --version
xcodebuild -version
```

Respect the session's `DEVELOPER_DIR`/toolchain selection. Use the pinned CI or
repository selector when it differs. Do not run `xcode-select --switch`, install
an SDK/runtime, or change language/isolation defaults as an incidental fix.
On Linux or another host, use the project's selected Swift distribution and
target triple; Apple frameworks and simulator destinations are unavailable there.

## Identify the driver and dependency boundary

- Read wrappers, manifest plugins, macros and generation steps before running
  them. Discovery commands such as package description evaluate build inputs;
  Xcode discovery may also resolve dependencies.
- Inspect the relevant `Package.resolved`, workspace pins, binary artifacts,
  package traits/features and local package paths. Keep dependency updates out
  of unrelated fixes.
- Locked-version flags constrain resolution; they do not prevent downloading
  missing artifacts or establish a network sandbox. Inspect the selected
  tool's help and cached state before using `--skip-update`,
  `--force-resolved-versions` or Xcode's resolution flags. If network fetches
  require approval, an absent dependency is a reported gap until authorized.
- Check `Sources`/`Tests` paths, excludes, resources, module maps and product
  membership. A source file on disk need not be part of the selected target.
- Generated Xcode projects and protocol models belong to their generator.
  Regenerate with the established command and review its diff; avoid editing
  derived files or changing project membership by assumption.

Prefer the repository runner over generic `xcodebuild` or `swift test` commands.
Ghostty's macOS wrapper first depends on its native library build; Stripe's
runner chooses schemes, test plans and simulator runtime. Those are local
contracts, not universal Swift build recipes.

## Diagnose the layer that failed

Distinguish manifest evaluation, dependency resolution, macro/plugin host
compilation, target compilation, linking, signing, installation, test discovery
and runtime assertions. A macro runs for the host even when its output compiles
for a different platform. A simulator slice and device slice are separate
artifacts; an Apple Silicon host does not make them interchangeable.

An SDK declaration can be present at compile time while the deployment minimum
is older. Use the appropriate availability contract (`@available`, `#available`)
and test the supported fallback. `canImport` answers a module question, not an
OS-version or entitlement question. SwiftPM's platform minimum is not a promise
that every dependency and imported framework works on every host.

For migrations, establish a passing baseline, change one compatibility boundary,
then run affected consumers and runtime lanes. Recheck default isolation and
nonisolated async semantics as settings, not just the compiler version. Preserve
warnings that expose real boundary violations instead of lowering strictness.

Authorities: [SwiftPM documentation](https://docs.swift.org/main/documentation/packagemanagerdocs/),
[package resolution](https://github.com/swiftlang/swift-package-manager/blob/main/Sources/PackageManagerDocs/Documentation.docc/ResolvingPackageVersions.md),
[Xcode package CI](https://developer.apple.com/documentation/xcode/building-swift-packages-or-apps-that-use-them-in-continuous-integration-workflows).
