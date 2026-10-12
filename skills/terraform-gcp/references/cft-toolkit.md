# Cloud Foundation Toolkit (CFT) — Modules, CLI, Metadata & Policy

The **Cloud Foundation Toolkit** is Google's official IaC foundation: a curated set of production-ready Terraform modules following Google best practices, plus the `cft` developer CLI and a blueprint-quality standard. Treat it as the "standard library" for GCP Terraform — prefer reusing a CFT module over hand-rolling a resource graph, and prefer CFT's conventions (metadata, testing, lint) when authoring your own modules.

- Modules live in the **`terraform-google-modules`** GitHub org and on the Terraform Registry as `terraform-google-modules/<name>/google`.
- Blueprint catalog: <https://cloud.google.com/docs/terraform/blueprints/terraform-blueprints>.
- The toolkit repo (`GoogleCloudPlatform/cloud-foundation-toolkit`) holds the `cft` CLI, the blueprint-test framework, the blueprint tflint ruleset, and the metadata schema.

> **Always confirm the exact module `source` and current `version` on the Terraform Registry before pinning.** Module names below are stable, but pin versions explicitly (prod) per SKILL.md version policy — do not copy a version from memory.

## When to use a CFT module vs roll your own

| Situation | Do |
|-----------|-----|
| Standard service (VPC, GKE, Cloud SQL, project, IAM, GCS, …) | **Use the CFT module.** It encodes security defaults, ordering, and edge cases you'll otherwise rediscover in incidents. See the per-service module names in [GCP Service Playbooks](gcp-services.md). |
| Org/landing-zone scaffolding | Use **example-foundation** + **bootstrap** + **project-factory** (below). |
| Thin wrapper over 1–2 resources with no real logic | A small local module or raw resources is fine — a CFT module adds indirection without payoff. |
| Bleeding-edge / Preview feature a module hasn't adopted | Raw resource with `provider = google-beta` (see [dual-provider model](gcp-services.md#google-vs-google-beta--the-dual-provider-model)). |
| Authoring a module others will consume | Follow the **CFT module standard** (below): structure, `metadata.yaml`, blueprint tests, blueprint lint. |

## CFT vs Cloud Foundation Fabric

Both are Google-maintained module collections; they make different tradeoffs.

- **CFT** (`terraform-google-modules/*`): many **independently-versioned, single-purpose** modules published to the Registry, each with its own release cadence, tests, and `metadata.yaml`. Stable interfaces, broad adoption, good for composing piecemeal.
- **Fabric** (`GoogleCloudPlatform/cloud-foundation-fabric`): a **monorepo** of lighter-weight modules + end-to-end blueprints (FAST landing zone), faster-moving, more opinionated, consumed by Git ref rather than the Registry.

Rule of thumb: reach for **CFT** when you want Registry-pinned, independently-versioned building blocks; reach for **Fabric** when you want a cohesive, opinionated end-to-end foundation and are comfortable pinning to Git refs. The official comparison is `FABRIC-AND-CFT.md` in the Fabric repo.

## example-foundation: the reference landing zone

`terraform-example-foundation` is the canonical multi-stage GCP landing zone. The staged structure is the model to copy even if you don't use it verbatim — each stage is a **separate state** with its own lifecycle, and later stages consume earlier stages' outputs via `terraform_remote_state`:

| Stage | Purpose | Key modules |
|-------|---------|-------------|
| `0-bootstrap` | Seed project, Terraform state bucket, CI/CD SA + Workload Identity Federation, org-level permissions | `bootstrap` |
| `1-org` | Org-wide policies, folders, logging/billing exports, KMS, SCC | `org-policy`, `folders`, `log-export` |
| `2-environments` | Per-env (dev/nonprod/prod) folders, projects, baseline | `project-factory` |
| `3-networks` | Shared VPC(s), subnets, firewall, DNS, NAT, hybrid connectivity | `network`, `cloud-nat`, `cloud-dns` |
| `4-projects` | App/workload projects with Shared VPC attachment + IAM | `project-factory` |
| `5-app-infra` | Workload resources (the actual apps) | service modules |

