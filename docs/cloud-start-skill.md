# Cloud startup instructions

Add the following instructions to the environment's startup skill or equivalent startup prompt. Preserve the existing project-specific startup instructions.

```text
At task startup, read the repository's AGENTS.md and follow its toolchain and authority rules.
Read cloud-environment-runtime from the configured user skill directory to establish
which execution, network, credential, and persistence surfaces this task actually has.
Resolve every bundled path from the directory containing that skill's SKILL.md.

The personal skill library is installed under $HOME/.agents/skills by setup and maintenance.
It includes tometo-mode, pstack workflows, language skills, writing skills, and optional
integration routes. Use $tometo-mode when explicitly requested or when its description
matches the task. Read its SKILL.md and the selected sibling skills before acting.
Select language skills using the actual repository files and pinned toolchain.

Check available tools before choosing a route. A skill file does not supply an MCP server,
browser, native app, compiler, corpus, provider account, worker engine, or credentials.
Use the available cloud CLI, service, browser, and artifact surfaces. When a route's
required capability is absent, report the concrete limitation and continue independent
work within the user's scope. Do not assume local Mac apps exist in the cloud.

Follow the user's authorization, approval, and delegation rules. Skill installation
never grants permission to deploy, publish, delete resources, read secrets, contact
others, or launch external providers. Do not print secrets or copy credentials.

If a required skill is absent, check the saved setup/maintenance result and the configured
user skill directory. Do not invent installed capabilities or silently fetch a newer
branch. Report the pinned commit and missing surface needed to resume the task.
```

If you choose a different installation directory, update both these instructions and the harness's skill discovery configuration. Check that the cloud task reads this startup content after publishing the environment.
