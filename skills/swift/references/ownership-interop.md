# Ownership, ARC and native boundaries

## Own resources through their last use

Trace who creates, retains, borrows and destroys each native object, callback
target, buffer and subscription. A strong closure capture can keep its owner
alive; `[weak self]` is appropriate only when abandoning work on owner loss is
the intended contract. A weak capture followed by a strong binding across an
unbounded loop can still retain the owner indefinitely. `unowned` requires a
proven lifetime relationship, not an expectation that it usually exists.

ARC manages references; it does not provide a fallible asynchronous shutdown
protocol. Use explicit `close`/`flush`/`stop` when completion or errors matter.
Keep `deinit` as a fallback rather than the only durability acknowledgement.
Actor-isolated deinitialization capabilities vary with compiler/settings;
verify the selected language contract rather than assuming UI teardown is on
the main actor. [Ghostty and DuckDB receipts](production-patterns.md#native-lifetime-and-fallible-close)
show why resource lifetime, affinity and successful finalization are distinct.

## Keep unsafe memory contracts local

- Pointers obtained through `withUnsafe*`, `withCString` or collection buffer
  closures have the documented scoped validity; do not return/store them or let
  an asynchronous callback use them later. Verify whether the native callee
  copies bytes or retains the address. Use owned native storage for retained
  arguments, with an explicit free path.
- Track byte lengths versus elements, alignment, initialization, binding,
  mutability and aliasing. Contiguous representation is not proof of ABI layout
  for arbitrary Swift structs. Validate integer conversions and input bounds.
- Keep owners alive until the final native use; lexical appearance alone may
  not establish the required lifetime. Use scoped borrowing or an appropriate
  `withExtendedLifetime` boundary when needed. It cannot resurrect a dangling
  pointer or fix concurrent teardown.
- Pair `Unmanaged.passRetained` with exactly one consuming release;
  `passUnretained` borrows and needs an independent owner. Choose
  `takeRetainedValue` versus `takeUnretainedValue` from that ownership contract.
  A raw/opaque pointer is not a lifetime or thread-safety guarantee.
- Unregister/quiesce callbacks before freeing borrowed userdata. If teardown
  is deferred to an executor, account for the interval before it runs and for
  executor shutdown. Merely scheduling destruction does not prove completion.

An actor can serialize calls to a C handle without guaranteeing a fixed OS
thread. Check whether the native contract requires non-overlap, queue affinity,
thread affinity or UI actor isolation; those need different adapters. Keep
native ownership wrappers small and expose operations rather than arbitrary
pointers when practical.

## Respect imported-language and host contracts

Read C headers, module maps, nullability, Objective-C ownership conventions,
completion/delegate annotations and generated Swift interfaces. Preserve error
translation and Objective-C selectors. Imported callback APIs may invoke
synchronously or on another queue; verify instead of relying on an async-looking
Swift signature. `canImport(ObjectiveC)` and Foundation on Linux do not imply
Darwin Foundation behavior or Apple framework availability.

For C++, use the project's selected interoperability mode, supported type
mapping, lifetime annotations and compiler/stdlib tuple. Do not prescribe the
new safe interoperability mode to older targets or assume a Swift view owns its
C++ backing storage. See [Swift C++ interop](https://www.swift.org/documentation/cxx-interop/)
and [pointer binding rules](https://developer.apple.com/documentation/swift/unsafepointer).
For Kotlin/Native, inspect the selected export mode and generated interface;
ObjC framework export and Swift export can expose different types and ownership.

Exercise the real foreign boundary with repeated create/use/destroy, early
failure, cancellation, callback-after-close and invalid inputs. Sanitizers may
help on supported targets, but a pure Swift mock cannot validate native ABI,
use-after-free or the framework's thread requirements.
