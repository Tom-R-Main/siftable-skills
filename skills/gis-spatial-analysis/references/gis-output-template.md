# GIS Output Template

Use this structure for final outputs. Keep it compact for small questions and
expand it for high-stakes analysis, map design, or implementation work.

## Spatial Verdict

- Recommended path:
- Mode:
- Confidence:
- Do not do:

## System Architecture

Use when building a custom GIS system.

- Product layer:
- Reference systems to borrow from:
- Core abstraction:
- Build vs borrow decision:
- Prototype slice:
- Main invariant:
- Silent failure to instrument:

## Corpus Grounding

List only sources actually used.

```text
- Source title, chunk/page: what it contributes
```

## Spatial Question

- Operational question:
- Study area:
- Required layers:
- Geometry/data model:
- CRS and units:
- Output artifact:

## Deterministic Workflow

1. Input preparation:
2. Analysis operations:
3. Tool/engine:
4. Parameters:
5. Output:
6. Reproducibility notes:

## QGIS Automation Plan

Use when relevant.

- Interface: qgis_process / PyQGIS / QGIS GUI / QGIS Server / plugin
- Algorithms or APIs:
- Input paths:
- Output paths:
- Layer validity checks:
- CRS/transform checks:
- Overwrite policy:
- Error handling:

## Validation

- CRS/units check:
- Geometry/topology check:
- Count/area/distance sanity check:
- Edge cases:
- Visual inspection:
- Assumptions that could flip the result:

## Map Or Rendering Plan

Use when relevant.

- Audience and purpose:
- Basemap:
- Symbolization/classification:
- Legend/labels:
- Projection/scale:
- Web rendering mode:
- Performance risks:

## Next Action

- Immediate next step:
- Information worth gathering:
- Command/code/artifact to produce:
