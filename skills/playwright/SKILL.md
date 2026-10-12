---
name: "playwright"
description: "Use when the task requires automating a real browser from the terminal (navigation, form filling, snapshots, screenshots, data extraction, UI-flow debugging) via `playwright-cli` or the bundled wrapper script."
---


# Playwright CLI Skill

Drive a real browser using an already installed `playwright-cli` or the project's existing Playwright harness. This skill does not fetch npm packages, download browsers, or provision authentication. Respect any host browser-control rules and the user's selected session.
Treat this skill as CLI-first automation. Do not pivot to `@playwright/test` unless the user explicitly asks for test files.

## Prerequisite check

Confirm the configured `PLAYWRIGHT_CLI_BIN` (or `playwright-cli` on PATH) is executable, inspect its help/version, and verify the browser binaries needed for the selected route exist. Missing CLI/browser is a capability gap; installation or fetching requires separate authorization. Do not run `npx --yes` implicitly.

## Skill path

Resolve `SKILL_DIR` from the loaded `SKILL.md`, then set:

```bash
PWCLI="$SKILL_DIR/scripts/playwright_cli.sh"
```

The wrapper invokes the existing executable and adds an optional `PLAYWRIGHT_CLI_SESSION`. Its `--help` describes the adapter without network access; inspect the underlying executable's help for its command contract. In headless cloud sessions, omit `--headed` unless a display is actually available.

## Quick start

Use the wrapper script:

```bash
"$PWCLI" open https://playwright.dev --headed
"$PWCLI" snapshot
"$PWCLI" click e15
"$PWCLI" type "Playwright"
"$PWCLI" press Enter
"$PWCLI" screenshot
```

Provisioning a CLI is separate from driving the browser. Report missing capabilities and follow the user-approved environment setup path.

## Core workflow

1. Open the page.
2. Snapshot to get stable element refs.
3. Interact using refs from the latest snapshot.
4. Re-snapshot after navigation or significant DOM changes.
5. Capture artifacts (screenshot, pdf, traces) when useful.

Minimal loop:

```bash
"$PWCLI" open https://example.com
"$PWCLI" snapshot
"$PWCLI" click e3
"$PWCLI" snapshot
```

## When to snapshot again

Snapshot again after:

- navigation
- clicking elements that change the UI substantially
- opening/closing modals or menus
- tab switches

Refs can go stale. When a command fails due to a missing ref, snapshot again.

## Recommended patterns

### Form fill and submit

```bash
"$PWCLI" open https://example.com/form
"$PWCLI" snapshot
"$PWCLI" fill e1 "user@example.com"
"$PWCLI" fill e2 "nonsecret fixture text"
"$PWCLI" click e3
"$PWCLI" snapshot
```

### Debug a UI flow with traces

```bash
"$PWCLI" open https://example.com --headed
"$PWCLI" tracing-start
# ...interactions...
"$PWCLI" tracing-stop
```

### Multi-tab work

```bash
"$PWCLI" tab-new https://example.com
"$PWCLI" tab-list
"$PWCLI" tab-select 0
"$PWCLI" snapshot
```

## Wrapper script

Use the loaded skill's adapter when useful, or the repository's established harness. It never runs `npx`, installs packages, or downloads browsers. Inspect the actual external CLI before relying on version-sensitive flags.

## References

Open only what you need:

- CLI command reference: `references/cli.md`
- Practical workflows and troubleshooting: `references/workflows.md`

## Guardrails

- Always snapshot before referencing element ids like `e12`.
- Re-snapshot when refs seem stale.
- Prefer explicit commands over `eval` and `run-code` unless needed.
- When you do not have a fresh snapshot, use placeholder refs like `eX` and say why; do not bypass refs with `run-code`.
- Use `--headed` when a visual check will help.
- When capturing artifacts in this repo, use `output/playwright/` and avoid introducing new top-level artifact folders.
- Default to CLI commands and workflows, not Playwright test specs.
