#!/usr/bin/env python3
"""Guard the ekta4401 remix image (spinoffs/jukuravi/EKTA37-REMIX-PLAN.md).

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
import build_ekta4401 as remix  # noqa: E402

SOURCE = ROOT / "roms" / "ekta37.bin"
CHUNKS_LOW = ((0x000B, 0x0800), (0x0800, 0x1000), (0x1000, 0x1800))
CHUNKS_HIGH = ((0x180B, 0x2000), (0x2000, 0x2800), (0x2800, 0x3000),
               (0x3000, 0x3800), (0x3800, 0x4000))
TABLE_RUNTIME = 0xF900
HANDLER_RUNTIME = 0xF934
HELP_START = 0xF934 + 7
HELP_LENGTH = len(remix.HELP_TEXT)
HELP_END = HELP_START + HELP_LENGTH
J_RUNTIME = 0xFB7A
J_REGION_END = 0xFBCD
GAP_USED_TO = 0x3BEB
DISK_REGION = remix.DISK_REGION
DISK_VECTORS = remix.DISK_VECTORS


def fail(message: str) -> None:
    print(f"EKTA4401-TEST: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_static(image: bytes, metadata: dict[str, object]) -> None:
    t36 = remix.t36_image()
    committed = (REMIX / "ekta4401.bin").read_bytes()
    if committed != image:
        fail("committed ekta4401.bin differs from the rebuild")
    if len(image) != 16384:
        fail("image is not 16 KiB")

    source = SOURCE.read_bytes()
    changed = {i for i in range(16384) if source[i] != image[i]}
    allowed = set(range(0x00DF, 0x00DF + 27))          # banner line
    allowed |= {0x1924, 0x1925}                        # table pointer operand
    allowed |= set(range(0x3900, GAP_USED_TO))         # table, H, loader segs, J
    allowed |= set(range(*DISK_REGION))                # stripped floppy + segs
    allowed |= {v + n for v in DISK_VECTORS for n in range(3)}  # no-disk stubs
    allowed |= {0x000A - n for n in range(3)}          # low chunk checksums
    allowed |= {0x180A - n for n in range(5)}          # upper chunk checksums
    stray = changed - allowed
    if stray:
        fail(f"image changes bytes outside the patch set: {sorted(stray)[:8]}")
    for label, region in (
        ("banner", range(0x00DF, 0x00DF + 27)),
        ("table pointer", range(0x1924, 0x1926)),
        ("relocated table", range(0x3900, 0x3934)),
        ("loader segments", range(*DISK_REGION)),
        ("no-disk vectors", range(0x3F50, 0x3F5C)),
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
    if b"'EktaSoft '88" in image:
        fail("stock factory identity line survives in the image")
    if metadata["commands"] != "FDSXGMCEKTBRWPAHJ":
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
    if new_table.get("J") != J_RUNTIME:
        fail("J does not dispatch to the service handler")
    if len(metadata["loader_segments"]) != 5:
        fail("loader segment set is incomplete")
    for segment in metadata["loader_segments"]:
        rom_at = int(str(segment["rom"]), 16)
        length = int(segment["bytes"])
        if image[rom_at:rom_at + length] != t36[int(str(segment["dst"]), 16):
                                                int(str(segment["dst"]), 16) + length]:
            fail(f"stored loader segment {segment['name']} is not verbatim T36")
    for vector in DISK_VECTORS:
        if image[vector] != 0xC3:
            fail("a reclaimed floppy vector is not a jump")
    print("EKTA4401-TEST: static checks passed", flush=True)


def run_cosim(trace: Path, image: bytes, temp: Path, keys: str | None) -> dict[str, int]:
    """Boot the image once and count bus activity that identifies our code.

    The console renders through the same D800h+ address window the relocated
    code occupies, so absolute read counts there are dominated by framebuffer
    traffic. Every count below is therefore compared against a keyless
    control run; only the difference is evidence. The frame interrupt (argv[4])
    must be on or the keyboard is never scanned and no command dispatches.
    """
    label = keys or "none"
    rom = temp / f"rom-{label}.bin"
    rom.write_bytes(image)
    bus = temp / f"bus-{label}.trace"
    environment = os.environ.copy()
    environment.update(
        JUKU_BUS_TRACE=str(bus),
        JUKU_BUS_TRACE_LIMIT="60000000",
        JUKU_CHECKPOINT_PREFIX=str(temp / f"cp-{label}"),
        JUKU_CHECKPOINT_CYC="55000000",
    )
    if keys:
        environment.update(
            JUKU_KEYS=keys, JUKU_KEY_HOLD_FRAMES="6", JUKU_KEY_GAP_FRAMES="8"
        )
    completed = subprocess.run(
        [str(trace), str(rom), "60000000", "0", "200000"],
        cwd=temp, env=environment, capture_output=True, text=True,
        timeout=900, check=False,
    )
    if completed.returncode != 0:
        fail(f"cosim exited {completed.returncode}: {completed.stderr[-400:]}")
    counts = {"help": 0, "service": 0, "usart": 0}
    with bus.open() as stream:
        for line in stream:
            parts = line.split()
            if len(parts) != 3:
                continue
            if parts[0] == "MR":
                address = int(parts[1], 16)
                if HELP_START <= address < HELP_END:
                    counts["help"] += 1
                elif J_RUNTIME <= address < J_REGION_END:
                    counts["service"] += 1
            elif parts[0] == "IW" and int(parts[1], 16) in (0x08, 0x09):
                counts["usart"] += 1
    framebuffer = (temp / f"cp-{label}.ram").read_bytes()[0xD800:0xD800 + 40 * 241]
    counts["screen"] = sum(1 for byte in framebuffer if byte)
    return counts


def check_boot(trace: Path, image: bytes) -> None:
    with tempfile.TemporaryDirectory(prefix="ekta4401-") as name:
        temp = Path(name)
        control = run_cosim(trace, image, temp, None)
        if control["screen"] < 500:
            fail("boot produced no banner screen")
        if control["usart"] != 0:
            fail("control boot unexpectedly drives the USART")

        pressed_h = run_cosim(trace, image, temp, "H")
        help_delta = pressed_h["help"] - control["help"]
        if help_delta < HELP_LENGTH:
            fail(
                f"H did not walk the help text (delta {help_delta}, "
                f"expected at least {HELP_LENGTH})"
            )

        pressed_j = run_cosim(trace, image, temp, "J")
        service_delta = pressed_j["service"] - control["service"]
        if service_delta < 1000:
            fail(f"J service handler did not run (delta {service_delta})")
        if pressed_j["usart"] < 1000:
            fail(
                "J did not bring up the Jukuravi loader: no USART traffic "
                f"({pressed_j['usart']} events)"
            )
        print(
            f"EKTA4401-TEST: boot ok — H help delta +{help_delta}, "
            f"J service delta +{service_delta}, loader USART "
            f"{pressed_j['usart']} events",
            flush=True,
        )


def main() -> int:
    image, metadata = remix.build()
    check_static(image, metadata)
    if len(sys.argv) == 2:
        check_boot(Path(sys.argv[1]).resolve(), image)
    elif len(sys.argv) != 1:
        fail("usage: test.py [/path/to/trace]")
    print(f"EKTA4401-TEST: PASS {hashlib.sha256(image).hexdigest()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
