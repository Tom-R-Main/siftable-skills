#!/usr/bin/env bash
set -euo pipefail
usage() {
  cat <<'EOF'
Usage: design-reference.sh DESCRIPTION /absolute/task-scratch/reference.png
Requires DESIGN_REFERENCE_BIN: approved external generator supporting
--description TEXT --output ABSOLUTE_PATH, with opaque configured credentials.
The adapter does not supply image generation, authentication, or a provider.
EOF
}
case "${1:-}" in -h|--help|help) usage; exit 0;; esac
[[ $# -eq 2 && -n "$1" && "$2" = /* && ! -e "$2" && ! -L "$2" ]] || { usage; exit 2; }
[[ -n "${DESIGN_REFERENCE_BIN:-}" && "$DESIGN_REFERENCE_BIN" = /* && -x "$DESIGN_REFERENCE_BIN" ]] || {
 printf 'Set DESIGN_REFERENCE_BIN to an approved generator executable.
' >&2; exit 1;
}
[[ -d "$(dirname "$2")" ]] || { printf 'Output parent must already exist.
' >&2; exit 2; }
command -v python3 >/dev/null || { printf 'python3 is required for PNG readback.
' >&2; exit 1; }
"$DESIGN_REFERENCE_BIN" --description "$1" --output "$2" >&2
python3 - "$2" <<'PYCODE'
import pathlib,sys
p=pathlib.Path(sys.argv[1])
if p.is_symlink() or not p.is_file():
 raise SystemExit('Generator did not produce an ordinary file at the requested path')
with p.open('rb') as f:
 if f.read(8)!=b'\x89PNG\r\n\x1a\n': raise SystemExit('Generator output is not PNG')
print(p)
PYCODE
