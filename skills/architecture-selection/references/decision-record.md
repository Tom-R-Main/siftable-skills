# Compact decision record

Adapt this to the existing plan/ADR; a small choice may need one paragraph. Do not invent budgets or a document hierarchy. Writing a record does not authorize implementing a migration.

**Decision and scope:** component, new/extend/port/replace, and explicit constraints.

**Workload and objective:** input distribution/limits, frequency/concurrency, trust, heap/lifetimes, hardware/host; hard requirements and primary optimization goal. Mark unknowns.

**Execution design:** placement → algorithm/representation → ownership/scheduling → language/runtime/framework → boundaries. Identify the implementation assets being reused.

| Candidate | Mechanism and expected benefit | Hard-constraint fit | Evidence and limits | Residual risk / cost |
|---|---|---|---|---|
| Selected path | Concrete work saved or capability gained | Pass/fail/unknown | Observed / source-backed / inferred / unavailable | Remaining defect classes, operations, migration |
| Strongest alternative, including current stack where applicable | Different mechanism | Pass/fail/unknown | Same semantics and workload? | Why it loses or when it would win |

**Boundary contract:** data shape/volume, allocate/retain/mutate/free, concurrency/cancel/completion, errors, authority and failure containment. Omit when no new boundary is proposed.

**Decisive check:** independent correctness oracle; representative workload and intended production configuration; acceptance threshold if known; adverse case; what was actually executed versus proposed.

**Historical basis, when relevant:** decision date/revision, stated rationale versus reconstruction, proposal/merge/revert/supersession status, and which constraints changed.

**Recommendation:** why this design wins given current evidence, unresolved assumptions, and the observation that reverses the decision. Distinguish a provisional choice from a demonstrated gain.

**Handoff:** interface/ownership sketch, relevant installed language/domain skills, ordered implementation/validation, compatibility and recovery obligations. Preserve any existing approval boundary.
