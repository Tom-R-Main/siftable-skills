# Siftable Skills

Siftable Skills gives a coding agent methods it can reuse: how to investigate a regression, review an interface, learn from another repository, or verify a change on the real application. There are 58 skills for engineering, design, planning, and writing.

Start with **Tometo Mode** if you want the agent to coordinate the work. It reads the project, selects the relevant skills, and carries an authorized change through verification. Use an individual skill when the job is narrower.

Each skill is a folder with a `SKILL.md` entrypoint and any references or helpers it needs. The installer follows links between sibling skills, so selecting a workflow brings its dependencies with it. You can install the library outside your application repository.

I believe that while frontier models are extremely capable, they often still revert to the mean of development practices rather than the very best practices. That's why I use language and framework specific skills to eke out performance gains wherever the agents work, to steer the models towards excellence.

## Start here

Use Python 3 and a reviewed checkout of this repository. Set the destination to a directory your agent discovers; `$HOME/.agents/skills` is one common choice.

```bash
# Preview Tometo Mode and its dependencies.
python3 scripts/install_skills.py --destination "$HOME/.agents/skills" \
  --skill tometo-mode

# Apply the same selection.
python3 scripts/install_skills.py --destination "$HOME/.agents/skills" \
  --skill tometo-mode --apply
```

Start a fresh agent task and ask:

```text
Use $tometo-mode to implement this feature and verify it through the real user path.
```

Check that the agent reads the skill. Files on disk establish installation; discovery depends on your agent and its configuration.

For the whole collection, omit `--skill tometo-mode`. For a smaller selection, use `--profile engineering`, `--profile languages`, or repeat `--skill NAME`. The engineering profile includes Tometo, verification, language skills, and Linux. The languages profile includes Kotlin and the existing language and frontend skills. Every selection includes its declared dependencies.

## What Tometo does

Tometo gives substantial work a consistent shape: understand the promise, inspect the code, choose the right method, implement within scope, and check the result at the boundary the user will use. A passing unit test supports a narrower claim than a verified user journey. The final report should make that difference clear.

The main routes are:

| Need | Skill |
| --- | --- |
| Find the cause of a regression | [pstack-investigate](skills/pstack-investigate/SKILL.md) |
| Decide interfaces and ownership | [pstack-architect](skills/pstack-architect/SKILL.md) |
| Review a diff | [pstack-interrogate](skills/pstack-interrogate/SKILL.md) |
| Exercise changed behavior | [pstack-verify](skills/pstack-verify/SKILL.md) |
| Make a verification recipe reusable | [pstack-create-verification-skill](skills/pstack-create-verification-skill/SKILL.md) |
| Learn a mechanism from another codebase | [repo-learn](skills/repo-learn/SKILL.md) |
| Improve interactions or challenge a layout | [emil-design-eng](skills/emil-design-eng/SKILL.md) and [break-ui](skills/break-ui/SKILL.md) |

The [Tometo entrypoint](skills/tometo-mode/SKILL.md) also routes task framing, catch-up reports, relevant language guidance, and optional formal or recurring-work checks. Those references load when the task needs them. A small fix can stay small.

You can ask for a narrower procedure directly:

```text
Use $rust to diagnose this lifetime issue with the repository's pinned toolchain.
Use $break-ui to stress-test this component with plausible worst-case data.
Use $repo-learn to compare recovery mechanisms before we choose one for this project.
```

The [skill guide](docs/skill-guide.md) explains how to choose, combine, document, and maintain skills, including a repo-learn example.

## Installation and updates

The installer reads a local checkout and uses Python's standard library. It stages complete packages, checks their contents and executable bits, and records hashes in `.siftable-skills.json` in the destination.

To refresh an installation, repeat its selection from your reviewed checkout:

```bash
python3 scripts/install_skills.py --destination "$HOME/.agents/skills" \
  --skill tometo-mode --apply --update
```

Updates replace only unchanged packages this installer already manages. It refuses unmanaged conflicts, local modifications, and symlink paths. Repeating the same installation is idempotent. Changing a selection leaves previously installed skills in place.

