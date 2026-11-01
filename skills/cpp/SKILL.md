---
name: cpp
description: Implement, review, debug, test, migrate, and optimize C++ code, libraries, native interfaces, templates, and build targets using the project's compiler, standard library, ABI, and verification contract.
---

# C++

Start from the target's actual contract: compiler and standard library, language
mode, platform, build driver, ownership model, error policy, and test membership.
A successful compile with a global compiler does not establish compatibility
with the shipped library or application.

## Establish the contract

Read applicable contributor instructions, nearby implementation and callers,
build definitions, presets/toolchain files, dependency locks, and CI. Locate the
owning target before interpreting a header or changing a shared definition.

```sh
git rev-parse --show-toplevel
rg --files -g 'CMakeLists.txt' -g 'CMakePresets.json' -g 'CMakeUserPresets.json' \
  -g '*toolchain*.cmake' -g 'BUILD' -g 'BUILD.bazel' -g '.bazelrc' \
  -g 'SConstruct' -g 'meson.build' -g 'Makefile' -g 'compile_commands.json' \
  -g 'vcpkg.json' -g 'conanfile.*'
```

Determine, per affected target:

- selected compiler, target triple, SDK/sysroot, standard library and runtime;
- required language level, extensions, exception/RTTI policy, feature macros,
  debug iterator modes, assertions, and relevant compiler flags;
- static/shared linkage, visibility, ABI commitments, host tools versus target
  artifacts, generated code, and supported compiler/platform configurations;
- repository build/test/format commands and which tests exercise this target.

Use the project-selected compiler's version command after locating it. Inspect
recipes before running them: configuration can execute code or fetch dependencies.
Preserve standard level, dependency versions, public layout, and build policy
unless the task changes them. For details and conditional CMake examples, read
[builds and toolchains](references/builds-toolchains.md).

## Load guidance for the changed boundary

- Resource owners, views, invalidation, special members, and native references:
  [ownership and lifetimes](references/ownership-lifetimes.md).
- Exception guarantees, error translation, cleanup and post-failure state:
  [errors and invariants](references/errors-invariants.md).
- Threads, locks, atomics, pools, callbacks, coroutines and shutdown:
  [concurrency](references/concurrency.md).
- Public APIs, templates, headers, overloads, modules and binary compatibility:
  [API, templates and ABI](references/api-templates-abi.md).
- C/host interfaces, operating-system resources, bytes and unchecked operations:
  [systems boundaries](references/systems-boundaries.md).
- Regression tests, sanitizers, fuzzing and measurements:
  [testing and performance](references/testing-performance.md).
- Conditional lessons traced through production code:
  [production patterns](references/production-patterns.md).
- Source identities, evidence limits, authoritative documentation and ecosystem
  discovery: [sources](references/sources.md).

Open only relevant references. Check version-sensitive APIs against the selected
compiler **and** library; a `-std` setting alone does not prove library support.

## Make the narrow change

Trace producer → owner/borrow boundary → consumer → failure and destruction.
For bugs, identify or add a focused regression and observe its failure before
implementing the correction when locally reproducible. Keep unrelated cleanup,
dependency updates, language modernization and architecture changes separate.

Make these decisions visible in the code and explanation:

- who owns, borrows, invalidates, transfers, destroys and may mutate each value;
- which invariant holds after failure, and whether work is retried, discarded,
  rolled back, or left in a documented failed state;
- who owns asynchronous work, releases blocked waits, completes it, and may be
  destroyed by the completion callback;
- which source/API/ABI, wire format, ordering or performance property is promised.

Prefer existing resource wrappers and value types over new manual cleanup.
Choose unique or shared ownership from the lifecycle; `shared_ptr` is not a
general fix for dangling callbacks or data races. Preserve framework ownership,
allocator and thread-affinity rules rather than imposing STL replacements.

Use semantic navigation with the target's compilation database when available.
Compiler diagnostics and repository evidence outrank generic modernization
rules. Do not apply broad formatter, clang-tidy fix, generator, or package-manager
write modes as an incidental step.

## Verify the actual behavior

Use the repository's narrowest relevant runner first, then its required broader
checks. Confirm the changed translation unit is built and the intended tests
are discovered and executed; zero tests, compiled-out assertions, or a disabled
backend do not qualify behavior. There is no universal C++ build command.

Add lanes according to the boundary: host integration for FFI, fault injection
for fallible state, real backend/platform checks, sanitizer or bounded fuzz runs
for memory/byte processing, synchronized schedules for concurrency, and comparable
optimized workloads for performance. Report unavailable lanes without weakening
the contract to obtain a green run.

Report the resulting behavior, preserved invariants, exact checks and relevant
configuration, and remaining limits. Distinguish compile-only, test definitions
read, model exercises, executed component tests, and full application behavior.
