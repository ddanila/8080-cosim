#!/usr/bin/env bash
# Guard the ekta37 SkoolKit disassembly: the vendored skool must regenerate
# byte-identically from the vendored ctl, and must reassemble to the exact
# pinned roms/ekta37.bin. See disasm/README.md.
set -euo pipefail
cd "$(dirname "$0")/.."

EKTA37_SHA256=fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27
SKOOLKIT_VERSION=10.0

check_tmp=$(mktemp -d)
trap 'rm -rf "$check_tmp"' EXIT

if ! command -v sna2skool.py >/dev/null 2>&1; then
  python3 -m venv "$check_tmp/venv"
  "$check_tmp/venv/bin/pip" install --quiet "skoolkit==$SKOOLKIT_VERSION"
  export PATH="$check_tmp/venv/bin:$PATH"
fi

python3 - <<'EOF'
import hashlib
digest = hashlib.sha256(open("roms/ekta37.bin", "rb").read()).hexdigest()
expected = "fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27"
assert digest == expected, f"roms/ekta37.bin differs: {digest}"
EOF

sna2skool.py --hex --org 0 --start 0 --end 16384 \
  --ctl disasm/ekta37/ekta37.ctl roms/ekta37.bin 2>/dev/null \
  > "$check_tmp/regen.skool"
diff -u disasm/ekta37/ekta37.skool "$check_tmp/regen.skool" \
  || { echo "EKTA37-DISASM: vendored skool is stale vs ctl" >&2; exit 1; }

skool2bin.py disasm/ekta37/ekta37.skool "$check_tmp/roundtrip.bin" 2>/dev/null
python3 - "$check_tmp/roundtrip.bin" "$EKTA37_SHA256" <<'EOF'
import hashlib, sys
digest = hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()
assert digest == sys.argv[2], f"round-trip binary differs: {digest}"
EOF

echo "EKTA37-DISASM-CHECK: PASS"
