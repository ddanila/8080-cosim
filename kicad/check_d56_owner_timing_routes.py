#!/usr/bin/python3
"""Guard the owner-closed D54/D55/D56 timing topology and routed copper."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD_JSON = ROOT / "kicad" / "juku.board.json"
SOURCE = ROOT / "kicad" / "juku.kicad_pcb"
ROUTED = ROOT / "kicad" / "juku_routed.kicad_pcb"
AFFECTED_NETS = ("PIT_HSYNC_DSL", "VERT_SYNC", "D56_Q2N_TAG16", "SYNC_B")
BLOCKERS = {
    "shorting_items",
    "clearance",
    "tracks_crossing",
    "hole_clearance",
    "hole_to_hole",
    "track_dangling",
    "via_dangling",
    "copper_edge_clearance",
}


def expected_endpoints() -> dict[tuple[str, str], str]:
    spec = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    result: dict[tuple[str, str], str] = {}
    for net_name in AFFECTED_NETS:
        for ref, pin in spec["nets"][net_name].get("nodes", []):
            endpoint = (ref, pin)
            if endpoint in result:
                raise SystemExit(f"board JSON duplicates affected endpoint {ref}.{pin}")
            result[endpoint] = net_name
    return result


def pad_nets(board: pcbnew.BOARD, endpoints: dict[tuple[str, str], str]) -> dict[tuple[str, str], str]:
    result = {}
    for ref, pin in endpoints:
        footprint = board.FindFootprintByReference(ref)
        pad = footprint.FindPadByNumber(pin) if footprint else None
        if pad is None:
            raise SystemExit(f"missing PCB endpoint {ref}.{pin}")
        result[(ref, pin)] = pad.GetNetname()
    return result


def route_stats(board: pcbnew.BOARD) -> dict[str, dict[str, float | int]]:
    result = {}
    for net_name in AFFECTED_NETS:
        items = [item for item in board.GetTracks() if item.GetNetname() == net_name]
        tracks = [item for item in items if item.GetClass() == "PCB_TRACK"]
        result[net_name] = {
            "segments": len(tracks),
            "vias": sum(item.GetClass() == "PCB_VIA" for item in items),
            "length_mm": sum(pcbnew.ToMM(item.GetLength()) for item in tracks),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--routed", type=Path, default=ROUTED)
    parser.add_argument("--kicad-cli", type=Path)
    args = parser.parse_args()

    cli = args.kicad_cli
    if cli is None:
        cli = Path(
            subprocess.check_output(
                [str(ROOT / "scripts" / "find-kicad-cli.sh")], text=True
            ).strip()
        )

    expected = expected_endpoints()
    source = pcbnew.LoadBoard(str(args.source))
    routed = pcbnew.LoadBoard(str(args.routed))
    for label, board in (("source", source), ("routed", routed)):
        actual = pad_nets(board, expected)
        if actual != expected:
            mismatches = {
                f"{ref}.{pin}": (expected[(ref, pin)], actual[(ref, pin)])
                for ref, pin in expected
                if actual[(ref, pin)] != expected[(ref, pin)]
            }
            raise SystemExit(f"{label} D56 owner-timing pad mismatch: {mismatches}")

    source_stats = route_stats(source)
    if any(item["segments"] or item["vias"] for item in source_stats.values()):
        raise SystemExit(f"source PCB unexpectedly owns routed D56 timing copper: {source_stats}")

    stats = route_stats(routed)
    if stats["SYNC_B"] != {"segments": 0, "vias": 0, "length_mm": 0}:
        raise SystemExit(f"singleton SYNC_B retained obsolete routed copper: {stats['SYNC_B']}")
    for net_name in AFFECTED_NETS[:3]:
        if not stats[net_name]["segments"]:
            raise SystemExit(f"routed PCB has no copper for {net_name}")
    total_length = sum(float(stats[name]["length_mm"]) for name in AFFECTED_NETS)
    total_segments = sum(int(stats[name]["segments"]) for name in AFFECTED_NETS)
    total_vias = sum(int(stats[name]["vias"]) for name in AFFECTED_NETS)
    if total_length > 176.0 or total_segments > 125 or total_vias > 9:
        raise SystemExit(
            "D56 timing reroute exceeded the guarded compactness envelope: "
            f"length={total_length:.3f} segments={total_segments} vias={total_vias}"
        )

    with tempfile.TemporaryDirectory(prefix="juku-d56-owner-timing-") as tmp_name:
        report_path = Path(tmp_name) / "drc.json"
        proc = subprocess.run(
            [
                str(cli),
                "pcb",
                "drc",
                "--format",
                "json",
                "--output",
                str(report_path),
                str(args.routed),
            ],
            text=True,
            capture_output=True,
        )
        if not report_path.exists():
            raise SystemExit(f"KiCad DRC produced no report: {proc.stdout}{proc.stderr}")
        report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("unconnected_items"):
        raise SystemExit(f"routed PCB has {len(report['unconnected_items'])} open item(s)")
    counts: dict[str, int] = {}
    for violation in report.get("violations", []):
        kind = violation.get("type", "unknown")
        counts[kind] = counts.get(kind, 0) + 1
    failures = {kind: counts.get(kind, 0) for kind in BLOCKERS if counts.get(kind)}
    if failures:
        raise SystemExit(f"D56 owner timing reroute has electrical DRC blockers: {failures}")

    print(
        "D56 OWNER TIMING ROUTES: PASS; "
        f"length={total_length:.3f}mm segments={total_segments} vias={total_vias} "
        "opens=0 electrical=0"
    )


if __name__ == "__main__":
    main()
