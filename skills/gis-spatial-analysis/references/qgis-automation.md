# QGIS Automation

Use this reference when the answer should produce QGIS/PyQGIS/qgis_process work
or extract QGIS Processing behavior for a custom GIS system. This is secondary
to `gis-system-architecture.md` when the user is designing their own stack.

## Routing

- Core architecture: use `qgis-architecture.md`.
- Data loading/provider issues: identify provider, URI, layer validity, encoding,
  file locks, auth, and schema.
- CRS/projection issues: inspect CRS, axis order, units, datum transform, and
  target analysis CRS before running operations.
- Vector analysis: buffer, clip, intersect, dissolve, spatial join, nearest,
  aggregate, and writer/export parameters.
- Raster analysis: warp, align, clip, resample, map algebra, nodata, DEM
  derivatives, and cell-size decisions.
- Layout/export: map item, extent, scale, legend, labels, atlas, DPI, PDF/SVG/PNG.
- Web services: WMS/WFS/WMTS/XYZ, OGC API, server publication, and tile caching.
- Plugins: metadata, lifecycle hooks, actions, UI forms, resources, and reload.

## qgis_process Pattern

Prefer capability discovery over memorized algorithm syntax.

```bash
qgis_process list
qgis_process help native:buffer
qgis_process run native:buffer -- INPUT=... DISTANCE=... OUTPUT=...
```

Before running:

- Confirm the QGIS install and version.
- Inspect algorithm help for exact parameter names.
- Write outputs to new files unless the user explicitly permits overwrite.
- Prefer GeoPackage for vector intermediates and GeoTIFF for raster outputs.
- Use absolute paths in generated commands.

## PyQGIS Pattern

Use PyQGIS when the workflow needs project composition, layer styling, layout
export, custom expressions, plugin code, or iterative control.

Always include:

- QGIS application bootstrap requirements for standalone scripts.
- Layer validity checks after loading.
- Explicit CRS transform context.
- Error handling around processing results.
- Output path checks before writing.

## Anti-Patterns

- Assuming the goal is to use QGIS directly when the task is to extract logic
  for a custom GIS system.
- Running buffer/distance/area in EPSG:4326 without a tool that handles geodesic
  measurement intentionally.
- Assuming `lat, lon` when APIs expect `lon, lat`.
- Treating an invalid loaded layer as usable.
- Overwriting source files or writing outputs into unclear temp paths.
- Using UI clicks when `qgis_process`, Processing, or PyQGIS can make the
  workflow reproducible.
- Trusting a map screenshot without checking the output data table/geometry.

## Error Diagnosis

1. Name the symptom.
2. Check layer validity and provider error message.
3. Check path, permissions, encoding, and file locks.
4. Check CRS/units and geometry validity.
5. Run the smallest reproducible operation.
6. Only then patch the workflow or code.
