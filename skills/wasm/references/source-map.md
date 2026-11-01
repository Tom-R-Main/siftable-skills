# Source map and provenance

## Scope and retrieval

Created for the wasm skill on 2026-11-01. Transfer question: which host, artifact, binding, memory and execution invariants should change an assistant's WASM implementation choices? No application target was supplied; compatibility tests remain candidates.

The maintained source was authored with a private, task-scoped evidence library. That library, its source snapshots and probe artifacts are not distributed here. The pinned source identities below support independent retrieval; they do not supply a configured evidence store or runtime qualification. Use a separately authorized evidence library when applying [repo-learn](../../repo-learn/SKILL.md), and recheck the relevant source and host before consequential reuse.

## Focused mechanisms

- **Owned bytes across guest/worker boundaries:** MDN growth semantics and DuckDB copy/release plus per-message transfer behavior. Local Node API probes support growth/copy/transfer distinctions; DuckDB integration and browser deployments were not executed. Reject a blanket requirement to copy already-owned results.
- **Component artifact and WIT world:** WIT world definitions and Wasmtime's mismatch/typed-call test definitions. Tests were inspected, not run. Reject component machinery for an ordinary browser JS-glue contract.
- **Host authority and separate budgets:** Wasmtime preopens, limiter scope, per-memory limits, fuel tests and epoch example. Not runtime-qualified here. Inspect version-specific defaults; guest limits do not cover all host memory/callbacks.
- **Feature chain and deployment:** WABT reader/validator, Binaryen validator, DuckDB feature/isolation selection, proposal process and spec test scope. Source-supported; no optimizer, browser feature deployment or upstream suite executed. Do not transplant DuckDB's exact feature requirements into other applications.

## Reference navigation

All 15 supplied repositories were metadata-cataloged. The following are navigation routes, not claims that every repository was deeply reviewed:

