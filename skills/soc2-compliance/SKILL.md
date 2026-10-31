---
name: soc2-compliance
description: Plan, assess, implement, evidence, or review SOC 2 readiness and controls. Use for SOC 2 Type 1 or Type 2 scoping, Trust Services Criteria mapping, system descriptions, control matrices, evidence requests, gap assessments, remediation plans, auditor handoff, continuous control monitoring, vendor SOC report review, or translating security operations such as IAM, logging, SIEM, incident response, vulnerability management, change management, backup, and third-party risk into audit-ready controls.
---

# SOC 2 Compliance

Treat SOC 2 as an evidence-backed examination of a service organization's system and controls, not as a checklist or a product certification. Distinguish it from a Security Operations Center (also “SOC”): security operations can operate and evidence controls, but does not itself establish SOC 2 compliance.

## Start with the engagement boundary

1. Identify the service, legal entity, system boundary, locations, infrastructure, people, processes, data, and subservice organizations in scope.
2. Establish the intended report:
   - Type 1: design and implementation of controls as of a specified date.
   - Type 2: design and operating effectiveness over a specified period.
3. Confirm the Trust Services Categories. Security is foundational; add availability, processing integrity, confidentiality, or privacy only when commitments, risks, or customers require them.
4. Identify the current authoritative AICPA Trust Services Criteria, Description Criteria, attestation standards, and auditor-specific evidence expectations. Obtain exact wording from current authorized AICPA material rather than paraphrasing from memory; confirm the edition before issuing a formal matrix. Do not infer current requirements from this skill alone.
5. Separate readiness advice from the independent attestation. Only a qualified independent CPA firm can issue the SOC 2 report.

Read `references/trust-services-criteria.md` before mapping criteria or discussing report scope. Read `references/soc2-assessment-workflow.md` for readiness or remediation work.

## Run structured discovery

Before proposing controls, use the 30-question sequence in
`references/discovery-best-practices.md`. Ask only the unresolved questions that
can materially change scope, control design, evidence, or report timing. Do not
force all 30 into one interview when repository, configuration, contract, or
system evidence can answer them directly.

For each question:

1. inspect available authoritative artifacts;
2. record the answer, assumptions, inclusions, exclusions, and unresolved items;
3. distinguish current practice from the recommended target;
4. identify the authoritative population and expected evidence;
5. map gaps to an owner, deadline, acceptance test, and auditor-confirmation need.

Copy `assets/soc2-discovery-register.yaml` when a durable discovery record is
useful. Preserve the stable question IDs `ENG-01` through `CTL-01` so findings,
controls, and evidence requests can link back to the decision that produced
them.

## Build the control model

Use this trace for every control:

`commitment or requirement -> risk -> criterion -> control objective -> control activity -> owner -> frequency -> population -> evidence -> test -> exception -> remediation`

Do not start from a generic control catalog and retrofit the system. Inspect actual architecture, policy, identity, deployment, monitoring, ticketing, vendor, and incident artifacts first.

For each control, record:

- stable control ID and exact scope;
- risk and applicable criterion or criteria;
- preventive, detective, or corrective nature;
- manual, automated, or hybrid operation;
- owner, performer, reviewer, frequency, and evidence repository;
- population source and how completeness and accuracy are established;
- expected evidence and test method;
- dependencies, complementary user-entity controls, and subservice-organization treatment;
- exceptions, compensating controls, and remediation status.

Read `references/control-evidence-patterns.md` when designing evidence or testing a control.

## Ground criteria and implementation separately

Use the current official sources in `references/source-map.md`. An already configured authorized corpus may help locate evidence; no private library, database, embedding service, credentials, or ingestion wrapper is bundled or required.

AICPA criteria and attestation standards define the examination. NIST, CSA, OWASP and MITRE provide implementation and testing guidance, not additional SOC 2 criteria. Security-operations guidance can inform a control; it cannot establish that the control exists or operated. Verify the edition and applicable scope, cite the actual title and section or page, and involve the service auditor for interpretation.

For AI systems, a relevant AI control framework can supply candidate control activities or testing questions. Map them explicitly to the selected criteria; a framework mapping or self-assessment is not operating evidence. Read `references/security-operations-evidence.md` when translating operational records into audit evidence.

## Produce decision-ready outputs

For a readiness engagement, select the artifacts the scope requires:

1. Scope memo: service, boundary, categories, report type, period/date, subservice method, and exclusions.
2. Criteria-control matrix: one row per control with risk, criterion, owner, frequency, evidence, and status.
3. Evidence request list: artifact, population, source system, owner, period, due date, and completeness check.
4. Gap and remediation register: finding, risk, affected criterion/control, severity, owner, action, target date, and retest.
5. Readiness summary: what is designed, implemented, operating, evidenced, excepted, blocked, and ready for auditor review.

Label every conclusion:

- `verified`: supported by inspected evidence;
- `reported`: asserted by an owner but not independently checked;
- `inferred`: reasoned from indirect evidence;
- `missing`: required evidence was not provided;
- `not applicable`: excluded with documented rationale.

## Guardrails

- Never state “SOC 2 compliant” from a readiness scan or tool output.
- Never invent criteria text, control operation, evidence, dates, samples, populations, or auditor conclusions.
- Do not confuse a policy with proof that a control operated.
- Do not use screenshots as the only evidence when exportable system records exist.
- Preserve provenance, timestamps, scope, and chain of custody for evidence.
- Minimize sensitive data in collected evidence; redact secrets and unrelated personal data.
- Report exceptions rather than silently substituting compensating evidence.
- Treat vendor attestations, penetration tests, vulnerability scans, and monitoring tools as inputs to controls, not controls by themselves.
- Verify current AICPA material and engage the service auditor for judgment calls.
