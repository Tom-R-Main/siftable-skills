# Go unsafe, CGO, FFI, and platform work

The language specification, `unsafe` package docs, cgo command docs, runtime
pointer rules, and target repository are authoritative.

## Contents

- Unsafe boundary and proof obligations
- CGO ownership and pointer passing
- ABI and representation
- Build, cross-compilation, OS, architecture, and kernel behavior
- eBPF and privileged tests
- Review checklist

## Unsafe boundary

An `unsafe` operation removes specific compiler checks; it does not prove:

- pointer validity or provenance;
- alignment;
- object lifetime or pinning;
- bounds;
- initialization;
- concurrent access;
- GC visibility;
- ABI layout; or
- target portability.

Keep unsafe code small and wrap it in a typed safe API whose preconditions and
postconditions are testable. Put the proof next to the operation when it depends
on details not expressed by types.

Prefer modern helpers such as `unsafe.Slice`, `unsafe.String`,
`unsafe.StringData`, and `unsafe.SliceData` when supported by the module instead
of manually constructing `reflect.SliceHeader` or `StringHeader`. These helpers
still require valid lifetimes and bounds.

Do not store a Go pointer in `uintptr` across an operation that can permit the GC
to move or collect the referenced object. `uintptr` is an integer, not a GC root.
Conversions accepted in one expression may be invalid when split across
statements; read the current unsafe rules.

Run ordinary correctness tests with pointer checking enabled by the repository.
`-gcflags=all=-d=checkptr=2` can provide stronger diagnostics on supported
toolchains but may expose deliberate low-level patterns; interpret rather than
blindly suppress.

## CGO ownership and pointer passing

Define ownership for every allocation and handle crossing the boundary:

- who allocates and frees;
- whether memory may be retained after the call;
- whether callbacks can occur and on which thread;
- whether Go pointers are visible to C across calls;
- how cancellation and partial failure clean up;
- how panics and foreign exceptions/errors are translated.

Go pointers passed to C are constrained because the garbage collector must know
where Go pointers live. Do not let C retain Go memory containing unpinned Go
pointers. Use `runtime.Pinner` only when its exact supported contract fits; it
does not make arbitrary object graphs permanently safe for C.

For C-owned buffers returned to Go, validate pointer/length pairs before making
a slice view. Do not read after free. For Go-owned output returned to C, expose
an explicit release operation if ownership transfers.

Use `runtime/cgo.Handle` for opaque references to Go values passed through C
when appropriate; do not smuggle raw Go pointers through integer fields.

## ABI and representation

Do not assume Go struct layout is a stable C ABI. Account for:

- padding and alignment;
- integer width and signedness;
- endianness;
- pointer size;
- packed foreign structs;
- flexible arrays and unions;
- calling convention and symbol visibility;
- ownership of strings and NUL termination;
- thread-local or callback requirements.

Prefer a small C ABI using fixed-width types, opaque handles, and
pointer-plus-length pairs. Add compile-time/static assertions on the foreign side
and runtime/round-trip tests on supported targets.

## Build and cross-compilation

CGO builds depend on the C compiler, linker, headers, libraries, pkg-config,
sysroot, and target triple. `GOOS`/`GOARCH` alone is not enough.

- Check `CGO_ENABLED`, `CC`, `CXX`, `PKG_CONFIG`, build tags, and repository
  container/toolchain.
- A local pure-Go test may exclude all CGO files and therefore say nothing about
  the FFI implementation.
- Cross-compiling may compile but cannot execute tests without a target runner.
- Race, ASan, and MSan support is target/toolchain-specific and can be mutually
  incompatible with other modes. Follow repository CI.
- Do not add host-installed libraries or network-fetched toolchains without
  authorization.

## OS, architecture, and kernel behavior

Platform-specific work needs both compile coverage and behavior coverage.

- Use filename suffixes and build tags consistently with nearby code.
- Keep shared semantics in common files and isolate irreducible syscall/ABI
  differences.
- Translate platform errors without losing inspectable causes that callers rely
  on.
- Preserve partial-read/write, EINTR, timeout, and close semantics.
- Document externally discovered quirks with a source or issue when the code
  would otherwise look unnecessary.
- Avoid changing unrelated timeout or retry thresholds while fixing one
  platform mechanism.

## eBPF and privileged tests

Go wrappers around eBPF involve several contracts at once: Go API, ELF/BTF,
kernel verifier, generated bindings, byte order, kernel version/features,
capabilities, and resource lifetime.

- Use the repository's BPF compiler/container and generator versions.
- Treat generated object files and bindings as coupled outputs.
- Make fd and map/program/link ownership explicit; copying a Go wrapper does not
  duplicate the kernel resource safely unless documented.
- Distinguish compile-only tests, simulator tests, unprivileged tests,
  privileged live-kernel tests, and kernel-matrix CI.
- Record the kernel, architecture, privileges, and features used for validation.
- Error paths must close partially created fds and detach links according to the
  API contract.

## Unsafe/FFI review checklist

- Can the same result be expressed safely with acceptable measured cost?
- Is each pointer valid, aligned, in bounds, initialized, and alive long enough?
- Does the GC know about every live Go pointer?
- Are allocation and release responsibilities explicit on every path?
- Are callbacks, threads, cancellation, panic, and foreign errors translated?
- Is ABI layout verified rather than assumed?
- Were pure-Go and CGO variants both selected intentionally?
- Were supported targets compiled and real boundary behavior exercised?
- Did generation use pinned tools and leave an understood diff?
