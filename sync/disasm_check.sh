#!/usr/bin/env bash
# Guard every vendored ROM disassembly: each skool must regenerate
# byte-identically from its ctl, and must reassemble to the exact pinned ROM.
# See disasm/README.md.
set -euo pipefail
cd "$(dirname "$0")/.."

SKOOLKIT_VERSION=10.0

# name:size:sha256 -- pins for every disassembled image
MANIFEST="
ekta24:16384:e1bd9894134ee4085c14bde854780539d3b1e03cfc032c81ec352729e9d69287
ekta31:16384:26f1f4161a547ea60312a250bde9df41c0b07a939c0b880628050eaec18ec4e4
ekta32:16384:1826563e23b5d8bc23c61694ceccb923d6a31778077934ad0338772070671122
ekta35:16384:e8fe5e657037b8f3203f57512cd01cc35f7eaa2a3f0dae8d0ae19378908bd518
ekta37:16384:fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27
ekta43:16384:39e3ca8978b369632d03c658300654445b898139009f188cb154e2f901238ba7
jmon22:16384:1b68f89ae4355391f434b3fae34e95cb4b150bf4bbcb967b5b177d48cd390589
jmon33:16384:ce9e9c63abbb1780566423a871081bd0bf048a2f3c79e370b465ea9869ff51b8
jbasic11:8192:ff86e17c7ce6de177e18bc0468d23cee7ed2ecd6e8adc56950138cdf6ee5ba60
"

check_tmp=$(mktemp -d)
trap 'rm -rf "$check_tmp"' EXIT

if ! command -v sna2skool.py >/dev/null 2>&1; then
  python3 -m venv "$check_tmp/venv"
  "$check_tmp/venv/bin/pip" install --quiet "skoolkit==$SKOOLKIT_VERSION"
  export PATH="$check_tmp/venv/bin:$PATH"
fi

for entry in $MANIFEST; do
  name=${entry%%:*}
  rest=${entry#*:}
  size=${rest%%:*}
  sha=${rest#*:}

  python3 - "roms/$name.bin" "$sha" <<'EOF'
import hashlib, sys
digest = hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()
assert digest == sys.argv[2], f"{sys.argv[1]} differs: {digest}"
EOF

  sna2skool.py --hex --org 0 --start 0 --end "$size" \
    --ctl "disasm/$name/$name.ctl" "roms/$name.bin" 2>/dev/null \
    > "$check_tmp/$name.skool"
  diff -u "disasm/$name/$name.skool" "$check_tmp/$name.skool" \
    || { echo "DISASM-CHECK: $name vendored skool is stale vs ctl" >&2; exit 1; }

  skool2bin.py "disasm/$name/$name.skool" "$check_tmp/$name-rt.bin" 2>/dev/null
  python3 - "$check_tmp/$name-rt.bin" "$sha" <<'EOF'
import hashlib, sys
digest = hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()
assert digest == sys.argv[2], f"round-trip binary differs: {digest}"
EOF
  echo "DISASM-CHECK: $name PASS"
done

echo "DISASM-CHECK: PASS (all images)"
