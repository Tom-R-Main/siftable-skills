# Siftable Skills

A personal skill library for coding, verification, planning, and writing. The collection includes Tometo Mode, the pstack workflows, language-specific engineering skills, and optional routes to browsers, design tools, local corpora, and supervised workers.

Each package lives under `skills/<name>/`. It contains instructions and any bundled scripts, references, assets, or tests. Workflow packages can depend on sibling skills through explicit relative resource links; the installer includes their full dependency closure. Installed skills use their own package and sibling resources, without repository-root files at runtime.

## Install from a reviewed checkout

Use Python 3's standard-library installer after obtaining a reviewed local checkout:

```bash
# Preview all skills without changing files.
python3 scripts/install_skills.py --destination "$HOME/.agents/skills"

# Install all skills and verify the resulting files.
python3 scripts/install_skills.py --destination "$HOME/.agents/skills" --apply

# Select a workflow and its declared dependencies.
python3 scripts/install_skills.py --destination "$HOME/.agents/skills" \
  --skill tometo-mode --skill zig --apply

# Replace only unchanged packages previously managed by this installer.
python3 scripts/install_skills.py --destination "$HOME/.agents/skills" --apply --update
```

The destination is required. `--profile all` is the default; `--profile engineering` selects Tometo Mode, pstack workflows, and language skills, while `--profile languages` selects the language and frontend skills. Repeated `--skill NAME` arguments select individual packages. Both profiles and individual selections include declared sibling dependencies.

