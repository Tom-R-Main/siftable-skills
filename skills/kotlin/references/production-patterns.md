# Production boundaries from real Kotlin applications

Read for native/session lifetimes, callback adapters, resource-backed queries,
multi-provider search, offline synchronization, engine threads, or local test
contracts. Reviewed 2026-10-16 against the six commits listed below. The examples
are evidence for decisions, not certified implementations to copy wholesale.
Reference checkouts are optional; the skill does not depend on these local paths.

## Keep architecture and enforceable contracts local

Find the existing state owner, public module surface, DI wiring, error helper,
and test fake before adding equivalents. Element X uses composable presenters;
Now in Android uses ViewModels and Hilt; AVNC integrates Views and native sessions;
Unciv uses engine-specific dispatchers. Each has a valid context. Kotlin does not
require converting any of them to the others.

Prefer a project's existing cancellation-aware result helper over a new
near-duplicate, after reading its implementation. Element X also enforces this
choice through a custom Detekt rule. Architecture/import checks can encode
additional rules that a compiler or formatter alone does not check. Follow those
rules within their project; do not promote a local ban on state defaults or a
specific dependency-injection framework into a universal Kotlin rule.

Map source roots, flavors, and convention plugins before selecting checks.
Lawnchair's AOSP-derived source directories and Unciv's test assets and working
directory are concrete reasons not to assume standard layout or raw compiler
commands. Verify screenshots through the supported comparison lane; generating
new baselines is a separate mutation governed by that project's workflow.

## Native resources, callbacks, and shutdown

For JNI/FFI handles, sockets, executors, and rendering resources, trace creation,
all users/callbacks, and release. State guards and locks must prevent access
after destruction and make repeat cleanup safe where the API promises it.
Shutdown should stop new work, coordinate in-flight users, release resources,
and finish on the required thread. Do not mechanically replace a lock with
`@Volatile`: visibility of one field does not protect a compound handle lifetime.
Keep waits and potentially blocking native work off UI/event-loop critical paths.

AVNC's client guards native calls and destruction with a shared lock and a
destroyed state; its session orders messenger/client/SSH shutdown. These show
ownership questions to preserve, not proof of every possible race being absent.
Compilation of the Kotlin wrapper does not exercise the native ABI or cleanup.

For a single-result callback use the version's supported cancellable suspension
adapter. Wire cancellation to the real operation's cancellation/unregistration,
respect callback-thread requirements, and handle completion/cancellation races.
If callbacks can complete more than once, use the supported atomic completion
protocol or prove the callback contract; checking `isActive` alone is not atomic.
If a callback returns a resource, arrange cleanup when cancellation wins before
the caller receives ownership. Check the pinned continuation API signatures.

For repeating callbacks, use `callbackFlow` with paired teardown in `awaitClose`.
Handle unavailable services, failed registration, initial values, and repeated
collection. Select `trySend`, blocking send, buffer, or conflation from callback
thread and delivery semantics; do not block a system callback just to retain
every update. Restarting collection must not accumulate registrations.

For listener registries, distinguish the callback object from each registration
and its owner. Two owners may legally share one callback; stopping one must
remove only its registrations, including when filters differ. Track registration
tokens or equivalent ownership rather than removing every matching callback.
For hierarchical dispatch, test a diamond of interfaces as well as a linear
class chain. Deduplicate repeated ancestor visits or registration identities;
a `Set` of newly allocated identity-based wrappers does not deduplicate logical
registrations. Preserve independently registered subscriptions according to the
API's delivery contract.

## Search pipelines and resource-backed reads

Treat a replacement query as a lifecycle boundary. Cancel obsolete producers
through the established job/latest-operator path and ensure late callbacks or
non-cooperative work cannot publish stale results into the current query. Choose
an identity/generation guard when the underlying API cannot cancel reliably.

For several independent providers, decide whether one operational failure should
fail the whole search or become a provider-specific result. Supervision alone
does not recover an exception. Preserve parent cancellation and permission-denied
outcomes instead of mapping every failure to an empty result. Coordinate parallel
state updates atomically, and bound concurrency if work grows with input size.

Keep resource-backed work inside both its resource lifetime and execution
context. A lazy Sequence returned from `use` can retain a closed cursor; a lazy
transform returned from `withContext(IO)` can do its expensive work later on the
caller's thread. Materialize owned values before closure when bounded, or use an
explicit streaming API that owns iteration, cancellation, and close. Lawnchair's
query helper builds its result list while the cursor is open before exposing a
Sequence. Review that useful lifetime boundary separately from its catch policy.

## Offline data, checkpoints, and persistent workers

