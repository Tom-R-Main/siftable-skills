# Optional recurring-work controls

Read only for authorized design, implementation, or diagnosis of recurring or chained agent work. Ordinary feature tasks do not use this reference. It grants no schedule, monitoring, external-message, PR, merge, deployment, or spend authority. Reuse the existing supervisor or orchestrator; do not create a competing controller.

## Define the run contract

Record only what the workflow needs:

- Trigger and input identity, including the ticket, PR, source artifact, or schedule occurrence it represents.
- Resources read and written, permitted effects, and the artifact/version against which decisions remain valid.
- A stable work key and the coordinator's actual claim/lock mechanism so overlapping runs cannot perform the same work. Deduplicate intake separately so one source event does not create multiple tickets.
- A validated result schema and allowed transitions, including success, blocked, and needs-human outcomes. Reject malformed or stale results before applying effects.
- The next trigger and an observable acknowledgment that the intended downstream run started. Applying a label or emitting a completion string alone does not prove the handoff worked.
- A finite attempt budget across the whole chain, concurrency/resource limits, and a stopping condition. Retries must not reset the budget by launching a new run. When a run has a deadline, cap polling and backoff by the remaining time, bound individual calls, and retain the deadline across handoffs.
- Where a human re-enters, which decision or input is needed, the retained evidence, and how work resumes without repeating completed effects.

Enforce mechanical controls in the coordinator or harness. A prompt asking agents not to duplicate work is not a lock. Match the state store and transition mechanism to the existing system rather than inventing another workflow engine.

## Recover and check

Bind PR work to repository and PR identity, including the head repository for forks and the checked head SHA. Branch names alone cannot identify a PR. Distinguish active PRs from closed or merged history before resuming; report multiple active matches as ambiguous.

Reconcile an uncertain effect by readback before retry, following [pstack-verify](../../pstack-verify/SKILL.md). If a PR exists and only review dispatch failed, resume dispatch against that PR; do not rerun implementation and create another. Preserve work keys, artifact identities, receipts, attempts, and unresolved outcomes across runs.

Select checks for the actual mechanism: overlapping triggers, repeated source events, malformed output, a stale artifact, a lost response after an effect, failure between stages, or exhausted retries. Use task-owned fixtures and endpoints with the [verification isolation recipe](../../pstack-create-verification-skill/references/isolation.md). Report an unobservable downstream handoff as unresolved.

For authorized activation, introduce a bounded trigger or small batch first and widen only when observed outcomes justify it. Keep quiet while monitored state is unchanged unless the user requested periodic updates. A design or local dry run does not authorize activation.

Source status: Matt Pocock's software-factory proposal was unmerged when reviewed on October 23, 2026. This borrows control questions and a concrete chained-workflow example, not its factory architecture or fixed review policy. See [provenance](provenance.md#targeted-refresh-2026-10-23).
