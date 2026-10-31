# Wayland and desktop integration

Identify the component and the target session before applying compositor
advice. A client, compositor, window manager, shell/panel, greeter, session
manager, portal frontend/backend, and kernel display/input stack own different
parts of a failure.

## Establish the component contract

Record the target compositor/backend, protocol versions, relevant library
versions, GPU/driver and rendering path, seat/session ownership, and whether
execution is nested, headless, on a VM, or on physical outputs/input devices.
Check relevant `WAYLAND_DISPLAY`, `XDG_RUNTIME_DIR`, session bus and display
values selectively, without dumping the user's environment. A privileged
process launched from a shell may lack the graphical user's bus and session.

- Distinguish display/input device permissions and seat activation from a
  renderer or protocol failure. Do not replace logind/libseat integration with
  running the entire compositor as root or broadly changing device permissions.
- Check protocol XML/version negotiation and generated-code procedures. Keep
  resource destruction, listener lifetime, client disconnect, output removal,
  seat removal, and callback reentrancy explicit.
- Keep session-lock state separate from the lock client's resource lifetime.
  Once locked, a locker crash, lost surface, timeout, or output change must not
  expose desktop content or route input to unlocked clients. Preserve protection
  until a valid unlock transition, including during teardown and recovery.
- Treat pending state, committed state, and rendered state as separate until
  the protocol says they advance together. Preserve serial/acknowledgement and
  transaction boundaries; a frame callback is not a generic readiness signal.
- Keep blocking work off the input/render event loop unless the framework's
  contract explicitly permits it. Use the existing event-loop and cancellation
  abstractions; verify cleanup if work completes after a resource disappears.
- Buffer release, rendering completion, presentation, and explicit-sync fences
  are distinct events. Follow the actual graphics/protocol ownership rules;
  a CPU lock cannot by itself prove GPU completion.
- For portal failures, trace application request through the session bus,
  selected portal backend, permission flow, and compositor integration. An
  installed portal package does not prove that the session selected it.

## Lessons from the reference repositories

**Hyprland:** The inspected event-loop code uses owned file descriptors,
registered Wayland event sources, timers, and readable waiters. One readable
callback removes its event source and transfers the waiter out of the live
collection before calling client code, explicitly accounting for reentry.
Preserve such ownership transitions when modifying callbacks. Its Makefile's
`test` recipe runs the `hyprtester` integration harness; CMake registers GTests
separately, and its custom `tests` target only builds the test executable.
Confirm the chosen command executes the relevant tests and record their counts.
Discover target/library requirements from the selected revision; do not assume
a compositor or plugin built against another revision is valid.

**River:** This snapshot is the non-monolithic compositor with a separate window
manager using `river-window-management-v1`. Its architecture describes
`WindowManager`, `Window`, `Output`, and `Seat` advancing manage/render phases;
rendered state is double-buffered. Old river-classic configuration or built-in
tiling assumptions do not establish this version's behavior. The inspected
`zig build test` step runs a slotmap test, so it does not prove compositor,
protocol, input, or rendering coverage. Use its declared Zig and library
requirements rather than a language skill's default compiler.

**COSMIC Epoch:** The root is a component/submodule integration tree. Establish
the responsible component and its recorded revision before claiming an
implementation fact. In the reviewed checkout every component submodule was
uninitialized, so evidence is limited to root documentation, gitlinks and
recipes. Do not infer `cosmic-comp` or `cosmic-session` internals from that.
The root justfile loads dotenv configuration and delegates builds/installs
across components; read recipes before execution without opening secret files.
Fetching components or running broad desktop installation requires the relevant
authority. Preserve pinned gitlinks rather than switching all components to
their newest branch tips.

These are architectural examples, not interchangeable frameworks or a required
desktop choice. Repository contribution policies remain scoped to actual work
on that project; see [sources](sources.md).

## Validate the changed layer

Use pure state/protocol tests where supported, then a nested/headless harness
for client lifecycle and event-loop behavior. Confirm what it exercises. Test
actual DRM/KMS, hotplug, multi-output scaling, input, GPU synchronization,
session lock, suspend/resume, or session startup on the real target only when
the change affects those contracts. A nested compositor does not establish
physical display, seat or session-lock correctness. Lock changes need crash/
disconnect and output-change cases while locked, not just a successful unlock.

Keep the user's active graphical session intact. Starting another greeter,
replacing session services, changing the default session, or restarting the
live compositor is distinct from an isolated test and needs appropriate
authorization. Report the backend, protocol/session scope, observed behavior,
and any hardware or component coverage that remains untested.
