# GCP Service Playbooks — Navigate by Service

Per-service Terraform guidance for the GCP surfaces you provision most. Each section gives: the **canonical resources**, the **CFT module** that already solves it (prefer reusing it — see [CFT Toolkit](cft-toolkit.md)), the **destroy/safety gotchas** that bite in production, and **`google` vs `google-beta`** notes where a feature is Preview-only.

This is a navigation layer, not a substitute for provider docs. Always confirm exact argument names and current defaults against the provider docs for the version you pin — defaults change across major versions (`deletion_protection` is the classic example).

## How to read this file

Jump to the service:

- **Foundation / org**: [Projects & Project Factory](#projects--project-factory) · [IAM & Service Accounts](#iam--service-accounts) · [Org Policy & Folders](#org-policy-folders--resource-hierarchy)
- **Networking**: [VPC / Subnets / Networking](#vpc-networking) · [DNS](#cloud-dns) · [Load Balancing](#load-balancing)
- **Compute / containers / serverless**: [Compute Engine (VMs)](#compute-engine-vms) · [GKE](#gke-kubernetes-engine) · [Cloud Run](#cloud-run) · [Cloud Functions](#cloud-functions)
- **Data / databases**: [Cloud SQL](#cloud-sql) · [AlloyDB / Spanner / Firestore](#alloydb-spanner-firestore-bigtable) · [BigQuery](#bigquery) · [Memorystore (Redis)](#memorystore-redis)
- **Storage**: [Cloud Storage (GCS)](#cloud-storage-gcs) · [Artifact Registry](#artifact-registry)
- **Security / secrets**: [Secret Manager](#secret-manager) · [KMS](#cloud-kms)
- **Messaging / events**: [Pub/Sub](#pubsub) · [Eventarc / Workflows](#eventarc--workflows)
- **Observability**: [Logging, Monitoring, Log Export](#observability-logging-monitoring-log-export)

> **The single most common GCP-Terraform production incident is an accidental destroy.** Stateful resources (Cloud SQL, GKE, BigQuery datasets/tables, buckets) ship with destroy guards that you must consciously disable. The [Destroy-Safety Cheat Sheet](#destroy-safety-cheat-sheet) at the bottom consolidates every guard.

---

## Projects & Project Factory

**Canonical resources:** `google_project`, `google_project_service`, `google_project_iam_member` / `_binding`, `google_project_default_service_accounts`.

**CFT module:** `terraform-google-modules/project-factory/google` — the standard way to stamp out projects with billing, APIs, default SA hygiene, Shared VPC attachment, and budget alerts in one call. For org scaffolding use `terraform-google-modules/bootstrap` (seed project + CI/CD service account + state bucket) — this is the bottom of the [example-foundation](cft-toolkit.md#example-foundation-the-reference-landing-zone) stack.

**Gotchas:**
- **Enable APIs before resources that need them.** `google_project_service` activation is eventually consistent; a resource in the same apply can race ahead of API enablement. Either split into a bootstrap stage or let the project-factory module's `activate_apis` handle ordering.
- **`disable_on_destroy = true` (the default) disables the API service on destroy** — which can cascade to *other* resources in the project still using that API. Set `disable_on_destroy = false` for shared/long-lived projects.
- **`disable_dependent_services`** controls whether disabling an API also disables services that depend on it — surprising blast radius; set deliberately.
- Prefer `google_project_iam_member` (additive, one principal) over `google_project_iam_binding` (authoritative for the role) over `google_project_iam_policy` (authoritative for the **whole** project — will strip bindings managed elsewhere, including by Google). Mixing authoritative and additive resources on the same role fights and produces permadiffs.

## IAM & Service Accounts

**Canonical resources:** `google_service_account`, `google_service_account_iam_member`, `google_project_iam_member`, `google_*_iam_member/_binding/_policy` (the IAM triplet exists per resource type), `google_service_account_key` (avoid).

**CFT modules:** `terraform-google-modules/iam/google` (project/folder/org/bucket/etc. IAM at scale via `for_each` maps), `terraform-google-modules/service-accounts/google`.

**Gotchas:**
- **The IAM resource triplet — pick one model per role and never mix:**
  - `_member` — additive, manages one (principal, role) pair. Safest default; co-exists with bindings made elsewhere.
  - `_binding` — authoritative for **one role**, replaces all members for that role.
  - `_policy` — authoritative for the **entire resource**, replaces the whole IAM policy. Almost never what you want on projects/orgs — it will clobber Google-managed bindings and cause lockouts.
- **Never create `google_service_account_key`** unless a system genuinely cannot use Workload Identity / Workload Identity Federation / ADC. Static keys are long-lived credentials that land in state. Prefer WIF for CI (see SKILL.md operating model) and Workload Identity for GKE workloads.
- **Service-account impersonation** (`google_service_account_iam_member` with `roles/iam.serviceAccountTokenCreator`) plus the provider's `impersonate_service_account` is the key-free pattern for least-privilege automation.
- IAM Conditions (`condition {}` block) add expiry/resource constraints — use for time-boxed or resource-scoped grants.

## Org Policy, Folders & Resource Hierarchy

**Canonical resources:** `google_folder`, `google_org_policy_policy` (v2, replaces deprecated `google_organization_policy`), `google_organization_iam_*`, `google_folder_iam_*`.

**CFT modules:** `terraform-google-modules/folders/google`, `terraform-google-modules/org-policy/google`.

**Gotchas:**
- Use the **v2 Org Policy** resource `google_org_policy_policy` (`spec { rules { ... } }`), not the legacy `google_organization_policy`.
- Org-level changes have org-wide blast radius and usually require `roles/orgpolicy.policyAdmin` — treat every org-policy apply as production-critical with a reviewed plan artifact.
- `cft launchpad generate` can scaffold the folder/org hierarchy from a YAML spec; `cft scorecard` audits live org-policy posture against a [policy library](cft-toolkit.md#policy-validation-config-validator--gcloud-beta-terraform-vet).

## VPC Networking

**Canonical resources:** `google_compute_network` (set `auto_create_subnetworks = false`), `google_compute_subnetwork`, `google_compute_router` + `google_compute_router_nat`, `google_compute_firewall`, `google_compute_global_address` + `google_service_networking_connection` (private services access / PSA), `google_compute_address`.

**CFT modules:** `terraform-google-modules/network/google` (VPC + subnets + secondary ranges + routes + firewall), with submodules for `cloud-nat`, `cloud-router`, `firewall-rules`, `vpc-serverless-connector-beta`, `network-peering`.

**Gotchas:**
- **Never use the default VPC.** Always `auto_create_subnetworks = false` and define subnets explicitly with named secondary ranges (GKE pods/services need these).
- **Firewall: avoid `0.0.0.0/0` source ranges.** Scope to subnet CIDRs, tags, or service accounts (`source_service_accounts` / `target_service_accounts` beat tag-based rules for identity-based control).
- **Private Services Access for managed DBs** (Cloud SQL private IP, AlloyDB, Memorystore): you must pre-provision `google_compute_global_address` (purpose `VPC_PEERING`) + `google_service_networking_connection`. Forgetting this is the #1 "private DB won't provision" failure. The connection has order-of-deletion hazards — destroy the consumers first.
- **Serverless VPC access** (Cloud Run / Functions reaching VPC resources): `google_vpc_access_connector`, or on Cloud Run v2 use **Direct VPC egress** (`network_interfaces` in `google_cloud_run_v2_service`) which is newer and connector-free.
- Subnet `secondary_ip_range` changes can force subnet replacement — plan carefully on live networks.

## Cloud DNS

**Canonical resources:** `google_dns_managed_zone`, `google_dns_record_set`, `google_dns_policy`.

**CFT module:** `terraform-google-modules/cloud-dns/google` (public/private/forwarding/peering zones).

**Gotchas:**
- Private zones bind to networks via `private_visibility_config`. DNSSEC is configured on the managed zone, not records.
- `google_dns_record_set` is authoritative for the (name, type) tuple — managing the same record outside Terraform fights.

## Load Balancing

**Canonical resources:** the LB is assembled from many primitives — `google_compute_global_forwarding_rule`, `google_compute_target_https_proxy`, `google_compute_url_map`, `google_compute_backend_service`, `google_compute_health_check`, `google_compute_managed_ssl_certificate`.

**CFT modules:** `terraform-google-modules/lb-http/google` (external global HTTP(S) LB — the most common), plus `lb` (TCP) and the `lb-internal` submodule. These collapse the ~7-resource assembly into one module call.

**Gotchas:**
- **Google-managed SSL certs take time to provision** and require the domain's DNS to already point at the LB IP — reserve the `google_compute_global_address` first, wire DNS, then the cert goes ACTIVE. Expect `terraform apply` to complete before the cert is live; don't treat PROVISIONING as failure.
- Prefer the module over hand-assembling primitives — the resource graph is error-prone and the module encodes the correct dependency order.

## Compute Engine (VMs)

**Canonical resources:** `google_compute_instance`, `google_compute_instance_template` + `google_compute_instance_group_manager` / `_region_instance_group_manager` (MIGs), `google_compute_disk`.

**CFT modules:** `terraform-google-modules/vm/google` (submodules: `compute_instance`, `instance_template`, `mig`, `umig`).

**Gotchas:**
- **Use instance templates + MIGs, not standalone instances**, for anything that needs to scale or self-heal. Templates are immutable — changes force a new template; wire `create_before_destroy` on rolling updates.
- Enable **Shielded VM** (`shielded_instance_config`) and **Confidential VM** where the workload warrants. Set `metadata = { block-project-ssh-keys = "true" }` and prefer OS Login (`enable-oslogin`) over project SSH keys.
- `boot_disk` changes and several `network_interface` changes force replacement; use `lifecycle { ignore_changes }` for fields mutated out-of-band (e.g., labels set by autoscalers).

## GKE (Kubernetes Engine)

**Canonical resources:** `google_container_cluster`, `google_container_node_pool`.

**CFT module:** `terraform-google-modules/kubernetes-engine/google` — the reference GKE module, with `safer-cluster`, `private-cluster`, `autopilot`, and `beta-*` submodule variants. Strongly prefer it; a production-grade GKE cluster has dozens of security-relevant knobs the module sets correctly.

**Gotchas:**
- **`deletion_protection` defaults to `true` on provider 5.0.0+** — `terraform destroy` fails until you explicitly set `deletion_protection = false`. (Verified against current provider docs.)
- **Remove the default node pool:** create the cluster with `remove_default_node_pool = true` + `initial_node_count = 1`, then manage node pools as separate `google_container_node_pool` resources. Otherwise node-pool changes churn the whole cluster.
- **`ip_allocation_policy` (VPC-native) requires the subnet's secondary ranges** to exist first — see [VPC Networking](#vpc-networking).
- Use **Workload Identity** (`workload_identity_config { workload_pool = "PROJECT.svc.id.goog" }`) for pod→GCP auth instead of node SA keys.
- **Autopilot** clusters (`enable_autopilot = true`) ignore many node-pool fields — don't set them or you'll get permadiffs.
- Many hardening features (binary authorization, confidential nodes, some network policy modes) are **`google-beta`-only** — those resources need `provider = google-beta`.

## Cloud Run

**Canonical resources:** prefer **v2** — `google_cloud_run_v2_service`, `google_cloud_run_v2_job`. The v1 `google_cloud_run_service` (Knative-style `template.spec.containers`) is legacy; new work uses v2 (cleaner `template.containers` schema, native gradual rollout, Direct VPC egress).

**CFT module:** `terraform-google-modules/cloud-run/google` (submodules including v2). For most single-service deploys the raw `google_cloud_run_v2_service` resource is clear enough to use directly.

**Gotchas:**
- **Public access is a separate resource:** `google_cloud_run_v2_service_iam_member` granting `roles/run.invoker` to `allUsers`. Forgetting it → 403s; adding it unintentionally → a public service. Make it explicit.
- **Ingress + VPC:** set `ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"` or `_INTERNAL_ONLY` for private services. For egress to VPC, use **Direct VPC egress** (`template.vpc_access.network_interfaces`) on v2 — no connector needed.
- **Secrets:** mount Secret Manager secrets via `template.containers.env { value_source { secret_key_ref } }` rather than baking secrets into env literals (which land in state/plan).
- **Traffic splitting** lives in the `traffic {}` block; on v2, `template` changes create a new revision and `traffic` controls promotion — manage gradual rollouts there, not by recreating the service.
- v1→v2 is **not** an in-place migration (different resource type) — it's a `removed`/`import` migration. Plan it as a state operation.

## Cloud Functions

**Canonical resources:** prefer **gen2** — `google_cloudfunctions2_function` (runs on Cloud Run under the hood). `google_cloudfunctions_function` is gen1/legacy.

**CFT module:** `terraform-google-modules/cloud-functions/google`.

**Gotchas:**
- **Source upload pattern:** zip the source → `google_storage_bucket_object` in a deploy bucket → reference via `build_config.source.storage_source`. A new zip hash triggers redeploy; a stable name with changed content can fail to redeploy — include the content hash in the object name.
- gen2 event triggers go through **Eventarc** (`event_trigger { trigger_region, event_type, ... }`) — the function's SA needs `roles/eventarc.eventReceiver` and the Pub/Sub/Eventarc plumbing must exist.
- Gen2 invoker permissions are Cloud Run IAM (`roles/run.invoker`), since gen2 *is* Cloud Run.

## Cloud SQL

**Canonical resources:** `google_sql_database_instance`, `google_sql_database`, `google_sql_user`.

**CFT module:** `terraform-google-modules/sql-db/google` (submodules `mysql`, `postgresql`, `mssql`, plus HA/read-replica variants). This is the module the CFT [blueprint-testing](blueprint-testing.md) docs use as the worked example.

**Gotchas (this resource is a minefield — read all):**
- **Two independent deletion guards, both matter:**
  - `deletion_protection` (Terraform-level) — defaults to `true` on newer providers; blocks `terraform destroy` only. You must explicitly set `deletion_protection = false` to ever destroy.
  - `settings.deletion_protection_enabled` (**API-level**, default `false`, provider 4.48.0+) — guards against deletion across **all surfaces** (API, gcloud, Console, Terraform). Enable this for real production data.
- **Private IP requires Private Services Access set up first** — `google_compute_global_address` (purpose `VPC_PEERING`) + `google_service_networking_connection`, and the instance's `settings.ip_configuration.private_network` must reference the VPC. The instance can't be created before the PSA connection exists, and **destroy order matters** (kill the instance before the connection).
- **Generated passwords land in state.** Either source from Secret Manager, or on provider 6.x+ use the ephemeral `random_password` + `google_sql_user` write-only/ephemeral pattern. Mark related outputs `sensitive`.
- `database_version` downgrades and several `settings` changes force replacement — a replace on a stateful DB means data loss unless you've taken a backup. Always `terraform plan` and look for `# forces replacement`.
- HA = `availability_type = "REGIONAL"`. Backups + PITR via `settings.backup_configuration`.

## AlloyDB, Spanner, Firestore, Bigtable

**Canonical resources:** `google_alloydb_cluster` + `google_alloydb_instance`; `google_spanner_instance` + `google_spanner_database`; `google_firestore_database` + `google_firestore_index`; `google_bigtable_instance` + `google_bigtable_table`.

**Gotchas:**
- **AlloyDB** needs Private Services Access (same PSA prerequisite as Cloud SQL private IP). Cluster and instance are separate resources with a strict create/destroy order.
- **Spanner** `google_spanner_database` has `deletion_protection` (default `true`) — same destroy-guard pattern; also `version_retention_period` for PITR.
- **Firestore**: one default database per project historically; `google_firestore_database` supports named DBs now. `delete_protection_state` guards deletion. Composite indexes are their own resources.
- Several of these have **`google-beta`-only** advanced features (AlloyDB AI, some Firestore settings) — check the docs' beta markers.

## BigQuery

**Canonical resources:** `google_bigquery_dataset`, `google_bigquery_table`, `google_bigquery_job`, `google_bigquery_routine`.

**CFT module:** `terraform-google-modules/bigquery/google`.

**Gotchas:**
- **`google_bigquery_table.deletion_protection` defaults to `true`** — `terraform destroy` (and table-replacing changes) fail until set to `false`. (Verified against current provider docs.) `google_bigquery_dataset` has `delete_contents_on_destroy` (default `false`) — a non-empty dataset won't destroy unless you set it `true`.
- **Schema changes:** many column changes (type changes, drops) force table replacement = data loss. Additive columns are safe; manage schema as JSON and diff carefully.
- Dataset-level access (`access {}` blocks) vs IAM resources (`google_bigquery_dataset_iam_*`) — don't manage the same grants in both, they fight.

## Memorystore (Redis)

**Canonical resources:** `google_redis_instance` (Memorystore for Redis), `google_redis_cluster` (newer clustered offering), `google_memcache_instance`.

**CFT module:** `terraform-google-modules/memorystore/google`.

**Gotchas:**
- Needs **Private Services Access** for `PRIVATE_SERVICE_ACCESS` connect mode (same PSA prerequisite as Cloud SQL/AlloyDB), or `DIRECT_PEERING`.
- `redis_version` upgrades and `tier`/`memory_size_gb` changes have replace/in-place nuances — plan first.

## Cloud Storage (GCS)

**Canonical resources:** `google_storage_bucket`, `google_storage_bucket_object`, `google_storage_bucket_iam_member`.

**CFT module:** `terraform-google-modules/cloud-storage/google` (creates buckets with sane defaults via `for_each` over names).

**Gotchas:**
- **`force_destroy` defaults to `false`** — `terraform destroy` of a **non-empty** bucket fails. Set `force_destroy = true` only when you accept that destroy deletes all objects. (Verified against current provider docs.) This is the GCS analogue of the DB deletion guards.
- **Always set `uniform_bucket_level_access = true`** — disables legacy per-object ACLs and is required by most org policies and the [blueprint tflint](cft-toolkit.md#cft-blueprint-lint--the-blueprint-tflint-ruleset) / security baselines.
- **`public_access_prevention = "enforced"`** to block accidental public buckets.
- Versioning (`versioning { enabled = true }`) + lifecycle rules (`lifecycle_rule`) for retention/cost. For state buckets specifically, see [State Management](state-management.md).
- CMEK via `encryption { default_kms_key_name }` — the bucket's service agent needs `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the key first (chicken-and-egg; provision the IAM binding before the bucket references the key).

## Artifact Registry

**Canonical resources:** `google_artifact_registry_repository`, `google_artifact_registry_repository_iam_member`.

**CFT module:** `terraform-google-modules/artifact-registry/google`.

**Gotchas:**
- Replaces the deprecated Container Registry (`gcr.io`). `format` (DOCKER/MAVEN/NPM/…) is immutable — wrong format = replace.
- Cleanup policies (`cleanup_policies`) manage image retention; some were `google-beta`-only before graduating — check the version.
- Grant `roles/artifactregistry.reader` to the runtime SA (Cloud Run/GKE) and `writer` to CI.

## Secret Manager

**Canonical resources:** `google_secret_manager_secret`, `google_secret_manager_secret_version`, `google_secret_manager_secret_iam_member`.

**CFT module:** `terraform-google-modules/secret-manager/google`.

**Gotchas:**
- **Do not put the secret payload in Terraform.** `google_secret_manager_secret_version.secret_data` lands in **state in plaintext**. Either create the secret *container* with Terraform and populate versions out-of-band (gcloud/CI), or on provider 6.x+ use `secret_data_wo` (write-only) so the payload never enters state. This is the GCP instance of the SKILL.md write-only/secrets rule.
- Grant `roles/secretmanager.secretAccessor` to the consuming SA — scope to the specific secret, not the project.
- Cloud Run/Functions can reference secrets directly (see those sections) — prefer that over reading the secret into Terraform at all.

## Cloud KMS

**Canonical resources:** `google_kms_key_ring`, `google_kms_crypto_key`, `google_kms_crypto_key_iam_member`.

**CFT module:** `terraform-google-modules/kms/google`.

**Gotchas:**
- **Key rings and keys cannot be deleted** — `terraform destroy` *removes them from state but leaves them in GCP* (by design; KMS is append-only for crypto-material safety). Plan for this; don't expect destroy to clean up.
- `prevent_destroy` lifecycle is often added to keys. Rotation via `rotation_period`.
- The CMEK pattern: each service has a per-service service agent that needs `roles/cloudkms.cryptoKeyEncrypterDecrypter` on the key **before** the encrypted resource references it.

## Pub/Sub

**Canonical resources:** `google_pubsub_topic`, `google_pubsub_subscription`, `google_pubsub_topic_iam_member`.

**CFT module:** `terraform-google-modules/pubsub/google`.

**Gotchas:**
- Dead-letter topics need the Pub/Sub **service agent** granted `roles/pubsub.publisher` on the DLQ topic and `subscriber` on the source — a common missing-permission failure.
- Subscription `ack_deadline_seconds`, `retry_policy`, `expiration_policy` — set `expiration_policy { ttl = "" }` to prevent auto-deletion of long-lived subscriptions.
- Push subscriptions to Cloud Run need an OIDC token (`push_config.oidc_token`) and the invoker SA wired with `roles/run.invoker`.

## Eventarc & Workflows

**Canonical resources:** `google_eventarc_trigger`, `google_workflows_workflow`, `google_cloud_scheduler_job`, `google_cloud_tasks_queue`.

**Gotchas:**
- Eventarc triggers underpin Cloud Functions gen2 event triggers and direct event routing; the trigger SA needs `roles/eventarc.eventReceiver` (+ source-specific roles).
- `google_cloud_scheduler_job` hitting Cloud Run/Functions needs an OIDC token block and invoker IAM.

## Observability (Logging, Monitoring, Log Export)

**Canonical resources:** `google_logging_project_sink` / `_folder_sink` / `_organization_sink`, `google_monitoring_alert_policy`, `google_monitoring_dashboard`, `google_monitoring_notification_channel`, `google_logging_metric`.

**CFT modules:** `terraform-google-modules/log-export/google` (+ destination submodules for storage/bigquery/pubsub) and `terraform-google-modules/cloud-operations/google`.

**Gotchas:**
- **Log sinks use a Google-managed writer identity** (`writer_identity` output) that must be granted write access on the destination (bucket/dataset/topic). Set `unique_writer_identity = true` and bind the identity to the destination — forgetting this silently drops logs.
- Org/folder sinks aggregate across all children (`include_children = true`) — large blast radius and cost; scope intentionally.

---

## `google` vs `google-beta` — the dual-provider model

This is GCP-specific and trips people constantly. Authoritative behavior (from the provider's own `provider_versions` guide):

- There are **two providers** that share one documentation set: `hashicorp/google` (GA only) and `hashicorp/google-beta` (GA **plus** Preview/beta resources and fields). Beta-only fields/resources are **clearly marked in the docs**.
- They **release in lockstep with identical version numbers** (both are on 7.x — 7.36.0 as of June 2026). Pin both to the same constraint.
- `google-beta` sends **all** requests to the beta API endpoint when one exists — even requests that use no beta features. Using `google-beta` is "like using `gcloud beta` over `gcloud`."
- **Select per-resource** by setting the meta-argument on the resource:
  ```hcl
  resource "google_compute_instance" "beta" {
    provider = google-beta   # this resource uses the beta endpoint
    # ...
  }
  ```
- **It is safe to use both in one configuration.** Declare both in `required_providers`, and set `provider = google` / `provider = google-beta` explicitly on each resource for clarity. Parallel `provider "google" {}` and `provider "google-beta" {}` blocks don't interfere.
- **If you omit `provider`, Terraform uses `google` by default** — even if you only defined a `google-beta` block. A "why isn't my beta field working" bug is usually a missing `provider = google-beta`.
- **Import defaults to `google`.** To import a beta-managed resource: `terraform import -provider=google-beta google_x.y ID`.
- **Lifecycle:** beta features graduate to GA and then appear in `google`. When that happens you can drop `provider = google-beta` for that resource — but doing so may show a diff if beta-only fields are set; migrate deliberately.

`required_providers` for a config using both:
```hcl
terraform {
  required_providers {
    google      = { source = "hashicorp/google",      version = "~> 7.0" }
    google-beta = { source = "hashicorp/google-beta",  version = "~> 7.0" }
  }
}
```

---

## Destroy-Safety Cheat Sheet

Every GCP resource that guards against accidental deletion, and the knob that disables the guard. **Before any `terraform destroy` or replace-forcing change on these, run `terraform plan` and confirm the guard state.**

| Resource | Guard argument | Default | Scope of protection |
|----------|----------------|---------|---------------------|
| `google_sql_database_instance` | `deletion_protection` | `true` (newer providers) | Terraform `destroy` only |
| `google_sql_database_instance` | `settings.deletion_protection_enabled` | `false` | **All surfaces** (API/gcloud/Console/TF) |
| `google_container_cluster` | `deletion_protection` | `true` (provider 5.0.0+) | Terraform `destroy` only |
| `google_bigquery_table` | `deletion_protection` | `true` | Terraform `destroy` + replace |
| `google_bigquery_dataset` | `delete_contents_on_destroy` | `false` | Non-empty dataset won't destroy |
| `google_storage_bucket` | `force_destroy` | `false` | Non-empty bucket won't destroy |
| `google_spanner_database` | `deletion_protection` | `true` | Terraform `destroy` |
| `google_firestore_database` | `delete_protection_state` | varies | Database deletion |
| `google_kms_crypto_key` / `_key_ring` | *(none — cannot be deleted)* | n/a | Destroy only removes from state |

General hygiene: add `lifecycle { prevent_destroy = true }` to irreplaceable stateful resources, and keep a fresh backup before any apply that a plan shows as `# forces replacement` on a data-bearing resource. See SKILL.md's Response Contract and [State Management: Safe Destroy](state-management.md#safe-destroy-protocol).
