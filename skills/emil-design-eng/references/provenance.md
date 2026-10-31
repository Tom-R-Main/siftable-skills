# Provenance and adaptation

Curated from Emil Kowalski's MIT-licensed [skills repository](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202), reviewed in full on October 26, 2026 at immutable commit `2d228630ba1446365f614a108cb8252f1feda202`. Retain the included upstream LICENSE when redistributing substantial adapted material.

This portable adaptation resolves bundled references and sibling skills relative to the loaded package. The main skill remains short; specialist source material is exposed through conditional references, not default stages or newly installed libraries.

| Local reference | Reviewed upstream material |
|---|---|
| [Motion](motion.md) | [emil-design-eng](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/skills/emil-design-eng/SKILL.md), [animate and recipes](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202/skills/animate), [animation-vocabulary](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/skills/animation-vocabulary/SKILL.md) |
| [Performance](performance.md) | [animation-performance](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/skills/animation-performance/SKILL.md), [performance cheatsheet](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/performance-cheatsheet.md) |
| [Review/discovery](review-and-discovery.md) | [review-animations and standards](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202/skills/review-animations), [find-animation-opportunities](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/skills/find-animation-opportunities/SKILL.md), [improve-animations and templates](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202/skills/improve-animations) |
| [Mobile web](mobile-web.md) | [mobile-native](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/skills/mobile-native/SKILL.md), [apple-design](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/skills/apple-design/SKILL.md) |
| [Prototypes](prototypes.md) | [prototype and picker](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202/skills/prototype) |
| [Libraries](libraries.md) | [pick-ui-library](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/skills/pick-ui-library/SKILL.md), [ask-sonner and API](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202/skills/ask-sonner) |
| [Native specialists](native-specialists.md) | [animate-expo and recipes](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202/skills/animate-expo), [write-swift](https://github.com/emilkowalski/skills/blob/2d228630ba1446365f614a108cb8252f1feda202/skills/write-swift/SKILL.md) |

Corrections preserve existing scope and product semantics:

- No readiness-only response, persona claim, compulsory table, fixed variant/finding count, or new approval stage. Reviews remain read-only and already-authorized implementation continues.
- Timings, curves, press scaling, blur and stagger are contextual choices. The source's universal 300ms cap conflicts with its 200–500ms drawer examples; no such universal cap is imported.
- Compositor eligibility, driver scheduling and measured runtime cost are separate. Blanket guarantees about CSS/WAAPI/Motion props, clipping, blur and `will-change` are not imported. Official sources reviewed include [Motion performance](https://motion.dev/docs/performance), [MDN reduced motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion), and [W3C Pointer Events](https://www.w3.org/TR/pointerevents3/#details-of-touch-action-values).
- Reduced motion can remove nonessential motion. Input/focus, visibility, selection, pinch zoom and accessible alternatives remain functional; visual gesture recipes are not complete controls.
- The prototype picker is a behavior sketch, not verbatim code. Validate an invalid/out-of-range URL selection and preserve native activation/focus; do not copy its blank-initial-variant edge case.
- Sonner examples require the installed package/types and cascade. `dismissible` is not automatically a duration setting; blanket `!important` is not a styling policy.
- Swift concurrency depends on target settings, including NonisolatedNonsendingByDefault. `private` is not file scope. Expo recipes depend on installed framework generations and are not verified drop-ins.

No upstream example was compiled or run during source review. Each real project must establish its own driver, versions and relevant browser/device evidence. This adaptation installs instructions only, with no packages, runtime provider, global hook, scheduled work, or statechart tooling. Dryer remains advisory; formal and recurring-work checks remain optional.
