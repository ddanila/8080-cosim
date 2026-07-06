#!/usr/bin/env python3
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOARD = ROOT / "kicad" / "juku_routed.kicad_pcb"
DEFAULT_OUT_DIR = ROOT / "fab" / "gerbers"
EXPECTED_FAB_FILES = [
    "juku_routed-F_Cu.gtl",
    "juku_routed-B_Cu.gbl",
    "juku_routed-F_Silkscreen.gto",
    "juku_routed-B_Silkscreen.gbo",
    "juku_routed-F_Mask.gts",
    "juku_routed-B_Mask.gbs",
    "juku_routed-Edge_Cuts.gm1",
    "juku_routed-job.gbrjob",
    "juku_routed.drl",
]
ELECTRICAL_BLOCKERS = {
    "clearance",
    "shorting_items",
    "unconnected_items",
}


def repo_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def find_kicad_cli():
    if os.environ.get("KICAD_CLI"):
        return os.environ["KICAD_CLI"]
    helper = ROOT / "scripts" / "find-kicad-cli.sh"
    if helper.exists():
        result = run([str(helper)], stdout=subprocess.PIPE)
        return result.stdout.strip()
    return "kicad-cli"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def gerber_markers(name):
    if name.endswith(".drl"):
        return ["M48", "METRIC"]
    if name.endswith(".gbrjob"):
        return ["Header", "GeneralSpecs", "FilesAttributes"]
    markers = ["%TF.GenerationSoftware,KiCad", "%FSLAX46Y46*%", "%MOMM*%"]
    if "-Edge_Cuts." in name:
        markers.append("%TF.FileFunction,Profile")
    elif "_Cu." in name or "-F_Cu." in name or "-B_Cu." in name:
        markers.append("%TF.FileFunction,Copper")
    elif "_Mask." in name or "-F_Mask." in name or "-B_Mask." in name:
        markers.append("%TF.FileFunction,Soldermask")
    elif "_Silkscreen." in name or "-F_Silkscreen." in name or "-B_Silkscreen." in name:
        markers.append("%TF.FileFunction,Legend")
    return markers


def file_marker_status(path):
    text = path.read_text(errors="replace")
    missing = [marker for marker in gerber_markers(path.name) if marker not in text]
    if path.name.endswith(".gbrjob"):
        try:
            data = json.loads(text)
            if data.get("GeneralSpecs", {}).get("LayerNumber") != 2:
                missing.append("LayerNumber=2")
        except json.JSONDecodeError:
            missing.append("valid JSON")
    return "PASS" if not missing else "missing " + ", ".join(missing)


def run_drc(kicad_cli, board, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "juku_routed-drc.json"
    run([
        kicad_cli,
        "pcb",
        "drc",
        "--severity-all",
        "--format",
        "json",
        "--output",
        str(json_path),
        str(board),
    ], stdout=subprocess.PIPE)
    return json_path


def write_sha256sums(out_dir, rows):
    sha_path = out_dir / "SHA256SUMS"
    lines = []
    for name, digest, _size, _marker in rows:
        if digest:
            lines.append(f"{digest}  {name}")
    sha_path.write_text("\n".join(lines) + ("\n" if lines else ""))
    return sha_path


def build_report(board, out_dir, kicad_cli, kicad_version, drc):
    violations = drc.get("violations", [])
    unconnected = drc.get("unconnected_items", [])
    violation_types = Counter(v.get("type", "unknown") for v in violations)
    blocker_counts = Counter()
    for name in ELECTRICAL_BLOCKERS:
        if name == "unconnected_items":
            blocker_counts[name] = len(unconnected)
        else:
            blocker_counts[name] = violation_types.get(name, 0)

    file_rows = []
    failures = []
    for name in EXPECTED_FAB_FILES:
        path = out_dir / name
        if not path.exists() or path.stat().st_size == 0:
            failures.append(f"Missing or empty fabrication file: {name}")
            file_rows.append([name, "-", "-", "FAIL"])
            continue
        marker_status = file_marker_status(path)
        if marker_status != "PASS":
            failures.append(f"{name}: {marker_status}")
        file_rows.append([name, sha256(path), path.stat().st_size, marker_status])

    electrical_gate = "PASS" if not any(blocker_counts.values()) else "FAIL"
    package_gate = "PASS" if not failures else "FAIL"
    overall = "REVIEW REQUIRED"
    if electrical_gate == "FAIL" or package_gate == "FAIL":
        overall = "NOT READY"
    elif not violations and not unconnected:
        overall = "READY"

    lines = [
        "# Main board fabrication readiness",
        "",
        f"Board: `{repo_relative(board)}`",
        f"KiCad CLI: `{kicad_cli}`",
        f"KiCad version: `{kicad_version}`",
        f"Status: **{overall}**",
        "",
        "## Gates",
        "",
        f"- Electrical/routing gate: **{electrical_gate}**",
        f"- Fabrication-file inventory gate: **{package_gate}**",
        f"- Total DRC findings: {len(violations)}",
        f"- Unconnected items: {len(unconnected)}",
        "",
        "## Electrical Blockers",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ]
    for name in sorted(blocker_counts):
        lines.append(table_row([name, blocker_counts[name]]))

    if violation_types:
        lines.extend(["", "## DRC Finding Types", "", "| Type | Count |", "| --- | ---: |"])
        for typ, count in sorted(violation_types.items()):
            lines.append(table_row([typ, count]))

    lines.extend([
        "",
        "## Fabrication Files",
        "",
        "| File | SHA256 | Bytes | Format markers |",
        "| --- | --- | ---: | --- |",
    ])
    lines.extend(table_row(row) for row in file_rows)

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.extend([
        "",
        "## Disposition",
        "",
    ])
    if overall == "READY":
        lines.append("KiCad DRC and fabrication inventory are clean.")
    elif overall == "REVIEW REQUIRED":
        lines.append(
            "Routing/electrical blockers are clear and the Gerber/drill inventory "
            "is present. Remaining DRC findings are mechanical/silkscreen/library "
            "review items that need human disposition before ordering."
        )
    else:
        lines.append(
            "Do not order from this package until the failed gate(s) above are fixed."
        )
    lines.append("")
    return "\n".join(lines), overall


def main():
    board = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_BOARD
    out_dir = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_OUT_DIR
    kicad_cli = find_kicad_cli()
    kicad_version = run([kicad_cli, "version"], stdout=subprocess.PIPE).stdout.strip()
    drc_path = run_drc(kicad_cli, board, out_dir)
    drc = json.loads(drc_path.read_text())

    report, status = build_report(board, out_dir, kicad_cli, kicad_version, drc)
    rows = []
    for name in EXPECTED_FAB_FILES:
        path = out_dir / name
        if path.exists() and path.stat().st_size > 0:
            rows.append((name, sha256(path), path.stat().st_size, ""))
    sha_path = write_sha256sums(out_dir, rows)

    report_path = out_dir / "fab-readiness.md"
    report_path.write_text(report)
    print(report)
    print(f"Wrote {repo_relative(report_path)}")
    print(f"Wrote {repo_relative(sha_path)}")
    return 0 if status in {"READY", "REVIEW REQUIRED"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
