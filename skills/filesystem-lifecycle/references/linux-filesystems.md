# Linux filesystem accounting

## Boundaries

Resolve each approved root and keep discovery/deletion on its starting `st_dev`. Add another mount as a separate root. Detect bind mounts and nested mount points before recursive deletion; a shared device number alone may not distinguish every bind mount.

## Accounting

Record logical size, allocated blocks, inode/link count, filesystem/mount identity, and available bytes on the target mount. Reflinks on Btrfs/XFS, sparse files, hardlinks, overlay filesystems, and container layers can make candidate size differ from recovery.

Use fresh `statvfs`/`df` free bytes for the postcondition. Do not sum free space across mounts or promise recovery from `du` alone.

## Platform caveats

Treat `/proc`, `/sys`, `/dev`, container overlay mounts, remote filesystems, and FUSE mounts as out of generic recursive scope. Use owner-specific operations for package managers, containers, snapshots, and system journals.
