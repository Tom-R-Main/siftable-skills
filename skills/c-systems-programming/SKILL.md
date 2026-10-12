---
name: c-systems-programming
description: Implement, debug, and review C systems software. Use for descriptor ownership, process lifetimes, signals, IPC, nonblocking I/O, and platform-aware verification.
license: MIT
---

# C systems engineering

This workflow is original material authored for this repository under its MIT
license. It replaces an imported tutorial; neither that tutorial's examples nor
its third-party licensing are carried into this skill. Platform documentation
establishes API behavior; this skill organizes implementation and verification.

## Establish the execution contract

Before editing, identify the target OS and kernel range, libc, architecture, C
standard, compiler, build driver, and supported deployment targets. Read the
project's contributor guidance, warning policy, test commands, feature-test
macros, and platform adapters. Determine which interfaces are ISO C, POSIX, or
OS extensions. A successful build on one libc does not prove another target.

Follow the existing build system and dependency pins. Set required feature-test
macros before system headers through the established build configuration; do
not scatter declarations or casts around missing prototypes. Inspect available
local manual pages and the selected platform's documentation when an interface
or return-value contract is uncertain. See the [official source map](references/platform-contracts.md).

Describe the changed operation in terms of input, effect, completion condition,
resource ownership, and failure outcome. State whether cancellation can leave
partial effects, which limits bound work, and how callers learn what completed.

## Make progress and ownership visible

For every acquired descriptor, mapping, allocation, lock, and child process,
identify one responsible owner and its release path. Separate borrowed handles
from transferred ownership. Keep partially initialized objects safe to clean
up; publish them only after their required invariants hold.

Descriptor integers are reusable identifiers. Coordinate closing and handoff
with concurrent users; closing a descriptor elsewhere is not a general
cancellation mechanism. Audit `dup` and inherited descriptors as shared open
file descriptions, including offset and status-flag effects. Prefer atomic
close-on-exec creation where supported; applying it afterward can race with
another thread creating a child.

Model I/O as progress over a bounded buffer. Preserve positive byte counts,
advance only the completed range, and distinguish EOF from an error. A short
transfer is not automatically failure. Keep `ssize_t` results signed until
checked; bound each request and prevent size/offset overflow. The
[Linux read contract](https://man7.org/linux/man-pages/man2/read.2.html) documents
these distinctions.

Handle `EINTR` according to the specific operation and cancellation policy,
rather than retrying every syscall indiscriminately. For nonblocking work,
`EAGAIN`/`EWOULDBLOCK` normally means await readiness with retained state.
Readiness is a prompt to attempt progress, not a promise of complete transfer.
Define a response to zero progress so a loop cannot spin forever. Apply
deadlines and fairness budgets when one connection could monopolize the loop.

Do not blindly retry `close` after failure: descriptor state and interruption
semantics depend on the platform, and reuse can make a retry close a different
resource. Check the [target's close contract](https://man7.org/linux/man-pages/man2/close.2.html).
For durable output, distinguish buffered writes, successful close, and the
project's required synchronization protocol.

## Treat processes and signals as protocols

Specify executable selection, argument and environment construction, working
directory, inherited descriptors, process-group behavior, and how startup
failure reaches the parent. Avoid shell interpretation when arguments are
already structured. Use the project's process abstraction, or consider
`posix_spawn` when its available actions fit the required setup.

After `fork` in a multithreaded process, the child cannot safely use arbitrary
library code before `exec`. Keep that path within the applicable
async-signal-safe contract; avoid allocator, logging, and mutex-dependent
helpers. Communicate launch failure through a deliberately designed channel
and use `_exit` on that failure path. Assign child reaping to an explicit owner
and interpret exit status separately from signal termination.

Use `sigaction` with deliberate masks and restart behavior. A signal handler
should record minimal state and arrange a wakeup; ordinary code performs
cleanup. Preserve `errno` if the handler changes it. Follow the
[async-signal-safety rules](https://man7.org/linux/man-pages/man7/signal-safety.7.html)
instead of assuming a small function is safe.

For a self-pipe design, make the handler's write end nonblocking, retain a
pending-state indication, and allow a full pipe to mean that a wakeup is already
queued. Drain and reconcile in normal execution. Coordinate masks and waiting
to avoid a signal arriving between checking state and blocking. In threaded
programs, consider a designated signal-waiting thread with consistent masks.
Make repeated shutdown requests and partial initialization safe.

## Design IPC around bounded state

For streams, define framing, maximum frame length, byte order, parsing state,
and incomplete-message behavior. Reads and writes need not align with protocol
messages. Pipe atomicity has size and concurrency conditions; it does not
remove the need for a receiver's framing contract.

Bound queued data and explain backpressure, overload rejection, and slow-peer
behavior. Distinguish peer closure, truncated input, protocol rejection, and
transport failure. Decide how `SIGPIPE` is handled without silently changing
unrelated code's process-wide behavior. For shared memory, specify initialization,
publication ordering, synchronization, and recovery from an abandoned owner;
`volatile` does not supply a concurrency protocol.

Keep pathname and descriptor operations consistent with the security and
race model. Review symlink following, relative directory handles, permissions,
and source/destination aliasing before truncation or replacement. Preserve the
first meaningful failure through cleanup; report secondary cleanup failures
without replacing the original cause. `errno` matters only at the documented
failure boundary and must be saved before intervening calls.

## Verify the changed boundary

Run the repository's focused checks before broad suites. Compile with its
strict warning policy and inspect diagnostics without suppressing real type,
prototype, or ownership defects. Exercise relevant behavior with controlled
fixtures: short transfers, interruption, readiness races, EOF mid-frame,
exhausted resources, startup failure, child termination, and cancellation after
partial progress. Assert output and externally visible effects as well as exit
status; verify that descriptors, children, and temporary resources are reclaimed.

Use supported AddressSanitizer/UndefinedBehaviorSanitizer lanes for memory and
undefined behavior, and a separate ThreadSanitizer lane for threaded changes.
Exercise process interactions and relevant OS/libc targets independently.
Fault injection must reach the changed operation and prove recovery rather than
merely provoke an unrelated error. Report executed, skipped, and unsupported
checks distinctly. Claim throughput or latency improvements only from
comparable workloads with correctness preserved.
