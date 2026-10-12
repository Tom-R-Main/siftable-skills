---
name: pstack-maintain-verification-skill
description: "Audit a project verification skill against source and live feature behavior. Use when its harness or instructions have drifted; correct verified harness drift within scope without hiding product regressions."
license: MIT
metadata:
  upstream: cursor/plugins/pstack
  upstream-commit: 5bf2b1544db739998121a306340631963c2ff3de
  adaptation: tometo-codex
---

# Maintain a verification skill

Locate the existing project verification skill and its feature map. If multiple plausible targets remain after reading task context, ask which target; if absent, point to [pstack-create-verification-skill](../pstack-create-verification-skill/SKILL.md). Do not invent an audit target.

Limit edits to that skill's directory and its owned harness. An audit-only request stays read-only. A maintenance/fix request authorizes proven skill corrections, not product changes.

Apply [pstack-verify](../pstack-verify/SKILL.md) to the live recipes: distinguish delivery from the requested effect, check resource-bound readbacks, and invalidate current-state evidence after subsequent edits or navigation. Check relevant failure/recovery paths when the mapped feature promises them. Historical events and answer provenance need their own evidence; a generic final screen cannot replace either. Reconcile an uncertain mutation before retry, without repeating effects just to obtain proof.

1. Reconcile the index with feature files and current public entry points. Inspect relevant source changes for omitted features; require a concrete source path before calling one missing.
2. Trace each mapped feature to source and derive a concise live recipe. For a large map, bounded read-only source reviewers may work independently when permitted; only the coordinator drives shared app state.
3. Follow the skill's launch model and doctor checks. Exercise every mapped feature at least once, track entry-point/sub-feature gaps, and preserve evidence. Do not call a pass clean merely because source looks consistent.
4. Recheck health after surprises. Reset a wedged state or relaunch only the run-owned instance. Clean failed-attempt residue without deleting prior proof. If a doctor command itself has drifted, correct it within scope and re-run the affected path before judging the app.
5. Classify drift: wrong documentation, harness inability to drive working behavior, or a product regression. Fix only authorized documentation/harness drift. Do not redefine expected behavior to make a broken product pass. An unreachable feature is unverified, with the attempted route and missing prerequisite recorded.
6. Re-run affected live paths after every harness correction. Complete cleanup and verify evidence survival. Report feature coverage and outcome: **clean** only for completed source/live coverage without material gaps, **changed** for executed corrections with their coverage, or **blocked** when coverage could not finish. Partial corrections may accompany a blocked result.

Keep evidence in the project-designated output location, scoped to the task. Commit, PR creation, scheduled maintenance, merge, and external messages require their own task authorization; none is an automatic final step.

Source and adaptation details: [provenance](references/provenance.md). Read only when auditing or updating this skill.
