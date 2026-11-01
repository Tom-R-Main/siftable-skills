# Conditional patterns from production repositories

Source traces reviewed 2026-11-01. These are applicability checks, not prescriptions
to copy a repository's architecture. Pinned paths and revisions are in
[sources](sources.md). Source observations do not establish runtime behavior.

## Match native acquisition to the producer

OBS's `obs.hpp` distinguishes adopting an already-owned C reference from acquiring
a new reference to a borrowed object. Weak-source promotion either returns an
owned strong reference or reports expiry. `ThumbnailItem` uses the owning helpers
across its weak-source lifetime. Retaining wrappers acquire a replacement before
releasing the old value so an alias does not die during assignment.

Transfer when wrapping intrusive/native references: audit the producer and the
specific wrapper path, including null, weak promotion, copies and self-aliasing.
Reject the inference that every raw pointer is a borrow or that every smart
pointer constructor should retain. Refcount ownership does not prove thread
safety or permitted destruction location.

Cheapest check: instrument retain/release and final destruction; test adopt-owned,
retain-borrowed, copy, self-alias replacement and expiry. A release-before-retain
control should fail for reacquiring an already destroyed object.

## Reconcile failure before cleanup can replay it

DuckDB's `BaseAppender::Flush` resets its collection if its `FlushInternal` call
throws, then rethrows. Its destructor helper can otherwise attempt `Close` after
a caller catches an error. Clearing this failed collection prevents implicit
replay. The existing interrupted-appender regression uses controlled gates and
checks subsequent clear/close/fresh work.

Transfer to buffered effects with automatic finalization: choose post-failure
state and retry eligibility explicitly. This source implements discard at one
catch boundary; do not claim all failures roll back, every partial row flushes,
or external transactions/durability are proved. Explicit fallible finalization
also lets callers observe errors that destructor fallback suppresses.

Cheapest check: throw from the downstream effect, catch while the writer remains
alive, then destroy it; require no automatic retry of that failed batch. A broken
keep-pending control must attempt it again. Explicit reset must still admit fresh
work when recovery is promised.

## Trace cleanup's lock and pin effects

DuckDB's move-only `BufferHandle` retains a pin whose byte pointer is borrowed.
Its destruction unpins and can reacquire a block lock; `StandardBufferManager::Pin`
places the handle outside a nested lock scope to avoid destruction under that
lock. A shared block owner is not the same as a resident-buffer pin.

Transfer: inspect transitive deleter/destructor behavior and reverse destruction
order. A local RAII object can be memory-safe yet deadlock on release; keeping a
metadata owner does not necessarily keep borrowed bytes resident. Validate the
actual pin/eviction and lock-order contracts before changing lexical scopes.

## Freeze membership, assign slots, wait, reduce

Binaryen precreates per-function analysis entries, claims functions with an
atomic work index, and waits for its pool callbacks before serial aggregation.
This keeps borrowed job state alive through completion and separates independent
analysis from the merge. Its default pointer-keyed map order is not stable source
order, and its worker loop is not evidence of callback exception recovery.

Transfer to independent batches only after checking container concurrency,
non-inserting lookup, stable storage, one writer per slot, shared-input immutability
and completion synchronization. Do not infer that `map[]` or packed proxy writes
are generally safe, or add a singleton pool solely because this source uses one.

Cheapest check: gate a worker before its final write; the dispatcher/reducer must
wait. Release it and compare with sequential output under the intended merge
order. A no-wait control must expose incomplete results without introducing an
uncontrolled use-after-free in the test itself.

## Cancellation must release the progress dependency

qBittorrent's `AsyncFileSender::DataPipe` bounds buffered bytes with a semaphore.
A worker blocked acquiring space cannot reach its next interruption check.
Sender destruction/socket failure request interruption and drain the pipe to
return capacity. Shared ownership retains pipe state through deferred worker
completion; QObject deletion still follows event-loop affinity.

Transfer to blocking bounded pipelines: identify who wakes each wait after a
consumer disappears. Prefer an existing close/stop-aware protocol when available.
Do not copy draining universally, equate wakeup with join, promise no last write,
or mistake a per-pipe capacity for an aggregate memory bound.

Cheapest check: fill capacity, establish a blocked producer, request stop and
observe it remains pending, then close/release and observe completion. Always
release/join in test cleanup so the negative control cannot strand a worker.

## Separate shared storage, snapshot and accessibility

TensorFlow documents that tensor copies and slices can share their underlying
buffer. `tensor_data()` borrows bytes; `tensor_data_cord()` retains the buffer.
Neither guarantees CPU-addressable device memory, and slices can change alignment.
The `SharesBufferWith` test definition distinguishes a copy from a separate
allocation.

Transfer to retained views or tensor/native APIs: establish storage lifetime,
aliasing/mutation, layout/alignment and device accessibility independently. Copy
the payload or use the backend's transfer path when the consumer needs an
independent snapshot or host data. A retained wrapper alone is insufficient.

## Preserve project-specific build and test meaning

Godot's SCons flags disable exceptions by default. TensorFlow's Bazel configuration
selects host and target dialects. WABT requires a language mode and separately
controls exceptions and test dependencies. Bitcoin requires C++20 at this captured
revision, rejects builds disabling its assertions, and has separate unit,
functional and fuzz lanes. whisper.cpp's visible C++17 assignment in its root
CMake file is conditional on Emscripten, not a universal native-target claim.

Transfer: read effective target settings and the runner, including later
overrides and consumers. Do not impose a universal C++ level, exception policy,
`NDEBUG` assumption or generic CTest command. Missing dependencies and zero selected
tests remain visible qualification limits.
