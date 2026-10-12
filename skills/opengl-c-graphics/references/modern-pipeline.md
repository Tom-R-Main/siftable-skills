# Modern OpenGL Pipeline (C)

Source: **LearnOpenGL** (Joey de Vries) — modern 3.3 core profile. The book's
samples are C++, but every call below is the plain C API. Where the book uses a
C++-only helper (GLM math, `Shader`/`Camera` classes, `std::vector`), the C
equivalent is noted. Checklist, not law.

## The minimal program, in call order

1. **Init + window + context** (GLFW)
   ```c
   glfwInit();
   glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
   glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
   glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
   #ifdef __APPLE__
   glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GLFW_TRUE);  /* mandatory on macOS */
   #endif
   GLFWwindow *win = glfwCreateWindow(800, 600, "app", NULL, NULL);
   glfwMakeContextCurrent(win);
   ```
2. **Load function pointers** — *after* a context is current. GL entry points are
   resolved at runtime; calling any `gl*` before the loader runs is a crash.
   ```c
   gladLoadGLLoader((GLADloadproc)glfwGetProcAddress);   /* GLAD */
   /* or GLEW: glewExperimental = GL_TRUE; glewInit(); */
   ```
3. **Viewport** + resize callback: `glViewport(0,0,w,h)`; register
   `glfwSetFramebufferSizeCallback` to re-call it on resize.
4. **Upload geometry** (VAO + VBO, below).
5. **Compile + link shaders** (below).
6. **Render loop** until `glfwWindowShouldClose(win)`:
   ```c
   glClearColor(0.1f,0.1f,0.12f,1.0f);
   glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);   /* depth bit if testing */
   glUseProgram(prog);
   glBindVertexArray(vao);
   glDrawArrays(GL_TRIANGLES, 0, 3);          /* or glDrawElements */
   glfwSwapBuffers(win);
   glfwPollEvents();
   ```
7. **Teardown**: `glDelete*` every object, then `glfwDestroyWindow` + `glfwTerminate`.

See `../examples/triangle.c` for the full C-correct program.

## Buffers and vertex array objects

- VBO holds raw bytes; VAO records *attribute layout* + the `GL_ELEMENT_ARRAY_BUFFER`
  binding. The VBO is captured **per attribute** at `glVertexAttribPointer` time
  (whatever is bound to `GL_ARRAY_BUFFER` then), not as VAO state.
  ```c
  glGenVertexArrays(1, &vao); glGenBuffers(1, &vbo);
  glBindVertexArray(vao);
  glBindBuffer(GL_ARRAY_BUFFER, vbo);
  glBufferData(GL_ARRAY_BUFFER, sizeof verts, verts, GL_STATIC_DRAW);
  glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3*sizeof(GLfloat), (void*)0);
  glEnableVertexAttribArray(0);
  ```
- `glVertexAttribPointer(index, size, type, normalized, stride, offset)`. The
  **offset is a byte count cast to `(void*)`** — an API wart, not a real pointer.
  Interleaved attrs: same VBO, different `offset`, shared `stride`.
- Usage hints: `GL_STATIC_DRAW` (set once, draw many), `GL_DYNAMIC_DRAW`
  (re-specified often), `GL_STREAM_DRAW` (set once, used a few times). Hints only.
- Indexed drawing: bind an `GL_ELEMENT_ARRAY_BUFFER` (EBO) *while the VAO is bound*
  — the binding is saved in the VAO. Draw with
  `glDrawElements(GL_TRIANGLES, count, GL_UNSIGNED_INT, 0)`. Do **not** unbind the
  EBO before unbinding the VAO.

## Shaders (compile → link)

Status checks are not optional — see `../examples/triangle.c` for the version that
sizes the info log from `GL_INFO_LOG_LENGTH` instead of a fixed 512-byte buffer.
```c
GLuint vs = glCreateShader(GL_VERTEX_SHADER);
glShaderSource(vs, 1, &src, NULL);           /* src is const char* */
glCompileShader(vs);
GLint ok; glGetShaderiv(vs, GL_COMPILE_STATUS, &ok);   /* glGetShaderInfoLog on fail */

GLuint prog = glCreateProgram();
glAttachShader(prog, vs); glAttachShader(prog, fs);
glLinkProgram(prog);
glGetProgramiv(prog, GL_LINK_STATUS, &ok);             /* glGetProgramInfoLog on fail */
glDeleteShader(vs); glDeleteShader(fs);                /* delete after a successful link */
```

## Uniforms

- `glGetUniformLocation(prog, "name")` returns `-1` if the name is absent **or
  optimized out**. Cache locations; do not query every frame.
