# Persistence and context ownership

Read this only for persistence changes. Keep the selected SwiftData, Core Data
or other storage framework; a language skill does not authorize replacing it.
Establish schema versions, context owners, store configuration, migrations,
supported OS versions and whether CloudKit is actually enabled.

## Contexts, identifiers and saved state

Treat live SwiftData models and `ModelContext` as owned by their concurrency
domain. Use an appropriate `ModelActor` or established context adapter, and pass
validated value snapshots or persistent identifiers across boundaries rather
than live model instances. Re-fetch in the receiving context and handle missing
or deleted objects. Do not add `@unchecked Sendable` to transport a model.
Verify the selected SDK's generated interfaces and container/executor contract.

An inserted SwiftData model initially has a temporary persistent identifier;
do not publish it as a durable foreign key or synchronization identity before
the applicable save/identity transition. Distinguish persistent framework
identity from the domain's own stable identifier. For Core Data, follow context
`perform`/queue ownership and object-ID rules; an arbitrary Swift actor does not
replace them.

When the user-visible operation promises persistence, explicitly await/observe
the appropriate save and propagate failure. A mutation to an in-memory model,
view refresh, autosave configuration or ARC release is a weaker acknowledgement.
Trace a transaction through committed state before advancing a sync cursor or
reporting success. Do not confuse a local save with remote synchronization.

Authorities: [ModelContext](https://developer.apple.com/documentation/swiftdata/modelcontext),
[ModelActor](https://developer.apple.com/documentation/swiftdata/modelactor),
[insert and temporary identity](https://developer.apple.com/documentation/swiftdata/modelcontext/insert(_:)),
[Core Data concurrency](https://developer.apple.com/documentation/coredata/using-core-data-in-the-background).

## Schema and query changes

Choose relationship inverses and deletion rules from domain ownership, including
orphan behavior. Cascading is correct only when the related objects should die
with that owner. Review legacy stored data, uniqueness and merge policy before
adding constraints. A successful clean-store test does not verify an upgrade.
Do not reset or delete an existing store to make migration pass.

Test migrations against representative previous-version stores in a disposable
copy, including failure/rollback and retry. Verify the generated schema and
runtime query translation on supported OS versions; a macro that compiles does
not establish that a predicate works on the selected persistent backend.
Separate framework/OS-specific bug reports from universal syntax rules.

Choose count-only fetches, limits, prefetching, batches and indexes from measured
access patterns and availability. Preserve sort/identity semantics and avoid
holding an entire import graph when batches suffice. In-memory tests are useful
for logic but cannot qualify disk migration, crash durability or CloudKit.

## Apply synchronization constraints only when configured

For SwiftData with CloudKit, recheck the supported schema and release tuple.
Apple documents restrictions on uniqueness constraints, nonoptional
relationships and the deny deletion rule. Local uniqueness must not be promoted
into a distributed uniqueness guarantee. Handle delayed/partial relationship
arrival, offline edits, conflicts and retries without assuming an immediate
remote commit. Schema initialization and production promotion are separate
deployment actions subject to the task's authorization.

See [Apple's sync schema requirements](https://developer.apple.com/documentation/swiftdata/syncing-model-data-across-a-persons-devices).
Qualify sync with the actual configured integration in addition to local tests;
do not apply these constraints to every local-only database.
