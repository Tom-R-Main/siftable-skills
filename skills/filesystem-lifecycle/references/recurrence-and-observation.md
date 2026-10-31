# Receipt comparison and optional observation

## Compare

Compare only explicitly supplied before/after inventories and optional apply receipts. Do not search conversation history or discover receipts outside that scope. Preserve timestamps, filesystem/source identity and completeness.

- `recreated` requires a successful removal receipt before the current observation for the same resource and compatible filesystem.
- Without that evidence, a newly seen path is `newly_observed`.
- A missing path in partial coverage is `not_assessed`; absence from a report alone does not prove removal.
- Distinguish the resource's current identity from its stable path. Inode reuse or a different resource at the same path limits attribution.
- Report elapsed time since verified removal, current allocated footprint, prior measured free-space change and known recovery costs. Unknown costs remain unknown.
- Prior free-space change is a volume-wide interval observation, not an exclusive measurement of that candidate's freed blocks.

Recommendations must follow the observations: for example, repeated dependency hydration may justify package-manager cache reuse; a recreated VM bundle may justify reviewing the owner's retention settings. Do not edit settings, install tools, schedule work, kill processes or automatically delete the regrown resource.

## Mole

Mole is an optional observation source. Use only the installed executable's version and supported structured analysis/status/history surfaces. Record version, operation, scope, completeness and any bounded failure. Missing or incompatible tools produce unavailable evidence; they do not trigger installation.

Do not call cleanup, optimization, uninstall, purge, installer, slimming, update, configuration or dry-run commands through this adapter. Some dry runs write persistent preview files; real cleanup rescans rather than executing this skill's frozen IDs. Mole's `cleanable` field describes its catalog, not this skill's deletion authority.

Keep imported partial/unavailable markers. Bound process duration and captured output, use argv rather than a shell, and avoid exposing arbitrary stderr or command-line secrets. A report can explain what Mole observed without treating its history as an authenticated authorization record.

## Sources

Design references, not executable instructions:

- [Mole macOS observation contract](https://github.com/tw93/Mole/blob/main/skills/mole/references/macos.md)
- [mac-storage-doctor ownership and coverage ideas](https://github.com/SomSamantray/mac-storage-doctor/blob/main/SKILL.md)
- [Linux disk-storage diagnosis](https://github.com/peterbamuhigire/linux-skills/blob/main/06-storage-and-filesystems/linux-disk-storage/SKILL.md)
