# Artifact inspection, optimization, and diagnosis

## Inspect before rewriting

Record tool versions, installed cross-targets, artifact kind, imports/exports and features. Distinguish compiler presence, dependency resolution, successful cross-compilation, generated binding production and real-host execution; each is a separate prerequisite or result. Core-module tools in WABT include:

```sh
wasm-objdump -x input.wasm
wasm2wat input.wasm -o input.wat
wasm-validate input.wasm
```

Use component-aware wasm-tools for components. Core validation does not establish component linkage. Select the deployment's supported feature set, checking installed `--help`: flags/defaults change. A pass with permissive defaults is weaker than validation against the intended host profile.

WABT feeds selected features into both binary reading and validation. Its matrix separately lists parsing, validation, execution and wasm2c support. Binaryen's SIMD ternary regression requires an extra feature even with basic SIMD enabled. Track complete features across tools and execute the final artifact in its consumer. Proposal phase/meeting agreement does not certify runtime availability.

For cached/AOT artifacts, distinguish a core/component binary from runtime-serialized native code. Wasmtime's unsafe deserialization APIs require trusted, unmodified runtime-produced serialized bytes; they are not validators for arbitrary uploaded WASM. Check provenance and runtime/engine/target compatibility before cache reuse; handle incompatibility through the project's rebuild path. Ordinary source-WASM validation does not establish serialized-code trust.

## Optimize after correctness and measurement

Binaryen wasm-opt optimizes supported core artifacts; WABT inspects/validates. Compare optimization/shrink levels such as `-O3` versus `-Oz` against the actual goal without overwriting the original. Verify feature handling. Do not use `--all-features`, fast-math, trap-changing options or lowering passes merely to hide an error without reviewing semantic/deployment effects.

Validate optimized output against intended features and compare representative public results with the original. Preserve required exports/metadata and debug/source-map artifacts. Package matching glue/binary versions. Smaller code may execute/compile more slowly; compressed transfer and raw binary size differ.

Benchmark download/cache, compile/instantiate, marshaling/copies, worker scheduling, execution, output consumption, peak memory and repeated calls. Compare a suitable JS/native baseline and record input, device/host, cold/warm state, versions and feature variant. Avoid language-wide size claims such as “Rust ~50KB” or “Go ~2MB.”

## Diagnose the failing boundary

| Symptom | Discriminating checks |
| --- | --- |
| Fetch/streaming | HTTP status, URL/base path, application/wasm, CORS/CSP, stale cache |
| Compile/validation | Core vs component, truncation, version, exact unsupported feature |
| Link/instantiate | Import namespace/name/type, glue version, WIT/WASI version/world |
| Trap/corrupt output | Range/encoding, pointer+length bounds, arithmetic, lifetime/growth, cleanup |
| Freeze/memory growth | UI work, interruption, host I/O, output/queue bounds, retained views, instance reset |
| Local success/deployed failure | Asset URLs, probes, isolation/resources, provider limits/compatibility |

Core spec tests express semantics, while proposals/meetings document evolution. Verify current host docs and real deployments where availability matters. Source inspection, upstream test definitions, isolated API probes and target execution remain distinct evidence levels.
