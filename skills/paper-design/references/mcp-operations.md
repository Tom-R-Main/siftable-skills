# Paper MCP operations

This reference records what was exercised against Paper Desktop MCP `0.5.3` on 2026-08-08. Always load the live `paper-mcp-instructions` guide and current tool schemas first; Paper changes quickly.

## Capability status

| Capability | Status in the 2026-08-08 lab | Notes |
| --- | --- | --- |
| Create and open a file | Tested | A separate `Paper Skill Lab — 2026-08-08` file was used. |
| Read file, page, artboard, and token context | Tested | `get_basic_info` returned artboards, dimensions, fonts, and token hash. |
| Font lookup | Tested | Arial and Helvetica Neue returned exact weights; `system-ui` lookup reported unavailable. |
| Create and update tokens | Tested | 35 tokens across all supported namespaces were created; font and signal tokens were updated. |
| Create desktop and mobile artboards | Tested | 1440×900 and 390×844 artboards rendered correctly. |
| Insert HTML as editable layers | Tested | Flex layouts, text, rules, and inline SVG became editable subtrees. |
| Replace a subtree with HTML | Tested | A placeholder was replaced by a complete action group. |
| `<x-paper-clone>` | Tested | Desktop rows cloned into mobile and accepted top-level width/padding overrides. |
| Deep duplicate plus descendant map | Tested | `duplicate_nodes` returned descendant mappings used for immediate batch edits. |
| Batch text, layer-name, and style edits | Tested | `set_text_content`, `rename_nodes`, and `update_styles` preserved the structure. |
| Reorder existing nodes | Tested | `move_nodes` changed order and restored it while preserving identity. |
| SVG as a real subtree | Tested | Paths and circles remained inspectable vector descendants and retained token fills/strokes. |
| Screenshot checkpoints | Tested | Both artboards were reviewed at native resolution. |
| Tree, computed styles, token search | Tested | Tree summary, batched styles, and `find_nodes` by token all returned exact structure. |
| JSX/Tailwind extraction | Tested | Output preserved structure and tokens but required typography normalization. |
| Finish working indicator | Tested | Worked even after the weekly quota was exhausted. |
| PNG/SVG export and combined PDF | Tested on Pro | Desktop PNG was 1440×900, mobile `@2x` PNG was 780×1688, and the two-page combined PDF rendered cleanly. |
| Comment inspection | Tested | The lab contained no threads, and the all-status read completed successfully. |
| Snapshot, manual vector editing, shaders | Docs/UI only | Not exercised through MCP in this lab. |

## Start and finish protocol

1. Load `get_guide({ topic: "paper-mcp-instructions" })` once per session.
2. Read with `get_basic_info`; read `get_selection` if the user is pointing at a frame.
3. Use `get_tree_summary` for cheap orientation before requesting full JSX.
4. Call `get_screenshot` before edits when preserving an existing direction matters.
5. Mutate incrementally and screenshot after meaningful groups.
6. Call `finish_working_on_nodes` at completion or when blocked.

Use `fileId` explicitly when more than one file may be open. Otherwise the most recently opened file becomes sticky for the session.

## Read operations

- `list_files`, `open_file`, `get_basic_info`, `get_selection`
- `get_node_info`, `get_children`, `get_tree_summary`
- `get_screenshot`, `get_jsx`, `get_computed_styles`, `get_fill_image`
- `find_nodes` for token, literal style, or text matching
- `get_tokens` in `json`, `css`, or `tailwind` format
- `get_font_family_info`, `get_guide`
- comment-thread listing and reading
- image/video export and combined PDF export

Prefer the cheapest exact read. A tree summary is better than full JSX for orientation; computed styles are better than screenshots for implementation values.

## Mutation operations

- `create_file`, `create_page`, `create_artboard`
- `write_html` in `insert-children` or `replace` mode
- `duplicate_nodes`, `move_nodes`
- `set_text_content`, `rename_nodes`, `update_styles`
- `create_tokens`, `set_tokens`
- `set_comment_thread_status`
- `delete_nodes` only after verifying the exact node and parent

Treat every mutation as scoped to a named artboard or selected subtree. Avoid broad deletion.

## Tested findings and gotchas

- HTML clones retained descendant content and styles, but the cloned root layer name became `Frame`. Rename meaningful clones immediately.
- Fixed icon and status widths allowed the same cloned rows to wrap cleanly on mobile.
- The official mobile status-bar guide uses `system-ui`; it rendered correctly even though font lookup said the family was unavailable. Use the official guide markup unchanged except color.
- Token-bound nodes remained discoverable by `find_nodes` after a token value changed, confirming the reference rather than a literal style was preserved.
- Tailwind JSX extraction mapped top-level tokenized typography well but emitted explicit `system-ui` font classes on some descendants. Treat export as evidence and scaffolding, not finished code.
- `get_computed_styles` can preserve CSS variable references rather than resolving everything to literals. Pair it with `get_tokens` when implementing.
- A normal read tool can consume quota. When the limit error appears, do not spend calls probing other nonessential tools.
- A full-artboard SVG export favored visual fidelity: it used a large `<foreignObject>` with expanded computed CSS and embedded fonts. Do not treat that artifact as clean production SVG; use the actual SVG subtree or optimize deliberately.
- The combined PDF preserved both artboards visually, but it was not a tagged PDF. Treat Paper PDF export as a presentation/review artifact unless accessibility is independently remediated and verified.

## Quota preflight

As of 2026-08-08, Paper's official pricing page lists 100 MCP tool calls per week on Free and 1,000,000 per week on Pro. Verify the current pricing before making a recommendation.

For Free-plan work:

- inspect once, then batch read requests;
- batch text/style/token updates;
- duplicate known structures instead of regenerating them;
- use 1× screenshots unless small text requires 2×;
- avoid repeated `get_basic_info` and full JSX calls;
- reserve calls for final screenshots and code extraction;
- stop immediately when the quota response includes a reset interval.

## Safe operation recipes

### Existing design edit

`get_basic_info` → `get_selection` → `get_tree_summary` → `get_screenshot` → exact mutation → `get_screenshot` → targeted fix → `finish_working_on_nodes`

### New responsive concept

brief → font lookup → token inspection/creation → desktop artboard → incremental groups → screenshot → mobile artboard → reuse/recompose → screenshot → `finish_working_on_nodes`

Do not merely scale the desktop. Preserve token semantics while changing composition and line wrapping for the narrower frame.

### Paper-to-code

`get_tree_summary` → `get_jsx` → batched `get_computed_styles` → `get_tokens` → `get_fill_image` as needed → implement in repository conventions → run and screenshot application → compare to Paper

### Clone-first repetition

Build one correct row or card, duplicate it, then use the descendant map for batch content edits. Use `<x-paper-clone>` when placing existing subtrees inline in new HTML. Rename clone roots if the layer tree matters.

## Sources

- https://paper.design/docs/mcp
- https://paper.design/pricing
- https://paper.design/build-log
