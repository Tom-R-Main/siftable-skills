---
name: sentry
description: Inspect Sentry issues, events, and recent application errors through a configured read-only connector or API route, and distinguish observed failures from inferred causes.
license: Apache-2.0
---

# Sentry investigation

Use an available Sentry connector first. Otherwise use an already configured, trusted API client with read-only access. Discover the tool schema or client help before querying. This package supplies instructions, not credentials or a client executable.

Establish the organization, project, environment, time range, and question from the request or authorized project context. Ask only for missing identifiers that cannot be resolved from connected metadata. Do not substitute a different project or silently widen production access.

Find representative issues, then inspect event details needed to establish the trigger, affected release, stack, frequency, and scope. Compare the relevant source and release identity before proposing a cause. A similar stack trace or coincident deployment is evidence for a hypothesis, not proof of causality. Report unavailable or truncated events explicitly.

Use opaque runtime credentials or governed connector scopes. Do not open secret files, print token values, or ask for credentials in chat. If authentication is missing, explain the required read capability and let the user configure it through their approved route.

Minimize copied event data. Remove personal information, authorization headers, cookies, request payload secrets, and unrelated customer content before sharing evidence. Read-only investigation does not authorize resolving issues, changing alerts, deploying a fix, or messaging others.

Return the observed symptom and impact, relevant issue links and source/release identity, likely cause with uncertainty, and the smallest supported next check or fix. Verify any authorized code fix through the project's actual failing boundary.
