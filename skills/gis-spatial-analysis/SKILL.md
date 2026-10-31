---
name: gis-spatial-analysis
description: Plan, implement, or audit GIS analysis, QGIS automation, cartography, CRS and geometry handling, and MapLibre or deck.gl map rendering.
---

# GIS Spatial Analysis

Use this skill to turn spatial questions and custom GIS-system ideas into
grounded architecture, deterministic workflows, map design choices, rendering
plans, implementation slices, and validation plans. Use authorized source material as evidence; deterministic GIS tools or implemented code do the actual spatial computation. An optional corpus is a retrieval aid, not a required runtime.

## Workflow

1. Classify the mode:
   - Spatial analysis: buffers, overlays, joins, proximity, raster, topology,
     network, hydrology, interpolation, or suitability.
   - QGIS workflow: desktop steps, Processing algorithms, PyQGIS, projects,
     providers, layouts, plugins, or server/process usage.
   - Map design: audience, purpose, hierarchy, basemap, legend, color,
     classification, scale, projection, and export medium.
   - AI-guided GIS: natural-language request to validated deterministic workflow.
   - Web mapping: MapLibre style/sources/layers/tiles/workers/rendering,
     deck.gl layers, overlays, picking, performance, or integration.
   - Custom GIS system: extract architecture, algorithms, data models, renderer
     patterns, tile pipelines, validation logic, or UX primitives from QGIS,
     MapLibre, OpenFreeMap, and deck.gl.
   - Architecture/codebase: QGIS, MapLibre, deck.gl, provider/rendering, or
     pipeline internals.
2. Ask only material questions when missing facts would change the workflow:
   data availability, geometry types, CRS/units, scale, output medium, accuracy
   requirement, audience, and acceptable uncertainty. Otherwise proceed with
   labeled assumptions.
3. Inspect current official documentation or an already configured authorized GIS corpus. Retrieve by concept, then cite the source title and page, section, or code range used. Without a corpus, work from supplied data and primary documentation; do not imply retrieval occurred.
   - For custom GIS-system design, also load `references/retrieval-routing.md`
     and select architecture and domain evidence that answers the actual question.
4. Separate planning from execution:
   - LLM: intent parsing, workflow decomposition, tool selection, code drafting,
     map critique, and explanation.
   - Deterministic engine: QGIS Processing, PyQGIS, PostGIS, GeoPandas/Shapely,
     GDAL/OGR, raster tools, or MapLibre/deck.gl rendering.
5. Validate before trusting:
   - CRS and units are explicit.
   - Geometry validity/topology is checked.
   - Spatial predicates and buffers match the question.
   - Counts/areas/distances have sanity checks.
   - Map design choices match audience, purpose, scale, and medium.
6. Load the relevant reference:
   - `references/gis-workflow.md` for deterministic AI-guided GIS workflow.
   - `references/gis-system-architecture.md` for building a custom GIS stack
     from QGIS/MapLibre/OpenFreeMap/deck.gl reference systems.
   - `references/spatial-primitives.md` for core GIS concepts and operations.
   - `references/map-design.md` for cartographic decisions.
   - `references/qgis-architecture.md` for QGIS internals and code paths.
   - `references/qgis-automation.md` for PyQGIS/qgis_process workflows and
     deterministic QGIS execution.
   - `references/web-map-rendering.md` for MapLibre/deck.gl architecture.
7. Use `references/gis-output-template.md` when a structured analysis or map handoff is useful.

## Guardrails

- Do not claim a spatial answer is computed unless a deterministic tool actually
  computed it or the user supplied computed evidence.
- Never ignore CRS, units, geometry validity, scale, or precision. These are
  common sources of wrong GIS answers.
- Treat LLM spatial reasoning as planning support, not as geometry truth.
- Prefer reproducible workflows: data inputs, operations, parameters, versions,
  output artifacts, and validation checks.
- For map design, optimize for audience and purpose before decoration.
- For custom GIS design, distinguish reference extraction from dependency
  adoption. Borrow concepts intentionally; do not assume QGIS UI/Qt/C++ choices
  are the right product shape.
- For web maps, distinguish data ownership from rendering: tile/style/source
  systems feed MapLibre; OpenFreeMap can inform tile serving; deck.gl owns
  analytical GPU layers.
- Ignore visibly garbled PDF extraction snippets unless cleaner neighboring hits
  support the same point.

## References

- Load `references/gis-workflow.md` for mode routing, forcing questions,
  deterministic execution, validation, and AI-guided GIS boundaries.
- Load `references/gis-system-architecture.md` when the user is building a
  custom GIS product or extracting logic from QGIS, MapLibre, OpenFreeMap, or
  deck.gl.
- Load `references/retrieval-routing.md` to choose corpus query shapes for
  custom GIS architecture, deterministic GIS, web rendering, map design, or
  spatial analysis.
- Load `references/spatial-primitives.md` for CRS, vector/raster, topology,
  geoprocessing, spatial joins, raster analysis, and data quality checks.
- Load `references/map-design.md` for cartographic design, symbols, color,
  legends, hierarchy, scale, projections, and export choices.
- Load `references/qgis-architecture.md` for QGIS project/layer/provider,
  rendering, Processing, PyQGIS, server, and repo architecture.
- Load `references/qgis-automation.md` when writing or reviewing PyQGIS,
  qgis_process, Processing, layout export, provider loading, CRS debugging, or
  QGIS plugin automation.
- Load `references/web-map-rendering.md` for MapLibre/deck.gl browser map
  rendering and integration choices.
- Load `references/gis-output-template.md` before producing a final map or plan.
- Load `references/source-map.md` when refreshing the corpus, validating ingest,
  or explaining provenance.
