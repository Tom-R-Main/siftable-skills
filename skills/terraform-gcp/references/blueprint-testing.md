# Blueprint Testing — CFT's GCP-Native Integration Framework

The CFT **blueprint-test** framework (`infra/blueprint-test`, Go packages `tft` and `gcloud`) is the GCP-native layer that sits **above** native `terraform test` and **on top of** Terratest. Where native tests assert on plan/state values, blueprint tests stand up real GCP resources, then assert against the **live API** (via `gcloud … describe`) and verify **idempotency** (a second plan shows no changes). This is the framework every `terraform-google-modules` module uses.

Use this when: authoring or reviewing a CFT-style module, you need to assert that provisioned GCP resources are *actually* configured correctly (not just that the plan looked right), or you're wiring a module's CI. For the pure-Terraform/native/Terratest decision, start at [Testing Frameworks](testing-frameworks.md); come here for the GCP integration layer.

## Prescriptive directory structure

The framework is convention-driven — layout *is* configuration:

```
my-module/
├── modules/…                 # submodules
├── examples/                 # each subdir is a runnable root module that calls the module
│   ├── simple/
│   └── private/
└── test/
    ├── setup/                # provisions the test PROJECT + prerequisites (run once)
    │   └── outputs.tf        #   outputs here are auto-exported as TF_VAR_* to every test
    ├── fixtures/             # optional: wrap an example to add test-only inputs
    │   └── private/
    └── integration/          # Go tests
        ├── discover_test.go  #   the auto-discovery entrypoint
        └── private/
            └── private_test.go  # custom assertions for the "private" example
```

- **`test/setup`** — a Terraform config that creates the **project**, enables APIs, and creates any prereqs (networks, SAs) the examples need. Its outputs are **automatically loaded as `TF_VAR_*` environment variables** into both auto-discovered and custom tests — this is how `project_id` flows from setup into every example without hard-coding.
- **`examples/<name>`** — a real root module using the module under test as `source = "../../"` (or a submodule). Examples double as **documentation** and **test subjects**.
- **`test/fixtures/<name>`** — optional wrapper around an example to inject test-only variables and unify the interface. **Discouraged unless necessary** — prefer testing the example directly.
- **`test/integration`** — Go tests. Auto-discovery handles the common case; add a `<example>_test.go` only when you need custom assertions.

## The four stages

Every test (auto-discovered or custom) runs four stages, mapping to Terraform lifecycle:

| Stage | Runs | Asserts |
|-------|------|---------|
| `init` | `terraform init` + `terraform validate` | config is valid |
| `apply` | `terraform apply` | resources provision without error |
| `verify` | `terraform plan` | **idempotency** — no further adds/changes/destroys (no permadiff) |
| `teardown` | `terraform destroy` | clean teardown |

Run a single stage with the `RUN_STAGE` env var — invaluable for iterating (apply once, re-run `verify` repeatedly, teardown only when done):

```bash
cd test/integration
go test -v                                   # all stages, all tests
RUN_STAGE=apply  go test -v -run TestPrivate # just apply, just one test
RUN_STAGE=verify go test -v -run TestPrivate # re-check idempotency without re-applying
RUN_STAGE=teardown go test -v -run TestPrivate
```

> Staged execution lets you keep expensive infra up across edit/verify cycles and tear it down deliberately — the GCP analogue of "don't pay for a full apply just to re-check an assertion."

## Auto-discovered tests

A single discovery entrypoint tests **every** example/fixture that doesn't have a custom test, with the default idempotency verification — zero per-example boilerplate:

```go
package test

import (
	"testing"
	"github.com/GoogleCloudPlatform/cloud-foundation-toolkit/infra/blueprint-test/pkg/tft"
)

func TestAll(t *testing.T) {
	tft.AutoDiscoverAndTest(t)
}
```

Discovery rules: every dir under `test/fixtures/` is queued; then every dir under `examples/` **not** already covered by a fixture or a custom integration test is queued. Each runs the four stages with `DefaultVerify` (idempotency).

## Custom tests — assert against the live GCP API

When idempotency isn't enough, write a `Test*` function. The pattern: construct the blueprint test, define a verifier that calls `DefaultVerify` (keep the idempotency check) **then** queries the live API with the `gcloud` helper and asserts:

