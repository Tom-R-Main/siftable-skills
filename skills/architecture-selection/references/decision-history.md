# Reconstruct a decision without hindsight

Use when learning from repository architecture, migrations, PRs, ADRs, or design discussions. A successful project demonstrates a feasible design; it does not prove the chosen technology beat alternatives.

## Separate the questions

Record the question being answered: why the authors chose it then, what the current implementation does, or what the target project should choose now. These can have different answers. A teaching sample, constrained port, or vendor integration may intentionally optimize different objectives from a greenfield product.

Find the original decision, linked discussion, alternatives and rejected proposals, review objections, implementation/tests, and follow-up corrections. Use bounded local history first; use authorized upstream read tools when needed. Do not fetch entire histories to answer one question. Missing or shallow history leaves rationale unknown; infer mechanisms from source without attributing intentions to authors.

Record repository/revision, decision date, PR URL and head/merge identity, status, relevant comment anchors, and current source evidence. Open, closed-unmerged, merged, reverted, and superseded are different states. A PR description can describe an early stage later replaced within the same PR; inspect the final diff and consumer. A merged PR establishes adoption, not deployed success. Later discussion may report another version or platform; preserve that context.

Separate explicit maintainer rationale, contributor claims, reviewer concerns, reported experiments, and your reconstruction. Retain negative evidence: failed approaches, reverts, uncovered platforms, and tests that missed the real consumer. Do not turn a post-hoc language rationale into a controlled comparison.

## Test transfer

For each lesson, name the mechanism, enabling constraints, cost transferred elsewhere, counterexample, and cheapest target check. Verify the actual feature/configuration and target-specific branches: a common API may enforce different limits on native and Wasm targets; initialization success may still leave runtime capabilities unusable. Specify the required degradation/fallback behavior and how the user observes it.

When evaluating the skill itself, distinguish source-informed review from a held-out prediction. A stronger retrospective gives an evaluator the original problem/constraints before revealing the chosen design and outcome, then examines whether its questions and checks would expose the actual tradeoff. Matching the historical winner is not the success criterion. Do not claim predictive accuracy from reading the answer first.
