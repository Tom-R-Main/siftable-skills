# Grounding and provenance

This is a local execution workflow combining pstack's proof principles, its project verification skills, and the interview's implementation/observation/correction loop. `pstack-verify` is a local adaptation name, not an upstream skill name. Existing tometo host routing and authorization remain authoritative.

## Transcript

Matt Pocock and Lauren Tan / poteto, [source video](https://www.youtube.com/watch?v=MN9dGgmLyso). The locally generated transcript covers 1:06:45. It is machine transcription, with pstack spelling normalized; technical names may still be wrong. The observations below paraphrase the discussion rather than treating its anecdotes as universal guarantees.

| Time | Discussion | Local decision |
|---|---|---|
| [10:41](https://www.youtube.com/watch?v=MN9dGgmLyso&t=641s) | Tautological tests cost attention without proving useful behavior. | Choose an independently expected observable result and a plausible defect the check could catch. |
| [17:45–19:10](https://www.youtube.com/watch?v=MN9dGgmLyso&t=1065s) | Give the agent hands and eyes; seeing its output enables iteration. Verification closes the loop. | Drive the actual user boundary before claiming changed behavior works. |
| [21:59–24:19](https://www.youtube.com/watch?v=MN9dGgmLyso&t=1319s) | Encode deterministic work in a CLI/script, leaving judgment to the agent; otherwise each agent rebuilds verification differently. | Reuse project drivers; create grounded launch/doctor/drive/evidence/cleanup recipes only when needed. |
| [32:51–33:12](https://www.youtube.com/watch?v=MN9dGgmLyso&t=1971s) | Observe agent mistakes and make them impossible through codebase constraints. | Route recurring failures to types, lint, helpers, or deterministic checks, within authorized scope. |
| [54:03–55:19](https://www.youtube.com/watch?v=MN9dGgmLyso&t=3243s) | Verifiers run the app, look for regressions and bugs, fix, and repeat. Verification effort can range from multiple agents to self-verification. | Use a bounded adversarial check/fix/recheck loop; scale independence to consequence without a fixed swarm. |
| [57:47–58:31](https://www.youtube.com/watch?v=MN9dGgmLyso&t=3467s) | Autonomy depends on how well the domain can be verified; hard-to-verify domains remain difficult. | Report unverified boundaries explicitly. Passing local checks never supplies merge/deploy authorization. |
| [61:33–65:00](https://www.youtube.com/watch?v=MN9dGgmLyso&t=3693s) | Combine useful workflows and learn from actual corrections in past transcripts. | Integrate with existing tometo routes; keep project maps current instead of copying the whole upstream framework. |

## Upstream

Reviewed at immutable commit `7022c81efb48d8b5eb15498ce6043a3bd74b694c` on 2026-10-02:

- [Prove It Works](https://github.com/cursor/plugins/blob/7022c81efb48d8b5eb15498ce6043a3bd74b694c/pstack/skills/principle-prove-it-works/SKILL.md): observe the real artifact and prefer rerunnable checks.
- [Create Verification Skill](https://github.com/cursor/plugins/blob/7022c81efb48d8b5eb15498ce6043a3bd74b694c/pstack/skills/create-verification-skill/SKILL.md): project discovery, launch/doctor/drive/evidence/cleanup, feature map, execute the generated verifier.
- [Maintain Verification Skill](https://github.com/cursor/plugins/blob/7022c81efb48d8b5eb15498ce6043a3bd74b694c/pstack/skills/maintain-verification-skill/SKILL.md): source/live coverage, preserve evidence, distinguish harness drift from product regressions.
- [Test Behavior, Not Implementation](https://github.com/cursor/plugins/blob/7022c81efb48d8b5eb15498ce6043a3bd74b694c/pstack/skills/principle-test-behavior-not-implementation/SKILL.md): public calls and literal observable outcomes instead of self-referential assertions.
- [Encode Lessons in Structure](https://github.com/cursor/plugins/blob/7022c81efb48d8b5eb15498ce6043a3bd74b694c/pstack/skills/principle-encode-lessons-in-structure/SKILL.md): prefer enforceable mechanisms for recurring failures.
- [Feature](https://github.com/cursor/plugins/blob/7022c81efb48d8b5eb15498ce6043a3bd74b694c/pstack/skills/poteto-mode/playbooks/feature.md) and [Autopilot Full](https://github.com/cursor/plugins/blob/7022c81efb48d8b5eb15498ce6043a3bd74b694c/pstack/skills/poteto-mode/playbooks/autopilot-full.md): matching-surface proof, live regression checks, artifact identity, fix/recheck rounds.

Adaptations: host-native tools; one owner of shared runtime state; proportional verification effort; inherited model settings; no automatic PR creation, external messages, merge, deploy, scheduling, or memory writes. The undefined-return heuristic in the upstream test principle is not treated as a universal test oracle; a credible independently expected behavior and plausible defect are the criterion. Claims about environment-specific guarantees are not imported.

## Footwork

Historical optional-runtime source inspection, HEAD `e3b7b086d96c036763458f6501010dc3a9e4881b`, on 2026-10-02. These are source-visible mechanics, not a claim that a live Footwork run was performed:

- `jevdual/python/jevdual/verify.py`, `Verifier` and `check_claims`: completion plus per-requirement unmet checks; supported claim sources and an uncertain band. Adapt the evidence requirement, not Jev's numerical thresholds or text-matching heuristics as universal correctness tests.
- `jevdual/python/jevdual/ledger.py`, `Ledger`: historical actions, current state, and answer evidence have different carry/invalidation semantics. Local adaptation requires fresh current-state checks after known invalidation and does not copy the probabilistic default-to-historical behavior.
- `jevdual/python/jevdual/receipts.py`, `Receipt` and `receipt_from_effect`: delivery, observed change, and failed/unobservable actions are distinct. A `confirmed` receipt is not task completion.
- `jevdual/python/jevdual/completion.py`, `effects`, `floor`, and `repeat_of`: typed evidence for a requested save/submission/read, limits from later edits or wrong-document readback, and duplicate-submission detection. Use resource-bound postconditions, not merely a success screen.
- `jevdual/python/jevdual/grants.py`, `Proposal`, `Grant`, and `why_not`: operation/resource/target/arguments/current value/selection bind a permission to an actual dispatch. Adapt scope checks while preserving the user's existing authorization and host policy; no new permission ceremony for routine authorized work.
- `jevdual/python/jevdual/agent.py`, `_verify_s2_done`: a model's own completion claim goes through verification too. The local skill gives its own final report the same evidence standard as a delegate's.

The interrupted-dispatch rule treats `outcome_unknown` as unresolved, requires manual reconciliation, and forbids replay from a missing session. It is an evidence/authority policy, not proof of any deployed certified browser ledger. Unknown outcomes remain unresolved until read-only observation or an actual idempotency contract establishes a safe next action.

No Footwork provider, grant store, probability model, relay, or effect certification is activated by installing this skill. Project harnesses remain responsible for actual observations and deterministic assertions.

### Concrete hands and eyes

The [footwork-tools route](../../footwork-tools/SKILL.md) adds the source-visible operator CLI (`cli.py`, `session.py`), native AX driver (`native.py`), dedicated-browser driver (`browser_driver.py`), provenance-bearing carries and saved-file checks (`carry.py`), and optional browser capture/transport helpers under `tools/`. Its [context reference](../../footwork-tools/references/contexts.md) separates concrete configured executable access, host-native routes, and untested UI/provider readiness. This tool routing is grounded in the interview's 17:45–19:10 discussion.

## Targeted refresh (2026-10-15)

Added explicit test-boundary catches/misses, sensitivity to broken behavior while tolerating internal refactors, and readback of intentional local code/fixture mutations before trusting a forced failure. Mutation sensitivity remains distinct from reproducing the original defect. See the [tometo refresh](../../tometo-mode/references/provenance.md#targeted-refresh-2026-10-15) for immutable Matt Pocock and pstack source commits and adaptation limits. No new test-approval or release authority is implied.

## Targeted refresh (2026-10-26)

Added optional [advisory checks](advisory-checks.md) for duplication, complexity, and targeted mutation testing, plus preservation of the last independent behavioral check during authorized test pruning. These add no tool installation, required score, refactoring, CI/hook, release, or global machine enforcement authority.

Sources and reviewed limits:

- Matt's [test-pruning record](https://github.com/mattpocock/course-video-manager/blob/279315673b519bf5a85bf76da6f536890b34f524/docs/plans/test-pruning.md#L176-L189) kept two proposed deletions because each was the last guard on a distinct behavior.
- [ub-mode](https://github.com/unclebob/ub-mode/blob/57a8bdd28e45ed41900ace0bafa2ff76dd9ed70f/SKILL.md) proposes deterministic quality tools. Borrow targeted sensitivity assessment, not mandatory tools, numerical gates, wholesale redesign, exhaustive logs, or automatic commits/pushes.
- Dryer at `66ff6d21a42c04afcad89c78a80066176d1294b0`: [set-based fingerprints](https://github.com/unclebob/dryer/blob/66ff6d21a42c04afcad89c78a80066176d1294b0/src/dryer/shape.py#L98-L108) are structural similarity, not behavioral equivalence or a removable-line percentage. [Changed selection](https://github.com/unclebob/dryer/blob/66ff6d21a42c04afcad89c78a80066176d1294b0/src/dryer/cli.py#L263-L283) compares changed files only with one another. [Empty scan handling](https://github.com/unclebob/dryer/blob/66ff6d21a42c04afcad89c78a80066176d1294b0/src/dryer/cli.py#L296-L316) leaves prior metrics intact. Bounded Clojure CLI checks reproduced both consequences without installing dependencies.
- Dryer [reader dispatch](https://github.com/unclebob/dryer/blob/66ff6d21a42c04afcad89c78a80066176d1294b0/src/dryer/clojure_read.py#L336-L359) rejects valid var-quote syntax and drops the following forms. A bounded CLI check reproduced a warning, successful exit, and missed duplicate candidates; the equivalent `(var target)` control found them. [TypeScript template literal handling](https://github.com/unclebob/dryer/blob/66ff6d21a42c04afcad89c78a80066176d1294b0/src/dryer/astnorm.py#L158-L163) discards interpolation structure in static inspection. The cross-language suite and that TypeScript path were not executed. Recheck these caveats for another version rather than assuming they persist.
- Mutator at `a5a0cb803b66e0cdb8bf471b3b08af701d424a41`: [generic failure classification](https://github.com/unclebob/mutator/blob/a5a0cb803b66e0cdb8bf471b3b08af701d424a41/src/mutator/workers.py#L296-L324) does not separate behavioral kills from invalid or infrastructure failures. [Cache selection](https://github.com/unclebob/mutator/blob/a5a0cb803b66e0cdb8bf471b3b08af701d424a41/src/mutator/engine.py#L61-L98) preserves kills based on function text, not the whole relevant test artifact. [Linked worker files](https://github.com/unclebob/mutator/blob/a5a0cb803b66e0cdb8bf471b3b08af701d424a41/src/mutator/workers.py#L122-L131) and inherited environment do not establish effect isolation. These are source findings; mutator was not installed or executed.

The mode's [October 26 refresh](../../tometo-mode/references/provenance.md#targeted-refresh-2026-10-26) records the remaining source and workflow updates. Formal checking remains optional; statechart remains deferred.

## Frontend integration (2026-10-26)

The optional [break-ui](../../break-ui/SKILL.md) and [emil-design-eng](../../emil-design-eng/SKILL.md) routes add realistic schema-backed data/layout cases and relevant motion interruption/input checks. Their provenance records upstream commit `2d228630ba1446365f614a108cb8252f1feda202` and corrections. They preserve the task's audit/fix mode, actual data and public boundaries, run-owned fixtures, and evidence limits; no required all-surface matrix or new runtime is implied.

## User-directed performance acceptance (2026-11-01)

Added comparable workload/resource acceptance for performance and technology-selection promises, including consumer/boundary costs and correctness checks. This implements the library's system-efficiency policy; it does not claim a new benchmark result, universal language ranking, or upstream refresh. Actual target execution remains required for runtime claims.
