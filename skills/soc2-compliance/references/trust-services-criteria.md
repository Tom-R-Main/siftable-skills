# Trust Services Criteria and SOC 2 boundaries

Use this reference for scoping and criteria routing. Verify exact wording and current applicability against AICPA material before issuing a formal matrix.

## SOC 2 is an attestation framework

SOC 2 addresses controls at a service organization relevant to security, availability, processing integrity, confidentiality, or privacy. Management describes the system, identifies service commitments and system requirements, specifies controls, and makes an assertion. An independent service auditor examines the subject matter and issues the report.

Do not call a readiness assessment, automated scan, vendor dashboard, or internal review a SOC 2 audit or certification.

## Report types

- **Type 1** evaluates whether controls are suitably designed and implemented as of a specified date.
- **Type 2** additionally evaluates operating effectiveness over a specified period.

For a Type 2 readiness review, require evidence across the entire period and account for control frequency, population completeness, changes, and exceptions. A point-in-time screenshot cannot prove period operation.

## Trust Services Categories

- **Security**: protection against unauthorized access, use, or disclosure and against damage that could compromise the system's objectives.
- **Availability**: system availability for operation and use as committed or agreed.
- **Processing integrity**: complete, valid, accurate, timely, and authorized system processing.
- **Confidentiality**: protection of information designated confidential.
- **Privacy**: collection, use, retention, disclosure, and disposal of personal information.

Security uses the common criteria. The other categories add category-specific criteria to the common criteria. Do not add categories only for marketing; tie them to commitments, requirements, data, and risk.

## Common-criteria routing

Route controls through these domains before reaching for a product checklist:

- CC1: control environment;
- CC2: communication and information;
- CC3: risk assessment;
- CC4: monitoring activities;
- CC5: control activities;
- CC6: logical and physical access;
- CC7: system operations;
- CC8: change management;
- CC9: risk mitigation, including vendor and business-partner risk.

The points of focus help interpretation but are not a substitute for evaluating whether the criterion is met in the organization's circumstances.

## System description

The description should make the subject matter testable. Cover:

- services provided and principal commitments;
- system requirements and boundaries;
- infrastructure, software, people, procedures, and data;
- significant events and incidents relevant to the description;
- applicable criteria and controls;
- subservice organizations and the carve-out or inclusive method;
- complementary user-entity controls;
- significant system changes during the period.

Reconcile the written description to live architecture, data flows, inventories, deployment paths, ownership, and vendor dependencies.

## Authoritative-source check

At the start of a formal engagement, confirm:

- AICPA 2017 Trust Services Criteria with revised points of focus (2022), or its current successor;
- AICPA 2018 SOC 2 Description Criteria with revised implementation guidance (2022), or its current successor;
- currently effective Statements on Standards for Attestation Engagements;
- the current AICPA SOC 2 guide and the service auditor's request list.

If sources conflict, prioritize current AICPA standards and the independent service auditor's documented interpretation. Record the version and retrieval date in the assessment.
