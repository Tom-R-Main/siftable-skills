# Errors, invariants and post-failure state

Match the repository's error model: exceptions, status/error-code returns,
expected-like types, fatal invariants, or an established combination. Godot and
WABT demonstrate no-exception configurations; that does not make exceptions
inappropriate in a repository designed around them. Preserve inspectable errors,
actionable context and caller recovery without introducing an unrelated library.

## Choose a guarantee at the operation boundary

- Nonthrowing: the promised operation cannot let an exception escape. An escaping
  exception from `noexcept` terminates; the keyword does not implement recovery.
- Strong: failure leaves the promised logical state unchanged. Build/validate
  candidate state before a commit step whose failure behavior is understood.
- Basic: invariants and resource ownership remain valid, but values may change.
- An explicitly failed/poisoned state may reject further work until reset or
  disposal when safe continuation cannot be promised.

These are operation-specific promises, not labels inferred from RAII alone.
State what happens to counters, ownership, registrations, queued work, published
results and external effects after each fallible step. A leak-free failure can
still leave a corrupt object or replay partially completed work.

## Cleanup can perform effects

When a destructor or guard can flush/commit, trace what happens if the caller
catches a failure and keeps the object alive. Will cleanup attempt the same batch
again? Choose discard, retry, rollback or poison deliberately; do not silently
discard retryable work or call a discard policy transactional rollback.

DuckDB resets a failed collection around a specific `FlushInternal` failure so
destruction cannot implicitly replay that collection. That catch scope does not
cover every earlier failure, and it does not prove external transaction rollback.
The transferable check is the failed effect's state and retry eligibility.

Destructors commonly cannot report failure usefully, especially during unwinding.
Provide explicit fallible finalization when the result matters, followed by
idempotent resource cleanup. Do not throw from cleanup during another exception.
Catch by appropriate reference and preserve propagation (`throw;`) when adding
context does not require translation. Catch-all handlers need a deliberate
boundary policy; swallowing all errors into apparent success hides lost work.

## Validate at trust boundaries

Assertions document programmer invariants only under their configured policy.
Many projects disable ordinary assertions in optimized builds; Bitcoin explicitly
keeps its assertion contract enabled. Inspect the actual macros and build before
assuming either behavior. Validate untrusted lengths, indices, formats and domain
values through a caller-visible failure path, not a debug-only assertion.

Capture `errno` or platform last-error state before cleanup/logging overwrites it.
Translate exceptions before crossing a C/foreign caller that cannot handle them;
define allocation, partial-result ownership and diagnostic lifetime on failure.
An `extern "C"` declaration changes linkage, not error safety.

Test the exact failure boundary with injected allocation/I/O/callback failures.
Check state and retry behavior as well as destructor counts. Include a catch that
occurs before object destruction, repeated close/reset, and subsequent valid
work when recovery is supported. A test that only checks that an exception was
thrown cannot establish the post-failure guarantee.
