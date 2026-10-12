# Zig memory diagnostics with Valgrind

Use for CPU-side memory corruption, C/GTK/FFI lifecycle bugs, or leak investigations. Read alongside the project's ordinary safe-mode and allocation-failure tests. Memcheck supplements them; it does not certify complete memory safety.

## Sources and version boundary

Inspected on 2026-10-09:

- Ghostty: [Ghostty](https://github.com/ghostty-org/ghostty), commit `246f702876b924a1cb7cade1e99274d1470302fc`, Zig 0.16 contract.
- Valgrind: [Valgrind](https://sourceware.org/git/?p=valgrind.git), commit `0ff27aab0831786c7f419e73a2b5217cbbcc792d`.
- [Official Memcheck manual](https://valgrind.org/docs/manual/mc-manual.html) and [platform support](https://valgrind.org/info/platforms.html).

Local Valgrind sources: `memcheck/docs/mc-manual.xml` for client requests, leak policy, suppressions, and allocator visibility; `memcheck/tests/mempool2.c` / `.vgtest` for an annotated custom-pool example. A source checkout is not an installed runnable tool. Check the actual executable/version and CPU/OS support before running or claiming a result.

Ghostty patterns below are source observations, not fresh executed tests. Its 0.16 APIs must be checked against the selected compiler before adapting them to 0.17.

## What Ghostty actually does

| Mechanism | Source locator | Consequence |
| --- | --- | --- |
| Separate application and unit-test lanes | `build.zig`: `run-valgrind`, `test-valgrind` | Exercise GUI lifecycle and targeted unit paths separately |
| Baseline CPU target | `build.zig` Valgrind executable/test construction | Avoid unsupported native instructions in the instrumented binary |
| Debug, symbols, frame pointers, unwind tables for tests | `build.zig` construction of `ghostty-test` | Retain useful stack traces; tests explicitly use LLVM |
| Flags: full leak checks, error exit 1, 50 callers, suppression file, suppression generation | `build.zig` Valgrind commands | Unsuppressed counted errors fail the lane; generated suppressions are suggestions, not automatically adopted |
| Dedicated CI job installing Valgrind and libc debug symbols | `.github/workflows/test.yml:valgrind` | Native Linux-oriented memory checking separate from ordinary tests |
| Global allocator switches to libc under Valgrind when libc is linked | `src/global.zig` allocator selection | Memcheck sees individual application allocations through intercepted libc calls |
| Invalid-read bug recorded during GTK disposal | `src/apprt/gtk/class/inspector_window.zig:dispose` | Weak-reference teardown matters even when there is no leak |
| Explicit handling of intentionally undefined parser storage | `src/terminal/Parser.zig:init`, `osc.zig:init` | Tool-visible definedness is considered alongside Zig's compiler behavior |
| Definedness annotation at an opaque internal page-compression boundary | `src/terminal/compress/Page.zig:compress` | Struct padding should not obscure legitimate codec diagnostics |
| Expensive tests/integrity checks skipped; cursor timer slowed | `src/terminal/Page.zig`, `Screen.zig`, `src/renderer/Thread.zig:cursorBlinkInterval` | A Valgrind run is not the same workload or full invariant coverage as a normal run |
| Reviewed suppression policy and graceful app shutdown | `valgrind.supp` introduction, `HACKING.md` memory-leak section | Count suppressed errors separately and allow native resources to tear down |

Ghostty's `test-valgrind` wraps the `src/main.zig` test executable. Separate `test-lib-vt` and ABI-schema steps exist; do not assume this one wrapper exercises every exported library variant. Read the current build graph and test filter.

## Allocator visibility is part of the test design

Memcheck tracks addressability and definedness for executed CPU accesses, but logical allocation boundaries are not automatically visible inside an arena, pool, mmap region, or custom suballocator. Ghostty deliberately routes its global allocations to libc under Valgrind. This improves individual-block visibility; it does not change every page/pool/test allocator in the process.

Options for a project are:

- A libc-backed diagnostic lane for allocations crossing C/host boundaries.
- A safety allocator lane retaining allocator mismatch, double-free, and leak diagnostics.
- Precise custom-allocator annotations using malloc-like/free-like client requests or memory-pool requests, with redzones and unallocated regions marked inaccessible.

Verify the allocator actually used by the test, including nested arenas/pools and third-party allocations. If a diagnostic lane changes allocation behavior, retain a separate lane using the normal representation and its invariants. An overflow within one large addressable slab can corrupt an adjacent logical object without violating Memcheck's visible block boundary.

Check the selected Zig version's `std.valgrind` client-request APIs before writing annotations. The Valgrind manual's pool invariant is explicit: unallocated portions and redzones need to be inaccessible; knowing only the superblock address is insufficient. Use a small intentional invalid-access/definedness case in an isolated test binary when qualifying a new annotation or harness, and confirm that the lane reports it and fails.

## Undefined bytes and padding

Ghostty's parser reassigns intentionally undefined fields in a Valgrind-specific path for a compiler/tool interaction. Do not universalize that workaround without checking the compiler version and reproducing the issue.

For internal raw-memory compression, Ghostty marks a page representation defined because semantically irrelevant padding is deliberately preserved as bytes. `makeMemDefined` changes the tool's shadow state; it does not initialize actual memory, sanitize secrets, validate semantic fields, or establish safe serialization.

Prefer initialized explicit fields and canonical encoding at external persistence/network boundaries. Use a definedness annotation only for a known, addressable range whose representation contract makes undefined padding irrelevant. Do not mark an entire object defined to silence an unexplained branch-on-uninitialized-value report. For diagnosis, `--track-origins=yes` traces undefined-value origins at additional cost; it is an optional diagnostic addition, not one of Ghostty's observed default flags.

## Suppressions and pass/fail policy

Ghostty's suppression file acknowledges possible over-suppression. It includes specific GTK/GLib lifetime behavior and a Zig DEFLATE definedness case. These entries are hypotheses with scope and rationale, not proof that all suppressed bugs are harmless.

When triaging a new report:

1. Reproduce the precise action and inspect allocation/free/use stacks before suppressing it.
2. Fix project-owned lifetime defects where possible. Treat an upstream/driver report as a separate diagnosis.
3. If a suppression is justified, constrain its error kind and stack, document the trigger/version/reason, and retain an unsuppressed reproducer when feasible.
4. Record suppressions used and revisit broad or stale entries after library/toolchain changes.

`--gen-suppressions=all` prints templates; it is not authorization to add them. Avoid wildcarding all project frames or disabling undefined-value diagnostics globally.

Distinguish display from failure policy. `--leak-check=full` plus `--error-exitcode=1` does not mean every retained allocation fails: Memcheck defaults to counting definite and possible leaks as errors, while reachable allocations are a different category. `--show-leak-kinds=all` shows more categories; `--errors-for-leak-kinds=...` separately chooses which fail the lane. Set the policy deliberately for application shutdown versus a short-lived library test, and report suppressed/reachable results rather than hiding them behind a zero exit code.

## Practical workflow

For Ghostty itself, with its selected compiler and already available dependencies, its existing entry points are:

```sh
zig build test-valgrind -Dtest-filter='relevant test'
zig build run-valgrind
```

These are project-specific 0.16 build steps, not commands to impose on arbitrary 0.17 projects. A Zig build can fetch missing dependencies; honor the task's network/install authorization. For a new project, inspect or add an appropriately scoped lane rather than assuming the generic `zig-gates.sh` helper runs Memcheck.

Run native debug/safe tests first; use a narrow Memcheck reproducer second. Retain debug symbols and supported CPU features. Exercise initialization, repeated create/use/destroy, callbacks, cancellation, reconfiguration, and shutdown where the changed lifetime requires it.

For interactive Ghostty, close windows and quit normally. The suppression-file notes explain that SIGINT leaves GTK resources alive and produces a misleading teardown picture. Treat a crash or timeout as incomplete teardown evidence, even when its log also shows leaks. Consider intermediate/delta leak checks for long-running services rather than relying only on exit.

Preserve command, revision, Zig/Valgrind versions, target, allocator lane, suppression file, test filter, skip count, exit status, and full error/leak summary. Do not benchmark under Memcheck: it alters timing, scheduling, and sometimes project behavior.

## Limits and platform selection

Memcheck can expose invalid accesses, bad frees, uninitialized-value use, and leaks along paths actually exercised. It does not prove state-machine correctness, all object lifetimes, GPU device-memory safety, race freedom, or bounded latency. Use ordinary invariant/property/OOM tests and the relevant native device or concurrency tests as separate evidence.

Ghostty skips some integrity checks under Valgrind to control runtime cost; keep their ordinary test lane. A suppressed or skipped defect is not checked by that run.

The official supported-platform table lists Linux ARM64 and AMD64, but no native Apple Silicon macOS target; Darwin coverage is limited to listed older Intel versions. Prefer a supported Linux/native CI environment for this lane on a modern Mac workflow. Do not interpret an unsupported host, absent executable, or harness compile as a successful memory check, and do not install or fetch tools implicitly when authorization is required.
