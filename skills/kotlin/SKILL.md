---
name: kotlin
description: Implement, review, debug, test, migrate, or optimize Kotlin code and builds. Use for .kt/.kts, Kotlin API and Java interop, coroutines and Flow, Gradle Kotlin configuration, JVM backends, Android/Compose, Kotlin Multiplatform, and Kotlin compiler or standard-library contributions.
---

# Kotlin

Work from the project's selected compiler, build driver, source sets, and callers.
Kotlin, Gradle, AGP, JDKs, compiler plugins, and kotlinx libraries have distinct
compatibility constraints; remembered APIs or a reference checkout cannot resolve
those constraints for the target project.

## Establish the project contract

Read applicable repository guidance, the affected implementation and tests, and
the build configuration before editing or executing build scripts. Identify:

- Application, library, build logic, script, or Kotlin compiler repository.
- Gradle wrapper or other driver, included builds and convention plugins,
  affected modules, variants, source sets, and configured consumers.
- Kotlin/KGP version, `languageVersion` and `apiVersion`, opt-ins, compiler
  plugins, stdlib, coroutines, and serialization versions.
- Gradle runtime JDK, Java/Kotlin compilation toolchains and bytecode targets,
  Android SDK/AGP, and any Apple, JS, Wasm, or Native requirements.
- CI's actual test, analysis, API compatibility, and generation commands.

Start with a focused inventory, excluding generated outputs and dependencies:

```sh
git rev-parse --show-toplevel
rg --files -g 'AGENTS.md' -g '*gradle*' -g '*versions*.toml' \
  -g 'pom.xml' -g 'mvnw*' -g '*detekt*' -g '*ktlint*' -g '.editorconfig' \
  -g '!**/build/**' -g '!**/.gradle/**' -g '!**/node_modules/**'
```

Inspect relevant configuration selectively; do not dump properties files or
environment variables that may contain credentials. A global `kotlinc` version
does not establish the compiler used by Gradle or an IDE.

Gradle configuration executes code even for `help` or `tasks`; wrapper bootstrap
can download Gradle even for `--version`. Inspect wrappers and build logic first;
respect the session's network and write permissions. `--offline` is a dependency
resolution option, not a network sandbox or a guarantee that a wrapper cannot download.
For build failures or migrations, read
[builds and toolchains](references/builds-toolchains.md).

## Select focused guidance

Read only the references needed by the change:

| Concern | Reference |
| --- | --- |
| Nullability, domain types, generics, collections, Java interop, public ABI | [Language and API design](references/language-api-interop.md) |
| Coroutine owners, cancellation, supervision, Flow, state and events | [Concurrency and Flow](references/coroutines-flow.md) |
| Tests, virtual time, real execution, profiling and benchmarks | [Testing and performance](references/testing-performance.md) |
| Source sets, expect/actual, Native, Android, Compose, AGP migration | [Multiplatform and Android](references/multiplatform-android.md) |
| Ktor, Spring, persistence boundaries, JSON and generated serializers | [Backends and serialization](references/backend-serialization.md) |
| Native handles, callback adapters, resource-backed queries, offline sync, engine threads, and lessons from real applications | [Production patterns](references/production-patterns.md) |
| FIR, IR, compiler diagnostics, stdlib, generated test runners | [Kotlin repository work](references/compiler-repository.md) |
| Provenance, official documentation, and upstream skill comparisons | [Sources](references/sources.md) |

## Implement against the contract

- Model invalid states deliberately: narrow nullable or external input at the
  boundary, use meaningful types and exhaustive outcomes, and keep public
  abstractions small. Match local idioms; scope functions and extensions should
  clarify ownership and control flow.
- Treat `val`, read-only collections, and data classes as separate concepts.
  They do not by themselves make an object graph immutable or thread-safe.
- Keep cancellation observable. Broad catches and `runCatching` around suspend
  work need particular scrutiny; converting cancellation into an ordinary
  failure changes the owner's lifecycle contract.
- Keep asynchronous work attached to its actual owner. Prefer a suspending
  operation when the caller owns completion; choose state/event primitives
  from required replay, fan-out, loss, and acknowledgement semantics.
- Identify framework-specific execution and shutdown boundaries: a render
  thread, Android main thread, native session, and persistent worker have
  different contracts. Preserve the repository's adapters and state-holder
  architecture rather than replacing them to match a generic Kotlin example.
- Preserve source, binary, wire, and behavior compatibility independently.
  Default parameters and successful consumer recompilation do not prove ABI
  compatibility for existing binaries.
- Avoid incidental dependency upgrades, architectural migrations, generated
  edits, suppressions, or opt-ins that only hide a failed gate.
- For a defect, use a focused reproducer or regression test when practical.
  Confirm the observed failure and smallest correction; state when the original
  environment cannot be reproduced.

For reviews, trace a concrete transition from producer through stored state to
consumer, including actual keys, conflict policies, and failure return paths.
Check that the trigger is allowed by upstream contracts. Keep read-only review
reproducers outside the target repository, and distinguish source reasoning,
source-derived harness results, and original Kotlin/application execution.

## Verify the changed behavior

Use the repository's commands, starting with the affected module and target.
Discover task names from its build scripts and CI configuration and, when execution is permitted, its
task listing. Do not assume every project has `test`, `allTests`, or `detekt`.

Examples below apply only if those exact tasks and test filters exist:

```sh
./gradlew :service:test --tests 'example.AccountServiceTest'
./gradlew :service:check
./gradlew :app:testDebugUnitTest
./gradlew :shared:jvmTest
```

Run configured analysis in check mode, appropriate consumer/API gates, and any
platform lanes affected by shared code. Confirm tests executed: `NO-SOURCE`,
skipped tasks, cached reports, and compilation alone do not prove a new runtime
behavior. Use a bounded artifact-level smoke test for a changed CLI, service,
library boundary, or UI flow when that is the behavior under review.

Report the change, selected versions/targets where relevant, commands and
observed results, and material gaps. Separate code failures from missing caches,
toolchains, devices, services, or host support. Claim performance improvements
only from comparable measurements with correctness checks.
