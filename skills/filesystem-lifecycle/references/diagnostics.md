# Passive diagnosis and reports

Use `doctor` to explain pressure before selecting a removal. Require explicit roots for recursive observation. The volume supplies capacity evidence; it is not an implicit recursive root.

Keep metadata traversal bounded by depth, entry count and elapsed time. Report inaccessible, excluded, timed-out and deferred areas. A partial size is observed coverage, not a total; unavailable is not zero. Do not follow symlinks or cross mounts, including same-device bind mounts. Exclude cloud-provider paths and sensitive user-data locations. Inspect metadata only; never open environment/key files or document bodies.

Distinguish capacity exhaustion, inode exhaustion, deleted-open files, large directory footprints and unexplained accounting differences. A process owning an unlinked file is diagnostic evidence, not authority to restart or kill it. A snapshot observation does not authorize thinning snapshots.

On macOS, keep filesystem available bytes and APFS container observations separate. Shared capacity must not be summed across volumes. Allocated blocks do not establish exclusive APFS ownership; snapshots, clones and concurrent writers limit attribution. On Linux, mount identity and inode availability supplement byte counts. Do not prescribe partition, swap, journal-retention or network-mount changes through this skill.

## Resource catalog

The bundled catalog describes discovery and explanation. Entries declare platform, path pattern, owner resolver, required probes, recovery method and supported actions. Entries default to inventory-only. A catalog match cannot authorize deletion, invoke an arbitrary command, or turn an unknown resource into `safe_now`. Executable adapters retain their independent eligibility checks.

Owner attribution may use bounded, allowlisted bundle or launchd metadata. A matching vendor name does not prove disposability. Missing, ambiguous or inaccessible ownership evidence remains explicit.

## Report contract

Render one table:

`Resource | Owner/purpose | Classification | Allocated size | Recovery confidence | Blocker | Proposed action`

Show coverage gaps after the table. For apply receipts, lead with measured filesystem free-space change and show partial/uncertain actions prominently. Keep logical bytes, allocated footprint, estimated recovery and observed free-space change distinct. Ease of removal is not a safety classification.

JSON is the machine-readable evidence; Markdown is a view of the same record. Output defaults to stdout. Persist only to the requested output path. Inspection has no scheduled follow-up and does not mutate owner settings.
