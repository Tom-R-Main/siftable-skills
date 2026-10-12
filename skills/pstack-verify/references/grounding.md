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
