#!/usr/bin/env python3
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = ROOT / "fab" / "gerbers"

INPUTS = [
    "juku_routed-F_Cu.gtl",
    "juku_routed-B_Cu.gbl",
    "juku_routed-F_Mask.gts",
    "juku_routed-B_Mask.gbs",
    "juku_routed-F_Silkscreen.gto",
    "juku_routed-B_Silkscreen.gbo",
    "juku_routed-Edge_Cuts.gm1",
    "juku_routed.drl",
]

EXPECTED_SVGS = [
    "juku_routed-F_Cu.gtl.top.copper.svg",
    "juku_routed-B_Cu.gbl.bottom.copper.svg",
    "juku_routed-F_Mask.gts.top.soldermask.svg",
    "juku_routed-B_Mask.gbs.bottom.soldermask.svg",
    "juku_routed-F_Silkscreen.gto.top.silkscreen.svg",
    "juku_routed-B_Silkscreen.gbo.bottom.silkscreen.svg",
    "juku_routed-Edge_Cuts.gm1.all.outline.svg",
    "juku_routed.drl.all.drill.svg",
    "juku_routed.top.svg",
    "juku_routed.bottom.svg",
]

SCREENSHOTS = [
    ("juku_routed.top.svg", "juku_routed-tracespace-top.png"),
    ("juku_routed.bottom.svg", "juku_routed-tracespace-bottom.png"),
]


def repo_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def run_tracespace(out_dir, render_dir):
    npx = shutil.which("npx")
    if not npx:
        return "npx executable not found"

    missing_inputs = [name for name in INPUTS if not (out_dir / name).exists()]
    if missing_inputs:
        return "Missing Tracespace inputs: " + ", ".join(missing_inputs)

    render_dir.mkdir(parents=True, exist_ok=True)
    for old in list(render_dir.glob("*.svg")) + list(render_dir.glob("*.png")):
        old.unlink()

    cmd = [
        npx,
        "--yes",
        "@tracespace/cli",
        "--quiet",
        f"--out={render_dir}",
        *[str(out_dir / name) for name in INPUTS],
    ]
    try:
        completed = subprocess.run(cmd, text=True, capture_output=True, timeout=90)
    except subprocess.TimeoutExpired:
        return "Tracespace render timed out after 90 seconds"
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
        return float(values[2]), float(values[3])
    except ValueError:
        return None


def inspect_svg(path, allow_empty=False):
    if not path.exists() or path.stat().st_size == 0:
        return ["missing or empty"], None
    text = path.read_text(errors="replace")
    failures = []
    if "<svg" not in text:
        failures.append("missing SVG root")
    dimensions = svg_dimensions(text)
    if not dimensions:
        failures.append("missing numeric viewBox")
    elif (dimensions[0] <= 0 or dimensions[1] <= 0) and not allow_empty:
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
            "--window-size=1600,1400",
            f"--screenshot={image}",
            source.resolve().as_uri(),
        ]
        try:
            completed = subprocess.run(cmd, text=True, capture_output=True, timeout=45)
        except subprocess.TimeoutExpired:
            failures.append(f"{image_name}: Chrome screenshot timed out after 45 seconds")
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
    failures = []
    render_failure = run_tracespace(out_dir, render_dir)
    if render_failure:
        failures.append(render_failure)

    rows = []
    for name in EXPECTED_SVGS:
        path = render_dir / name
        svg_failures, dimensions = inspect_svg(path, allow_empty=name == "juku_routed-B_Silkscreen.gbo.bottom.silkscreen.svg")
        failures.extend(f"{name}: {failure}" for failure in svg_failures)
        viewbox = f"{dimensions[0]:.3f} x {dimensions[1]:.3f}" if dimensions else "-"
        rows.append([
            repo_relative(path),
            path.stat().st_size if path.exists() else 0,
            viewbox,
            "PASS" if not svg_failures else "FAIL",
        ])

    extra = sorted(path.name for path in render_dir.glob("*.svg") if path.name not in EXPECTED_SVGS)
    if extra:
        failures.append("Unexpected Tracespace SVG outputs: " + ", ".join(extra))

    failures.extend(run_chrome_screenshots(render_dir))
    screenshot_rows = []
    for _, image_name in SCREENSHOTS:
        image = render_dir / image_name
        ok = image.exists() and image.stat().st_size >= 10000
        screenshot_rows.append([
            repo_relative(image),
            image.stat().st_size if image.exists() else 0,
            "PASS" if ok else "FAIL",
        ])

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Main board external Gerber/drill review",
        "",
        f"Package: `{repo_relative(out_dir)}`",
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
    lines.extend(f"- `{repo_relative(out_dir / name)}`" for name in INPUTS)
    lines.extend([
        "",
        "## Rendered SVG Outputs",
        "",
        "| File | Bytes | ViewBox | Status |",
        "| --- | ---: | ---: | --- |",
    ])
    lines.extend(table_row(row) for row in rows)
    lines.extend([
        "",
        "## Browser Screenshots",
        "",
        "| File | Bytes | Status |",
        "| --- | ---: | --- |",
    ])
    lines.extend(table_row(row) for row in screenshot_rows)

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), status


def main():
    out_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUT_DIR
    report, status = build_report(out_dir)
    path = out_dir / "external-gerber-review.md"
    path.write_text(report)
    print(report)
    print(f"Wrote {repo_relative(path)}")
    return 0 if status == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
