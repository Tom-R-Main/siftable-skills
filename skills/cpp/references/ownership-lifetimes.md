# Ownership and lifetimes

At every boundary ask whether the value is owned, borrowed, adopted, retained,
transferred, or invalidated. C++ types express only part of that contract.

## Owners and special members

Prefer value members and existing RAII wrappers. Default special members when
members already express the invariant. A raw owning handle needs a deliberate
destructor, copy policy and move policy; deleting copy is often appropriate for
unique resources. Review all special members together instead of adding a
destructor and accidentally retaining shallow copy behavior or suppressing moves.

Initialization follows base/member declaration order, not initializer-list order;
destruction reverses it. If construction throws, completed base/member subobjects
are destroyed, but the complete object's destructor does not run. Put each acquired
resource into an owner before the next fallible step. A scope guard handles
cleanup, but still needs a deliberate success/disarm transition.

`std::move` permits moving; it does not perform a move by itself. Moving a const
object can select a copy. Preserve normal return-value elision rather than adding
`std::move` to every local return. A moved-from object's usable operations depend
on its contract; do not read old contents or assume every user-defined type is
automatically valid after a poorly implemented move. A truthful nonthrowing move
can affect container reallocation guarantees; do not add `noexcept` speculatively.

Use `unique_ptr` for exclusive heap ownership and `shared_ptr` for genuinely shared
lifetime. Shared ownership can create cycles and extend expensive lifetimes;
weak promotion can fail. Ownership of a control block does not make pointee
mutation safe, serialize concurrent access to the same smart-pointer object, or
guarantee where final destruction occurs.

## Borrowed values and invalidation

Pointers, references, iterators, `string_view`, `span`, range views and many proxy
objects do not keep their referents alive. Trace the underlying allocation and
owner, not just the wrapper's scope. Check:

- returned views/references to locals, temporaries or a reallocated container;
- mutation, erase, rehash, swap and move invalidation for the actual container;
- stored lambdas capturing locals or `this`, including `[=]`'s pointer capture;
- views that borrow another view's predicate/state or lazily compute results;
- `auto` losing references or retaining proxy objects unexpectedly;
- nonterminated string views crossing APIs that require a C string.

`reserve` can move invalidation earlier; it does not establish an unbounded
lifetime guarantee. A stable pointee address and a stable vector element address
are different contracts. Prefer an owned result when it must outlive the input,
or accept an owner whose lifetime genuinely contains consumption. Do not paper
over a lifetime defect by converting every path to shared ownership.

TensorFlow's tensor copy/slice can retain shared storage rather than copy values.
Retaining the buffer, obtaining an immutable snapshot, and obtaining host-readable
aligned data are separate questions. A small retained slice can also keep a large
allocation alive. Check device, layout and aliasing contracts before reading or
mutating through a view.

## Native references and teardown

For intrusive C references, distinguish a producer's already-owned result from
a borrow. Adopt the former; acquire a reference to extend the latter. Match each
owned reference to one release and preserve null/expired promotion behavior.
Replacement may need to retain the incoming alias before releasing the old owner.
OBS's wrapper trace illustrates this distinction; raw-pointer spelling does not
tell you which path is correct.

For callbacks, prove registration lifetime, any native ownership transfer,
unregistration and quiescence before freeing userdata. A weak-pointer check only
protects the state it successfully retains; it does not wait for all native work
or enforce a GUI/graphics thread's destruction policy.

Keep fallible `close`, flush or commit observable when callers need its result;
destructor cleanup must follow the project's nonthrowing/error-reporting policy.
Member order and lexical scope matter when cleanup reacquires a lock or joins a
worker. A handle destroyed under the same nonrecursive lock it needs to release
can deadlock even though its memory ownership is correct.
