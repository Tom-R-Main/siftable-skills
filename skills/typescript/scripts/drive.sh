#!/usr/bin/env bash
# Generic "did it typecheck, test, build, and actually run?" driver for ANY
# TypeScript project. Run from a package root:
#
#   "$TYPESCRIPT_SKILL_DIR/scripts/drive.sh"            # gates + build + probe a CLI bin
#   "$TYPESCRIPT_SKILL_DIR/scripts/drive.sh" --version  # probe bins with a different flag
#
# It runs the gates (ts-gates.sh), runs the `build` script if present, then tries
# to launch the package's declared `bin`(s) once to confirm the artifact starts.
# By default it probes with `--help`; pass a different probe arg as $1.
#
# This is the FLOOR ("it launches"), not the ceiling. Servers, web apps, and
# libraries need per-type driving — see "Run / drive" in SKILL.md.
set -uo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  printf '%s\n' \
    'Usage: drive.sh [probe-argument]' \
    'Run TypeScript gates, build when configured, and probe declared package binaries.' \
    'The probe argument defaults to --help.'
  exit 0
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
probe_arg="${1:---help}"

[[ -f package.json ]] || { echo "no package.json in $PWD — run from a TS project root" >&2; exit 1; }

pm="npm"
if   [[ -f pnpm-lock.yaml ]]; then pm="pnpm"
elif [[ -f yarn.lock      ]]; then pm="yarn"
elif [[ -f bun.lockb || -f bun.lock ]]; then pm="bun"
fi
command -v "$pm" >/dev/null 2>&1 || pm="npm"
run_script() { case "$pm" in yarn) yarn "$1" ;; *) "$pm" run "$1" ;; esac; }
has_script() { node -e 'process.exit((require("./package.json").scripts||{})[process.argv[1]]?0:1)' "$1" 2>/dev/null; }

echo "== gates (typecheck + lint + test) =="
"$here/ts-gates.sh"

if [[ "${SKIP_TS_BUILD:-0}" != "1" ]] && has_script build; then
  echo "== build =="
  run_script build
fi

echo "== launch declared bin(s) =="
# Read the `bin` field: string -> one bin named after the package; object -> map.
# (while-read, not mapfile — macOS ships bash 3.2 which lacks mapfile.)
bins=()
while IFS= read -r line; do
  [[ -n "$line" ]] && bins+=("$line")
done < <(node -e '
  const p=require("./package.json"); const b=p.bin;
  if(!b){process.exit(0);}
  if(typeof b==="string"){console.log(b);}
  else {for(const k of Object.keys(b)) console.log(b[k]);}
' 2>/dev/null)

if (( ${#bins[@]} == 0 )); then
  echo "  (no \"bin\" field — server/web/library project; gates+build are the smoke."
  echo "   Drive the real flow per SKILL.md: boot+curl a server, vite preview a web app,"
  echo "   or 'node -e' a tiny import for a library.)"
  exit 0
fi

fail=0
for entry in "${bins[@]}"; do
  [[ -f "$entry" ]] || { printf '  \033[33mnot built\033[0m  %s (run build?)\n' "$entry"; fail=$((fail+1)); continue; }
  if out="$(node "$entry" "$probe_arg" 2>&1)"; then status=0; else status=$?; fi
  first="$(printf '%s' "$out" | head -1)"
  if [[ -n "$out" ]]; then
    printf '  \033[32mlaunched\033[0m  %-28s %s\n' "$(basename "$entry")" "${first:0:60}"
  else
    printf '  \033[31mno output\033[0m %-28s (exit %d)\n' "$(basename "$entry")" "$status"
    fail=$((fail+1))
  fi
done
exit "$fail"