When the application is offline-first, preserve its authoritative read path.
Now in Android reads mapped models from Room and syncs network changes into that
store. Bypassing it with a direct network response creates another visible state
path. Do not impose a disk-first design on a project with a different contract.

Advance sync checkpoints only after the corresponding writes succeed. If data
and checkpoint use different stores, do not assume atomicity: partial application
must be replayable/idempotent or explicitly reconciled. Test failure after an
early write, cancellation before checkpointing, repeat sync, deletion, and restart
as applicable. Network availability is a scheduling signal, not proof that a
particular service request will succeed.

Trace checkpoint acknowledgements through their actual adapters: a `Unit` return
or outer `Result.isSuccess` does not prove a durable write if an inner layer
logs and swallows its I/O failure. Fault injection should reach the persistence
adapter, not stop at an always-successful in-memory fake. Replayed data writes
and external effects are distinct: after a committed batch, a notification may
still be pending even though its record now counts as existing on retry.

Use the existing persistent-work owner for work intended to survive the screen
or process. Preserve unique-work identifiers and understand KEEP/REPLACE/APPEND
semantics before changing them. Now in Android's stable sync work name prevents
duplicate enqueues for that logical operation; inventing a new name can bypass
that coordination. Unique enqueueing does not prove exactly-once side effects,
so preserve retry, idempotency, and conflict policies too.

For persisted schema/model changes, use the supported migration procedure,
preserve versioned schemas, and test supported old stores with representative
data. AVNC tests migration paths across schema versions. Schema validation alone
does not prove the data survived correctly. Recreating a database or rewriting
old fixtures can conceal a broken upgrade.

### Inspect storage identity and derived state

For refresh/reconciliation code, inspect exported/generated schema, true keys,
conflict policies, and relevant triggers. `INSERT(REPLACE)` does not replace a
logical domain ID unless the inserted values actually conflict with its stored
identity. Standalone FTS tables may allocate a new rowid on each insertion.
Read-side ID deduplication can hide repeated results while stale terms, counts,
or retained rows remain wrong.

Exercise first population, identical refresh, changed content, removal, and
failure/retry where those transitions are supported. For a complete relationship
snapshot, compare added and removed junction memberships; inserting current
links alone only grows the set. Distinguish this from an intentionally additive
API before recommending replacement. `Upsert` updates and delete/reinsert
replacement can have different foreign-key cascade effects.

Use a real storage-engine lane for identity, uniqueness, cascades, and relation
queries. A source-derived SQL harness can establish those mechanisms with the
actual schema/queries; it does not execute Room-generated DAOs, Flow invalidation,
or the Kotlin app. Check whether test fakes can mutate payloads, remove relations,
and fail after partial progress before claiming their tests cover those paths.

## Engine threads and the smallest real test boundary

Thread affinity comes from the runtime, not from the word "main". Unciv dispatches
libGDX UI work through its GL adapter and shuts down owned executors when the
game ends. Android's main dispatcher cannot substitute for that render thread.
Preserve thread-affine creation, use, and disposal and verify behavior during
engine shutdown. A non-daemon pool may keep a process alive but does not make
work durable across process death.

Use the repository's existing dispatchers, fakes, runner, and asset setup. Element
X gives injected test dispatchers the same scheduler and observes presenter
state with Molecule/Turbine. Unciv distinguishes ordinary logic tests from tests
that need a headless render loop. Now in Android tests DAO-backed reads and sync
versions using fake data sources. These prove different boundaries: fake DAO
tests do not establish SQL correctness, and headless GL mocks do not establish
device rendering performance.

## Primary API checks

