---
name: architecture-selection
description: Choose or reassess programming languages, frameworks, runtimes, dependencies, and execution boundaries using workload constraints and checkable evidence. Use for consequential stack decisions or migration proposals, not ordinary implementation in an established stack.
---

# Architecture selection

Produce a defensible choice and the test that could overturn it. Select the execution design before loading implementation skills. Respect explicit user choices, repository contracts, and the task's design/review/implementation scope; a recommendation grants no rewrite or deployment authority.

## Establish the decision

Read actual callers, manifests, deployment constraints, existing decisions, and available verification. Trace consequential claims through the selected configuration, owning implementation, actual consumer, and decisive test. Resolve stale descriptions against executable paths; inspect target-specific enforcement and fallback behavior, not just API availability. Identify whether this is a new system, an extension, a constrained port, or a replacement. Keep the current system as a candidate for existing products. A small fix does not reopen the stack.

State the workload: typical and largest inputs, frequency, concurrency, key skew/cardinality, lifetime/heap shape, trust boundaries, target hardware, and required platform capabilities. Separate hard constraints from objectives. Name the primary objective and relevant budgets: useful throughput at a latency/error target, tail latency, CPU per operation, peak memory, startup, distribution size, responsiveness, or energy measured on the target. Unknown budgets remain unknown. Meeting a budget establishes feasibility, not optimality.

Prefer complete-system performance and resource efficiency subject to required semantics, security, reliability, accessibility, and operability. Consider native implementations as first-class whole applications or subsystems. Do not require building a high-level version first. Agent assistance can change implementation feasibility; developer familiarity and historical manual shipping speed are weak tie-breakers. Concrete delivery constraints, available expertise for incident recovery, maintenance, and migration risk still count.

## Compare complete designs

Work in this order, revisiting earlier choices when evidence changes:

1. **Placement:** browser, server, database/query engine, GPU, device, or existing OS/library facility. Distinguish the language directing work from the engine executing it.
2. **Algorithm and representation:** eliminate work; choose layout, indexing, batching, and data movement before attributing cost to a language.
3. **Ownership and scheduling:** allocation/retention, mutation, admission bounds, cancellation, completion, and recovery. Identify the defect classes that matter and what rejects or detects them.
4. **Implementation:** language, runtime, framework, libraries, target/toolchain support, and artifact distribution. These are separate choices: TypeScript does not select React; Rust does not select Wasm or microservices.
5. **Boundaries:** modules, FFI, workers, processes, remote services. Credit each boundary's specific benefit and charge its conversions, copies, retained memory, scheduling, startup, deployment, and failure costs.

Shortlist the few genuinely different viable paths. Read [candidate guidance](references/candidates.md) for language/framework choices, and [boundaries and replacements](references/boundaries-and-replacements.md) when splitting, porting, or owning dependencies. A simple in-language design is a useful baseline; fewer languages/processes is a preference to test, not a reason to discard isolation, independent scaling, hardware placement, or reliability requirements.

For each candidate record the proposed mechanism, hard-constraint fit, strongest evidence, main residual risk, and a disconfirming observation. Compare equivalent validation, numeric accuracy, error behavior, durability, compatibility, and recovery. Reject a candidate that fails a hard constraint rather than hiding the failure inside a weighted score. Check reachable fallback, degraded, rollout, and dependency-unavailable configurations too; specify rejection or fail-closed behavior when fallback cannot preserve a hard requirement. Do not manufacture precise scores from unknowns.

## Resolve decisive uncertainty

Use source and current primary documentation for capability claims. Bind version-sensitive APIs to the actual target toolchain and retrieve relevant definitions/examples; a version in a prompt is insufficient. Inspect available compiler, build, debugging, and runtime observation paths before promising that agents can deliver the design.

For an existing system, locate the relevant cost with profiles/traces and capture a baseline. For greenfield work, use a representative slice when measurement could change the decision. Test the complete path under intended production settings, with safety checks/configuration actually intended for deployment. Include cold and warm behavior, realistic concurrency, overload/memory pressure, and a case favorable to the alternative when relevant. Measure CPU, memory, and latency separately; faster inner work may improve capacity without appreciably reducing waiting time.

Establish an independent correctness oracle before interpreting speed. Use external vectors, contracts, known behavior, or independently derived properties; challenge it with a deliberate wrong result when practical. Roundtrips alone can hide compatible mistakes. Compiler acceptance, sanitizer passes, benchmark rankings, and model confidence do not prove product correctness.

For repository or PR retrospectives, read [decision history](references/decision-history.md) to reconstruct the choice without hindsight.

Read [evidence rules](references/evidence.md) when evaluating research, benchmark claims, safety guarantees, or an uncertain recommendation. If evidence is unavailable, make the best-supported provisional choice, state the assumption and next discriminating check, and continue work already authorized. Do not require benchmarking every routine choice or invent an approval stage. Repeated uninformative experiments call for a revised hypothesis, not an arbitrary universal retry count.

## Deliver and hand off

Put a compact record in the existing plan or an authorized decision document; use [the decision template](references/decision-record.md) for a substantial comparison. Include the selected design, why alternatives lose, evidence level, uncertainty, acceptance check, and reconsideration trigger. State whether the result is a recommendation, a source-backed capability assessment, a prototype result, or a measured production-path result.

Pass the chosen placement, contracts, resource goals, and unresolved checks to interface/ownership planning and the installed language/domain skills. Those skills own implementation and toolchain mechanics; they must not silently reselect the stack. In Tometo, this is a conditional selection phase before architecture sketches and implementation, not a second orchestrator. A design-only task ends with the decision; an authorized implementation continues within scope.
