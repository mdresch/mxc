#!/usr/bin/env bash
# Rust validation for MXC. Run from anywhere.
#
# Default: fmt, clippy -D warnings, and the full workspace test suite.
# That suite is the regression check. A non-zero cargo test exit fails this script.
#
# --coverage also runs cargo-llvm-cov and fails when line coverage is under
# the floor (default 100). Install once with: cargo install cargo-llvm-cov
# Use --coverage for a new crate or a story module that can meet the floor.
# The repository CI jobs fail on cargo test, not on a workspace-wide percentage.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/../src"
COVERAGE=false
FAIL_UNDER=100

usage() {
    echo "Usage: scripts/validate-rust.sh [--coverage] [--fail-under N]"
    echo ""
    echo "Runs, from src/:"
    echo "  cargo fmt --all -- --check"
    echo "  cargo clippy --workspace --all-targets -- -D warnings"
    echo "  cargo test --workspace"
    echo ""
    echo "Options:"
    echo "  --coverage       Also run cargo llvm-cov --workspace --fail-under-lines N"
    echo "  --fail-under N   Line-coverage floor used with --coverage (default: 100)"
    echo "  -h, --help       Show this help"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --fail-under)
            FAIL_UNDER="${2:?--fail-under requires a number}"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

cd "$SRC_DIR"

echo "== cargo fmt =="
cargo fmt --all -- --check

echo "== cargo clippy =="
cargo clippy --workspace --all-targets -- -D warnings

echo "== cargo test =="
cargo test --workspace

if [[ "$COVERAGE" == true ]]; then
    if ! command -v cargo-llvm-cov >/dev/null 2>&1; then
        echo "cargo-llvm-cov is not installed. Install it with: cargo install cargo-llvm-cov" >&2
        exit 1
    fi
    echo "== cargo llvm-cov (fail under ${FAIL_UNDER}% lines) =="
    cargo llvm-cov --workspace --fail-under-lines "$FAIL_UNDER"
fi
