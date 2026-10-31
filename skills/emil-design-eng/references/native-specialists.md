Relevance gate: Read this only for actual Expo/React Native or Swift implementation tasks. Ordinary mobile web work belongs in mobile-web.md; Kotlin and Rust tasks use their own specialists.

# Native specialists

Use the [shared workflow](../SKILL.md) and [provenance](provenance.md). Load only the platform section needed by the current task; this reference does not supply a complete native build or device-control toolchain.

## Expo and React Native

- Establish the installed React Native, Expo, Reanimated, gesture-handler, and router versions from the project and lockfile before adapting examples.
- Determine whether the app uses the New Architecture and whether the relevant native build supports it. Treat Reanimated 3 and 4 setup as version-specific.
- Check worklet configuration, required providers, gesture roots, router placement, and native module availability against the actual installed stack.
- Treat upstream recipes as design sketches, not compiled drop-ins. Verify imports, threading assumptions, APIs, and platform support before using them.
- Keep layout, animation, and gesture ownership aligned with the existing component architecture; avoid duplicating providers to make a local example run.
- Use shared values and UI-thread work where appropriate, but measure the affected interaction before asserting that moving work improves performance.
- Handle gesture cancellation, interruptions, navigation, and component teardown so transient state cannot remain active.
- Keep semantic accessibility actions and visible alternatives for swipe-only behavior. Haptics supplement feedback and must not carry the only indication of success or failure.
- Apply reduced-motion behavior consistently across animation primitives, transitions, and screen-level overrides. Do not let an override silently re-enable motion globally.
- Preserve useful state feedback when motion is reduced; check rapid or repeated activation and interruptions.
- Run the project's existing type checks, tests, and build or device driver where available. Report unavailable runtime coverage explicitly.
- Qualify device-dependent claims by platform, device, OS, build, and tested interaction. Simulator or emulator success is not proof of actual-device behavior.
- Use [footwork-tools](../../footwork-tools/SKILL.md) only for requested, available device interaction; do not assume access to a phone or native automation driver.

## Swift

- Confirm this is a Swift-language task before applying these rules. Identify compiler version, Swift language mode, deployment target, SDK, and concurrency settings from the project.
- Read existing build settings for default actor isolation and upcoming feature flags. Do not globally enable Approachable Concurrency to make a snippet compile.
- Gate newer language or framework features on the actual toolchain and deployment target; a recent compiler alone does not establish every behavior or API's availability.
- In particular, `nonisolated async` execution semantics depend on `NonisolatedNonsendingByDefault` and the applicable isolation context, not on compiler 6.2 alone.
- Distinguish declaration isolation, executor behavior, and `Sendable` requirements. Verify a proposed concurrency fix against the project's settings instead of adding annotations mechanically.
- Actor methods can suspend at `await`; other work may change actor state before execution resumes. Revalidate assumptions after suspension or keep the state transition within an appropriate synchronous region.
- Avoid holding stale indexes, authorization decisions, or partially updated invariants across suspension points. Cancellation and error paths must leave state coherent.
- Choose access control by the intended boundary: `private` permits access within the declaration and same-file extensions of that declaration; `fileprivate` permits access throughout the source file.
- Do not widen access merely to satisfy an example. Prefer the smallest boundary that matches actual callers and tests.
- Measure launch, scrolling, allocation, or concurrency performance using the project's available instruments and a stated scenario; keep debug and release observations distinct.
- Use the existing compiler, tests, preview, simulator, or application driver that the project actually provides. Do not claim a native build passed from static reading alone.

## Evidence and routing

- Native recipes still need real integration checks for keyboard/focus behavior, accessibility, platform lifecycle, and interrupted work when those affect the feature.
- Use [pstack-verify](../../pstack-verify/SKILL.md) when the project has an appropriate real-surface verification path; record unsupported coverage instead of inventing a driver.
- Keep web/PWA guidance in [mobile-web](mobile-web.md), library selection in [libraries](libraries.md), and performance or motion guidance in the corresponding parent-routed reference.
- Consult the reviewed source links and correction notes in [provenance](provenance.md) when an upstream recipe appears to conflict with the installed platform's contract.
