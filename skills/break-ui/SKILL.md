---
name: break-ui
description: "Stress-test a component or screen with realistic, schema-backed data, states, and layout conditions to find UI failures. Use for requests to break UI, test worst-case data, or audit edge cases; preserve whether the request authorizes observation, fixtures, or fixes."
license: MIT
metadata:
  upstream: emilkowalski/skills
  upstream-commit: 2d228630ba1446365f614a108cb8252f1feda202
  adaptation: tometo-portable
---

# Break UI with realistic inputs

Find what fails when the real component receives plausible difficult inputs through its existing data boundary. Preserve the component's purpose and the user's requested mode. For visual taste or motion critique, use the corresponding design or animation skill.

## Keep the requested scope

- **Audit only:** inspect source and observe an already authorized surface. Do not edit source, add a toggle, or launch an unauthorized runtime. Report unobserved cases as inferred or unavailable.
- **Stress test:** create and run owned fixtures within the request's scope. Prefer existing Storybook stories, component tests, prototype routes, or the project's verification harness.
- **Implementation or fixes already authorized:** preserve failing evidence, apply the smallest useful fix, and recheck. Do not insert a new report-and-permission stage. Unresolved product preferences remain decisions for the user.
- A fixture-only request produces the requested fixtures and replay instructions; do not expand it into redesign or remediation.

Do not seed production, contact external URLs or media hosts, send messages, or exercise live side effects. Use reserved example domains for displayed strings and local assets or intercepted responses for media and requests. Follow the project's launch and cleanup recipe; read the existing [isolation reference](../pstack-create-verification-skill/references/isolation.md) when a run can write state or reach services. Close run-owned temporary helpers when finished; do not leave a persistent helper running by default.

## Map the rendered surface

Identify the real component and its callers before constructing data. Record each rendered field's source, type, observed limits, and optionalness, with source paths or API/schema references. Include list length, counts, timestamps, enum labels, action labels, tooltips, avatars, and fallbacks.

Check relevant validators, API types, database constraints, and form limits. Record disagreements between boundaries. Use **no limit found** or **unknown** when evidence is missing; absence of a discovered limit does not prove an unbounded field. Distinguish missing, null, empty, and whitespace-only values according to the contract.

Read the applicable groups in [the catalog](references/catalog.md). Choose plausible production values or actual accepted bounds. Keep malformed or contract-invalid probes separate from expected-valid production cases, and label why that defensive boundary matters. Do not require random strings or unreasonable lengths to manufacture a failure.

## Build a replayable stress case

Feed the actual component through its fixture, props, mock, or API-stub boundary, following existing types and conventions. Do not hand-edit UI markup or CSS merely to create a break. A standalone reimplementation can illustrate an idea but cannot prove the original component's behavior.

Use one mixed stress fixture for applicable fields, distributing cases across visible rows. Add empty, one-item, and realistic large-bound cases where the surface supports them; include page-boundary cases for paginated lists. Derive size from the product contract or observed use, and record unknown limits rather than inventing them.

Make fixtures selectable and replayable when useful, preferably through existing stories or harness controls. A dev-only route, URL parameter, or control is optional; choose placement that preserves the tested container and interaction. Keep test controls out of production builds. Record the fixture identity, selected state, and reproducible entry point.

## Observe the actual layout

Use [footwork-tools](../footwork-tools/SKILL.md) to establish an available observation/action route, then [pstack-verify](../pstack-verify/SKILL.md) for artifact identity, reproducible evidence, and scope-bound rechecks. Source inspection alone supports an inference, not a visual pass.

Test at the component's actual container width and applicable narrow/wide bounds, including text growth or browser zoom. Exercise supported dark mode, RTL, locale, keyboard, touch/pointer, and loading/error states when relevant. Do not impose unsupported environments as product requirements. Keep coverage and unavailable conditions explicit.

Look for unreadable or hidden content, unreachable actions, distorted media, clipping, broken fallbacks, misleading counts or dates, and large-list degradation. Check selection, copying, focus, and access to disclosed full values. Compare the ordinary fixture too, so a stress fix does not silently regress it.

Diagnose from the actual DOM, computed styles, data contract, and interaction. Flex shrinking, intrinsic minimum widths, overflow, or line height are hypotheses until checked; do not apply a canned CSS prescription. The catalog lists candidate mechanisms and tradeoffs.

Choose wrapping, truncation, or clamping per field. Do not truncate critical compared values such as amounts, dates, or distinguishing identifiers; use an accessible responsive representation when space is constrained. A `title` attribute alone does not provide reliable disclosure for keyboard, touch, or assistive technology. Follow the existing correct rendering boundary for untrusted text; do not introduce raw HTML or double escaping.

## Report or fix within scope

Report the failures that matter, with triggering value/state, container/environment, observed effect, evidence path, affected source path, and smallest useful fix. Separate **observed**, **inferred**, and **unavailable** evidence; mark an unconfirmed cause as inferred. Keep unresolved product decisions distinct from mechanical defects and recommend a choice with its reason.

Include what held up and the coverage limits. Identify the checked checkout/commit plus relevant local changes, or saved artifact/build, and the running version when available. Use real captures only; never fabricate a screenshot or imply an unrun fixture passed. A fixture/stub result does not prove a live integration.

When fixes are authorized, keep the original failing observation, fix within owned scope, and replay the failed and affected ordinary cases against the changed artifact. Retain a useful dev-only regression fixture when consistent with project conventions; preserve evidence independently of scratch cleanup. Report remaining failures and unavailable checks without treating them as passes.

Source and adaptation details: [provenance](references/provenance.md), for audits or updates.
