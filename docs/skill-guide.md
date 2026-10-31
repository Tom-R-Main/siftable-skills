# Use and maintain the skills

A skill should make the next decision easier. Choose one for the method the task needs, read its entrypoint, and follow its relevant references. Installing more skills does not establish that an agent selected them or that their tools work in your environment.

## Choose the route

Use [Tometo Mode](../skills/tometo-mode/SKILL.md) for a substantial engineering task that spans methods. It coordinates the work and delegates toolchain details to the matching language or domain skill. Invoke an individual skill for a focused investigation, review, design task, or writing job.

Keep the task's mode explicit. An audit produces findings. A plan produces a plan. An implementation request can continue through scoped fixes and verification. External effects still need task authorization. Repeating a submission to obtain evidence can duplicate the effect; reconcile uncertain state first.

For changed behavior, [pstack-verify](../skills/pstack-verify/SKILL.md) starts from the user's promise and actual entry point. Use the existing project driver. When a reusable driver is missing, [create a project-local verification recipe](../skills/pstack-create-verification-skill/SKILL.md); when it has drifted, [maintain it](../skills/pstack-maintain-verification-skill/SKILL.md). Record runtime access that remains unavailable.

Load optional references for a concrete reason. Formal checks address a selected invariant; recurring-work controls address triggers, deduplication, handoffs, and recovery. Neither is a prerequisite for an ordinary feature change.

## Learn from another repository

[Repo-learn](../skills/repo-learn/SKILL.md) helps answer a transfer question: which mechanism in a source repository could improve a decision in the target project? Read the source checkout without modifying it, identify a counterexample, and test the proposed transfer before relying on it.

The bundled helper uses Python's standard library and SQLite with FTS5. Git supplies revision metadata when available. It does not fetch repositories, execute their code, or choose a global store.

Set these variables to reviewed paths before running the example. The store must be an approved output directory outside the reference checkout; `REPO_LEARN_DIR` is the installed skill directory.

```bash
python3 "$REPO_LEARN_DIR/scripts/repo_learn.py" --store "$PATTERN_STORE" doctor
python3 "$REPO_LEARN_DIR/scripts/repo_learn.py" --store "$PATTERN_STORE" \
  query 'recovery after interrupted writes'
python3 "$REPO_LEARN_DIR/scripts/repo_learn.py" --store "$PATTERN_STORE" \
  catalog "$REFERENCE_REPO"
```

Search a bounded area, then capture the lines that support the mechanism:

```bash
python3 "$REPO_LEARN_DIR/scripts/repo_learn.py" --store "$PATTERN_STORE" \
  find "$REFERENCE_REPO" 'checkpoint' --glob 'src/*.py' --limit 12
python3 "$REPO_LEARN_DIR/scripts/repo_learn.py" --store "$PATTERN_STORE" \
  read "$REFERENCE_REPO" src/recovery.py --start 20 --end 70 \
  --question 'What prevents a retry from skipping an unfinished write?'
```

Replace the example path and line range with source that actually exists. A search result includes coverage and continuation information. An empty or partial result does not prove the mechanism is absent. A captured snippet identifies the bytes read; changed callers or configuration can still invalidate a conclusion.

Use the returned evidence IDs in a pattern card following the [record schema](../skills/repo-learn/references/toolchain.md#pattern-record). Include the mechanism, when it applies, when it fails, its tradeoffs, and the target check that could disprove the transfer. Query existing cards before adding one; extend the existing lesson when it already covers the same invariant.

```bash
python3 "$REPO_LEARN_DIR/scripts/repo_learn.py" --store "$PATTERN_STORE" \
  add-pattern "$PATTERN_CARD"
python3 "$REPO_LEARN_DIR/scripts/repo_learn.py" --store "$PATTERN_STORE" verify
python3 "$REPO_LEARN_DIR/scripts/repo_learn.py" --store "$PATTERN_STORE" export
```

SQLite is canonical; JSON files and `patterns.md` are inspectable projections. If the helper reports that a card committed but its projection failed, retry the identical card to repair that projection. A conflicting payload needs a new version. Commands can write catalog, evidence, or journal records, so even a query needs an approved store.

Keep evidence private unless publication is authorized. Filename exclusions are a limited safeguard, not comprehensive secret detection. This library ships no seeded personal store or source corpus. Source inspection, model probes, fixture tests, and real-target execution should remain separate claims.

## Document or update a skill

Read the maintained source and existing callers before editing. A package lives under `skills/<name>/`; its `SKILL.md` frontmatter names the same directory and briefly describes when the skill helps.

```yaml
---
name: example-skill
description: Describe the actual capability and the task that should select it.
---
```

Write the decision-changing procedure in the entrypoint. Link substantial conditional guidance from `references/` where it becomes relevant. Add scripts when repeated mechanics justify them, and validate their observable behavior. Avoid repeating the whole procedure in the README.

Make the package usable after installation:

- Resolve helpers and references from the loaded skill directory. Runtime use must not depend on repository-root files or a particular user's home directory.
- Link required sibling resources with relative Markdown links. The installer derives dependency closure from declared resources; mentioning a skill name alone does not declare that dependency.
- State which tools must be configured separately. A bundled adapter, schema, or source description does not supply a runtime or prove access.
- Preserve source attribution, license notices, and version identity. Do not copy private corpora, credentials, local binaries, personal workflows, or project-specific configuration into a public package.
- Update the README inventory and `skill-sources.json` when packages or source records change. A source hash identifies the compared entrypoint; it does not certify the public adaptation or live integration.

Run the repository checks from its root:

```bash
python3 scripts/validate_repo.py
python3 scripts/run_tests.py
```

The clean-install checks exercise independent packages alone and workflows with their declared sibling dependencies. Installer tests challenge unmanaged conflicts, local edits, interruptions, and recovery. These are package and fixture results. A new live integration still needs observation on its intended surface.

The source of these contracts is the [installer](../scripts/install_skills.py), [resource validator](../scripts/validate_repo.py), [clean-install checks](../scripts/test_clean_install.py), and [repo-learn contract](../skills/repo-learn/references/toolchain.md). Check those owners when behavior changes.
