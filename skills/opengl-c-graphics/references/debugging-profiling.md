# Debugging & Profiling (C)

Source: **OpenGL Insights** — Ch.33 (ARB_debug_output), Ch.34 (the OpenGL timer
query), Ch.35/37/38 (real-time profiling, perf-state & memory tracking). Checklist,
not law.

## glGetError — the fallback, not the tool

`glGetError()` returns **one** error flag per call and must be drained in a loop;
it tells you *that* something failed since the last check, not *where*. Coarse and
slow if sprinkled everywhere. Use debug output instead when available; keep
`glGetError` for older contexts.
```c
for (GLenum e; (e = glGetError()) != GL_NO_ERROR; )
    fprintf(stderr, "GL error 0x%x\n", e);
```

## Debug output — the right tool (KHR_debug core in 4.3; ARB_debug_output)

1. **Create a debug context.** From GLFW: `glfwWindowHint(GLFW_OPENGL_DEBUG_CONTEXT,
   GLFW_TRUE)` before window creation. (Raw WGL/GLX use
   `WGL_CONTEXT_DEBUG_BIT_ARB` / `GLX_CONTEXT_DEBUG_BIT_ARB`.) The spec recommends
   the extension be active only in a debug context — it can cost performance.
2. **Register a callback** — the driver calls it with every event:
   ```c
   void APIENTRY gl_debug_cb(GLenum source, GLenum type, GLuint id,
                             GLenum severity, GLsizei length,
                             const GLchar *message, const void *userParam);
   ...
   glEnable(GL_DEBUG_OUTPUT);
   glEnable(GL_DEBUG_OUTPUT_SYNCHRONOUS);    /* see below */
   glDebugMessageCallback(gl_debug_cb, my_user_ptr);
   ```
   (`...ARB` suffixes for the extension form: `glDebugMessageCallbackARB`.)
3. **`GL_DEBUG_OUTPUT_SYNCHRONOUS`**: the callback fires while the offending GL call
   is **still on the call stack**. Put a breakpoint in the callback and the
   debugger's stack points straight at the bad call. Without it the driver reports
   "at its convenience" (asynchronously) and the stack is useless.
4. **CRITICAL — async-signal-style rule:** calling **any** GL or window-system
   function *inside* the callback is **undefined behaviour and may crash** (Insights
   Ch.33). Do logging / breakpoints / set a flag only — no GL calls.
5. **Filter the firehose** with `glDebugMessageControl(source, type, severity,
   count, ids, enabled)` — e.g. mute `GL_DEBUG_SEVERITY_NOTIFICATION`. Inject your
   own markers with `glDebugMessageInsert(GL_DEBUG_SOURCE_APPLICATION,
   GL_DEBUG_TYPE_MARKER, id, GL_DEBUG_SEVERITY_NOTIFICATION, len, msg)`.
6. If no callback is set, events queue in an internal **message log** — drain it
   with `glGetDebugMessageLog(...)` (it's a fixed-size queue; full = dropped).

Enum families: `GL_DEBUG_SOURCE_*` (API, SHADER_COMPILER, THIRD_PARTY,
APPLICATION, WINDOW_SYSTEM, OTHER); `GL_DEBUG_TYPE_*` (ERROR, DEPRECATED_BEHAVIOR,
UNDEFINED_BEHAVIOR, PORTABILITY, **PERFORMANCE**, MARKER, OTHER);
`GL_DEBUG_SEVERITY_*` (HIGH, MEDIUM, LOW, NOTIFICATION).

## Timer queries — measure GPU time, not CPU time (Ch.34)

`glfwGetTime`/`clock_gettime` measure the CPU; the GPU runs **frames behind**, so
CPU timers around GL calls are meaningless. Use query objects:

```c
GLuint q[2];
glGenQueries(2, q);
glQueryCounter(q[0], GL_TIMESTAMP);   /* record "now" on the GPU timeline */
draw_scene();
glQueryCounter(q[1], GL_TIMESTAMP);
...
GLuint64 t0, t1;
glGetQueryObjectui64v(q[0], GL_QUERY_RESULT, &t0);   /* nanoseconds */
glGetQueryObjectui64v(q[1], GL_QUERY_RESULT, &t1);
double ms = (double)(t1 - t0) / 1.0e6;
```

- Two mechanisms: **`glBeginQuery(GL_TIME_ELAPSED)` / `glEndQuery`** (a span — but
  **cannot nest**), or **`glQueryCounter(id, GL_TIMESTAMP)`** (a point — place
  anywhere, even between someone else's begin/end; preferred for libraries).
- Results are **nanoseconds in `GLuint64`** — a 32-bit counter overflows in
  seconds, so never use `GLuint`.
- **Avoid the stall when reading.** `glGetQueryObject*` with `GL_QUERY_RESULT`
  blocks until the result exists. Poll `GL_QUERY_RESULT_AVAILABLE` (non-blocking)
  first, or read **N frames late** — the GPU can be ~5 frames behind.
  **Double/triple-buffer your query objects** and never reissue a query before
  retrieving its previous result (you'd overwrite it).
- Buffer-swap is **not** a sync point — don't assume results are ready after
  `glfwSwapBuffers`.

## Memory & state tracking (Ch.37/38)

GPU memory and driver state aren't in core GL; query via vendor extensions —
`NVX_gpu_memory_info` (`GL_GPU_MEMORY_INFO_*`) on NVIDIA, `ATI_meminfo` on AMD.
Track per-frame to catch leaks/thrashing. Treat as advisory and vendor-specific.

## C-side notes

- The callback **must** be declared with `APIENTRY` (the `GLDEBUGPROC` calling
  convention) or you get a function-pointer-type mismatch / crash on Windows.
- `glDebugMessageCallback` may be `NULL` if the context lacks the feature — gate on
  `GL_CONTEXT_FLAG_DEBUG_BIT` (via `glGetIntegerv(GL_CONTEXT_FLAGS, ...)`) and a
  non-NULL pointer before calling it (see `../examples/triangle.c`).
- Every `glGenQueries` needs a matching `glDeleteQueries`.
