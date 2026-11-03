# Study and event contract

The bundled example is a starting point for authoring, not a researched audience. The CLI validates structure and referential integrity; the agent reviews the relevance and truth of evidence.

## Study

Use JSON with `schema_version: 1`, a stable `id`, a `product` description, and `target: {"revision": "reviewed-build-id"}`. Supply nonempty `personas` and `journeys` lists.

Each persona has `id`, `name`, `goals` (strings), `knowledge` (strings), `constraints` (including integer `max_steps`), `evidence` (objects with `source` and `claim`), `assumptions` (strings), and `prior_experience` (strings). An empty evidence list is allowed when assumptions are explicit. Evidence citations describe the basis for the persona, not proof that a journey succeeded. Use anonymized research summaries and references, not raw participant records or credentials.

Each journey has `id`, `goal`, `start_url`, `success_criteria` (strings), and `initial_state` describing the fixture/account/reset condition. The harness does not provision that state. Describe the starting condition precisely enough for the driver to recreate it. Use IDs with lowercase letters, digits, and hyphens.

`plan` snapshots the study in a new run directory and produces one packet per persona and journey. Persona experience is explicit study input; events never silently rewrite it. A changed persona or starting state invalidates a controlled before/after comparison. The comparison permits different product revisions and deployment URLs.

## Events

Save an event JSON file and call `record`. The event includes `step`, `kind`, `summary`, `source`, and `artifacts`. Use `kind: observation`, `judgment`, or `outcome`. Observations use `source: browser` or `fixture`; judgments and outcomes use `source: model`. Artifact paths are relative to the run directory and must resolve inside that session's directory, without symlinks. The recorder hashes their contents, and later reads verify those hashes.

An observed successful state might be recorded as:

```json
{
  "step": 1,
  "kind": "observation",
  "summary": "The source appears in the connected sources list.",
  "source": "browser",
  "artifacts": ["sessions/first-time-editor--download-document/source-connected.txt"],
  "criteria": ["The source appears in the connected sources list."]
}
```

The actual artifact must come from a driver observation. Match criterion strings exactly to the journey's criteria. Observations advance the step by one, starting at 1. Judgments and outcomes use the latest observation's step (or 0 if blocked before any action). Follow with an outcome event carrying `status: completed`, `abandoned`, `blocked`, or `budget_exhausted`, for example:

```json
{"step": 1, "kind": "outcome", "summary": "The declared criterion was observed.", "source": "model", "artifacts": [], "status": "completed"}
```

Completion requires recorded browser observations with artifacts covering every success criterion. Model statements and fixture playback cannot establish observed completion. An outcome closes the session; further events are rejected.

Use `judgment` for simulated confusion or trust reactions; link the visible evidence prompting that interpretation. The host remains responsible for accurate action accounting and authentic driver output. The harness is a local evidence ledger, not a browser sandbox or independent attestation service.

## Reports and comparisons

`report` creates JSON and Markdown in a new directory. It accounts for every planned session, including unstarted sessions. Read the per-session observations and judgments before prioritizing a finding. A blocked driver is different from a product failure; simulated abandonment is different from observed human abandonment.

`compare` reads both runs and refuses incompatible study conditions. Results describe this cohort's recorded outcomes and actions; they do not establish statistical significance, causal impact, or population completion rates. Preserve original runs for inspection and create a new run for each revision.
