---
name: supervise-workflow
description: Compile and supervise trusted coding workflows from Codex, Claude Code, Cursor, or Kimi, using pinned Claude Fable 5 or Opus 5 planning/review and isolated Codex Sol or Kimi K3 implementation. Use for bounded implementation, reviewing an existing committed diff, fresh-context review, reference-driven UI, or work that needs worktree isolation, monitor-run verification, remediation, and accept/remediate/escalate judgment without hand-patching worker output.
---

# Supervise Workflow

Act as the trusted monitor. Treat every launched model as an untrusted worker.
Keep acceptance, policy, verification, design grounding, and final judgment on the
monitor side. Never repair worker output yourself; remediate by resampling.

Resolve this skill directory from the loaded `SKILL.md`, then set:

```bash
SKILL_DIR="<skill-directory>"
ENGINE="${SUPERVISE_WORKFLOW_BIN:?Set an approved native supervision executable}"
ASSETS_DIR="${SUPERVISE_WORKFLOW_ASSETS:?Set its matching validated runtime assets}"
[[ "$ENGINE" = /* && -x "$ENGINE" && -d "$ASSETS_DIR" ]] || exit 1
```

This skill ships workflow instructions, reference policies/schemas/prompts, and a readable worker contract. It does not ship a native engine, provider executables, compiled asset manifest, or a complete engine asset directory. The files under `assets/` are reference-only; do not point `SUPERVISE_WORKFLOW_ASSETS` at them or invent hash guarantees. Require a user-configured native engine and its matching externally validated assets, inspect their version/integrity, and confirm every required command and policy against that release before proceeding. Never fetch/install a runtime or authenticate a provider automatically. Normal supervision commands must not invoke Node or a `.mjs` compatibility engine. Missing runtime leaves supervision unavailable; ordinary bounded work may continue only under its own task authorization.

## 1. Preflight and intake

Run doctor for only the workers the selected pattern needs, for example
`"$ENGINE" --assets-dir "$ASSETS_DIR" doctor --backend codex,claude` for Sol plus
Opus 5 or `"$ENGINE" --assets-dir "$ASSETS_DIR" doctor --backend codex,kimi,claude`
for the full UI path. Resolve
the current git root and collect a bounded
task contract: objective, acceptance criteria, include/exclude globs, deterministic
verify command, an optional read-only preflight command, an early checkpoint
command, generated-file policy, and whether visual verification is required. Do
not launch an unjudgeable task. When `doctor` reports a missing worker, report the capability gap. Installation, authentication, provider changes, and paid probes require existing user authorization; do not automatically execute its `fixes` suggestions. Rerun doctor after authorized provisioning.

Before a long or paid Sol run, or after a Codex CLI/model upgrade, exercise the
exact model and structured-output surface (this spends a small model call):

```bash
"$ENGINE" --assets-dir "$ASSETS_DIR" doctor --backend codex --probe --probe-model gpt-5.6-sol
```

Provider/schema failures make doctor fail. PostHog or model-cache stderr is kept
as diagnostic evidence and is not itself a failure when the probe succeeds.

Before the first paid Opus run, or after a Claude CLI/model upgrade, exercise the
exact planner/reviewer surface with a tiny structured-output call:

```bash
claude -p --safe-mode --model claude-opus-5 --effort xhigh \
  --permission-mode plan --tools Read,Grep,Glob --no-session-persistence \
  --output-format json \
  --json-schema '{"type":"object","properties":{"ok":{"const":true}},"required":["ok"],"additionalProperties":false}' \
  'Return the required JSON with ok=true. Do not use tools.'
```

For a Fable supervisor profile, run the same probe with
`--model claude-fable-5 --effort max`. A successful generic Claude doctor does
not prove that the account can invoke Fable. Do not silently fall back to Opus;
surface model availability or provider-reported fallback to the user.

Read [runtime.md](assets/policies/runtime.md) before the first run on a
machine or when changing worker permissions.

Use the smallest pattern that addresses the failure mode:

- `single-worker`: one bounded implementation.
- `review-existing`: one fresh read-only review of committed `HEAD` against an
  explicit `base_ref`, with no implementation worker.
- `fresh-context-review`: implementation plus an independent read-only reviewer;
  use the selected Fable or Opus profile for medium-risk work.
