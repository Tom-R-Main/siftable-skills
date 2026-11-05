# Source review and evidence boundaries

Read this only when tracing the 2026-11-05 refresh or reassessing a claim.
Guidance is original synthesis; no upstream implementation or transcript is
vendored. Local reference checkouts were inspected read-only at these commits;
they were not fetched, built, or treated as installed production dependencies.

| Source | Inspected evidence | Decision carried into the skill |
| --- | --- | --- |
| [rust-lang/rust at 249c1e4](https://github.com/rust-lang/rust/tree/249c1e4e31111b54ad2483cfd4cea06c7020c653) | `RELEASES.md`; `library/core/src/ops/deref.rs`; unstable-book deref-patterns chapter; `library/core/src/mem/mod.rs`; `AGENTS.md` and dev-guide LLM guidance | Verify 1.99 release claims against release notes; keep `DerefPure`/deref patterns experimental; correct validity example; honor the owning project's contribution policy only in its scope. |
| [Rust SDK at 5596a8a](https://github.com/modelcontextprotocol/rust-sdk/blob/5596a8a0bba2a1ec5519cc855cdadf23e4dcecdc/crates/rmcp/src/service.rs) | Task sets, cancellation selection, bounded response drain | Retain task ownership guidance; distinguish cancellation, draining and progress. The SDK source was not a liveness proof. |
| [Wasmtime at c4ce499](https://github.com/bytecodealliance/wasmtime/blob/c4ce4993c5cab36a0b1445a6e83d7f7dd24745ce/crates/wiggle/src/lib.rs) | `GuestMemory::Unshared` versus `Shared` with `UnsafeCell` | External mutability belongs in the storage/reference contract; do not blindly copy unsafe impls or infer synchronization from `UnsafeCell`. |
| [Polars at be404e6](https://github.com/pola-rs/polars/tree/be404e6312936c1cf4836b26c677dba9faa493f9) | Root manifest; `crates/polars-ffi/src/version_0.rs` release callback and raw ownership transfer | Inspect explicit workspace resolver; review allocation ownership and release-once behavior at FFI boundaries. No claim that the inspected wrapper is sound follows from this audit. |

For variadic ABI restrictions, the Rust checkout's
`compiler/rustc_ast_passes/src/ast_validation.rs` checks ordinary definitions
separately from the import/naked-function allowlist in
`compiler/rustc_abi/src/extern_abi.rs`; target support is separately classified in
`compiler/rustc_target/src/spec/mod.rs`. Release-only triage also checked
`library/core/src/ub_checks.rs` for the limits of debug-assertion checks and the
1.81 release notes for the panic-abort transition.

The user supplied five speech transcripts plus an inline Beyond the Ampersand
transcript. Speech recognition errors and omitted slides make these discovery
sources, not authority for exact symbols or syntax:

- **Beyond the Ampersand:** selected the stable guard reborrow and raw/pinned
  projection distinctions. Handle traits/operators remain design concepts;
  verify experiments in the [Beyond Refs repository](https://github.com/rust-lang/beyond-refs).
- **Oxidizing Fields of Mistria:** selected full-data-path measurements,
  component migration and compatibility sampling. Did not adopt the speaker's
  advice to skip beta testing or infer universal engine/language preferences.
- **BorrowSanitizer talk:** selected foreign-mutation lifetime review and the
  distinction between MIR interpretation and native instrumentation. Verify
  current coverage with the [project](https://borrowsanitizer.com/) and
  [Miri](https://github.com/rust-lang/miri#readme); no talk-time performance or
  parity figures are encoded as current guarantees.
- **Rust 1.99 changelog:** selected only the release-note-backed changes in
  [editions and migration](rust-editions-migration.md). New syntax/APIs were
  documentation-reviewed, not compiled locally. Intermediate build layout is
  not an artifact-discovery contract.
- **Bryan Cantrill talk and Alice Ryhl interview:** reinforced small inspectable
  diffs, compiler feedback plus behavioral evidence, and understanding generated
  code. No celebrity opinion, AI-detector claim, or blanket rewrite policy was
  promoted into a rule. Cantrill's future-lock example motivated checking the
  liveness of unpolled futures separately from cancellation safety.

The executable example suite checks guard reborrowing, rejected direct-guard
and reference-to-guard controls, a rejected escaping guard reference, raw
initialization and zero-initialized `bool` under installed Rust 1.95.0 and 1.98.0.
The two documented examples and borrow-conflict controls cover editions
2021/2024; destructured field references also cover editions 2015/2018.
These checks do not validate aliasing models, foreign code, a Rust compiler
build, BorrowSanitizer, or application performance. Existing gate tests use fake
tools to exercise orchestration; they are not end-to-end compiler verification.
