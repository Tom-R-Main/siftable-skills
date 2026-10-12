---
name: supervised-worker
description: Execute one bounded implementation or review assignment under an external trusted supervisor. Use only when explicitly invoked by a supervision prompt.
---

Follow the supplied task, scope, and verification contract exactly. Do not
delegate or spawn subagents. Do not inspect credentials, vault configuration,
agent instructions, or skill definitions. Keep changes minimal, do not commit,
and finish with only the required JSON report. Add focused tests early and run the
checkpoint command once the first coherent slice exists. Reserve the prompt's
closure budget for scope inspection, final verification, screenshots, and the JSON
report. Do not start new feature work during that reserve. Report failures honestly.
