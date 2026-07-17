#!/usr/bin/env python3
"""Cosim machine checkpoint reference for the ROMBIOS TDD post-banner boundary."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "ekdos-checkpoint-reference.md"
ROM = ROOT / "roms" / "ekta37.bin"
DISK = ROOT / "media" / "disks" / "JUKU1.CPM"

EXPECTED = {
    "pc": "0484",
    "sp": "D44C",
    "a": "A1",
    "b": "D7",
    "c": "E7",
    "d": "00",
    "e": "A1",
    "h": "FD",
    "l": "2F",
    "iff": "0",
    "mode": "0",
    "portc": "80",
    "kbd_col": "0F",
    "pic_mask": "FF",
    "fdc_enabled": "1",
    "fdc_motor_on": "0",
    "fdc_sector": "01",
}
EXPECTED_WRITES = "30000"
EXPECTED_RAM_SHA = "eaa42964cdbc37bce58081edc085c5bcf94e95deed6454230e1aab8f1c3a38d4"
EXPECTED_VRAM_SHA = "0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68"


def sha256(path: Path) -> str:
    return subprocess.check_output(["sha256sum", str(path)], text=True).split()[0]


def parse_state(path: Path) -> dict[str, str]:
    state: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        state[key] = value
    return state


def run_checkpoint(tmp: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, str], str, str]:
    cc = os.environ.get("CC", "cc")
    writes = os.environ.get("EKDOS_CHECKPOINT_WRITES", EXPECTED_WRITES)
    max_cycles = os.environ.get("EKDOS_CHECKPOINT_MAX_CYCLES", "250000000")
    frame_cycles = os.environ.get("EKDOS_CHECKPOINT_FRAME_CYCLES", "200000")
    trace = tmp / "trace"
    prefix = tmp / "ekdos-checkpoint"
    old_vram = tmp / "old-vram.bin"
    cosim_vram = ROOT / "cosim" / "vram.bin"
    had_vram = cosim_vram.exists()
    if had_vram:
        shutil.copyfile(cosim_vram, old_vram)

    subprocess.run(
        [
            cc,
            "-O2",
            "-I",
            str(ROOT / "cosim"),
            "-o",
            str(trace),
            str(ROOT / "cosim" / "trace.c"),
            str(ROOT / "cosim" / "i8080.c"),
            str(ROOT / "cosim" / "juk_disk.c"),
            str(ROOT / "cosim" / "juku_fdc.c"),
        ],
        cwd=ROOT,
        check=True,
    )
    env = os.environ.copy()
    env["JUKU_KEYS"] = "TDD"
    env["JUKU_DISK"] = str(DISK)
    env["JUKU_CHECKPOINT_PREFIX"] = str(prefix)
    proc = subprocess.run(
        [str(trace), str(ROM), max_cycles, writes, frame_cycles],
        cwd=ROOT / "cosim",
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    state = parse_state(prefix.with_suffix(".state"))
    ram_sha = sha256(prefix.with_suffix(".ram"))
    vram_sha = sha256(cosim_vram) if cosim_vram.exists() else "missing"

    if had_vram:
        shutil.copyfile(old_vram, cosim_vram)
    elif cosim_vram.exists():
        cosim_vram.unlink()

    return proc, state, ram_sha, vram_sha


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ekdos-checkpoint.") as tmp_name:
        proc, state, ram_sha, vram_sha = run_checkpoint(Path(tmp_name))

    failures: list[str] = []
    if proc.returncode != 0:
        failures.append(f"trace exited {proc.returncode}")
    if state.get("vram_writes") != EXPECTED_WRITES:
        failures.append(f"vram_writes={state.get('vram_writes')} expected {EXPECTED_WRITES}")
    for key, expected in EXPECTED.items():
        if state.get(key) != expected:
            failures.append(f"{key}={state.get(key)} expected {expected}")
    if ram_sha != EXPECTED_RAM_SHA:
        failures.append(f"RAM SHA256 {ram_sha} expected {EXPECTED_RAM_SHA}")
    if vram_sha != EXPECTED_VRAM_SHA:
        failures.append(f"VRAM SHA256 {vram_sha} expected {EXPECTED_VRAM_SHA}")

    status = "PASS" if not failures else "REGRESSION"
    lines = [
        "# EKDOS checkpoint reference",
        "",
        f"Status: **{status}**",
        "",
        "This guard regenerates a full cosim machine checkpoint at 30,000",
        "framebuffer writes on the vendored `media/disks/JUKU1.CPM` `TDD` path.",
        "That is the last byte-identical `juku_top` comparison point before the",
        "first PIC/PPI setup window at 30,520 writes.",
        "",
        "The generated checkpoint files are not committed. They are an automation",
        "source for the checkpoint-resumed HDL diagnostics and a historical",
        "anchor for the uninterrupted prompt guard.",
        "",
        "## Command",
        "",
        "```sh",
        "sync/ekdos_checkpoint_reference.py",
        "```",
        "",
        "## Evidence",
        "",
        f"- Trace exit code: `{proc.returncode}`",
        f"- VRAM writes: `{state.get('vram_writes', 'missing')}`",
        f"- CPU cycles: `{state.get('cyc', 'missing')}`",
        f"- RAM SHA256: `{ram_sha}`",
        f"- VRAM SHA256: `{vram_sha}`",
        "",
        "| Field | Value |",
        "| --- | ---: |",
    ]
    for key in (
        "pc",
        "sp",
        "a",
        "b",
        "c",
        "d",
        "e",
        "h",
        "l",
        "sf",
        "zf",
        "hf",
        "pf",
        "cf",
        "iff",
        "mode",
        "portc",
        "kbd_col",
        "pic_icw1",
        "pic_icw2",
        "pic_mask",
        "fdc_enabled",
        "fdc_motor_on",
        "fdc_track",
        "fdc_physical_track",
        "fdc_sector",
    ):
        lines.append(f"| `{key}` | `{state.get(key, 'missing')}` |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- This proves the cosim checkpoint is stable; it does not by itself",
            "  resume the die-accurate HDL CPU.",
            "- This checkpoint is now a historical lower-level anchor: later",
            "  checkpoint-resumed diagnostics and the uninterrupted Verilator prompt",
            "  guard cover the first PIC/PPI/FDC window without replaying the full",
            "  framebuffer draw in every routine check.",
        ]
    )
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print("\n".join(lines))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
