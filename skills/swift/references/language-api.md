# Language and API design

## Model the actual domain

Use optional values for absence, throwing operations or explicit outcomes for
failure, and associated-value enums for mutually exclusive states. Avoid optional
field bags that admit impossible combinations. Narrow Foundation/Objective-C
`Any` and external payloads once at their boundary. Force unwraps and `try!` need
an established invariant; they are unsuitable recovery for ordinary external input.

Choose structs/enums for independent values and classes for shared identity or
reference lifetimes. A struct may share class members; copying it is not a deep
copy. Copy-on-write collections do not make concurrent mutations to the same
variable safe. `Hashable` keys need stable equality/hash inputs while stored;
avoid tying persistent identity to mutable display fields or array position.

Swift strings have Unicode-aware indices. `String.count`, UTF-8 byte counts and
UTF-16 offsets differ. At Foundation, editor, parser or C boundaries, name the
unit and convert with the appropriate view/range API; do not advance integer
offsets into arbitrary text. Test combining characters, emoji and non-ASCII input.

## Keep abstractions proportional

Read call sites before choosing argument labels, overloads, defaults and effects.
Follow [Swift's API design guidelines](https://www.swift.org/documentation/api-design-guidelines/).
Prefer concrete types when substitution is unnecessary; introduce a protocol for
a real interface, not every class. Keep access control narrow.

Use generics or opaque `some P` when preserving one concrete implementation/type
relationship matters; use existential `any P` for runtime heterogeneity where
supported. Account for associated types, existential opening, boxing and the
selected compiler. `some` does not permit unrelated concrete return types on
arbitrary branches; result builders have their own transformation rules.

Protocol-extension helpers and protocol requirements have different dispatch
behavior. If a behavior must vary through the protocol interface, inspect its
requirements and actual existential/generic call sites. Avoid assuming a helper
that merely shares a method name is a dynamically dispatched customization point.

Preserve actionable error context and the caller's recovery choices. Use typed
throws only where supported and useful to the API contract. `try?` erases error
information, including cancellation; use it only when every relevant failure
really means the same fallback. Assertions document programmer invariants; they
do not replace external-input validation, and optimization can change enforcement.

## Preserve serialization and SDK contracts

`Codable` synthesis is a representation convenience, not schema validation or
domain validation. Check missing versus null, default values, unknown enum
cases, dates/time zones, numeric precision, key names, resource bounds and
forward compatibility. A default-valued property does not establish the intended
decode-if-missing policy. Use custom decoding when the wire contract requires it.

Do not replace a form encoder with JSON or generic URL utilities just because
both produce strings. Preserve repeated keys, indexed arrays, null policy,
escaping and ordering where consumers/signatures rely on them. Pin those details
with consumer-style fixtures; [Stripe's example](production-patterns.md#build-drivers-and-wire-contracts)
is a concrete contract, not a universal encoding format.

Separate source compatibility, Swift ABI, module stability, Objective-C selectors,
wire format and persisted data. Check exported headers and real clients for
`@objc`/`dynamic` changes. Defaults and successful recompilation do not prove
existing binaries still work. Review isolation or `Sendable` additions for
consumer impact too.

For binary-distributed libraries, follow the existing library-evolution policy.
`@inlinable` exposes implementation to clients and constrains future changes;
`@frozen` commits representation/case information. Neither is a generic speed
annotation. Do not enable `BUILD_LIBRARY_FOR_DISTRIBUTION` for every application
or source package. See [library evolution](https://www.swift.org/blog/library-evolution/index.html).
