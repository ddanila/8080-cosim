#!/usr/bin/env python3
"""Guard the ektaravi remix image (spinoffs/jukuravi/EKTA37-REMIX-PLAN.md).

Static: the committed image rebuilds byte-identically from pinned ekta37,
differs from the source only in the intended places, and satisfies the
ROM's own eight chunk checksums.

Behavioral (cosim): the image boots and paints its banner; pressing `H`
reaches the relocated dispatch table, executes the new handler, and walks
the help text -- proven from the CPU bus trace, not from pixels.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMIX = ROOT / "spinoffs" / "jukuravi" / "remix"
sys.path.insert(0, str(REMIX))
import build_ektaravi as remix  # noqa: E402

SOURCE = ROOT / "roms" / "ekta37.bin"
CHUNKS_LOW = ((0x000B, 0x0800), (0x0800, 0x1000), (0x1000, 0x1800))
CHUNKS_HIGH = ((0x180B, 0x2000), (0x2000, 0x2800), (0x2800, 0x3000),
               (0x3000, 0x3800), (0x3800, 0x4000))
TABLE_RUNTIME = 0xF900
HANDLER_RUNTIME = 0xF931
HELP_END = 0xF9CB


def fail(message: str) -> None:
    print(f"EKTARAVI-TEST: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_static(image: bytes, metadata: dict[str, object]) -> None:
    committed = (REMIX / "ektaravi.bin").read_bytes()
    if committed != image:
        fail("committed ektaravi.bin differs from the rebuild")
    if len(image) != 16384:
        fail("image is not 16 KiB")

    source = SOURCE.read_bytes()
    changed = {i for i in range(16384) if source[i] != image[i]}
    allowed = set(range(0x00DF, 0x00DF + 27))          # banner line
    allowed |= {0x1924, 0x1925}                        # table pointer operand
    allowed |= set(range(0x3900, 0x39CB + 1))          # table + handler + text
    allowed |= {0x000A - n for n in range(3)}          # low chunk checksums
    allowed |= {0x180A - n for n in range(5)}          # upper chunk checksums
    stray = changed - allowed
    if stray:
        fail(f"image changes bytes outside the patch set: {sorted(stray)[:8]}")
    for label, region in (
        ("banner", range(0x00DF, 0x00DF + 27)),
        ("table pointer", range(0x1924, 0x1926)),
        ("relocated table", range(0x3900, 0x39CC)),
    ):
        if not changed & set(region):
            fail(f"expected {label} patch is missing from the image")

    for n, (lo, hi) in enumerate(CHUNKS_LOW):
        if image[0x000A - n] != sum(image[lo:hi]) & 0xFF:
            fail(f"low chunk {n} checksum is wrong")
    for n, (lo, hi) in enumerate(CHUNKS_HIGH):
        if image[0x180A - n] != sum(image[lo:hi]) & 0xFF:
            fail(f"upper chunk {n} checksum is wrong")

    if image[0x00DF:0x00DF + 27] != remix.BANNER_NEW:
        fail("banner line is not the remix identity")
    if b"EktaSoft" in image:
        fail("stock EktaSoft identity survives in the image")
    if metadata["commands"] != "FDSXGMCEKTBRWPAH":
        fail(f"command set differs: {metadata['commands']}")

    # every stock command must still dispatch to its stock handler
    stock_table, i = {}, 0x1977
    while source[i] != 0x00:
        stock_table[chr(source[i])] = source[i + 1] | (source[i + 2] << 8)
        i += 3
    new_table, i = {}, 0x3900
    while image[i] != 0x00:
        new_table[chr(image[i])] = image[i + 1] | (image[i + 2] << 8)
        i += 3
    for letter, target in stock_table.items():
        if new_table.get(letter) != target:
            fail(f"command {letter} no longer dispatches to {target:04X}h")
    if new_table.get("H") != HANDLER_RUNTIME:
        fail("H does not dispatch to the new handler")
    print("EKTARAVI-TEST: static checks passed", flush=True)


def check_boot(trace: Path, image: bytes) -> None:
    with tempfile.TemporaryDirectory(prefix="ektaravi-") as name:
        temp = Path(name)
        rom = temp / "ektaravi.bin"
        rom.write_bytes(image)
        bus = temp / "bus.trace"
        environment = os.environ.copy()
        environment.update(
            JUKU_KEYS="H",
            JUKU_KEY_HOLD_FRAMES="6",
            JUKU_KEY_GAP_FRAMES="8",
            JUKU_BUS_TRACE=str(bus),
            JUKU_BUS_TRACE_LIMIT="40000000",
            JUKU_CHECKPOINT_PREFIX=str(temp / "cp"),
            JUKU_CHECKPOINT_CYC="24000000",
        )
        completed = subprocess.run(
            [str(trace), str(rom), "25000000"],
            cwd=temp, env=environment, capture_output=True, text=True,
            timeout=600, check=False,
        )
        if completed.returncode != 0:
            fail(f"cosim exited {completed.returncode}: {completed.stderr[-400:]}")

        table = handler = text = 0
        with bus.open() as stream:
            for line in stream:
                parts = line.split()
                if len(parts) != 3 or parts[0] != "MR":
                    continue
                address = int(parts[1], 16)
                if TABLE_RUNTIME <= address < HANDLER_RUNTIME:
                    table += 1
                elif HANDLER_RUNTIME <= address < HANDLER_RUNTIME + 7:
                    handler += 1
                elif HANDLER_RUNTIME + 7 <= address <= HELP_END:
                    text += 1
        if table == 0:
            fail("relocated dispatch table was never read: parser still uses D977h")
        if handler == 0:
            fail("H handler never executed")
        if text < 100:
            fail(f"help text was not walked (only {text} reads)")

        framebuffer = (temp / "cp.ram").read_bytes()[0xD800:0xD800 + 40 * 241]
        if sum(1 for byte in framebuffer if byte) < 500:
            fail("boot produced no banner screen")
        print(
            f"EKTARAVI-TEST: boot ok — table {table} reads, handler {handler}, "
            f"help text {text}",
            flush=True,
        )


def main() -> int:
    image, metadata = remix.build()
    check_static(image, metadata)
    if len(sys.argv) == 2:
        check_boot(Path(sys.argv[1]).resolve(), image)
    elif len(sys.argv) != 1:
        fail("usage: test.py [/path/to/trace]")
    print(f"EKTARAVI-TEST: PASS {hashlib.sha256(image).hexdigest()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
