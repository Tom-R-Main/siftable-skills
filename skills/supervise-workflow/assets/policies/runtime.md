# Reference runtime boundaries

These policies describe the expected external engine contract. The engine and its matching manifest/worker assets are not shipped here. Preflight the actual release; this document alone supplies no isolation, hash, timeout, or permission guarantee.

The invoking Codex, Claude Code, Cursor, or Kimi Code session is the trusted monitor. The
engine is deterministic policy and orchestration. Claude Fable 5, Claude Opus 5,
Codex Sol, and Kimi K3 are untrusted workers.

Codex workers run through `codex exec` with `workspace-write` for implementation
or `read-only` for review. Kimi prompt mode has unattended permissions and no
equivalent filesystem sandbox; its containment is the dedicated worktree,
restricted skill directory, explicit scope, process-group timeout, disabled
telemetry/update/cron/background keep-alive, and independent diff verification.

Claude planner/reviewer nodes run as new Claude Code prompt-mode sessions with
`--safe-mode`, `--permission-mode plan`, and only `Read,Grep,Glob`. They receive
structured-output schemas and sanitized inputs. Compiled plans pin
`claude-opus-5` at `xhigh` effort by default. The first-class Fable profile pins
exact `claude-fable-5` at `max` effort for the applicable planner and/or reviewer
roles. An explicitly invoked Fable workflow must contain a Fable node; unavailable
or provider-reported fallback execution must not be described as Fable. Provision authentication separately through user-approved runtime configuration. Doctor may verify authentication status without exposing credentials. Set
`SUPERVISE_CLAUDE_BIN` only to a trusted executable.

`review-existing` creates a detached worktree at the repository's committed
`HEAD`, computes the merge-base against the required `base_ref`, and uses that
base for changed paths, scope, diff, and verification evidence. It refuses a
dirty source checkout so uncommitted work cannot be silently excluded. It has no
implementation node and cannot be remediated in place.

The portable engine invokes Codex through `codex exec` because Claude Code,
Cursor, Kimi, and shell hosts cannot access Codex app subagents. The executable
harness does not currently implement a native Codex-subagent adapter. A Codex host
may choose native delegation manually, but that bypasses the harness's automatic
event digest, timeout, report, and policy capture; do not describe it as equivalent
or use it when those guarantees are required.

Never give workers vault access, raw credentials, the active checkout, or broad
home-directory context. Permit design-corpus retrieval only in the trusted host.
Use only opaque configured runtime credentials or governed scopes; never fetch vault values. If retrieval credentials are unavailable, report the gap; pass only sanitized results to the worker.

Use the sibling `generating-design-references` workflow only from the trusted host
after corpus retrieval fails to provide a visual precedent. The monitor must view
and critique the PNG, then declare it under `design.generated_reference_images`.
The engine copies it into private inputs for read-only Claude planning and worker
inspection. Writers receive disposable copies and the trusted inputs are
hash-checked after each write round. Kimi loads only the `supervised-worker` skill;
the generator is not in its skills directory. Worker-side generator invocation
remains a policy violation.

Reviewer packets live in per-workspace disposable reviewer directories outside
the trusted writer-input manifest. This permits live tournament scheduling without
mistaking monitor-created evidence for writer tampering. The manifest is checked
around planner, writer, and reviewer execution.

Set `SUPERVISE_CODEX_BIN` or `SUPERVISE_KIMI_BIN` only to trusted executables when
the default binaries are not on `PATH`.

When Kimi is missing, report the missing capability. Do not install packages, authenticate, or enable a provider without explicit authorization. Rerun doctor after the user provisions a trusted CLI.
Prompt mode already uses unattended permissions; do not add `--yolo` or `--auto`.
The npm package currently declares Node 22.19 or newer; doctor reports a warning
when the host Node is older even if the already-installed binary still starts.

The engine emits bounded progress heartbeats on stderr without printing provider
thought text. Capture stdout for final evidence and stderr for live progress and
timing. Do not put `tail` downstream of the live engine process.

For durable execution, launch with `nohup`, redirect stdout to
`engine-stdout.json` and stderr to `engine-stderr.log`, save `$!` in `engine.pid`,
and then `tail -f` the stderr file. Tailing the file is safe; piping the live engine
through `tail` is not. Recover a failed review with `rerun-review --run-dir ...
--workspace ...`; report-only writer defects do not need remediation.

Node evidence exposes three gates: process health, integrity/policy health, and
report validity. Candidate review scheduling depends only on writer integrity and
an in-scope non-empty artifact; deterministic verify, visual, copy, process, and
report failures travel in the review packet rather than suppressing review.
Final judgment still requires an explicit tournament selection, all required
reviews, and green scope, deterministic verify, visual verify, and optional
copy-policy evidence.

Visual verification has an independent 90-second default timeout and a 180-second
configuration ceiling. Numeric viewport heights above 2400 are rejected because
document height is not browser viewport height. The monitor snapshots the
candidate before visual verification, copies declared artifacts to evidence, and
removes every newly created visual file from the worktree so Chrome profiles and
caches cannot become worker scope violations. Existing candidate files modified
by the visual command are reported as monitor mutations and fail the visual gate.

Tournament runs emit `presentation.json` and `presentation.md` throughout the
DAG. `ready_for_selection` is a successful presentation terminal condition, not
acceptance. `select` records the human winner and is mandatory before tournament
`remediate`; `reverify` reruns monitor evidence without spending a worker round.
During long writer calls, the scheduler polls changed files every two seconds and
publishes an untrusted live preview once changed HTML and an image coexist. This
allows early side-by-side viewing without pretending that writer integrity or
monitor verification has completed.

Kimi implementation time is split into an implementation phase and an enforced
`closure_reserve_ms`. If implementation reaches the soft boundary, the engine
terminates that process group and starts a pinned-session finalization phase that
may only verify, clean scope, and emit the report. It falls back to the
working-directory-scoped `--continue` only when the stream exposed no session id.
The reserve has its own hard kill; both phases are recorded in node metadata.

When the implementation stream exposes a Kimi session id, the reserve uses
`--session <id>` instead of relying on `--continue`; doctor requires that flag.
Kimi Code requires the non-interactive prompt as an argv value. The engine redacts
that value from persisted invocation metadata, but same-user process-list exposure
remains a Kimi CLI limitation.

Monitor verification runs worker-authored repository code. The harness uses a
non-login `zsh -f`, removes secret-like environment variables and shell/runtime
startup injection variables, SSH agent sockets, and cloud/cluster/Docker/GitHub
configuration channels, and sets `CI=true`; it is not an OS sandbox. Treat
Kimi-authored verification as residual arbitrary-code risk and use an external
container/sandbox for hostile or high-trust-boundary repositories.

Review diffs are bounded. When a diff exceeds the packet limit, the artifact and
verification summary explicitly mark it truncated and the reviewer must inspect
the worktree directly. Newly changed symbolic links fail the scope gate rather
than allowing verification to follow a worker-selected external target. The
runtime tracks spawned process groups and terminates
them on scheduler failure, SIGINT, SIGTERM, or engine exit. Automated delegation
detection covers provider collaboration events and nested Codex, Claude, or Kimi
CLI launches, but remains defense-in-depth rather than a substitute for sandboxing.

Codex remediation starts a fresh `codex exec` session with explicit worktree,
workspace-write sandbox, and disposable inputs. It does not use `codex exec
resume`, whose current CLI surface cannot reassert those flags.
