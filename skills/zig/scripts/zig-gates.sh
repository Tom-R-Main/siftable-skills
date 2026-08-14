#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  printf '%s\n' \
    'Usage: zig-gates.sh' \
    '' \
    'Run conservative Zig formatting, test, and build gates from a project root.' \
    '' \
    'Environment:' \
    '  SKIP_ZIG_TEST=1    Skip the discoverable `zig build test` step.' \
    '  SKIP_ZIG_BUILD=1   Skip `zig build`.' \
    '  ZIG_TEST_ARGS      Extra whitespace-separated arguments for `zig build test`.' \
    '  ZIG_BUILD_ARGS     Extra whitespace-separated arguments for `zig build`.'
  exit 0
fi

if (($# > 0)); then
  printf '[zig-gates] error: unsupported argument: %s\n' "$1" >&2
  exit 2
fi

log() { printf '[zig-gates] %s\n' "$*"; }

if ! command -v zig >/dev/null 2>&1; then
  printf '[zig-gates] error: zig not found on PATH\n' >&2
  exit 127
fi

log "zig $(zig version)"

# Prefer git-tracked files when available; fall back to find for standalone folders.
zig_files=()
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  while IFS= read -r file; do
    zig_files+=("$file")
  done < <(git ls-files '*.zig')
else
  while IFS= read -r file; do
    zig_files+=("$file")
  done < <(find . -type f -name '*.zig' -not -path './zig-cache/*' -not -path './.zig-cache/*' -not -path './zig-out/*' | sort)
fi

if ((${#zig_files[@]} > 0)); then
  log "zig fmt --check (${#zig_files[@]} files)"
  zig fmt --check "${zig_files[@]}"
else
  log "no .zig files found; skipping fmt"
fi

if [[ -f build.zig ]]; then
  if [[ "${SKIP_ZIG_TEST:-0}" != "1" ]]; then
    if zig build --help 2>/dev/null | grep -Eq '(^|[[:space:]])test([[:space:]]|$)'; then
      log "zig build test ${ZIG_TEST_ARGS:-}"
      # shellcheck disable=SC2086
      zig build test ${ZIG_TEST_ARGS:-}
    else
      log "no discoverable zig build test step; skipping"
    fi
  fi

  if [[ "${SKIP_ZIG_BUILD:-0}" != "1" ]]; then
    log "zig build ${ZIG_BUILD_ARGS:-}"
    # shellcheck disable=SC2086
    zig build ${ZIG_BUILD_ARGS:-}
  fi
else
  log "no build.zig found; skipping build/test steps"
fi

log "ok"