If an update is interrupted, preserve the transaction and follow the [recovery procedure](docs/cloud-setup.md#recover-an-interrupted-update). Packages installed by the earlier ZIP method are unmanaged; review them or choose an empty destination before migrating.

For cloud agents, follow [Cloud setup](docs/cloud-setup.md) and [Cloud startup instructions](docs/cloud-start-skill.md). Pin a reviewed commit in both setup and maintenance, then test discovery in a fresh task. Updating this repository does not change an existing cloud environment's pin.

## Tools and permissions

Skills provide procedures and bundled helpers. Compilers, browsers, native apps, MCP servers, provider CLIs, worker engines, and credentials come from your environment.

Browser and native-app work needs an available observation and action tool. Supervised workflows need a compatible, separately configured engine. Corpus retrieval needs an authorized backend and source collection. PDF, transcription, and Sentry workflows use the available document or service route. Each skill explains its requirements and reports missing capabilities.

The task still determines what the agent may do. Installing a skill grants no authority to deploy, delete data, send messages, publish, or spend money. Verification should name the artifact checked and the behavior observed; an unavailable integration remains unverified.

## Use a local Colophon profile

The [Colophon skill](skills/colophon/SKILL.md) connects to a separately installed Colophon runtime. Colophon owns the local registry and validates profiles; the adapter checks exported prompt receipts and Markdown candidates. The writing agent then uses the private guidance with the document's supported facts.

Set `COLOPHON_BIN` when the runtime is not on `PATH`. Create a private registry using the [generic example](skills/colophon/assets/profiles.example.json), with aliases pointing to profiles you configured locally. Registry lookup uses an explicit `--registry`, then `COLOPHON_PROFILES_FILE`, then the standard Colophon configuration directory. From a reviewed checkout:

```bash
python3 skills/colophon/scripts/colophon_adapter.py doctor
python3 skills/colophon/scripts/colophon_adapter.py profiles
python3 skills/colophon/scripts/colophon_adapter.py prompt my-voice \
  --output "$PRIVATE_PROMPT" --mode numeric --task rewrite
python3 skills/colophon/scripts/colophon_adapter.py \
  check-candidate README.md README.candidate.md
```

Choose an authorized private output path before exporting. Author profiles, source works, annotations, and guidance containing excerpts stay external to Git or untracked and ignored. This repository ships no author library. Export does not call a writing model, and a structural pass does not establish factual or literary quality. See the [runtime contract](skills/colophon/references/runtime-contract.md) for setup, privacy, receipts, and verification limits.

## Maintain the library

```bash
python3 scripts/validate_repo.py
python3 scripts/run_tests.py
```

Validation checks package metadata, resource links, symlinks, personal paths, excluded personal workflows, and likely secrets. Tests cover helpers, installer conflicts and recovery, offline cloud setup, and clean installations with only the declared dependencies. Filesystem mutation tests use disposable fixtures. Live provider, browser, cloud, and native-app behavior needs its own checks.

See [the authoring guide](docs/skill-guide.md#document-or-update-a-skill) before changing a package. Keep the procedure in the skill, conditional detail in references, and provenance in [skill-sources.json](skill-sources.json). The current refresh preserves reviewed public adapters and tested helpers where local sources contain private data or depend on a particular runtime.

Personal and project-specific workflows, material sourced through personal-workflow collections, private corpora, credentials, local binaries, and repository overlays are excluded. Source and license attribution stays with the packages.

## All skills

<!-- skill-inventory:start -->
58 skill packages are included.

| Skill | Scope |
| --- | --- |
| [`autoplan`](skills/autoplan/SKILL.md) | Compatibility route to Tometo Mode |
| [`aws-secrets-manager`](skills/aws-secrets-manager/SKILL.md) | Opaque runtime secret integration and metadata-only diagnosis |
| [`break-ui`](skills/break-ui/SKILL.md) | Schema-backed UI data, layout, and edge-state stress testing |
| [`c-systems-programming`](skills/c-systems-programming/SKILL.md) | C file I/O, processes, signals, and operating-system interfaces |
| [`cloud-environment-runtime`](skills/cloud-environment-runtime/SKILL.md) | Cloud execution, network, credential, and persistence context |
| [`colophon`](skills/colophon/SKILL.md) | Local voice-profile discovery, verified prompt export, and Markdown candidate checks |
| [`css`](skills/css/SKILL.md) | CSS, Tailwind, cascade, layouts, and computed styles |
| [`emil-design-eng`](skills/emil-design-eng/SKILL.md) | Frontend interaction, motion, accessibility, and performance |
| [`filesystem-lifecycle`](skills/filesystem-lifecycle/SKILL.md) | Evidence-based storage audits and guarded filesystem cleanup |
| [`footwork-tools`](skills/footwork-tools/SKILL.md) | Observation and action routes for browsers, apps, services, and artifacts |
| [`generating-design-references`](skills/generating-design-references/SKILL.md) | Design-reference generation through an approved image tool |
| [`gh-fix-ci`](skills/gh-fix-ci/SKILL.md) | GitHub Actions failure investigation and bounded remediation |
| [`gis-spatial-analysis`](skills/gis-spatial-analysis/SKILL.md) | Deterministic GIS, QGIS, cartography, and web-map workflows |
| [`go`](skills/go/SKILL.md) | Go implementation, review, modules, toolchains, and validation |
| [`grok-guide`](skills/grok-guide/SKILL.md) | Explicit Grok planning, replanning, and completion-audit integration |
| [`human-writing`](skills/human-writing/SKILL.md) | Public prose with factual, source, voice, and text-hygiene checks |
| [`investigate`](skills/investigate/SKILL.md) | Compatibility route to pstack investigation |
| [`kotlin`](skills/kotlin/SKILL.md) | Kotlin APIs, coroutines, Gradle, Android, and multiplatform work |
| [`linux`](skills/linux/SKILL.md) | Kernel, userspace, services, and desktop integration |
| [`mermaid`](skills/mermaid/SKILL.md) | Mermaid diagram rendering through the selected available route |
| [`opengl-c-graphics`](skills/opengl-c-graphics/SKILL.md) | Core-profile OpenGL in C, shaders, buffers, and GPU diagnosis |
| [`paper-design`](skills/paper-design/SKILL.md) | Paper design inspection, editing, export, and handoff |
| [`pdf`](skills/pdf/SKILL.md) | PDF extraction, creation, manipulation, rendering, and verification |
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
| [`repo-learn`](skills/repo-learn/SKILL.md) | Source-grounded engineering patterns and explicit evidence stores |
| [`review`](skills/review/SKILL.md) | Compatibility route to pstack independent review |
| [`rust`](skills/rust/SKILL.md) | Rust ownership, errors, async, unsafe/FFI, toolchains, and Cargo gates |
| [`screenshot`](skills/screenshot/SKILL.md) | Scoped desktop, app, window, and region capture |
| [`search-local-corpus`](skills/search-local-corpus/SKILL.md) | Backend-neutral retrieval with source locators and citations |
| [`searching-design-corpus`](skills/searching-design-corpus/SKILL.md) | Specialized design and systems corpus retrieval through an adapter |
| [`semantic-density`](skills/semantic-density/SKILL.md) | Precise internal notes, prompts, and model-facing instructions |
| [`sentry`](skills/sentry/SKILL.md) | Read-only issue and event investigation through configured access |
| [`sharp-edit`](skills/sharp-edit/SKILL.md) | Concise business writing with preserved facts, certainty, and voice |
| [`soc2-compliance`](skills/soc2-compliance/SKILL.md) | SOC 2 scope, controls, evidence, readiness, and gap assessment |
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
| [`transcribe`](skills/transcribe/SKILL.md) | Audio/video transcription with timestamps and optional speaker labels |
| [`typescript`](skills/typescript/SKILL.md) | TypeScript types, compiler behavior, modules, and build/test gates |
| [`zig`](skills/zig/SKILL.md) | Version-aware Zig APIs, allocation, I/O, FFI, and measured optimization |
<!-- skill-inventory:end -->

## Source and license

Maintained by [Thomas Main](https://github.com/Tom-R-Main). See the [MIT License](LICENSE), [third-party notices](THIRD_PARTY_NOTICES.md), and [source records](skill-sources.json) for the origin and terms of adapted material. As the name Tometo mode suggests, the basic way it works is heavily based on Poteto mode by Lauren Tan and her [skills work](https://github.com/cursor/plugins/tree/main/pstack/skills).
