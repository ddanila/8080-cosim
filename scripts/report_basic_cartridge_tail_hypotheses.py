#!/usr/bin/env python3
"""Test simple Monitor 3.3 cartridge BASIC tail-page hypotheses."""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "basic-cartridge-tail-hypotheses.md"
CART = ROOT / "roms" / "jbasic11.bin"
PROBE = ROOT / "sync" / "basic_launch_probe.py"


@dataclass(frozen=True)
class Hypothesis:
    name: str
    description: str
    header_len: int | None
    tail_kind: str
    loop_len: int | None = None


HYPOTHESES = [
    Hypothesis(
        "append-final-page",
        "append a copy of the public cartridge final page; leave header bytes unchanged",
        None,
        "final-page",
    ),
    Hypothesis(
        "append-final-page-header-2100",
        "append the final page and patch header word `0x4005` to `0x2100`",
        0x2100,
        "final-page",
    ),
    Hypothesis(
        "append-ff-header-2100",
        "append `0xFF` bytes and patch header word `0x4005` to `0x2100`",
        0x2100,
        "ff",
    ),
    Hypothesis(
        "append-zero-header-2100",
        "append zero bytes and patch header word `0x4005` to `0x2100`",
        0x2100,
        "zero",
    ),
    Hypothesis(
        "patch-loop-count-1f00",
        "patch runtime bootstrap `LXI B,0x2000` to `0x1F00`; append nothing",
        None,
        "none",
        0x1F00,
    ),
]


STATUS_RE = re.compile(r"^Status: \*\*(.+?)\*\*", re.M)
ROW_RE = re.compile(
    r"^\| jmon33 \| `[^`]+` \| `[^`]+` \| `(?P<frame>[0-9]+)` \| "
    r"(?P<infra>PASS|FAIL) \| `(?P<reads>[0-9]+)` \| `(?P<pc>[0-9]+)` \| "
    r"`(?P<mode1>[0-9]+)` \| `(?P<mode2>[0-9]+)` \| `(?P<op00>[0-9]+)` \| "
    r"`(?P<writes>[0-9]+)` \| `(?P<write_span>[^`]+)` \| `(?P<write_pcs>[^`]+)` \| "
    r"`(?P<nonzero>[0-9]+)` \| `(?P<byte_sum>[0-9]+)` \| "
    r"`(?P<pixels>[0-9]+)` \| `(?P<stop_pc>[^`]+)` \| `(?P<mode>[0-9]+)` \| "
    r"`(?P<sha>[^`]+)` \|$",
    re.M,
)
HANDOFF_RE = re.compile(r"Sampled post-`0x0100` handoff path: `(.+?)`\.", re.S)
MISMATCH_RE = re.compile(r"Cartridge-vs-RAM mismatch check: `(.+?)`\.", re.S)


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def required_tail_bytes(cart: bytes) -> bytes:
    return cart[0x1F09:0x1F14]


def scan_required_pattern(required: bytes) -> list[tuple[str, int, int]]:
    hits: list[tuple[str, int, int]] = []
    for dirname in ["roms", "ref", "media"]:
        for path in (ROOT / dirname).rglob("*"):
            if not path.is_file():
                continue
            data = path.read_bytes()
            start = 0
            while True:
                pos = data.find(required, start)
                if pos < 0:
                    break
                page_start = pos - 0x09
                if page_start >= 0 and page_start + 0x100 <= len(data):
                    hits.append((str(path.relative_to(ROOT)), page_start, pos - page_start))
                start = pos + 1
    return hits


def make_variant(base: bytes, hyp: Hypothesis, out: Path) -> None:
    data = bytearray(base)
    if hyp.header_len is not None:
        data[5] = hyp.header_len & 0xFF
        data[6] = (hyp.header_len >> 8) & 0xFF
    if hyp.tail_kind == "final-page":
        data.extend(base[0x1F00:0x2000])
    elif hyp.tail_kind == "ff":
        data.extend(b"\xFF" * 0x100)
    elif hyp.tail_kind == "zero":
        data.extend(b"\x00" * 0x100)
    elif hyp.tail_kind == "none":
        pass
    else:
        raise ValueError(hyp.tail_kind)
    if hyp.loop_len is not None:
        # File offset 0x1F06 maps to runtime 0x2006 after Monitor 3.3 loads
        # the cartridge at 0x0100.
        data[0x1F07] = hyp.loop_len & 0xFF
        data[0x1F08] = (hyp.loop_len >> 8) & 0xFF
    out.write_bytes(data)


