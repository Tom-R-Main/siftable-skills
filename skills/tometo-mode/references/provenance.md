# Provenance

Adapted from Lauren Tan / poteto pstack, MIT licensed, at immutable commit `5bf2b1544db739998121a306340631963c2ff3de`. This is a curated Codex adaptation, not the upstream Cursor plugin.

- https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/poteto-mode/SKILL.md
- https://github.com/cursor/plugins/blob/5bf2b1544db739998121a306340631963c2ff3de/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md

Changes: native available tools and inherited model settings; task-scoped routing; existing local skill ownership; bounded verification and explicit limitations; no Cursor-only mode metadata, fixed model slugs, automatic PR posting, telemetry, or implicit authority to send messages, merge, deploy, or write memory. Sibling skill links are explicit installation dependencies; install their closure as well. Upstream updates require a reviewed rebase of these adaptations.

Verification refresh, 2026-10-02: this route now uses the shared `pstack-verify` execution workflow. Its [grounding](../../pstack-verify/references/grounding.md) records source grounding, upstream commit `7022c81efb48d8b5eb15498ce6043a3bd74b694c`, and the inspected Footwork source. Other upstream adaptations remain based on the original commit above.

## Footwork tools refinement (2026-10-02)

Added [footwork-tools](../../footwork-tools/SKILL.md) for actual observation/action access by context, local operator CLI commands and source-bound handoffs. See its [source and runtime limits](../../footwork-tools/references/contexts.md). This extends the earlier evidence discipline with concrete drivers; it does not activate providers or a remote integration.

## Targeted refresh (2026-10-15)

The maintained source records an October 15 review of reference checkouts at pstack `e5136d82418d2db3165ea1050d17577cd618cc05` and Matt Pocock skills `49dd158d1076134a641b33efb035946536778336`. This is a selective adaptation; the baseline metadata and host-specific adapters remain intact.

