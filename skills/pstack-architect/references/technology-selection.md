# Performance and technology selection

The maintained decision framework is [architecture selection](../../architecture-selection/SKILL.md). Use it when language, framework, runtime, dependency, or execution placement is a material design choice, then return to interface/ownership planning.

It preserves the performance-first policy: compare complete-system costs and concrete platform/component benefits; consider native applications directly; treat developer familiarity as a weak tie-breaker; retain correctness, reliability, maintenance, and migration obligations. It adds defect-class reasoning, memory shape, boundary accounting, behavioral oracles, and explicit evidence limits. A bounded change in an established stack does not reopen the stack decision.