The installer stages complete directories, hashes installed contents and executable bits, and stores `.siftable-skills.json` in the destination root. It refuses symlinks, unmanaged conflicts, and managed packages with local changes. Repeating an installation with unchanged sources is idempotent. Updates roll back on ordinary failures and leave a recovery transaction if interrupted; see the [recovery procedure](docs/cloud-setup.md#recover-an-interrupted-update).

Packages copied by the earlier cloud ZIP installer are unmanaged by this installer. Use an empty configured skill directory or review and relocate conflicting packages before migrating. Installation does not remove packages when a selection changes.

For a durable personal library across cloud repositories, follow [Cloud setup](docs/cloud-setup.md) and [Cloud startup instructions](docs/cloud-start-skill.md). They install from an immutable Git commit into the cloud user skill directory during setup and maintenance, while preserving the application repository and its existing build setup. Saving settings, publishing the environment, and checking fresh-task discovery happen in the cloud environment.

## Included skills

<!-- skill-inventory:start -->
45 skill packages are included.

| Skill | Scope |
| --- | --- |
| [`autoplan`](skills/autoplan/SKILL.md) | Compatibility route to Tometo Mode |
| [`c-systems-programming`](skills/c-systems-programming/SKILL.md) | C file I/O, processes, signals, and operating-system interfaces |
| [`cloud-environment-runtime`](skills/cloud-environment-runtime/SKILL.md) | Cloud execution, network, credential, and persistence context |
| [`css`](skills/css/SKILL.md) | CSS, Tailwind, cascade, layouts, and computed styles |
| [`filesystem-lifecycle`](skills/filesystem-lifecycle/SKILL.md) | Evidence-based storage audits and guarded filesystem cleanup |
| [`footwork-tools`](skills/footwork-tools/SKILL.md) | Observation and action routes for browsers, apps, services, and artifacts |
| [`generating-design-references`](skills/generating-design-references/SKILL.md) | Design-reference generation through an approved image tool |
| [`gh-fix-ci`](skills/gh-fix-ci/SKILL.md) | GitHub Actions failure investigation and bounded remediation |
| [`go`](skills/go/SKILL.md) | Go implementation, review, modules, toolchains, and validation |
| [`grok-guide`](skills/grok-guide/SKILL.md) | Explicit Grok planning, replanning, and completion-audit integration |
| [`human-writing`](skills/human-writing/SKILL.md) | Public prose with factual, source, voice, and text-hygiene checks |
| [`investigate`](skills/investigate/SKILL.md) | Compatibility route to pstack investigation |
| [`mermaid`](skills/mermaid/SKILL.md) | Mermaid diagram rendering through the selected available route |
| [`opengl-c-graphics`](skills/opengl-c-graphics/SKILL.md) | Core-profile OpenGL in C, shaders, buffers, and GPU diagnosis |
| [`paper-design`](skills/paper-design/SKILL.md) | Paper design inspection, editing, export, and handoff |
| [`pgvector-postgres`](skills/pgvector-postgres/SKILL.md) | PostgreSQL vector search, plans, recall, indexes, and migrations |
| [`plan`](skills/plan/SKILL.md) | Evidence-grounded plans and visual sequencing |
| [`plan-eng-review`](skills/plan-eng-review/SKILL.md) | Compatibility route to pstack architecture review |
| [`playwright`](skills/playwright/SKILL.md) | Browser automation through the configured Playwright route |
| [`predict-future`](skills/predict-future/SKILL.md) | Scoreable probabilistic forecasts and decision update triggers |
| [`pstack-architect`](skills/pstack-architect/SKILL.md) | Interfaces, ownership, module boundaries, and executable change plans |
| [`pstack-create-verification-skill`](skills/pstack-create-verification-skill/SKILL.md) | Project-local verification harness creation and execution |
| [`pstack-interrogate`](skills/pstack-interrogate/SKILL.md) | Independent diff scrutiny, traceable findings, and review verdicts |
| [`pstack-investigate`](skills/pstack-investigate/SKILL.md) | Defect reproduction, competing causes, and bounded verified fixes |
| [`pstack-maintain-verification-skill`](skills/pstack-maintain-verification-skill/SKILL.md) | Verification harness audits against source and live behavior |
| [`pstack-verify`](skills/pstack-verify/SKILL.md) | Verification on real apps, CLIs, services, or artifacts |
| [`react-best-practices`](skills/react-best-practices/SKILL.md) | React and Next.js rendering, hooks, bundles, and measured performance |
| [`review`](skills/review/SKILL.md) | Compatibility route to pstack independent review |
| [`rust`](skills/rust/SKILL.md) | Rust ownership, errors, async, unsafe/FFI, toolchains, and Cargo gates |
| [`search-local-corpus`](skills/search-local-corpus/SKILL.md) | Backend-neutral retrieval with source locators and citations |
| [`searching-design-corpus`](skills/searching-design-corpus/SKILL.md) | Specialized design and systems corpus retrieval through an adapter |
| [`semantic-density`](skills/semantic-density/SKILL.md) | Precise internal notes, prompts, and model-facing instructions |
| [`sharp-edit`](skills/sharp-edit/SKILL.md) | Concise business writing with preserved facts, certainty, and voice |
| [`strategic-decision-mapping`](skills/strategic-decision-mapping/SKILL.md) | Actors, incentives, moves, countermoves, and next decisions |
| [`supervise`](skills/supervise/SKILL.md) | Compatibility route to supervised coding |
| [`supervise-fable`](skills/supervise-fable/SKILL.md) | Fable planning/review with isolated implementation workers |
| [`supervise-kimi`](skills/supervise-kimi/SKILL.md) | Kimi design implementation with independent supervised review |
| [`supervise-opus`](skills/supervise-opus/SKILL.md) | Opus planning/review with isolated implementation workers |
| [`supervise-workflow`](skills/supervise-workflow/SKILL.md) | Supervised workflow contracts, worker isolation, verification, and recovery |
| [`teach`](skills/teach/SKILL.md) | Concept and skill teaching grounded in the current workspace |
| [`terraform-gcp`](skills/terraform-gcp/SKILL.md) | Google Cloud Terraform/OpenTofu, IAM, state, services, and verification |
| [`thinking-scientific-method`](skills/thinking-scientific-method/SKILL.md) | Falsifiable hypotheses, predictions, tests, and revision |
| [`tometo-mode`](skills/tometo-mode/SKILL.md) | Coordinated engineering with specialty skills and executable verification |
| [`typescript`](skills/typescript/SKILL.md) | TypeScript types, compiler behavior, modules, and build/test gates |
| [`zig`](skills/zig/SKILL.md) | Version-aware Zig APIs, allocation, I/O, FFI, and measured optimization |
<!-- skill-inventory:end -->

## Use a skill

Explicit invocation asks the agent to read and apply a particular procedure:

```text
Use $tometo-mode to implement this feature and verify it on the real application.
Use $zig to diagnose this allocator boundary using the repository's pinned toolchain.
Use $typescript to review this narrowing error and run the relevant compiler gates.
Use $rust to review this async lifetime issue and verify the bounded fix.
```

Some harnesses also discover skills from their descriptions. Confirm discovery in a fresh task after installation; files on disk alone do not prove a harness loaded them. Read each selected `SKILL.md` before using its scripts, and follow the user's scope and authorization rules.

## Optional integrations

Installation supplies skill files and bundled helpers. It does not provision compilers, browser engines, native applications, provider CLIs, MCP servers, credentials, corpus contents, or worker engines.

| Route | What must be available separately |
| --- | --- |
| Tometo Mode and pstack | The selected repository's build/runtime tools and an observation surface for real verification; delegation requires an available authorized worker tool |
| Language skills | The repository's selected compiler, package manager, libraries, and build contract |
| Footwork and Playwright | A configured browser/CLI/service observation surface; native Mac routes require a Mac |
| Paper and design references | The relevant MCP or approved image-generation capability |
| Grok and supervised workers | A user-configured provider/worker engine that implements the documented request contracts; bundled adapters do not supply an engine |
| Corpus retrieval | A user-configured retrieval backend and permitted corpus; private data is not bundled |
| Terraform GCP | Terraform/OpenTofu and separately configured authorized Google Cloud access |
| Cloud environment runtime | An actual configured cloud task and its supported network/credential tools |

When an integration is absent, the skills require the agent to identify the missing capability and continue work supported by the current environment. Skills never grant deployment, deletion, secret access, messaging, or publication authority.

`search-local-corpus` exposes a backend-neutral JSON interface. `searching-design-corpus` retains the specialized design-corpus route behind its documented adapter. See their bundled contracts before supplying a backend.

## Validate changes

```bash
python3 scripts/validate_repo.py
python3 scripts/run_tests.py
```

Static validation checks frontmatter, package names, relative resources, symlinks, personal paths, and likely secrets. It does not execute new integration scripts to infer whether a capability exists. The test runner separately exercises the original allowlisted `--help` contracts, deterministic package tests, installer conflict and recovery cases, and the documented cloud setup against an offline Git fixture.

Clean-install tests copy independent skills alone and workflows with only their declared sibling closure into temporary installation trees. Mutation tests operate on fixtures. These checks establish package portability and installer behavior; live provider, cloud, browser, and native-app integrations need verification on their actual surfaces.

## Source and license

The collection is maintained by [Thomas Main](https://github.com/Tom-R-Main). See the [MIT License](LICENSE), [Third-party notices](THIRD_PARTY_NOTICES.md), and `skill-sources.json` for provenance and adapted components. Source refreshes preserve the selected local workflow and portable adapters; they do not silently change the pinned commit in a published cloud environment.
