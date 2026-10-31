# Language, public APIs, and Java interop

Use the selected compiler/API level. New syntax, opt-in contracts, annotations,
and compiler-plugin behavior require evidence from that version.

## Make state and failure visible

- A nullable type represents absence, not all possible errors. Use an existing
  typed outcome or sealed hierarchy when callers must distinguish failures.
  Match every relevant subtype in public mappings; a catch-all can hide an
  unhandled new outcome. Check the project's enum/sealed evolution policy.
- Read mutable/custom properties once into a local value when needed for a
  valid smart cast. `!!` and unchecked casts need a real invariant, not just a
  desire to satisfy the compiler. `require`, `check`, and `error` communicate
  different contracts; external bad input often needs a recoverable outcome.
- `T`, `T?`, and Java platform types have different nullability guarantees.
  Normalize uncertain Java input at the boundary. Do not blanket-suppress
  JSpecify/nullability diagnostics introduced by a migration.
- Scope functions change the receiver/result shape and may hide non-local
  returns in inline lambdas. Choose them for clarity; nested receiver DSLs are
  not inherently more idiomatic than named local variables.

## Ownership and equality

`val` fixes a reference, not its contents. `List<T>` restricts this reference's
operations; another alias may still mutate the backing collection. `toList()`
does not recursively copy elements. Copy at a boundary when snapshot ownership
requires it; choose persistent collections only when they fit the project.

Data-class generated equality, hash, components, and copy concern primary
constructor properties. A body property can change without changing equality;
`copy()` is shallow. Mutable keys, mutable elements, arrays' equality behavior,
and in-place mutation of published state deserve explicit tests. These issues
also affect StateFlow conflation and UI observation.

Use value classes for meaningful single-value domains when their ABI and
serialization behavior fit. They may box through nullable/generic/interface
paths; do not promise zero allocation. A `typealias` adds a name, not a distinct
domain type. Avoid converting persistence entities or framework proxy types to
data/value classes solely for terseness.

## Generics and callable APIs

Use declaration-site `out`/`in` according to producer/consumer behavior; inspect
Java wildcard generation when crossing the JVM boundary. Star projection is an
unknown type, not permission to cast or insert arbitrary values. Reified inline
parameters permit some runtime type operations but do not restore erased nested
generic arguments. Keep `@Suppress("UNCHECKED_CAST")` local to a proved boundary.

Extensions resolve statically from the receiver's declared type, and applicable
members take precedence. Put behavior on the owning type when access to its
invariants matters; use extensions for deliberate adapters rather than global
utility clutter. Adding a member can change which callable existing source uses.

## Compatibility has several dimensions

For a published library or Java consumer, inspect the actual generated surface:

- JVM names, overloads, erasure, property accessors, nullability, wildcards,
  visibility, value-class mangling, and configured interface-default mode.
- Public inline bodies and `@PublishedApi` dependencies: implementation details
  may already be embedded in downstream binaries.
- Default parameters, constructor changes, data-class components/copy, and
  parameter names used by Kotlin named callers.
- Annotation use-site targets (`@field:`, `@get:`, `@param:`) and compiler
  defaults affecting serialization, validation, persistence, or reflection.

Adding a parameter with a default may let source recompile while breaking an
existing binary's method/constructor descriptor. `@JvmOverloads` is not a
universal compatibility repair. Preserve overloads or use the project's supported
compatibility mechanism, then run its API/ABI gate and representative old-binary
and Java-consumer checks when that is the commitment.

Use `@JvmStatic`, `@JvmName`, `@Throws`, and wildcard annotations only for a
specific caller contract. Kotlin does not enforce checked exceptions, but Java
callers may need a declared throws surface. Changing annotation defaults or
`-jvm-default` can be a migration even if Kotlin tests still compile.

## Sources

- [Calling Java from Kotlin](https://kotlinlang.org/docs/java-interop.html)
- [Data classes and shallow copying](https://kotlinlang.org/docs/data-classes.html)
- [Read-only and mutable collections](https://kotlinlang.org/docs/collections-overview.html)
- [Library backward compatibility](https://kotlinlang.org/docs/api-guidelines-backward-compatibility.html)
- [Local stdlib evidence and community API-design skills](sources.md)
