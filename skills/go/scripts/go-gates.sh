#!/usr/bin/env sh
# Resolve the bundled Python helper without requiring dirname or a toolchain.
set -eu
SCRIPT_DIR=${0%/*}
[ "$SCRIPT_DIR" != "$0" ] || SCRIPT_DIR=.
for GO_GATES_PY in python3 /usr/bin/python3 /usr/local/bin/python3 /opt/homebrew/bin/python3; do
  if command -v "$GO_GATES_PY" >/dev/null 2>&1; then
    exec "$GO_GATES_PY" "$SCRIPT_DIR/go_gates.py" "$@"
  fi
done
printf '%s\n' '[go-gates] error: python3 not found' >&2
exit 127
