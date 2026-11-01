# WASI, WIT, and host controls

## Select an artifact the host consumes

`wasm32-wasi` is the old Rust target name. Use `wasm32-wasip1` for preview-1 core imports; use `wasm32-wasip2` for a supported WASIp2 command/component host. Neither means every OS facility works. Custom plugin worlds need WIT bindings and export wiring, not merely a changed target triple.

Use the project's component build driver and WIT dependency-resolution order. With targets/dependencies already available, standalone command examples are:

```sh
cargo build --release --target wasm32-wasip1
# Alternative for a WASIp2 component command:
cargo build --release --target wasm32-wasip2
wasmtime run path/to/command.wasm
```

Confirm installed runtime support and CLI options. Install missing targets only within authorization. Go's `GOOS=wasip1 GOARCH=wasm` produces a preview-1 executable. A core module needs compatible componentization/adaptation for a component-only host; adapter versions/ABIs matter. Do not wrap an existing component again or assume any core module adapts to any world.

The compiler target does not uniquely identify the final component's WASI interfaces. The inspected wasmCloud OCI example's build recipe uses `wasm32-wasip2` while its WIT declares `wasi:http/handler@0.3.0`. Inspect final WIT, build wrapper and binding versions, including WASIp3/native async where the project uses them; do not invent a target-triple recipe from the interface version.

## Make a WIT world the contract

An interface names functions/types; a world specifies imports/exports. A complete small contract:

```wit
package example:calculator@0.1.0;

interface math {
    add: func(a: s32, b: s32) -> s32;
}

world calculator {
    export math;
}
```

Generate host/guest bindings for the same world and compatible package versions. Inspect actual output with component-aware tools such as `wasm-tools component wit component.wasm`; validate using supported features. Check installed command syntax.

WIT/Canonical ABI lifting/lowering supplies typed boundaries, not shared native layouts/heaps or zero-copy strings/lists. Resources are handles with ownership/borrowing semantics, not raw cross-component pointers. Preserve resource destruction, borrow scope and post-return cleanup in generated bindings. Represent expected domain failures with an explicit `result` contract; traps are different failures.

Distinguish synchronous WIT functions implemented with async host wrappers from native WIT `async func`, `stream`, and `future` contracts. Inspect generated binding mode, host async/concurrent ABI support and compatible instantiate/call/drop paths in the pinned runtime. Rust `async` alone does not establish that compatibility. Follow the pinned bindings' cleanup lifecycle; check whether post-return cleanup is automatic before adding explicit calls.

Check required imports, WASI interface versions and host functions before instantiation. Test a typed roundtrip and a missing/incompatible import; test resource release where resources exist. A type-correct host function still needs a permission policy. The browser's core `WebAssembly.instantiate` API does not itself load arbitrary components; qualify a component runtime/transpilation path if needed.

## Authority and resource limits are separate

Choose directories/preopens and permissions, environment/arguments, stdio, networking, clocks/randomness and custom host calls. Inspect host defaults instead of assuming all are denied. Imports may delegate powerful behavior; registering WASI is not an authority policy. Do not inherit the entire host filesystem/environment to fix a failing test.

Wasmtime controls have different scopes:

- Guest memory/table/instance limits: attach a limiter to the Store. `StoreLimitsBuilder::memory_size` is per linear memory, not aggregate process memory. The inspected version's ResourceLimiter excludes shared-memory growth and host bookkeeping/allocations. Budget memory/instance counts, host buffers and queued bytes separately as needed.
- Fuel: enable consumption in engine configuration and provide per-Store fuel. Handle exhaustion. Fuel is a guest execution budget, not wall time or a host I/O timeout.
- Epochs: enable interruption, set a Store deadline, and arrange an independent task/clock that advances the engine epoch. The ticker must run independently of the blocked guest and advance the same engine. Check whether deadline behavior traps, renews, or yields in the pinned API. No advancing epoch means no interruption from that deadline.
- Host work: blocking/async imports, network/files, generated output and host allocations need separate bounds/cancellation. Guest interruption does not automatically stop them.

Test controls proportionate to the plugin's trust/resources: finite-success control, allowed/denied path, excess growth, infinite guest loop, slow host import. Guest `memory.grow` may return `-1` on refusal while a host growth API returns an error; not every limit becomes a trap. Preserve error categories for malformed artifact, linkage, trap, domain rejection, permission and budget exhaustion.

If the requirement is a strict whole-process memory budget, investigate platform-supported process/container enforcement and runtime/host overhead separately; a per-guest-memory limit cannot guarantee RSS.

For Wasmer, WasmEdge, wasmCloud, embedded or edge hosts, check their own support/linking/authority APIs; do not translate Wasmtime knobs by name. Embedded deployments also need architecture/AOT compatibility, memory/scheduler limits and board-level evidence.

Sources: [Rust WASIp1](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip1.html), [Rust WASIp2](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html), [WIT reference](https://component-model.bytecodealliance.org/design/wit.html). Local source and unexecuted upstream test anchors: [source-map.md](source-map.md).
