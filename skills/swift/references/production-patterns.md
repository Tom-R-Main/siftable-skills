# Source-backed production patterns

Reviewed 2026-11-01. These are bounded source observations and candidate transfer
rules, not runtime certification or blanket endorsements of the repositories.
All links pin the inspected commit. Upstream tests below were read, not run.

## Waiters and timeout races

OpenClaw at `17fdb02f60f5ef5fb3310cf2af8c603b05ae65dc`:

- [LocationServiceSupport.swift, 24–62](https://github.com/openclaw/openclaw/blob/17fdb02f60f5ef5fb3310cf2af8c603b05ae65dc/apps/shared/OpenClawKit/Sources/OpenClawKit/LocationServiceSupport.swift#L24-L62)
  stores continuations by request UUID, drains them before resuming, and removes
  only the cancelled caller. It stops the shared platform request when no
  registered waiters remain. Admission checks cancellation before installing a
  continuation; cleanup hops back to the main actor.
- [AsyncTimeout.swift, 1–135](https://github.com/openclaw/openclaw/blob/17fdb02f60f5ef5fb3310cf2af8c603b05ae65dc/apps/shared/OpenClawKit/Sources/OpenClawKit/AsyncTimeout.swift#L1-L135)
  explicitly models cancellation before admission and registers racer handles
  under the same mutex. Resolution consumes the continuation once, then cancels
  handles and resumes outside the lock. Its unstructured race avoids joining a
  cancellation-ignoring loser; the source assigns cleanup and stale-result safety
  to callers.

Transfer: distinguish per-caller completion from shared operation ownership, and
deadline response from effect termination. Reuse only after checking framework
callback/coalescing semantics, executor, toolchain and deployment availability.
Do not copy the mutex/timeout implementation into every async method.

Counterexamples: cancelling caller A globally can strand B; missing the
cancel-before-install state leaves a waiter alive forever; returning on timeout
can leave an uncooperative operation producing effects later. Next target test:
control admission and callback timing, cancel one of two callers, then require
the other to finish exactly once; separately track late effects after timeout.

## Native lifetime and fallible close

Ghostty at `2f967e3a6ab231188c29a97fb422e479a254e97c`:

- [Ghostty.Surface.swift, 11–83](https://github.com/ghostty-org/ghostty/blob/2f967e3a6ab231188c29a97fb422e479a254e97c/macos/Sources/Ghostty/Ghostty.Surface.swift#L11-L83)
  transports a native handle while marking operations with execution constraints.
  Its deinitializer frees immediately on the main thread or schedules main-actor
  destruction from another thread. The source explicitly notes that the deferred
  path cannot await completion.
- [SurfaceView.swift, 615–685](https://github.com/ghostty-org/ghostty/blob/2f967e3a6ab231188c29a97fb422e479a254e97c/macos/Sources/Ghostty/Surface%20View/SurfaceView.swift#L615-L685)
  passes unretained view userdata and scopes C-string arguments around native
  surface creation. The native callee's retention/copy contract still needs
  checking before transferring this arrangement.

DuckDB at `910c73dabeafc0290907a0c37e09f6abed8e9446`:
[Appender.swift, 68–143](https://github.com/duckdb/duckdb/blob/910c73dabeafc0290907a0c37e09f6abed8e9446/tools/swift/duckdb-swift/Sources/DuckDB/Appender.swift#L68-L143)
retains its connection, exposes a throwing `flush`, and attempts `try? flush()`
before native destruction in `deinit`. That fallback cannot report durability
failure to a caller. It motivates explicit fallible finalization when success
matters, not a claim that this wrapper is leak-free on every initialization path.

OBS at `65c320b46e1af5c7a555161aea6182cdf7a8c524`:
[OBSSwapChain.swift, 106–125](https://github.com/obsproject/obs-studio/blob/65c320b46e1af5c7a555161aea6182cdf7a8c524/libobs-metal/OBSSwapChain.swift#L106-L125)
separates retained from unretained opaque exports. This declaration alone does
not prove every consuming C caller balances them correctly.

Transfer: specify owner lifetime, borrowing, native API affinity, fallible close
and acknowledged teardown separately. Reject generic actor-only adapters for
fixed-thread APIs. Next target tests: native callback during/after close,
background last-release, repeated create/destroy, and an injected flush failure
that must remain observable. A successful ARC release is not a successful flush.

## State and rendering boundaries

Bitwarden iOS at `e915735c6cf66d953fdd42ec74dcc9a1d06e3484`:
[Store.swift, 1–135](https://github.com/bitwarden/ios/blob/e915735c6cf66d953fdd42ec74dcc9a1d06e3484/BitwardenKit/UI/Platform/Application/Utilities/Store.swift#L1-L135)
adapts a main-actor processor's publisher, synchronous actions and async effects
into a view-facing store. [StoreTests.swift, 1–130](https://github.com/bitwarden/ios/blob/e915735c6cf66d953fdd42ec74dcc9a1d06e3484/BitwardenKit/UI/Platform/Application/Utilities/StoreTests.swift#L1-L130)
assert forwarding, child-store mapping, binding actions and async effects.
These assertions support testing the adapter contract; they do not prove the
app's navigation or automatically establish cancellation for every effect.

A2UI at `825beac2813a6d0ccef3b6fb4124ad6c3c8419f0`:
[SurfaceRedrawTests.swift, 16–221](https://github.com/a2ui-project/a2ui/blob/825beac2813a6d0ccef3b6fb4124ad6c3c8419f0/swift/swiftui/Tests/A2UISwiftUITests/SurfaceRedrawTests.swift#L16-L221)
hosts SwiftUI under AppKit/UIKit, flushes layout, and counts which components
rebuild after a leaf update. It also checks an unrelated data update causes no
component redraw. This is stronger invalidation evidence than a model mutation
alone, but the fixture's serialized/main-actor setup and layout pumping remain
part of the test contract. Counts do not measure frame time or usability.

Transfer: preserve the existing state owner and verify each seam at the right
layer. Reject mandatory Store/Processor adoption or a universal observation
migration. Next target test: send a real binding/action, observe the resulting
state and hosted update, then separately drive the app's actual entry path.

## Build drivers and wire contracts

Stripe at `a574b182e6098525af8945d22d092f2f1fdff3fa`:
[Package.swift](https://github.com/stripe/stripe-ios/blob/a574b182e6098525af8945d22d092f2f1fdff3fa/Package.swift)
declares tools 6.1, language mode `.v5` and library targets, with no test targets
in that manifest. Its [agent guide](https://github.com/stripe/stripe-ios/blob/a574b182e6098525af8945d22d092f2f1fdff3fa/AGENTS.md)
routes tests through the repository's simulator-aware runner. A generic
`swift test` instruction would miss the intended SDK test owner.

[URLEncoder.swift, 49–106](https://github.com/stripe/stripe-ios/blob/a574b182e6098525af8945d22d092f2f1fdff3fa/StripeCore/StripeCore/Source/Helpers/URLEncoder.swift#L49-L106)
and [URLEncoderTest.swift, 1–61](https://github.com/stripe/stripe-ios/blob/a574b182e6098525af8945d22d092f2f1fdff3fa/StripeCore/StripeCoreTests/Helpers/URLEncoderTest.swift#L1-L61)
establish nested bracket keys, indexed arrays and escaping as observable request
semantics. Replacing that contract with a fashionable serializer is not a safe
refactor merely because it compiles.

A2UI's [manifest, 54–145](https://github.com/a2ui-project/a2ui/blob/825beac2813a6d0ccef3b6fb4124ad6c3c8419f0/Package.swift#L54-L145)
instead owns generation plugins and core/UI test targets. Identify resources,
generation and platform guards before assuming a test target runs on Linux.

Transfer: select verification from actual target membership and preserve
consumer-visible bytes. Next target check: prove the chosen test was selected
and executed, then compare representative wire output against a consumer fixture.

## Examples that need more evidence

CUA at `0cdcec94bc9988d41087d470b32f1fad2ba28691`:
[VMVirtualMachineLifecycleMonitor.swift, 1–59](https://github.com/trycua/cua/blob/0cdcec94bc9988d41087d470b32f1fad2ba28691/libs/lume/src/Virtualization/VMVirtualMachineLifecycleMonitor.swift#L1-L59)
uses a terminal-event stream, a mutable `finished` flag and `@unchecked Sendable`.
The snippet alone does not prove all callback and host-stop paths serialize;
inspect owning queues/callers before calling it safe or identifying a race.
Do not promote its annotation into generic advice.

whisper.cpp at `482279b8a18855ba741d7b88c30fcb3874691f59`:
[LibWhisper.swift, 1–57](https://github.com/ggml-org/whisper.cpp/blob/482279b8a18855ba741d7b88c30fcb3874691f59/examples/whisper.swiftui/whisper.cpp.swift/LibWhisper.swift#L1-L57)
puts a C context behind an actor and scopes string/sample buffers around a
synchronous native call. This demonstrates exclusion and borrowing; it does
not establish a fixed thread, cooperative cancellation, or a recommended CPU
thread count. Verify those native requirements independently.
