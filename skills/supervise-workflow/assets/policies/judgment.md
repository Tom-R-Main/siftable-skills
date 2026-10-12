# Trusted judgment

Classify findings as:

- **P0:** acceptance failure, data loss, security issue, or broken verification.
- **P1:** real bug, material scope violation, or near-term reliability failure.
- **P2:** defensible to ship but should be fixed or covered.
- **P3:** non-blocking nit.

Require concrete evidence for every P0/P1. Independent verification outranks the
worker report. A worker claiming verification passed when the monitor rerun fails
is dishonesty and requires escalation.

Treat implementation report shape separately from the deliverable. A report-only
schema defect is evidence quality, not a remediation finding, when integrity and
monitor-run scope/verify/visual/copy gates are green. It must never override an
independent review, and it never permits acceptance without the required review.

For tournaments, distinguish `ready_for_selection` from `ready_for_judgment`.
Selection permits a human side-by-side decision despite red verify/visual/copy
evidence; it never means ship-ready. Require an explicit selected workspace, all
strict monitor gates, and an accepting required review before final judgment.
Browser and copy-policy infrastructure failures call for monitor-only `reverify`,
not worker remediation. Sol may polish only the selected candidate.

Return a verdict with `findings`, `overall_correctness`, `explanation`,
`confidence`, and `decision`.

| Condition | Decision |
|---|---|
| Correct, verify and scope pass, no P0/P1, confidence >= 0.8 | accept |
| Repairable failure with fewer than two remediation rounds | remediate |
| Confidence below 0.8, dishonesty, serious scope/security issue, or exhausted rounds | escalate |
