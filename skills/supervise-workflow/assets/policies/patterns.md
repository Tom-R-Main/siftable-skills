# Workflow patterns

| Pattern | Use when | Failure mode prevented | Shape |
|---|---|---|---|
| `single-worker` | A scoped task has one obvious implementation path | orchestration overhead | implement, then deterministic verify |
| `review-existing` | An existing committed branch or change needs independent review without implementation | unnecessary writer mutation or a manual reviewer that bypasses harness evidence | detached worktree at `HEAD`, monitor diff/verification against explicit `base_ref`, fresh selected-profile review |
| `fresh-context-review` | Correctness or scope deserves independent scrutiny; normal medium-task tier | producer self-preference | one implementer, deterministic verify, fresh read-only review |
| `planned-fresh-context-review` | The task is multi-file, ambiguous, or high blast radius | implementation starts from an unexamined approach | fresh selected-profile plan, Sol or gated Kimi implementation, monitor verification, separate fresh selected-profile review |
| `candidate-tournament` (`two-candidate-tournament` remains compatible) | Two to four named, materially different designs or approaches are valuable | premature convergence | 2-4 directed candidates, one fresh review per viable candidate, trusted comparison; execution concurrency remains capped at 2 |

Choose the smallest useful pattern. Parallelize only independent candidates.
Never run dependent edits concurrently or put two writers in one worktree.
For review-only requests, use `review-existing`; require a clean checkout and an
explicit `base_ref` so the engine cannot silently omit uncommitted changes or
guess the comparison boundary.
The runtime schedules from live dependency completion rather than fixed waves, so
a fast candidate can enter independent verification and review while a slower
candidate continues in its own worktree.

Use Codex Sol for general implementation and remediation. The default supervisor
profile pins `claude-opus-5` at `xhigh` effort. The Fable profile pins exact
`claude-fable-5` at `max` effort as reviewer, planner, or both; an explicitly
invoked Fable workflow must contain at least one Fable node. Use Kimi K3 only for
reference-driven frontend implementation when both design evidence and visual
verification exist. Claude nodes remain read-only, a model reviewer supplies
findings, and the invoking host remains the final judge.

Treat the patterns as task-size tiers. Small, deterministic, low-blast-radius work
collapses to `single-worker`; do not use that pattern for an explicitly requested
Fable run because it contains no Fable role. Medium work normally omits the
planning session and uses Sol plus a fresh selected-profile review. Large or
ambiguous work uses the planned pattern. The task contract, not the planner
output, is authoritative.

Do not use a tournament merely to get two samples of the same prompt. A tournament
spec must provide two to four distinct `candidate_directions`. After remediation, rerun the
review for the repaired candidate before judgment.

Candidate review is intentionally looser than final acceptance. An in-scope
artifact with green writer integrity proceeds to review and presentation even if
the writer process/report, deterministic verify, visual capture, or copy policy
is red. This keeps infrastructure failures from suppressing comparison. Final
judgment remains strict. Select one candidate explicitly before remediation; only
the winner receives Sol polish. Prefer two directions for ordinary marketing
mocks and use three or four only for genuinely different compositions.
Long-running writers may expose an untrusted HTML-plus-image live preview before
completion so the host can compare directions early. It is presentation only and
cannot satisfy selection or judgment gates.
