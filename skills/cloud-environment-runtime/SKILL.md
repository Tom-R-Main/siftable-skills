---
name: cloud-environment-runtime
description: Establish the selected cloud task's execution, network, and credential context before using cloud tools. Use at cloud task startup or when diagnosing remote access; installing this skill does not create an environment or grant credentials.
metadata:
  adaptation: portable-runtime-routing
---

# Cloud runtime context

Use the host's available managed-environment instructions and tools as the
authority for its executor, network policy, credential bindings and readiness.
Read those instructions at startup and after a context handoff. If the host
exposes an environment-status tool, call its documented schema; do not invent
a tool or reuse another chat's instance identity.

Record the selected repository and execution directory, task branch, operating
system, available shell, and project-selected toolchains. A local reference or
skill file is not proof that the matching runtime is available. Preserve the
task's assigned checkout; do not switch branches to imitate a desktop convention.

Before authorized network work, inspect the host's supported network-policy
snapshot. Distinguish desired settings from current enforced policy. Likewise,
configured credential names are not evidence of current readiness or remote
API authorization. Report unavailable observations rather than treating them
as successful checks.

Use injected credentials opaquely through the documented CLI or SDK. Do not
print the environment, open credential files, copy local authentication, start
interactive login or redeem a vault secret to make an unavailable route work.
For a provider with several configured identities, use the manifest's documented
alias and profile selectors for that command; a default identity is not proof
that it is the intended one. The host's current manifest schema controls the
selection mechanism.

Before Docker, VPN or TCP forwarding work, read the installed managed-runtime
guidance for proxy routing, certificate trust, supported transports and grants.
Do not start Docker, configure a relay, download a helper or widen network policy
solely because a skill mentions it. Task authorization and current host policy
must cover the concrete operation.

For diagnosis, preserve the actual command, resource identity, bounded sanitized
error and fresh readiness evidence. A health or version check qualifies only
its observed boundary. Recheck relevant readiness after setup changes and verify
the target operation separately.

Skill installation, saved environment settings, publication, cache restoration,
fresh-task discovery and successful runtime behavior are separate states.
Verify them through the environment's supported configuration workflow and a
fresh task. This instruction file neither publishes configuration nor retains
arbitrary files uploaded to one chat.

See the official [cloud environment guide](https://learn.chatgpt.com/docs/environments/cloud-environment)
for setup and caching. The active host's exposed tools and current instructions
remain authoritative for executor-specific behavior.
