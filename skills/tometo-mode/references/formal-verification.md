# Optional formal verification

Read only when formal checking is requested, or a consequential invariant makes it useful within the authorized architecture or investigation task. Ordinary feature work stays with [pstack-verify](../../pstack-verify/SKILL.md). This reference does not require formal checks, install a verifier, or activate statechart tooling.

## Create a project check

Choose a concrete promise that existing tests do not adequately cover, such as exclusive ownership, retry safety, permissions, or recovery across interleavings. State the property, the harm if it fails, and the actual public behavior it represents. Reuse an existing project verifier before creating another.

Select a tool for the question and available environment. Distinguish a code-level verifier, a bounded model, and generated-input tests. If the appropriate verifier is unavailable, report the missing capability; a test fallback remains a test. Tool installation or external execution follows the task's existing permissions.

Map every modeled action and condition to current source files and symbols, including all writers of the protected state. Preserve real atomic boundaries: an await, transaction, restart, or competing writer can split an apparent single step. Record assumptions, bounds, excluded effects, tool version, configuration, and artifact identity, including relevant uncommitted changes.

Write a project-local verification recipe with the exact command, prerequisites, covered code, property, expected result, counterexample interpretation, evidence location, and last confirmed source identity. Leave no executable placeholders. A sync commit alone cannot identify a dirty patch.

Execute the recipe and challenge its sensitivity with a representative defect in an isolated task-owned copy when justified and authorized. Confirm the mutation landed, follow the entire recipe, preserve the result, restore only the experiment, and rerun the final artifact. A handwritten model does not automatically observe a product-code mutation: re-establish the source correspondence or replay through the actual public boundary. If the workflow misses the break, report that gap; a passing unchanged model is insufficient evidence about changed code. Probe sensitivity does not reproduce an original defect.

Replay a reported counterexample through actual code when possible. A model step that cannot happen indicates a modeling error; a reachable violation is a product finding. Do not weaken the property to make it pass. Product fixes require implementation scope. If execution is unavailable, deliver a draft with the blocked step.

## Maintain an existing check

Locate its coverage map, assumptions, bounds, command, and last confirmed source identity. Run the existing recipe once and preserve the baseline, without treating its pass as proof of current correspondence.

Inspect changes since the sync point plus current staged, unstaged, and relevant untracked work. Follow renamed or moved functions and new writers of guarded state. Classify each relevant change as no semantic effect, model/harness drift, an intentionally changed promise with evidence, or a possible product defect. If no sync point exists, record the best available historical baseline and its uncertainty.

Update the model from source before interpreting a rerun. Change the property only for an intended promise change supported by requirements or source history; disclose any reduced bound. Recheck sensitivity and replay affected counterexamples. Keep verification corrections separate from product remediation.

Advance the coverage and sync record only after confirming correspondence and executing the recipe on the identified artifact. A baseline pass followed by a failure after correspondence repair was a pass on a stale description; say so. Do not advance a blocked check's sync record.

Report correspondence status, execution result, covered property, assumptions/bounds, artifact identity, counterexample or sensitivity evidence, and remaining gaps separately. A model pass proves its stated model and bounds; code correspondence and runtime behavior need their own evidence.

Sources and adaptation limits: [provenance](provenance.md#targeted-refresh-2026-10-23).
