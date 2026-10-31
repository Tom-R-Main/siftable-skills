# SOC 2 discovery questions and best-practice targets

Use this reference before designing a control matrix or readiness plan. It
defines the 30 decisions most likely to change scope, control design, evidence,
or report timing.

## Contents

- [How to use the questions](#how-to-use-the-questions)
- [Engagement and boundary](#engagement-and-boundary)
- [Identity and access](#identity-and-access)
- [Engineering and vulnerability management](#engineering-and-vulnerability-management)
- [Detection and response](#detection-and-response)
- [Resilience and control assurance](#resilience-and-control-assurance)
- [Source-routing rules](#source-routing-rules)
- [Structured capture](#structured-capture)

## How to use the questions

For each question, establish:

- `current`: what inspected evidence shows now;
- `target`: the risk-appropriate best-practice state;
- `gap`: the difference between current and target;
- `population`: the authoritative set of events, identities, assets, or records;
- `evidence`: the artifacts that can prove design and operation;
- `decision`: owner, deadline, accepted risk, and auditor confirmation if needed.

The targets below are design prompts, not universal SOC 2 requirements. Tailor
them to service commitments, system requirements, risks, architecture, and the
independent service auditor's judgment.

## Engagement and boundary

### ENG-01 — What service, product, and legal entity will the report describe?

**Target:** Define one testable system boundary: legal entity, services, system
purpose, infrastructure, software, people, procedures, and data. Avoid “the
whole company” unless that is genuinely the intended subject matter.

**Inspect:** legal structure, product/service catalog, architecture, ownership,
contracts, billing, and the draft system description.

**Evidence:** approved system description, architecture diagram, service
inventory, system owner.

### ENG-02 — Type 1 or Type 2, and what date or period?

**Target:** Use Type 1 for design and implementation at a specified date. Prefer
Type 2 when customers need assurance over operation across a period. Begin the
period only after material controls operate and retain evidence.

**Inspect:** customer deadline, readiness state, control start dates, evidence
cadence, auditor availability, acquisition or system-change timing.

**Evidence:** engagement decision, target date or period, readiness calendar,
control-operation start dates.

### ENG-03 — Which Trust Services Categories apply?

**Target:** Start with Security and add Availability, Processing Integrity,
Confidentiality, or Privacy only when commitments, product behavior, data use,
or risk justify the additional criteria.

**Inspect:** contracts, SLAs, privacy notices, data classes, processing
commitments, customer requirements, and risk register.

**Evidence:** category-selection rationale and criterion-to-risk mapping.

### ENG-04 — Which promises, requirements, and obligations apply?

**Target:** Maintain an obligation register covering contracts, SLAs, privacy
notices, security addenda, regulatory duties, questionnaires, policies, and
marketing claims. Map each material promise to controls.

**Inspect:** executed agreements, standard terms, public commitments, policy
statements, regulatory analysis, sales questionnaires.

**Evidence:** obligation register with source clause, scope, owner, and control
mapping.

### ENG-05 — Which systems, environments, locations, teams, and processes are included?

**Target:** Maintain a version-controlled scope inventory reconciled to live
administrative systems rather than relying on a narrative list.

**Inspect:** cloud organizations and billing, repositories, deployment
pipelines, IdP, HR, SaaS inventory, data stores, facilities, support and
security processes.

**Evidence:** reconciled scope inventory with source, owner, status, and
last-verified date.

### ENG-06 — What is excluded, and can the exclusion withstand challenge?

**Target:** Give every exclusion a rationale, dependency analysis, risk
assessment, and auditor disposition. Reconsider excluded components that can
affect included services.

**Inspect:** architecture dependencies, shared services, identity, logging,
deployment, backup, support, and vendor paths.

**Evidence:** exclusion register and dependency review.

### ENG-07 — Which subservice organizations matter, and is each carved out or included?

**Target:** Inventory critical suppliers and deliberately select carve-out or
inclusive treatment. For carved-out providers, inspect assurance reports,
bridge letters, complementary subservice controls, exceptions, and gaps.

**Inspect:** vendor architecture, data access, contracts, current reports,
report periods, exceptions, CSOCs, and monitoring.

**Evidence:** vendor inventory, SOC reports, bridge letters, CSOC mapping,
exception and compensating-control decisions.

### ENG-08 — Which complementary user-entity controls are required?

**Target:** Define only customer controls necessary for the service
organization's controls to achieve the criteria. Communicate them in contracts,
documentation, configuration guidance, or onboarding.

**Inspect:** system assumptions, tenant configuration, customer administration,
shared-responsibility documents, support records.

**Evidence:** CUEC register and customer-facing communication.

### ENG-09 — Which data classes exist, and how do they flow, persist, and disappear?

**Target:** Model collection, transformation, transmission, storage, backup,
export, retention, and deletion for each material data class and downstream
processor.

**Inspect:** schemas, object storage, queues, analytics, backups, exports,
vendors, retention jobs, deletion paths.

**Evidence:** data inventory, flow diagrams, retention schedule, deletion
configuration, sampled deletion result.

### ENG-10 — Which auditor, prior findings, and evidence expectations apply?

**Target:** Engage the CPA firm before freezing the control matrix. Reconcile
its request list with previous findings, customer questionnaires, known
exceptions, and the organization's actual evidence sources.

**Inspect:** engagement assumptions, PBC list, prior reports, bridge letters,
readiness reviews, questionnaires, open remediation.

**Evidence:** auditor request register, prior-finding disposition, readiness
decision log.

## Identity and access

### IAM-01 — What are the authoritative identity populations?

**Target:** Designate systems of record for employees, contractors, service
accounts, customer identities, and privileged identities. Reconcile the
populations rather than assuming one directory is complete.

**Inspect:** HRIS, contractor system, IdP, cloud IAM, SaaS administrators,
service-account registries, customer identity stores.

**Evidence:** population exports, reconciliation totals, discrepancies, owner
attestation.

### IAM-02 — How does joiner-mover-leaver processing operate?

**Target:** Trigger access changes from authoritative lifecycle events. Define
approval, deadlines, role changes, termination handling, failed-automation
alerts, and manual fallback.

**Inspect:** HR events, identity automation, tickets, group membership, access
removal timestamps, failures and exceptions.

**Evidence:** complete event population and end-to-end timing from lifecycle
event to access result.

### IAM-03 — Who can reach production, customer data, and security-sensitive systems?

**Target:** Maintain a role-to-resource matrix. Prefer least privilege,
individual identity, time-bound elevation, and no standing production access
where practical.

**Inspect:** cloud roles, databases, CI/CD, repositories, customer-support
tools, backups, SIEM/EDR, break-glass and vendor access.

**Evidence:** access exports, role definitions, elevation logs, approved
exceptions.

### IAM-04 — How are access reviews defined and populated?

**Target:** Review privileged and high-risk access more frequently than
ordinary access. Generate populations directly from source systems, reconcile
completeness, require resource-owner decisions, and verify removals.

**Inspect:** review frequency, source query, filters, reviewer competence,
decisions, removal completion, overdue responses.

**Evidence:** preserved population, reconciliation, reviewer decisions, removal
records and timestamps.

### IAM-05 — How are MFA, passwords, sessions, recovery, secrets, keys, and emergency access protected?

**Target:** Require phishing-resistant MFA for privileged and high-risk access
where supported. Screen passwords against compromised values, protect recovery,
bound sessions, centralize secrets, rotate according to risk, and test
break-glass access.

**Inspect:** IdP and application policy, MFA enrollment, recovery roles,
session settings, secret stores, key age, emergency procedures and tests.

**Evidence:** configuration exports, coverage reports, exception list,
recovery/audit logs, secret inventory, break-glass test.

## Engineering and vulnerability management

### ENGR-01 — What paths can change production?

**Target:** Enumerate and govern application deployments, infrastructure-as-code,
console changes, database migrations, feature flags, configuration stores,
vendor consoles, scripts, and emergency tooling. Block unmanaged mutation
paths.

**Inspect:** repositories, pipelines, cloud IAM and audit logs, database roles,
configuration platforms, vendor administration.

**Evidence:** deployment architecture, mutation-path inventory, privileged-role
inventory, audit-log samples.

### ENGR-02 — How are ordinary changes reviewed, tested, approved, deployed, and rolled back?

**Target:** Create traceable linkage among requirement, diff, risk, peer review,
tests, security checks, approval, deployment identity, production result, and
rollback.

**Inspect:** branch protection, CI rules, approval independence, deployment
authorization, failed changes, rollback tests.

**Evidence:** complete change population and sampled end-to-end change records.

### ENGR-03 — How are emergency changes identified and reviewed?

**Target:** Define objective emergency criteria, restrict performers, record
reason and affected assets contemporaneously, require prompt retrospective
review, and trend recurring emergency changes.

**Inspect:** emergency labels and bypass mechanisms, privileged logs,
retrospective timing, repeat causes.

**Evidence:** complete emergency-change population, retrospective approvals,
corrective actions.

### ENGR-04 — Does vulnerability discovery cover the attack surface?

**Target:** Combine source, dependency, secret, image/container, cloud,
host, external attack-surface, API, web-application, and penetration testing.
Measure coverage against the scoped asset inventory.

**Inspect:** scanner inventories, schedules, authentication, failed scans,
exclusions, unsupported assets, external exposure.

**Evidence:** scanner-to-asset coverage matrix, scan health, exclusion register,
findings.

### ENGR-05 — How are vulnerabilities prioritized, excepted, remediated, and retested?

**Target:** Combine severity with exploitability, exposure, asset criticality,
data sensitivity, and known active exploitation. Use time-bounded exceptions,
compensating controls, escalation, and retesting before closure.

**Inspect:** SLA model, KEV matching, backlog age, exception expiration,
ownership, closure evidence, recurring causes.

**Evidence:** full finding population, SLA calculations, exception approvals,
remediation artifacts, retest results.

### ENGR-06 — Which API and workflow security properties are tested?

**Target:** Test object-, property-, and function-level authorization;
authentication and sessions; resource consumption; sensitive business flows;
SSRF; misconfiguration; API inventory; unsafe downstream consumption;
injection; and leakage.

**Inspect:** endpoint and schema inventories, actor/object authorization matrix,
negative tests, rate limits, third-party API trust boundaries.

**Evidence:** test plan, endpoint coverage, results, findings, remediation and
retest.

### ENGR-07 — How are penetration-test findings linked to accountable closure?

**Target:** Scope tests from the real production attack surface and material
data flows. Link every finding to an owner, risk decision, remediation,
independent retest, closure authority, and residual risk.

**Inspect:** authorization and scope, tester independence, dates, exclusions,
findings, duplicate handling, accepted risk.

**Evidence:** signed report, finding register, remediation changes, retest and
closure records.

## Detection and response

### DET-01 — Which logs are collected, and where are the material gaps?

**Target:** Build a risk-driven log-source register spanning identity, cloud
control plane, applications, APIs, databases, endpoints, networks, CI/CD,
repositories, security tools, backups, and administrative actions.

**Inspect:** asset-to-source coverage, onboarding, event types, owners,
intentional gaps, disabled or unsupported sources.

**Evidence:** log-source inventory mapped to assets, risks, detections, and
ingestion status.

### DET-02 — How are log completeness, timing, retention, integrity, and monitoring health proven?

**Target:** Monitor expected volume, ingestion delay, parser failure, timestamp
synchronization, retention, integrity, access, and collector health. Test that
a known event becomes searchable.

**Inspect:** pipeline and queue health, schema/parsing, clock configuration,
retention policy, privileged access, outage alerts.

**Evidence:** health reports, synthetic events, failed-ingestion alerts,
retention settings, access reviews.

### DET-03 — How is the detection catalog governed?

**Target:** Give each detection an owner, threat hypothesis, data dependency,
severity, response route, test method, tuning history, known blind spots, and
last successful test.

**Inspect:** active, disabled, muted, and experimental rules; data dependencies;
testing; false-positive/negative learning.

**Evidence:** detection catalog, test events, alert/case records, tuning and
disable approvals.

### DET-04 — What distinguishes an event, alert, case, and incident?

**Target:** Use a formal taxonomy: event is observable activity; alert is an
analytic result; case is an investigation container; incident is an authorized
classification based on defined impact and confidence thresholds.

**Inspect:** definitions, severity matrix, decision authority, escalation,
downgrade and closure rules.

**Evidence:** approved classification standard and sampled transitions.

### DET-05 — What must an incident record contain?

**Target:** Preserve detection source, timeline, affected identities/assets/data,
evidence, decisions, containment, eradication, recovery, communications,
legal/privacy review, vendor involvement, and corrective actions.

**Inspect:** case schema, evidence preservation, communication authority,
regulatory/contractual triggers, post-incident process.

**Evidence:** incident case, supporting artifacts, approvals, post-incident
review and corrective-action links.

### DET-06 — How do hunts, incidents, vulnerabilities, and intelligence improve controls?

**Target:** Feed lessons into the risk register, control design, engineering
backlog, training, detection catalog, architecture, and vendor oversight. Track
corrective actions to an effectiveness test.

**Inspect:** hunt and incident lessons, recurring findings, detection gaps,
backlog linkage, overdue corrective actions.

**Evidence:** lessons record, linked changes, owner and deadline, verification
result.

## Resilience and control assurance

### RES-01 — What are the recovery objectives and how are they demonstrated?

**Target:** Derive service-specific RTO and RPO from business impact. Define
backup boundaries, protect recovery data from ordinary administrative
compromise, test usable restores and failover, and compare observed recovery to
objectives.

**Inspect:** impact analysis, backup scope and exclusions, immutability,
restore/failover procedures, dependencies, exercise outcomes.

**Evidence:** RTO/RPO approval, backup configuration, restore and failover
results, corrective actions.

### CTL-01 — Is every control specified and testable?

**Target:** Give each control a stable ID, objective, risk/criterion mapping,
scope, owner, operator, frequency or trigger, population, procedure, expected
evidence, retention, exception path, reviewer, and completeness/accuracy test.

**Inspect:** control matrix, policies, procedures, automated configurations,
population queries, evidence repositories, exception records.

**Evidence:** control specification, population, sample selection, operation
artifacts, exceptions, reviewer conclusion.

## Source-routing rules

Use current primary sources and record access dates:

- **Engagement, description, criteria, report, CUECs, and subservice method:**
  current AICPA SOC 2 guide, Trust Services Criteria, Description Criteria, and
  applicable SSAEs.
- **Governance and general control design:** NIST Cybersecurity Framework 2.0,
  NIST SP 800-53, NIST SP 800-53A, and CIS Controls.
- **Authentication:** NIST SP 800-63B.
- **Secure development and vulnerability remediation:** NIST SP 800-218,
  CISA Known Exploited Vulnerabilities, OWASP ASVS, and OWASP API Security Top
  10.
- **Logging and monitoring:** NIST SP 800-92, NIST SP 800-137, and CISA logging
  guidance.
- **Incident response:** NIST SP 800-61 and CISA incident-response guidance.
- **Contingency and recovery:** NIST SP 800-34.
- **Supplier risk:** NIST SP 800-161 and current supplier due-diligence guidance.

Use current primary documentation or an authorized configured corpus for operational depth, especially:

| IDs | Suggested local query concepts |
| --- | --- |
| IAM-03–IAM-05 | privileged access, credential abuse, password storage, session compromise, cloud identity |
| ENGR-04–ENGR-07 | attack-surface coverage, BOLA, API authorization, web testing, vulnerability remediation, penetration-test retest |
| DET-01–DET-03 | log-source coverage, SIEM health, detection engineering, alert triage |
| DET-04–DET-06 | incident classification, investigation, containment, threat hunting, lessons learned |
| RES-01 | recovery, backup restoration, failover, operational resilience |

Local retrieval is implementation evidence, not criteria authority and not
proof of the organization's control operation.

## Structured capture

Use `assets/soc2-discovery-register.yaml`. Preserve:

- stable question ID and domain;
- answer state: `verified`, `reported`, `inferred`, `missing`, or
  `not_applicable`;
- current practice and target practice;
- assumptions, inclusions, exclusions, and unresolved decisions;
- authoritative population and completeness check;
- inspected and expected evidence;
- criterion, risk, control, and obligation links;
- sources with version and access date;
- gap, owner, deadline, acceptance test, and retest;
- auditor-confirmation status.
