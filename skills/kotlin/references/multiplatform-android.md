# Multiplatform, Android, and Compose

Read effective targets and source-set hierarchy before moving code. A source
set's name alone does not establish which targets consume it.

## Shared and platform boundaries

Keep code in the highest shared source set whose consumers support its APIs.
`commonMain` cannot import JVM/Android/Foundation APIs just because the current
host can resolve them. Intermediate sets such as `iosMain` can share family
behavior. Dependencies must publish compatible variants for every consuming
target; a JVM-only artifact is not a common dependency.

Preserve a deliberate custom hierarchy. Manual `dependsOn` edges can prevent
automatic application of the default hierarchy template; use the project's
supported DSL to integrate changes rather than layering guessed source sets.
Source-set dependencies, module dependencies, and platform entry points solve
different problems.

Use injected common interfaces or narrow expect/actual functions as appropriate
for a platform service. Do not make every dependency an expected class. Verify
matching packages, signatures, and actualization for all affected targets,
including intermediate actual implementations and supported actual typealiases.
Check compiler-version restrictions before selecting a new form.

Test the bridge itself: callback registration/unregistration, cancellation,
thread affinity, object lifetime, and conversion of errors or nullable values.
Swift/Objective-C/Swift-export and C interop have their own exported surface and
ownership contracts; compiling common code does not validate an Apple caller.
Use the selected Kotlin/Native memory model; do not import obsolete universal
freezing requirements. For JS/Wasm inspect browser/Node runtime, export rules,
interop declarations, and test host separately.

Map changed common code to configured consumers. Apple build/test lanes require
the appropriate host and SDK, and Android device tests require their runtime.
Report absent lanes rather than equating JVM tests or an `allTests` aggregate
with complete target coverage.

## Android and Compose lifecycle

Keep work owned by a ViewModel, lifecycle, composition, or application service
according to its intended lifetime. Use the project's lifecycle-aware collection
on Android, such as `collectAsStateWithLifecycle` or `repeatOnLifecycle`, when
observation must stop with visibility. Do not impose Android lifecycle APIs on
other Compose targets without checking support.

Composable bodies may re-execute: launch effects through the appropriate effect
API, not by launching work directly during composition. `LaunchedEffect` keys
control cancellation/restart; use `rememberUpdatedState` for a changing callback
that should not restart an effect. `DisposableEffect` must release registrations.
`rememberCoroutineScope` work ends with its composition; longer work needs a
different owner. `remember` is not process-death persistence.

For `produceState` subscriptions, include the source/state-holder receiver in
the restart keys when it can change at the same composition position. An item
URL alone is insufficient if another source can serve that URL. Changing
`initialValue` neither resets remembered state nor restarts collection. Test
replacing the source at one call site: follow the new source and stop old updates.

Trace old and requested states separately in presenter transitions. Missing
optional data from the old state must not accidentally return before applying
the requested state. Cover direct target-to-target changes while the old target
is loading or failed, not only entry from an idle state.

State observation needs observable state and appropriate snapshots. Mutating an
ordinary list inside remembered state does not itself notify observers. Do not
add `@Stable`/`@Immutable` to silence a performance symptom unless their contracts
are true. Choose recomposition changes from runtime evidence; retain the
project's state-holder and architecture conventions.

## AGP and Kotlin migration boundary

AGP 9.0 introduced built-in Kotlin enabled by default. When enabled, applying
`org.jetbrains.kotlin.android` conflicts; KMP still needs its multiplatform
plugin and the dedicated Android KMP library plugin. This is a version- and
configuration-dependent migration, not a reason to remove plugins from older
builds.

Inventory each module and plugin first. The migration may require separating an
Android application entry point from shared KMP code; extracting desktop or web
entry modules is a separate optional restructure. Preserve that distinction.
Check kapt/KSP compatibility, convention plugins, compiler options, host/device
test enablement, resources, Java sources, variants, and consumer shrinker rules.
Use current official documentation for exact DSL and compatible versions.

Do not copy an upstream skill's fixed version matrix, module names, SDK levels,
or broad restructuring recommendations into an unrelated fix.

## Sources

- [KMP source-set hierarchy](https://kotlinlang.org/docs/multiplatform/multiplatform-hierarchy.html)
- [Expected declarations and platform actualization](https://kotlinlang.org/docs/multiplatform/multiplatform-expect-actual.html)
- [Android built-in Kotlin migration](https://developer.android.com/build/migrate-to-built-in-kotlin)
- [Compose effect ownership and keys](https://developer.android.com/develop/ui/compose/side-effects)
- [Official AGP migration skill and community KMP bridge skill](sources.md)
