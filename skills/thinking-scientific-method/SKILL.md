---
name: thinking-scientific-method
description: Investigate uncertainty with explicit hypotheses, discriminating predictions, bounded experiments, and evidence-based revision. Use for debugging, performance investigations, feature experiments, or experiment design when an observation can settle competing explanations.
---

# Scientific investigation

Turn an uncertain claim into a test with an independently expected result. An experiment can support an explanation within tested conditions; it cannot grant deployment authority, prove an untested population behaves identically, or erase disconfirming evidence.

## Establish the question

Record the observed behavior, affected surface, source artifact/version, baseline, and unknowns. Keep observations separate from explanations. Choose a question small enough that an authorized experiment can answer it; if the request is planning-only, design the experiment without running mutations.

## Make alternatives distinguishable

Write the leading hypothesis and at least one plausible alternative when uncertainty is material. For each, name an observation that would support it and an observation that would contradict it. A useful prediction differs between alternatives. If both explanations predict the same observation, choose another measurement.

Example: a CLI becomes slower on large inputs. One explanation is repeated parsing; another is output serialization. Measure parse and serialization time separately on fixed input and output sizes. Changing both size and formatting at once cannot distinguish those causes.

## Freeze the experiment before running

Specify:

- The independent variable, measurement, baseline, and relevant negative control.
- Input identity, runtime version, configuration, and artifact under test.
- A smallest credible sample and repetition strategy, including warmup or ordering effects for benchmarks.
- Expected supporting and contradicting outcomes, tolerance for noise, and what makes the result inconclusive.
- Time/resource budget, stop rule, scope, recovery path, and existing authority.

Do not choose thresholds after seeing the result. For product experiments, specify the population, assignment unit, primary outcome, guardrails, and analysis window; account for interference, selection, repeated peeking, and missing data. Do not claim causal evidence from an uncontrolled before/after comparison.

## Run the smallest discriminating test

Prefer isolated fixtures, established project drivers, and reversible local changes. Preserve real failure conditions when reproducing a defect. Change one mechanism at a time where possible and keep the comparison conditions matched. Use instrumentation that measures the promised boundary rather than an adjacent proxy.

Before a consequential or uncertain dispatch, confirm the operation and target are in scope. Cloud changes, production traffic experiments, paid provider calls, external messages, and destructive actions need their own existing authorization. A good experiment design is not permission to execute it.

Keep failed runs and negative results. When the probe fails, distinguish probe validity from the product outcome. Repair a repeatedly invalid probe before drawing another causal conclusion. Never silently exclude an inconvenient observation.

## Revise from the evidence

Compare the result with the frozen predictions. Report supported, contradicted, or inconclusive; explain alternative causes and measurement limits. Choose the next smallest discriminating test or implement a bounded fix when the task authorizes it. Recheck the original failing surface and relevant regression path after a change.

Use [pstack-investigate](../pstack-investigate/SKILL.md) for mechanism tracing and [pstack-verify](../pstack-verify/SKILL.md) for actual-surface verification. Those workflows preserve scope, independent expectations, and uncertain-effect reconciliation.

## Evidence record

Keep a compact task-local record: question, artifact, hypotheses, frozen predictions, experiment/control, measurement, result, decision, and remaining uncertainty. Bind output to the checked artifact and include enough commands/input identity to reproduce it. Store no credentials or unrelated private captures.

State the strongest conclusion the evidence supports and what would change it. A passing local test, independent review, CI, merge, deployment, production observation, adoption, and business outcome remain separate claims.

## Provenance

This portable workflow is original text based on general experimental-method concepts and this library's evidence/authority discipline. A local skill from `tjboudreaux/cc-thinking-skills` inspired the skill selection, but no redistributable license was found at its recorded source commit `97531944ecd082cb263a367f5806fb2353c0d049`; its text is not copied here.