Takeaways for any GCP estate: **bootstrap state + CI identity first**, **one state per stage/lifecycle**, **org → networks → projects → apps dependency direction**, and **WIF for CI from day one** (never long-lived SA keys).

## The `cft` CLI

Install:
```bash
# VERSION = "latest" or a semver like "v1.x.x"; PLATFORM = linux | darwin | windows
curl https://storage.googleapis.com/cft-cli/latest/cft-$(uname -s | tr A-Z a-z)-amd64 --output cft
chmod +x cft
```
(Note: the toolkit repo's `cli/README.md` lists only a subset of commands and is stale — the real surface is below.)

### Command surface

```
cft
├── version
├── scorecard              # score a GCP env against a policy library (CAI + Config Validator)
├── report                 # inventory reports from Cloud Asset Inventory exports
│   └── list-available-reports
├── launchpad generate     # generate IaC from CFT custom-resource YAML (org/folder hierarchy)
└── blueprint              # blueprint authoring toolchain
    ├── metadata           # generate/validate metadata.yaml + metadata.display.yaml
    ├── test               # blueprint integration-test runner (see blueprint-testing.md)
    │   ├── list           #   list auto-discovered + explicit tests
    │   ├── run            #   run tests (honours RUN_STAGE)
    │   ├── init           #   scaffold a new blueprint test
    │   ├── lint           #   lint the blueprint (blueprint tflint ruleset)
    │   └── convert        #   convert legacy kitchen/InSpec tests (experimental)
    ├── builds avgtime     # CI build timing stats
    └── catalog list       # list blueprint catalog entries
```

### `cft blueprint metadata` — the Blueprint metadata standard

Modules in the CFT ecosystem ship a **`metadata.yaml`** (auto-generated) and **`metadata.display.yaml`** (hand-authored UI metadata). This is what powers Registry/Marketplace discovery, the variable/output catalog, and required-roles/services declarations.

```bash
cft blueprint metadata -p <module-root> -d     # generate metadata.yaml + metadata.display.yaml
cft blueprint metadata -v                        # validate against the schema
```

`metadata.yaml` is a KRM-style document (`apiVersion`/`kind`/`metadata`/`spec`). The `spec` captures, among others:

- **`info`** — `title`, `source` (`repo`, `sourceType`, `dir`), `version`, `actuationTool` (terraform + version), `description`, `costEstimate`, `deploymentDuration`, `cloudProducts`, `softwareGroups`, `singleDeployment`.
- **`content`** — `architecture` (`diagrams`), `documentation`, `examples`, `subBlueprints`.
- **`interfaces`** — `variables` (with types/defaults/required), `variableGroups`, `outputs`.
- **`requirements`** — `roles` (IAM roles needed to deploy), `services` (APIs to enable), `providerVersions`.

Even if you don't publish to the Registry, generating `metadata.yaml` is a cheap way to get a **machine-checkable catalog of your module's inputs/outputs and its required roles + APIs** — useful for least-privilege CI SA scoping and for documenting the API-enablement prerequisites.

### `cft blueprint lint` & the blueprint tflint ruleset

`cft blueprint test lint` runs the **`tflint-ruleset-blueprint`** plugin, which enforces conventions for blueprint/sample quality on top of standard `tflint`:

| Rule | Enforces |
|------|----------|
| `terraform_required_version_range` | `required_version` must be a **bounded range** (`>= min, < max`), not unpinned and not pinned below a floor — keeps modules consumable across a known Terraform window. |
| `terraform_doc_sample_restricted_blocks` | Doc/example samples must be **self-contained root modules** — no `module {}` calls and no `variable {}` indirection (so a copied sample runs as-is). |
| `terraform_doc_sample_restricted_resources` | Doc samples must not use `null_resource` (no fake/placeholder resources in published examples). |

Pair this with the standard static stack from [Security & Compliance](security-compliance.md): `tflint` (general), `trivy config .`, `checkov -d .`.

### `cft scorecard` — policy posture of a live environment

`scorecard` audits an **existing** GCP org/folder/project against a **Config Validator policy library**, using **Cloud Asset Inventory (CAI)** as the source of truth (resources + IAM). It's the "are we compliant right now" complement to pre-apply policy checks.

```bash
cft scorecard \
  --policy-path <path-to>/policy-library \
  --bucket <gcs-bucket-with-CAI-export> \
  --target-organization <ORG_ID> --refresh \
  --output-format json
```
- Source the inventory from `--bucket` (GCS CAI export), `--dir-path` (local), or `--stdin` (CAI JSON) — exactly one.
- `--refresh` re-exports CAI for the `--target-project|-folder|-organization` (ADC must be a service account).
- `--output-format txt|json|csv`, `--output-metadata-fields`, `--workers N` for concurrency.

## Policy validation: Config Validator & `gcloud beta terraform vet`

CFT's policy story is **one policy library, two enforcement points** — the same constraints gate both a Terraform plan (pre-apply) and a live environment (post-hoc).

- **Policy library** = a directory of OPA-style **constraint templates** (the reusable rule logic) + **constraints** (the parameterized instances). Google ships a starter library (`GoogleCloudPlatform/policy-library`) with org-policy, IAM, networking, encryption, and CIS-benchmark constraints you clone and tune.
- **`gcloud beta terraform vet`** (the successor to the standalone `terraform-validator`) validates a **Terraform plan JSON** against the policy library **before apply** — wire it into the CI plan stage so violations fail the PR:
  ```bash
  terraform plan -out=tfplan.tfplan
  terraform show -json tfplan.tfplan > tfplan.json
  gcloud beta terraform vet tfplan.json --policy-library=./policy-library
  ```
- **`cft scorecard`** runs the **same** constraints against **CAI** for drift/posture auditing of what's actually deployed.

This gives a single source of policy truth across the lifecycle: author constraints once → enforce at plan time in CI → audit continuously in prod. It complements (does not replace) `trivy`/`checkov`, which are config-file scanners with their own built-in rule packs.

## The CFT module standard (when authoring modules)

If you write a module to CFT quality, the conventions are:

- **Structure:** `main.tf` / `variables.tf` / `outputs.tf` / `versions.tf`, plus `modules/` (submodules), `examples/` (each a runnable root module), `test/` (setup/fixtures/integration — see [blueprint-testing.md](blueprint-testing.md)), `metadata.yaml` + `metadata.display.yaml`, `README.md` (often generated from metadata + `terraform-docs`), `CHANGELOG.md`.
- **Versioning:** semantic versioning, automated releases (the repo uses release-please), `required_version` as a **bounded range** (per the blueprint lint rule), providers pinned.
- **Interfaces:** every variable typed + described + validated; secrets `sensitive`/write-only; outputs described and minimal (don't echo whole provider objects). See [Module Patterns](module-patterns.md).
- **Testing:** auto-discovered blueprint tests over every `examples/` dir, custom Go tests for non-trivial assertions, `DefaultVerify` idempotency on every example. See [blueprint-testing.md](blueprint-testing.md).
- **Lint clean:** `cft blueprint test lint` + `tflint` + `trivy` + `checkov` all green.

## See also

- [GCP Service Playbooks](gcp-services.md) — which CFT module solves each service, plus per-service gotchas.
- [Blueprint Testing](blueprint-testing.md) — the `tft`/`gcloud` integration-test framework CFT modules use.
- [Security & Compliance](security-compliance.md) — `trivy`/`checkov` and secrets handling.
- [CI/CD Workflows](ci-cd-workflows.md) — where `gcloud beta terraform vet` and the plan-artifact gate slot into pipelines.
