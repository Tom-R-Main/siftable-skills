#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in -h|--help|help)
 cat <<'EOF'
Usage: playwright_cli.sh <playwright-cli arguments>
Uses an already installed playwright-cli or PLAYWRIGHT_CLI_BIN executable.
No packages, browsers, profiles, providers, or credentials are installed.
For the external CLI command list, invoke the configured executable --help.
EOF
 exit 0;; esac
cli="${PLAYWRIGHT_CLI_BIN:-playwright-cli}"
command -v "$cli" >/dev/null 2>&1 || { printf 'Configure an installed Playwright CLI; no automatic fetch is performed.
' >&2; exit 1; }
has_session_flag=false
for arg in "$@"; do case "$arg" in --session|--session=*) has_session_flag=true;; esac; done
if [[ "$has_session_flag" == false && -n "${PLAYWRIGHT_CLI_SESSION:-}" ]]; then
  exec "$cli" --session "$PLAYWRIGHT_CLI_SESSION" "$@"
fi
exec "$cli" "$@"
