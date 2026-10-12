#!/usr/bin/env bash
# Shim: the gates live in rust_gates.py (same knobs, same exit codes).
# Uses only bash builtins so it works with an empty PATH; python3 is
# resolved from PATH first, then the usual absolute locations.
dir="${BASH_SOURCE[0]%/*}"
[[ "$dir" == "${BASH_SOURCE[0]}" ]] && dir=.
for py in python3 /usr/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  if command -v "$py" >/dev/null 2>&1; then exec "$py" "$dir/rust_gates.py" "$@"; fi
done
printf '[rust-gates] error: python3 not found\n' >&2
exit 127
