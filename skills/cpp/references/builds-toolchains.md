# Builds, toolchains and language support

Identify the driver: CMake/presets, Bazel, SCons, Meson, Make, a bootstrap script,
or a package-manager toolchain. Read its target and CI configuration before
running it. Godot's SCons build, TensorFlow's Bazel targets, and a small CMake
library require different verification routes.

## Read the effective target

- A root-level standard assignment may be conditional or overridden later.
  Inspect target properties, transitive compile features and the actual compile
  command. `CMAKE_CXX_STANDARD` initializes targets when created; editing it
  after target creation does not retroactively update those targets.
- `CXX_STANDARD` may permit fallback when `CXX_STANDARD_REQUIRED` is unset.
  `cxx_std_20` requests a language level, not every C++20 library facility.
  `CXX_EXTENSIONS` controls extension mode separately. Preserve the project's
  policy rather than mechanically setting all three.
- Compiler front-end support, library headers, linked library/runtime, SDK and
  deployment target are separate constraints. Check feature-test macros and a
  focused compile/link/run under the real configuration for needed facilities
  such as ranges, format, stop tokens or expected. Do not infer availability
  from a compiler version or `__cplusplus` alone; MSVC also has mode-reporting
  options to consider.
- Flags can differ for C, C++, Objective-C++, CUDA, host code generators and
  cross-compiled targets. A working host utility does not prove target support.
- Record exception/RTTI flags, alignment/SIMD assumptions, sanitizer settings,
  optimization/LTO, visibility, CRT linkage and debug-library modes. These may
  affect correctness or compatibility as well as diagnostics.

Compilation databases support clangd/clang-tidy when produced by the real build.
They can be stale or omit generated/platform units. Inspect the entry's compiler,
working directory, includes, defines, language mode and output. Header diagnostics
depend on the consuming translation unit; standalone `clang++ file.cpp` often
tests a different configuration.

## Configuration is execution

CMake `FetchContent` can populate sources during configuration; other build
systems and dependency providers also execute scripts or resolve dependencies.
Reading presets is discovery; running configure is a separate action. Inspect
presets' inheritance, include files, toolchain and environment references without
printing secrets. Preserve lockfiles and dependency caches. Offline options do
not manufacture a missing source tree or installed toolchain.

Use separate build directories for incompatible compiler/ABI/sanitizer options;
do not reuse an unrelated cache or delete a user's build to fix a configuration.
Honor generated-source update procedures. Do not edit generated files when the
maintained input owns the behavior.

## Conditional CMake route

Only for a project whose inspected driver uses these commands, with authorized
configuration and an approved output directory:

```sh
cmake --preset <configure-preset>
cmake --build --preset <build-preset> --target <focused-target>
ctest --preset <test-preset> -R '<anchored-test-expression>' --output-on-failure
```

Or use its existing build tree with `cmake --build <build-dir> --config <config>`
and `ctest --test-dir <build-dir> -C <config>`. Single-configuration generators
select `CMAKE_BUILD_TYPE` at configure time; multi-configuration generators select
the configuration at build/test time. The test executable and its configuration
must match. Inspect CTest registration and test-runner filters before execution;
use `--no-tests=error` when supported and still inspect selected/executed counts.

For Bazel, identify the exact label, `.bazelrc` configs, toolchain/platform and
test arguments. For SCons, inspect target, platform, features and test flags.
Do not substitute generic CMake or a standalone compilation for the owner's
required integration lane. A deliberately isolated source-component exercise
can add evidence when the full driver is unavailable; label its reduced scope.
