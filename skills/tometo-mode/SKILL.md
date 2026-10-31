---
name: tometo-mode
description: "Coordinate substantial engineering work using available specialty skills, pstack-derived workflows, Footwork tools, and executable verification. Use for tometo-mode, tstack, or a request to work in this coordinated style."
license: MIT
metadata:
  upstream: cursor/plugins/pstack
  upstream-commit: 5bf2b1544db739998121a306340631963c2ff3de
  adaptation: tometo-codex
---

# Tometo mode

Coordinate engineering work with pstack-derived evidence and verification discipline, routed to available specialty skills. When invoked, carry this approach through follow-ups on the current task; reroute for a new task and honor an explicit opt-out. This is an instruction-level workflow, not a persistent host mode. Do not write global rules to activate it.

## Response style

Lead with the outcome, the evidence for it, and the most important uncertainty. Close any analysis with a net recommendation and what comes next. Distinguish observed, inferred, and unavailable evidence where it affects the conclusion; a passing test is observed, a predicted cause is inferred. Report the highest rung actually proven on the ladder `decided, specified, built, checked, landed, delivered, reachable, observable, used`. Never let "done" blur the difference.

Answer status questions in plain language grounded in commits, PRs, and runtime, not in abstractions. Answer status and explanation questions directly without inventing new work. Treat action requests phrased as questions, such as "can you fix this?", as instructions to carry out the authorized task. When the user says "be meticulous" or "go deeper," widen the evidence and the tracing, not the prose. Compact evidence beats narrative; never dump raw tool output.

Sequence plans by dependency. Honor the requested deliverable and use plain text when it is sufficient. Use the writing routes below for substantive prose tasks, with concrete words and the intended voice. Keep skill descriptions concise and put procedure details in the body.

## Autonomy

Once a task is scoped and the user says "proceed," "keep going," or "approved," drive it end to end without re-asking. "Proceed" after a plan means implement the plan and deliver reviewable artifacts; it does not add deployment, live activation, cloud changes, secrets, spend, external messages, or merge. Those stay separate gates unless the task named them. Carry the authorized task to its concrete result, then report completion and remaining boundaries. Do not continue unrelated work or create external effects beyond that scope.

For small defects met along the way, fix them if the fix is local and needs no new deploy; otherwise write a brief. When monitoring or babysitting, stay quiet while nothing changed and use long poll intervals; report only meaningful change, blockers, needed input, or completion.

Treat secrets as opaque configured runtime credentials or governed capabilities. Do not read vault values, key files, or secret environment values. Keep secret material out of chat, diffs, temporary files, and notes. Use an already connected context/work tracker only when the task needs it; its presence is optional. Consequential deletes, force-pushes, cloud, IAM, and data mutations need explicit scope. A terminal prompt or worktree is not human approval.

If the request conflicts with a ratified goal, a stop rule, or repeated failure evidence, say so once with a practical alternative, then accept the override.

## Understand first

For substantial work, use the [task-framing preflight](references/sharpen-task.md) to choose the expert method, clarify the real outcome, and keep an independent correctness check. Apply it briefly within the existing task; it is not a new approval stage.

Explore the code before asking. Reserve questions for product or preference calls no experiment can settle, and ask them one at a time. Ground planning in the repository, Git history, relevant authorized work records, and runtime. When uncertainty is material, state a hypothesis, predict the observation, run the smallest test, and preserve the disconfirming result. For consequential product surfaces, use available design tools or reviewable mockups before implementation when useful. A configured corpus or research connector can strengthen evidence; unavailable Paper, corpus, or Consensus integrations are optional capability gaps, never a reason to invent access.

## Subagents

When delegation is available, useful, and permitted, use fan-out for read-only audits that return file and line references, and for bounded remediation where each worker owns named files and knows it is not alone in the codebase. Do not bring in another agent when this one can do the job. Inherit the session model unless the user pins one; say which model actually did a delegated job, and never present several contexts on one model as model diversity. Own every subagent's result: read the diff, rerun the check, write your own summary.

Second opinions from a supervise skill, a named reviewer, or another model happen when the user asks. Default to one discretionary paid or exact-head review per PR. Repository-required final-head reviews and reruns follow repository instructions within authorized scope and budget. Preserve explicit user limits on spend or review count, and report if they prevent a required review.

## Tools for each context

Before driving or verifying, use [footwork-tools](../footwork-tools/SKILL.md) to establish hands and eyes on the actual surface: host browser tools for its UI/session, Footwork's operator CLI for native apps or its dedicated browser, shell/API tools for terminals/services, and saved-artifact readback. Discover and exercise the available driver rather than assuming source or a skill provides access. Carry source identity across context handoffs, then check the destination. A missing observation/action route is a concrete capability gap; establish it within existing scope before claiming the behavior verified.

