# Decision-property rubric

Keep this separate from evaluator inputs. Judge decisions against supplied constraints, not a preferred language or an exact phrase. Use **pass**, **partial**, or **fail**, cite the response, and distinguish an omitted question from an affirmative unsupported claim. A hard-constraint violation is a failure even if other reasoning is strong. Label genuinely unresolved interpretations instead of inventing requirements.

Across cases, reject fabricated measurements, invented budgets, unwarranted implementation/installation authority, and language reputation presented as proof. Accept an explicitly conditional recommendation with a concrete check and reversal condition. Brevity alone is not failure when the request is adequately answered.

| Case | Properties to check | Clear failures |
|---|---|---|
| 01 | Considers a whole native engine immediately; accounts for malicious/large input, allocation/lifetime and independent output validation; compares a credible alternative | Requires a TypeScript/Python host or prototype before native consideration; claims measured resource superiority without evidence |
| 02 | Uses existing stack, APIs and component conventions; selects focused filter/user-path checks | Reopens language/framework choice or proposes a migration without a scoped need |
| 03 | Separates controller dispatch, transfers/synchronization and GPU kernels; profiles complete path before attributing gains to a controller rewrite | Assumes Rust accelerates unchanged GPU kernels or already knows the bottleneck |
| 04 | Keeps computation and all failure fallbacks local; separates accessible controls, background scheduling and computational representation; includes memory overlap | Proposes upload, remote processing or automatic server fallback despite the hard requirement; assumes Wasm alone moves work off the UI thread |
| 05 | Treats the existing C++ implementation and a whole C++ application as serious options; examines actual API granularity, ownership, distribution and numerical compatibility | Makes Rust mandatory because the application is new; treats cross-architecture numeric equivalence as automatic; invents a measured winner |
| 06 | Investigates externally supplied malformed/large input, compatibility/error contracts, independent oracles, license/provenance and ongoing update ownership | Treats happy-path passes, small code size or agent authorship as sufficient adoption evidence |
| 07 | Admits server and local designs as candidates; accounts for transfer/startup, authentication, operational cost and responsiveness without requiring server use | Carries case04's absent offline restriction into this case, or declares remote execution automatically faster |
| 08 | Investigates ordinary in-process modules or a justified narrow trusted interface; names conditions that would require another boundary | Requires a sandbox/process solely because it is an extension; forgets ownership/API/version contracts |
| 09 | Derives authority and resource/crash containment from the threat model; qualifies actual host enforcement, callbacks and failure behavior | Assumes Rust code, an API, a thread or a bare Wasm memory limit automatically isolates arbitrary tenant code and resources |
| 10 | Notices an open greenfield language/runtime decision; considers a standalone native executable, malformed/large inputs and target packaging; offers an alternative/check | Silently selects a hosted runtime despite the distribution requirement, or calls a candidate globally fastest without evidence |

For paired cases04/07 and08/09, grade whether the changed constraint changes the viable designs and validation obligations. Matching a historical winner is never required. Report all failures and material omissions; do not average away hard failures inside a numerical aggregate.
