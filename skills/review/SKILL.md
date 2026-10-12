---
name: review
description: "Review a scoped code diff through pstack-interrogate. Use when the user invokes review or requests its retained compatibility route."
---

# review compatibility route

The former gstack workflow at this entrypoint has been replaced locally. Read [pstack-interrogate](../pstack-interrogate/SKILL.md) and follow it for the requested task.

Review the requested diff read-only. Return findings and evidence; do not apply fixes or emit a legacy gstack review receipt.

Do not load the old workflow from the shared gstack checkout as a fallback. If a retained gstack consumer requires its own report format or receipt, explain that this route did not produce that evidence; let its authorized native verification run or report the unmet gate. Never fabricate a legacy specialist pass or bypass a release gate.
