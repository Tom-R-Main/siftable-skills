# Design provenance

Created 2026-10-30 as a repository-learning route for tometo-mode. This is original workflow/tool code informed by implementation inspection; it does not vendor upstream source. The package is staged in the active project; global installation is separate.

| Source | Inspected revision | Borrowed decision |
|---|---|---|
| agent-skills | a117418ab3596c59d641cab4cb89bdbe560fb277 | Minimum falsifiable trace, evidence classes, counterexamples, stopping rule. |
| gitnexus | 401fc96c16426cd5c261ae7e54b5a667516fa452 | Content-based freshness and visible graph incompleteness; optional structural lane. |
| octocode | c265e3f9413161c900cbf4aa70d451b8e6b3920a | Bounded ranges, precise anchors, explicit partial/fallback states. |
| repomix | 7d7b28bf3e651e2f34a284ca9c91074edfe1b88d | Selected context export; compression/security caveats. |
| opensrc | b51de60867e806da1839b33dd29c29424f12521b | Verify actual source identity instead of requested version labels. |
| matt-pocockskills | a496f5513d4a4cf889bc48e189e579f4b0bdf6aa | Progressive disclosure; mechanical lessons become code. |
| cursor-plugins | 4dd1d05818d19792e7cd6e818f1667f95f7e1dbe | Non-overlapping exploration, epistemic boundaries, scoped retrospectives. |
| deepwiki-open | cdd19ca055aff4985eeb52e8515774471b967d26 | Citation grounding and source freshness are distinct from generated presentation. |
| ghidra | 4718f50d9941b9d7b7ebd1febc2982f055560a73 | Bounded staged analysis and partial completion; binary lane only when needed. |

The attached research synthesis was treated as source material. Primary abstracts qualify its claims: CodeCompass tested a particular repository/task distribution; Codebase-Memory reports reduced token use alongside lower aggregate answer quality (83% versus 92%). Graph navigation is therefore a conditional tool choice, not an assumption of universally better comprehension. See https://arxiv.org/abs/2602.20048 and https://arxiv.org/abs/2603.27277. Prometheus's revised title and abstract emphasize working memory: https://arxiv.org/abs/2507.19942.