```go
package mysql_public

import (
	"fmt"
	"testing"

	"github.com/GoogleCloudPlatform/cloud-foundation-toolkit/infra/blueprint-test/pkg/gcloud"
	"github.com/GoogleCloudPlatform/cloud-foundation-toolkit/infra/blueprint-test/pkg/tft"
	"github.com/stretchr/testify/assert"
)

func TestMySqlPublicModule(t *testing.T) {
	bpt := tft.NewTFBlueprintTest(t)

	bpt.DefineVerify(func(assert *assert.Assertions) {
		bpt.DefaultVerify(assert) // keep the no-permadiff idempotency check

		// Pull a Terraform output, then describe the real resource via gcloud.
		// gcloud.Run returns a parsed (gjson) result you query with .Get(path).
		op := gcloud.Run(t, fmt.Sprintf("sql instances describe %s --project %s",
			bpt.GetStringOutput("name"), bpt.GetStringOutput("project_id")))

		assert.Equal("MYSQL_8_0", op.Get("databaseVersion").String(), "db version matches")
		assert.True(op.Get("settings.ipConfiguration.ipv4Enabled").Bool(), "ipv4 enabled")
		assert.Contains(op.Get("gceZone").String(), "us-central1", "in expected region")
		assert.GreaterOrEqual(op.Get("settings.dataDiskSizeGb").Float(), 10.0, "disk sized")
		assert.Empty(op.Get("settings.userLabels"), "no labels set")
	})

	bpt.Test() // execute all four stages
}
```

Key API surface:

- **`tft.NewTFBlueprintTest(t)`** — constructs a test bound to an example (auto-located, or set options). Exposes outputs: `GetStringOutput`, `GetJsonOutput`, etc.
- **`DefaultVerify(assert)`** — the standard idempotency assertion (plan shows no changes). Call it inside your custom verify so you keep that guarantee.
- **`gcloud.Run(t, "<gcloud args>")`** — runs `gcloud … --format=json`, returns a **gjson** result; query nested fields with `.Get("a.b.c").String()/.Bool()/.Float()`. This is how you assert *real* GCP state, not just Terraform's view.
- **`DefinePlan(func(ps *terraform.PlanStruct, assert))`** — assert on the **plan JSON** (resource change counts, attribute values) to fail fast *before* an expensive apply, or to smoke-test config with no apply at all. There's no default plan function; opt in by defining one.
- **`PlanAndShow()`** — ad-hoc plan within a stage (e.g., extra checks in `verify`).

Run a custom test by name (regex):
```bash
go test -run TestMySqlPublicModule ./... -v
go test -run TestAll/* .            # all auto-discovered cases
go test -v ./... -p 1 .            # everything, serialized (-p 1 avoids parallel project contention)
```

## Cost & CI discipline

Blueprint tests provision **real, billable** GCP resources, so:

- **Run `test/setup` once** to create a dedicated test project; reuse it across runs. Tear down infra per-test via the `teardown` stage; tear down the project rarely.
- **Gate full integration on `main`/scheduled**, not every PR push — on PRs prefer `init`/`validate`, `lint`, plan-assertions (`DefinePlan`), and native/mock tests. See [CI/CD Workflows](ci-cd-workflows.md).
- Use `-p 1` (or per-test project isolation) to avoid parallel tests colliding on shared project quota/resources.
- Always let `teardown` run (even on failure paths in CI) so test projects don't accumulate orphaned billable resources.

## How this fits the testing stack

| Layer | Tool | Asserts on | Cost |
|-------|------|-----------|------|
| Static | `fmt`, `validate`, `tflint` (+ blueprint ruleset), `trivy`, `checkov` | source files | free |
| Plan-time policy | `gcloud beta terraform vet` (Config Validator) | plan JSON vs policy library | free |
| Unit | native `terraform test` + mock providers (1.7+) | computed values, no real infra | free–low |
| **Integration (GCP)** | **blueprint-test (`tft`/`gcloud`)** | **live GCP API + idempotency** | **real infra** |
| Posture (live env) | `cft scorecard` (CAI) | deployed reality vs policy library | low |

Blueprint testing is the rung where you confirm the module *actually does the right thing on GCP*. Lower rungs catch more, cheaper, earlier — push as much as possible down the stack and reserve blueprint integration for what only a real apply can prove. See [cft-toolkit.md](cft-toolkit.md) for the policy rungs and [testing-frameworks.md](testing-frameworks.md) for native/Terratest depth.
