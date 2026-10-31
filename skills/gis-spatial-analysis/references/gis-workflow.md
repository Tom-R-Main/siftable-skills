# GIS Workflow

Use this reference when turning a spatial request into a reproducible plan.

## Forcing Questions

Ask only the questions that can change the workflow.

- Purpose: what decision, map, or artifact will this support?
- Study area: what geography and boundary define the work?
- Data: what layers exist, where did they come from, and are they current?
- Geometry: point, line, polygon, raster, mesh, point cloud, tile, or table?
- CRS and units: what CRS is each layer in, and what units should distances,
  buffers, areas, and scales use?
- Accuracy: what precision and tolerance are acceptable?
- Output: map, table, GeoPackage, tiles, web layer, report, script, or QGIS
  project?
- Validation: what independent check would catch a wrong answer?

## Deterministic Execution Pattern

1. Restate the spatial question in operational terms.
2. Inventory required layers and attributes.
3. Normalize CRS, geometry validity, and units.
4. Build a task graph of GIS operations.
5. Execute with QGIS Processing, PyQGIS, PostGIS, GeoPandas/Shapely, GDAL/OGR,
   raster tools, or a renderer.
6. Validate counts, distances, areas, topology, edge cases, and visual output.
7. Return provenance, assumptions, artifacts, and limitations.

## AI-Guided GIS Boundary

The model can parse intent, choose tools, draft code, explain workflows, and
critique maps. It should not invent computed spatial answers. A correct answer
requires a deterministic engine or user-supplied computation.

Use retrieval to ground tool names, parameters, and architecture. Use generated
code as a draft that must be checked against data schema and tool docs.

## Validation Checklist

- CRS chosen for the operation, not just the data source.
- Distance/area operations use projected units when needed.
- Invalid geometries repaired or excluded with a named rule.
- Spatial predicates match semantics: intersects, contains, within, touches,
  overlaps, nearest, crosses, disjoint.
- Buffer dissolve/endcap/join options are intentional.
- Overlay outputs are checked for slivers, multipart features, and nulls.
- Raster cell size, alignment, nodata, resampling, and extent are explicit.
- Output map scale and classification do not imply false precision.
- Results include enough provenance to rerun the workflow.
