#!/usr/bin/env python3
"""Guard the ekta4401 remix image (spinoffs/jukuravi/EKTA37-REMIX-PLAN.md).

Static: the committed image rebuilds byte-identically from pinned ekta37,
differs from the source only in the intended places, and satisfies the
ROM's own eight chunk checksums.

Behavioral (cosim): the image boots and paints its banner; `H` walks the help
text, `V` executes the write-only framebuffer demo, and `J` starts the copied
loader -- proven from CPU bus activity rather than a guessed final screenshot.
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
HANDLER_RUNTIME = 0xF937
HELP_START = HANDLER_RUNTIME + 7
HELP_LENGTH = len(remix.HELP_TEXT)
HELP_END = HELP_START + HELP_LENGTH
DEMO_RUNTIME = 0xF9DF
DEMO_REGION_END = 0xFB18
J_RUNTIME = 0xFCBB
J_REGION_END = 0xFD11
GAP_USED_TO = 0x3D2F
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
    d15 = (REMIX / "ekta4401-d15.bin").read_bytes()
    d16 = (REMIX / "ekta4401-d16.bin").read_bytes()
    if len(d15) != 8192 or d15 != image[:0x2000]:
        fail("D15 programming image is not the exact low 8 KiB")
    if len(d16) != 8192 or d16 != image[0x2000:]:
        fail("D16 programming image is not the exact high 8 KiB")
    if d15 + d16 != image:
        fail("D15+D16 programming images do not reproduce ekta4401.bin")
    if hashlib.sha256(d15).hexdigest() != metadata["d15_sha256"]:
        fail("D15 programming-image identity differs")
    if hashlib.sha256(d16).hexdigest() != metadata["d16_sha256"]:
        fail("D16 programming-image identity differs")

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
    if metadata["commands"] != "FDSXGMCEKTBRWPAHJV":
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
    serial_handoff = bytes(
        (
            0xCD,
            remix.LOADER_RESTORE_SERIAL & 0xFF,
            remix.LOADER_RESTORE_SERIAL >> 8,
            0xC3,
            remix.LOADER_ENTRY & 0xFF,
            remix.LOADER_ENTRY >> 8,
        )
    )
    j_region = image[J_RUNTIME - 0xC000 : J_REGION_END - 0xC000]
    if j_region.count(serial_handoff) != 1:
        fail("J does not restore the exact T36 serial/PIT state before entry")
    if new_table.get("V") != DEMO_RUNTIME:
        fail("V does not dispatch to the visual demo")
    demo = metadata["visual_demo"]
    if demo["runtime"] != f"0x{DEMO_RUNTIME:04X}" or demo["logo"] != "JUKU 2026":
        fail("visual demo identity/layout differs")
    if demo["frames"] != 12 or demo["framebuffer_bytes_per_frame"] != 40 * 241:
        fail("visual demo frame contract differs")
    if demo["pattern"] != "symmetric-diamond-tunnel":
        fail("visual demo pattern identity differs")
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


def run_cosim(trace: Path, image: bytes, temp: Path, keys: str | None) -> dict[str, object]:
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
    counts = {
        "help": 0,
        "demo": 0,
        "demo_ram": 0,
        "service": 0,
        "usart": 0,
        "video_writes": 0,
        "video_value_mask": 0,
    }
    demo_active = False
    demo_frame_starts = 0
    demo_frame = bytearray(remix.FRAMEBUFFER_BYTES)
    with bus.open() as stream:
        for line in stream:
            parts = line.split()
            if len(parts) != 3:
                continue
            if parts[0] == "MR":
                address = int(parts[1], 16)
                if HELP_START <= address < HELP_END:
                    counts["help"] += 1
                elif DEMO_RUNTIME <= address < DEMO_REGION_END:
                    counts["demo"] += 1
                elif remix.DEMO_RAM_RUNTIME <= address < (
                    remix.DEMO_RAM_RUNTIME + 0x0200
                ):
                    counts["demo_ram"] += 1
                elif J_RUNTIME <= address < J_REGION_END:
                    counts["service"] += 1
            elif parts[0] == "MW":
                address = int(parts[1], 16)
                if remix.FRAMEBUFFER_BASE <= address < (
                    remix.FRAMEBUFFER_BASE + remix.FRAMEBUFFER_BYTES
                ):
                    offset = address - remix.FRAMEBUFFER_BASE
                    value = int(parts[2], 16)
                    if demo_active:
                        if offset == 0:
                            demo_frame_starts += 1
                            if demo_frame_starts == 2:
                                # The second frame's first write means the
                                # complete first frame, plaque and logo are
                                # available as a deterministic visual oracle.
                                counts["visual_frame"] = bytes(demo_frame)
                        demo_frame[offset] = value
                    counts["video_writes"] += 1
                    counts["video_value_mask"] |= 1 << value
            elif parts[0] == "IW":
                port = int(parts[1], 16)
                value = int(parts[2], 16)
                if port == remix.MODE_PORT and value & 0x03 == 0x03:
                    demo_active = True
                if port in (0x08, 0x09):
                    counts["usart"] += 1
    framebuffer = (temp / f"cp-{label}.ram").read_bytes()[0xD800:0xD800 + 40 * 241]
    counts["screen"] = sum(1 for byte in framebuffer if byte)
    state = {}
    for line in (temp / f"cp-{label}.state").read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            state[key] = value
    counts["accepted_video_writes"] = int(state["vram_writes"])
    counts["final_mode"] = int(state["mode"])
    return counts


def check_visual_frame(frame: object) -> None:
    """Reject the old address-hash texture as well as byte-level regressions."""
    if not isinstance(frame, bytes) or len(frame) != remix.FRAMEBUFFER_BYTES:
        fail("V did not expose a complete first animation frame")

    x_distance = tuple(range(19, -1, -1)) + tuple(range(20))
    expected = bytearray(
        0xFF if ((x_distance[x] + abs(y - 120) // 8) & 0x02) == 0 else 0x00
        for y in range(241)
        for x in range(40)
    )
    for y in range(remix.LOGO_ROW - 1, remix.LOGO_ROW + 9):
        start = y * 40 + remix.LOGO_COLUMN - 1
        expected[start : start + len(remix.LOGO_TEXT) + 2] = bytes(
            len(remix.LOGO_TEXT) + 2
        )
    logo = remix.logo_bytes()
    for row in range(8):
        start = (remix.LOGO_ROW + row) * 40 + remix.LOGO_COLUMN
        expected[start : start + len(remix.LOGO_TEXT)] = logo[
            row * len(remix.LOGO_TEXT) : (row + 1) * len(remix.LOGO_TEXT)
        ]
    if frame != bytes(expected):
        first = next(
            i for i, pair in enumerate(zip(frame, expected)) if pair[0] != pair[1]
        )
        fail(f"V first-frame visual oracle differs at framebuffer byte {first}")

    binary_ratio = sum(value in (0x00, 0xFF) for value in frame) / len(frame)
    mirror_ratio = sum(
        frame[y * 40 + x] == frame[y * 40 + 39 - x]
        for y in range(241)
        for x in range(20)
    ) / (241 * 20)
    neighbor_ratio = sum(
        frame[y * 40 + x] == frame[y * 40 + x + 1]
        for y in range(241)
        for x in range(39)
    ) / (241 * 39)
    white_ratio = frame.count(0xFF) / len(frame)
    if binary_ratio < 0.98 or mirror_ratio < 0.98 or neighbor_ratio < 0.40:
        fail(
            "V lacks tunnel structure "
            f"(binary={binary_ratio:.3f}, mirror={mirror_ratio:.3f}, "
            f"neighbor={neighbor_ratio:.3f})"
        )
    if not 0.30 < white_ratio < 0.70:
        fail(f"V tunnel has unbalanced black/white coverage ({white_ratio:.3f})")


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

        pressed_v = run_cosim(trace, image, temp, "V")
        demo_delta = pressed_v["demo"] - control["demo"]
        demo_ram_delta = pressed_v["demo_ram"] - control["demo_ram"]
        writes_delta = pressed_v["video_writes"] - control["video_writes"]
        accepted_delta = (
            pressed_v["accepted_video_writes"] - control["accepted_video_writes"]
        )
        if demo_delta < 150:
            fail(f"V did not copy its mapped-ROM body (read delta {demo_delta})")
        if demo_ram_delta < 1_000_000:
            fail(f"V copied body did not sustain execution (delta {demo_ram_delta})")
        if writes_delta < 120_000:
            fail(f"V demo did not paint full frames (write delta {writes_delta})")
        if accepted_delta < 120_000:
            fail(f"V framebuffer writes were not accepted (delta {accepted_delta})")
        if not pressed_v["video_value_mask"] & 1 or not (
            pressed_v["video_value_mask"] & (1 << 0xFF)
        ):
            fail("V demo did not generate both black and white tunnel bands")
        check_visual_frame(pressed_v.get("visual_frame"))
        if pressed_v["final_mode"] != 1:
            fail(f"V did not restore memory mode 1 (mode {pressed_v['final_mode']})")

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
            f"V ROM/RAM reads +{demo_delta}/+{demo_ram_delta}, "
            f"video writes +{writes_delta} accepted +{accepted_delta}, "
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
