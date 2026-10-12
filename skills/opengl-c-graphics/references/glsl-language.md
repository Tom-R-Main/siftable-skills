# GLSL Language Reference (for C callers)

Source: **OpenGL Shading Language**, 3rd ed. ("the Orange Book", Rost / Ginsburg /
Licea-Kane et al.). This is the language the C program feeds as text to
`glShaderSource`. Focus here is what a C programmer must get right at the GLSL/GL
boundary. Checklist, not law.

## Programmable stages & execution model

Pipeline order: **vertex** → tessellation control (TCS) → *(fixed tessellator)* →
tessellation evaluation (TES) → **geometry** → *(rasterizer)* → **fragment**;
plus the standalone **compute** stage. Fixed-function steps sit between programmable
stages (the book stresses you replace fixed functionality stage-by-stage). The
vertex processor runs once per vertex; the fragment processor once per fragment,
possibly in parallel across many cores — never assume execution order or shared
state between invocations.

## Version & profile

- First non-comment line: `#version 330 core` (or `150`, `410`, `460`...). `core`
  vs `compatibility`; OpenGL ES uses `#version 300 es`.
- The GLSL version is tied to the GL context version you created in C. Asking for a
  `#version` the driver's context can't provide → compile error.

## Types

- Scalars: `bool`, `int`, `uint`, `float`, `double`.
- Vectors: `vec2/3/4`, `ivec*` (int), `uvec*` (uint), `bvec*` (bool), `dvec*`
  (double). Swizzles: `.xyzw`, `.rgba`, `.stpq`; writable on l-values.
- Matrices: `mat2/3/4` and non-square `matCxR` (e.g. `mat4x3`), `dmat*`.
  **Column-major** — matches what `glUniformMatrix4fv(..., GL_FALSE, ...)` expects.
- Opaque samplers: `sampler2D`, `sampler3D`, `samplerCube`, `sampler2DArray`,
  `sampler2DShadow`, `samplerCubeShadow`, and integer variants `isampler*` /
  `usampler*`. A sampler uniform's value (set from C via `glUniform1i`) is a
  **texture-unit index**, not a texture name.
- Aggregates: arrays (`float w[4]`, `.length()`), `struct`s, and interface blocks.

## Storage / interface qualifiers

- `in` / `out` — stage inputs and outputs. These **replace the deprecated
  `attribute` (vertex in) and `varying` (vs→fs)** keywords. Between stages, an
  `out` in one stage matches an `in` of the same name/type in the next.
- Vertex inputs are *generic vertex attributes*. Bind a name to an index from C
  with `glBindAttribLocation(prog, idx, "name")` **before linking**, or — preferred
  — pin it in GLSL: `layout(location = 0) in vec3 aPos;`.
- `uniform` — same value across all invocations of a draw; set from C with
  `glGetUniformLocation` + `glUniform*`. **Cannot** be changed within a single
  draw call.
- `const` (compile-time constant), `buffer` (SSBO storage), `shared` (compute
  workgroup-shared).
- Interpolation qualifiers on `in`/`out`: `smooth` (default, perspective-correct),
  `flat` (no interpolation — required for integer varyings and `gl_PrimitiveID`),
  `noperspective`, `centroid`.
- `layout(...)` qualifiers: `location=`, `binding=` (samplers/UBO/SSBO),
  `std140`/`std430` (block memory layout — std140 has strict alignment/padding
  rules you must mirror in the C struct), `triangles`/`max_vertices` (geometry),
  `local_size_x` (compute).

## Built-in variables

- Vertex: `gl_Position` (**must** write, `vec4` clip-space, `out`), `gl_PointSize`,
  `gl_VertexID`, `gl_InstanceID`.
- Fragment: `gl_FragCoord` (`in`, window-space x,y,z,1/w), `gl_FrontFacing`,
  `gl_PointCoord`, `gl_FragDepth` (`out`, optional — writing it disables early-Z).
- Geometry: `gl_in[]` array, `gl_PrimitiveIDIn`, plus `EmitVertex()` /
  `EndPrimitive()`.
- Tessellation: `gl_TessCoord`, `gl_TessLevelOuter[]`, `gl_TessLevelInner[]`,
  `gl_PatchVerticesIn`.

## Built-in functions (groups, with real names)

- **Angle/trig**: `radians`, `degrees`, `sin`, `cos`, `tan`, `asin`, `acos`,
  `atan`.
- **Exponential**: `pow`, `exp`, `log`, `exp2`, `log2`, `sqrt`, `inversesqrt`.
- **Common**: `abs`, `sign`, `floor`, `ceil`, `fract`, `mod`, `min`, `max`,
  `clamp`, `mix`, `step`, `smoothstep`. (`genType` = any of float/vec2/3/4.)
- **Geometric**: `length`, `distance`, `dot`, `cross`, `normalize`, `faceforward`,
  `reflect`, `refract`.
- **Matrix**: `matrixCompMult`, `transpose`, `inverse`, `determinant`, `outerProduct`.
- **Vector relational** (return `bvec`): `lessThan`, `lessThanEqual`, `greaterThan`,
  `equal`, `notEqual`, plus `any`, `all`, `not`.
- **Derivatives** (fragment only): `dFdx`, `dFdy`, `fwidth`.
- **Texture lookup** — exact signatures from the book (sampler2D forms):
  ```glsl
  vec4 texture     (sampler2D s, vec2 P [, float bias]);   // normalized coords, filtered
  vec4 textureLod  (sampler2D s, vec2 P, float lod);       // explicit mip level
  vec4 texelFetch  (sampler2D s, ivec2 P, int lod);        // integer texel, no filtering
  vec4 textureProj (sampler2D s, vec3/vec4 P);             // projective (÷ last comp)
  vec4 textureGrad (sampler2D s, vec2 P, vec2 dPdx, vec2 dPdy);
  ivec2 textureSize(sampler2D s, int lod);
  ```
  `*Offset` variants add a constant integer texel offset; `i`/`u` sampler variants
  return `ivec4`/`uvec4`.

## Precision (OpenGL ES / `es` profile)

`highp`, `mediump`, `lowp`. In ES fragment shaders there is **no default float
precision** — you must declare one (`precision mediump float;`) or compilation
fails. Desktop core ignores precision qualifiers (parsed, no effect).

## C-side gotchas at the GLSL boundary

- A `std140` UBO/SSBO block laid out in C must obey alignment: `vec3` aligns to 16
  bytes, array elements pad to `vec4`, `mat4` is 4×`vec4`. Mismatched padding =
  silently wrong data, no error. Prefer `std430` for SSBOs (tighter) and verify
  with `glGetActiveUniformBlockiv` / `glGetUniformIndices` offsets if unsure.
- `glGetUniformLocation`/attribute location returns `-1` for names the linker
  removed as unused (dead-code elimination). Calling `glUniform*` with `-1` is a
  silent no-op, not an error — guard it.
- Vertex attribute `type` in `glVertexAttribPointer` must match how the shader
  reads it: use `glVertexAttribIPointer` for integer `in`s (`int`/`ivec`) — the
  float path would silently convert.
