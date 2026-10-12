---
name: pstack-create-verification-skill
description: "Create and execute a project-local verification skill that launches and drives the real surface, records feature coverage, and preserves evidence. Use when authorized work needs a repeatable verification recipe and none exists."
license: MIT
metadata:
  upstream: cursor/plugins/pstack
  upstream-commit: 5bf2b1544db739998121a306340631963c2ff3de
  adaptation: tometo-codex
---

# Create a verification skill

Generate reusable instructions for another agent to prove real application behavior. Prefer an existing repository skill and harness; extend them rather than create a competing verification system. Stay inside the authorized project.

## Discover from the repository

Identify the real user surface, documented run/build commands, toolchain, readiness signals, existing tests and drivers, observable state, and isolation controls. Read configuration schemas or examples for required variable names without exposing secret values. Use [footwork-tools](../footwork-tools/SKILL.md) to choose and establish the actual observation/action driver for the surface, then follow its host skill. Record a working observation and action recipe; a referenced but unavailable tool leaves the verifier a draft. Do not assume Cursor tools or a particular browser backend.

Distinguish an application defect, missing local prerequisite, and missing harness capability. If the project cannot start, report the concrete blocker; do not silently widen this task into repairing unrelated product code.

## Generate

Use the repository's existing discoverable skill location. Otherwise use `.agents/skills/verify-<app>/` for a Codex project. Inspect existing instructions before adding a directory. Include a valid name and a description naming the app, surface, and trigger.

Write only grounded commands, with no unresolved placeholders:

- **Launch:** exact build/start command, working directory, readiness check, and isolated ports/data/profile selection. A short-lived CLI may launch anew for each drive.
- **Doctor:** a cheap read-only check of the intended artifact/version, readiness, and ownership before driving. Repeat after surprising behavior; reset stale state when process health does not imply UI health.
- **Drive:** existing harness commands and stable selectors/arguments from the real app. Exercise public user paths, not internal setters or test-only bypasses.
- **Evidence:** actions plus observed results, relevant side effects, exit status, and artifact identity. Store proof outside scratch directories that cleanup removes. Do not capture credentials or unrelated personal data.
- **Cleanup:** terminate only processes started by this run, using recorded handles; remove only run-owned scratch state. Preserve proof. Never kill by broad process name or port alone.
- **Helpers:** executable scripts only when they remove repeated or fragile work, with exact invocations in the skill.

Create `features/README.md` and a small initial set of feature pages grounded in source routes, commands, or menus. Each page records purpose, user entry point(s), prerequisites, driving recipe, observable success/failure, and known coverage gaps. List the mapped entry points so later runs cannot quietly prove only the convenient path.

For multi-step flows, map each required criterion to historical-action, current-state, or answer evidence, including the intended resource and any invalidation conditions. Choose readback that proves the requested effect; a delivered input, changed page, or generic confirmation is insufficient for persistence or submission claims. Include a relevant failure/recovery recipe and reconcile uncertain mutations before retry. Reuse deterministic driver checks for these mechanics. The execution standard is [pstack-verify](../pstack-verify/SKILL.md).

## Execute before delivery

Follow the generated instructions yourself: launch, doctor, drive at least one mapped feature through its actual public interface, capture proof, clean up, then confirm proof still exists. On failed attempts, clean up run-owned resources before retrying. Validate added helper scripts and skill frontmatter.

If runtime access is blocked, deliver a clearly labeled draft with the exact unexecuted steps and reason; never claim a tested verifier. One feature executed validates that path, not the entire feature map. Report executed coverage explicitly.

Mention [pstack-maintain-verification-skill](../pstack-maintain-verification-skill/SKILL.md) for future drift checks. Do not schedule maintenance, publish, or open a PR unless requested or already authorized.

Source and adaptation details: [provenance](references/provenance.md). Read only when auditing or updating this skill.
