# Provenance and maintenance

Research reviewed 2026-10-16. These are source materials, not imported operating
instructions or dependencies. The skill is an original synthesis. No external
installer, hook, agent-role bundle, or upstream skill is required to use it.
Recheck moving documentation against the target project's actual versions.

## Related language workflows

Reviewed the installed Go, Rust, TypeScript, Zig, and C systems programming
entrypoints under the installed skill catalog. Go's project-contract
discovery, Rust's build-driver precedence, and their focused-to-broad validation
informed the workflow. TypeScript's artifact execution requirement informed
runtime smoke checks. Zig's version-sensitive references informed the distinction
between a reference checkout and the target compiler. These local paths record
design provenance and are not runtime dependencies.

The Kotlin skill keeps those useful patterns, with a shorter description and
conditional references. It deliberately avoids a universal Gradle gate script:
task names, variants, source sets, hosts, and build side effects are
project-specific.

## Kotlin's agent-skills repository

- [Kotlin/kotlin-agent-skills](https://github.com/Kotlin/kotlin-agent-skills)
- [AGP 9 migration skill](https://github.com/Kotlin/kotlin-agent-skills/blob/main/skills/kotlin-tooling-agp9-migration/SKILL.md)

The migration skill informed plugin/module inventory and the separation between
a required Android split and optional broader restructuring. Exact versions,
DSL, SDK choices, and plugin compatibility should come from current primary
documentation for the selected tuple. This skill does not install the official
bundle or adopt its repository-specific naming convention.

## Community Kotlin skills reviewed

- [Chris Banes: concurrency and Flow](https://github.com/chrisbanes/skills/blob/main/skills/kotlin-concurrency-and-flow/SKILL.md)
  informed explicit work ownership and state/event delivery decisions. The local
  synthesis leaves channel/broadcast choice conditional on fan-out, gaps,
  cancellation, persistence, and acknowledgement requirements.
- [Chris Banes: API design](https://github.com/chrisbanes/skills/blob/main/skills/kotlin-api-design/SKILL.md)
  informed function ownership, semantic single-value domains, exhaustive public
  outcomes, and small platform seams.
- [Mariano Miani: KMP bridges](https://github.com/mmiani/kotlin-kmp-claude-agent-skills/blob/main/skills/kotlin-platform-kmp-bridges/SKILL.md)
  informed source-set placement and choosing interfaces versus expect/actual.
  Claims about actualization restrictions must be verified against official
  compiler-version documentation rather than inherited from the community text.
- [Mariano Miani: KMP testing](https://github.com/mmiani/kotlin-kmp-claude-agent-skills/blob/main/skills/kotlin-testing-kmp/SKILL.md)
  informed shared versus platform test coverage and test-layer selection.

The synthesis does not impose MVI, a fixed module layout, a DI framework, or
another author's review format. Community guidance identifies useful questions;
compiler behavior and library guarantees need primary-source evidence.

## Primary technical authorities

Each focused reference links the documentation for its claims. Core sources:

- [KGP configuration/compatibility](https://kotlinlang.org/docs/gradle-configure-project.html)
  and [compiler options](https://kotlinlang.org/docs/gradle-compiler-options.html).
- [Java interop](https://kotlinlang.org/docs/java-interop.html),
  [data classes](https://kotlinlang.org/docs/data-classes.html),
  [collections](https://kotlinlang.org/docs/collections-overview.html), and
  [backward compatibility](https://kotlinlang.org/docs/api-guidelines-backward-compatibility.html).
- [Coroutine exceptions](https://kotlinlang.org/docs/exception-handling.html),
  [StateFlow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/),
  [SharedFlow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/), and
  [coroutine testing](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/).
- [KMP hierarchy](https://kotlinlang.org/docs/multiplatform/multiplatform-hierarchy.html),
  [built-in Android Kotlin](https://developer.android.com/build/migrate-to-built-in-kotlin), and
  [Compose effects](https://developer.android.com/develop/ui/compose/side-effects).
- [Serialization](https://kotlinlang.org/docs/serialization.html),
  [JSON options](https://kotlinlang.org/api/kotlinx.serialization/kotlinx-serialization-json/kotlinx.serialization.json/-json-builder/),
  [Spring Kotlin support](https://docs.spring.io/spring-framework/reference/languages/kotlin/spring-projects-in.html), and
  [Ktor testing](https://ktor.io/docs/server-testing.html).

The moving KGP documentation displayed Kotlin 2.4.21 and coroutine API pages
displayed 1.11.0 during review; JSON API documentation displayed a release
candidate. These observations identify the research context, not recommended
dependency pins or compatibility claims for other releases. Prefer tagged
source/docs and local compilation for the selected project.

## Direct local evidence

The Kotlin checkout at the Kotlin reference checkout was read at
commit `d0a09eaba269a02ad8db305711a3bb7ff333550e`:

- `libraries/stdlib/src/kotlin/util/Result.kt:141-159` demonstrates the broad
  catch in both runCatching overloads.
- `libraries/stdlib/src/kotlin/Collections.kt` documents the separate read-only
  and mutable collection surfaces.
- Root/area-routing, build, authoring, and fixture documents ground
  [compiler repository work](compiler-repository.md).

The checkout was not built, modified, or used to infer the latest stable
language version. Its instructions apply within its own repository scope.

## Production application review

On 2026-10-16, reviewed AVNC, Element X Android, Kvaesitso, Lawnchair, Unciv,
and Now in Android from pinned reference checkouts. The resulting
[production-patterns reference](production-patterns.md) contains pinned commits,
file/line evidence, decision guidance, and limits for all six.

This pass strengthened native/callback resource ownership, resource-backed lazy
evaluation, runtime-specific thread affinity, repository architecture gates,
source roots and test harnesses, offline reads, sync checkpoints, persistent-work
identity, and data-preserving migrations. It reinforced the existing cancellation
and shared test-scheduler guidance. Application code was inspected read-only;
none of those applications was built or executed, and no empirical performance
or security certification is implied.

## Live read-only review using this skill

On 2026-10-16, applied the existing skill to Now in Android's sync and derived
search state at `a49ed253d75e61a2b6ab80a8da677b57437b08eb`, then refined guidance
from the actual review. This was an application exercise, not a measured
comparison against an assistant without the skill.

- [Search population and ID deduplication](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/core/data/src/main/kotlin/com/google/samples/apps/nowinandroid/core/data/repository/DefaultSearchContentsRepository.kt#L47-L76),
  [FTS inserts](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/core/database/src/main/kotlin/com/google/samples/apps/nowinandroid/core/database/dao/NewsResourceFtsDao.kt#L29-L38), and
  [exported Room schema](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/core/database/schemas/com.google.samples.apps.nowinandroid.core.database.NiaDatabase/14.json)
  motivated checking actual persisted identity rather than trusting a REPLACE
  annotation or consumer deduplication.
- [Relationship insertion and batched notification logic](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/core/data/src/main/kotlin/com/google/samples/apps/nowinandroid/core/data/repository/OfflineFirstNewsRepository.kt#L83-L140)
  motivated removed-membership checks and separating committed data from pending
  external effects during retries. A topic-removal trigger remains conditional
  on the upstream payload permitting membership removal.
- [Checkpoint adapter](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/core/datastore/src/main/kotlin/com/google/samples/apps/nowinandroid/core/datastore/NiaPreferencesDataSource.kt#L169-L186)
  motivated tracing persistence acknowledgements through swallowed I/O errors.

Four disposable SQLite checks with correction controls reproduced duplicate
index growth, obsolete-term matches, stale index counts after deletion, and
retained removed relationships. They used checked-in Room DDL, DAO SELECTs, and
SQL equivalent to the declared conflict operations. They did not execute Kotlin,
Room-generated DAOs, Flow invalidation, WorkManager, or an Android device. Adapter
and notification findings were established by source/control-flow review only.

Technical checks used [SQLite FTS identity](https://www.sqlite.org/fts3.html#section_1_3),
[SQLite conflict policies](https://www.sqlite.org/lang_conflict.html), and
[Room FTS rowid/content linkage](https://developer.android.com/reference/androidx/room/Fts4).

## Applied Element X and Unciv review

Applied the skill to Element X's cache/content-validation/reply path at
`b1f04799a4d71bdb96af70aac3a41d6fd73e9a68` and Unciv's event bus at
`409b34de9803fc00b5043a4cd110b5e9b3b1df5c`, keeping both checkouts read-only.

- Element X's [validation collectors](https://github.com/element-hq/element-x-android/blob/b1f04799a4d71bdb96af70aac3a41d6fd73e9a68/libraries/matrixui/src/main/kotlin/io/element/android/libraries/matrix/ui/media/contentvalidation/ContentValidationState.kt#L176-L198)
  and [reply consumer](https://github.com/element-hq/element-x-android/blob/b1f04799a4d71bdb96af70aac3a41d6fd73e9a68/libraries/textcomposer/impl/src/main/kotlin/io/element/android/libraries/textcomposer/ComposerModeView.kt#L135-L144)
  motivated receiver-sensitive `produceState` keys. Its
  [mode transition](https://github.com/element-hq/element-x-android/blob/b1f04799a4d71bdb96af70aac3a41d6fd73e9a68/features/messages/impl/src/main/kotlin/io/element/android/features/messages/impl/messagecomposer/MessageComposerPresenter.kt#L859-L892)
  motivated checking old-state guards that abort a requested transition.
- Unciv's [event bus](https://github.com/yairm210/Unciv/blob/409b34de9803fc00b5043a4cd110b5e9b3b1df5c/core/src/com/unciv/logic/event/EventBus.kt)
  and [real interface diamond](https://github.com/yairm210/Unciv/blob/409b34de9803fc00b5043a4cd110b5e9b3b1df5c/core/src/com/unciv/logic/multiplayer/OnlineMultiplayerEvents.kt#L10-L36)
  motivated separating callback identity, registration ownership, and ancestor
  deduplication. Broad-root subscriptions and shared-handler ownership are
  supported API cases; no current production caller triggering them was found.

Isolated source-derived Python/Java models reproduced the four failure
mechanisms with correction and negative controls. They did not execute original
Kotlin, Compose, or either application. Unciv's four EventBus test annotations
were commented out in this snapshot; the existing test-execution guidance
already catches that gap. Seven independent synthetic review cases then checked
the revised skill's discrimination, including valid keyed subscriptions,
owner-specific cleanup, ancestor deduplication, and ConcurrentMap initialization.
This exercise does not measure improvement against a no-skill baseline.
