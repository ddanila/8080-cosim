#!/usr/bin/env bash
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
archive="$project_root/third_party/open-watcom-v2/open-watcom-v2-c-linux-x64-20260820"
destination="$project_root/.tools/open-watcom-v2-20260820"
expected_sha="f83c158176f740ec656394a1ec531e2e6d8b78ebdfa4496460f9a0e457475e85"
expected_size=129055748

if [[ ! -f "$archive" ]]; then
    echo "Vendored Open Watcom archive is missing: $archive" >&2
    exit 1
fi
if head -n 1 "$archive" | grep -q '^version https://git-lfs.github.com/spec/v1$'; then
    echo "Open Watcom is an unmaterialized Git LFS pointer." >&2
    echo "Run: git lfs pull --include=third_party/open-watcom-v2/open-watcom-v2-c-linux-x64-20260820" >&2
    exit 1
fi
actual_size=$(stat -c %s "$archive")
actual_sha=$(sha256sum "$archive" | awk '{print $1}')
if [[ "$actual_size" != "$expected_size" || "$actual_sha" != "$expected_sha" ]]; then
    echo "Vendored Open Watcom identity mismatch" >&2
    echo "  expected $expected_size bytes $expected_sha" >&2
    echo "  actual   $actual_size bytes $actual_sha" >&2
    exit 1
fi

if [[ ! -x "$destination/binl64/wcl" ]]; then
    mkdir -p "$destination"
    unzip -q -o "$archive" -d "$destination"
    chmod +x "$destination/binl64"/* 2>/dev/null || true
fi

banner=$("$destination/binl64/wcl" 2>&1 || true)
if ! grep -q 'Open Watcom C/C++ x86 16-bit Compile and Link Utility' <<<"$banner" ||
        ! grep -q 'Aug 20 2026 02:25:10' <<<"$banner"; then
    echo "Extracted Open Watcom compiler identity differs" >&2
    printf '%s\n' "$banner" >&2
    exit 1
fi
echo "Open Watcom V2: PASS ($actual_sha, source cf43271464fdd57065d3d72de8ca917c55c6a887)"