- [Single-shot cancellable callback and resource transfer](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/suspend-cancellable-coroutine.html)
- [libGDX thread affinity](https://libgdx.com/wiki/app/threading)
- [Offline-first data ownership](https://developer.android.com/topic/architecture/data-layer/offline-first)
- [WorkManager unique work](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/manage-work)
- [Room migrations and their tests](https://developer.android.com/training/data-storage/room/migrating-db-versions)

## Repository evidence

The pinned links below were checked against clean local tracked trees. They
identify observed implementation or test intent, not a test run.


### avnc

Snapshot: `1e209d630d106d1901f6d8bec671da6c41c2f18a`.


- [Native handle state and cleanup](https://github.com/gujjwal00/avnc/blob/1e209d630d106d1901f6d8bec671da6c41c2f18a/app/src/main/java/com/gaurav/avnc/vnc/VncClient.kt#L297-L313) — `app/src/main/java/com/gaurav/avnc/vnc/VncClient.kt:297-313`.

- [Ordered session shutdown](https://github.com/gujjwal00/avnc/blob/1e209d630d106d1901f6d8bec671da6c41c2f18a/app/src/main/java/com/gaurav/avnc/session/RemoteSession.kt#L126-L140) — `app/src/main/java/com/gaurav/avnc/session/RemoteSession.kt:126-140`.

- [All-pairs supported schema migration checks](https://github.com/gujjwal00/avnc/blob/1e209d630d106d1901f6d8bec671da6c41c2f18a/app/src/androidTest/java/com/gaurav/avnc/model/DatabaseTest.kt#L17-L35) — `app/src/androidTest/java/com/gaurav/avnc/model/DatabaseTest.kt:17-35`.



### element-x-android

Snapshot: `b1f04799a4d71bdb96af70aac3a41d6fd73e9a68`.


- [Cancellation-aware Result helper](https://github.com/element-hq/element-x-android/blob/b1f04799a4d71bdb96af70aac3a41d6fd73e9a68/libraries/core/src/main/kotlin/io/element/android/libraries/core/extensions/Result.kt#L13-L29) — `libraries/core/src/main/kotlin/io/element/android/libraries/core/extensions/Result.kt:13-29`.

- [Custom Detekt enforcement](https://github.com/element-hq/element-x-android/blob/b1f04799a4d71bdb96af70aac3a41d6fd73e9a68/tests/detekt-rules/src/main/kotlin/io/element/android/detektrules/RunCatchingRule.kt#L21-L41) — `upstream/tests/detekt-rules/src/main/kotlin/io/element/android/detektrules/RunCatchingRule.kt:21-41`.

- [Composable presenter and app-owned work](https://github.com/element-hq/element-x-android/blob/b1f04799a4d71bdb96af70aac3a41d6fd73e9a68/features/share/impl/src/main/kotlin/io/element/android/features/share/impl/SharePresenter.kt#L30-L68) — `features/share/impl/src/main/kotlin/io/element/android/features/share/impl/SharePresenter.kt:30-68`.

- [Presenter state transitions with fake dependencies](https://github.com/element-hq/element-x-android/blob/b1f04799a4d71bdb96af70aac3a41d6fd73e9a68/features/share/impl/src/test/kotlin/io/element/android/features/share/impl/SharePresenterTest.kt#L40-L90) — `features/share/impl/src/test/kotlin/io/element/android/features/share/impl/SharePresenterTest.kt:40-90`.

- [Injected dispatchers share the test scheduler](https://github.com/element-hq/element-x-android/blob/b1f04799a4d71bdb96af70aac3a41d6fd73e9a68/tests/testutils/src/main/kotlin/io/element/android/tests/testutils/TestCoroutineDispatchers.kt#L25-L37) — `upstream/tests/testutils/src/main/kotlin/io/element/android/tests/testutils/TestCoroutineDispatchers.kt:25-37`.



### Kvaesitso

Snapshot: `8f6a916108e8f2fc79c02a721031212a259898b5`.


- [Parallel providers and atomic result updates](https://github.com/MM2-0/Kvaesitso/blob/8f6a916108e8f2fc79c02a721031212a259898b5/services/search/src/main/java/de/mm20/launcher2/search/SearchService.kt#L118-L140) — `services/search/src/main/java/de/mm20/launcher2/search/SearchService.kt:118-140`.

- [Plugin permission, cancellation, and failure translation](https://github.com/MM2-0/Kvaesitso/blob/8f6a916108e8f2fc79c02a721031212a259898b5/services/plugins/src/main/java/de/mm20/launcher2/plugins/PluginService.kt#L155-L178) — `services/plugins/src/main/java/de/mm20/launcher2/plugins/PluginService.kt:155-178`.

- [Listener registration paired with teardown](https://github.com/MM2-0/Kvaesitso/blob/8f6a916108e8f2fc79c02a721031212a259898b5/app/ui/src/main/java/de/mm20/launcher2/ui/launcher/widgets/clock/parts/AlarmPartProvider.kt#L56-L69) — `app/ui/src/main/java/de/mm20/launcher2/ui/launcher/widgets/clock/parts/AlarmPartProvider.kt:56-69`.



### lawnchair

Snapshot: `85335d904a1c8b9790e40c581226684c59166297`.


- [Animation cancellation bridge](https://github.com/LawnchairLauncher/lawnchair/blob/85335d904a1c8b9790e40c581226684c59166297/lawnchair/src/app/lawnchair/LauncherStateExtensions.kt#L12-L28) — `lawnchair/src/app/lawnchair/LauncherStateExtensions.kt:12-28`.

- [Receiver teardown and context-specific blocking helpers](https://github.com/LawnchairLauncher/lawnchair/blob/85335d904a1c8b9790e40c581226684c59166297/lawnchair/src/app/lawnchair/util/FlowUtils.kt#L30-L47) — `lawnchair/src/app/lawnchair/util/FlowUtils.kt:30-47`.

- [Materialization before cursor closure](https://github.com/LawnchairLauncher/lawnchair/blob/85335d904a1c8b9790e40c581226684c59166297/lawnchair/src/app/lawnchair/search/algorithms/engine/provider/FileSearchProvider.kt#L292-L319) — `lawnchair/src/app/lawnchair/search/algorithms/engine/provider/FileSearchProvider.kt:292-319`.

- [Flavor dimensions and nonstandard source roots](https://github.com/LawnchairLauncher/lawnchair/blob/85335d904a1c8b9790e40c581226684c59166297/build.gradle#L257-L307) — `build.gradle:257-307`.



### Unciv

Snapshot: `409b34de9803fc00b5043a4cd110b5e9b3b1df5c`.


- [GL dispatch, shutdown, and daemon distinctions](https://github.com/yairm210/Unciv/blob/409b34de9803fc00b5043a4cd110b5e9b3b1df5c/core/src/com/unciv/utils/Concurrency.kt#L74-L94) — `core/src/com/unciv/utils/Concurrency.kt:74-94`.

- [Actual render-thread dispatch and disposed-engine handling](https://github.com/yairm210/Unciv/blob/409b34de9803fc00b5043a4cd110b5e9b3b1df5c/core/src/com/unciv/utils/Concurrency.kt#L211-L229) — `core/src/com/unciv/utils/Concurrency.kt:211-229`.

- [Headless/render-thread harness and teardown](https://github.com/yairm210/Unciv/blob/409b34de9803fc00b5043a4cd110b5e9b3b1df5c/tests/src/com/unciv/testing/GdxTestRunner.kt#L30-L64) — `upstream/tests/src/com/unciv/testing/GdxTestRunner.kt:30-64`.

- [Test working directory, assets, and JVM agent](https://github.com/yairm210/Unciv/blob/409b34de9803fc00b5043a4cd110b5e9b3b1df5c/tests/build.gradle.kts#L24-L40) — `upstream/tests/build.gradle.kts:24-40`.

- [Explicit seeds for repeatable map-generation checks](https://github.com/yairm210/Unciv/blob/409b34de9803fc00b5043a4cd110b5e9b3b1df5c/tests/src/com/unciv/logic/map/ResourceDiversityTest.kt#L84-L98) — `upstream/tests/src/com/unciv/logic/map/ResourceDiversityTest.kt:84-98`.



### nowinandroid

Snapshot: `a49ed253d75e61a2b6ab80a8da677b57437b08eb`.


- [DAO-backed reads, model mapping, and network-to-store sync](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/core/data/src/main/kotlin/com/google/samples/apps/nowinandroid/core/data/repository/OfflineFirstTopicsRepository.kt#L33-L65) — `core/data/src/main/kotlin/com/google/samples/apps/nowinandroid/core/data/repository/OfflineFirstTopicsRepository.kt:33-65`.

- [Apply changes before advancing sync version](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/core/data/src/main/kotlin/com/google/samples/apps/nowinandroid/core/data/SyncUtilities.kt#L79-L104) — `core/data/src/main/kotlin/com/google/samples/apps/nowinandroid/core/data/SyncUtilities.kt:79-104`.

- [Stable unique sync work identity](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/sync/work/src/main/kotlin/com/google/samples/apps/nowinandroid/sync/initializers/SyncInitializer.kt#L24-L40) — `sync/work/src/main/kotlin/com/google/samples/apps/nowinandroid/sync/initializers/SyncInitializer.kt:24-40`.

- [Injected worker dispatcher and success/retry policy](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/sync/work/src/main/kotlin/com/google/samples/apps/nowinandroid/sync/workers/SyncWorker.kt#L55-L85) — `sync/work/src/main/kotlin/com/google/samples/apps/nowinandroid/sync/workers/SyncWorker.kt:55-85`.

- [Tests assert the read source and post-sync checkpoint](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/core/data/src/test/kotlin/com/google/samples/apps/nowinandroid/core/data/repository/OfflineFirstTopicsRepositoryTest.kt#L67-L101) — `core/data/src/test/kotlin/com/google/samples/apps/nowinandroid/core/data/repository/OfflineFirstTopicsRepositoryTest.kt:67-101`.

- [Network callbacks clean up and conflate status updates](https://github.com/android/nowinandroid/blob/a49ed253d75e61a2b6ab80a8da677b57437b08eb/core/data/src/main/kotlin/com/google/samples/apps/nowinandroid/core/data/util/ConnectivityManagerNetworkMonitor.kt#L71-L89) — `core/data/src/main/kotlin/com/google/samples/apps/nowinandroid/core/data/util/ConnectivityManagerNetworkMonitor.kt:71-89`.
