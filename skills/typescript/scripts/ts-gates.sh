#!/usr/bin/env bash
# Narrow→broad validation gates for ANY TypeScript project.
# Run from the package/project root (the dir with package.json / tsconfig.json):
#
#   "$TYPESCRIPT_SKILL_DIR/scripts/ts-gates.sh"
#
# Order: typecheck (the real TS gate) → lint → test. Auto-detects the package
# manager, prefers your package.json scripts, and falls back to a direct tsc.
#
# Knobs: SKIP_TS_TYPECHECK=1  SKIP_TS_LINT=1  SKIP_TS_TEST=1
#        TS_TSCONFIG=path/to/tsconfig.json   (override which project to check)
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  printf '%s\n' \
    'Usage: ts-gates.sh' \
    'Run TypeScript typecheck, lint, and test gates from a project root.' \
    'Environment: SKIP_TS_TYPECHECK, SKIP_TS_LINT, SKIP_TS_TEST, TS_TSCONFIG, TS_USE_TSGO.'
  exit 0
fi

if (($# > 0)); then
  printf "[ts-gates] unsupported argument: %s\n" "$1" >&2
  exit 2
fi

log() { printf '[ts-gates] %s\n' "$*"; }

[[ -f package.json || -f tsconfig.json || -n "${TS_TSCONFIG:-}" ]] || {
  printf '[ts-gates] no package.json/tsconfig.json here — run from a TS project root\n' >&2
  exit 1
}

# Honor the package manager declaration or nearest in-scope lockfile.
pm="npm"
if [[ -f package.json ]]; then
  command -v node >/dev/null 2>&1 || { echo 'node is required to inspect package.json' >&2; exit 127; }
  declared_pm="$(node -e 'const p=require("./package.json"); if(p.packageManager) console.log(p.packageManager.split("@")[0]);')"
  if [[ -n "$declared_pm" ]]; then
    case "$declared_pm" in npm|pnpm|yarn|bun) pm="$declared_pm" ;; *) echo "unsupported package manager: $declared_pm" >&2; exit 2 ;; esac
  fi
fi
if [[ -z "${declared_pm:-}" ]]; then
  search_dir="$(pwd -P)"
  workspace_root="$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$search_dir")"
  workspace_root="$(cd "$workspace_root" && pwd -P)"
  while :; do
    if [[ -f "$search_dir/pnpm-lock.yaml" ]]; then pm="pnpm"; break
    elif [[ -f "$search_dir/yarn.lock" ]]; then pm="yarn"; break
    elif [[ -f "$search_dir/bun.lockb" || -f "$search_dir/bun.lock" ]]; then pm="bun"; break
    elif [[ -f "$search_dir/package-lock.json" ]]; then pm="npm"; break
    fi
    [[ "$search_dir" == "$workspace_root" || "$search_dir" == "/" ]] && break
    search_dir="$(dirname "$search_dir")"
  done
fi

# has_script <name> — true if package.json defines a non-placeholder script
has_script() {
  [[ -f package.json ]] || return 1
  node -e '
    const s=(require("./package.json").scripts)||{};
    const v=s[process.argv[1]];
    if(!v) process.exit(1);
    if(/no test specified/.test(v)) process.exit(1);
    process.exit(0);
  ' "$1" 2>/dev/null
}
run_script() {
  command -v "$pm" >/dev/null 2>&1 || { echo "required package manager $pm is unavailable; use the repository pinned installation" >&2; return 127; }
  case "$pm" in
    yarn) yarn "$1" ;;
    *)    "$pm" run "$1" ;;
  esac
}

# Resolve only an installed workspace compiler. Repository scripts stay first.
find_compiler() {
  local search_dir workspace_root
  search_dir="$(pwd -P)"
  workspace_root="$(git rev-parse --show-toplevel 2>/dev/null || printf '%s' "$search_dir")"
  workspace_root="$(cd "$workspace_root" && pwd -P)"
  while :; do
    if [[ -x "$search_dir/node_modules/.bin/tsc" ]]; then
      TSC="$search_dir/node_modules/.bin/tsc"
      return 0
    fi
    [[ "$search_dir" == "$workspace_root" || "$search_dir" == "/" ]] && break
    search_dir="$(dirname "$search_dir")"
  done
  printf '[ts-gates] no installed workspace TypeScript compiler; install locked dependencies with authorization or use the repository typecheck script\n' >&2
  return 1
}
log "pm=$pm"

# --- 1. typecheck (the gate that matters most) ---
if [[ "${SKIP_TS_TYPECHECK:-0}" != "1" ]]; then
  if has_script typecheck; then
    log "$pm run typecheck"; run_script typecheck
  elif has_script type-check; then
    log "$pm run type-check"; run_script type-check
  else
    cfg="${TS_TSCONFIG:-tsconfig.json}"
    if [[ -f "$cfg" ]]; then
      find_compiler
      if grep -q '"references"' "$cfg" 2>/dev/null; then
        log "$TSC -b $cfg  (project references / composite build)"
        "$TSC" -b "$cfg"
      else
        log "$TSC --noEmit -p $cfg"
        "$TSC" --noEmit -p "$cfg"
      fi
    else
      log "no tsconfig ($cfg); skipping typecheck"
    fi
  fi
  # Optional preview compiler is an additional check, never the primary gate.
  if [[ "${TS_USE_TSGO:-0}" == "1" && -x node_modules/.bin/tsgo ]]; then
    cfg="${TS_TSCONFIG:-tsconfig.json}"
    if [[ -f "$cfg" ]]; then
      log "tsgo cross-check after authoritative typecheck"
      if grep -q '"references"' "$cfg" 2>/dev/null; then
        node_modules/.bin/tsgo -b "$cfg"
      else
        node_modules/.bin/tsgo --noEmit -p "$cfg"
      fi
    fi
  fi
else
  log "SKIP_TS_TYPECHECK=1"
fi

# --- 2. lint (only if the project defines it; eslint-on-everything is noisy) ---
if [[ "${SKIP_TS_LINT:-0}" != "1" ]] && has_script lint; then
  log "$pm run lint"; run_script lint
else
  log "no lint script (or skipped)"
fi

# --- 3. test ---
if [[ "${SKIP_TS_TEST:-0}" != "1" ]] && has_script test; then
  log "$pm run test"; run_script test
else
  log "no test script (or skipped)"
fi

log "ok"
