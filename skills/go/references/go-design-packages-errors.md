# Go design, packages, values, and errors

Use the selected toolchain's `go doc`, standard-library source, language
specification, and nearby repository code for version-sensitive behavior.

## Contents

- Package and API boundaries
- Zero values, constructors, pointers, and values
- Slice, map, string, and resource ownership
- Interfaces, generics, and iterators
- Error contracts
- Documentation, compatibility, and review checklist

## Package and API boundaries

Start with the dependency direction and behavior, not a directory template.

- A package should have one recognizable responsibility and a name that reads
  naturally at use sites. Avoid `util`, `common`, `helpers`, and `types` when a
  domain name exists; do not rename an established package merely to satisfy
  this preference.
- Keep exported surface area small. Exporting commits the project to names,
  method sets, errors, serialization, concurrency behavior, and documentation.
- Package layout follows import and ownership boundaries. `internal` enforces an
  import boundary; `cmd`, `pkg`, `api`, and service layers are conventions, not
  language requirements.
- Avoid import cycles by correcting dependency direction. Common repairs are a
  small consumer-owned interface, a domain data type moved toward its owner, or
  orchestration lifted to a higher package. Do not create a grab-bag package to
  make the compiler quiet.
- Keep `main` thin when the application benefits from testable construction,
  but a small command does not need ceremonial layering.

Before changing a public API, search:

```sh
rg -n 'SymbolName|package/path' --glob '*.go' .
gopls references path/to/file.go:line:column 2>/dev/null
go doc ./path/to/package.SymbolName
```

Check external implementations and consumers, generated mocks, compile-time
interface assertions, examples, build-tag variants, and serialization formats.

## Zero values and constructors

A useful zero value reduces setup and composes well, but it is not mandatory.

Use the zero value when:

- its behavior is valid and unsurprising;
- lazy initialization is safe;
- copying before use has defined semantics; and
- cleanup is unnecessary or naturally idempotent.

Use a constructor when:

- invariants must be validated;
- defaults cannot be represented by zero;
- dependencies, registration, goroutines, files, sockets, or foreign handles
  are acquired;
- several fields must agree; or
- a later method would otherwise fail for a structurally valid-looking value.

State whether construction transfers ownership and whether failure leaves any
resource for the caller to release.

## Pointer and value semantics

Choose based on meaning:

- Use a pointer when identity, shared mutation, nil, non-copyable state, or a
  consistent pointer method set matters.
- Use a value when independent copying is part of the type's semantics and the
  value is safe to copy.
- Types containing mutexes, atomics, once values, or handles are usually not
  copyable after first use. Document this and let `go vet`'s copylock analysis
  help where applicable.
- Do not set a universal byte-size threshold. Measure hot call paths when copy
  cost is a concern.

Receiver consistency matters, but semantics outrank uniformity. Remember:

- Methods on `T` belong to the method sets of both `T` and `*T`.
- Methods on `*T` do not belong to the method set of `T`.
- Interface satisfaction can therefore change when a receiver changes.
- A typed nil pointer stored in an interface makes the interface non-nil.

## Slices, maps, strings, and ownership

Slices are descriptors over backing arrays. Maps are reference-like runtime
objects. Neither implies exclusive ownership.

At boundaries decide and, when non-obvious, document:

- May the callee mutate the input?
- May the caller retain or mutate the returned value?
- Is a clone shallow or deep?
- Is a returned buffer reused on the next call?
- Is concurrent access supported?
- Does a subslice retain a much larger allocation?

Common review points:

- `append` can reuse the caller's backing array or allocate a new one depending
  on capacity. Use `slices.Clone` or an explicit copy when isolation is part of
  the contract.
- `copy` and `slices.Clone` are shallow for elements containing pointers,
  slices, maps, or other references.
- Nil and empty slices differ in some JSON, reflection, equality, and API
  contracts. Preserve the representation the boundary requires.
- A nil map can be read but panics on assignment. Concurrent map access needs
  synchronization or single-owner confinement.
- Converting between `string` and `[]byte` copies under ordinary safe Go. Avoid
  unsafe zero-copy conversions unless profiles justify them and lifetime is
  provable.

## Interfaces

Prefer interfaces defined by the consumer around the behavior it needs.

Good reasons for an interface:

- multiple implementations exist or are planned as part of the task;
- testing needs a controllable external boundary;
- a package boundary should hide a volatile implementation;
- the API represents a capability such as `io.Reader`.

Weak reasons:

- every concrete type "should" have an interface;
- a framework expects service/repository layers;
- mocking a large concrete API seems easier than narrowing the dependency;
- a one-off implementation might theoretically change someday.

Keep interfaces small enough that callers can implement them without importing
unrelated policy. Do not return an interface solely to hide a useful concrete
API. When nil is meaningful, specify whether typed nil implementations are
valid.

## Generics and iterators

Use generics when the same algorithm or data structure genuinely applies to a
family of types and the constraint expresses the needed operations.

- Prefer the smallest useful constraint. `any` communicates no operations;
  `comparable` communicates equality and map-key suitability.
- Avoid exposing implementation types through constraints accidentally.
- Consider inference, readable errors, compile time, code size, and public API
  compatibility—not only line-count reduction.
- Prefer `slices`, `maps`, `cmp`, and ordinary loops when they already express
  the operation clearly.
- Do not convert domain-specific behavior into a generic helper merely to remove
  a few repeated lines.

For range-over-function iterators, define:

- ordering and determinism;
- whether values alias internal storage;
- whether mutation during iteration is allowed;
- early-stop and cleanup behavior;
- how errors are surfaced; and
- whether an iterator may be used concurrently or more than once.

## Error contracts

Ask what callers need to decide.

| Need | Representation |
| --- | --- |
| No programmatic distinction | contextual ordinary error |
| Stable condition | sentinel checked with `errors.Is` |
| Structured data | typed error checked with `errors.As`/`AsType` |
| Several independent failures | `errors.Join` when all remain relevant |
| Boundary translation | map to protocol/domain result and intentionally stop or preserve the chain |

Wrap with `%w` only when preserving inspection is part of the API. Excessive
wrapping can expose dependencies as compatibility commitments. Add context once
per meaningful operation; avoid repeating the same subject at every layer.

Prefer the happy path down the page and handle errors near the operation. Check
cleanup errors when they can invalidate success, for example buffered writes,
commits, response bodies used for connection reuse, and durable file updates.

Logging and returning the same error often produces duplicates. Usually a
library returns context and an application boundary logs once. Exceptions exist
when the records have different contracts, such as a local security audit event
plus an intentionally redacted public error.

## Documentation and compatibility

Public documentation should state behavior callers cannot safely infer:

- zero value and constructor requirements;
- ownership and lifetime;
- goroutine safety;
- blocking and cancellation;
- mutation and aliasing;
- ordering and determinism;
- valid-after-close behavior;
- errors callers may inspect;
- compatibility or deprecation path.

Examples are executable public documentation. Use them when a correct call
sequence or output contract is easier to demonstrate than describe.

## Review checklist

- Does the package own a coherent responsibility?
- Is each abstraction required by a real boundary?
- Are zero, nil, copy, and close semantics deliberate?
- Are mutable or retained slices/maps/buffers documented or isolated?
- Do interfaces live near consumers and remain narrow?
- Does the error chain expose exactly the intended contract?
- Are exported behavior, wire formats, and observability compatible?
- Do comments explain invariants and obligations rather than syntax?
