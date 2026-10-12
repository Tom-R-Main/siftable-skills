---
name: generating-design-references
description: Generate and critique a design-reference image when no existing visual precedent fits. Use only when an approved image-generation tool or user-configured generator is available; the result is a reasoning scaffold rather than a deliverable or fidelity target.
---

# Generating design references

Create a concrete visual anchor to think against when a blank-page interface decision cannot be grounded in an existing reference. Installing this skill does not supply image generation, provider authentication, or a cost-free route.

## Ground before generating

1. Search [searching-design-corpus](../searching-design-corpus/SKILL.md) when a corpus is configured and inspect the project's existing UI and user-supplied references.
2. Record why available precedents do not fit. Missing corpus access is a limitation, not evidence that no precedent exists.
3. Generate only when a concrete image will resolve a meaningful design uncertainty. Do not substitute repeated generation for building and exercising the interface.

## Capability preflight

Prefer the active host's exposed image tool and follow its runtime skill. Confirm generation is available, the user's scope permits it, and any paid provider invocation is authorized. Do not assume a local subscription transfers to cloud, inspect credentials, install a provider, or claim there is no API cost.

When no native tool is exposed, a user may configure `DESIGN_REFERENCE_BIN` to an absolute trusted executable implementing:

```text
<generator> --description <text> --output <absolute PNG path>
```

The external generator must use opaque configured runtime credentials, honor the exact output path, and exit nonzero on failure. It is not bundled. The adapter below only invokes that configured executable and verifies the saved file's PNG signature; it supplies no model or authentication.

Resolve `SKILL_DIR` from this loaded file. Choose a new output path in the authorized task scratch area:

```bash
"$SKILL_DIR/design-reference.sh" "<what to depict, with style cues>" "$RUN_DIR/reference.png"
```

The adapter refuses an existing destination, never scans global image directories, and reports the exact output file. On an uncertain dispatch, inspect the requested file and provider status before retrying.

## View, critique, and verify

Open the actual saved image with the host's image-viewing tool. Generation without viewing is not design evidence. Critique hierarchy, spacing, type, components, accessibility, and fit to the product and acceptance criteria. Record what to use and reject.

Generated images remain reasoning scaffolds; user-supplied references may be fidelity targets. Never ship a generated mockup as the working interface or treat it as proof of behavior. In a supervised workflow, only the trusted monitor generates, views, critiques, and supplies the image. Writers may inspect the supplied copy but must not invoke the generator. Verify the resulting implementation on its actual surface.
