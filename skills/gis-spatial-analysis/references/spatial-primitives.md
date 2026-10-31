# Spatial Primitives

Use this reference for the core concepts that should be explicit in GIS answers.

## Data Models

- Vector: points, lines, polygons, attributes, topology, multipart features.
- Raster: cells, bands, resolution, extent, nodata, resampling, map algebra.
- Tables: attributes with keys that may join to spatial layers.
- Tiles: pyramid-indexed vector or raster chunks for web rendering.
- Point clouds/meshes: dense 3D or surface data with specialized providers.

## CRS And Measurement

- Geographic CRS gives angular coordinates; projected CRS gives planar units.
- Use appropriate projections for distance, area, direction, or shape.
- Never buffer or measure in degrees unless the workflow explicitly supports it.
- Track datum transformations and axis/order expectations.
- For web maps, distinguish display projection from analysis projection.

## Common Operations

- Select/filter by attribute or spatial predicate.
- Reproject/transform layers into an analysis CRS.
- Buffer, dissolve, clip, erase, intersect, union, difference.
- Spatial join, nearest neighbor, point-in-polygon, aggregate by polygon.
- Raster reclassify, slope/aspect, zonal statistics, cost surface, viewshed.
- Network routing, service areas, snapping, topology repair.
- Generalize/simplify for scale while preserving intended topology.

## Quality Risks

- Missing metadata or stale source data.
- Mixed CRS or unit assumptions.
- Invalid geometries and self-intersections.
- Boundary effects near study-area edges.
- Slivers and duplicate records after overlay.
- Unclear inclusion rule for features crossing a boundary.
- Classification or color choices that exaggerate patterns.
- Web map tiles that render smoothly while source data failed to load.
