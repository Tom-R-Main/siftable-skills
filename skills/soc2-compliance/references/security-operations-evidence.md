# Security operations as SOC 2 evidence

Security-operations sources cover Security Operations Centers, SIEM, threat hunting, and incident response. Use them to design and evaluate the operation of security controls, especially logical access, system operations, monitoring, incident response, and risk mitigation. Do not treat it as authoritative SOC 2 criteria.

## Evidence-producing security operations

### Logging and detection

Maintain a scoped log-source inventory and reconcile it to assets, identities, cloud control planes, SaaS platforms, and critical applications. For each source, document event coverage, onboarding state, parsing health, retention, integrity, access, monitoring, and gaps.

Evidence should show both configuration and operation: source status, rule or analytic changes, alert populations, triage, escalation, closure, and review.

### Incident response

An incident-response plan becomes meaningful when roles, severity, communications, containment, eradication, recovery, evidence preservation, and post-incident actions operate in practice. Exercises and real incidents should produce durable records with timelines, decisions, approvals, affected systems, lessons, and tracked remediation.

### Threat hunting

Threat hunting can supplement automated detection by testing hypotheses across endpoint, identity, cloud, network, and third-party data. Preserve the hypothesis, data sources, query, time range, analyst, findings, escalation, and detection improvements. Do not present ad hoc hunts as a substitute for baseline monitoring.

### Forensics

For forensic artifacts, preserve acquisition method, timestamps, hashes, custody, storage, access, and analysis steps. Minimize unrelated sensitive data. If the evidence supports an audit control rather than litigation, still maintain enough provenance for independent review.

### Application and API security testing

Use penetration-testing references to improve risk identification, test design, and remediation quality for scoped applications and APIs. Preserve authorization, scope, environment, methodology, test dates, tester independence, findings, affected assets, severity rationale, remediation tickets, retest results, and accepted exceptions.

A testing technique is not itself a SOC 2 requirement, and a penetration-test report does not replace secure development, change management, vulnerability management, access control, or monitoring controls. Translate findings into the risk-control-evidence trace and avoid placing exploit details or live credentials in the audit package.

### Password and credential risk

Password-cracking references can help evaluate password-storage design, hash strength, legacy exposure, credential monitoring, and authentication risk. Keep testing authorized and isolated. Evidence should focus on approved methodology, affected population, aggregate results, remediation, and retest rather than recovered plaintext credentials.

### Metrics

Prefer metrics that expose coverage and control performance:

- log-source and asset coverage;
- detection-to-triage and triage-to-containment time;
- aged alerts and unreviewed exceptions;
- incident severity and recurrence;
- detection false-negative and false-positive learning;
- remediation closure and overdue actions;
- exercise and restore-test results.

Avoid vanity counts that can improve while risk worsens.

## Cross-domain visibility

Modern intrusion paths span identity, endpoint, cloud, SaaS, virtualization, third-party integrations, and AI control planes. Scope monitoring and incident evidence around those paths, not only endpoint alerts. The CrowdStrike 2026 guide in the corpus is useful for current attacker-path examples, including identity and cloud movement and the need for AI-tool interaction logs and governance.

## Mapping discipline

For every operational practice:

1. identify the scoped risk and applicable criterion;
2. state the control objective;
3. define the repeatable activity, owner, and frequency;
4. define the complete population;
5. specify retained evidence and review;
6. test exceptions and remediation.

A SIEM, EDR, MDR provider, ticketing tool, or threat-intelligence feed is a component. The control is the governed activity and evidence around it.
