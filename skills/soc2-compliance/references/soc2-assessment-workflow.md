# SOC 2 readiness and remediation workflow

## 1. Frame the objective

Capture the business reason, target customers, deadlines, intended report type, categories, expected period, auditor, and decision owners. Identify whether the request is readiness, implementation, evidence preparation, report review, or continuous monitoring.

## 2. Establish scope

Build a boundary inventory:

- products, APIs, environments, regions, networks, and cloud projects;
- production data classes and flows;
- identity providers and privileged paths;
- source control, CI/CD, artifact, and change-approval systems;
- logging, detection, incident, vulnerability, backup, and continuity systems;
- employees, contractors, facilities, and key roles;
- subservice organizations and downstream processors.

Record inclusions, exclusions, dependencies, and the rationale for each.

## 3. Gather commitments and risks

Extract commitments from contracts, policies, privacy notices, SLAs, architecture requirements, and customer promises. Build or refresh the risk register. Map each in-scope risk to criteria before mapping controls.

## 4. Inventory actual controls

Inspect live configurations and operating records. For each control, determine:

- whether it exists and matches its documentation;
- whether the owner and frequency are explicit;
- whether the population can be reproduced;
- whether evidence is durable, attributable, time-bounded, and reviewable;
- whether exceptions are captured and resolved;
- whether the control changed during the period.

Classify maturity as `not designed`, `designed`, `implemented`, `operating`, `evidenced`, or `auditor-ready`.

## 5. Design tests

Choose inquiry, observation, inspection, or reperformance based on the control and engagement stage. Define the population, period, sampling approach, expected result, completeness checks, and exception handling before collecting samples.

For automated controls, test configuration, change governance, access, dependencies, and representative operation. Automation does not eliminate evidence or change-control requirements.

## 6. Remediate

Prioritize gaps by criterion impact, risk, report timing, evidence lead time, and dependency. Prefer durable system controls and exportable evidence over manual screenshots. Assign an owner, target date, acceptance test, and retest result.

Do not backdate approvals or manufacture historical evidence. If a Type 2 control lacks sufficient operating history, surface the timing consequence.

## 7. Prepare the auditor handoff

Deliver:

- approved scope and system description;
- management criteria-control matrix;
- policy and procedure index;
- population reports and evidence packages;
- risk assessment and vendor register;
- incident, change, access, vulnerability, backup, and continuity records;
- exceptions and remediation log;
- complementary user-entity and subservice-organization control mapping.

Keep an evidence index with source system, query/export method, custodian, period, hash or immutable reference where appropriate, and redaction notes.

## 8. Operate continuously

After the report period, preserve control ownership, evidence cadence, exception review, risk updates, vendor monitoring, system-description changes, and readiness for bridge letters or the next examination. Track drift in both the control and the evidence-generation path.
