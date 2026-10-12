# macOS and APFS accounting

## Measure the target volume

```bash
df -k /System/Volumes/Data
```

Record available KiB before mutation and after each lane. APFS volumes in one container share capacity, so never sum their reported free-space values.

## Separate logical size from recovery

APFS clones share blocks until divergence. Sparse files contain logical ranges without allocated blocks. Hardlinks expose one inode through multiple paths. Directory totals, Finder categories, Docker estimates, and candidate sums therefore differ from physical recovery.

Record logical and allocated bytes as prioritization evidence. APFS clones can make these totals substantially overstate the cache's exclusive footprint, particularly when cached environments share unpacked wheels. Mark reclaimability `unknown` or `partial` when sharing cannot be proved away. Use fresh target-volume free bytes as the completion test.

These are volume-wide interval changes; concurrent writes, deletions and snapshots can contribute. Record the verified owner effects separately from the measured free-space change.

A first-extent comparison cannot establish a file's full sharing or physical reclaimability, especially when installed copies outside the cache were not measured. Keep such probes exploratory; do not relabel an allocated footprint as physical storage or use an estimate to authorize deletion.

## Enforce boundaries

- Resolve the candidate and approved root before classification.
- Keep recursive discovery and deletion on the root's device.
- Treat nested mounts as `unknown` unless separately included and classified.
- Never follow a symlink during recursive deletion.
- Record device, inode, link count, mount ID, and symlink state; revalidate before mutation.

## Protect owner-managed resources

- Never manually delete `Docker.raw`.
- Treat VM bundles, simulators, Photos, Mail, iCloud/File Provider data, Time Machine snapshots, and recovery state as owner-managed objects.
- Check open handles even when an app window appears closed.

## Source

Apple File System and safe file access: https://developer.apple.com/documentation/foundation/about-apple-file-system
