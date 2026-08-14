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

log() { printf '[ts-gates] %s\n' "$*"; }

[[ -f package.json || -f tsconfig.json || -n "${TS_TSCONFIG:-}" ]] || {
  printf '[ts-gates] no package.json/tsconfig.json here — run from a TS project root\n' >&2
  exit 1
}

# --- detect package manager from the nearest lockfile ---
pm="npm"
if   [[ -f pnpm-lock.yaml ]]; then pm="pnpm"
elif [[ -f yarn.lock      ]]; then pm="yarn"
elif [[ -f bun.lockb || -f bun.lock ]]; then pm="bun"
elif [[ -f package-lock.json ]]; then pm="npm"
fi
command -v "$pm" >/dev/null 2>&1 || pm="npm"

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
  case "$pm" in
    yarn) yarn "$1" ;;
    *)    "$pm" run "$1" ;;
  esac
}

# Prefer the project's compiler, then an already-installed global compiler.
# Never fetch a toolchain implicitly; installation is a separate user decision.
if [[ -x node_modules/.bin/tsc ]]; then
  TSC="node_modules/.bin/tsc"
  log "pm=$pm  tsc=$($TSC --version 2>/dev/null || echo '?')"
elif command -v tsc >/dev/null 2>&1; then
  TSC="$(command -v tsc)"
  log "pm=$pm  tsc=$($TSC --version 2>/dev/null || echo '?') (global)"
else
  printf '[ts-gates] no TypeScript compiler found; install TypeScript in the project or provide tsc on PATH\n' >&2
  exit 127
fi

# Native Go port (TypeScript 7) — opt-in only; the project's own tsc stays the
# authoritative gate. tsgo is a drop-in CLI (same --noEmit/-p/-b flags, same codes).
if [[ "${TS_USE_TSGO:-0}" == "1" && -x node_modules/.bin/tsgo ]]; then
  TSC="node_modules/.bin/tsgo"
  log "TS_USE_TSGO=1 -> tsgo (preview; cross-check only)"
fi

# --- 1. typecheck (the gate that matters most) ---
if [[ "${SKIP_TS_TYPECHECK:-0}" != "1" ]]; then
  if has_script typecheck; then
    log "$pm run typecheck"; run_script typecheck
  elif has_script type-check; then
    log "$pm run type-check"; run_script type-check
  else
    cfg="${TS_TSCONFIG:-tsconfig.json}"
    if [[ -f "$cfg" ]]; then
      if grep -q '"references"' "$cfg" 2>/dev/null; then
        log "$TSC -b $cfg  (project references / composite build)"
        # shellcheck disable=SC2086
        $TSC -b "$cfg"
      else
        log "$TSC --noEmit -p $cfg"
        # shellcheck disable=SC2086
        $TSC --noEmit -p "$cfg"
      fi
    else
      log "no tsconfig ($cfg); skipping typecheck"
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
