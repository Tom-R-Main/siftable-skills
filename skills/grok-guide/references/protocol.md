# Grok Guide Authority Protocol

Read this reference for every `$grok-guide` lifecycle.

## Authority table

| Actor | Owns | May not do |
|---|---|---|
| Human | Objective, hard constraints, sensitive-data boundary, release | Be bypassed at a blocking question or release gate |
| Grok | Framing, non-goals, governing decisions, task graph, replan, audit | Read the repository directly, edit files, override human constraints |
| Codex coordinator | Evidence, feasibility, dispatch, integration, verification | Silently alter controlling plan fields or call work complete without audit |
| Codex worker | One bounded task | Expand scope, modify unlisted paths, redesign the task graph |

Human safety policy outranks every plan. Codex may challenge Grok only with concrete evidence. A challenge becomes a structured replan request, not an improvised replacement plan.

## Lifecycle state machine

```text
human objective
  -> fact-only exploration
  -> local packet preview
  -> disclosure and credential gates
  -> Grok plan
     -> needs_human: STOP -> human answer -> replan
     -> needs_evidence: STOP -> new facts -> replan
     -> ready: feasibility validation -> bounded execution
  -> contradiction? STOP affected work -> replan
  -> Codex verification
  -> Grok audit
     -> fail: replan if ceiling remains, otherwise human
     -> needs_human: STOP -> human
     -> pass: human release gate
```

Only a `ready` plan has dispatchable tasks. Only an audit `pass` reaches the release gate. Only the human closes the task.

## Blocking-question semantics

Treat readiness as protocol state, not prose:

- `needs_human` means a policy, product, risk, or preference decision belongs to the human. Return no tasks. Ask exactly the structured questions.
- `needs_evidence` means repository facts are insufficient. Return no tasks. Gather only evidence that can answer the structured questions.
- `ready` means there are no blocking questions and every task is dispatchable.

Bind each resolution to the original question ID. Do not fold unrelated guidance into a resolution. A resolution produces a versioned replan, never an in-place mutation.

## Feasibility gate

Before dispatch, Codex checks the plan without replacing it:

1. Every governing decision cites known evidence.
2. Every dependency exists and tasks are topologically ordered.
3. Every allowed path is safe, repository-relative, and actually in scope.
4. Acceptance criteria are observable.
5. Verification commands are available and proportionate.
6. No task violates a human constraint or non-goal.

If a check fails because the plan is invalid or infeasible, submit evidence to `replan`. If it fails because the request packet is malformed or the runner has an operational failure, fail closed before disclosure or dispatch.

## Contradiction packet

A worker contradiction must state:

- stable contradiction ID;
- claim that conflicts with the current plan;
- supporting evidence IDs;
- impact on objective, decision, dependency, or acceptance criterion;
- blocked task IDs;
- decision Grok must make.

Pause only affected tasks unless their dependents make broader work unsafe. Preserve completed evidence and unaffected human constraints. Grok may change only what the contradiction requires.

Replan versions are monotonic: plan 1, replan 2, replan 3. Two replans is the hard ceiling. Any remaining contradiction after plan version 3 goes to the human.

## Worker-result contract

For each task, capture:

- status: `completed`, `blocked`, or `failed`;
- concise summary;
- evidence IDs used or produced;
- exact files changed;
- command-level test results;
- contradictions;
- residual risks.

Do not mark a task completed merely because code was written. Do not omit failed or not-run verification. A changed path outside `allowedPaths` invalidates the result and requires replan or human intervention.

## Audit contract

The audit evaluates each deterministic checklist item:

- the original objective;
- every human constraint;
- each non-goal;
- every governing decision;
- every task acceptance criterion;
- every stop condition.

`pass` requires every item met, no deviations, no unresolved risks, and no questions. `fail` requires an unmet criterion. `needs_human` requires uncertainty or a question the human must resolve. Passing tests alone never imply `pass`.

## Data and credential boundary

- Send only validated structured JSON in a disposable mode-0700 packet directory.
- Cap evidence at 50 facts, 4 KiB per excerpt, and 256 KiB per packet.
- Reject hidden, traversal, credential, generated, or unrelated paths.
- Reject high-confidence secrets; redact lower-confidence secret-shaped values locally.
- Preview proprietary evidence and obtain packet-specific approval.
- Use only opaque configured runtime credentials or governed scopes; never read vault values or key files.
- Require a compatible external harness that keeps credentials out of prompts, arguments, output, and persisted evidence.
- Interpret `local_grok_cli_remote_inference` correctly: local CLI routing, remote xAI inference.
- Report disclosed bytes and packet hash. Do not retain prompts, excerpts, plans, or results as logs.

No local dollar ceiling is currently assumed. Report runner cost metadata when present and honor any budget the human sets for the task. Do not infer that provider account limits or auto-top-up state remain unchanged.

## Operational failures

Treat authentication, ZDR preflight, CLI version, process spawn/exit, timeout, output limit, credential reflection, envelope mismatch, schema mismatch, audit-checklist mismatch, disclosure-budget exhaustion, and cleanup uncertainty as operational failures.

An operational failure does not become a plan, replan, or audit verdict. Report the failure code and safe retry path. Never weaken the schema or switch authentication routes silently.

## Completion report

At the human gate, report:

```text
objective
final plan version and replan count
audit verdict
tasks and changed files
verification results
deviations and unresolved risks
packet hash and cumulative disclosed bytes
authentication source and remote-inference route
known cost metadata
human decision required
```