| Repository | Route when needed | Review depth here |
| --- | --- | --- |
| [wasm-spec](https://github.com/WebAssembly/spec/tree/6057acdb1a213f85369c64454c078a15f11ac4b1) | Core semantics, `.wast` conformance tests, JS API | Core test-scope anchor |
| [wasm-design](https://github.com/WebAssembly/design/tree/6e43416ebc8becd6cdf5d91d9ae7d3712111df32) | Rationale, embedding and security limits | Guest linear-memory isolation anchor |
| [wasm-proposals](https://github.com/WebAssembly/proposals/tree/df6a2aca1cd9d779eb4f2f3e19dae8277f336015) | Proposal status and engine-support pointers | Status/process anchor; not live deployment support |
| [wasm-meetings](https://github.com/WebAssembly/meetings) | Historical design decisions/process | Catalog only; not runtime authority |
| [wasm-component-model](https://github.com/WebAssembly/component-model/tree/fed10b0b823b82553dd8363f16a640816f5eac65) | WIT, worlds, Canonical ABI/resources | WIT world anchor |
| [wasm-binaryen](https://github.com/WebAssembly/binaryen/tree/677ad318579711a259e28c03e4c7cbdfd150b02b) | Optimizer passes and feature validation | Validator + direct regression inspection |
| [wasm-wabt](https://github.com/WebAssembly/wabt/tree/ed1a832d9553158a2a67bf6c6d98a96207a4ee6b) | WAT/binary inspection, feature-scoped core validation | Reader/validator + support matrix |
| [wasmtime](https://github.com/bytecodealliance/wasmtime/tree/b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49) | Component embedding, WASI authority, limits/interruption | Implementations and focused test definitions |
| [wasmCloud](https://github.com/wasmCloud/wasmCloud/tree/c9eda622142ba7c506ee2282697012205c2daff8) | Component builds, WIT resolution and native async HTTP | OCI example interfaces/build and CI recipe anchors |
| [mdn-content](https://github.com/mdn/content/tree/a0ba038b5e77c06c820e90dc39133acb70dd476a) | Browser loading, memory growth and web deployment | Memory growth anchor |
| [duckdb-wasm](https://github.com/duckdb/duckdb-wasm/tree/1f85a503e0c25f0c0980f205915de328c923f476) | Browser worker bindings, feature bundles and byte ownership | Selected implementation and public output test |
| [automerge](https://github.com/automerge/automerge/tree/5bae7757ef7b92c8cd6850def388f22767305ccb) | JS/WASM driver, conditional package exports and packed consumers | Build/glue, initialization, exports and packaging-runner anchors; no CRDT algorithm transfer |
| [Graphite](https://github.com/GraphiteEditor/Graphite/tree/b64765ec9b726130771e4cf2fb9a96eb430f09a0) | Long-lived Rust graphics/editor WASM integration | Vite reload/glue lifecycle anchor; no editor architecture recommendation |
| [tinysearch](https://github.com/tinysearch/tinysearch/tree/d6c92d5a62cec0a09cb153b4ec55365b20c5aa0b) | Static browser search/build packaging | Generated-file test anchor; no browser execution or ranking/performance claim |
| [yew](https://github.com/yewstack/yew/tree/bfa6c19af971084f9547495388bde9aceeb81aaa) | Rust web UI target runners and browser CI | Runner configuration/feature-lane anchors; no framework adoption requirement |

## Captured source identities

| Evidence | Repository / source lines | HEAD |
| --- | --- | --- |
| `ev-c42d5069074fd783357686a5` | `Graphite/frontend/vite.config.ts:77–100` | `b64765ec9b726130771e4cf2fb9a96eb430f09a0` |
| `ev-69618bdf3f5b88bf8a65cc07` | `automerge/javascript/package.json:26–81` | `5bae7757ef7b92c8cd6850def388f22767305ccb` |
| `ev-149bf9d8e083b40e56371d3c` | `automerge/javascript/packaging_tests/run.mjs:350–427` | `5bae7757ef7b92c8cd6850def388f22767305ccb` |
| `ev-99fba4d75a30ad1ca4122ab3` | `automerge/javascript/scripts/build.mjs:113–144` | `5bae7757ef7b92c8cd6850def388f22767305ccb` |
| `ev-8b4b1439c3c3a681b59db07b` | `automerge/javascript/scripts/build.mjs:161–217` | `5bae7757ef7b92c8cd6850def388f22767305ccb` |
| `ev-f7afe919e28f6f6a58d15c94` | `automerge/javascript/src/low_level.ts:88–132` | `5bae7757ef7b92c8cd6850def388f22767305ccb` |
| `ev-cf5a63499d49c4db9a7c98d3` | `duckdb-wasm/packages/duckdb-wasm/src/bindings/bindings_base.ts:708–719` | `1f85a503e0c25f0c0980f205915de328c923f476` |
| `ev-789379d574b05e51bcf9df92` | `duckdb-wasm/packages/duckdb-wasm/src/parallel/worker_dispatcher.ts:380–403` | `1f85a503e0c25f0c0980f205915de328c923f476` |
| `ev-cc6dbb2d308c5dbb00e9537f` | `duckdb-wasm/packages/duckdb-wasm/src/platform.ts:76–124` | `1f85a503e0c25f0c0980f205915de328c923f476` |
| `ev-8bdfee237b77909108515947` | `duckdb-wasm/packages/duckdb-wasm/test/filesystem.test.ts:108–140` | `1f85a503e0c25f0c0980f205915de328c923f476` |
| `ev-358db1ed9a35805ee392d0eb` | `duckdb-wasm/packages/duckdb-wasm/test/filesystem.test.ts:124–147` | `1f85a503e0c25f0c0980f205915de328c923f476` |
| `ev-be78296ceaa9d1b06d596547` | `mdn-content/files/en-us/webassembly/reference/javascript_interface/memory/grow/index.md:72–97` | `a0ba038b5e77c06c820e90dc39133acb70dd476a` |
| `ev-d78ae8f844305d1c8b9e36c2` | `tinysearch/tests/integration_test.rs:27–100` | `d6c92d5a62cec0a09cb153b4ec55365b20c5aa0b` |
| `ev-72203d6f5c4fbbe462572033` | `wasm-binaryen/src/wasm/wasm-validator.cpp:1641–1670` | `677ad318579711a259e28c03e4c7cbdfd150b02b` |
| `ev-7b8a4f4957a1316ff4da8ad4` | `wasm-component-model/design/mvp/WIT.md:155–212` | `fed10b0b823b82553dd8363f16a640816f5eac65` |
| `ev-40be445c9eef37215ff459af` | `wasm-component-model/design/mvp/WIT.md:1570–1580` | `fed10b0b823b82553dd8363f16a640816f5eac65` |
| `ev-aa2728849d3f994fa3614b90` | `wasm-design/Security.md:79–102` | `6e43416ebc8becd6cdf5d91d9ae7d3712111df32` |
| `ev-ce14856c244af8c2bb38b6e8` | `wasm-proposals/README.md:1–83` | `df6a2aca1cd9d779eb4f2f3e19dae8277f336015` |
| `ev-218accd2b4fb41047c4765b2` | `wasm-spec/test/core/README.md:1–11` | `6057acdb1a213f85369c64454c078a15f11ac4b1` |
| `ev-804cbd3d9688bc51e39dabd7` | `wasm-wabt/README.md:37–67` | `ed1a832d9553158a2a67bf6c6d98a96207a4ee6b` |
| `ev-f4092e3bb590f13f0c30a90f` | `wasm-wabt/src/tools/wasm-validate.cc:47–88` | `ed1a832d9553158a2a67bf6c6d98a96207a4ee6b` |
| `ev-70a482e9402d9247645824f4` | `wasmCloud/.github/actions/build-rust-component/action.yml:38–66` | `c9eda622142ba7c506ee2282697012205c2daff8` |
| `ev-f19b08ebebbb19cb52b72941` | `wasmCloud/examples/oci-registry/README.md:61–79` | `c9eda622142ba7c506ee2282697012205c2daff8` |
| `ev-96b6e58f6195e5ee19816afb` | `wasmCloud/examples/oci-registry/src/lib.rs:1–7` | `c9eda622142ba7c506ee2282697012205c2daff8` |
| `ev-d5d3523c70e2713b57694a18` | `wasmtime/crates/wasi/src/ctx.rs:253–310` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-3f206d4d99ac7b81ad22acb0` | `wasmtime/crates/wasmtime/src/config.rs:1305–1322` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-491839296cfdbe648c71c49c` | `wasmtime/crates/wasmtime/src/runtime/component/func.rs:539–573` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-5cb6989ac3752d02118cfaef` | `wasmtime/crates/wasmtime/src/runtime/limits.rs:10–75` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-e8cef3746236d4c1c6b6837b` | `wasmtime/crates/wasmtime/src/runtime/limits.rs:239–260` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-3f4d4ebbc976dac6ff25be7e` | `wasmtime/crates/wasmtime/src/runtime/module.rs:374–421` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-d395c0a9adeb99656ba8fd4d` | `wasmtime/examples/interrupt.rs:1–34` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-ed3abb8d6feb97402874c5f3` | `wasmtime/tests/all/component_model/aot.rs:1–72` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-1d9c98dea2f0692f36f625da` | `wasmtime/tests/all/component_model/missing_async.rs:160–228` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-815ab77884528222a30bf89d` | `wasmtime/tests/all/fuel.rs:452–510` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-39bf4bdcb31115d62760ae70` | `wasmtime/tests/all/limits.rs:5–91` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-841d7d35e49264a7ae1064cf` | `wasmtime/tests/all/module_serialize.rs:1–79` | `b1f81d2ad4fc64fbe0e70a7cc5fccac1a7864c49` |
| `ev-814bc4d54e77ca0a37973a38` | `yew/.cargo/config.toml:1–8` | `bfa6c19af971084f9547495388bde9aceeb81aaa` |
| `ev-012fb1d0c2a3ab5cf31c3f2e` | `yew/.github/workflows/main-checks.yml:95–115` | `bfa6c19af971084f9547495388bde9aceeb81aaa` |

The partial DuckDB test anchor ending at line 140 is retained as a historical read; use the complete 124–147 anchor for the public CSV assertion.

The helper refuses `.wast` as an unsupported extension. The explicitly supplied file `wasm-binaryen/test/lit/validation/simd-ternary.wast:1–10` was inspected directly instead: its negative command enables basic SIMD and expects the FP16 requirement diagnostic. Owning validator code is captured above. A supplemental exact snapshot/hash is in the task outputs; the regression was not run. No helper evidence identity was fabricated for it.

## Initial verification and limits

The maintained source records an isolated authoring probe using tiny core fixtures and built-in Node APIs. Nine checks passed on Node v22.17.1: instantiate overloads, required imports, malformed-module CompileError, guest RuntimeError, growth/owned-copy lifetime, grow(0), shared-buffer extent, clone/transfer, and streaming MIME controls. This is an isolated API probe, not a DuckDB/browser/edge/component integration or performance test.

No reference repository code/test suite was run or changed. No dependencies/toolchains were installed or fetched. Wasmtime, wasm-tools, WABT, Binaryen and wasm-pack executables were unavailable during validation; examples using them were not executed. Rust/Go command examples were checked against official docs, not built. Packaging/schema and fresh-context decision checks do not establish performance/correctness gains in application projects.

Official docs checked during authoring: [Rust WASIp1](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip1.html), [Rust WASIp2](https://doc.rust-lang.org/rustc/platform-support/wasm32-wasip2.html), [Go WASM](https://go.dev/wiki/WebAssembly), [wasm-pack build](https://wasm-bindgen.github.io/wasm-pack/book/commands/build.html), [Cloudflare JS/WASM](https://developers.cloudflare.com/workers/runtime-apis/webassembly/javascript/). Recheck changing host/tool claims when acting. The development wasm-pack book marks some content unpublished; installed versions control available commands.

## Review against code skills and real repositories

A second pass compared Rust, Go, TypeScript and Zig verification contracts, then traced Automerge, Yew, Graphite, tinysearch, wasmCloud and additional Wasmtime/Component Model sources. It repaired repository-driver/language-gate routing, target-specific runner coverage, packed export/initialization acceptance, Node Buffer copy semantics and the failing smoke example. New component guidance separates native async-WIT ABI from async wrappers and final interface versions from target triples. Cached/AOT deserialization now has an explicit trust boundary.

Private authoring records contain the review diff and three new Node probes/results. Those artifacts and the original nine API probes are not bundled. All 38 anchors were reverified fresh after review; 14 of the supplied repositories now have focused captured source, with meetings remaining catalog-only. Upstream suites and real package/browser/component integrations were not executed. No general WASM gate script was added: the real repositories require different drivers and runners.

Pinned Wasmtime cleanup source confirms post-return is handled automatically in that revision and older explicit methods are deprecated no-ops. The skill preserves binding-owned cleanup and asks for a version check; it does not impose manual calls. The new native async and serialized-code cards are distinct additions; driver/consumer/ownership corrections repair existing skill guidance rather than duplicating the older patterns.

## Real compiler and integration execution (2026-11-01)

Follow-up testing built actual compiler output with Go 1.27.0 and Rust 1.98.0, then drove generated bindings in Node 22.17.1 and Chromium 156 over task-owned localhost HTTP. Go JS callbacks, invalid inputs, retained output and shutdown passed in both hosts. Go WASIp1 file/preopen behavior passed with allowed and denied controls in Node WASI. The unmodified installed Go syscall/js suite was compiled to WASM and passed all 37 top-level tests (zero skipped); the parent replay passed the same artifact.

Rust wasm-bindgen 0.2.129 generated Node CJS and web ESM bindings; consumer tests covered numeric ABI, nontrivial bytes, retained output across forced growth, Result conversion and missing-import/pre-init controls. Three wasm-bindgen-test cases passed as compiled WASM under Node, and Chromium passed the public byte/error/lifetime checks. Rust WASIp1 commands passed success, invalid-input and overflow cases through Node WASI. Rust WASIp2 built as a component and was rejected by the core-only loader as expected; component execution remains unverified.

Prerequisite failures repaired the skill: check the installed cross-targets and exact binding CLI/crate pairing; prove offline resolution with the real build rather than extracted source-directory presence. Rust targets were initially absent, then the user explicitly approved installation of wasm32-unknown-unknown, wasm32-wasip1 and wasm32-wasip2 for toolchain 1.98.0. No other dependency download was performed. The isolated Rust fixture used task-local path patches to exact extracted cached sources because registry archive/index availability was incomplete; this does not prove an upstream lockfile build. A copied Tinysearch checkout remained blocked on offline argh resolution, and its lockfile was not altered to disguise that result.

The maintained source also records host-adapter routing and shared-file checks. This portable package uses sibling routes and has no fixed host root or cross-host symlink requirement.

Exact commands, hashes and failed prerequisite logs remain in the private authoring records and are not shipped. The compiler and integration results above are historical source-authoring evidence, not checks rerun against this distribution or a user's project. Node WASI path tests are limited behavior checks, not a security qualification. No Wasmtime/edge-provider execution or performance claim was established. The task-owned HTTP server and isolated browser tab were closed. Initial source-review-only statements above describe the earlier authoring phase and are superseded by this execution record for the lanes actually run.

## Portable package (2026-11-01)

Adapted from the maintained local WebAssembly skill. The entrypoint and three technical references retain their implementation and verification guidance; the source map replaces private store locations and host installation paths with portable source identities and explicit evidence limits. No runtime, compiler, toolchain target, private evidence store, or probe fixture is included. This package routes to the bundled source-language skills and the project's existing build driver.
