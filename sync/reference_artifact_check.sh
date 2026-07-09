#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

check_dir() {
  local dir="$1"
  local first_path
  if [ ! -f "$dir/SHA256SUMS" ]; then
    echo "reference artifact check: missing $dir/SHA256SUMS" >&2
    exit 2
  fi
  first_path="$(awk 'NF >= 2 {print $2; exit}' "$dir/SHA256SUMS")"
  if [ "${first_path#"$dir"/}" != "$first_path" ]; then
    sha256sum -c "$dir/SHA256SUMS"
  else
    (cd "$dir" && sha256sum -c SHA256SUMS)
  fi
}

check_dir ref/baltijets-tech-docs
check_dir ref/ekdos-source
check_dir ref/extracted-software
check_dir ref/firmware
check_dir ref/reconstructed-proms
check_dir ref/wd1772-vg93

echo "REFERENCE-ARTIFACT-CHECK: PASS"
