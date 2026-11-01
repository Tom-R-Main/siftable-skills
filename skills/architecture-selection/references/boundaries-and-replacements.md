# Boundaries and replacements

## Make a boundary earn its place

| Boundary | Concrete benefit | Contract and costs to inspect |
|---|---|---|
| In-language module | Local representation and shared lifecycle | Ownership, visibility, shared state, error propagation |
| In-process native/FFI | Reuse a strong implementation or native capability | ABI/layout, alloc/free pairing, borrowed buffer lifetime, retention, callbacks/reentrancy, thread affinity, errors/unwinding, shared crash consequences |
| Wasm guest | Restricted imports or portable execution | Actual host/artifact support, bindings/copies, memory growth, imports/capabilities, interruption, host-side I/O and resource limits |
| Worker/process | UI responsiveness, crash containment, privilege or lifecycle separation | Transfer/serialization, queues and byte bounds, cancellation, startup, restart, observability; a worker thread is not process crash isolation |
| Remote service | Placement, independent scaling, organizational or reliability boundary | Network/serialization, partial failure, authentication, retries/idempotency, distributed state, deployment and operational ownership |

Account for both directions, payload and call frequency, retained backing buffers, peak simultaneous representations, and build/distribution complexity. For data-heavy or memory-capped paths, record logical items versus physical entries/backing bytes, each copy or transfer, overlapping lifetime, and the scope and oversized-item behavior of every quota. A queue budget is not a whole-process limit. Batching can improve throughput while harming latency; copying a small result can release a large backing allocation. Treat generated bindings as executable code requiring real consumer tests. Neither a C ABI nor generated types settle ownership or runtime validation.

Wasm host isolation does not make unsafe guest code internally memory-safe or establish tenant/resource isolation by itself. Specify the threat model and host controls. Do not mandate a process for every FFI seam, or consolidate services merely because agents generate the code. Real blast-radius, availability, privilege, locality, and scaling needs survive agent assistance.

## Port with a behavioral oracle

Separate a structurally close port from an algorithm/representation redesign; simultaneous changes make attribution and regression diagnosis harder. Establish expected behavior from callers, formats, external fixtures, and the existing system while identifying known defects that should not be preserved. Compare errors, numeric conversion/precision, ordering, encoding, persistence/recovery, and lifecycle behavior as well as happy outputs.

Include ambient inputs where relevant: locale, time zone, environment configuration, filesystem/platform behavior, and scheduling. Check partial migration steps, mixed-version compatibility, cancellation/disposal, startup and shutdown. Exercise the real host boundary. Tests copied mechanically from a port can preserve the same misunderstanding; audit the oracle. Document deliberate compatibility changes separately.

Inventory actual consumers, including imported language APIs, scripts, tests, plugins, and CLI callers; executable compatibility alone may miss them. Distinguish offline execution from offline building and artifact distribution. Estimate build/artifact distribution, debugging and observability, data/schema migration, rollback or forward recovery, upstream changes, and future maintenance. Agent authoring lowers some costs; it does not make a language switch cheap or reversible when persistent formats, external APIs, or deployment contracts are involved.

## Dependencies: preserve accumulated behavior

Distinguish removing unused features, configuring/building upstream source, vendoring/patching, and replacing the implementation. Each transfers different obligations. Count trusted/executed/shipped behavior and patch ownership, not just package names; copied code remains a dependency.

A narrow stable leaf may be worth owning when semantics and an independent oracle are tractable. Crypto, databases, codecs, protocol stacks, Unicode/time handling, parsers of hostile input, and accessibility components carry substantial accumulated behavior. Prefer established implementations unless a concrete requirement and verification plan justify replacement. This is not a categorical ban on building a parser or database.

For source builds or forks record upstream origin/revision/license, modifications, reproducible build, update/security-fix path, and compatibility/failure checks. Preserve provenance in machine-readable metadata when tooling supports it. A smaller API or passing unit suite does not reproduce upstream assurance. Revisit a fork when its patch/update burden exceeds its measured benefit.
