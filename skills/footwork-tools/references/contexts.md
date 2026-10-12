# Optional Footwork runtime contract

Adapted from a source inspection of an optional Footwork runtime on 2026-10-02, commit `e3b7b086d96c036763458f6501010dc3a9e4881b`. The runtime is not bundled. These source-relative records are historical provenance, not a public dependency URL or cloud execution claim. Verify the user-configured runtime and supported commands before use. Sources: `jevdual/python/jevdual/cli.py`, `session.py`, `native.py`, `browser_driver.py`, `carry.py`; `tools/browser-inspection/README.md`; `tools/inspection-transport/README.md`.

## Local Footwork executable

Footwork is optional. Set `FOOTWORK_BIN` to a user-configured executable or use an already installed `footwork` on PATH:

```sh
fw="${FOOTWORK_BIN:-footwork}"
command -v "$fw" >/dev/null || { echo "Footwork runtime unavailable" >&2; exit 1; }
"$fw" --help
```

Do not install dependencies, initialize providers, or grant OS permissions automatically. Help verifies executable access only. Native commands require macOS, a compatible driver, and current permissions; Linux/cloud sessions should use the project Playwright harness, shell/API driver, or artifact tools instead. Dedicated browser and model-backed judgments require their own preflight. Installing this skill proves none of those capabilities. Use the documented CLI or an actually exposed connector; never invent MCP methods.

`apps` and `menu --app APP --window TITLE_FRAGMENT` observe native state through Cua Driver. UI access requires the macOS driver and relevant permissions. `start`, `look`, and `read` use driver observations; `do` can invoke TypeSafe judgments, while `s1` and `done` invoke TypeSafe. Provider/key availability must come from an approved mechanism without opening key files or printing values. Automated `run` also selects a System 2 provider; it is not the default when the current agent can drive the operator session.

## Operator session

The following are command templates. Replace app/title/path and element IDs with the actual task and fresh observations. Set `fw` from the configured runtime as above; choose an absolute, new `fw_session` inside the authorized task's private scratch area. Never reuse another run's session directory: `start` unlinks previous session/carry/grant records there.

```sh
"$fw" start "TASK" --app "APP" --window "TITLE_FRAGMENT" --require "OBSERVABLE CRITERION" --session "$fw_session"
"$fw" look --session "$fw_session"
"$fw" look --menu-bar --session "$fw_session"
"$fw" do click OBSERVED_ID --session "$fw_session"
"$fw" do type OBSERVED_FIELD_ID "TASK TEXT" --session "$fw_session"
"$fw" look --session "$fw_session"
"$fw" status --session "$fw_session"
```

`do` also supports `append`, `enter`, `scroll`, `hover`, `key`, `hotkey`, `menu`, and browser `navigate`. Select from the observed menu. IDs renumber between commands: `do append "Scratch note" "TEXT"` resolves an unambiguous observed label on the fresh observation; an exact label wins, ambiguous matches stop. Obtain menu paths with `look --menu-bar` rather than guessing them. Separator difference: native `append` adds a newline if the existing document lacks one; browser `append` inserts the supplied text directly with no separator. Choose text appropriate to that context. Inspect driver effect, receipt and fresh readback: `do` may return exit 0 even when the driver refuses a dispatch or its effect is unobservable. Existing task authorization governs any grant or `--authorize`; these are machine gate inputs, not a reason to request the same permission again. Do not disable the destructive judgment.

For Footwork's own Chrome session, replace the start command with `start "TASK" --browser --url "TASK_URL" ...`. This binds Footwork's dedicated browser/tab and does not inherit an existing host-browser tab or its authentication. Keep the host Browser/Chrome route for a user's selected or signed-in session.

## Carry across contexts and check the file

Choose explicit source and destination session directories. Source element IDs come from a fresh source `look`; destination IDs come from its own `look`.

```sh
"$fw" read OBSERVED_SOURCE_ID --as value --session "$fw_source"
"$fw" snapshot-file "$fw_file" --session "$fw_destination"
"$fw" do append OBSERVED_DESTINATION_ID @value --from "$fw_source" --session "$fw_destination"
```

Save through the destination app's observed, authorized UI. Then read the actual disk artifact:

```sh
"$fw" check-file "$fw_file" @value --from "$fw_source" --session "$fw_destination"
"$fw" check-file "$fw_file" @value --from "$fw_source" --appended --session "$fw_destination"
```

Ordinary `check-file` accepts an exact plain-text line; it does not prove the rest of the file is preserved, the value appears once, or a rich document renders correctly. `--appended` checks the file against its pre-action snapshot plus one final carried value; use it when that is the promised outcome. Success exits 0, a content mismatch exits 6, and a missing carry/snapshot exits 4. These checks require no UI or model provider. `done "ANSWER" --context-from SOURCE_SESSION --session DESTINATION_SESSION` supplies trajectory context to Jev; its judgment is not a substitute for deterministic destination readback.

## Extra browser evidence

An optional runtime's source-relative `tools/browser-inspection/capture.mjs` exports `createCapture({tab, cdp, projectRoot, allowedOrigin, ...})`. Read its adjacent README and the active host browser API before integrating. Inject an already selected, permitted tab/CDP adapter. If the host runtime forbids arbitrary module imports or CDP access, use its native evidence facilities; do not bypass those rules.

The helper records action intent, before/after references, supported events, capture gaps and a sealed hash manifest. It does not launch/navigate on import, prove the requested effect, or survive a disconnected runtime. The Playwright bridge at `tools/inspection-transport/playwright-cdp-bridge.mjs` accepts a caller-owned page; it does not launch one. Domain ownership, explicit origin, private artifact opt-ins, bounded capture and cleanup belong to the caller. Avoid attaching a second controller to a shared tab. These helpers add eyes around actions; they do not add authority or certify browser effects.

## Interview grounding

The locally generated transcript of [Matt Pocock and Lauren Tan](https://www.youtube.com/watch?v=MN9dGgmLyso&t=1065s), 17:45–19:10, ties hands and eyes to running the app, interacting as a user, and collecting traces/snapshots so the agent can iterate. The 21:59–24:19 discussion supports reusable deterministic commands for mechanics. Footwork provides concrete operator/session/carry primitives for that loop; native/browser support is source-visible and must be checked on the actual runtime. Full verification provenance: [pstack grounding](../../pstack-verify/references/grounding.md).