- Task framing: pstack [sharpen](https://github.com/cursor/plugins/blob/79afd75d5bd51383fbb526b72f36db03180b8301/pstack/skills/sharpen/SKILL.md), October 13; adapted as [task framing](sharpen-task.md) with explicit user constraints preserved.
- Read-only catch-up: pstack [ketchup](https://github.com/cursor/plugins/blob/afd51cf66a3100a95f878d6c4b93a01f6508e3b0/pstack/skills/ketchup/SKILL.md), October 14; adapted as [catch-up](catch-up.md), without fixed presentation counts or new execution for visuals.
- Verification readiness: pstack [usable clean-start readiness and substitute-target gaps](https://github.com/cursor/plugins/commit/c49b37a2c0e7bede60a71ad7322e3f12c337a3da), October 12. Use only isolated run-owned data; record missing setup without weakening a journey or claiming a product failure.
- Regression proof: Matt's [mutation readback](https://github.com/mattpocock/skills/blob/f3fc5632f401156837ee3872f14fe33ccf1024ea/skills/engineering/diagnosing-bugs/SKILL.md) and [test-boundary catches/misses](https://github.com/mattpocock/skills/blob/3f599139104dfceabc7754eeb91319802f85e042/skills/engineering/tdd/SKILL.md), October 7. A forced failure proves probe sensitivity, not original-defect reproduction. No universal TDD or approval of every test boundary.
- Review grounding: Matt's [explicit standards discovery](https://github.com/mattpocock/skills/blob/3da8c01116264675eeefbd6e9d59c734de9095cc/skills/engineering/code-review/SKILL.md), October 7. Keep local synthesized review and proportional independence.
- Reasoning and diagnostics: pstack's [principle simplification](https://github.com/cursor/plugins/commit/e5136d82418d2db3165ea1050d17577cd618cc05), October 14, and [cheap ongoing diagnostic signal](https://github.com/cursor/plugins/commit/36cecbf2b5089b275254d59cb4612d6f96f00fbd), October 13. Local process guidance now follows repository isolation, evidence-based review, reviewable PR boundaries, and authorized cleanup rather than fixed mechanism prescriptions.

These changes add no merge, deployment, external messaging, monitoring, spend, or memory-write authority. Framing and catch-up are internal reference routes, not separately installed slash commands. Host-specific entrypoints retain their adapters; the portable packages use explicit sibling dependencies.

## Targeted refresh (2026-10-23)

The maintained source records a review of October 9–23 history in reference checkouts and GitHub. Pstack's latest relevant commit was `4ec7ffa173eaa70d3d9467a627baf0954645a353`; Matt Pocock skills main was `5beb35b040e3de97e54fa9e386d7e42d15c295c2`. Earlier October 15 adaptations remain in place.

- Complete catch-ups: pstack [every waiting item](https://github.com/cursor/plugins/commit/16541c6bc1ed6c8d808b2f78a33364003e82b967) and [no word-budget omissions](https://github.com/cursor/plugins/commit/bc1443790cc980d0ea857663260a831299884508), adapted without fixed word counts or new visual execution.
- Runtime isolation: Matt's CVM [resolved storage containment](https://github.com/mattpocock/course-video-manager/commit/89245b3099e6807026edf6a1eb799eac2555df1b), [live-drive refusal](https://github.com/mattpocock/course-video-manager/commit/9354dd7e0a4252c68ba6e09677103fe08480b1ac), and [live recorder refusal](https://github.com/mattpocock/course-video-manager/commit/73d62e2d7cd77913cd5d365efb1d50545ed20571), adapted in the [isolation recipe](../../pstack-create-verification-skill/references/isolation.md). No machine-specific paths or dead-port values became universal policy.
- Optional formal checks: pstack [create](https://github.com/cursor/plugins/blob/6b78e9f4e46c75d1697d837e51f07c2692e60b24/pstack/skills/create-formal-verification-skill/SKILL.md) and [maintain](https://github.com/cursor/plugins/blob/7b353f78f6ec193bdbe48ed8059444eb09b6878e/pstack/skills/maintain-formal-verification-skill/SKILL.md), adapted as [one conditional reference](formal-verification.md). Code correspondence, dirty artifact identity, bounded claims, and runtime evidence remain separate. No verifier installation or mandatory formal gate was added.
- Optional recurring work: Matt's [software-factory proposal](https://github.com/mattpocock/skills/blob/b59cab42bf1206e1363eafc37f71b21c3bcaa12f/skills/in-progress/software-factory/SKILL.md), open [PR 1316](https://github.com/mattpocock/skills/pull/1316) when reviewed, plus the [course example's concrete handoff/recovery](https://github.com/mattpocock/cohort-005-project-fork-2/commit/984a30917a3235fc28bc469534e1ae7fe23ae022). [Local controls](recurring-work.md) borrow bounded transitions, deduplication, and recovery, not automatic activation, a factory vocabulary, or a fixed review quota.
- Dated project notes: Matt's [commit-cited history](https://github.com/mattpocock/skills/commit/5beb35b040e3de97e54fa9e386d7e42d15c295c2), restricted to already-authorized handoffs and decision records. No new wiki, memory writes, or scheduled upkeep.
- Mechanical route checks: pstack's [docs-vs-tree check](https://github.com/cursor/plugins/commit/019a6a20592c10bf92869e5740368f578a9997fd) inspired a local read-only checker for routes, names, symlinks, and explicitly shared host assets. Host-specific adapters remain distinct.

Statechart remains deferred. No statechart script, Java/TLC dependency, Mermaid package fetch, or new runtime provider was added. Upstream's rewritten-prompt sharpen behavior was not adopted; the local preflight still continues authorized work. This refresh grants no new external effects, activation, release, spend, or memory authority.

## Targeted refresh (2026-10-26)

Reviewed pstack since the October 23 refresh through `e73df471cd4bd918367e99f3dd9c51bd53ddf5f0`, Matt Pocock skills main at unchanged `5beb35b040e3de97e54fa9e386d7e42d15c295c2`, and CVM changes through `9b13531b5751ed4c539ac849211bf8bcc97887ff`. Matt's factory PR 1316 remained open at `b59cab42bf1206e1363eafc37f71b21c3bcaa12f` when checked. This is a selective adaptation, not a full upstream sync.

- Maintained skill source: pstack [reflect cache correction](https://github.com/cursor/plugins/commit/7054003c3723e82d099fb7620e3bc8d7d63eebc6), adapted to canonical source, symlink identity, and host adapters.
- Optional recurring controls: pstack [remaining-time polling/backoff](https://github.com/cursor/plugins/commit/fe096ef31c94c30997207ffb6e30c51f15a34f16), [fork head identity](https://github.com/cursor/plugins/commit/96dec8ee58deb7b388fa080fbceaba4460a7c9dd), and [active PR precedence](https://github.com/cursor/plugins/commit/3c596e701b5ca3d213e072464eec36baf0dee3e7). The local reference also calls for bounded individual calls; the upstream sleep cap alone does not prove a strict end-to-end deadline.
- Staged-content integrity: Matt's [accidental worktree gitlinks fix](https://github.com/mattpocock/course-video-manager/commit/da04bf45220545f329f686ca4d8825074556cbe3). Inspect paths and modes within an authorized commit; retain legitimate submodules rather than importing a blanket gitlink ban.
- Test pruning: Matt's [last behavioral checks retained](https://github.com/mattpocock/course-video-manager/blob/279315673b519bf5a85bf76da6f536890b34f524/docs/plans/test-pruning.md#L176-L189), adapted in the shared verification skill.
- Optional advisory checks: [ub-mode](https://github.com/unclebob/ub-mode/blob/57a8bdd28e45ed41900ace0bafa2ff76dd9ed70f/SKILL.md), dryer `66ff6d21a42c04afcad89c78a80066176d1294b0`, and mutator `a5a0cb803b66e0cdb8bf471b3b08af701d424a41` informed [advisory code checks](../../pstack-verify/references/advisory-checks.md). [Verification grounding](../../pstack-verify/references/grounding.md#targeted-refresh-2026-10-26) records source findings and executed-check limits. No mandatory TDD, CRAP/duplication threshold, perfect mutation score, exhaustive action log, or automatic push to main was imported.

Dryer remains optional and advisory. No dryer tool, quality gate, dependency, global hook, or statechart tooling was installed. Formal verification and recurring-work references remain conditional, and statechart remains deferred. New pstack statechart/Pele integration and ketchup-video were not adopted.

## Frontend integration (2026-10-26)

Added [emil-design-eng](../../emil-design-eng/SKILL.md) and [break-ui](../../break-ui/SKILL.md), adapted from the fully reviewed MIT-licensed Emil Kowalski repository at `2d228630ba1446365f614a108cb8252f1feda202`. The portable packages preserve this routing through explicit sibling dependencies, independent of host-specific installation roots.

[Craft provenance](../../emil-design-eng/references/provenance.md) maps all 15 source skills to conditional references or the stress-test skill, and records corrections to workflow control, accessibility, performance assumptions, recipes and specialist toolchain guidance. [Stress-test provenance](../../break-ui/references/provenance.md) records catalog corrections and evidence limits. No library, provider, global hook, schedule, deployment or statechart tooling was added. Existing Paper, CSS/React/TypeScript and public-boundary verification retain their responsibilities; dryer, formal checks and recurring work retain their current optional/advisory status.

## Portable refresh (2026-10-31)

Adapted the maintained local skill into this distributable package, retaining task framing, complete catch-ups, optional formal and recurring controls, source maintenance, staged-content integrity, and frontend routes. Local account, vault/CLI, home-directory, shared-host link, machine-policy history, and fixed response-format assumptions were generalized. This refresh uses inspected local source files; the dated upstream records above are provenance, not a claim of a new network sync or live integration check. The route checker is bundled and accepts configured roots without host-specific defaults.