- You must `glUseProgram(prog)` before any `glUniform*` (uniforms are per-program
  state). Setters: `glUniform1f/2f/3f/4f`, `glUniform1i` (also how you bind a
  sampler to a texture unit), `glUniformMatrix4fv(loc, 1, GL_FALSE, &m[0][0])`.
- **Matrices are column-major.** Pass `transpose = GL_FALSE` for GLM/cglm data.

## Textures

```c
glGenTextures(1, &tex);
glBindTexture(GL_TEXTURE_2D, tex);
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);   /* or CLAMP_TO_EDGE, MIRRORED_REPEAT */
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, data);
glGenerateMipmap(GL_TEXTURE_2D);
```
- Pixel loading: the book uses `stb_image.h` (`stbi_load`, `stbi_image_free`). Call
  `stbi_set_flip_vertically_on_load(true)` — image origin is top-left, GL's is
  bottom-left. Match internal format to channel count (`GL_RGBA`/`GL_UNSIGNED_BYTE`
  for 4-channel PNG).
- Multiple textures: `glActiveTexture(GL_TEXTURE0 + n)`, bind, then set the sampler
  uniform with `glUniform1i(loc, n)` (the *unit index*, not the texture name).

## Transform / coordinate pipeline

local → **model** → world → **view** → **projection** → clip → (÷w) NDC → **viewport** → screen.
- C++ uses GLM. In C use **cglm** (`cglm/cglm.h`: `glm_perspective`, `glm_lookat`,
  `glm_mat4_mul`, `glm_rotate`, `glm_translate`) or hand-rolled 4×4s. cglm writes
  column-major `mat4`, directly feedable to `glUniformMatrix4fv` with
  `transpose = GL_FALSE`.
- Enable depth for 3D: `glEnable(GL_DEPTH_TEST)` and clear `GL_DEPTH_BUFFER_BIT`.
- View matrix from a camera = `lookAt(pos, pos + front, up)`.

## Advanced GL — topic → the GL calls it introduces

| Topic | Key calls / enums |
|---|---|
| Depth testing | `glEnable(GL_DEPTH_TEST)`, `glDepthFunc(GL_LESS)`, `glDepthMask` |
| Stencil testing | `glEnable(GL_STENCIL_TEST)`, `glStencilFunc`, `glStencilOp`, `glStencilMask` |
| Blending | `glEnable(GL_BLEND)`, `glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)`, `glBlendEquation` |
| Face culling | `glEnable(GL_CULL_FACE)`, `glCullFace(GL_BACK)`, `glFrontFace(GL_CCW)` |
| Framebuffers | `glGenFramebuffers`, `glBindFramebuffer(GL_FRAMEBUFFER, fbo)`, `glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tex, 0)`, `glCheckFramebufferStatus(...) == GL_FRAMEBUFFER_COMPLETE` |
| Renderbuffers | `glGenRenderbuffers`, `glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, w, h)`, `glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)` |
| Cubemaps | `GL_TEXTURE_CUBE_MAP`, 6 faces `GL_TEXTURE_CUBE_MAP_POSITIVE_X + i`, `samplerCube` |
| UBOs | `layout(std140, binding=0)` block; `glBindBufferBase`/`glBindBufferRange(GL_UNIFORM_BUFFER, ...)`; share matrices across programs |
| Geometry shaders | `GL_GEOMETRY_SHADER`, `EmitVertex()`/`EndPrimitive()`, `layout(triangles)`/`layout(triangle_strip, max_vertices=N)` |
| Instancing | `glDrawArraysInstanced(mode, first, count, n)`, `gl_InstanceID`; instanced arrays via `glVertexAttribDivisor(idx, 1)` |
| MSAA | `glfwWindowHint(GLFW_SAMPLES, 4)`, `glEnable(GL_MULTISAMPLE)`; offscreen via `glRenderbufferStorageMultisample` / `glTexImage2DMultisample` + `glBlitFramebuffer` |

## Advanced lighting / PBR — one-liners (LearnOpenGL Parts V–VI)

Blinn-Phong (halfway vector) · gamma correction (render linear, present sRGB:
`GL_SRGB8_ALPHA8` or pow 1/2.2) · shadow mapping (render depth to FBO from the
light, compare) · point shadows (depth cubemap) · normal mapping (sample normals in
tangent space via a TBN matrix) · parallax mapping · HDR (render to a float
`GL_RGBA16F` target, then tone-map) · bloom (bright-pass + two-pass Gaussian blur) ·
deferred shading (G-buffer with MRT: `glDrawBuffers` writes position/normal/albedo) ·
SSAO · PBR (Cook-Torrance: distribution/geometry/Fresnel) + IBL (irradiance +
prefiltered env map + BRDF LUT). Each is "render to texture, then sample it."
