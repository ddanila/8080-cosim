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
check_dir ref/reconstructed-firmware
check_dir ref/wd1772-vg93
check_dir ref/datasheets

# The owner photographs are Git LFS objects rather than checksum-manifested
# reference directories.  A pointer stub is useful to Git but cannot support
# the visual/continuity evidence claimed by the generated PCB reports.
check_photo_dir() {
  local dir="$1"
  local expected="$2"
  local photo_count=0
  local photo
  for photo in "$dir"/*.jpg; do
    [ -e "$photo" ] || continue
    photo_count=$((photo_count + 1))
    if head -n 1 "$photo" | grep -qx 'version https://git-lfs.github.com/spec/v1'; then
      echo "reference artifact check: Git LFS owner photo is not materialized: $photo" >&2
      echo "reference artifact check: run 'git lfs pull --include=$dir/*.jpg'" >&2
      exit 2
    fi
    if ! file "$photo" | grep -q 'JPEG image data'; then
      echo "reference artifact check: owner photo is not a JPEG: $photo" >&2
      exit 2
    fi
  done
  if [ "$photo_count" -ne "$expected" ]; then
    echo "reference artifact check: expected $expected owner photos in $dir, found $photo_count" >&2
    exit 2
  fi
}

# 50 from the original survey session + the two 2026-07-22 X3-connector
# supplemental photos (SURVEY.md "2026-07-22 supplemental photos" section).
check_photo_dir ref/photos/juku-pcb-2 52
check_photo_dir ref/photos/dgsh5-109-009-sb 26

echo "REFERENCE-ARTIFACT-CHECK: PASS"
