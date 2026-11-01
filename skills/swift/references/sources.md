# Sources and maintenance

Research date: 2026-11-01. This skill is an original synthesis, with links to
source rather than copied implementation code. Reference repositories remained
read-only and were not built or executed. A pinned receipt establishes inspected
bytes, not current upstream quality or tested correctness. Recheck the target
compiler, SDK, settings, framework contracts and callers before adoption.

## Language-skill grounding

Reviewed Kotlin, Go, Rust, TypeScript and Zig skill entrypoints and Kotlin's
source-provenance reference. Kotlin supplies the compact project-contract →
conditional-reference → implementation → verification structure. Go and Rust
reinforce actual build-driver/toolchain precedence; TypeScript reinforces
artifact execution; Zig reinforces native ownership and distinguishing source
checkouts from the target dialect. These are design antecedents, not runtime
skill dependencies. No universal Swift gate script is bundled: Xcode schemes,
destinations, package test membership and build side effects differ materially.

## Corpus coverage

A filename inventory across the existing reference collection found 9,278
`.swift` files in 29 repositories. The scan included hidden files and excluded
Git metadata, node_modules, build/dist/.build, Pods, vendor and data directories.
Counts include manifests, generated files, samples, vendored code outside those
exclusions, and deliberately invalid parser fixtures. They describe search
coverage, not review depth, authorship or quality. No repositories were fetched.

| Checkout label | Swift files | Treatment |
| --- | ---: | --- |
| bitwarden-ios | 2,780 | State-owner adapter and test definitions traced |
| stripe-ios | 2,631 | Manifest, test driver, encoder and consumer fixtures traced |
| openclaw | 1,617 | Waiter ownership, timeout state machine and build settings traced |
| cua | 608 | Native lifecycle stream sampled; queue invariant remains unproven |
| kotlin | 415 | Interop/compiler fixtures located; not application style authority |
| a2ui | 245 | Core/renderer build boundary and hosted redraw tests traced |
| ghostty | 199 | Native lifetime, borrowed userdata and build driver traced |
| open-codex-computer-use | 165 | Package/native app paths inventoried |
| dust | 110 | Experimental mobile/generated token paths inventoried |
| astryx | 79 | Native templates/package paths inventoried |
| semgrep | 66 | Parser fixtures; excluded as best-practice exemplars |
| gitnexus | 63 | Parser/control-flow fixtures; excluded as production exemplars |
| deepseek-harness | 52 | Experimental macOS native bridge paths inventoried |
| duckdb | 45 | Native owner and fallible flush boundary traced |
| obs-studio | 39 | Retained/unretained exports and UI/native seam sampled |
| PaddleOCR | 33 | iOS demo paths inventoried |
| t3-code | 25 | Mobile native modules inventoried |
| rea | 20 | Process/native UI bridge paths inventoried |
| t3-code-ov2 | 14 | Mobile modules and regression fixtures inventoried |
| shooter | 13 | iOS app paths inventoried |
| agent-desktop | 11 | UI fixture apps; not general application style authority |
| tailscale | 9 | macOS test virtualization paths inventoried |
| posthog | 9 | Mobile integration/widget paths inventoried |
| whisper.cpp | 8 | Actor-owned C context and scoped borrows sampled |
| pdf_oxide | 7 | Swift binding/example paths inventoried |
| bun | 5 | Fuzz harness paths; not general application style authority |
| refined-github | 5 | Safari app paths inventoried |
| bitwarden | 4 | Safari extension bridge paths inventoried |
| harper | 1 | Language fixture; excluded as best-practice exemplar |

The [production-patterns reference](production-patterns.md) contains exact
repository identities, commits, source paths/ranges, transfer conditions,
counterexamples and next checks for the selected mechanisms. The breadth scan
was followed by focused reading; it was not an audit of every Swift file.

Repo-learn captured selected evidence with HEAD, file/slice hashes and questions.
Its local authoring store and exports remain separate from this portable skill;
using the skill requires neither those checkouts nor the author's evidence DB.
Existing pattern cards were consulted for waiter cancellation, native handles,
and bounded-result evidence before selecting the Swift-specific distinctions.
Source-backed lessons remain distinct from model tests and target execution.

## Community comparisons

The user-supplied Two Straws directory led to six selected skill comparisons.
See [the comparison record](community-comparison.md) for pinned entrypoints,
the focused references actually read, adopted improvements and rejected
transfers. External skills are research inputs, not installation dependencies
or a new source of the user's preferences.

## Follow-up execution with the installed skill

On 2026-11-01, used Swift 6.3.2 / Xcode 26.5 on macOS to run byte-identical
isolated package snapshots from three existing reference checkouts, without
fetching dependencies or modifying the originals:

- OpenClaw's `apps/shared/OpenClawMLXTTSProtocol` at the commit already listed
  in production patterns: seven original XCTest cases passed.
- CUA's `libs/spaces-notch-swift` at the listed CUA commit: 18 original Swift
  Testing cases passed; the built helper's `--version` and `--selftest` passed.
- [Astryx's Apple package](https://github.com/facebook/astryx/tree/d51f57efa6f3a0e53584df9ad68c2abbeb30c8cb/packages/native/apple):
  233 original Swift Testing cases passed, including hosted rendering fixtures.

Independent source review followed by additional test-only CUA snapshot probes
exposed two concrete missed cases: complete/final-chunk oversized lines bypass
the splitter's bound, and a repeated older-query state can replace newer local
typing. The actual Swift probes failed the intended assertions; exact-limit and
overflow-recovery controls passed. The resulting input-framing and repeated-echo
guidance is conditional in the testing reference. No upstream correction was
made, and a passing original suite was not treated as proof against these defects.

These are package/helper-boundary checks. The full apps, Electron integration,
iOS simulator lanes, native input permissions and deployment were not qualified.
The installed skill supported the review and test selection; no comparison
against an unskilled agent or measured productivity benefit was established.

## Primary technical authorities

Read only the source relevant to the selected version and task:

- [API design](https://www.swift.org/documentation/api-design-guidelines/),
  [language guide](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/),
  [library evolution](https://www.swift.org/blog/library-evolution/index.html).
- [SwiftPM](https://docs.swift.org/main/documentation/packagemanagerdocs/),
  [dependency resolution](https://github.com/swiftlang/swift-package-manager/blob/main/Sources/PackageManagerDocs/Documentation.docc/ResolvingPackageVersions.md),
  [Xcode package CI](https://developer.apple.com/documentation/xcode/building-swift-packages-or-apps-that-use-them-in-continuous-integration-workflows).
- [Swift 6 migration](https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/),
  [SE-0461 async isolation](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0461-async-function-isolation.md),
  [SE-0466 default isolation](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md),
  [nonisolated async migration diagnostic](https://docs.swift.org/latest/documentation/diagnostics/nonisolated-nonsending-by-default/).
- [SwiftUI model data](https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app),
  [Swift Testing](https://developer.apple.com/documentation/testing),
  [test suite organization](https://docs.swift.org/latest/documentation/testing/organizingtests/),
  [test serialization scope](https://developer.apple.com/videos/play/wwdc2024/10195/).
- [C++ interoperability](https://www.swift.org/documentation/cxx-interop/),
  [unsafe pointers](https://developer.apple.com/documentation/swift/unsafepointer).

Official documentation is moving and some pages require JavaScript or were not
retrievable in the authoring browser. Linked proposals, indexed official text
and inspected source ground the specific decisions here; links do not imply
every page was fully read. Feature implementation in a proposal does not imply
that every target has enabled it. This skill deliberately does not pin a
universal latest Swift/Xcode release or a preferred app architecture.
