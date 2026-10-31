---
name: pstack-interrogate
description: "Review a scoped code diff with independent scrutiny, traceable findings, and a synthesized verdict. Use for requested code review; keep review separate from implementation and release authority."
license: MIT
metadata:
  upstream: cursor/plugins/pstack
  upstream-commit: 5bf2b1544db739998121a306340631963c2ff3de
  adaptation: tometo-codex
---

# Interrogate

Produce a review verdict. Do not modify the reviewed code or post comments unless the user separately requests those actions. A review inside an implementation task returns findings to that task's owner; it does not take over implementation.

## Bind the scope

Establish the intended behavior from the request, relevant requirements, and actual callers. Resolve the requested base and target. Record full commit IDs for committed work. For working-tree review, include staged, unstaged, and relevant untracked files and capture their contents or hashes; do not substitute `HEAD` for dirty work. Respect a user's specific file scope and report excluded context that limits the verdict.

Read [the review rubric](references/review-rubric.md). Review standards and requirement conformance as separate passes so neither gets mistaken for the other. Use repository/domain rules where they affect correctness.

Discover the standards that apply to changed paths: ancestor and nested `AGENTS.md` instructions, `CODING_STANDARDS.md`, `CONTRIBUTING.md`, and relevant domain guidance or ADRs. Record the applicable source paths and give each reviewer the same list alongside the intent and rubric. Distinguish documented requirements from judgment calls, and leave mechanically enforced formatting to tooling.

## Independent scrutiny

If the authoring agent is performing this review and delegation is permitted, use a fresh reviewer with the requested scope, intended behavior, relevant repository instructions, and the rubric. This skill requests that bounded independent review; it does not require an implementation worker. If the caller already supplied an independent review context, use it directly.

Use multiple model families only when the user requested them or an already-authorized available workflow supports them. Inherit model settings otherwise. Do not claim model diversity for several agents using the same model. Respect explicit limits on additional reviews. If independence cannot be obtained, perform the available review and label it a self-review or single-context review.

Each reviewer owns read-only inspection of the reviewed files, may run authorized local checks, and returns findings with a concrete trigger, affected path/line, consequence, and evidence or a clearly stated uncertainty. Supply the same intent and rubric to every reviewer. Reviewers must not edit, merge, deploy, send messages, or expand scope.

## Judge the evidence

Trace each material finding through callers and types; run a small reproducer when useful. Deduplicate findings and explain disagreements. Agreement helps prioritize inspection; it is not proof. A lone reproducible issue outranks unsupported consensus.

Separate blocking findings, worthwhile non-blocking changes, and dismissed claims. Do not invent a numerical quality score or reject code solely for an arbitrary file-length threshold. Keep speculative redesign out of the blocking list unless it causes a concrete scoped defect or demonstrable maintenance problem.

Before delivering, verify that the reviewed files/artifact still match the recorded scope. If it changed, reassess the changed paths and their effects before carrying the verdict forward. A clean review means no actionable findings within the checked scope, not proof that all runtime behavior works.

Return findings first, then the verdict, scope/artifact identity, actual reviewer independence/model coverage, checks run, and gaps. No automatic fixes, PR comments, gstack receipts, merge, or deployment follow from this verdict. Retained gstack release tooling may run its own review; never label this as a gstack specialist pass that did not occur.

Source and adaptation details: [provenance](references/provenance.md). Read only when auditing or updating this skill.
