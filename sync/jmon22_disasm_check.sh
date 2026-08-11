#!/usr/bin/env bash
# Guard the jmon22 SkoolKit disassembly: the vendored skool must regenerate
# byte-identically from the vendored ctl, and must reassemble to the exact
# pinned roms/jmon22.bin. See disasm/README.md.
set -euo pipefail
cd "$(dirname "$0")/.."

JMON22_SHA256=1b68f89ae4355391f434b3fae34e95cb4b150bf4bbcb967b5b177d48cd390589
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
digest = hashlib.sha256(open("roms/jmon22.bin", "rb").read()).hexdigest()
expected = "1b68f89ae4355391f434b3fae34e95cb4b150bf4bbcb967b5b177d48cd390589"
assert digest == expected, f"roms/jmon22.bin differs: {digest}"
EOF

sna2skool.py --hex --org 0 --start 0 --end 16384 \
  --ctl disasm/jmon22/jmon22.ctl roms/jmon22.bin 2>/dev/null \
  > "$check_tmp/regen.skool"
diff -u disasm/jmon22/jmon22.skool "$check_tmp/regen.skool" \
  || { echo "JMON22-DISASM: vendored skool is stale vs ctl" >&2; exit 1; }

skool2bin.py disasm/jmon22/jmon22.skool "$check_tmp/roundtrip.bin" 2>/dev/null
python3 - "$check_tmp/roundtrip.bin" "$JMON22_SHA256" <<'EOF'
import hashlib, sys
digest = hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()
assert digest == sys.argv[2], f"round-trip binary differs: {digest}"
EOF

echo "JMON22-DISASM-CHECK: PASS"
