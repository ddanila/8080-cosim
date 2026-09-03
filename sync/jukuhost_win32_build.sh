#!/usr/bin/env bash
# Reproducibly cross-build the self-contained 32-bit Windows host.
set -euo pipefail

project_root=$(cd "$(dirname "$0")/.." && pwd)
output_dir=${1:-"$project_root/build/win32"}
payload_source=${JUKUWIN_PAYLOAD_SOURCE:-"$project_root/../cpm-plus-juku/out"}

"$project_root/tools/bootstrap-open-watcom.sh"
# shellcheck source=../tools/open-watcom-env.sh
source "$project_root/tools/open-watcom-env.sh"

mkdir -p "$output_dir"
"$project_root/tools/generate-jukuwin-resources.py" \
    --directory "$output_dir" >"$output_dir/RESOURCE.LOG"
(cd "$output_dir" && wrc -q -r -bt=nt -i="$WATCOM/h/nt" \
    -fo=JUKUWIN.RES JUKUWIN.RC)
if [[ -d "$payload_source" ]]; then
    "$project_root/tools/generate-jukuwin-payloads.py" \
        --manifest "$project_root/host/windows/payload-manifest.json" \
        --source-dir "$payload_source" \
        --output "$output_dir/jukuwin_payloads.generated.c" \
        >"$output_dir/PAYLOAD.LOG"
    cmp "$output_dir/jukuwin_payloads.generated.c" \
        "$project_root/host/windows/jukuwin_payloads.c"
else
    printf '%s\n' "Payload source absent; compiling the checked generated catalog" \
        >"$output_dir/PAYLOAD.LOG"
fi

sources=(
    host/src/jukuhost_core.c
    host/src/jukuhost_bootstrap.c
    host/src/jukuhost_config.c
    host/src/jukuhost_evidence.c
    host/src/jukuhost_media.c
    host/src/jukuhost_service.c
    host/src/jukuhost_session.c
    host/src/jukuhost_sha256.c
    host/src/platform_file.c
    host/src/platform_win32.c
    host/src/jukuhost_runner.c
    host/windows/jukuwin_config.c
    host/windows/jukuwin_payloads.c
    host/windows/jukuwin_serial_select.c
    host/windows/jukuwin_serial_win32.c
    host/windows/jukuwin_app.c
)
objects=()
compile_flags=(
    -bt=nt -zastd=c99 -ox -s -w4 -we -dJH_WIN32
    -i="$project_root/host/include"
    -i="$project_root/host/src"
    -i="$project_root/host/windows"
    -i="$WATCOM/h/nt"
)

{
    for source in "${sources[@]}"; do
        unit=$(basename "${source%.c}")
        object="$output_dir/$unit.o"
        objects+=("$object")
        wcc386 "${compile_flags[@]}" -fo="$object" "$project_root/$source"
    done
    {
        echo "system nt_win"
        echo "name $output_dir/JUKUWIN.EXE"
        echo "option map=$output_dir/JUKUWIN.MAP"
        echo "option quiet"
        for object in "${objects[@]}"; do
            echo "file $object"
        done
        echo "library comdlg32"
    } >"$output_dir/LINK.RSP"
    wlink @"$output_dir/LINK.RSP"
    (cd "$output_dir" && wrc -q -bt=nt JUKUWIN.RES JUKUWIN.EXE)
} >"$output_dir/BUILD.LOG" 2>&1

test -s "$output_dir/JUKUWIN.EXE"
test -s "$output_dir/JUKUWIN.MAP"
"$project_root/tools/normalize-pe.py" "$output_dir/JUKUWIN.EXE" \
    >>"$output_dir/BUILD.LOG"
sha256sum "$output_dir/JUKUWIN.EXE"
echo "JUKUWIN-WIN32-BUILD: PASS ($(stat -c %s "$output_dir/JUKUWIN.EXE") bytes)"
