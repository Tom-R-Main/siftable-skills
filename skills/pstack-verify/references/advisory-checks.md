# Optional advisory code checks

Use for a requested duplication, complexity, or test-strength assessment, or a concrete uncertainty in consequential changed logic. Ordinary feature work does not require these checks. Select only the relevant check and prefer the project's existing installed tooling. This reference creates no mandatory metric gate or tool-installation authority; preserve existing repository-required checks.

## Duplicate candidates and complexity

Dryer is optional and advisory. Before running it, establish the installed version, supported input languages, selection semantics, and permitted report location. Check for implicit package or parser-grammar downloads as well as bootstrap installation; those follow the task's existing network and installation approval, even when the launcher is already installed. If the tool is unavailable, report that limitation and continue the source assessment.

Compare the intended candidates against the intended corpus. A changed-files-only scan does not prove absence of duplication against unchanged code. Record filters, skipped files, parser warnings, and unanalysed regions. Missing candidates after incomplete parsing are incomplete evidence. Confirm the report belongs to this artifact and invocation: an empty scan may leave a previous snapshot intact.

Treat a similarity score as shared normalized structure, not behavioral equivalence, a percentage of removable lines, or permission to refactor. Normalization can erase literals, local-variable relationships, and executable details; set-based fingerprints underweight repeated structures. Trace candidates through callers, domain ownership, and likely reasons to change before recommending consolidation. Similar code can belong to independently evolving behaviors.

Use complexity and coverage measurements to prioritize inspection. State their scope and measurement limits; missing or failed coverage is unknown rather than an invented zero. Do not introduce universal CRAP, duplication, coverage, or mutation-score targets. Recommend a structural change only when it improves the scoped behavior or demonstrable maintenance cost. An assessment does not authorize code edits, gates, or hooks.

For an authorized test-pruning decision, follow the [test-preservation guidance](../SKILL.md#drive-observe-challenge) before removing coverage.

## Targeted mutation testing

Choose this only when a specific test-sensitivity question justifies it, such as a consequential guard, retry, permission, or regression path. Bound the source scope and cost. Reuse [verification isolation](../../pstack-create-verification-skill/references/isolation.md) for baseline and mutant runs; copied source overlays do not by themselves confine test effects.

Capture a passing baseline and the relevant source, tests, dependencies, configuration, tool version, and runtime inputs. Confirm each intended mutation landed. Distinguish a behavioral assertion detecting the defect from an invalid mutation, compilation/import failure, runner error, or timeout. A tool's generic killed count alone cannot establish test sensitivity. Assess surviving mutants against the promised behavior; justify equivalence before dismissing one. Strengthen tests for meaningful missing behavior, not incidental implementation details or a perfect score.

Reuse cached results only when the inputs relevant to that evidence remain valid. Unchanged function text cannot preserve a kill after tests, dependencies, or configuration changed. Label carried historical results and rerun affected checks when their inputs change. Restore only run-owned experiment changes and recheck the final artifact; sensitivity remains distinct from reproducing an original defect.

Report the checked artifact, command and selection, baseline, meaningful results, invalid or unresolved cases, cache validity, and remaining coverage limits. These checks supplement proof at the actual public boundary; they do not establish production behavior or authorize release.

Reviewed tool versions, observed caveats, and upstream sources: [grounding](grounding.md#targeted-refresh-2026-10-26).
