#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACE_C = ROOT / "cosim" / "trace.c"
I8080_C = ROOT / "cosim" / "i8080.c"
ROM = ROOT / "roms" / "ekta37.bin"
DEFAULT_DISK = ROOT / "media" / "disks" / "JUKU1.CPM"


PORT_RE = re.compile(r"^\s*0x([0-9A-Fa-f]{2})\s*:\s*([0-9]+)(?:\s+last=0x([0-9A-Fa-f]{2}))?")
STOP_RE = re.compile(r"stopped pc=0x([0-9A-Fa-f]{4}) cyc=([0-9]+) halted=([0-9]+) iff=([0-9]+) mode=([0-9]+) switches=([0-9]+)")
VRAM = ROOT / "cosim" / "vram.bin"
VRAM_WIDTH = 320
VRAM_STRIDE = 40
VRAM_LINES = 241
PROMPT_PATTERN = [
    "................",
    "....#......#....",
    "...#.#......#...",
    "..#...#......#..",
    "..#...#.......#.",
    "..#####......#..",
    "..#...#.....#...",
    "..#...#....#....",
    "................",
    "................",
]


def run_probe(max_cycles, frame_cycles, disk_path):
    cc = os.environ.get("CC", "cc")
    with tempfile.TemporaryDirectory(prefix="ekdos-fdc-probe.") as tmp:
        tmpdir = Path(tmp)
        trace = tmpdir / "trace"
        subprocess.run(
            [
                cc,
                "-O2",
                "-I",
                str(ROOT / "cosim"),
                "-o",
                str(trace),
                str(TRACE_C),
                str(I8080_C),
                str(ROOT / "cosim" / "juk_disk.c"),
                str(ROOT / "cosim" / "juku_fdc.c"),
            ],
            cwd=ROOT,
            check=True,
        )
        env = os.environ.copy()
        env["JUKU_KEYS"] = "TDD"
        if disk_path:
            env["JUKU_DISK"] = str(disk_path)
        else:
            env.pop("JUKU_DISK", None)
        proc = subprocess.run(
            [str(trace), str(ROM), str(max_cycles), "0", str(frame_cycles)],
            cwd=ROOT / "cosim",
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    return proc


def parse_ports(stdout):
    section = None
    ports = {"out": {}, "in": {}}
    for line in stdout.splitlines():
        if line.startswith("==== OUT ports"):
            section = "out"
            continue
        if line.startswith("==== IN ports"):
            section = "in"
            continue
        if line.startswith("==== hottest PCs"):
            section = None
            continue
        if section not in ports:
            continue
        match = PORT_RE.match(line)
        if not match:
            continue
        port = int(match.group(1), 16)
        count = int(match.group(2))
        last = int(match.group(3), 16) if match.group(3) is not None else None
        ports[section][port] = {"count": count, "last": last}
    return ports


def parse_stop(stderr):
    for line in reversed(stderr.splitlines()):
        match = STOP_RE.search(line)
        if match:
            pc, cyc, halted, iff, mode, switches = match.groups()
            return {
                "pc": int(pc, 16),
                "cycles": int(cyc),
                "halted": int(halted),
                "iff": int(iff),
                "mode": int(mode),
                "switches": int(switches),
            }
    return {}


def vram_pixel(vram, x, y):
    byte = vram[y * VRAM_STRIDE + (x // 8)]
    return (byte >> (7 - (x % 8))) & 1


def find_a_prompt(vram_path):
    try:
        vram = vram_path.read_bytes()
    except FileNotFoundError:
        return None
    if len(vram) != VRAM_STRIDE * VRAM_LINES:
        return None

    ph = len(PROMPT_PATTERN)
    pw = len(PROMPT_PATTERN[0])
    for y in range(VRAM_LINES - ph + 1):
        for x in range(3):
            ok = True
            for dy, row in enumerate(PROMPT_PATTERN):
                for dx, want in enumerate(row):
                    if vram_pixel(vram, x + dx, y + dy) != (want == "#"):
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                return {"x": x, "y": y}
    return None


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value is not None else "-" for value in values) + " |"


def repo_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def build_report(proc, max_cycles, frame_cycles, disk_path):
    ports = parse_ports(proc.stdout)
    stop = parse_stop(proc.stderr)
    failures = []
    disk_selected = bool(disk_path)
    disk_loaded = "loaded JUKU disk image" in proc.stderr
    prompt = find_a_prompt(VRAM) if disk_selected else None

    if proc.returncode != 0:
        failures.append(f"trace exited with status {proc.returncode}")
    if disk_selected and not disk_loaded:
        failures.append("selected EKDOS_PROBE_DISK was not loaded as a valid raw Juku disk image")
    if ports["out"].get(0x1C, {}).get("count", 0) == 0:
        failures.append("ROMBIOS did not write the WD1793 command/status register at port 0x1C")
    status_reads = ports["in"].get(0x1C, {}).get("count", 0)
    if disk_selected and status_reads == 0:
        failures.append("ROMBIOS did not read the WD1793 status register")
    if not disk_selected and status_reads < 1000:
        failures.append("ROMBIOS did not enter the expected WD1793 status polling loop")
    data_reads = ports["in"].get(0x1F, {}).get("count", 0)
    if disk_selected:
        if data_reads < 512:
            failures.append("ROMBIOS did not perform at least one 512-byte sector transfer")
        if prompt is None:
            failures.append("disk-backed run did not render the EKDOS `A>` prompt bitmap")
    elif data_reads != 512:
        failures.append("ROMBIOS did not perform the expected 512-byte first-sector data read")

    reached_fdc = not failures
    if failures:
        status = "REGRESSION"
    elif disk_selected:
        status = "EKDOS A> PROMPT REACHED"
    else:
        status = "READY FOR EXTERNAL EKDOS IMAGE"
    disk_label = repo_relative(disk_path) if disk_selected else "not selected"
    lines = [
        "# EKDOS/FDC boot-path probe",
        "",
        f"Status: **{status}**",
        "",
        "This probe exercises the factory boot sequence mined from Baltijets doc 003:",
        "`ROMBIOS 3.43` -> `*` -> `<T>, <D>, <D>` from `JUKU-1` toward the",
        "`A>` EKDOS prompt. By default it uses the vendored `media/disks/JUKU1.CPM`",
        "image, so this guard stays reproducible without network access. Set",
        "`EKDOS_PROBE_DISK=/path/to/image` to run the same path through another",
        "raw Juku disk image, or set `EKDOS_PROBE_DISK=none` for the legacy",
        "no-image boundary.",
        "",
        "## Command",
        "",
        "```sh",
        (
            f"EKDOS_PROBE_DISK={disk_label} JUKU_KEYS=TDD cosim/trace "
            f"roms/ekta37.bin {max_cycles} 0 {frame_cycles}"
            if disk_selected
            else f"JUKU_KEYS=TDD cosim/trace roms/ekta37.bin {max_cycles} 0 {frame_cycles}"
        ),
        "```",
        "",
        "## Summary",
        "",
        f"- Trace exit code: {proc.returncode}",
        f"- Disk image: {disk_label}",
        f"- Disk image loaded by cosim: {'yes' if disk_loaded else 'no'}",
        f"- Stop PC: {stop.get('pc', 0):04X}" if stop else "- Stop PC: not parsed",
        f"- Cycles: {stop.get('cycles', 0)}" if stop else "- Cycles: not parsed",
        f"- Mode switches: {stop.get('switches', 0)}" if stop else "- Mode switches: not parsed",
        f"- WD1793 status/command writes (`0x1C`): {ports['out'].get(0x1C, {}).get('count', 0)}",
        f"- WD1793 status reads (`0x1C`): {ports['in'].get(0x1C, {}).get('count', 0)}",
        f"- WD1793 data reads (`0x1F`): {ports['in'].get(0x1F, {}).get('count', 0)}",
        (
            f"- EKDOS `A>` prompt bitmap: found at x={prompt['x']}, y={prompt['y']}"
            if prompt
            else "- EKDOS `A>` prompt bitmap: not checked" if not disk_selected else "- EKDOS `A>` prompt bitmap: not found"
        ),
        f"- Probe failures: {len(failures)}",
        "",
        "## FDC I/O Ports",
        "",
        "| Direction | Port | Count | Last write |",
        "| --- | ---: | ---: | --- |",
    ]
    for direction, label in [("out", "OUT"), ("in", "IN")]:
        for port in [0x1C, 0x1D, 0x1E, 0x1F]:
            row = ports[direction].get(port, {"count": 0, "last": None})
            last = f"0x{row['last']:02X}" if row["last"] is not None else "-"
            lines.append(table_row([label, f"0x{port:02X}", row["count"], last]))

    lines.extend(
        [
            "",
            "## Disposition",
            "",
            "- The keyboard/frame-interrupt path is sufficient to drive ROMBIOS into the documented disk boot path.",
            "- The no-image run proves the BIOS/FDC boundary without depending on disk contents.",
            "- A disk-backed run is selected with `EKDOS_PROBE_DISK=/path/to/image`; invalid paths or unsupported raw image sizes fail this report explicitly.",
            "- The exact target remains the factory acceptance result `A>` after `<T>, <D>, <D>`.",
        ]
    )
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)
    lines.append("")
    return "\n".join(lines), reached_fdc


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "docs" / "ekdos-fdc-probe.md")
    max_cycles = int(os.environ.get("EKDOS_PROBE_MAX_CYCLES", "250000000"))
    frame_cycles = int(os.environ.get("EKDOS_PROBE_FRAME_CYCLES", "200000"))
    disk_env = os.environ.get("EKDOS_PROBE_DISK", "")
    if disk_env.lower() in {"none", "no", "0"}:
        disk_path = None
    elif disk_env:
        disk_path = Path(disk_env).expanduser()
    elif DEFAULT_DISK.exists():
        disk_path = DEFAULT_DISK
    else:
        disk_path = None
    proc = run_probe(max_cycles, frame_cycles, disk_path)
    report, ok = build_report(proc, max_cycles, frame_cycles, disk_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report)
    print(report)
    print(f"Wrote {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
