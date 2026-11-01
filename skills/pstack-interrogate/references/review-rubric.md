# Review rubric

Inspect relevant lenses, not a mandatory checklist for every change.

- **Requirement conformance:** Does the observable result satisfy the stated intent and non-goals? Are required callers and entry points covered?
- **Correctness:** Trace boundary values, error paths, encoding, state transitions, cancellation, retries, and partial execution where relevant. Show the path that makes a failure possible.
- **Ownership and concurrency:** Who writes shared state? Does the mechanism prevent inconsistent intermediate states and time-of-check/time-of-use errors? Is replay safe after partial failure?
- **Root cause:** Does the change repair the mechanism or hide its symptom? Before removing a guard or retry, prove what made it necessary and what now enforces that condition.
- **Structure:** Do data and interfaces express the domain? Check accidental coupling, scattered validation, leaked implementation details, and needless layers against actual callers. Preserve required compatibility during staged migrations.
- **Technology choice:** For a scoped architecture decision, does the language/framework choice serve the workload and resource goals? Challenge choices based mainly on familiarity, boilerplate, or manual shipping speed; account for available agent skills and toolchain support. Concrete component, SDK, platform, or UI benefits can justify higher abstractions. Preserve correctness, safety, and the authorized migration boundary.
- **Performance and resources:** Trace avoidable allocation, copying, serialization, runtime overhead, I/O, and boundary crossings in the changed path. Judge latency, throughput, memory, and startup claims using comparable representative evidence, including integration costs. Language names or isolated kernel timings alone do not establish a system improvement.
- **Verification:** Do checks exercise public behavior and literal expected results? Does a passing unit test leave an integration boundary untested? Inspect artifacts rather than trusting worker summaries.
- **Security:** Trace an actual input path to the dangerous sink, missing authorization, or secret exposure. Avoid hypothetical vulnerability lists.
- **Complexity:** Flag concrete avoidable maintenance cost in the scoped change. Suggest larger cleanups separately; do not invent size limits or force a rewrite.

For each actionable finding: location, trigger/precondition, causal path, consequence, evidence, and the smallest useful correction. Distinguish observed reproduction from static reasoning and unresolved suspicion.
