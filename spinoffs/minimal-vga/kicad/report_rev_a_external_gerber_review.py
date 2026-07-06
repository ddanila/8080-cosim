#!/usr/bin/env python3
import re
import shutil
import subprocess
import sys
from pathlib import Path


INPUTS = [
    "gerbers/rev-a-physical-F_Cu.gtl",
    "gerbers/rev-a-physical-In1_Cu.g1",
    "gerbers/rev-a-physical-In2_Cu.g2",
    "gerbers/rev-a-physical-B_Cu.gbl",
    "gerbers/rev-a-physical-F_Mask.gts",
    "gerbers/rev-a-physical-B_Mask.gbs",
    "gerbers/rev-a-physical-F_Silkscreen.gto",
    "gerbers/rev-a-physical-B_Silkscreen.gbo",
    "gerbers/rev-a-physical-Edge_Cuts.gm1",
    "drill/rev-a-physical.drl",
]

EXPECTED_SVGS = [
    "rev-a-physical-F_Cu.gtl.top.copper.svg",
    "rev-a-physical-In1_Cu.g1.inner.copper.svg",
    "rev-a-physical-In2_Cu.g2.inner.copper.svg",
    "rev-a-physical-B_Cu.gbl.bottom.copper.svg",
    "rev-a-physical-F_Mask.gts.top.soldermask.svg",
    "rev-a-physical-B_Mask.gbs.bottom.soldermask.svg",
    "rev-a-physical-F_Silkscreen.gto.top.silkscreen.svg",
    "rev-a-physical-B_Silkscreen.gbo.bottom.silkscreen.svg",
    "rev-a-physical-Edge_Cuts.gm1.all.outline.svg",
    "rev-a-physical.drl.all.drill.svg",
    "rev-a-physical.top.svg",
    "rev-a-physical.bottom.svg",
]

SCREENSHOTS = [
    ("rev-a-physical.top.svg", "rev-a-physical-tracespace-top.png"),
    ("rev-a-physical.bottom.svg", "rev-a-physical-tracespace-bottom.png"),
]


def run_tracespace(out_dir, render_dir):
    npx = shutil.which("npx")
    if not npx:
        return "npx executable not found"

    missing_inputs = [name for name in INPUTS if not (out_dir / name).exists()]
    if missing_inputs:
        return "Missing Tracespace inputs: " + ", ".join(missing_inputs)

    render_dir.mkdir(parents=True, exist_ok=True)
    for old_svg in render_dir.glob("*.svg"):
        old_svg.unlink()

    cmd = [
        npx,
        "--yes",
        "@tracespace/cli",
        "--quiet",
        f"--out={render_dir}",
        *[str(out_dir / name) for name in INPUTS],
    ]
    try:
        completed = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return "Tracespace render timed out after 60 seconds"
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip()
        return "Tracespace render failed" + (f": {detail}" if detail else "")
    return None


def svg_dimensions(text):
    match = re.search(r'viewBox="([^"]+)"', text)
    if not match:
        return None
    values = match.group(1).split()
    if len(values) != 4:
        return None
    try:
        width = float(values[2])
        height = float(values[3])
    except ValueError:
        return None
    return width, height


def inspect_svg(path):
    if not path.exists() or path.stat().st_size == 0:
        return ["missing or empty"], None
    text = path.read_text(errors="replace")
    failures = []
    if "<svg" not in text:
        failures.append("missing SVG root")
    dimensions = svg_dimensions(text)
    if not dimensions:
        failures.append("missing numeric viewBox")
    elif dimensions[0] <= 0 or dimensions[1] <= 0:
        failures.append("non-positive viewBox")
    return failures, dimensions


def find_chrome():
    for name in ["google-chrome", "chromium", "chromium-browser"]:
        path = shutil.which(name)
        if path:
            return path
    return None


def run_chrome_screenshots(render_dir):
    chrome = find_chrome()
    if not chrome:
        return ["Chrome/Chromium executable not found for browser screenshots"]

    failures = []
    for source_name, image_name in SCREENSHOTS:
        source = render_dir / source_name
        image = render_dir / image_name
        if not source.exists():
            failures.append(f"{image_name}: missing source SVG {source_name}")
            continue
        cmd = [
            chrome,
            "--headless",
            "--no-sandbox",
            "--disable-gpu",
            "--window-size=1400,1400",
            f"--screenshot={image}",
            source.resolve().as_uri(),
        ]
        try:
            completed = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
        except subprocess.TimeoutExpired:
            failures.append(f"{image_name}: Chrome screenshot timed out after 30 seconds")
            continue
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            failures.append(f"{image_name}: Chrome screenshot failed" + (f": {detail}" if detail else ""))
            continue
        if not image.exists() or image.stat().st_size < 10000:
            failures.append(f"{image_name}: missing, empty, or suspiciously small PNG")
            continue
        if not image.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            failures.append(f"{image_name}: missing PNG signature")
    return failures


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def build_report(out_dir):
    render_dir = out_dir / "review" / "tracespace"
    render_failure = run_tracespace(out_dir, render_dir)
    failures = []
    if render_failure:
        failures.append(render_failure)

    rows = []
    for name in EXPECTED_SVGS:
        path = render_dir / name
        svg_failures, dimensions = inspect_svg(path)
        failures.extend(f"{name}: {failure}" for failure in svg_failures)
        if dimensions:
            viewbox = f"{dimensions[0]:.3f} x {dimensions[1]:.3f}"
        else:
            viewbox = "-"
        rows.append(
            [
                f"review/tracespace/{name}",
                path.stat().st_size if path.exists() else 0,
                viewbox,
                "PASS" if not svg_failures else "FAIL",
            ]
        )

    extra = sorted(path.name for path in render_dir.glob("*.svg") if path.name not in EXPECTED_SVGS)
    if extra:
        failures.append("Unexpected Tracespace SVG outputs: " + ", ".join(extra))

    failures.extend(run_chrome_screenshots(render_dir))
    screenshot_rows = []
    for _, image_name in SCREENSHOTS:
        image = render_dir / image_name
        ok = image.exists() and image.stat().st_size >= 10000
        screenshot_rows.append(
            [
                f"review/tracespace/{image_name}",
                image.stat().st_size if image.exists() else 0,
                "PASS" if ok else "FAIL",
            ]
        )

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Rev A external Gerber/drill review",
        "",
        f"Package: `{out_dir}`",
        "Viewer: `@tracespace/cli` via `npx --yes @tracespace/cli --quiet`",
        f"Status: **{status}**",
        "",
        "This report records an independent render pass over the exported Gerber",
        "and Excellon drill files. It is a visual-review aid and parser sanity",
        "check; it does not replace final vendor upload review.",
        "",
        "## Inputs",
        "",
    ]
    lines.extend(f"- `{name}`" for name in INPUTS)
    lines.extend(
        [
            "",
            "## Rendered SVG Outputs",
            "",
            "| File | Bytes | ViewBox | Status |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    lines.extend(table_row(row) for row in rows)
    lines.extend(
        [
            "",
            "## Browser Screenshots",
            "",
            "| File | Bytes | Status |",
            "| --- | ---: | --- |",
        ]
    )
    lines.extend(table_row(row) for row in screenshot_rows)

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), status


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    report, status = build_report(out_dir)
    path = out_dir / "external-gerber-review.md"
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