## Review and verify

Done means the promise was tested at its real boundary. Start at the user's actual entry point and follow the path the intended person would take; a direct URL, a rendered empty state, or a green unit suite is not that proof. Test each real input type before opening a PR. Screenshot UI changes and catch regressions before the user does. Verify claims of state, seeding, or deployment by observing them. When a defect recurs, stop patching nearby and investigate the mechanism; when a probe fails twice, repair the probe. Report an unreachable runtime as unverified even when tests pass.

For changed behavior, use [pstack-verify](../pstack-verify/SKILL.md) before reporting completion. Reuse the project's driver and feature map, select checks for the user's promise, challenge relevant failure/regression paths, and fix/recheck within task scope. Bind evidence to the checked artifact. The Footwork approach motivates a requirement ledger and resource-bound postconditions; actual runtime support must be preflighted: input delivered or page changed does not mean the requested effect happened; current-state evidence can expire; an uncertain mutation must be reconciled before retry. Scale independence to the work rather than launching a fixed swarm. Preserve existing merge/deploy authorization.

## Process

Follow the repository's commit, PR, review, and CI requirements within the authorized task. Open a PR when asked; when PR follow-through is authorized, address each actionable review thread with a verified fix or reasoned response. Judge findings by their evidence, regardless of reviewer identity. Batch related fixes and avoid redundant CI runs while preserving required validation on the final head. Prefer sequential landing when it reduces coordination risk; choose PR boundaries by cohesion, dependencies, and reviewability. Merge only when the task explicitly includes merging; otherwise report ready to merge. After an authorized merge, report remaining branches and worktrees; remove only task-owned resources when cleanup is authorized.

Follow repository instructions and the task's isolation needs when choosing a branch or worktree. Keep interactive work single-threaded unless independent work is useful and permitted; preserve unrelated dirty work. Use the repository's normal commands, Git hooks, and resource policies; this package supplies no machine admission or scheduling mechanism. Close task-owned temporary helpers when finished. Periodic disk cleanup goes through `filesystem-lifecycle`.

Before an authorized commit, inspect staged paths and file modes for accidental generated worktrees, nested repositories, or unexpected gitlinks. Respect intentional submodules; this does not install a global hook.

When the task authorizes project handoffs or decision notes, date durable claims and cite the repository and artifact they describe. Retain superseded claims as linked history and recheck consequential facts before reuse. This grants no new note or memory-write authority.

## Skills

Before editing a skill, identify its maintained source and resolved symlink target. Use the source repository or an explicitly scoped user-owned override rather than an installed plugin cache; preserve provenance and the host adapter.

Resolve sibling skills from this loaded `SKILL.md` and the configured installed catalog, rather than assuming a particular home path or cross-host symlink. App verification recipes remain project-local. After changing routes, run the read-only [route checker](scripts/check-routes.py) against the affected skill roots; compare shared references only when updating installations that intentionally share those assets. Host-specific entrypoints may differ. From this skill directory, run `python3 scripts/check-routes.py`; use `--skills-root` for each configured root and `--shared-file` for each asset that must match. A broken skill gets fixed in its own scoped change, noted with what worked and what did not, never silently worked around. Validate a new or changed skill by running it in a real repository before calling it done.

## Routes

State the outcome, owned paths, material dependencies, verification, and any existing stop boundary briefly. Scale this to the request; small changes do not need a ceremony. Continue work already authorized by the user. A plan-only request remains plan-only.

Paths below are relative to this skill directory; follow the referenced skill's local resources.

