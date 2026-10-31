# QGIS Architecture

Use this reference when explaining or working in the QGIS codebase.

## Big Shape

QGIS is a Qt/C++ GIS platform with multiple shells around shared core services:

- `src/core`: data model, project model, providers, rendering settings,
  geometry, CRS, expressions, layouts, Processing registry, and registries.
- `src/gui`: reusable Qt widgets, source selectors, browser UI, map canvas
  helpers, and Processing UI components.
- `src/app`: desktop application orchestration.
- `src/providers`: dynamic data provider plugins for file, database, web, mesh,
  point cloud, and service sources.
- `src/analysis` and `src/core/processing`: analysis helpers and native
  Processing algorithms.
- `python` and `src/python`: PyQGIS bindings and embedded Python bridge.
- `src/server`: headless OGC/API map service runtime.
- `src/process`: `qgis_process` command-line Processing runner.

## Runtime Anchors

- `QgsApplication::initQgis()` initializes provider registry, data item registry,
  singleton project, auth storage, and network access manager.
- `QgsProject` is the in-memory document model: layers, layer tree, CRS,
  transform context, layouts, relations, metadata, temporal/elevation settings,
  map themes, and path resolution.
- Layers wrap provider data with QGIS behavior: styling, editing, labeling,
  selections, temporal settings, and project integration.
- Providers own data access and capabilities; provider metadata creates
  providers, parses URIs, supplies filters, and exposes browser items.

## Rendering Flow

1. `QgsMapCanvas` keeps `QgsMapSettings` aligned with project state.
2. Refresh filters invalid layers and builds render jobs.
3. Parallel or sequential render jobs prepare layer jobs.
4. Labeling, symbolization, caches, transform context, and map themes affect
   final output.

## Processing Mental Model

Processing algorithms are provider-owned, parameterized operations. Prefer
calling them through QGIS Processing or `qgis_process` for reproducible workflows
instead of treating them as isolated UI tools.

When answering codebase questions, cite the relevant source path and explain the
user workflow first, then the implementation path.
