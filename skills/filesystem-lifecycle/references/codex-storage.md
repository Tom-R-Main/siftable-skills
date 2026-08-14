# Codex task storage

Treat a Codex task as a logical resource spanning rollout/session files, indexes, and state-database references. Large JSONL files contain conversation history and persisted tool output; they are not ordinary caches.

## Preferred operation

Use a supported Codex archive, delete, or retention operation when available. Verify that it updates associated metadata and that the task is closed and not currently open.

## Raw-file fallback

Raw deletion is a last resort. Require explicit authorization for the exact closed rollout, inspect only the minimum metadata needed to establish identity and liveness, and account for associated database/index state. If no supported way exists to reconcile metadata, document the mismatch before acting.

Never bulk-delete task history to satisfy a generic free-space target. Never open an unsafe or enormous task in the desktop UI merely to classify it; stream bounded metadata instead.
