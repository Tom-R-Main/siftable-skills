# Web Map Rendering

Use this reference for MapLibre, deck.gl, and browser map architecture.

## MapLibre Mental Model

MapLibre GL JS consumes style JSON, sources, tiles, sprites, and glyphs. It does
not own the data. The main thread manages map state, camera, style, tile
selection, and render scheduling. Workers fetch and parse tiles. The painter
uploads buffers and draws ordered WebGL passes.

Key split:

- Map/Style: decide what should exist for the current camera and style.
- TileManager/Sources/Workers: fetch and convert geographic features into
  render-ready buckets.
- Painter: draw those buckets as ordered WebGL calls.

Failure mode: a smooth renderer can still show a blank map if source URLs,
tile coordinates, style layers, glyphs, sprites, or worker parsing fail.

## deck.gl Mental Model

deck.gl is a declarative GPU visualization engine. The app provides data,
layers, views, and view state. Deck diffs layer/view props, preserves internal
state by layer id, updates GPU attributes/uniforms, and draws via WebGL/WebGPU.

Use deck.gl for analytical/high-volume visual layers, picking, custom shaders,
3D/instanced rendering, and data-driven overlays.

## Integration Modes

- Interleaved: deck.gl shares MapLibre's WebGL2 context and inserts custom
  layers into the style stack. Use when deck layers must appear below labels or
  interact correctly with 3D/depth ordering.
- Overlaid: deck.gl uses a separate canvas synchronized to MapLibre camera and
  events. Use for simpler overlays with MapLibre controls/plugins.
- Reverse-controlled: deck.gl owns camera/input and MapLibre is a background
  child. Use when deck needs multi-view/custom interaction control.

## Debug Checklist

- Is the style JSON loaded and valid?
- Are source URLs, tile bounds, min/max zoom, and attribution correct?
- Are glyphs/sprites reachable?
- Are layer ids, source-layer names, and filters correct?
- Is the deck layer id stable across renders?
- Is `beforeId` valid for interleaved ordering?
- Is WebGL2 available when interleaving?
- Are coordinates lon/lat and in expected order?
- Are data volumes chunked/tiled enough for the browser?