- `planned-fresh-context-review`: a fresh selected-profile plan, Codex Sol
  implementation, and a separate fresh selected-profile review; use for large,
  ambiguous, or high-blast-radius tasks.
- `candidate-tournament` (compatible alias: `two-candidate-tournament`): two to
  four isolated candidates plus fresh reviews; use only when genuinely different approaches are valuable, and name distinct
  `candidate_directions` in the spec.

Read [patterns.md](assets/policies/patterns.md) when choosing between them.
For `review-existing`, require a clean source checkout and an explicit `base_ref`.
The engine creates a detached worktree at `HEAD`, computes the merge-base, and
reviews only that committed diff. Commit or otherwise isolate intended changes
before launch; the pattern refuses dirty source state rather than omitting it.

## 2. Ground design work on the trusted side

For non-obvious design decisions, use [searching-design-corpus](../searching-design-corpus/SKILL.md) when a corpus backend is already configured. Never let a worker call the corpus or access credentials. Use only opaque configured runtime credentials or governed scopes; no vault-value reads. Missing corpus is a documented limitation, not permission to start a database or install an embedding provider. Write only
sanitized passages, source names, page numbers, and copied reference assets to a
temporary evidence file. Never include credentials or vault commands.

When the corpus and repository contain no useful visual precedent and the UI is
genuinely starting from a blank page, read and invoke
[generating-design-references](../generating-design-references/SKILL.md)
on the trusted-monitor side. Use it sparingly:

1. Search the UI corpus first and record why its hits do not supply a usable
   precedent.
2. Generate one concrete visual anchor through an available image tool or a user-configured generator.
3. Open and inspect the returned PNG yourself; generation without viewing does
   not count as evidence.
4. Critique what to use and reject against the corpus, product context, and task
   contract. Record that critique in the sanitized design-evidence file.
5. Put the PNG path in `design.generated_reference_images`. Keep user-supplied
   screenshots or Figma exports in `design.reference_images`; those may be fidelity
   targets, while generated images are never targets or deliverables.

The engine copies both classes of image into trusted private inputs. Each writer
receives a disposable copy; the monitor hashes and rechecks the trusted originals
after every write round. The Claude planner must
view and critique every generated scaffold before its plan can unblock the writer.
Workers may inspect supplied images but may not run the generator themselves.

Use a repository overlay for stable local traps only when the user-configured runtime supports it. Inspect its effective policy and declare generated-file inclusions explicitly. This portable skill contains no private repository overlay; do not assume the external engine has the same defaults as a historical local build.

## 3. Compile and inspect the workflow

Write a task spec matching [spec-schema.json](assets/schemas/spec-schema.json)
to a private temporary run directory. Select `codex` for general implementation.
Select `kimi` only for reference-driven UI implementation with design evidence
and visual verification. Set `review_backend` to `claude` for Claude review. The
default profile pins planner and reviewer to fresh `claude-opus-5` sessions at
`xhigh` effort. The first-class Fable profile instead pins the applicable roles
to exact `claude-fable-5` sessions at `max` effort:

- Fable reviewer only: `fresh-context-review` or `review-existing` with
  `review_model: "claude-fable-5"` and `review_effort: "max"`.
- Fable planner and reviewer: `planned-fresh-context-review` with both model
  fields set to `claude-fable-5` and both effort fields set to `max`.
- Fable planner with Opus review: use only when planning is the dominant hard
  problem and deliberate cross-model review is worth more than a second Fable
  call.

`$supervise-fable` requires at least one Fable node; `$supervise-opus` keeps the
Opus defaults. In either profile, Claude nodes stay read-only and the host stays
the final judge. The compiler validates the complete spec schema, rejects unknown
keys, rejects obvious provider/model mismatches, and rejects planner, reviewer,
or tournament options on patterns where they would be ignored.

Use task-size tiers rather than the maximum ceremony every time:

- S: `single-worker` for a low-risk change of roughly three files / 100 lines or
  less whose acceptance is fully encoded by deterministic verification. Do not
  use this tier for an explicitly requested Fable run because it has no Fable
  role; use a fresh Fable review or propose the ordinary workflow instead.
- Existing diff: `review-existing` when the user asks only for an independent
  review. Omit `backend`, set an explicit `base_ref`, and pin the reviewer from
  the selected Fable or Opus profile.
- M: `fresh-context-review` with Sol writing and the selected supervisor profile
  reviewing; omit a separate planner.
