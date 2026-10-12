---
name: grok-guide
description: Use Grok 4.5 as an explicit strategic control plane above Codex for plan, replan, and completion-audit lifecycles. Use only when the user explicitly invokes $grok-guide or directly asks to use Grok as the guide, control plane, technical lead, or controlling planner. Do not trigger for ordinary planning, architecture, reviews, fuzzy tasks, or generic requests to consult another model.
---

# Grok Guide

Use a user-configured compatible Grok Guide executable to give Grok strategic authority while Codex retains safe execution authority. Set `GROK_GUIDE_BIN` to an absolute trusted executable, resolve `scripts/run-guide.sh` from this loaded skill, and run its `doctor`. The harness, provider, schemas/validator implementation, account, and inference service are not bundled. Inspect the installed harness version, request-validator support, disclosure/redaction policy, and configured credential route before sending evidence. This is an explicit workflow, not a generic second-opinion prompt or automatic MCP installation.

Read `references/protocol.md` before starting a lifecycle. Read `references/request-contracts.md` when constructing or changing a request. Read `references/companion-skills.md` before combining this workflow with another local or gstack skill.

## Non-negotiable authority

- Keep the human in control of the objective, hard constraints, sensitive-data boundary, and release decision.
- Give Grok ownership of objective framing, non-goals, governing decisions, task graph, stop conditions, replanning, and completion audit.
- Give Codex ownership of fact gathering, feasibility checks, worker dispatch, edits, integration, and verification.
- Never let Codex silently replace Grok's objective, non-goals, governing decisions, or task graph.
- Never let Grok read a repository working directory or edit repository files.
- Treat `STOP` below literally. Do not continue the lifecycle past a gate.

## Workflow

### 0. Establish the control record

Restate the exact human objective, hard constraints, sensitive-data classification, and release authority. Track these lifecycle fields in the primary task context:

```text
phase: evidence | plan | execute | replan | audit | human_gate
plan_version: 0
replan_count: 0
packet_hash: unset
disclosed_bytes: 0
approved_paths: []
```

If a missing human decision could materially change the objective or disclosure boundary, ask it now and STOP.

### 1. Gather facts before recommendations

Inspect only the files needed to establish repository facts. When subagents are available and allowed, use up to three read-only explorers with fact-only briefs; keep requirements and decisions in the primary context. Explorer output must contain paths, tight line spans, claims, excerpts, unknowns, and test state—not architectural recommendations.

Build a `GuideEvidencePacket` from those facts. Reject hidden or sensitive paths, traversal, secret-bearing excerpts, untracked sensitive files, generated output, and unrelated dirty state. Use repository-relative POSIX paths only.

### 2. Enforce disclosure and credential gates

Preview the exact packet locally: file count, paths, byte count, redactions, excluded paths, and whether the evidence is synthetic/public or proprietary.

- For proprietary evidence, require the human to approve that exact disclosure before invoking Grok. Approval of the skill itself is not blanket approval of later packets.
- Credentials remain opaque configured runtime credentials or governed scopes. Never read vault values or key files, print secret environment values, or place credentials in arguments.
- Use only an already configured, user-approved authentication route. Do not log in, install a provider, or initiate browser authentication automatically.
- Do not call the xAI API directly, use arbitrary prompts, pass a repository `cwd`, or install/register another bridge.

If exact disclosure approval is absent or the configured credential route is unavailable, STOP with the local preview and the missing authority or capability.

### 3. Ask Grok for the controlling plan

Validate the request against `grok-guide.request.v2`, then invoke:

```bash
"$SKILL_DIR/scripts/run-guide.sh" run /absolute/path/to/request.json
```

The external runtime must validate the request and use its opaque configured authentication; the wrapper does not select credentials. Capture the returned plan and operational metadata in the primary task context. Do not create Codex's implementation decomposition before a valid Grok plan exists.

### 4. Honor readiness

- `ready`: validate evidence references, task dependencies, allowed paths, acceptance criteria, verification, and feasibility; then proceed.
- `needs_human`: present only the structured human blocking questions and STOP. Bind answers to question IDs in a `human_resolution` replan request.
- `needs_evidence`: gather only the requested facts and STOP implementation. Bind new evidence IDs to question IDs in an `evidence_resolution` replan request.

Do not answer a human policy question on the user's behalf. Do not dispatch tasks from a blocked plan.

### 5. Execute the approved graph

Dispatch bounded workers from Grok's `workerBrief`, `dependsOn`, `allowedPaths`, `acceptanceCriteria`, and `verification`. Codex may choose execution mechanics within each task but must preserve the controlling fields.

Before accepting a worker result, verify:

- every changed file is in that task's `allowedPaths`;
- dependencies completed first;
- acceptance criteria have concrete evidence;
- test results are recorded honestly;
- contradictions and new risks are explicit.

Use parallel read-only workers freely when allowed. Serialize writers unless their worktrees and allowed paths are disjoint.

### 6. Replan contradictions; never improvise around them

Create a structured contradiction when evidence invalidates an assumption, a task cannot meet acceptance criteria, dependencies change, a non-goal would be violated, or an architectural decision must change. Stop affected work and submit `worker_contradiction` to `replan`.

Increment `replan_count` only after a valid new plan. Maximum: two replans. After two unsuccessful replans, STOP for human direction. Never disguise a third replan as a fresh plan.

### 7. Require Grok audit after verification

After all tasks have worker results and Codex verification has run, build an `audit` request. A passing test suite is evidence, not completion. Grok must audit every deterministic criterion against the objective, constraints, non-goals, governing decisions, acceptance criteria, and stop conditions.

- `pass`: report the audit and proceed to the human release gate.
- `fail`: route the concrete unmet criterion through replan if the ceiling permits; otherwise STOP for the human.
- `needs_human`: present the unresolved question and STOP.

Never upgrade `fail` or `needs_human` to success locally.

### 8. End at the human release gate

Report the plan version, audit verdict, changed files, verification, deviations, unresolved risks, disclosed bytes, authentication route, known cost metadata, and packet hash. The human alone accepts or requests changes.

Persist only non-sensitive decisions, hashes, metrics, and operational gotchas when project instructions require Sift tracking. Never persist excerpts, prompts, results, or credentials.

## Failure behavior

Fail closed on invalid schemas, unsupported evidence IDs, task cycles, missing dependencies, unauthorized paths, credential reflection, ZDR-preflight failure, CLI timeout, output limits, temporary-directory failure, or uncertain cleanup. Preserve no model output as authoritative after an operational failure.

The current harness is a manual CLI pilot. Do not claim that an MCP tool is installed, that Grok controls the Codex runtime directly, or that the v2 evaluation has passed unless current evidence proves it.
