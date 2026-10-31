# Builds, toolchains, and migrations

Reviewed 2026-10-16. Resolve version-sensitive DSL and compatibility claims
against the target project's pins and the official sources below.

## Find effective configuration

Read the wrapper properties, settings, module build files, version catalogs,
`pluginManagement`, included `build-logic`/`buildSrc`, convention plugins, and CI.
Versions and compiler options may be supplied by those layers rather than the
file being edited. Groovy and Kotlin DSL builds need the same investigation.

Resolve configured source roots, flavor/build-type combinations, generated
inputs, and project-local architecture checks too. Kotlin may live in `src/`,
`lawnchair/src/`, or an Android `java/` directory, not just `src/main/kotlin`.
Do not move it to a conventional layout during an unrelated change. A module's
short build file may inherit most of its contract from convention plugins.

Distinguish these settings before changing any:

| Setting | Contract |
| --- | --- |
| Wrapper distribution | Gradle executing the build |
| Gradle runtime JDK | JVM able to run that Gradle/AGP release |
| Java/Kotlin toolchains | JDKs selected for compilation and applicable tasks |
| Kotlin `jvmTarget`, Java target/release | Bytecode compatibility; a toolchain alone is not a deployment guarantee |
| `languageVersion`, `apiVersion` | Accepted syntax/semantics and usable Kotlin API level |
| Compiler plugin versions | Compatibility with compiler internals or supported integration |
| kotlinx libraries | Independently versioned dependencies, not the compiler version |

Check Java and Kotlin targets together. A newer JDK can accidentally expose APIs
unavailable on the deployment JVM; inspect Java `--release`, Kotlin's configured
JDK API restriction where supported, and a runtime test on the supported JDK.
Android desugaring and minSdk impose a different runtime API boundary.

`compilerOptions` is the modern typed DSL. Do not paste it into an older KGP that
does not support the chosen form. Find task/target overrides as well as extension
defaults; setting a root option does not prove the effective compilation changed.

## Execute only the selected lane

Use the wrapper or documented driver. Maven builds should use their own wrapper,
plugin configuration, lifecycle, and module selection; do not convert them to
Gradle. For standalone `.kts` files inspect script dependency annotations and the
script host before executing them. A `.gradle.kts` file uses Gradle's embedded
Kotlin as well as the build's plugin ecosystem.

Gradle writes caches and executes build logic during configuration. Wrapper
bootstrap, toolchain resolvers, Native toolchains, Android SDKs, Node/Yarn,
plugins, and custom tasks can each download tools independently. When network
access is restricted, verify prerequisites without invoking the wrapper first;
disable auto-provisioning only through supported invocation options where
appropriate, and report missing artifacts. Do not change persistent machine
configuration merely to run a check.

Use explicit module task paths. Inspect task dependencies if a check might also
publish, install, deploy, sign, or upload a build scan. Cache deletion, `clean`,
`--refresh-dependencies`, dependency-verification rewrites, and formatter fix
tasks are not routine diagnostics.

Do not build a universal gate by guessing task names. JVM test filtering with
`--tests` applies to compatible test tasks; Native/JS tests and Android device
tests may use different filtering and execution mechanisms.

## Change the compatibility tuple deliberately

For an upgrade, record the current and intended Kotlin/KGP, Gradle, AGP, JDK,
Compose compiler, KSP/kapt, serialization compiler plugin, and Native/Xcode
combinations as relevant. Consult compatibility tables for the chosen versions;
do not freeze a global latest-version matrix inside the skill.

Separate a required compatibility repair from an optional module restructure.
Preserve catalogs, locks, dependency verification, repositories, source-set
topology, and warning policy unless the task changes them. Prefer one coherent
migration slice with compile, behavior, and consumer checks over suppressing
every new warning or updating every plugin at once.

For Kotlin 2.x Compose compiler integration, inspect the project's actual plugin
setup rather than copying a legacy Compose compiler extension version. For
AGP's built-in Kotlin and KMP Android plugin changes, read
[multiplatform and Android](multiplatform-android.md).

## Sources

- [Kotlin Gradle configuration and compatibility](https://kotlinlang.org/docs/gradle-configure-project.html)
- [KGP compiler options and override levels](https://kotlinlang.org/docs/gradle-compiler-options.html)
- [Gradle wrapper](https://docs.gradle.org/current/userguide/gradle_wrapper.html)
- [Gradle Java toolchains](https://docs.gradle.org/current/userguide/toolchains.html)