- L: `planned-fresh-context-review` for multi-file, ambiguous, or high-blast-radius
  work, with the selected profile planning and reviewing in separate sessions.

Compile and validate:

```bash
"$ENGINE" --assets-dir "$ASSETS_DIR" compile --spec "$RUN_DIR/spec.json" --out "$RUN_DIR/plan.json"
"$ENGINE" --assets-dir "$ASSETS_DIR" validate --plan "$RUN_DIR/plan.json"
```

Inspect the emitted nodes, worktree count, concurrency, models, efforts, timeouts, and
verification commands before launch. State material assumptions. For reference
design work, prefer one Kimi writer followed by one fresh review from the selected
Fable or Opus profile. Cap deliberate execution concurrency at two even when
exploring three or four named directions.
For marketing mocks, prefer two directions unless a third direction is materially
different enough to justify its wall time. A tournament is a divergence and
selection tool, not three full ship pipelines.

The compiler assigns stable `AC1`, `AC2`, ... identifiers and derives per-run
planner/reviewer schemas whose enums require those exact IDs. There is no fuzzy
acceptance matching. To reuse a monitor-validated Claude plan, set
`plan_artifact: {report_file, task_contract_sha256}` on a
`planned-fresh-context-review` spec. The engine revalidates the artifact against
the current scope, AC IDs, contract hash, and generated-scaffold critiques before
skipping the planner session.

For copy-locked marketing mocks, opt into `task.copy_policy` with a newline or
JSON-array `locked_copy_file`, `scan_globs`, and optional
`allowed_visible_copy_file` for shared navigation, language, footer, and legal
chrome. Numeric counters are treated as ornament by default; set
`allow_numeric_ornament: false` to disable that. Label other fictional terminal
or demo prose with `data-decorative` (or the configured `decorative_marker`)
before writers run. Locked strings must remain present; shared chrome may appear
but is not a product-copy requirement. The dependency-free scanner is not a
browser DOM and must be paired with human visual review.

Use real browser viewports such as `1440x900` and `390x844`. Never encode full
document height as a viewport; the compiler rejects numeric viewports above
4096x2400. Set `design.visual_verify_timeout_ms` only when the 90-second default
is insufficient, up to the 180-second hard maximum. Declare screenshot outputs
with `design.visual_artifact_globs`; the monitor copies those artifacts into the
evidence directory and removes all files created by visual verification from the
candidate worktree, including Chrome profiles and caches.

## 4. Run and consume evidence

```bash
"$ENGINE" --assets-dir "$ASSETS_DIR" run --plan "$RUN_DIR/plan.json" --run-dir "$RUN_DIR"
```

The engine writes sanitized heartbeat/status lines to stderr and the final evidence
JSON to stdout. Redirect them separately when benchmarking. Do not pipe a long run
through `tail`; doing so hides progress until the process exits.

For a durable background run, redirect first and tail the file, not the process:

```bash
nohup "$ENGINE" --assets-dir "$ASSETS_DIR" run --plan "$RUN_DIR/plan.json" --run-dir "$RUN_DIR" \
  > "$RUN_DIR/engine-stdout.json" 2> "$RUN_DIR/engine-stderr.log" < /dev/null &
echo $! > "$RUN_DIR/engine.pid"
tail -f "$RUN_DIR/engine-stderr.log"
```

Use `kill -0 "$(cat "$RUN_DIR/engine.pid")"` to distinguish a quiet live run
from a dead launcher.

The engine creates one isolated worktree per writer, runs the workflow DAG,
captures provider events, sanitizes digests, runs verification independently
before review, and writes `evidence.json`. It never accepts or merges code. Every
role cites the immutable task-contract hash. The advisory plan may not change the
contract; writers must report plan deviations. Reviewers receive a sanitized diff,
changed-path set, and monitor-generated verification packet instead of trusting
the writer's claim that tests passed.

Evidence separates `process_ok`, `integrity_ok`, and `report_ok`. Once an
in-scope candidate artifact exists and writer integrity is green, its fresh review
runs even when process/report, deterministic verify, visual verify, or copy policy
is red. Those red gates remain in the reviewer packet and still block final
acceptance. Integrity, scope, symlink, and policy failures always block review.

