---
name: terraform-gcp
description: Use when writing, reviewing, or debugging Terraform/OpenTofu for Google Cloud Platform - GCP provider choice (google vs google-beta), GCS state, Workload Identity Federation, IAM, and per-service playbooks for Cloud Run, Cloud SQL, GKE, GCS, networking, Pub/Sub, BigQuery, Secret Manager; plus the Cloud Foundation Toolkit (CFT) modules, cft CLI, blueprint testing, metadata, and policy validation; CI, tests, scans, and state ops with version-aware guards.
license: Apache-2.0
metadata:
  author: Anton Babenko
  version: 1.18.0
---

# Terraform GCP Skill

Diagnose-first guidance for Terraform and OpenTofu on Google Cloud Platform. Core file is a workflow; depth lives in references loaded on demand. GCP is the default cloud in this installed variant.

## Navigate This Skill

Three ways in — pick the one that matches the task, then load only the matching reference.

**By GCP service** — provisioning or debugging a specific surface? Go straight to its playbook in [GCP Service Playbooks](references/gcp-services.md) (canonical resources, the CFT module that already solves it, destroy/safety gotchas, beta notes):

| | | | |
|---|---|---|---|
| [Projects / Factory](references/gcp-services.md#projects--project-factory) | [IAM & SAs](references/gcp-services.md#iam--service-accounts) | [Org Policy / Folders](references/gcp-services.md#org-policy-folders--resource-hierarchy) | [VPC Networking](references/gcp-services.md#vpc-networking) |
| [Cloud DNS](references/gcp-services.md#cloud-dns) | [Load Balancing](references/gcp-services.md#load-balancing) | [Compute (VMs)](references/gcp-services.md#compute-engine-vms) | [GKE](references/gcp-services.md#gke-kubernetes-engine) |
| [Cloud Run](references/gcp-services.md#cloud-run) | [Cloud Functions](references/gcp-services.md#cloud-functions) | [Cloud SQL](references/gcp-services.md#cloud-sql) | [AlloyDB/Spanner/Firestore](references/gcp-services.md#alloydb-spanner-firestore-bigtable) |
| [BigQuery](references/gcp-services.md#bigquery) | [Memorystore](references/gcp-services.md#memorystore-redis) | [Cloud Storage (GCS)](references/gcp-services.md#cloud-storage-gcs) | [Artifact Registry](references/gcp-services.md#artifact-registry) |
| [Secret Manager](references/gcp-services.md#secret-manager) | [Cloud KMS](references/gcp-services.md#cloud-kms) | [Pub/Sub](references/gcp-services.md#pubsub) | [Eventarc/Workflows](references/gcp-services.md#eventarc--workflows) |
| [Observability](references/gcp-services.md#observability-logging-monitoring-log-export) | [Destroy-safety cheat sheet](references/gcp-services.md#destroy-safety-cheat-sheet) | [google vs google-beta](references/gcp-services.md#google-vs-google-beta--the-dual-provider-model) | |

**By Cloud Foundation Toolkit capability** — using or authoring CFT modules, or wiring GCP-native quality gates:

- [CFT modules & ecosystem](references/cft-toolkit.md) — when to reuse a `terraform-google-modules` module vs roll your own, CFT vs Fabric, the [example-foundation landing zone](references/cft-toolkit.md#example-foundation-the-reference-landing-zone) stages.
- [`cft` CLI](references/cft-toolkit.md#the-cft-cli) — `scorecard`, `blueprint metadata`, `blueprint test`, `launchpad`, `report`.
- [Blueprint metadata standard](references/cft-toolkit.md#cft-blueprint-metadata--the-blueprint-metadata-standard) — `metadata.yaml` (inputs/outputs catalog + required roles/APIs).
- [Blueprint testing framework](references/blueprint-testing.md) — `tft`/`gcloud` integration tests asserting live GCP state + idempotency.
- [Policy validation](references/cft-toolkit.md#policy-validation-config-validator--gcloud-beta-terraform-vet) — `gcloud beta terraform vet` at plan time + `cft scorecard` on live env, one policy library.

**By failure mode** — debugging something broken? Use the [Diagnose Before You Generate](#diagnose-before-you-generate) routing table below.

**Cross-cutting references:** [Testing](references/testing-frameworks.md) · [Modules](references/module-patterns.md) · [CI/CD](references/ci-cd-workflows.md) · [Security](references/security-compliance.md) · [State](references/state-management.md) · [Code Patterns](references/code-patterns.md) · [Code Intelligence](references/code-intelligence-lsp.md) · [Quick Reference](references/quick-reference.md)

## Response Contract

Every Terraform/OpenTofu response must include:

1. **Assumptions & version floor** — runtime (`terraform` or `tofu`), exact version, GCP provider source/version, state backend, execution path (local/CI/Cloud/Atlantis), project/folder/org scope, region/zone, environment criticality. State assumptions explicitly if the user did not provide them.
2. **Risk category addressed** — one or more of: identity churn, secret exposure, blast radius, CI drift, compliance gaps, state corruption, provider upgrade risk, testing blind spots.
3. **Chosen remediation & tradeoffs** — what was chosen, what was traded off, why.
4. **Validation plan** — exact commands (`fmt -check`, `validate`, `plan -out`, policy check) tailored to runtime and risk tier.
5. **Rollback notes** — for any destructive or state-mutating change: how to undo, what evidence to keep.

Never recommend direct production apply without a reviewed plan artifact and approval.

Never run `terraform destroy` (targeted or full) without first running `terraform plan -destroy` and showing the user every resource that will be deleted — including implicit dependents pulled in via locals or `for_each`. Get explicit confirmation before proceeding. Never use `-auto-approve` on destroy.

## Workflow

1. **Capture execution context** — runtime+version, provider source/version, GCP project/folder/org, region/zone, backend, execution path, environment criticality.
2. **Diagnose failure mode(s)** using the routing table below. If intent spans categories, load both references.
3. **Load only the matching reference file(s)** — do not preload depth the task does not need.
4. **Propose fix with risk controls** — why this addresses the mode, what could still go wrong, guardrails (tests/approvals/rollback).
5. **Generate artifacts** — HCL, migration blocks (`moved`, `import`), CI changes, policy rules.
6. **Validate before finalizing** — run validation commands tailored to risk tier.
7. **Emit the Response Contract** at the end.

## GCP Default Operating Model

- Prefer `hashicorp/google` and `hashicorp/google-beta` for production GCP unless the user explicitly asks for an OpenTofu-native fork. They are the established Google Cloud providers and have the broadest docs, release history, module ecosystem, and support path.
- Treat `opentofu/google` as experimental or opt-in until the repo's release cadence, security policy, registry behavior, and compatibility story are proven for the target workload. If selected, call out provider-source risk separately from the Terraform-vs-OpenTofu CLI decision.
- For OpenTofu on GCP, do not assume the provider source must change. First verify whether the existing configuration uses `hashicorp/google`; keep it if it resolves and the organization has not chosen the `opentofu/google` fork.
- **`google` vs `google-beta` are two distinct providers, not a flag.** `google` = GA only; `google-beta` = GA **plus** Preview resources/fields (marked in the docs), sending all requests to beta endpoints. They release in lockstep (identical version numbers). Use both in one config and select per-resource with `provider = google-beta`; omitting `provider` silently defaults to `google`. A "documented field has no effect" bug is usually a missing `provider = google-beta`. Full rules in [Service Playbooks: dual-provider model](references/gcp-services.md#google-vs-google-beta--the-dual-provider-model).
- **Prefer a maintained Cloud Foundation Toolkit module over a hand-rolled resource graph** for standard services (VPC, GKE, Cloud SQL, project, IAM, GCS, …). CFT modules encode security defaults, dependency ordering, and edge cases you'll otherwise rediscover in incidents. See [GCP Service Playbooks](references/gcp-services.md) for the module per service and [CFT Toolkit](references/cft-toolkit.md#when-to-use-a-cft-module-vs-roll-your-own) for the reuse decision.
- **Stateful GCP resources guard against destroy and you must consciously disable the guard.** Cloud SQL/GKE/BigQuery default `deletion_protection = true`; GCS `force_destroy = false`; KMS keys cannot be deleted at all. Before any destroy or replace-forcing change on data-bearing resources, plan and check the [Destroy-Safety Cheat Sheet](references/gcp-services.md#destroy-safety-cheat-sheet).
- Default backend for team/prod GCP is `gcs` with versioning, uniform bucket-level access, retention/soft-delete policy where appropriate, and optional CMEK configured on the bucket. Never use local state for shared or production GCP.
- Prefer Application Default Credentials for local reads/plans and Workload Identity Federation for CI/CD. Avoid long-lived service-account JSON keys; if unavoidable, mark them temporary, never commit them, and never print their contents.
- Model least privilege with explicit service accounts and IAM bindings. Avoid broad primitive roles (`roles/editor`, `roles/owner`) unless the task is explicitly bootstrap-only and the blast radius is documented.
- For Cloud Run, Cloud SQL, Secret Manager, Artifact Registry, and IAM changes, assume production impact unless the environment is clearly non-prod. Require a reviewed plan artifact before apply.
- Use GCP-native validation where relevant: `gcloud beta terraform vet` or policy-controller checks for policy libraries, plus `terraform/tofu fmt -check`, `validate`, `plan -out`, `trivy config .`, and `checkov -d .`.

## Diagnose Before You Generate

| Failure category | Symptoms | Primary references |
|------------------|----------|--------------------|
| **Identity churn** | Resource addresses shift after refactor, `count` index churn, missing `moved` blocks | [Code Patterns: count vs for_each](references/code-patterns.md#count-vs-for_each-deep-dive), [Code Patterns: moved blocks](references/code-patterns.md#moved-blocks-terraform-11), [Code Patterns: LLM mistakes](references/code-patterns.md#llm-mistake-checklist--code-patterns) |
| **Secret exposure** | Secrets in defaults, state, logs, CI artifacts | [Security & Compliance](references/security-compliance.md), [Code Patterns: write-only](references/code-patterns.md#write-only-arguments-terraform-111), [State Management](references/state-management.md) |
| **Blast radius** | Oversized stacks, shared prod/non-prod state, unsafe applies | [State Management](references/state-management.md), [Module Patterns](references/module-patterns.md) |
| **Destroy cascade** | Targeted destroy deletes more than expected; locals referencing a targeted resource make all `for_each` consumers implicit dependents | Response Contract: plan-destroy first; [State Management: Safe Destroy](references/state-management.md#safe-destroy-protocol) |
| **CI drift** | Local plan ≠ CI plan, apply without reviewed artifact, unpinned versions | [CI/CD Workflows](references/ci-cd-workflows.md), [Code Patterns: versions](references/code-patterns.md#version-management) |
| **Compliance gaps** | Missing policy stage, no approval model, no evidence retention | [Security & Compliance](references/security-compliance.md), [CI/CD Workflows](references/ci-cd-workflows.md) |
| **Testing blind spots** | Plan-only validation of computed values, set-type indexing, mock/real confusion | [Testing Frameworks](references/testing-frameworks.md) |
| **State corruption / recovery** | Stuck lock, backend migration, drift reconciliation | [State Management](references/state-management.md) |
| **Provider upgrade risk** | Breaking-change provider bump, unpinned modules | [Code Patterns: versions](references/code-patterns.md#version-management), [Module Patterns](references/module-patterns.md) |
| **Provider lifecycle** | Removing a provider with resources still in state, orphaned resources, `removed` block usage | [State Management: Provider Removal](references/state-management.md#provider-removal) |
| **Bootstrap / orchestration misuse** | `null_resource` + `local-exec` for bootstrap, `remote-exec` for setup scripts, provisioner stdout leaking secrets in CI logs | [Code Patterns: Provisioners as Last Resort](references/code-patterns.md#provisioners-as-last-resort) |
| **Navigation / safe-rename blind spots** | Cannot locate symbol defs/refs semantically, value-symbol rename done as blind text replace, grep-only refactor missing refs, hallucinated `rg` shim | [Code Intelligence](references/code-intelligence-lsp.md#terraform-ls-capability-matrix) |
| **Cross-cloud / provider mapping** | "What's the Azure/GCP equivalent of X", picking a backend/auth model per cloud | [State Management: Cross-cloud equivalents](references/state-management.md#cross-cloud-equivalents) |
| **Accidental destroy of stateful GCP resources** | `destroy`/replace fails or (worse) succeeds on Cloud SQL, GKE, BigQuery, GCS; `deletion_protection`/`force_destroy` confusion | [Service Playbooks: Destroy-Safety Cheat Sheet](references/gcp-services.md#destroy-safety-cheat-sheet), [Service Playbooks: Cloud SQL](references/gcp-services.md#cloud-sql) |
| **Service-specific GCP gotcha** | Private-IP DB won't provision, Cloud Run 403, GKE node-pool churn, log sink drops, missing API enablement, IAM triplet fighting | [GCP Service Playbooks](references/gcp-services.md) (jump to the service) |
| **Beta feature not working** | A documented field/resource has no effect or errors; "is this GA or Preview?"; import of a beta resource | [Service Playbooks: google vs google-beta](references/gcp-services.md#google-vs-google-beta--the-dual-provider-model) |
| **Reinventing a solved module** | Hand-rolling a VPC/GKE/Cloud SQL/project resource graph that a maintained module already encodes | [CFT Toolkit: when to use a module](references/cft-toolkit.md#when-to-use-a-cft-module-vs-roll-your-own), [GCP Service Playbooks](references/gcp-services.md) |
| **GCP-native test/policy blind spots** | Plan looked right but live resource is misconfigured; no policy gate on plan or live env; module lacks integration tests | [Blueprint Testing](references/blueprint-testing.md), [CFT Toolkit: policy validation](references/cft-toolkit.md#policy-validation-config-validator--gcloud-beta-terraform-vet) |
| **Landing-zone / org bootstrap** | "How do I structure a multi-env GCP org from scratch", state-per-stage, CI identity | [CFT Toolkit: example-foundation](references/cft-toolkit.md#example-foundation-the-reference-landing-zone) |

## When to Use This Skill

**Activate when:** creating or reviewing Terraform/OpenTofu configurations or modules for GCP, setting up or debugging tests, structuring multi-environment GCP deployments, implementing IaC CI/CD, choosing module patterns or state organization, configuring or migrating GCS remote state backends, or comparing Terraform/OpenTofu for Google Cloud.

**Don't use for:** basic HCL syntax questions Claude already knows, provider API reference (link to docs), cloud-platform questions unrelated to Terraform/OpenTofu.

## Core Principles

### Module Hierarchy

| Type | When to Use | Scope |
|------|-------------|-------|
| **Resource module** | Single logical group of connected resources | VPC + subnets, SG + rules |
| **Infrastructure module** | Collection of resource modules for a purpose | Multiple resource modules in one region/account |
| **Composition** | Complete infrastructure | Spans multiple regions/accounts |

Flow: resource → resource module → infrastructure module → composition.

### Directory Layout

```
environments/   # prod/ staging/ dev/  — per-env configurations
modules/        # networking/ compute/ data/ — reusable modules
examples/       # minimal/ complete/ — docs + integration fixtures
```

Separate **environments** from **modules**. Use `examples/` as both documentation and test fixtures. Keep modules small and single-responsibility.

See [Module Patterns](references/module-patterns.md) for architecture principles, naming conventions, variable/output contracts.

### Naming Conventions (summary)

- Descriptive resource names (`google_compute_instance.web_server`, not `google_compute_instance.main`)
- Reserve `this` for genuine singleton resources only
- Prefix variables with context (`vpc_cidr_block`, not `cidr`)
- Standard files: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`

See [Module Patterns: Variable Naming](references/module-patterns.md) and [Code Patterns: Block Ordering](references/code-patterns.md#block-ordering--structure) for examples.

### Block Ordering (summary)

Resource blocks: `count`/`for_each` first → arguments → `tags` → `depends_on` → `lifecycle`.
Variable blocks: `description` → `type` → `default` → `validation` → `nullable` → `sensitive`.

See [Code Patterns: Block Ordering & Structure](references/code-patterns.md#block-ordering--structure) for the full rules and examples.

## Testing Strategy

### Decision Matrix: Which Testing Approach?

| Situation | Approach | Tools | Cost |
|-----------|----------|-------|------|
| Quick syntax check | Static analysis | `validate`, `fmt` | Free |
| Pre-commit validation | Static + lint | `validate`, `tflint`, `trivy`, `checkov` | Free |
| Terraform 1.6+, simple logic | Native test framework | `terraform test` | Free-Low |
| Pre-1.6, or Go expertise | Integration testing | Terratest | Low-Med |
| Security/compliance focus | Policy as code | OPA, Sentinel | Free |
| Cost-sensitive workflow | Mock providers (1.7+) | Native tests + mocks | Free |
| Plan-time GCP policy gate | Policy as code (GCP) | `gcloud beta terraform vet` + policy library | Free |
| GCP module — assert live API + idempotency | Blueprint integration test | CFT `tft`/`gcloud` ([Blueprint Testing](references/blueprint-testing.md)) | Real infra |
| Audit a live GCP env vs policy | Posture scoring | `cft scorecard` (CAI) | Low |
| Multi-cloud, complex | Full integration | Terratest + real infra | Med-High |

### Native Test Rules (1.6+)

Before writing test code: validate resource schemas via Terraform MCP so assertions target real attributes.

- `command = plan` — fast, for input-derived values only
- `command = apply` — required for **computed values** (ARNs, generated names) and **set-type nested blocks**
- Set-type blocks cannot be indexed with `[0]` — use `for` expressions or materialize via `command = apply`
- Common set types: S3 encryption rules, lifecycle transitions, IAM policy statements

See [Testing Frameworks](references/testing-frameworks.md) for static-analysis pipelines, native-test patterns, Terratest integration, mock providers, and the full LLM-mistake checklist.

## Count vs For_Each — Quick Rule

| Scenario | Use | Why |
|----------|-----|-----|
| Boolean condition (create / don't) | `count = condition ? 1 : 0` | Optional singleton toggle |
| Items may be reordered or removed | `for_each = toset(list)` | Stable resource addresses |
| Reference by key | `for_each = map` | Named access |
| Multiple named resources | `for_each` | Better identity stability |

**Never** use list index as long-lived identity — removing a middle element reshuffles every address after it. For the decision matrix, safe migration playbook, `moved` block patterns, and known-at-plan failure cases, see [Code Patterns: count vs for_each](references/code-patterns.md#count-vs-for_each-deep-dive).

## Locals for Dependency Management

Using `try()` in a local to prefer a conditional resource's attribute over its parent is a specialized but high-value pattern — it forces correct deletion order without explicit `depends_on`. Common use: VPC + secondary CIDR associations + subnets.

See [Code Patterns: Locals for Dependency Management](references/code-patterns.md#locals-for-dependency-management) for the full pattern and worked example.

## Module Development

Standard layout:

```
my-module/
├── README.md       # Usage documentation
├── main.tf         # Primary resources
├── variables.tf    # Typed inputs with descriptions
├── outputs.tf      # Output values
├── versions.tf     # required_version + required_providers
├── examples/
│   ├── minimal/
│   └── complete/
└── tests/
    └── module_test.tftest.hcl   # or Go for Terratest
```

**Variable contracts**: always `description`, always explicit `type`, use `validation` for complex constraints, use `sensitive = true` for secrets, prefer `optional()` with typed defaults (1.3+) over untyped `map(any)`.

**Output contracts**: always `description`, mark sensitive outputs, expose stable subsets (not whole provider objects).

See [Module Patterns](references/module-patterns.md) for the full contract patterns, module release checklist, and LLM-mistake checklist.

## Cloud Foundation Toolkit (CFT)

CFT is Google's official IaC foundation — the "standard library" for GCP Terraform. Two reflexes:

1. **Reuse before rolling your own.** For any standard service there's a maintained `terraform-google-modules/<name>/google` module encoding security defaults, dependency ordering, and edge cases. The [GCP Service Playbooks](references/gcp-services.md) name the module per service; [CFT Toolkit: when to use a module](references/cft-toolkit.md#when-to-use-a-cft-module-vs-roll-your-own) gives the decision. For a from-scratch org, copy the staged [example-foundation](references/cft-toolkit.md#example-foundation-the-reference-landing-zone) (bootstrap → org → networks → projects → apps, one state per stage, WIF for CI from day one).
2. **Adopt CFT's quality gates** even on your own modules — they are GCP-native and free:

| Gate | Tool | When |
|------|------|------|
| Plan-time policy | `gcloud beta terraform vet <plan.json> --policy-library=…` | CI plan stage, fails the PR on violations |
| Live-env posture | `cft scorecard --policy-path … --bucket <CAI-export>` | scheduled audit of deployed reality |
| Blueprint lint | `cft blueprint test lint` (`tflint-ruleset-blueprint`) | pre-commit / CI |
| Integration test | CFT `tft`/`gcloud` framework — asserts live GCP API + idempotency | on `main`/scheduled ([Blueprint Testing](references/blueprint-testing.md)) |
| Metadata catalog | `cft blueprint metadata -p . -v` — machine-checkable inputs/outputs + required roles & APIs | module authoring |

`gcloud beta terraform vet` (plan-time) and `cft scorecard` (live env) share **one policy library** — author constraints once, enforce across the lifecycle. Depth: [CFT Toolkit](references/cft-toolkit.md).

## CI/CD

Pipeline stages: **validate** → **test** → **plan** → **apply** (with environment protection).

Cost control: mock providers on PR validation, real-cloud integration only on main or scheduled, tag test resources, auto-cleanup.

Drift prevention: pin runtime and providers, commit `.terraform.lock.hcl`, apply the **reviewed plan artifact** from the plan stage (do not re-run `plan` inside the apply job), run policy/security stage on every path to apply.

See [CI/CD Workflows](references/ci-cd-workflows.md) for GitHub Actions, GitLab CI, and Atlantis templates plus the LLM-mistake checklist.

## Security & Compliance

**Essential checks:**

```bash
trivy config .
checkov -d .
```

**Don't:** store secrets in variables or `.tfvars`, use default VPC, skip encryption, open security groups to `0.0.0.0/0`, use inline `ingress`/`egress` blocks in `aws_security_group`.

**Do:** source secrets from GCP Secret Manager or use `write_only` arguments on 1.11+ where the provider supports them, create dedicated VPCs and subnets, enforce encryption at rest and TLS, use least-privilege IAM bindings, and prefer Workload Identity Federation over static service-account keys.

Marking a variable `sensitive = true` masks display only — the value still lives in state. Use `write_only` / `*_wo` on 1.11+, or keep secret material out of Terraform entirely via runtime lookups.

See [Security & Compliance](references/security-compliance.md) for trivy/checkov pipelines, state-file hardening, compliance mappings, and the LLM-mistake checklist.

## State Management

**Never use local state in teams or production.** Remote backends provide automatic locking, encryption, versioning, audit logging, and safe collaboration.

### Choosing a Remote Backend

GCP example (`gcs`; AWS `s3` / Azure `azurerm` / TF Cloud syntax: see [State Management: Choosing a Remote Backend](references/state-management.md#choosing-a-remote-backend)):

```hcl
terraform {
  backend "gcs" {
    bucket = "my-terraform-state"
    prefix = "prod/networking"
  }
}
```

Configure bucket versioning, uniform bucket-level access, retention or soft-delete policy where appropriate, and CMEK on the bucket when required. GCS has backend locking; for choosing among backends and their locking models, see [Choosing a Remote Backend](references/state-management.md#choosing-a-remote-backend).

### State Organization

| Pattern | Use When | Example Path |
|---------|----------|--------------|
| **Per environment** | Different teams per env | `prod/terraform.tfstate`, `staging/...` |
| **Per component** | Independent lifecycles | `prod/vpc/`, `prod/eks/`, `prod/rds/` |
| **Hybrid** (recommended) | Both benefits | `prod/networking/`, `prod/compute/`, `staging/networking/` |

Split state when: different teams, different update cadences, or >500 resources. Combine when: tightly coupled resources, <100 resources, same lifecycle.

See [State Management](references/state-management.md) for locking, migration, multi-team isolation, disaster recovery, and the LLM-mistake checklist.

## Version Management

| Component | Strategy | Example |
|-----------|----------|---------|
| Terraform runtime | Pin minor | `required_version = "~> 1.9"` |
| Providers | Pin major | `version = "~> 7.0"` |
| Modules (prod) | Pin exact | `version = "5.1.2"` |
| Modules (dev) | Allow patch | `version = "~> 5.1"` |

For GCP, pin to the `hashicorp/google` / `hashicorp/google-beta` major in use — both are currently on **major 7** (latest 7.36.x, June 2026), so `version = "~> 7.0"` is the live floor; treat `~> 5.0`/`~> 6.0` examples elsewhere in these references as illustrative constraint-syntax, not current GCP pins.

Commit `.terraform.lock.hcl` intentionally. Keep provider/runtime upgrades in a separate PR from functional changes. See [Code Patterns: Version Management](references/code-patterns.md#version-management) for constraint syntax and upgrade workflow.

## Modern Terraform Features (1.0+)

| Feature | Min version | Common use |
|---------|-------------|------------|
| `try()` | 0.13+ | Safe fallbacks, replaces `element(concat())` |
| `nullable = false` | 1.1+ | Prevent `null` silently overriding defaults |
| `moved` blocks | 1.1+ | Refactor without destroy/recreate |
| `optional()` with defaults | 1.3+ | Typed object attributes |
| `import` blocks | 1.5+ | Declarative imports, reviewable in VCS |
| `check` blocks | 1.5+ | Runtime assertions |
| Native `terraform test` | 1.6+ | Built-in test framework |
| Mock providers | 1.7+ | Cost-free unit testing |
| `removed` blocks | 1.7+ | Declarative resource removal |
| Provider-defined functions | 1.8+ | Provider-specific transformations (requires provider to declare functions) |
| Cross-variable validation | 1.9+ | Reference other `var.*` in `validation` blocks |
| `write_only` arguments | 1.11+ | Secrets never stored in state |
| S3 native lock-file | 1.10+ | State locking without DynamoDB |

Before emitting a feature, verify the runtime floor. See [Code Patterns: Feature Guard Table](references/code-patterns.md#feature-guard-table--version-floor--common-llm-errors) for the full table with common LLM error patterns per feature.

## Runtime-Specific Guidance

- **Terraform 1.0-1.5 (OpenTofu starts at 1.6)**: Terratest for integration, static analysis + plan validation only (no native tests).
- **1.6+**: native `terraform test` / `tofu test` available — migrate simple unit tests, keep Terratest for complex integration.
- **1.7+**: mock providers cut test cost — mock for unit tests, real runs for final integration.
- **1.10+**: S3 native lock-file (`use_lockfile`) is the correct default for new configurations — DynamoDB locking is no longer required.
- **1.11+**: `write_only` arguments for secret handling keep credentials out of state.
- **Terraform vs OpenTofu on GCP**: both CLIs are supported, but Terraform with `hashicorp/google` is the default production recommendation for GCP today. Choose OpenTofu when open-source governance or BUSL avoidance matters more than first-party HashiCorp/Google provider support. Treat `opentofu/google` as opt-in until its maintenance and security posture are proven. For licensing, governance, and feature delta, see [Quick Reference: Terraform vs OpenTofu](references/quick-reference.md#terraform-vs-opentofu-comparison).

## Code Intelligence (terraform-ls)

Semantic navigation for HCL. terraform-ls is optional; without it every row below degrades to a disclosed `rg` + Read fallback.

Self-contained terraform-ls layer of a generic code-intelligence discipline - apply the rows below directly. Recommended companion: the `code-intelligence` plugin (same `antonbabenko/agent-plugins` marketplace) carries the generic discipline (position anchoring, degradation gate, disclosure format, anti-phantom-shim) and ships `/code-intelligence:doctor` for readiness. If it is installed, defer to its generic protocol; this skill stays fully self-contained without it.

| Goal | Use | Tradeoff |
|------|-----|----------|
| Find definition / all references | terraform-ls `goToDefinition` / `findReferences` | Needs `init` + a position anchor |
| Rename value symbol (var/local/output/provider alias) | Manual: `findReferences` -> per-file fresh Read -> edit -> `validate` | No rename provider |
| Rename resource/module address | `moved` block + `plan` shows 0 destroy | Text rename forces destroy/recreate |
| Exact text / known name / `.tfvars` / non-HCL | `rg` + Read | No semantic scope |

✅ Supported: `goToDefinition`, `findReferences`, `documentSymbol`, `hover`, `workspaceSymbol`.
❌ Unsupported: `goToImplementation`, call hierarchy, rename provider. Do not call these then report their absence as a finding.

- ✅ Prereq: local `terraform`/`tofu` on PATH, `terraform init` run; cold start may need one retry.
- ✅ LSP calls are position-anchored (`file:line:character`) - anchor with `rg` first, never symbol-name-only.
- ❌ Do not claim "LSP broken, using rg" until the [Degradation Gate](references/code-intelligence-lsp.md#degradation-gate) passes; disclose any tool substitution on the first line.

Depth: [Code Intelligence](references/code-intelligence-lsp.md#terraform-ls-capability-matrix).

## Reference Files

Progressive disclosure — essentials here, depth on demand:

- [GCP Service Playbooks](references/gcp-services.md) — per-service guidance (Cloud Run, Cloud SQL, GKE, GCS, networking, IAM, Pub/Sub, BigQuery, Secret Manager, …): canonical resources, CFT module, destroy/safety gotchas, `google` vs `google-beta`
- [CFT Toolkit](references/cft-toolkit.md) — `terraform-google-modules` ecosystem, `cft` CLI, blueprint metadata standard, policy validation (`gcloud beta terraform vet` / `cft scorecard`), example-foundation landing zone, CFT vs Fabric
- [Blueprint Testing](references/blueprint-testing.md) — CFT's `tft`/`gcloud` integration-test framework: prescriptive layout, four stages, auto-discovered vs custom, asserting live GCP state + idempotency
- [Testing Frameworks](references/testing-frameworks.md) — static analysis, native tests, Terratest, mock providers
- [Module Patterns](references/module-patterns.md) — structure, variable/output contracts, `terraform_remote_state` rules, release checklist
- [CI/CD Workflows](references/ci-cd-workflows.md) — GitHub Actions, GitLab CI, Atlantis, cost control
- [Security & Compliance](references/security-compliance.md) — trivy/checkov, secrets handling, compliance mappings
- [State Management](references/state-management.md) — backends, locking, migration, multi-team, recovery
- [Code Patterns](references/code-patterns.md) — block ordering, `count`/`for_each` deep dive, modern features, version management, locals
- [Code Intelligence](references/code-intelligence-lsp.md) - terraform-ls capabilities, position-anchored calls, manual rename, degradation gate
- [Quick Reference](references/quick-reference.md) — command cheat sheets, flowcharts, troubleshooting

## License

Apache License 2.0. See LICENSE for full terms.

**Copyright © 2026 Anton Babenko**
