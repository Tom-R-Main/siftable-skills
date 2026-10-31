---
name: pstack-investigate
description: "Reproduce a software defect, distinguish competing causes, and verify a bounded fix on the original surface. Also supports read-only runtime and code-history investigations."
license: MIT
metadata:
  upstream: cursor/plugins/pstack
  upstream-commit: 5bf2b1544db739998121a306340631963c2ff3de
  adaptation: tometo-codex
---

# Investigate

Choose diagnosis-only or fix mode from the user's request. "Why is this broken?" does not by itself require editing. If fixing is already authorized, continue through the verified fix without another permission checkpoint.

1. Identify the actual user-visible failure, affected artifact, relevant version, and the smallest reachable reproduction. Inspect the existing run/test harness before inventing one. Use a project verification skill when present. Preserve failing output.
2. Trace the real path from input through ownership/state changes to the symptom. Inspect callers and boundaries, not just the function mentioned in the report. For a regression or rationale question, use scoped git history and relevant linked records; distinguish documented intent from inference. A shallow clone or unavailable record limits historical conclusions.
3. Form competing explanations and run the cheapest observation that distinguishes them. Add temporary instrumentation or vary one factor when needed. Use [thinking-scientific-method](../thinking-scientific-method/SKILL.md) for substantial experiment design, without treating its illustrative production experiments as authorization to deploy.
4. In fix mode, change the smallest mechanism supported by the evidence. Read the applicable language skill. Use [pstack-architect](../pstack-architect/SKILL.md) only if resolving ownership or interface design is necessary. Undo only your own disproven changes; preserve others' work.
5. Repeat the original reproduction against the changed artifact and exercise relevant failure paths. When a regression test adds durable protection, run it before the fix at a boundary that reaches the actual bug pattern; if added afterward, check it against the pre-fix artifact when practical. State what the chosen boundary catches and misses. If no affordable boundary reaches the bug, report the gap rather than adding a shallow test as proof. Run repository-required checks. Report an unreachable runtime as unverified, even if unit tests pass.

If an authorized local experiment forces a failure by changing code or a fixture, diff against the captured pre-experiment state to confirm the intended mutation landed before trusting the result. Confirm the failure matches the user's symptom, then restore only the experiment's changes and recheck. A forced failure demonstrates the probe's sensitivity, not that the original defect was reproduced.

Do not force a reproduction by mutating production, bypassing authorization, or expanding the target environment. When access is unavailable, finish the source investigation and name the exact missing evidence. A blocked integration check is not a reason to invent a root cause.

Deliver the cause and its evidence, the change if any, failing/passing observations, and remaining verification limits. Do not open a PR, send a message, or start ongoing monitoring unless that action is authorized by the task.

If finding the deciding fact required a deep investigation, propose the cheapest ongoing diagnostic signal that would have exposed it immediately. Implement it only within authorized scope; a proposal does not authorize deployment or monitoring.

Source and adaptation details: [provenance](references/provenance.md). Read only when auditing or updating this skill.