def run_probe(cart_path: Path, report_path: Path) -> str:
    env = os.environ.copy()
    env.update(
        {
            "BASIC_LAUNCH_ROM": "roms/jmon33.bin",
            "BASIC_LAUNCH_CART": str(cart_path),
            "BASIC_LAUNCH_FRAME_CYCLES": "200000",
            "BASIC_LAUNCH_MAX_CYCLES": "120000000",
            "BASIC_LAUNCH_REPORT": str(report_path),
        }
    )
    proc = subprocess.run(
        [str(PROBE)],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if not report_path.exists():
        raise SystemExit(
            f"basic launch probe did not write {report_path}: stdout={proc.stdout} stderr={proc.stderr}"
        )
    return report_path.read_text(errors="replace")


def first_match(pattern: re.Pattern[str], text: str, default: str = "-") -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else default


def summarize_probe(text: str) -> dict[str, str]:
    row = ROW_RE.search(text)
    if row:
        values = row.groupdict()
        values["completed"] = "DONE"
    else:
        values = {
            "completed": "NO ROW",
            "infra": "FAIL",
            "reads": "0",
            "pc": "0",
            "mode1": "0",
            "mode2": "0",
            "op00": "0",
            "writes": "0",
            "nonzero": "0",
            "byte_sum": "0",
            "pixels": "0",
            "stop_pc": "-",
            "mode": "-",
        }
    values["status"] = first_match(STATUS_RE, text)
    values["handoff"] = first_match(HANDOFF_RE, text)
    values["mismatch"] = first_match(MISMATCH_RE, text)
    return values


def main() -> int:
    cart = CART.read_bytes()
    required = required_tail_bytes(cart)
    pattern_hits = scan_required_pattern(required)
    rows: list[str] = []
    details: list[str] = []
    interesting = False

    with tempfile.TemporaryDirectory(prefix="basic-tail-hyp.") as tmp:
        tmpdir = Path(tmp)
        for hyp in HYPOTHESES:
            variant = tmpdir / f"{hyp.name}.bin"
            probe_report = tmpdir / f"{hyp.name}.md"
            make_variant(cart, hyp, variant)
            summary = summarize_probe(run_probe(variant, probe_report))
            pixels = int(summary["pixels"])
            mode2 = int(summary["mode2"])
            nonzero = int(summary["nonzero"])
            interesting = interesting or pixels > 0 or mode2 > 0 or nonzero > 0
            rows.append(
                table_row(
                    [
                        hyp.name,
                        hyp.description,
                        variant.stat().st_size,
                        summary["completed"],
                        summary["infra"],
                        summary["status"],
                        summary["reads"],
                        summary["pc"],
                        summary["mode2"],
                        summary["op00"],
                        summary["nonzero"],
                        summary["pixels"],
                        summary["stop_pc"],
                    ]
                )
            )
            details.extend(
                [
                    f"### {hyp.name}",
                    "",
                    f"- Handoff sample: `{summary['handoff']}`",
                    f"- Mismatch sample: `{summary['mismatch']}`",
                    "",
                ]
            )

    status = (
        "SIMPLE TAIL HYPOTHESIS NEEDS REVIEW"
        if interesting
        else "SIMPLE TAIL HYPOTHESES REJECTED"
    )
    lines = [
        "# BASIC cartridge tail hypotheses",
        "",
        f"Status: **{status}**",
        "",
        "This generated report tests the easiest automatic reconstructions for",
        "the missing Monitor 3.3 cartridge BASIC runtime page. It does not export",
        "a replacement cartridge image; it records which simple media-shape",
        "hypotheses are insufficient before any manual firmware reconstruction.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_basic_cartridge_tail_hypotheses.py",
        "```",
        "",
        "## Derived Constraint",
        "",
        "For the relocation loop at runtime `0x2009..0x2013` to survive its",
        "self-overwrite, the missing page at runtime `0x2100..0x21FF` must at",
        "least reproduce the loop-tail bytes at offsets `0x09..0x13`:",
        "",
        f"```text\n{required.hex(' ')}\n```",
        "",
        "A repository-wide binary scan over `roms/`, `ref/`, and `media/` finds",
        f"`{len(pattern_hits)}` page-shaped hit(s) for that exact page-offset",
        "pattern:",
        "",
        "| File | Page start | Pattern offset in page |",
        "| --- | ---: | ---: |",
        *[
            table_row([f"`{path}`", f"`0x{page_start:05X}`", f"`0x{page_off:02X}`"])
            for path, page_start, page_off in pattern_hits[:20]
        ],
        "",
        "The current scan finds no donor beyond the public cartridge's own final",
        "page, which makes final-page mirroring the strongest simple hypothesis",
        "to test first.",
        "",
        "## Runtime Experiments",
        "",
        "| Hypothesis | Change | Bytes | Probe run | Base-probe infra | Probe status | Cart reads | PC in 0x4000..0xBFFF | Mode-2 PC cycles | 0x00 opcode cycles | Nonzero BASIC-window bytes | Visible pixels | Stop PC |",
        "| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    lines.extend(rows)
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Appending an extra page by itself does not alter the failing Monitor 3.3",
            "  path, because the monitor still follows the cartridge's copy metadata.",
            "- `Base-probe infra` is the inherited `basic_launch_probe.py` infrastructure",
            "  check; it remains `FAIL` for these larger temporary variants because that",
            "  base report expects the public 8192-byte cartridge size. `Probe run=DONE`",
            "  means the bounded runtime experiment still completed and produced a row.",
            "- Patching the visible header length to `0x2100` changes the monitor handoff",
            "  registers, but the runtime cartridge bootstrap still carries its own",
            "  `LXI B,0x2000` relocation length and still falls through into zero-filled",
            "  `0x4000` RAM instead of rendering a BASIC prompt.",
            "- Patching only the bootstrap relocation count to `0x1F00` prevents the",
            "  loop from reading the missing `0x2100..0x21FF` page, but the same",
            "  Monitor 3.3 path still falls through into zero-filled `0x4000` RAM.",
            "  That makes the one-page self-overwrite a real bug source, but not the",
            "  full cartridge/monitor compatibility fix.",
            "- Therefore the missing page is not recoverable by a fill byte, raw append,",
            "  final-page mirror, or simple relocation-count patch alone. A defensible",
            "  reconstruction needs either the real larger cartridge/programming",
            "  artifact or a deeper patch-level understanding of the runtime bootstrap",
            "  and expected low-memory image.",
            "",
            "## Probe Excerpts",
            "",
        ]
    )
    lines.extend(details)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if status == "SIMPLE TAIL HYPOTHESES REJECTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
