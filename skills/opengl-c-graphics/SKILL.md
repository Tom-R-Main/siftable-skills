---
name: opengl-c-graphics
description: Build, debug, review, and optimize core-profile OpenGL in C. Use for contexts, shaders, buffers, textures, GL object lifetimes, and measured GPU performance.
---

# OpenGL in C

Domain skill for writing **modern, core-profile OpenGL in plain C** — not C++.
OpenGL is a C API, but most tutorials (including LearnOpenGL) are written in C++
with GLM math and RAII wrapper classes. Your job is to render the same pipeline in
idiomatic C: explicit object lifetimes, GL types, checked errors, no hidden
destructors. Treat "it linked and drew something" as insufficient — a GL program
can render a perfect triangle while leaking objects, ignoring errors, and stalling
the GPU every frame.

This skill is grounded in three sources, broken out under `references/`:
- **LearnOpenGL** → `references/modern-pipeline.md` (setup → draw → advanced GL)
- **Orange Book** (GL Shading Language) → `references/glsl-language.md` (GLSL)
- **OpenGL Insights** → `references/performance-async.md` + `references/debugging-profiling.md`

A complete, C-correct, warning-clean reference program is in
`examples/triangle.c`. A verification helper is `scripts/glcheck.sh`.

## First moves (detect the environment before editing)

1. **GL version + profile.** Grep for context hints (`GLFW_CONTEXT_VERSION_*`,
   `GLFW_OPENGL_CORE_PROFILE`, `glewInit`, raw WGL/GLX attribs). The `#version` in
   the shaders must match. On macOS, core profile **requires**
   `GLFW_OPENGL_FORWARD_COMPAT` and caps out at GL 4.1 (no 4.3+ debug output,
   compute, SSBO).
2. **Loader.** GLAD vs GLEW vs glad2 vs manual `glXGetProcAddress`. Function
   pointers are invalid until the loader runs *after* a context is current — a
   `gl*` call before that is a null-pointer crash, not a link error.
3. **Math + window libs.** GLFW/SDL2 for windowing; **cglm** is the C answer to
   C++'s GLM (column-major `mat4`, feeds `glUniformMatrix4fv` directly). Don't pull
   in C++ GLM from C.
4. **Build system.** Makefile / CMake / direct `cc`. Note `-std=`, warning flags,
   and how GL/GLFW are linked (`pkg-config --libs glfw3`, `-framework OpenGL` on
   macOS, `-lGL -ldl` on Linux).
5. **Reproduce first** for visual bugs: a black screen, wrong colors, or z-fighting
   each have distinct causes (see Troubleshooting).

## The C mindset for OpenGL

- **GL handles are unowned `GLuint`s.** `glGen*`/`glCreate*` give you a name; you
  own its lifetime and must `glDelete*` it on every exit path. There are no
  destructors. Name `0` is "none" and is never valid output — use it as your
  null/failure sentinel.
- **Use GL types, never bare `int`.** `GLuint` handles, `GLint` locations/sizes
  from `glGet*`, `GLsizei` counts, `GLsizeiptr`/`GLintptr` for buffer sizes/offsets
  (a 32-bit `int` overflows on large buffers), `GLchar` for shader text, `GLuint64`
  for timer results, `GLfloat` for vertex data.
- **Errors are sticky and silent.** A bad call sets an error flag and the call is
  ignored — rendering simply looks wrong. Compile/link **must** be status-checked;
  install debug output (below). `glGetUniformLocation` returning `-1` and
  `glUniform*(-1, ...)` being a silent no-op is the classic "my uniform does
  nothing" bug.
- **Bind-to-edit is global mutable state.** Most calls act on whatever is currently
  bound. Leaving objects bound across unrelated code is the source of
  hard-to-trace corruption — bind, edit, unbind, or use DSA (`glNamed*`) on 4.5+.
- **`std140` layout must be mirrored byte-for-byte in your C struct** (vec3→16B
  align, array stride padded to vec4). A mismatch is silently wrong, never an
  error. See `references/glsl-language.md`.

## Validation gates (run in order; fix failures before moving on)

This is the C verification ladder adapted to GL. `scripts/glcheck.sh file.c ...`
runs compile gates 1–2 for you; it does not execute the program. Set
`GLCHECK_OUTPUT_DIR` to an explicit output directory to retain binaries for runtime
checks, otherwise temporary build artifacts are removed.

