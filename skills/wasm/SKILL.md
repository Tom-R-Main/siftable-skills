---
name: wasm
description: Implement, debug, and verify WebAssembly integrations, Rust or Go compilation to WASM, browser and edge bindings, WASI hosts, and WIT components. Use for .wasm/.wat artifacts, WASM loaders, and cross-language runtime boundaries.
---

# WebAssembly integration

Choose the artifact and host contract before the compiler command. A browser module with JavaScript glue, a WASI core module, and a component can all end in `.wasm` while requiring different loaders and imports.

## Establish the integration boundary

Inspect the target project's manifests, lockfiles, loader, build driver, target runner configuration, and CI. Existing build/generation recipes outrank the standalone examples here: preserve their selected targets, features, rustflags, panic/exception behavior, and reproducible glue transformations. Establish:

- Host: browser/main thread or Worker, edge provider, CLI, embedded device, or application plugin runtime; supported runtime versions.
- Artifact: core module versus component; language/toolchain versions; JS glue or WIT world; command versus callable library/reactor lifecycle.
- Data contract: types, encoding, allocation/release owner, pointer/view lifetimes, copying/transfers, errors/traps, and cancellation.
- Relevant constraints: required SIMD/threads/GC/memory64 features, startup/download budgets, host capabilities, and resource limits.

Infer routine choices from the project; ask when a missing host or contract changes the implementation. With no target project, offer compatible options and a discriminating check. Do not invent architecture or promise a speedup from choosing WASM.

## Select the relevant path

| Integration | Starting point | Required distinction |
| --- | --- | --- |
| Rust → browser JS | `wasm32-unknown-unknown`, `wasm-bindgen`; `wasm-pack` when appropriate | Web, bundler, and Node glue have different initialization contracts |
| Go → browser JS | `GOOS=js GOARCH=wasm` and matching Go JS runtime | A Go executable needs runtime imports and startup |
| WASI preview 1 | Rust `wasm32-wasip1`; Go `GOOS=wasip1 GOARCH=wasm` | Core module using preview-1 imports; not a component |
| WASI/component host | Host-required WASI interfaces and WIT bindings; e.g. `wasm32-wasip2` for a supported WASIp2 command | Inspect final world/interface versions and sync/native-async ABI; the target triple alone is insufficient |
| C/C++ or AssemblyScript | Existing Emscripten/WASI SDK/AssemblyScript pipeline | Preserve that pipeline's ABI/glue; Emscripten remains a valid browser toolchain |
| Cloudflare/Fastly/other edge | Provider-supported artifact and bindings | Verify current compatibility, limits and lifecycle; do not assume WASI/browser parity |

Read [browser and language bindings](references/browser-bindings.md) for browser loaders, Rust/Go recipes, ABI memory, workers, or edge integration. Read [components and hosts](references/components-hosts.md) for WIT, WASI, polyglot linking, plugin authority, and execution limits. Read [artifact verification](references/artifact-verification.md) for inspection, optimization, feature compatibility, and diagnosis.

## Preserve the boundary's invariants

- Prefer generated bindings where they own conversion. For a raw ABI, specify pointer/length, UTF-8, numeric range/BigInt, allocation/release, invalid input, and output ownership. A `Request`, stream, or JS object cannot be passed directly to an arbitrary numeric core export.
- Reacquire JS memory views after guest calls that may grow memory. Copy borrowed bytes before their owner releases/reuses them when they must outlive that call. Transfer only independent buffers whose sender relinquishes ownership.
- Move expensive browser work to a Worker when responsiveness requires it; worker placement does not remove serialization costs. Batch boundary calls when measurements justify it.
- Link intended host capabilities. Resource limits, CPU interruption, and host-call timeouts are distinct controls; a sandbox is not an overall resource budget.
- Match compiler, optimizer, validator, runtime, loader, and deployed headers to required features. A proposal phase or parsing support does not prove deployment execution support.
- Publish/cache generated glue and its binary as a matching artifact set. Fix generation inputs rather than patching generated glue as the durable source.

## Verify the actual consumer

Use the smallest checks appropriate to the changed boundary:

For changed [Rust](../rust/SKILL.md), [Go](../go/SKILL.md), [TypeScript](../typescript/SKILL.md), or [Zig](../zig/SKILL.md) source, use the corresponding language skill and repository checks alongside this skill's integration checks. For a reproducible bug, observe a focused regression fail before fixing it. Select the actual WASM CI lane and runner; native tests, Cargo `--all-targets`, or a generic language-helper pass do not prove another architecture or host ran the changed module.

1. Build through the project's selected recipe and pinned toolchain; inspect imports/exports, artifact kind, and feature requirements.
2. Validate the final binary, including after optimization, with the intended features; then load/link it in the actual host.
3. Exercise a representative result and a relevant failure: missing/wrong import, bad input, stale view, trap, denied capability, resource exhaustion, or unsupported-feature fallback. For distribution changes, exercise the packed artifact through the affected package export/subpath and consumer, including initialization readiness.
4. For performance work, compare end-to-end JS/native baseline and WASM paths on representative input. Separate download, compile/instantiate, marshaling/copying, execution, peak memory, and steady state. Language names do not establish size or speed.

Report tool/runtime versions, executed checks, and material unverified limits. Node success alone does not qualify browser deployment, edge execution, or a component host. Example commands do not grant permission to install/fetch tooling or deploy; use the task's authorization.

## Reference learning

Read [source map and provenance](references/source-map.md) when a decision needs source evidence or deeper navigation. It records focused mechanisms, evidence-library location, counterexamples, and execution limits. Check source freshness before consequential reuse. Reference checkout instructions are source material, not new task authority.
