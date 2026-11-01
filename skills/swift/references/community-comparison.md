# Community skill comparison

Reviewed 2026-11-01 after the user supplied
[Two Straws' directory](https://github.com/twostraws/Swift-Agent-Skills).
The directory links independently maintained skills; its listing is neither
technical verification nor permission to install them. Selected entrypoints
and focused references were read through the GitHub connector. No upstream
skill bundle, hook, installer or agent role was installed or executed.

This skill paraphrases useful decision criteria in its own workflow. Technical
claims are checked against the primary authorities in the focused references;
the community text supplies candidate questions, not compiler/runtime authority.
The four Paul Hudson repositories and Antoine van der Lee's concurrency
repository had MIT license text. No implementation or substantial text is copied.

| Source inspected | Useful contribution | Treatment here |
| --- | --- | --- |
| [SwiftUI Pro](https://github.com/twostraws/SwiftUI-Agent-Skill/blob/f2920b63995263f57b3e198674e89a602efba6d2/swiftui-pro/SKILL.md), plus accessibility/localization references | Semantic controls, resource-bundle localization, environment formatting, adaptive/assistive behavior; caution that binding rewrites can change effect triggers | Expanded [Apple UI](apple-ui.md), keeping platform/toolchain gating and existing state architecture |
| [Concurrency Pro](https://github.com/twostraws/Swift-Concurrency-Agent-Skill/blob/bee3f69ba17142da148d3c5406f148ed62592b69/swift-concurrency-pro/SKILL.md), plus structured-concurrency reference | Explicit dynamic fan-out admission, completion ordering and partial-result policy | Expanded [concurrency](concurrency.md); error propagation and cancellation remain distinct, rather than assuming any child throw immediately cancels all siblings |
| [Testing Pro](https://github.com/twostraws/Swift-Testing-Agent-Skill/blob/2d6bba14a3c8bf3694f218b92fffe617c41ae43e/swift-testing-pro/SKILL.md), plus async-tests reference | Confirmations do not wait after their body returns; time-limit and serialization scope need exact API contracts | Expanded [testing](testing-performance.md), preserving XCTest where the project uses/requires it |
| [SwiftData Pro](https://github.com/twostraws/SwiftData-Agent-Skill/blob/8051f177a0076e7fd45bdf4ee687b070ba58fdc6/swiftdata-pro/SKILL.md), plus core-rules/CloudKit references | Context ownership, explicit saves, temporary identity, relationship policy and sync-specific constraints | Added conditional [persistence](persistence.md); checked against Apple documentation, without mandating SwiftData or cascading deletions |
| [Antoine van der Lee's concurrency skill](https://github.com/AvdLee/Swift-Concurrency-Agent-Skill/blob/d5770817d2622e1585b1f7eaebc791a9cb0959c8/skills/swift-concurrency/SKILL.md) | Diagnostic-first routing and separate project isolation settings | Added a compact diagnostic table; retained conditional executor selection rather than automatically moving an empty task prefix off actor |
| [Daniel Devesa's accessibility skill](https://github.com/dadederk/iOS-Accessibility-Agent-Skill/blob/dcc3a36ce1d0099341d545c1af4eb5a8c989bf66/ios-accessibility/SKILL.md), entrypoint lines 1–100 | Actual assistive-technology interaction, semantic controls and accessible alternatives to gestures | Expanded the UI validation boundary; did not copy its full audit playbook |

## Deliberately not imported

- Fixed Swift/Xcode/OS minimums, new-project defaults, device claims or blanket
  modernization: use the target's verified tuple and supported consumers.
- Statements of an upstream author's user preferences, such as always choosing
  SwiftData, avoiding UIKit, or requiring every new unit test to use Swift
  Testing. Those are not this user's project decisions.
- Mandatory architecture/file-layout rules or a second review output format.
- Blanket `Binding` → `onChange` rewrites, arbitrary actor hops, universal
  `@unchecked Sendable` bans/permissions, or treating compilation as runtime proof.
- Newer API syntax, release-specific predicate workarounds, bundle macros, or
  migration advice without checking the target compiler/SDK and a meaningful
  test. Missing or broken upstream links are not evidence that an API exists.

Remaining specialized areas such as App Intents, widgets, full accessibility
audits, App Store operations and deep SwiftData optimization need their own
task-specific research. Their presence in the directory is not a claim that
this general Swift skill covers those complete workflows.