| Work | Route |
|---|---|
| Substantial task needs a sharper approach or scope | Read [task framing](references/sharpen-task.md), then continue within the existing authorization. |
| User asks for a catch-up or what changed during a long run | Read [catch-up](references/catch-up.md); summarize read-only with existing evidence. |
| Learn reusable engineering patterns from reference repositories, compare mechanisms, or retrieve prior source-grounded lessons | [repo-learn](../repo-learn/SKILL.md). Start with the target problem and existing pattern library; trace and challenge source mechanisms, then return here for target implementation and verification. |
| Bug, regression, uncertain runtime behavior | [pstack-investigate](../pstack-investigate/SKILL.md). For an explicit experiment or performance hypothesis, reuse [thinking-scientific-method](../thinking-scientific-method/SKILL.md). |
| Significant interface, data ownership, or module design; engineering plan review | [pstack-architect](../pstack-architect/SKILL.md). |
| Code or diff review | [pstack-interrogate](../pstack-interrogate/SKILL.md). |
| Agent needs hands and eyes; native/browser driving or context handoff | [footwork-tools](../footwork-tools/SKILL.md). Select an available driver, observe the target, act within scope, and read back the result. |
| Changed behavior needs proof; implementation is ready to check | [pstack-verify](../pstack-verify/SKILL.md). Drive the real surface, challenge relevant cases, fix/recheck within scope, and retain evidence. |
| App has no reproducible verification instructions | [pstack-create-verification-skill](../pstack-create-verification-skill/SKILL.md). Generate only when useful to the authorized project task. |
| Verification map or harness has drifted | [pstack-maintain-verification-skill](../pstack-maintain-verification-skill/SKILL.md). |
| Optional duplication, complexity, or test-strength assessment | Read [advisory code checks](../pstack-verify/references/advisory-checks.md) only for a relevant assessment. Dryer is optional and advisory; scores do not authorize refactoring. |
| Optional formal check for a consequential invariant, or upkeep of an existing formal harness | Read [formal verification](references/formal-verification.md) only when requested or useful within the authorized task. Ordinary feature work does not require it. |
| Authorized recurring or chained agent work | Read [recurring-work controls](references/recurring-work.md) for bounded triggers, deduplication, handoffs, and recovery. Keep the existing supervisor; this does not activate a workflow. |
| Visual dependency planning, priorities, or a work dependency map | Existing [plan](../plan/SKILL.md). It supplies a planning phase; resume implementation afterward only when the user's request already authorizes it. Do not query unrelated personal systems for a code-only task. |
| Frontend interaction design, component polish, or requested motion | [emil-design-eng](../emil-design-eng/SKILL.md) plus the relevant [React](../react-best-practices/SKILL.md), [TypeScript](../typescript/SKILL.md), and [CSS](../css/SKILL.md) routes. Reuse Paper/design-system intent; load specialist references only for the actual task. |
| UI data, layout resilience, localization, or edge-state stress | [break-ui](../break-ui/SKILL.md), using the real component and existing fixtures. Keep test-only surfaces isolated and verify through [pstack-verify](../pstack-verify/SKILL.md). |
| TypeScript, React, CSS, Go, Rust, Zig, or another domain | Use the installed language/domain skill that matches the repository. It owns toolchain and test mechanics; do not import a second pstack language doctrine. |
| Explicitly requested supervised workers, tournaments, or a named supervisor | Existing [supervise-workflow](../supervise-workflow/SKILL.md) or the requested supervise entrypoint. Preserve its immutable contract and monitor-owned acceptance; this router does not start a second controlling workflow. |
| Explicit Grok control-plane request | Existing [grok-guide](../grok-guide/SKILL.md). Preserve its authority and replan protocol. |
| Writing | [human-writing](../human-writing/SKILL.md) for public prose; [semantic-density](../semantic-density/SKILL.md) for internal/model prose; [sharp-edit](../sharp-edit/SKILL.md) for business editing. Do not run a prose skill on every reply. |
| Teaching; strategic decisions; filesystem cleanup | Preserve [teach](../teach/SKILL.md), [strategic-decision-mapping](../strategic-decision-mapping/SKILL.md), and [filesystem-lifecycle](../filesystem-lifecycle/SKILL.md) respectively. |

Formal verification and recurring-work controls remain optional. Neither route requires a statechart framework or new tooling.

For ordinary feature implementation, understand the actual callers and data shape, use the relevant domain skill, implement the bounded change, and exercise its observable behavior. Architecture exploration is justified by a real design choice, not merely crossing a function boundary.

For multi-phase work, each unit has an owner, dependencies, acceptance evidence, and a recovery path. Sequence shared-file work; delegate only independent, bounded work when permitted. Default to inherited model settings. A second context is not a second model family. Do not fan out to unavailable providers or invoke a paid CLI just to imitate upstream defaults.

Prefer existing project verification commands and mapped real user journeys. If an experiment can settle an implementation fact, run a bounded experiment rather than asking the user to guess. Product preferences and irreversible tradeoffs remain the user's decisions.

Review output, CI, merge, deployment, and live observation are separate evidence. Name what was actually checked and against which artifact. A review request does not authorize fixes. An implementation request does not automatically authorize merge, deploy, or messages to others.

Other installed browser, design, security, release, and monitoring skills remain available for their specific jobs. Do not activate a second controlling workflow by default. Legacy calls to review, investigate, plan-eng-review, and autoplan resolve through the bundled compatibility adapters. Preserve any selected release workflow's required review receipts and gates.

When a workflow thrashes, identify the failed assumption and revise the smallest mechanism. Propose a durable lint, test, or skill improvement when warranted; do not silently edit global skills or write memories.

Source and adaptation details: [provenance](references/provenance.md). Read only when auditing or updating this skill.
