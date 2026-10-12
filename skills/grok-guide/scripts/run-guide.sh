#!/usr/bin/env bash
set -euo pipefail
usage() {
  cat <<'EOF'
Usage: run-guide.sh doctor | run /absolute/request.json
Requires GROK_GUIDE_BIN: an absolute user-configured compatible executable.
The external runtime must implement doctor and run, validate grok-guide.request.v2,
enforce disclosure/credential policy, and use opaque configured credentials.
No harness, provider, authentication or inference capability is bundled.
EOF
}
case "${1:-}" in -h|--help|help) usage; exit 0;; esac
[[ -n "${GROK_GUIDE_BIN:-}" && "$GROK_GUIDE_BIN" = /* && -x "$GROK_GUIDE_BIN" ]] || {
  printf 'Set GROK_GUIDE_BIN to an approved compatible absolute executable.
' >&2; exit 1;
}
case "${1:-}" in
 doctor) [[ $# -eq 1 ]] || { usage; exit 2; }; exec "$GROK_GUIDE_BIN" doctor ;;
 run)
  [[ $# -eq 2 && "$2" = /* && -f "$2" ]] || { usage; exit 2; }
  exec "$GROK_GUIDE_BIN" run "$2" ;;
 *) usage; exit 2;;
esac
