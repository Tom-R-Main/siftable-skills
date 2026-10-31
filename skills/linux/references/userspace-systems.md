# Linux userspace systems

Check the selected libc/runtime wrappers and target kernel behavior. Linux
mechanisms are not automatically portable POSIX behavior, and a kernel release
does not prove a feature is usable in the target sandbox.

## File descriptors and event loops

- Give each FD an owner and define borrow, duplication, transfer, and close.
  Descriptor numbers can be reused; a queued callback must not mistake a reused
  integer for the original resource. Distinguish descriptor flags from shared
  open-file-description state.
- Request close-on-exec atomically at creation where available (`O_CLOEXEC`,
  `SOCK_CLOEXEC`, `pipe2` flags) to avoid another thread's spawn racing a later
  `fcntl`. Confirm intentional inherited descriptors explicitly.
- Handle partial reads/writes, EOF, `EINTR`, `EAGAIN`/`EWOULDBLOCK`, and peer
  close according to the operation's documented semantics. Preserve progress;
  a retry must not duplicate a completed prefix. A zero-byte stream read is not
  the same as an empty datagram. Account for `SIGPIPE`/`EPIPE` on writes.
- Do not blindly retry `close()` on Linux after an error: the descriptor may
  already have been released and reused. Separate error reporting from durable
  write requirements; successful `write` or `close` is not a durability proof.
- Readiness permits an attempt; it does not reserve data or prove a complete
  application message is available. For edge-triggered epoll, use the intended
  nonblocking/drain and rearm contract. Bound buffers and define backpressure.
- Remove event sources, timers, and callbacks before releasing their backing
  objects, using the framework's supported lifecycle. Account for a callback
  that removes itself or invokes code that reenters the event loop.
- Choose clocks deliberately: monotonic elapsed time for deadlines; realtime
  for wall-clock timestamps. Include suspend-time behavior when it matters.

Hyprland's event-loop implementation illustrates source removal before an
invoked callback can reenter, as well as timer and readable-waiter ownership.
This is an example to examine, not proof that every path is race-free.

## Processes, signals, and terminals

Define which process owns spawning, signaling, waiting, and reaping. PID 1,
subreapers, ordinary parents, and service managers have different roles.

- Avoid competing waiters for the same children. Coder isolates its reaper
  from normal subprocess waiting through a separate process; use that as a
  design example rather than introducing a global reaper into every program.
- Handle interrupted waits and preserve exit versus signal termination.
  Runtime-specific wait errors are not ordinary numeric exit statuses. Test
  signal forwarding after handlers are ready, cancellation, and child cleanup.
- Distinguish a PID, process group, session, and cgroup. Sending a signal to
  one PID does not establish that grandchildren stopped. PID reuse also
  matters; choose an existing runtime abstraction or pidfds when appropriate
  and supported, rather than adding a new mechanism by default.
- In a multithreaded program, post-fork child work before exec has severe
  async-signal-safety constraints. Prefer the runtime's established spawning
  primitives. Signal handlers must use supported safe operations; keep complex
  cleanup in normal execution context.
- For PTYs, check controlling-terminal/session setup, foreground process
  group, terminal modes and echo, resize propagation, hangup, and shutdown.
  Track process exit, output completion, and terminal closure separately:
  on Linux an unneeded parent slave FD can keep master reads blocked after
  child exit, while closing the master at process exit can truncate buffered
  output. Close unneeded slave references after spawn and coordinate output
  drain with bounded cancellation/cleanup; report forced truncation separately
  from successful drain. Inspect how the runtime translates PTY hangup errors
  into EOF. Pipes and macOS PTYs do not establish this behavior.
  Keep interactive-shell and noninteractive command tests distinct.
- Use argument arrays for direct execution. When shell syntax is intentional,
  keep data separate and quote for that shell. Do not log full environments,
  token-bearing arguments, terminal contents, or unredacted workspace secrets.

Coder's reaper tests run signal-sensitive checks in a subprocess and synchronize
readiness. That avoids treating an arbitrary sleep or a signal sent to the test
runner as reliable lifecycle coverage.

## Filesystem and isolation boundaries

For path-sensitive or privileged code, state which directory and namespace the
path belongs to. When adversarial path replacement is relevant, prefer dirfd-
relative operations and supported resolution constraints over check-then-open.
An atomic rename and a crash-durable transaction are separate requirements;
inspect filesystem and `fsync` ordering when durability is the task.

Containers share their host kernel. UID mapping, mount/PID/network/user
namespaces, capabilities, seccomp, and LSM rules independently affect an
operation. A container root user is not necessarily host root; user-namespace
root and a capability in one namespace do not grant arbitrary host authority.
Read actual cgroup membership/delegation and v1/v2 layout before changing a
resource controller. Do not assume the application owns its parent's cgroup.

## Test observable behavior

Use a bounded Linux harness with owned child processes, scratch paths, explicit
ready signals, timeouts, and joined cleanup. Choose cases relevant to the change:
partial I/O and backpressure, peer close, signal interruption, cancelled startup,
FD inheritance/reuse, resource exhaustion, and exit during a callback. Assert
output/status and absence of leaked children or handles where observable.

Distinguish syscall errors from wrapper translations. A missing syscall can
justify a documented fallback; `EPERM`, `EACCES`, or another error needs its
own cause before the feature is declared unavailable. Avoid fallback loops
that suppress the original failure.
