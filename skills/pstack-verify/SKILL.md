---
name: pstack-verify
description: "Verify changed behavior on the real app, CLI, service, or artifact; exercise relevant failure and regression paths, fix within scope, and preserve reproducible evidence. Use before reporting an implementation complete or when asked to prove it works."
license: MIT
metadata:
  upstream: cursor/plugins/pstack
  upstream-commit: 7022c81efb48d8b5eb15498ce6043a3bd74b694c
  adaptation: tometo-shared
---

# Verify the changed behavior

Close the implementation loop by observing the result, not by accepting the implementer's report. Scale the effort to the claim and consequence. A small static edit can be checked directly against the saved artifact; changed runtime behavior needs a check on that runtime. Existing task scope and authorization govern fixes, external effects, merge, and deployment.

## Choose the proof

Translate the user's promise into observable success conditions before driving. Identify the actual entry point, required input variants, persistence or other side effects, and nearby behavior the change could break. Derive expected results from the request, established behavior, or an independent reference, not the implementation under test. Do not invent product requirements to test.

For a multi-step or consequential flow, keep a compact requirement ledger: criterion, kind, evidence source/step, result, and limitations. Distinguish **historical action** (a submission happened), **current state** (the intended saved value still holds), and **answer** (a reported fact has a source). Preserve observed historical events within the same run; recheck current state after edits, navigation, restarts, or other invalidation; ground each new answer in evidence for that answer. An unclassified requirement needs a fresh check rather than silently becoming historical. Overall completion requires every required criterion; confidence or a generic success screen cannot fill an evidence gap.

Read the repository's verification instructions and mapped feature paths. Prefer its existing `verify-<app>` skill and harness. If a repeatable driver is missing and creating one is useful to the authorized work, use [pstack-create-verification-skill](../pstack-create-verification-skill/SKILL.md). A one-off check does not need a new framework. If the map or harness has drifted, use [pstack-maintain-verification-skill](../pstack-maintain-verification-skill/SKILL.md) for bounded corrections. A generated but unexecuted verifier is a draft.

Make the artifact identifiable: record the checkout/commit plus relevant local changes, or the saved file/build/version for a non-Git artifact. Verify the version actually running when the runtime can expose it. A Git SHA alone does not identify an uncommitted patch or prove which build a server is serving.

## Drive, observe, challenge

1. Follow the project's launch, doctor, isolation, and cleanup recipe. Use [footwork-tools](../footwork-tools/SKILL.md) to establish a working observation/action route for this surface, then follow the selected host skill. A missing driver is a capability gap, not proof the product failed. Record handles for resources this run starts; keep a single owner of shared app state.
2. Run required project checks and drive the promised behavior through the real public interface. For UI work, start at the user's entry point; for a CLI, run the command; for a service or library, call its public boundary; for a generated artifact, open/read the saved output. Verify side effects as well as visible output. A convenient deep link is incomplete when another required entry point is untested.
3. Challenge the change with the smallest useful set of relevant cases: bad or empty input, repeat actions, reload/readback, interrupted operations, recovery, and nearby regressions. Select cases from the actual mechanism and consequence; do not turn this list into a mandatory matrix for unrelated work. Compare against the base version when it can distinguish a new regression from existing behavior; record when the feature is new or the baseline is unavailable.
4. Prefer deterministic assertions and repository drivers for mechanical checks. Keep agent judgment for selecting scenarios, interpreting evidence, and investigating surprises. A useful test can fail for a plausible defect and compares an observable result with an independently chosen expectation. Mock call counts, fixture-only assertions, or restating implementation constants do not prove the user's outcome. Use mocks at established external boundaries and state what remains unverified there.

