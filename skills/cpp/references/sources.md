# Sources and evidence boundaries

Authored 2026-11-01. Original guidance was grounded in the C systems, Zig, Rust,
Go and Swift skill workflows, then checked against selected C++ sources. Existing
language skills supplied ownership and verification questions, not authority to
copy version claims or mechanically translate examples.

## Local reference study

A filename inventory found 35,571 `.cpp`, `.cc`, `.cxx` and `.hpp` files across
55 checkouts, with dependency/build/data exclusions and normal ignore rules.
This includes examples and fixtures and is not a semantic audit of every file.
An explicit Bitcoin scan with VCS ignores disabled found another 1,444 `.cpp`/`.h`
files in its selected scope; its absence from the initial inventory was not
treated as absence of C++.

Eleven repositories were cataloged. Depth varies: ownership/concurrency traces
are deeper than manifest comparisons; cataloging alone is not code review.

| Source and captured HEAD | Decisive paths and scope |
| --- | --- |
| [OBS Studio](https://github.com/obsproject/obs-studio/tree/65c320b46e1af5c7a555161aea6182cdf7a8c524) | `libobs/obs.hpp:67–189`, `libobs/obs-source.c:933–951`, `frontend/utility/ThumbnailItem.cpp:58–76,160–183`: adopt/acquire, weak promotion and actual consumer |
| [DuckDB](https://github.com/duckdb/duckdb/tree/910c73dabeafc0290907a0c37e09f6abed8e9446) | `src/main/appender.cpp:39–60,395–424,744–758`; `test/appender/test_appender.cpp:275–287,804–896`; buffer handle and manager pin/unpin: failure state, explicit close, borrowed pin and destructor lock effects |
| [Binaryen](https://github.com/WebAssembly/binaryen/tree/677ad318579711a259e28c03e4c7cbdfd150b02b) | `src/ir/module-utils.h:260–328`, `src/passes/pass.cpp:976–1012`, `src/support/threads.cpp:198–252`, `src/passes/GlobalRefining.cpp:40–69`, `test/example/cpp-threads.cpp:1–60`: fixed slots, callback completion and aggregation |
| [qBittorrent](https://github.com/qbittorrent/qBittorrent/tree/62259b84b333ed5d8db106199db72dbe90ea90c1) | `src/base/http/asyncfilesender.cpp:62–125,248–376`: bounded capacity, stop/wakeup and deferred lifecycle |
| [Godot](https://github.com/godotengine/godot/tree/95c0fa5fe8a019adc29d074c16b64469b04571f7) | `SConstruct:920–954`: standard mode and no-exception/RTTI configuration |
| [TensorFlow](https://github.com/tensorflow/tensorflow/tree/55b14ff64d36f31b788b7566bc5ecaed985da4fe) | `.bazelrc:477–508`, `tensorflow/core/framework/tensor.h:328–394,638–665`, tensor implementation and `tensor_test.cc:1467–1480`: host/target flags and buffer distinctions; `op_kernel.h:237–249`, `op_requires.h:90–107`, `op_requires_test.cc:84–115`, and executor completion teardown: required completion and immediate destruction |
| [Bitcoin Core](https://github.com/bitcoin/bitcoin/tree/6c01bd0b2dc201c21e80ac3635828abf854ee5a0) | `CMakeLists.txt:76–136`, `doc/developer-notes.md:360–391`, `src/test/fuzz/checkqueue.cpp`, `src/util/check.h`, `src/util/overflow.h`: build/assertion/fuzz/arithmetic contracts; `src/serialize.h:302–362`, `src/test/serialize_tests.cpp:208–252`: canonical CompactSize, independent range checking and rejection tests |
| [WABT](https://github.com/WebAssembly/wabt/tree/ed1a832d9553158a2a67bf6c6d98a96207a4ee6b) | `CMakeLists.txt:18–76,155–183,651–686`, `src/utf8.cc:49–106`, `src/test-utf8.cc:25–86`: dialect/exception/test contract and byte-validation component |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp/tree/482279b8a18855ba741d7b88c30fcb3874691f59) | `CMakeLists.txt:40–62`: platform-conditional standard flags; contributor/agent guidance |

OpenCV and MuJoCo were cataloged and selected build definitions inspected for
contrasts; no distinct mechanism is attributed to catalog metadata alone.

Private authoring evidence is not distributed with this portable package. The
authoring library retains repo-learn evidence/cards and captures HEAD,
full-file/slice hashes and exact lines. Exact reads of `SConstruct` and `.bazelrc` are recorded separately
because the helper's text-file policy excludes those names. That limitation was
preserved rather than changing the helper or claiming those receipts are helper
evidence. Source content can drift after capture; recheck relevant callers and
configuration before consequential reuse.

Source traces and upstream test definitions are distinguished from executed
checks in the authoring report. Isolated component and mechanism exercises do
not qualify full applications, all compiler/OS combinations, Qt/GPU behavior,
ABI compatibility or performance. No upstream implementation was changed.

Installed-skill follow-up exercised unchanged Godot Span and Bitcoin CompactSize
components in isolated consumers. A snapshot-only permissive Bitcoin decoder
passed valid-input round trips while failing noncanonical rejection checks in
optimized and ASan/UBSan builds. TensorFlow completion was tested with an original
lifecycle model, with missing/duplicate completion and post-completion cleanup
controls; it was not framework execution. A second qBittorrent queued-storage
trace remained source-only because Qt was unavailable. These checks support the
narrow completion/codec guidance, not full engine, Qt, TensorFlow or node claims.

## Authoritative checks

Consult the selected versions when applying this skill; these links can track
newer content than a target's baseline.

- [C++ working draft](https://eel.is/c++draft/): language/library contracts;
  [container data races](https://eel.is/c++draft/container.requirements.dataraces),
  [jthread construction/destruction](https://eel.is/c++draft/thread.jthread.cons),
  [join synchronization](https://eel.is/c++draft/thread.jthread.mem),
  [exception specifications](https://eel.is/c++draft/except.spec).
  A living draft is not proof that a facility shipped in an older standard.
- [CMake standard property](https://cmake.org/cmake/help/latest/prop_tgt/CXX_STANDARD.html),
  [required standard](https://cmake.org/cmake/help/latest/prop_tgt/CXX_STANDARD_REQUIRED.html),
  [compile features](https://cmake.org/cmake/help/latest/manual/cmake-compile-features.7.html),
  [FetchContent](https://cmake.org/cmake/help/latest/module/FetchContent.html),
  [CTest](https://cmake.org/cmake/help/latest/manual/ctest.1.html).
- [Clang ASan](https://clang.llvm.org/docs/AddressSanitizer.html),
  [UBSan](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html),
  [TSan](https://clang.llvm.org/docs/ThreadSanitizer.html): supported diagnostics,
  instrumentation, linking and limits.
- [clangd compile commands](https://clangd.llvm.org/design/compile-commands),
  [libstdc++ dual ABI](https://gcc.gnu.org/onlinedocs/libstdc++/manual/using_dual_abi.html),
  [MSVC iterator modes](https://learn.microsoft.com/en-us/cpp/standard-library/iterator-debug-level):
  effective parser flags and library configuration are independent concerns.
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines):
  design cross-check, conditional on repository/platform policy. They do not
  mandate adopting exceptions, a framework, or a new dependency.

## Awesome C++ as discovery, not dependency policy

Reviewed the [awesome-cpp list](https://github.com/fffaraz/awesome-cpp/blob/e9b1ad8bc0ff454f42e6849961402c544779c6a4/README.md)
at `e9b1ad8bc0ff454f42e6849961402c544779c6a4`, particularly concurrency,
testing/debugging, allocation, build systems, static analysis and coding guidance.
It usefully surfaces alternative frameworks, runners and tools; it also contains
historical links and libraries for different standards, licenses and platforms.

Use it to locate candidates, then inspect a candidate's maintained source,
supported toolchain, license, target fit and integration cost. Its inclusion is
not evidence of current maintenance, correctness, performance, or a reason to
replace existing dependencies. No listed package was installed or benchmarked
as part of the comparison, and the catalog text was not copied into the skill.
