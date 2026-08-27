#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"
GALETTE_REV=af529870729b1da8794b002cd522f5bf2d53f230
RUST_VERSION=1.85.0
RUSTUP_VERSION=1.28.2
TARGET=x86_64-unknown-linux-gnu
TOOL_ROOT="$ROOT/.tools/vjuga-rust"
GALETTE_ROOT="$ROOT/.tools/galette"

if [ -x "$GALETTE_ROOT/bin/galette" ] &&
   [ "$("$GALETTE_ROOT/bin/galette" --version)" = "Galette 0.3.0" ]; then
  echo "Galette 0.3.0 already installed at $GALETTE_ROOT/bin/galette"
  exit 0
fi

command -v curl >/dev/null || { echo "curl is required" >&2; exit 2; }
command -v git >/dev/null || { echo "git is required" >&2; exit 2; }
vj_bootstrap_tmp="$(mktemp -d)"
trap 'rm -rf "$vj_bootstrap_tmp"' EXIT
RUSTUP_URL="https://static.rust-lang.org/rustup/archive/$RUSTUP_VERSION/$TARGET/rustup-init"
curl --proto '=https' --tlsv1.2 -fsSLo "$vj_bootstrap_tmp/rustup-init" "$RUSTUP_URL"
curl --proto '=https' --tlsv1.2 -fsSLo "$vj_bootstrap_tmp/rustup-init.sha256" "$RUSTUP_URL.sha256"
(cd "$vj_bootstrap_tmp" && sha256sum -c rustup-init.sha256)
chmod +x "$vj_bootstrap_tmp/rustup-init"
mkdir -p "$TOOL_ROOT/rustup" "$TOOL_ROOT/cargo"
RUSTUP_HOME="$TOOL_ROOT/rustup" CARGO_HOME="$TOOL_ROOT/cargo" \
  "$vj_bootstrap_tmp/rustup-init" -y --no-modify-path --profile minimal \
  --default-toolchain "$RUST_VERSION"
RUSTUP_HOME="$TOOL_ROOT/rustup" CARGO_HOME="$TOOL_ROOT/cargo" \
  "$TOOL_ROOT/cargo/bin/cargo" install --locked \
  --git https://github.com/simon-frankau/galette.git --rev "$GALETTE_REV" \
  --root "$GALETTE_ROOT"
test "$("$GALETTE_ROOT/bin/galette" --version)" = "Galette 0.3.0"
echo "Installed pinned Galette $GALETTE_REV with Rust $RUST_VERSION"