1. **Strict warnings = correctness failures.**
   `cc -std=c11 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Wstrict-prototypes`
   `-Wmissing-prototypes`. `-Wconversion` catches the `GLint`/`GLsizei`/`size_t`
   mismatches that pepper GL code.
2. **Sanitized build.** `-fsanitize=address,undefined -fno-omit-frame-pointer`,
   then run under a real display (GL needs a context; for CI use headless EGL or
   Xvfb). Catches the use-after-`stbi_image_free`, the off-by-one in an interleaved
   vertex buffer, the unchecked `glMapBufferRange` returning `NULL`.
3. **GL debug output at runtime** (`references/debugging-profiling.md`). A debug
   context + `glDebugMessageCallback` with `GL_DEBUG_OUTPUT_SYNCHRONOUS` turns
   silent GL errors into a breakpoint at the offending call. This is the single
   highest-leverage debugging step — prefer it over scattering `glGetError`.
4. **No leaked GL objects.** Every `glGen*`/`glCreate*`/`glFenceSync` has a matching
   `glDelete*`. Audit it like `malloc`/`free`.
5. **Measure, don't guess, performance.** GPU time via timer queries
   (`glQueryCounter` + `GLuint64`), not CPU wall-clock — the GPU runs frames behind.

## References (open as needed — checklists, not laws)

- `references/modern-pipeline.md` — the canonical setup→VAO/VBO→shader→texture→
  transform→draw call sequence, plus the advanced-GL topic→API map (framebuffers,
  UBOs, instancing, MSAA, deferred, PBR). **Start here for "how do I draw X".**
- `references/glsl-language.md` — GLSL stages, types, qualifiers, built-in
  variables/functions (with real signatures), `std140`, and the C↔GLSL boundary
  gotchas. **Open when writing/binding shaders.**
- `references/performance-async.md` — reducing driver calls, buffer orphaning,
  round-robin multi-buffering, `glMapBufferRange` + fence streaming, PBO texture
  upload. **Open when the frame is CPU-bound or transfers stall.**
- `references/debugging-profiling.md` — debug-output callback, `glGetError`, timer
  queries, GPU memory tracking. **Open when something is wrong or slow.**

## Common pitfalls

- **`gl*` before the loader / before a current context** → segfault. Order:
  context → make current → load → use.
- **Forgetting the EBO is VAO state**: unbinding `GL_ELEMENT_ARRAY_BUFFER` while the
  VAO is still bound erases it from the VAO.
- **Fixed 512-byte info-log buffer** truncates real errors — size from
  `GL_INFO_LOG_LENGTH` and heap-allocate (see `examples/triangle.c`).
- **`glVertexAttribPointer` offset** is a byte count cast to `(void*)`, not a
  pointer. Integer attributes need `glVertexAttribIPointer`, or they get silently
  float-converted.
- **Matrix transpose/order**: GL is column-major; pass `transpose = GL_FALSE` for
  GLM/cglm data. Model·View·Projection multiply order matters.
- **Texture image flip**: image origin is top-left, GL's is bottom-left —
  `stbi_set_flip_vertically_on_load`.
- **Calling GL inside a debug callback** → undefined behaviour (Insights Ch.33).
- **`glBufferSubData`/`glMapBuffer` on an in-flight buffer** → implicit GPU stall;
  orphan or use `GL_MAP_UNSYNCHRONIZED_BIT` + fences instead.
- **macOS** silently lacks GL 4.3+ — no core debug output, compute shaders, or
  SSBOs. Feature-gate on the actual context version, don't assume.

## Troubleshooting (visual symptoms → likely cause)

- **Black screen / nothing draws**: shader failed to compile/link (you skipped the
  status check); VAO not bound at draw; depth test on but depth buffer not cleared;
  geometry behind the near plane or culled (`glFrontFace` winding); uniform location
  `-1`.
- **Triangle but wrong color/uniform ignored**: didn't `glUseProgram` before
  `glUniform*`; uniform optimized out (`-1`); `std140` struct padding mismatch.
- **Z-fighting / depth garbage**: no `glEnable(GL_DEPTH_TEST)`; near plane too small
  / far too large; depth buffer not requested or not cleared.
- **Texture is black/garbage**: forgot `glGenerateMipmap` with a mipmap min-filter;
  internal format ≠ data format; sampler uniform set to the texture *name* instead
  of the *unit index*; image not flipped.
- **Frame hitches every N frames**: per-frame buffer/texture (re)creation or an
  implicit sync from `glBufferSubData`/`glGet*` — see `references/performance-async.md`.
