# GIS System Architecture

Use this reference when the user is building a GIS system rather than simply
using QGIS. Treat QGIS, MapLibre, OpenFreeMap, and deck.gl as implementation
reference systems to mine for architecture, data models, algorithms, and failure
patterns.

## Reference Repos

- QGIS: the selected qgis source checkout
- MapLibre: the selected maplibre source checkout
- OpenFreeMap: the selected openfreemap source checkout
- deck.gl: the selected deckgl source checkout

## Product Layers

Think in layers, and keep contracts explicit.

1. Source/providers: files, databases, APIs, OSM extracts, raster sources,
   vector tiles, point clouds, and remote services.
2. Spatial model: CRS, geometry types, features, attributes, topology, metadata,
   indexes, extents, validity, and precision.
3. Processing engine: deterministic operators, task graph, execution context,
   streaming/batching, provenance, and reproducibility.
4. Tile pipeline: source ingest, simplification, generalization, schema,
   encoding, tile pyramid, cache, invalidation, and serving.
5. Renderer: style model, source/layer graph, worker parsing, GPU buffers,
   picking, ordering, labels, terrain, and failure states.
6. Interaction: selection, identify, editing, snapping, measurement, filters,
   drawing, search/geocoding, and workflow state.
7. Map design: purpose, audience, visual hierarchy, classification, legends,
   labels, scale, export, and accessibility.
8. AI copilot: intent parsing, workflow planning, retrieval, code/tool calling,
   validation, audit trail, and memory.

## Extraction Heuristics

- From QGIS, extract data/provider abstractions, project/layer state, CRS
  discipline, Processing algorithms, layout/export concepts, and validation
  behavior. Do not assume the UX or C++/Qt structure is the product target.
- From MapLibre, extract style/source/layer separation, tile selection, workers,
  bucket parsing, painter ordering, glyph/sprite dependencies, and blank-map
  failure diagnosis.
- From OpenFreeMap, extract tile generation, hosting, cache, style delivery,
  and operational deployment patterns.
- From deck.gl, extract declarative layer lifecycle, attribute management,
  GPU data flow, picking, large-data performance, coordinate systems, and
  integration modes with MapLibre.

## Build-Vs-Borrow Questions

- Is this a core differentiator or plumbing?
- Is correctness deterministic and testable?
- Does an existing library already provide the hard invariant?
- Can the module be isolated behind a stable interface?
- What is the smallest artifact that proves the architecture?
- What failure mode will be silent unless instrumented?

## System Design Output

When designing your own GIS system, include:

- Target user/workflow:
- Reference systems to borrow from:
- Core data model:
- Deterministic execution path:
- Rendering path:
- Tile/data-serving path:
- Validation and provenance:
- Failure modes:
- First prototype slice:
- Tests or visual checks:
