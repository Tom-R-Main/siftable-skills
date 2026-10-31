Relevance gate: Read this only for mobile browser or PWA layout, input, touch, or platform integration work. Upstream `mobile-native` and `apple-design` concern web experiences; they do not select React Native or impose an Apple theme on unrelated products.

# Mobile web and PWA

Use the [shared workflow](../SKILL.md) and the product's existing components and visual language. Read [provenance](provenance.md) for the reviewed sources and corrections.

## Viewport, safe areas, and software keyboards

- Account for safe-area insets where content or controls reach a viewport edge; avoid adding the same inset twice through nested containers.
- Choose viewport units by behavior: `svh` stabilizes against browser chrome, while `dvh` follows the dynamic viewport. Verify the target browser's behavior before changing an existing layout.
- Test browser chrome expansion, orientation changes, software keyboard opening, and dismissal. A desktop resize alone does not cover those states.
- Keep focused inputs and their labels visible without trapping the document in an unscrollable fixed shell.
- Inspect layout and visual viewport changes before adding resize listeners or keyboard heuristics. Clean up listeners and avoid resize loops.
- Preserve user input, selection, focus, and scroll position through responsive transitions and keyboard changes.
- Use suitable input types, labels, autocomplete, and input modes; do not use placeholder text as the only label.
- Prevent accidental input zoom through readable input typography where needed; preserve the user's ability to pinch zoom.

## Touch, mouse, and semantic activation

- Support touch and mouse combinations, including tablets with trackpads. Screen width is not evidence of a particular input device.
- Gate hover-only decoration with appropriate hover and pointer capability queries; make every required action available without hover.
- Make targets large enough to acquire comfortably, with separation between adjacent controls. Check effective hit areas, not just icon dimensions.
- Keep links as links and actions as buttons, with visible keyboard focus and meaningful accessible names.
- `pointerdown` can start visual feedback; it must not replace semantic `click` activation or break keyboard, assistive technology, cancellation, or link behavior.
- Preserve content selection and normal link interactions. Never disable selection across all anchors or the entire page.
- Scope `touch-action` to the specific gesture surface and allowed axes; never apply `touch-action: none` globally.

## Gesture ownership and cancellation

- Track the initiating `pointerId`; ignore unrelated pointers and decide explicitly how additional contacts affect the interaction.
- Capture the pointer when the component owns the gesture, and handle `pointercancel` and `lostpointercapture` as cleanup paths.
- Release transient state, listeners, capture, and pending animation on completion, cancellation, or unmount.
- Arbitrate horizontal gestures against vertical page scrolling before committing. Avoid stealing scroll from nested content or browser navigation.
- Choose thresholds from the control's geometry and observed interaction; there is no universal swipe distance or velocity constant.
- Calculate velocity over a meaningful recent interval and preserve its direction. Use direction and displacement together when deciding whether to finish or return.
- Offer accessible button or keyboard alternatives to gesture-only actions, and avoid committing destructive actions during an ambiguous drag.

## Preferences and evidence

- Treat reduced motion, reduced transparency, and contrast preferences independently; one does not imply the others.
- Preserve state changes and useful feedback when simplifying animation or translucent surfaces. Check readability against actual backgrounds.
- Use [CSS guidance](../../css/SKILL.md) for layout and preference queries; read the motion reference only when animation is part of this task.
- Emulation can cover viewport and input scenarios; label it as emulation. Device-specific keyboard, browser chrome, scrolling, and gesture claims need evidence from that device and browser.
- Use [pstack-verify](../../pstack-verify/SKILL.md) when real-surface verification is relevant. Record what was exercised and what remains unverified.
- Use [footwork-tools](../../footwork-tools/SKILL.md) only when actual device access is requested and available. Do not assume phone access, expose a development server to the LAN, or bind to `0.0.0.0` merely to obtain a mobile check.