Manual adversarial exploration means using the app to look for mistakes. Call it exploration unless an actual fuzzing harness ran; do not claim formal verification or exhaustive coverage from clicking around. For substantial or difficult changes, a focused independent verifier may add confidence when delegation is permitted. Give it the promise, artifact identity, source paths, and permitted effects; let it derive checks rather than handing it the implementer's verdict. Use inherited model settings and report separate contexts as such. Do not create a fixed verifier swarm for routine work.

## Footwork: evidence for the requested effect

Separate input delivery, observable change, and the requested postcondition. A delivered click or a `confirmed` receipt proves only what the driver observed. A changed title, focused control, or closed dialog does not prove that the intended file was saved or the correct request submitted. Bind readback to the intended resource and arguments; record partial, refused, suspected-no-op, and unobservable outcomes without promoting them to success. A DOM field value can prove what the field holds, not that a server persisted it.

Use existing task authorization; do not ask again for an already-authorized action. Before a consequential drive, confirm the current target/resource, operation, and arguments still match that scope and any host-enforced grant. A label such as `Submit` is not sufficient target identity. Verification never authorizes wider access or a different recipient, amount, document, or live effect.

If dispatch may have happened but its reply or receipt is lost, record an unknown outcome and reconcile using read-only postconditions before considering another dispatch. Do not repeat a submission, delete, save, or navigation with side effects merely to obtain cleaner proof. Re-dispatch only when non-delivery is established or the actual system's idempotency contract makes retry safe and the action remains authorized; otherwise report the unresolved effect. Do not promise exactly-once execution from browser traces.

Keep the short action/observation trajectory needed to support the ledger. Completion claims must cite the actual postcondition or relevant historical evidence; remove unsupported facts or mark them inferred/unverified. Driver failures and uncertain model judgments stay unresolved until observation settles them. This workflow borrows Footwork's evidence discipline; it does not start Footwork, call Jev, import probability thresholds, or supply a certified effects ledger.

## Fix and recheck

Preserve a concrete failing observation before changing anything. Separate a product defect, a missing prerequisite, and a broken observation method. Recheck instance health after surprising behavior. If the same probe fails twice without new information, repair the probe or change the hypothesis rather than repeating it.

Fix product code only when the current task authorizes implementation/remediation. Verification-only requests report findings; harness maintenance stays inside its owned files. Never weaken the expected behavior or a required gate to manufacture a pass. Use a meaningful regression test or replayable reproduction for a demonstrated defect when that adds durable protection.

After a fix, drive the failed path and affected regressions again on the new artifact. Keep unaffected evidence only when its validity is clear; a previous pass does not prove changed code. Stop repeating passed checks unless another change, failure, or unresolved concern justifies it. If an external dependency, unsafe effect, or unavailable runtime prevents a check, mark that condition unverified with its attempted route and concrete blocker.

## Preserve the evidence

Use the project's evidence location, or a task-scoped output directory outside teardown scratch. Keep the report small:

- Artifact identity and the feature/entry point checked.
- Reproducible command or action sequence, prerequisites, expected result, and observed result.
- Relevant exit status, response, saved-state readback, screenshot, or other proof, with artifact paths.
- Required cases covered, remaining gaps, failures/fixes, and the checks rerun after changes.
- Outcome: **verified** only when the selected claim's required checks passed; **failed** for a demonstrated mismatch; **unverified** for missing proof. Partial successes stay visible without turning the whole claim into a pass.

Clean up only run-owned processes and scratch state, then confirm evidence remains readable. Keep local behavior, independent review, CI, merge, deployment, and live production observation as separate claims. Verification evidence informs a release decision; it does not grant release authority.

## Improve the next run

When authorized project changes add or alter a public flow, update the affected verification recipe and feature map and execute the changed recipe. For recurring agent failures, prefer a type constraint, lint rule, canonical helper, or deterministic check over another reminder. Capture judgment-dependent lessons in the scoped skill when warranted. Propose changes outside the authorized paths; do not silently edit global skills, memories, or schedules.

Read [grounding and provenance](references/grounding.md) when auditing or updating this workflow.
