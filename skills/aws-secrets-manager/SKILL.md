---
name: aws-secrets-manager
description: Design or review AWS Secrets Manager integrations while keeping secret values out of agent context, logs, command arguments, and generated artifacts.
license: MIT
---

# AWS Secrets Manager without exposing values

Treat credentials as opaque runtime capabilities. Use secret names, ARNs, version labels, schemas and policy metadata for reasoning; do not fetch plaintext values through the CLI, SDK, local agent endpoint, MCP tools or environment inspection. Do not open key files or ask the user to paste credentials.

## Select the supported runtime path

Inspect the application's existing secret integration and deployment configuration. Prefer an already configured workload identity and a supported service integration, secret mount or runtime resolver. A reference string is only a reference when the receiving service explicitly supports and resolves it; do not assume a generic command or container interprets a dynamic-reference syntax.

Resolve secrets in the authorized application runtime with least-privilege access to the required secret and version. The agent can edit non-secret configuration or application code within task scope. Provisioning identities, altering policies, rotating values, changing resources or activating a deployment still require the task's existing authorization.

Never interpolate a resolved value into a shell command, process argument, generated config, temporary file, tool output, diff or chat. A wrapper that keeps values out of stdout can still expose them through process listings, exception text, tracing, child logs or files; wrapper use alone is not a confidentiality guarantee. Use the application's supported protected input channel and verify its logging/redaction contract without printing the value.

## Diagnose without revealing credentials

Confirm identity, region, secret identifier, resource policy, workload permissions, selected version label, and network reachability using metadata-only operations within scope. Test success through a bounded application operation and a non-secret result. Authentication failures should report a category and affected capability, not request or echo credential material. Preserve failure evidence after redaction.

Read the current [AWS Secrets Manager documentation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html) for the chosen service integration, caching and rotation contract. This package supplies no resolver, plugin hook, vault, credentials or enforcement layer. Report a missing secure runtime route as a capability gap rather than fetching the value to make progress.
