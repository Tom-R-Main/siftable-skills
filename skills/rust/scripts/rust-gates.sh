#!/usr/bin/env bash
# Non-mutating narrow→broad gates for a Cargo-native project.
# Run from the package or workspace root:
#
#   /path/to/rust/scripts/rust-gates.sh
#
# Defaults:
#   detect build driver → fmt --check → clippy --all-targets -D warnings → cargo test
#
# The script REFUSES to run (exit 3) when the repo has its own build driver
# (x.py / x, an xtask crate, a justfile, or a Makefile with Rust targets):
# that driver's commands are the contract, and raw Cargo can produce
# confident wrong results (wrong toolchain, features, profile, or ignore list).
#
# The fmt gate FAILS (exit 4) instead of reporting diffs when rustfmt warns
# that rustfmt.toml uses nightly-only options on the current toolchain —
# stable rustfmt silently drops those options, so any diff it prints is
# measured against the wrong configuration.
#
# `cargo check` is skipped by default when Clippy runs, because Clippy
# repeats the same analysis; enable it as an explicit fast-fail.
#
# Selection knobs:
#   RUST_PACKAGE=name          check one package instead of --workspace
#   RUST_FEATURES=a,b          enable selected features
#   RUST_ALL_FEATURES=1        enable all features (only for composable features)
#   RUST_NO_DEFAULT_FEATURES=1 disable default features
#   RUST_UNLOCKED=1            omit --locked even when Cargo.lock exists
#
# Gate knobs:
#   RUST_GATES_FORCE_CARGO=1   run even though a build driver was detected
#   RUST_FMT_ALLOW_UNSTABLE_WARNINGS=1
#                              treat "unstable features" rustfmt warnings as
#                              non-fatal (you accept the diff may be wrong)
#   SKIP_RUST_FMT=1
#   SKIP_RUST_CLIPPY=1
#   SKIP_RUST_TEST=1
#   RUST_CHECK_ALWAYS=1        run cargo check even when Clippy also runs
#   SKIP_RUST_CHECK=1          never run cargo check (even if Clippy is skipped)
#   RUST_DENY_WARNINGS=0       do not add -D warnings to Clippy
#   RUST_TEST_ALL_TARGETS=1    add --all-targets to cargo test
#   RUST_DOC_TESTS=1           run a separate cargo test --doc gate
set -euo pipefail

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  printf '%s\n' \
    'Usage: rust-gates.sh' \
    '' \
    'Run non-mutating Rust gates from a Cargo package or workspace root:' \
    'rustfmt check, Clippy, and tests. Refuses (exit 3) when the repo has its' \
    'own build driver, and fails (exit 4) when rustfmt.toml uses nightly-only' \
    'options that the current toolchain silently ignores.' \
    '' \
    'Selection:' \
    '  RUST_PACKAGE=name          Check one package instead of --workspace.' \
    '  RUST_FEATURES=a,b          Enable selected features.' \
    '  RUST_ALL_FEATURES=1        Enable all features (composable feature sets only).' \
    '  RUST_NO_DEFAULT_FEATURES=1 Disable default features.' \
    '  RUST_UNLOCKED=1            Omit --locked even when Cargo.lock exists.' \
    '' \
    'Gates:' \
    '  RUST_GATES_FORCE_CARGO=1   Run even though a build driver was detected.' \
    '  RUST_FMT_ALLOW_UNSTABLE_WARNINGS=1' \
    '                             Accept rustfmt diffs measured with nightly-only' \
    '                             options dropped.' \
    '  SKIP_RUST_FMT=1            Skip the rustfmt check.' \
    '  SKIP_RUST_CLIPPY=1         Skip Clippy.' \
    '  SKIP_RUST_TEST=1           Skip cargo test.' \
    '  RUST_CHECK_ALWAYS=1        Run cargo check even when Clippy also runs.' \
    '  SKIP_RUST_CHECK=1          Never run cargo check.' \
    '  RUST_DENY_WARNINGS=0       Do not add -D warnings to Clippy.' \
    '  RUST_TEST_ALL_TARGETS=1    Add --all-targets to cargo test.' \
    '  RUST_DOC_TESTS=1           Run a separate cargo test --doc gate.'
  exit 0
fi

