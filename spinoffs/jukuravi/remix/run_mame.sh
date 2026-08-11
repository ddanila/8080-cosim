#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/../../.." && pwd)
custom_rom="$script_dir/ekta4401.bin"
basic_rom="$repo_root/roms/jbasic11.bin"

mame_bin=$(command -v mame || true)
if [[ -z "$mame_bin" && -x /usr/games/mame ]]; then
    mame_bin=/usr/games/mame
fi
if [[ -z "$mame_bin" ]]; then
    echo "MAME was not found (install it with: sudo apt install mame)" >&2
    exit 1
fi

for rom in "$custom_rom" "$basic_rom"; do
    if [[ ! -f "$rom" ]]; then
        echo "Required ROM is missing: $rom" >&2
        exit 1
    fi
done

mame_rompath=$(mktemp -d "${TMPDIR:-/tmp}/ekta4401-mame.XXXXXX")
trap 'rm -rf -- "$mame_rompath"' EXIT INT TERM
mkdir "$mame_rompath/juku"
cp "$custom_rom" "$mame_rompath/juku/ekta37.bin"
cp "$basic_rom" "$mame_rompath/juku/jbasic11.bin"

echo "Starting ekta4401 in MAME; enter V at the monitor prompt for the demo."
echo "The expected custom-ROM checksum warning is safe to continue past."
"$mame_bin" juku -bios 3.43m_37 -rompath "$mame_rompath" -window "$@"
