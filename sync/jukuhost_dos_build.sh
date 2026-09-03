#!/usr/bin/env bash
# Reproducibly build the 16-bit 8086 DOS Juku host with the vendored OW2.
set -euo pipefail

project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
output_dir=${1:-"$project_root/build/dos"}

"$project_root/tools/bootstrap-open-watcom.sh"
# shellcheck source=../tools/open-watcom-env.sh
source "$project_root/tools/open-watcom-env.sh"

mkdir -p "$output_dir"
rm -f "$output_dir"/*.o "$output_dir/JUKUHOST.EXE" \
    "$output_dir/JUKUHOST.MAP" "$output_dir/BUILD.LOG"

sources=(
    jukuhost_core
    jukuhost_bootstrap
    jukuhost_config
    jukuhost_evidence
    jukuhost_media
    jukuhost_service
    jukuhost_session
    jukuhost_sha256
    platform_file
    platform_dos
    jukuhost_runner
    jukuhost_main
)

compile_flags=(
    -bt=dos -ml -0 -zastd=c99 -ox -s -w4 -we -dJH_DOS
    -i="$project_root/host/include" -i="$project_root/host/src"
)

{
    for unit in "${sources[@]}"; do
        wcc "${compile_flags[@]}" \
            -fo="$output_dir/$unit.o" \
            "$project_root/host/src/$unit.c"
    done
    {
        echo "system dos"
        echo "name $output_dir/JUKUHOST.EXE"
        echo "option map=$output_dir/JUKUHOST.MAP"
        echo "option stack=24576"
        echo "option quiet"
        for object in "$output_dir"/*.o; do
            echo "file $object"
        done
    } >"$output_dir/LINK.RSP"
    wlink @"$output_dir/LINK.RSP"
} >"$output_dir/BUILD.LOG" 2>&1

test -s "$output_dir/JUKUHOST.EXE"
test -s "$output_dir/JUKUHOST.MAP"
sha256sum "$output_dir/JUKUHOST.EXE"
echo "JUKUHOST-DOS-BUILD: PASS ($(stat -c %s "$output_dir/JUKUHOST.EXE") bytes)"
