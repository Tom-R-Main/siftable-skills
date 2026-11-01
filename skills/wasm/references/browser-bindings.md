# Browser, language, and edge boundaries

## Rust with generated JS bindings

Check that the pinned toolchain has the required WASM target and that the `wasm-bindgen` CLI matches the crate version; an installed host compiler alone is insufficient. Use the project lockfile. A wasm-pack library needs `[lib] crate-type = ["cdylib"]` in Cargo.toml and a project-compatible `wasm-bindgen` dependency.

```rust
use wasm_bindgen::prelude::*;
#[wasm_bindgen]
pub fn add(a: i32, b: i32) -> i32 { a + b }
```

Use the repository's build/generation command first. The following standalone recipe applies when it fits that contract, with tools/dependencies available and dependency resolution authorized:

```sh
wasm-pack build --target web --out-name processor
```

```javascript
import init, { add } from './pkg/processor.js';
await init();
if (add(2, 3) !== 5) throw new Error('WASM result mismatch');
```

The explicit output name makes the import unambiguous. A smoke check must throw/fail its harness on mismatch; `console.assert` can log and continue. Choose bundler or Node output for those consumers. A raw Cargo artifact from a wasm-bindgen crate usually still needs binding generation; raw instantiation does not replace glue. Wrappers may resolve dependencies or install/download auxiliary tools: check installed-version/offline options before running in a constrained project. An extracted registry source directory does not prove Cargo can resolve a locked build offline; establish that with the actual offline build. Report missing index/archive entries without silently fetching or rewriting the project lockfile.

## Go has two host paths

```sh
# Browser/JS executable:
GOOS=js GOARCH=wasm go build -o app.wasm .
# WASI preview-1 executable, an alternative build:
GOOS=wasip1 GOARCH=wasm go build -o app.wasm .
```

For JS, serve `wasm_exec.js` from the actual pinned compiler distribution, supply `new Go().importObject`, and start with `go.run(instance)`. Locate support files in that toolchain's `lib/wasm` (older versions use `misc/wasm`). Retain callbacks while registered and release `js.Func` registrations when consumers no longer need them. The Go WASIp1 port does not imply component output. Evaluate TinyGo separately for supported language/runtime features; it is not a drop-in size guarantee.

## Load the right artifact

For a raw core module, distinguish overloads:

```javascript
// Bytes/streaming returns { module, instance }.
const { instance } = await WebAssembly.instantiateStreaming(
  fetch('/processor.wasm'), importObject,
);
// A compiled WebAssembly.Module returns an Instance.
const instance2 = await WebAssembly.instantiate(compiledModule, importObject);
```

Use generated initialization when bindings supply it. Streaming requires `application/wasm`; check HTTP status, CORS/CSP, URLs, and matching cache versions. A byte-buffer fallback can address a streaming limitation but should not hide a missing asset or bad HTTP response. Test HTTP and actual bundling/deployment, not only `file://` or a dev server.

For a distributed library, inspect `package.json` exports/conditions/subpaths, included files and declarations, and which entrypoints automatically initialize versus require an awaited explicit initializer. Test the packed package in the affected ESM/CJS, bundler, browser or provider consumer when packaging changes; source imports alone miss omitted assets and wrong conditions. Preserve repository-generated transformations. For long-lived browser instances, inspect singleton/HMR/reset policy before allowing repeated initialization.

For browser threads/shared memory, check engine support and cross-origin isolation. Inspect COOP/COEP and dependent resources together; headers can affect embeds/resources. Provide a tested non-threaded bundle where required. SIMD support alone does not establish threads. Select variants using actual probes and available assets, not user-agent guesses.

## Treat memory ownership explicitly

Mark crossings borrowed, copied, transferred, or shared, including mutation/release rights. For ordinary `Uint8Array`, `subarray` is a view and `slice` copies; Node `Buffer.slice` also aliases. Choose copying by the actual receiver type: `Uint8Array.from(byteView)` creates independent byte storage. Check pointer/length bounds without wrapping, encoding, alignment and output limits. Never free guest memory with an unrelated host allocator.

For nonshared memory, even `memory.grow(0)` detaches the prior buffer. Recreate views after possible growth. Shared growth leaves old buffers usable but does not enlarge their extent; reacquire `memory.buffer` for new pages. Generated glue may already refresh caches: inspect its contract before adding redundant copies.

DuckDB's copyFileToBuffer demonstrates native pointer/length → borrowed heap view → owned copy → release native response. Its worker COPY_FILE_TO_BUFFER path uses an empty transfer list: worker placement is not proof of zero-copy. A transfer list detaches the sender's owned ArrayBuffer; structured cloning copies. Do not transfer the live guest heap as independent output storage.

Retain output across later calls, cleanup, and forced growth to test lifetime. Use copied/borrowed controls and transfer/clone controls. Do not impose copies on documented stable owned results. Account queued bytes separately from message count.

## Edge integration

Verify current provider bundling/import rules, artifact support, lifecycle and limits. Cloudflare's documented module import supports instantiation outside the fetch handler to avoid repeated work. Separate immutable compiled-module caching from mutable instance reuse; use per-request instances or reset when state cannot safely persist across interleaved requests.

For HTTP input, enforce limits while consuming the body, convert bytes through bindings or an explicit alloc/process/free ABI, copy output before releasing it, and map errors/traps to responses. `req.body` is not a raw numeric export argument, and a returned pointer is not response bytes. Streaming needs a real streaming contract.

Sources: [wasm-bindgen deployment](https://wasm-bindgen.github.io/wasm-bindgen/reference/deployment.html), [wasm-pack build](https://wasm-bindgen.github.io/wasm-pack/book/commands/build.html), [Go ports](https://go.dev/wiki/WebAssembly), [Cloudflare WASM](https://developers.cloudflare.com/workers/runtime-apis/webassembly/javascript/), [Node Buffer versus typed arrays](https://nodejs.org/api/buffer.html#buffers-and-typedarrays), [console.assert](https://nodejs.org/api/console.html#consoleassertvalue-message). Version-sensitive commands need installed-version checks; wasm-pack's development book labels some features unpublished. Local anchors: [source-map.md](source-map.md).