if (($# > 0)); then
  printf '[rust-gates] error: unsupported argument: %s\n' "$1" >&2
  exit 2
fi

log() { printf '[rust-gates] %s\n' "$*"; }
err() { printf '[rust-gates] error: %s\n' "$*" >&2; }

if [[ ! -f Cargo.toml ]]; then
  err "no Cargo.toml; run from a Cargo package/workspace root"
  exit 1
fi

# --- build-driver detection -------------------------------------------------
drivers=()
[[ -f x.py || -f x ]] && drivers+=("x.py bootstrap (use ./x fmt / ./x test)")
if [[ -d xtask ]] || grep -qsE '^[[:space:]]*"?xtask"?[[:space:]]*[,]]|^[[:space:]]*members[[:space:]]*=.*xtask' Cargo.toml 2>/dev/null; then
  drivers+=("xtask crate (use cargo xtask <task>)")
fi
for jf in justfile Justfile .justfile; do
  [[ -f "$jf" ]] && drivers+=("$jf (use just <recipe>)") && break
done
if [[ -f Makefile ]] && grep -qsE '^(fmt|lint|clippy|test|check)[a-z_-]*:' Makefile; then
  drivers+=("Makefile with Rust targets (use make <target>)")
fi

if (( ${#drivers[@]} > 0 )) && [[ "${RUST_GATES_FORCE_CARGO:-0}" != "1" ]]; then
  err "build driver detected; raw Cargo gates are not this repo's contract:"
  for d in "${drivers[@]}"; do printf '[rust-gates]   - %s\n' "$d" >&2; done
  err "run the driver's fmt/lint/test commands, or set RUST_GATES_FORCE_CARGO=1"
  exit 3
fi

if ! command -v cargo >/dev/null 2>&1; then
  err "cargo not found on PATH"
  exit 127
fi

log "$(cargo --version 2>/dev/null || printf 'cargo ?')"
if command -v rustc >/dev/null 2>&1; then
  log "$(rustc --version 2>/dev/null || printf 'rustc ?')"
fi
if [[ -f rust-toolchain || -f rust-toolchain.toml ]]; then
  log "toolchain file present at root (rustup honors the nearest one walking up from CWD)"
fi

if [[ "${RUST_ALL_FEATURES:-0}" == "1" && -n "${RUST_FEATURES:-}" ]]; then
  err "choose RUST_ALL_FEATURES or RUST_FEATURES, not both"
  exit 2
fi

scope_args=()
if [[ -n "${RUST_PACKAGE:-}" ]]; then
  scope_args=(-p "$RUST_PACKAGE")
else
  scope_args=(--workspace)
fi

common_args=("${scope_args[@]}")
if [[ -f Cargo.lock && "${RUST_UNLOCKED:-0}" != "1" ]]; then
  common_args+=(--locked)
fi
if [[ "${RUST_ALL_FEATURES:-0}" == "1" ]]; then
  common_args+=(--all-features)
elif [[ -n "${RUST_FEATURES:-}" ]]; then
  common_args+=(--features "$RUST_FEATURES")
fi
if [[ "${RUST_NO_DEFAULT_FEATURES:-0}" == "1" ]]; then
  common_args+=(--no-default-features)
fi

# --- fmt --------------------------------------------------------------------
if [[ "${SKIP_RUST_FMT:-0}" != "1" ]]; then
  log "cargo fmt --all -- --check"
  fmt_err="$(mktemp)"
  fmt_status=0
  # stderr goes to a file first (race-free, bash-3.2 safe), then is replayed.
  cargo fmt --all -- --check 2>"$fmt_err" || fmt_status=$?
  cat "$fmt_err" >&2
  if grep -qs 'unstable features are only available in nightly channel' "$fmt_err"; then
    if [[ "${RUST_FMT_ALLOW_UNSTABLE_WARNINGS:-0}" == "1" ]]; then
      log "warning: rustfmt.toml uses nightly-only options; diff above may be wrong (allowed by knob)"
    else
      rm -f "$fmt_err"
      err "rustfmt.toml uses nightly-only options that this toolchain silently ignores;"
      err "any diff printed above is against the WRONG configuration."
      err "run \`cargo +nightly fmt --all -- --check\` (or the repo's own fmt command),"
      err "or set RUST_FMT_ALLOW_UNSTABLE_WARNINGS=1 to accept that risk."
      exit 4
    fi
  fi
  rm -f "$fmt_err"
  if (( fmt_status != 0 )); then
    exit "$fmt_status"
  fi
else
  log "SKIP_RUST_FMT=1"
fi

# --- check (fast-fail only) ------------------------------------------------
run_check=0
if [[ "${SKIP_RUST_CHECK:-0}" != "1" ]]; then
  if [[ "${SKIP_RUST_CLIPPY:-0}" == "1" || "${RUST_CHECK_ALWAYS:-0}" == "1" ]]; then
    run_check=1
  fi
fi
if (( run_check )); then
  log "cargo check (selected scope/features, all targets)"
  cargo check "${common_args[@]}" --all-targets
else
  log "cargo check skipped (Clippy covers it; set RUST_CHECK_ALWAYS=1 to force)"
fi

# --- clippy -----------------------------------------------------------------
if [[ "${SKIP_RUST_CLIPPY:-0}" != "1" ]]; then
  if [[ "${RUST_DENY_WARNINGS:-1}" != "0" ]]; then
    log "cargo clippy (selected scope/features, all targets, deny warnings)"
    cargo clippy "${common_args[@]}" --all-targets -- -D warnings
  else
    log "cargo clippy (selected scope/features, all targets)"
    cargo clippy "${common_args[@]}" --all-targets
  fi
else
  log "SKIP_RUST_CLIPPY=1"
fi

# --- test -------------------------------------------------------------------
if [[ "${SKIP_RUST_TEST:-0}" != "1" ]]; then
  if [[ "${RUST_TEST_ALL_TARGETS:-0}" == "1" ]]; then
    log "cargo test (selected scope/features, all targets)"
    cargo test "${common_args[@]}" --all-targets
  else
    log "cargo test (selected scope/features)"
    cargo test "${common_args[@]}"
  fi

  if [[ "${RUST_DOC_TESTS:-0}" == "1" ]]; then
    log "cargo test --doc (selected scope/features)"
    cargo test "${common_args[@]}" --doc
  fi
else
  log "SKIP_RUST_TEST=1"
fi

log "ok"
