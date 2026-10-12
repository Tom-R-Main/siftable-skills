#!/usr/bin/env bash
# glcheck.sh — apply the C verification ladder to a C OpenGL translation unit.
#
# Usage:  glcheck.sh file1.c [file2.c ...]
#   Compiles with strict warnings (warnings = correctness failures), then with
#   AddressSanitizer + UBSan. Auto-detects GLFW via pkg-config and links the right
#   platform GL framework/lib. Pass extra files (e.g. glad.c) as arguments.
#
# Env overrides:  CC=clang   STD=c11   GLFLAGS="..."   NO_SANITIZE=1
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  printf '%s\n' 'Usage: glcheck.sh file.c [more.c ...]' \
    'Build with strict warnings and ASan/UBSan. Does not run the binary.' \
    'Environment: CC, STD, GLFLAGS, NO_SANITIZE=1, GLCHECK_OUTPUT_DIR.' \
    'Set GLCHECK_OUTPUT_DIR to retain binaries for a separate runtime check.'
  exit 0
fi

CC="${CC:-cc}"
STD="${STD:-c11}"
WARN="-Werror -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Wstrict-prototypes -Wmissing-prototypes"

if [ "$#" -eq 0 ]; then
  echo "usage: $0 file.c [more.c ...]" >&2
  exit 2
fi

# --- locate GLFW / GL ---------------------------------------------------------
GLFLAGS="${GLFLAGS:-}"
if [ -z "$GLFLAGS" ]; then
  if command -v pkg-config >/dev/null && pkg-config --exists glfw3; then
    GLFLAGS="$(pkg-config --cflags --libs glfw3)"
  else
    echo "note: glfw3 not found via pkg-config; set GLFLAGS=... manually." >&2
  fi
fi

case "$(uname -s)" in
  Darwin) PLATFORM_LIBS="-framework OpenGL -framework Cocoa -framework IOKit" ;;
  Linux)  PLATFORM_LIBS="-lGL -ldl -lm -lpthread" ;;
  *)      PLATFORM_LIBS="" ;;
esac

rc=0
if [[ -n "${GLCHECK_OUTPUT_DIR:-}" ]]; then
  mkdir -p "$GLCHECK_OUTPUT_DIR"
  TMP="$(cd "$GLCHECK_OUTPUT_DIR" && pwd)"
else
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
fi

echo "== [1/2] strict warnings build ($CC -std=$STD) =="
# shellcheck disable=SC2086
if $CC -std="$STD" -O0 -g3 $WARN "$@" $GLFLAGS $PLATFORM_LIBS -o "$TMP/app_warn"; then
  echo "   ok: compiled clean under $WARN"
else
  echo "   FAIL: fix every warning/error above before proceeding." >&2
  rc=1
fi

if [ "${NO_SANITIZE:-0}" != "1" ]; then
  echo "== [2/2] sanitized build (ASan + UBSan) =="
  # shellcheck disable=SC2086
  if $CC -std="$STD" -O1 -g3 -fsanitize=address,undefined -fno-omit-frame-pointer \
        $WARN "$@" $GLFLAGS $PLATFORM_LIBS -o "$TMP/app_san"; then
    echo "   ok: built $TMP/app_san"
    if [[ -n "${GLCHECK_OUTPUT_DIR:-}" ]]; then
      echo "   run under an available display for runtime evidence:"
      echo "     ASAN_OPTIONS=detect_leaks=1 $TMP/app_san"
    else
      echo "   temporary binary will be removed; set GLCHECK_OUTPUT_DIR to retain it for runtime checks."
    fi
    echo "   (GL programs need a window/context; for CI use a headless EGL or Xvfb.)"
  else
    echo "   FAIL: sanitized build failed." >&2
    rc=1
  fi
fi

[ "$rc" -eq 0 ] && echo "glcheck: PASS" || echo "glcheck: PROBLEMS FOUND"
exit "$rc"
