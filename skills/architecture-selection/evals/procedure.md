# Repeatable architecture-selection evaluation

Use when maintaining or assessing the skill; this is not a prerequisite for application architecture work. These are synthetic design exercises, not runtime tests or historical-port reproductions. Inputs live in `prompts.json`; expectations are separate in `rubric.md`.

## Run

1. Pin the skill revision or file hashes, model/version, harness, available tools, instructions, sampling settings where controllable, and output limit. Use the same setup for both arms. Declare any unavoidable differences, including automatic host skill discovery.
2. Give a fresh baseline context one request from `prompts.json` without this skill. Give a separate fresh assisted context the same request plus `SKILL.md` and relevant guidance references. Neither receives the rubric, prior outputs, historical outcome or intended winner. Do not let an assisted context recursively load the evaluation material. Keep actions design-only unless an evaluation explicitly supplies an authorized executable fixture.
3. Prefer a fresh context per case; run paired variants separately to avoid priming. A batched context per arm is a cheaper smoke check: disclose cross-case priming and do not count its answers as independent trials. Agent runs still require the caller's available delegation and budget authority.
4. Preserve raw answers outside distributed skill packages. Randomize/anonymize arm labels for a reviewer when practical; otherwise disclose that grading was unblinded. Grade every case and pair using `rubric.md`, citing the actual response and any ambiguity.
5. Compare constraint preservation, viable alternatives, mechanism-based reasoning, decisive checks and reversal conditions. Record verbosity, unnecessary process and re-opening of settled architecture as costs, not just missing cautions.

## Interpret

A pass shows the sampled response met the specified decision properties. It does not show that the proposed system works, that the skill selected a globally optimal stack, or that the skill caused an improvement. A baseline can already pass. Report ties, regressions and negative findings. Multiple cases in one context and repeated samples from one model are not independent models.

Before adding stronger priors, repeat cases across enough fresh runs to distinguish a consistent omission from one answer; choose a meaningful sample for the claim rather than a universal run count. Broaden models only within explicit authorization. Add new cases for observed failures and leave existing cases intact when revising the skill, so repairs can be checked for regressions.

Historical migration cases can supplement the suite. Supply original constraints before revealing outcomes, note possible model recognition, and assess whether the questions expose the decisive tradeoff rather than whether the answer names the historical language. Keep source-backed feasibility, design-output evaluation, executed prototypes and production results distinct.
