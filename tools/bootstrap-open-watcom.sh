#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source "$project_root/tools/open-watcom-env.sh"
cache="$project_root/.tools/downloads"
archive="$cache/open-watcom-20260801"
url="https://github.com/open-watcom/open-watcom-v2/releases/download/2026-08-01-Build/open-watcom-2_0-c-linux-x64"
expected_sha=e1bc4e88fa47191118f29e53731e7f4542803c7f4c503e15d72f1f571ac0832f
mkdir -p "$cache"
exec 9>"$cache/open-watcom-20260801.lock"
flock 9
scratch=$(mktemp -d "$project_root/.tools/.watcom.XXXXXXXX")
trap 'rm -r -- "$scratch"' EXIT
verify() {
    echo "$expected_sha  $1" | sha256sum --check --status
}
if [[ ! -f "$archive" ]]; then
    curl --fail --location --silent --show-error --retry 3 "$url" -o "$scratch/download"
    verify "$scratch/download" || { echo "Upstream compiler checksum mismatch" >&2; exit 1; }
    mv "$scratch/download" "$archive"
elif ! verify "$archive"; then
    echo "Invalid cached compiler archive: $archive" >&2
    exit 1
fi
destination=$WATCOM
if [[ ! -d "$destination" ]]; then
    unzip -q "$archive" -d "$scratch/compiler"
    chmod +x "$scratch/compiler/binl64/"*
    mv "$scratch/compiler" "$destination"
fi

banner=$("$destination/binl64/wcl" 2>&1 || true)
if ! grep -q 'Open Watcom C/C++ x86 16-bit Compile and Link Utility' <<<"$banner" ||
        ! grep -q 'Aug  1 2026 04:25:00' <<<"$banner"; then
    echo "Extracted Open Watcom compiler identity differs" >&2
    printf '%s\n' "$banner" >&2
    exit 1
fi
echo "Open Watcom V2: PASS (2026-08-01-Build, $expected_sha)"
