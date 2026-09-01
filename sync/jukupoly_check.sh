#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$ROOT"
python3 tests/jukupoly_vgz_import_test.py
python3 tests/jukupoly_opl_trace_test.py
python3 tests/jukupoly_opl_voices_test.py
python3 tests/jukupoly_envelope_format_test.py
OPL_DIR="spinoffs/jukupoly/external/Nuked-OPL3"
OPL_COMMIT="765ec962e473aeb767e4cba74ffdc8f588ffbfe8"
if [[ ! -f "$OPL_DIR/opl3.c" || "$(git -C "$OPL_DIR" rev-parse HEAD)" != "$OPL_COMMIT" ]]; then
  echo "Nuked OPL3 submodule is missing or not at $OPL_COMMIT" >&2
  exit 1
fi
cc -std=c11 -O2 -Wall -Wextra -Werror -I"$OPL_DIR" \
  -o "$TMP/jukupoly_opl_oracle" \
  spinoffs/jukupoly/tools/jukupoly_opl_oracle.c "$OPL_DIR/opl3.c"
JUKUPOLY_OPL_ORACLE="$TMP/jukupoly_opl_oracle" \
  python3 tests/jukupoly_opl_oracle_test.py
JUKUPOLY_OPL_ORACLE="$TMP/jukupoly_opl_oracle" \
python3 tests/jukupoly_opl_envelope_test.py
python3 tests/jukupoly_opl_enhanced_test.py
python3 tests/jukupoly_opl_tremolo_test.py
python3 tests/jukupoly_opl_vibrato_test.py
python3 tests/jukupoly_opl_pitch_test.py
python3 spinoffs/jukupoly/tools/report_jukupoly_imp_m3.py --check
python3 spinoffs/jukupoly/tools/report_jukupoly_tremolo_target.py --check
python3 spinoffs/jukupoly/tools/report_jukupoly_tremolo_real.py --check
python3 spinoffs/jukupoly/tools/report_jukupoly_tremolo_real.py \
  --score spinoffs/jukupoly/firmware/jukupoly-opening-full-tremolo-m4.json \
  --output spinoffs/jukupoly/OPL-TREMOLO-FULL-M4.json --check
python3 spinoffs/jukupoly/tools/report_jukupoly_pitch_real.py --check
python3 spinoffs/jukupoly/firmware/build_jukupoly.py --check
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-suspense.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-suspense-generated.inc \
  --output spinoffs/jukupoly/firmware/suspense.com \
  --check
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-suspense-full.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-suspense-full-generated.inc \
  --output spinoffs/jukupoly/firmware/suspfull.com \
  --check
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-tdk-robots-60s.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-tdk-robots-60s-generated.inc \
  --output spinoffs/jukupoly/firmware/tdk60.com \
  --check
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-tdk-robots.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-tdk-robots-generated.inc \
  --output spinoffs/jukupoly/firmware/tdkrobot.com \
  --check
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-doomgate-vgz.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-doomgate-vgz-generated.inc \
  --output spinoffs/jukupoly/firmware/doomgate.com \
  --check
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-demons-vgz.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-demons-vgz-generated.inc \
  --output spinoffs/jukupoly/firmware/demons.com \
  --check
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-supaplex-main-vgz.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-supaplex-main-vgz-generated.inc \
  --output spinoffs/jukupoly/firmware/supaplex.com \
  --check
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-arkanoid-ending-vgz.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-arkanoid-ending-vgz-generated.inc \
  --output spinoffs/jukupoly/firmware/arkanoid.com \
  --check
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukupoly_test" \
  tests/jukupoly_test.c cosim/i8080.c
"$TMP/jukupoly_test" spinoffs/jukupoly/firmware/jukupoly.com
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukupoly_suspense_test" \
  tests/jukupoly_suspense_test.c cosim/i8080.c
"$TMP/jukupoly_suspense_test" \
  spinoffs/jukupoly/firmware/suspense.com
"$TMP/jukupoly_suspense_test" \
  spinoffs/jukupoly/firmware/suspfull.com 6400
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukupoly_mod_test" \
  tests/jukupoly_mod_test.c cosim/i8080.c
"$TMP/jukupoly_mod_test" \
  spinoffs/jukupoly/firmware/tdk60.com 3000
"$TMP/jukupoly_mod_test" \
  spinoffs/jukupoly/firmware/tdkrobot.com 25728
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -o "$TMP/jukupoly_vgz_test" \
  tests/jukupoly_vgz_test.c cosim/i8080.c
"$TMP/jukupoly_vgz_test" \
  spinoffs/jukupoly/firmware/doomgate.com 4826 96 98
"$TMP/jukupoly_vgz_test" \
  spinoffs/jukupoly/firmware/demons.com 7776 156 159
"$TMP/jukupoly_vgz_test" \
  spinoffs/jukupoly/firmware/supaplex.com 15240 305 308
"$TMP/jukupoly_vgz_test" \
  spinoffs/jukupoly/firmware/arkanoid.com 920 18 19 0
