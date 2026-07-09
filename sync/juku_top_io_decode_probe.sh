#!/usr/bin/env bash
# Fast diagnostic for the top-level I/O decoder instrumentation.
#
# This is not the EKDOS milestone gate. It proves the juku_top bench can see raw
# I/O cycles and that the delayed trace sampling observes the settled D7/D9
# chip-select decode before the long FDC probe reaches the post-banner window.
set -euo pipefail
cd "$(dirname "$0")/.."

REPORT=${JUKU_TOP_IO_DECODE_REPORT:-docs/juku-top-io-decode-probe.md}

JUKU_TOP_FDC_REPORT="$REPORT" \
JUKU_TOP_FDC_REPORT_TITLE="juku_top I/O decode probe" \
JUKU_TOP_FDC_TRACEIO=1 \
JUKU_TOP_FDC_STOPIO=20 \
JUKU_TOP_FDC_STOPFDC=0 \
JUKU_TOP_FDC_TIMEOUT=${JUKU_TOP_FDC_TIMEOUT:-60} \
sync/juku_top_fdc_probe.sh

python3 - "$REPORT" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
text = text.replace(
    "Status: **HDL JUKU_TOP FDC PATH NOT YET OBSERVED**",
    "Status: **HDL JUKU_TOP RAW I/O DECODE OBSERVED**",
    1,
)
text = text.replace(
    "This bounded diagnostic runs the LVS-checked `juku_top` with the vendored\n"
    "Juku disk image, frame interrupts, and the fixed ROMBIOS `TDD` keyboard\n"
    "sequence enabled. The default simulator is Icarus Verilog, matching the CI\n"
    "toolchain. Set `JUKU_TOP_FDC_SIM=verilator` for a faster local/deep reset\n"
    "run through the same testbench and stop hooks.",
    "This fast diagnostic runs the LVS-checked `juku_top` only far enough to\n"
    "sample the first settled raw I/O cycles and D7/D9 chip-select decode. It is\n"
    "not the EKDOS milestone gate; the full disk-backed prompt proof is tracked\n"
    "separately in `docs/juku-top-fdc-verilator-probe.md`.",
    1,
)
text = text.replace(
    "```sh\nsync/juku_top_fdc_probe.sh\n```",
    "```sh\nsync/juku_top_io_decode_probe.sh\n```",
    1,
)
path.write_text(text)
PY

if ! grep -q 'raw I/O trace observed | PASS' "$REPORT"; then
  echo "juku_top_io_decode_probe: raw I/O trace was not observed" >&2
  exit 1
fi
if ! grep -q 'ppi1=1' "$REPORT"; then
  echo "juku_top_io_decode_probe: first mirrored PPI1 access did not decode" >&2
  exit 1
fi
if ! grep -q 'ppi_ios=[1-9]' "$REPORT"; then
  echo "juku_top_io_decode_probe: no PPI0 decode was counted in the first I/O sample" >&2
  exit 1
fi

echo "JUKU-TOP-IO-DECODE-PROBE: PASS"
