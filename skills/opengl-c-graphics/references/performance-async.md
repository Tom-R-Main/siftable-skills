# Performance & Asynchronous Transfers (C)

Source: **OpenGL Insights** (eds. Cozzi & Riccio) — Ch.25 (reducing driver calls),
Ch.28 (async buffer transfers), Ch.29 (async texture transfers), Ch.21/26 (vertex
pulling / multi-array indexing). These are expert-level, GPU-measured practices.
Checklist, not law — and **measure before and after** (see `debugging-profiling.md`
for timer queries).

## Ch.25 — Reduce calls to the driver

The driver call itself is expensive (validation, state shadowing, sometimes a
kernel transition). Golden rules:

- **Filter redundant state changes.** Shadow GL state on the CPU and skip calls
  that would set state to its current value. The book notes state-tracking alone
  won't *dramatically* help unless your app actually issues redundant calls — so
  profile first.
- **Batch.** Merge draws that share state; sort draws by program → texture → VAO to
  minimize transitions between them.
- **Instance** instead of looping `glDrawArrays` per object
  (`glDrawArraysInstanced`, instanced arrays). See `modern-pipeline.md`.
- **Use UBOs** to push many uniforms in one update and share them across programs,
  rather than many `glUniform*` calls per frame.
- **Avoid `glGet*` / queries on the hot path** — most force a CPU↔GPU sync (stall).
- **Never create buffers/textures/programs per frame.** Allocate once, reuse.

## Ch.28 — Asynchronous buffer transfers (streaming dynamic data)

`GL_STATIC/DYNAMIC/STREAM_DRAW` are only *hints*; the real control over stalls is
**how you map/respecify the buffer**. A naive `glBufferSubData` or a plain
`glMapBuffer` on a buffer the GPU is still reading forces an **implicit
synchronization** (the CPU blocks until the GPU finishes). Three strategies to
avoid it:

1. **Round-robin / multi-buffering.** Keep N buffer objects and cycle one per frame
   so the CPU writes buffer *i* while the GPU still reads *i−1*. Simplest reliable
   way to dodge implicit sync.

2. **Buffer respecification ("orphaning").** Re-call
   `glBufferData(target, size, NULL, usage)` to throw away the current data store
   *before* uploading new data. The driver hands you a **fresh** block immediately
   and recycles the old one once the GPU is done — no stall, one buffer name.
   ```c
   glBindBuffer(GL_ARRAY_BUFFER, vbo);
   glBufferData(GL_ARRAY_BUFFER, size, NULL, GL_STREAM_DRAW);  /* orphan */
   glBufferSubData(GL_ARRAY_BUFFER, 0, size, new_data);        /* fresh store */
   ```
   `glMapBufferRange(... GL_MAP_INVALIDATE_BUFFER_BIT)` is the map-based equivalent.

3. **Manual synchronization** with `glMapBufferRange` + fences — fastest, most
   dangerous. You promise the GPU isn't using the region:
   ```c
   void *p = glMapBufferRange(GL_ARRAY_BUFFER, offset, size,
                              GL_MAP_WRITE_BIT | GL_MAP_UNSYNCHRONIZED_BIT);
   /* ...write p... */         /* UNSYNCHRONIZED: no implicit wait — your job */
   glUnmapBuffer(GL_ARRAY_BUFFER);
   GLsync f = glFenceSync(GL_SYNC_GPU_COMMANDS_COMPLETE, 0);   /* after the draw */
   /* before reusing that region next time: */
   glClientWaitSync(f, 0, TIMEOUT_NS);
   glDeleteSync(f);
   ```
   Map flags: `GL_MAP_WRITE_BIT`, `GL_MAP_READ_BIT`,
   `GL_MAP_INVALIDATE_RANGE_BIT`, `GL_MAP_INVALIDATE_BUFFER_BIT`,
   `GL_MAP_UNSYNCHRONIZED_BIT`, `GL_MAP_FLUSH_EXPLICIT_BIT` (then
   `glFlushMappedBufferRange`).

**Combine them:** a round-robin chain of unsynchronized buffers guarded by per-slot
fences is the book's best-performing pattern. Rule of thumb: **don't let the GPU
fall more than ~2 frames behind** the CPU, or `glClientWaitSync` becomes the stall
you were avoiding.

## Ch.29 — Asynchronous texture transfers

- Upload through a **Pixel Buffer Object** (`GL_PIXEL_UNPACK_BUFFER`). With a PBO
  bound, `glTexSubImage2D(..., offset)` takes a **buffer offset** instead of a
  client pointer, so the driver can DMA the copy asynchronously instead of blocking
  on your `malloc`'d array.
- Prefer **`glTexSubImage2D`** (updates in place) over `glTexImage2D` (reallocates
  the texture store) for per-frame updates.
- **Double-buffer the PBOs** (fill one with the CPU while the GPU consumes the
  other), same idea as buffer round-robin.

## Ch.21 / Ch.26 — Programmable vertex pulling & multi-array indexing

Instead of fixed-function attribute fetch, **pull** vertex data inside the vertex
shader from a buffer (texture buffer object / SSBO) indexed by `gl_VertexID` (and
`gl_InstanceID`). Lets one draw index several independent arrays and cuts attribute
setup. Trade-off: manual fetch can be slower than the hardware vertex puller for
simple layouts — measure.

## C-side notes

- Use `GLsizeiptr` for buffer sizes and `GLintptr` for offsets (the
  `glBufferData`/`glMapBufferRange` size/offset types), not `int` — large buffers
  overflow a 32-bit `int`.
- `glMapBufferRange` returns `NULL` on failure — check it before writing, exactly
  like `mmap`/`malloc`.
- A mapped pointer is invalid after `glUnmapBuffer`; never cache it across frames.
- `GLsync` objects are handles you own: every `glFenceSync` needs a matching
  `glDeleteSync`, or you leak GPU sync objects.
