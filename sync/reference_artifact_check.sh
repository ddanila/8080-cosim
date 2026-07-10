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

# The owner photographs are Git LFS objects rather than checksum-manifested
# reference directories.  A pointer stub is useful to Git but cannot support
# the visual/continuity evidence claimed by the generated PCB reports.
photo_count=0
for photo in ref/photos/juku-pcb-2/*.jpg; do
  [ -e "$photo" ] || continue
  photo_count=$((photo_count + 1))
  if head -n 1 "$photo" | grep -qx 'version https://git-lfs.github.com/spec/v1'; then
    echo "reference artifact check: Git LFS owner photo is not materialized: $photo" >&2
    echo "reference artifact check: run 'git lfs pull --include=ref/photos/juku-pcb-2/*.jpg'" >&2
    exit 2
  fi
  if ! file "$photo" | grep -q 'JPEG image data'; then
    echo "reference artifact check: owner photo is not a JPEG: $photo" >&2
    exit 2
  fi
done

if [ "$photo_count" -ne 22 ]; then
  echo "reference artifact check: expected 22 owner photos, found $photo_count" >&2
  exit 2
fi

echo "REFERENCE-ARTIFACT-CHECK: PASS"