For tournaments, the engine continuously writes `presentation.json` and
`presentation.md`, listing each direction, HTML paths, worker screenshots,
monitor-copied visual artifacts, gate status, and review result. The run is
successful when at least two safe candidates are `ready_for_selection`, even if
none is ship-ready. Open every presentation-ready candidate as soon as it lands;
do not wait for green visual/copy evidence or for another writer's soft timeout.
While a writer is still running, the engine polls changed files and announces an
explicitly untrusted live preview as soon as both HTML and an image exist. Use it
for early visual comparison, never for acceptance; `presentation_ready` still
requires completed writer integrity and in-scope monitor evidence.
When available in the host, use `/design-consultation`, `/design-review`, or
`/plan-design-review` as the human-facing comparison layer after this engine has
provided isolation and evidence.

For Kimi implementation nodes, `closure_reserve_ms` is enforced. The engine stops
the implementation process at the soft budget, continues the same worktree and
session with a verification-and-report-only prompt for the reserve, then applies
the normal hard timeout. Evidence records both phases.

When a Kimi result needs remediation, Codex Sol takes over the existing worktree
in a fresh sandboxed session and preserves correct work rather than restarting.
Codex-to-Codex remediation is also a fresh sample; the harness does not depend on
unproven resume-time sandbox inheritance. Do not add Kimi as an automatic
fourth role. Use a Kimi-vs-Kimi tournament only when the user explicitly values
two materially different visual directions.

Read `evidence.json`, worker reports, scope results, relevant diffs, and visual
artifacts. Do not read raw JSONL transcripts wholesale. Independently inspect the
highest-risk changed files and every required screenshot.

## 5. Judge and remediate

Apply [judgment.md](assets/policies/judgment.md). Accept only when the code
is correct, scope and independent verification pass, no P0/P1 exists, and
confidence is at least 0.8.

For repairable findings, write a findings-only prompt and run:

```bash
"$ENGINE" --assets-dir "$ASSETS_DIR" remediate \
  --run-dir "$RUN_DIR" \
  --workspace "<workspace-id>" \
  --findings "$RUN_DIR/findings-r2.md"
```

In a tournament, select the human-preferred direction before any remediation:

```bash
"$ENGINE" --assets-dir "$ASSETS_DIR" select --run-dir "$RUN_DIR" --workspace "<workspace-id>"
```

The engine rejects tournament remediation until selection is recorded. Do not
spend Sol rounds polishing losing directions.

If only monitor-owned verification failed—Chrome timeout, missing screenshot,
copy allowlist/chrome configuration, or another harness issue—fix that monitor
configuration and rerun evidence without a writer:

```bash
"$ENGINE" --assets-dir "$ASSETS_DIR" reverify --run-dir "$RUN_DIR" --workspace "<workspace-id>"
```

Never send a copy-policy or browser-infrastructure failure to Sol. Remediate only
code/design findings on the selected candidate.

Allow at most two remediation rounds. Escalate on worker dishonesty, unclear
visual judgment, scope/security violations, or exhausted remediation. Preserve
worktrees for autopsy or the user's merge flow; never merge or delete them without
authorization.

Escalate immediately when the immutable contract is ambiguous, the planner names
out-of-scope files or blocking questions, a worker changes a test/verification
script outside the declared scope, or reviewer and writer disagree about contract
meaning. A non-accept review is never judgment-ready merely because it returned
valid JSON.

`review-existing` has no writer to remediate. If its review returns findings,
apply them in the normal repository workflow and launch a new review against the
new committed `HEAD`; use `rerun-review` only to recover a failed reviewer
process against the unchanged diff.

After a successful writer remediation, the engine automatically re-runs that
workspace's blocked or stale review nodes. A workspace is judgment-ready only when
its writer integrity, required reviews, scope check, independent verification,
visual verification, and optional copy policy pass. Report-only shape defects do
not trigger writer remediation. If a review process alone failed, retry it without
resampling the writer:

```bash
"$ENGINE" --assets-dir "$ASSETS_DIR" rerun-review --run-dir "$RUN_DIR" --workspace "<workspace-id>"
```

In tournaments, one fully reviewed workspace may proceed even
when another candidate is abandoned, but it is not judgment-ready until explicitly
selected. Presentation and selection precede polish.

## 6. Report

Report task, pattern, workers, branches, rounds, findings by priority,
independent verification, visual evidence, disposition, worktrees, wall time,
tool/policy violations, and run directory. Do not expose raw events or secrets.
