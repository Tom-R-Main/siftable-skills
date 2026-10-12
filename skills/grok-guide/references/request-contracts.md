# Request Construction Reference

These request examples document the historical v2 protocol; a compatible external runtime and its versioned validator are required. Confirm its schemas and commands against the configured release rather than hand-validating JSON or treating this document as an executable validator.

## Shared invariants

- Request schema: `grok-guide.request.v2`.
- Evidence schema: `guide-evidence.v1`.
- Plan schema: `grok-guide.plan.v2`.
- Worker result schema: `grok-guide.worker-result.v1`.
- Audit schema: `grok-guide.audit.v1`.
- All objects reject unknown fields.
- Objective in every returned plan must exactly match the request objective.
- Plan starts at version 1 and increments by exactly one per replan.
- Evidence and task IDs are stable identifiers, not prose labels.
- All paths are safe repository-relative POSIX paths.
- Every excerpt SHA-256 is calculated after local redaction.

## Plan request

Use only these top-level fields:

```json
{
  "schemaVersion": "grok-guide.request.v2",
  "phase": "plan",
  "objective": "Exact human objective",
  "constraints": ["At least one hard constraint"],
  "evidencePacket": {
    "schemaVersion": "guide-evidence.v1",
    "packetId": "P1",
    "facts": [
      {
        "id": "E1",
        "path": "src/example.ts",
        "startLine": 10,
        "endLine": 20,
        "claim": "Repository-grounded fact",
        "excerpt": "Exact sanitized excerpt",
        "sha256": "64-lowercase-hex-digest-of-excerpt"
      }
    ],
    "unknowns": [],
    "testState": [
      {"command": "npm test", "status": "not_run", "summary": "Not run before planning"}
    ],
    "disclosure": {
      "fileCount": 1,
      "byteCount": 23,
      "redactionCount": 0,
      "excludedPaths": ["hidden files", "unrelated dirty paths"]
    }
  }
}
```

Compute byte counts and hashes; do not copy placeholder values. `plan` rejects `currentPlan`, `trigger`, and `workerResults`.

## Replan request

Copy the entire validated base request, set `phase` to `replan`, include the current plan, and provide exactly one trigger kind.

Worker contradiction:

```json
{
  "phase": "replan",
  "currentPlan": {"schemaVersion": "grok-guide.plan.v2"},
  "trigger": {
    "kind": "worker_contradiction",
    "workerResults": [
      {
        "schemaVersion": "grok-guide.worker-result.v1",
        "taskId": "T1",
        "status": "blocked",
        "summary": "What happened",
        "evidenceIds": ["E2"],
        "filesChanged": [],
        "tests": [],
        "contradictions": [
          {
            "id": "C1",
            "claim": "Plan assumption contradicted by evidence",
            "evidenceIds": ["E2"],
            "impact": "Why the task graph or decision is invalid",
            "blockedTaskIds": ["T1"],
            "decisionNeeded": "What Grok must decide"
          }
        ],
        "risks": []
      }
    ]
  }
}
```

Human resolution:

```json
{
  "trigger": {
    "kind": "human_resolution",
    "resolutions": [{"questionId": "Q1", "answer": "Exact human answer"}]
  }
}
```

Evidence resolution:

```json
{
  "trigger": {
    "kind": "evidence_resolution",
    "resolutions": [{"questionId": "Q1", "evidenceIds": ["E2"]}]
  }
}
```

Human and evidence resolutions are valid only against matching blocked readiness states and known question IDs.

## Audit request

Copy the validated base request, set `phase` to `audit`, include the final current plan, and include one current worker result for every plan task:

```json
{
  "phase": "audit",
  "currentPlan": {"schemaVersion": "grok-guide.plan.v2"},
  "workerResults": [
    {
      "schemaVersion": "grok-guide.worker-result.v1",
      "taskId": "T1",
      "status": "completed",
      "summary": "Bounded implementation result",
      "evidenceIds": ["E3"],
      "filesChanged": ["src/example.ts"],
      "tests": [{"command": "npm test", "status": "passed", "summary": "Relevant tests passed"}],
      "contradictions": [],
      "risks": []
    }
  ]
}
```

The harness supplies the deterministic audit checklist. Do not invent, omit, merge, or paraphrase criteria.

## Local validation and invocation

After confirming the configured runtime's doctor performs only local, no-inference checks, run:

```bash
"$SKILL_DIR/scripts/run-guide.sh" doctor
```

Invoke only after local preview and approval gates:

```bash
"$SKILL_DIR/scripts/run-guide.sh" run /absolute/request.json
```

The configured external runtime owns authentication and must use opaque credentials or governed scopes. The adapter never selects credentials, discovers vault entries, or reads secrets. Doctor support and its no-inference behavior must be confirmed from the actual runtime.
