# Apple UI state and lifecycle

## Find the state owner

Preserve the repository's state architecture. Follow user input through a
binding/action/effect into the owner, then follow publication to the rendered
view. [Bitwarden's Store/Processor seam](production-patterns.md#state-and-rendering-boundaries)
illustrates a deliberately separated action/effect model; it does not require
every SwiftUI app to adopt that architecture.

For an `ObservableObject` model, distinguish `@StateObject` ownership from
`@ObservedObject` observation of an injected instance; preserve its lifetime and
stable view identity. For the Observation macro, check SDK/deployment support:
use `@State` when the view owns the observable model, and `@Bindable` when a
bindable projection is needed. Reading an observable model can register
dependencies without either wrapper. Do not mechanically replace all wrappers
or mix the two models under the assumption that they have identical publication.

View `body` can be evaluated repeatedly. Keep it free of requests, registrations,
and persistent mutations. Use stable domain identity for list rows and navigation;
changing `.id` resets state rather than repairing its ownership. A computed
property that constructs a new store every render can discard the intended owner.

Read [Apple's model-data guidance](https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app)
when selecting observation APIs. The deployment target and target code take
precedence over examples using a newer SDK.

## Treat effects and adapters as lifecycle boundaries

Choose view-scoped `.task`/`.task(id:)` when work should follow the view or input
identity. Cancellation is cooperative; a cancelled task may still return a value.
Validate identity before publishing after suspension, especially for search,
selection, navigation, account changes and image loading. `onAppear` can repeat;
an unstructured task launched there needs its own owner. Keep CPU/blocking work
off the UI executor through a supported, explicit execution boundary.

In `UIViewRepresentable`/`NSViewRepresentable`, separate construction, updates
and dismantling. Keep delegate/coordinator lifetime stable, avoid feedback loops
between bindings and delegate callbacks, release observers/timers, and unregister
native callbacks before their target is destroyed. Verify focus, keyboard input,
accessibility and main-actor requirements in the hosted platform view.

Use `@MainActor` for UI ownership when appropriate; a Combine scheduler hop or
`Thread.isMainThread` check is not a general compiler-visible actor proof.
Follow the selected SDK's delegate isolation annotations. Do not introduce
`assumeIsolated` without proving that every invocation already meets its contract.

## Verify the UI promise at the rendered boundary

Reducer/store/model tests verify transitions. Hosted view tests can verify
publication, redraw and layout. UI automation or a real app flow verifies the
person's actual navigation and interaction. A passing lower layer does not
establish the higher layer. A2UI's hosted redraw tests are useful examples of
scoping invalidation, with an explicit platform host and layout flush.

For visible changes exercise loading, empty, error and populated states,
repeated navigation, cancellation/replacement, supported appearance and text
sizes, localization, keyboard/focus and accessibility as relevant. Match snapshot
runtime/device/scale; inspect changes before updating expected images. A preview
that compiles is not evidence that a shipped bundle includes its resources or
that its user journey works.

## Accessibility, localization and adaptive presentation

Prefer semantic `Button`, `Toggle`, `Link` and other platform controls over a
gesture attached to a visual container. Give icon controls meaningful localized
names and appropriate values/traits; hide decorative imagery, not interactive
controls. A UI-test accessibility identifier is not a spoken label. Check the
actual accessibility tree and relevant interaction with VoiceOver, keyboard or
Voice Control, rather than judging the pixels alone. Preserve focus when
content or presentation changes.

Use scalable text and layouts that tolerate the supported accessibility sizes,
narrow windows and long translations. Respect Reduce Motion and avoid conveying
state through color alone. Reuse the project's design system; verify the behavior
with assistive settings because a modifier checklist does not establish a usable
flow. See [Apple's accessibility fundamentals](https://developer.apple.com/documentation/swiftui/accessibility-fundamentals).

Keep the existing `.strings`, `.stringsdict` or string-catalog workflow. Verify
localizable key/resource types, interpolation, translator context and the bundle
that owns the resource; a framework/package string may silently look in the
app's main bundle if no correct bundle is supplied. `Bundle.module` is a SwiftPM
resource accessor, not a universal framework API. Do not adopt a newer bundle
macro without checking compiler support.

Use locale-aware formatting with the intended locale, calendar and time zone;
SwiftUI environment overrides matter for per-view settings and previews.
Distinguish localized UI messages from externally supplied verbatim content and
protocol serialization. Changing a custom binding setter to `onChange` can alter
whether equal-value or programmatic assignments trigger effects; preserve that
contract instead of applying a stylistic rewrite. See
[preparing views for localization](https://developer.apple.com/documentation/swiftui/preparing-views-for-localization).
