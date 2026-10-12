---
name: footwork-tools
description: "Equip an agent with observation and action tools for browser UI, native Mac apps, terminals/services, and saved artifacts. Use when tstack needs hands and eyes, Footwork operator commands, or evidence carried between contexts."
license: MIT
---

# Give the agent a usable surface

Choose tools that let the agent observe, act, and read back the result on the task's actual surface. Footwork supplies a concrete native/browser operator CLI and source-bound handoffs; the host's existing tools cover other contexts. A workflow description alone does not supply a working driver.

## Select and establish access

Read the applicable host tool skill and the project's launch/verification recipe. Discover the actual callable tools and installed executables; a skill in the catalog or source in a checkout is not proof of runtime access. Preserve an explicitly requested browser, app, profile, or driver. For semantic data operations, prefer the applicable connector/API/CLI; for UI behavior, exercise the UI. Do not substitute an API call for a required UI journey.

| Context | Eyes | Hands and route |
|---|---|---|
| Existing browser session or signed-in UI | DOM/accessibility snapshot, visible text, screenshot; supported console/network evidence when relevant | Installed Browser/Chrome skill and its documented tab API. On Claude, use the available browser skill/tool rather than assuming Codex APIs. Preserve the user's selected browser. |
| Disposable local web test | Fresh page snapshot, screenshot, errors and response/readback | Project Playwright harness or available Playwright tools when the host's browser rules permit; isolated test data/profile. |
| Native Mac app | Footwork `apps`, `menu`, session `look`, menu-bar paths, screenshots and action receipts | Footwork `start --app`, then `do` on fresh observed IDs. Read [local commands](references/contexts.md) before using it. The host's Computer Use skill is another driver when available and appropriate; follow its runtime and targeting rules. |
| Footwork's own browser | Bound tab's current DOM/menu, page text, screenshots and receipts | Footwork `start --browser`, then `look`/`do`; distinct profile, not a way to inherit the user's sign-in or switch away from a requested browser. |
| CLI or service | stdout/stderr, exit code, health/version, response and resource readback | Host shell/exec tool and project public CLI/API commands. Footwork does not supply a general terminal or service adapter. |
| Saved document, file, image, or media | Read saved content, render/view it, inspect the actual artifact | File tools or the installed document/media skill. For a plain-text value carried by Footwork, `check-file`; for exactly one preserved append, snapshot first and check with `--appended`. |
| Browser-to-app or another context handoff | Source value plus resource, element, observation and step; destination readback | Footwork `read --as NAME`, then `do type/append ... @NAME --from SOURCE_SESSION`; verify the destination separately. Other drivers must preserve equivalent provenance rather than inventing a Footwork session. |

Before the first consequential action, establish a fresh observation of the target and a working action route. Use an already-observed target; do not click guessed IDs or coordinates. Footwork IDs can renumber between commands; prefer an unambiguous observed label resolved on the fresh observation when that command supports it. A launcher/help check establishes executable access only. A health check establishes process readiness only. A real observation establishes what this driver can see now. Report which of those were actually checked.

When access is missing, name the missing executable, permission, profile, connection or unsupported capability. Use an already authorized matching tool when possible; do not silently install/fetch, read key files, start paid providers, or widen OS permissions to make a route work. Never call an untested surface ready.

## Observe, act, read back

Identify the app/window/tab/resource and run-owned session/output before driving. Keep one owner of shared UI state; a verifier must not fight another driver. Start Footwork in a fresh explicit session directory: `start` resets files in that directory. Keep `background_only` unless the task already authorizes broader desktop control.

Observe current state, choose one bounded action, dispatch through the selected driver, then obtain a fresh observation and the requested postcondition. Interpret delivery and receipts at their actual scope. Footwork `do` can exit 0 after a refused or unobservable dispatch; inspect its driver effect, receipt and readback rather than treating the exit status as success. If dispatch is uncertain, reconcile before retry, including before switching drivers. Do not bypass Footwork's gate with `--no-judge` or move to a different tool to evade a refusal.

Carry values between contexts with their source and timestamp/step. A stored carry describes what was read then; it does not promise that the source is unchanged now. Never fabricate a carry from model guesses or transplant IDs between surfaces. For a real Footwork run, use `read`; synthetic carries are appropriate only in explicitly labeled offline harness tests. Recheck the source when freshness matters and verify the exact destination separately. Native and browser `append` have different separator behavior; specify the intended final text and check it rather than assuming a common append contract.

Record commands/actions and selected observations needed to reproduce the result. Keep private captures within the authorized task's ignored/private output; do not collect unrelated screens or secrets. Retain limitations when a driver sees only a subtree, bounded text, viewport, or partial event stream.

Footwork's optional capture helper can journal actions, snapshots, supported network events and gaps around an already selected tab. Use it only through a host-permitted adapter; it neither launches a browser nor grants UI access. See [context-specific mechanics](references/contexts.md) for the module and its constraints.

Then use [pstack-verify](../pstack-verify/SKILL.md) to judge the promised outcome. Adding this skill equips routing and concrete commands; it does not register an MCP server, activate a remote relay, launch a provider, or prove every driver works live.
