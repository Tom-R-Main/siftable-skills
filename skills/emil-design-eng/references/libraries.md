Relevance gate: Read this only when choosing or adapting an interaction library, or resolving a concrete library integration issue. These are curated candidates and recipe cautions, not required dependencies.

# Interaction libraries

Use the [shared workflow](../SKILL.md) and [provenance](provenance.md). Prefer the project's existing primitives; simple feedback often belongs in [CSS](../../css/SKILL.md).

## Establish the installed contract

- Inspect the package manifest, lockfile, installed version, exported types, peer dependencies, and existing usage before adapting a recipe.
- Check the project's framework boundaries, providers, portals, styling conventions, and accessibility behavior before adding another abstraction.
- Use the installed version's API. Example imports, options, callbacks, and defaults from another release are not proof of compatibility.
- If a new library is justified, verify its current primary documentation and explain the capability it supplies beyond existing code.
- Keep upgrades and dependency changes within the task's authorization. Do not run an install, upgrade packages, or churn the lockfile merely because a candidate appears here.
- Prefer an existing headless primitive for focus, dismissal, keyboard navigation, and accessible semantics when it already meets the need.

## Candidates by problem

- Sonner: toast notifications when the project needs a consistent notification lifecycle and already uses or has chosen this pattern.
- Base UI: headless interaction primitives when existing components cannot supply the required behavior.
- Motion: coordinated or interruptible animation when CSS and the existing animation stack are insufficient.
- cmdk: command-menu behavior when search, selection, keyboard navigation, and composition fit the product's actual task.
- input-otp: segmented verification-code input when paste, autofill, focus, and assistive technology behavior have been verified.
- Virtualization: large collections when profiling shows rendering cost; account for variable sizes, focus, search, scroll restoration, and accessible navigation.
- Select the smallest useful integration. A toast need does not justify replacing the dialog, menu, motion, or form stack.

## Sonner integration cautions

- Place the provider/toaster in the framework's supported client boundary and intended layout scope. Check whether navigation remounts it and whether duplicate instances compete.
- Verify the installed types for provider props, toast options, callbacks, and custom content; do not import a remembered API signature untested.
- Use stable toast IDs when an operation should update one notification. Keep independent operations distinct and avoid stale updates after completion.
- Model pending, success, and failure against the actual promise lifecycle. Handle rejection in the application flow as well as notification rendering.
- Distinguish an operation failing from a toast being dismissed; dismissal callbacks must not silently change business state or imply success.
- Check timeout and dismissal options separately. `dismissible: false` is not a general control for disabling automatic timeout.
- Verify duration behavior and callback timing for the installed release; do not assume fixed defaults or callback types across versions.
- Keep user-facing errors useful and avoid exposing raw secrets, internal payloads, or stack traces through toast text.
- Make action buttons meaningful, accessible, and safe to invoke once or repeatedly as the operation requires. Preserve a durable path to consequential information.
- Inspect rendered markup, documented data attributes, and the current styling API before overriding appearance. Use scoped tokens or selectors; do not add blanket `!important` rules.
- Check stacking, pointer interaction, contrast, and announcement behavior on the real screen, including other overlays and narrow viewports.

## Validate the chosen integration

- Check keyboard operation, focus restoration, screen-reader semantics, reduced motion, interruption, and cleanup in the component's actual context.
- Measure performance before claiming a library or virtualization change improved it; include the data size and interaction used.
- Use the project's existing checks and [pstack-verify](../../pstack-verify/SKILL.md) when behavior on the running surface matters.
- Report the installed version and any unresolved compatibility boundary. A recipe is a starting point, not evidence that an integration works.
