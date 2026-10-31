# Working on the Kotlin compiler or standard library

Apply this only to a Kotlin language/tooling source checkout. Compiler-repository
tasks, build flags, fixture rules, and IDE requirements are not application-wide
Kotlin conventions.

## Identify the area and checkout

Read that checkout's root and area-specific guidance. Determine FIR/K2 frontend,
IR/backend, Analysis API, Gradle plugin, compiler plugin, stdlib, or test
infrastructure before choosing a runner or editing generated code.

The local reference checkout reviewed on 2026-10-16 was
the Kotlin reference checkout at commit
`d0a09eaba269a02ad8db305711a3bb7ff333550e`. Treat its paths and commands as
navigation hints, not proof of another checkout's current contract. This path is
optional source evidence; the skill must work without the external volume.

Useful entry points at that snapshot:

| Area | Evidence |
| --- | --- |
| Root instructions and area routing | `AGENTS.md`, `.ai/guidelines.md` |
| Fixture directives and generated runners | `.ai/testing.md` |
| Build provisioning and aggregate task descriptions | `ReadMe.md` |
| Test ownership and review expectations | `docs/code_authoring_and_core_review.md` |
| Diagnostic text | `docs/diagnostic_message_style_guide.md` |
| Bulk expected-output mutation | `docs/updating_test_data.md` |
| runCatching catches Throwable | `libraries/stdlib/src/kotlin/util/Result.kt` |
| Read-only/mutable collection interfaces | `libraries/stdlib/src/kotlin/Collections.kt` |

Read only the paths needed for the task. The root guide routes compiler and
Analysis API work to their own `AGENTS.md`; do not guess a generic test task
before consulting the relevant area. If the target checkout requires an IDE
tool or generator, follow its actual policy and available approved workflow.

## Test data is executable specification

Compiler fixtures encode language flags, API versions, modules, platforms,
diagnostic markers, and expected output. Preserve those semantics. A regression
may require a diagnostic test, a generated-code/IR check, a runtime box test, or
multiple backends; choose the smallest runner that proves the changed contract.

At the reviewed snapshot, adding fixture files requires test generation and
`*Generated.java` runners should not be edited manually. Inspect the area before
running the repository's `generateTests` task, then review the generated diff.
Do not carry this rule over to arbitrary projects that happen to have generated
Java sources.

Expected-output update flags mutate fixtures. A test that becomes green after
bulk expectation regeneration does not establish that the new behavior is
correct. First explain the intended semantic change, update only relevant
expectations, inspect them, and rerun with automatic updates disabled.

## Build and evidence limits

This repository can bootstrap compilers and provision multiple JDKs and large IDE
dependencies. Avoid an unrequested full build or automatic tool installation
just to read stdlib semantics. A checkout's development compiler and libraries
can differ from the target application's pinned release.

For an implementation change, use area-specific focused checks and the required
broader lanes. Distinguish compiling the compiler, executing its tests, and
compiling/running a user program with the newly built compiler. Cite source
paths/commit and actual diagnostics when explaining a language behavior; do not
infer release availability solely from development-branch source.

## Source

[Kotlin source at the reviewed commit](https://github.com/JetBrains/kotlin/tree/d0a09eaba269a02ad8db305711a3bb7ff333550e)
