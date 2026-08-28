#!/usr/bin/env python3
"""Independent R5.J3 archive rendering and first-system BOM reconciliation.

Unlike check_revb_package.py, this reviewer reads the frozen ZIPs, renders every
Gerber and Excellon member with gerbv, and reconciles the routed PCB footprint
sets against the connectivity descriptions and the first-system BOM contract.
It never uploads files and it cannot release ORDER HOLD.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
FAB = REPO / "fab" / "minimal-vga" / "revb"
DEFAULT_PACKAGE = FAB / "package"
DEFAULT_RENDER = DEFAULT_PACKAGE / "review-r5j3"
MANIFEST = REPO / "spinoffs" / "minimal-vga" / "docs" / "rev-b-five-board-package-manifest.json"
BOM = HERE / "five-board-bom.json"
CARDS = ("cpu", "mem", "io", "backplane", "video")
GRAPHIC_SUFFIXES = (".gtl", ".gbl", ".g1", ".g2", ".gts", ".gbs", ".gto", ".gbo", ".gm1", ".drl")
INTENTIONALLY_EMPTY = {
    "cpu-B_Silkscreen.gbo",
    "mem-B_Silkscreen.gbo",
    "io-B_Silkscreen.gbo",
    "backplane-B_Silkscreen.gbo",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def command_identity(command: list[str]) -> str:
    try:
        result = subprocess.run(command, cwd=REPO, text=True, capture_output=True,
                                timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    return (result.stdout.strip() or result.stderr.strip()).splitlines()[0]


def expected_refs(board: dict) -> set[str]:
    refs: set[str] = set()
    for chip in board["chips"]:
        ref = chip["ref"]
        if chip["type"] != "REVB_BUS_39_10":
            refs.add(ref)
        elif ref == "J_BUS":
            refs.update(("J_BUS", "J_EXT"))
        else:
            refs.update((f"{ref}_BUS", f"{ref}_EXT"))
    return refs


def pcb_refs(path: Path) -> set[str]:
    text = path.read_text(errors="strict")
    refs = re.findall(
        r'\(footprint\s+"[^"]+".*?\(property\s+"Reference"\s+"([^"]+)"',
        text,
        flags=re.S,
    )
    if not refs:
        raise ValueError("no footprint Reference properties found")
    if len(refs) != len(set(refs)):
        raise ValueError("duplicate footprint references found")
    return set(refs)


def verify_bom(contract: dict) -> tuple[list[str], dict]:
    errors: list[str] = []
    rows: dict[str, dict] = {}
    for card in CARDS:
        spec = contract.get("boards", {}).get(card, {})
        pcb = FAB / f"{card}.kicad_pcb"
        board_file = HERE / f"{card}.board.json"
        if not pcb.is_file() or not board_file.is_file():
            errors.append(f"{card}: routed PCB or board description missing")
            continue
        try:
            actual = pcb_refs(pcb)
            described = expected_refs(json.loads(board_file.read_text()))
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"{card}: footprint parse failed: {exc}")
            continue
        if actual != described:
            errors.append(
                f"{card}: PCB/board-description refs differ; "
                f"PCB-only={sorted(actual-described)}, description-only={sorted(described-actual)}"
            )
        dnp = set(spec.get("dnp_refs", []))
        if not dnp <= actual:
            errors.append(f"{card}: DNP refs absent from PCB: {sorted(dnp-actual)}")
        populated = len(actual - dnp)
        if spec.get("physical_footprints") != len(actual):
            errors.append(f"{card}: physical footprint count {len(actual)} != contract {spec.get('physical_footprints')}")
        if spec.get("populated_footprints") != populated:
            errors.append(f"{card}: populated count {populated} != contract {spec.get('populated_footprints')}")
        if spec.get("first_system_pcbs") != 1:
            errors.append(f"{card}: first-system PCB quantity is not one")
        rows[card] = {"physical": len(actual), "populated": populated,
                      "dnp": len(dnp), "dnp_refs": sorted(dnp)}

    total_physical = sum(row["physical"] for row in rows.values())
    total_populated = sum(row["populated"] for row in rows.values())
    total_dnp = sum(row["dnp"] for row in rows.values())
    totals = contract.get("totals", {})
    observed_totals = {
        "board_designs": len(rows),
        "first_system_pcbs": sum(contract.get("boards", {}).get(c, {}).get("first_system_pcbs", 0) for c in CARDS),
        "physical_footprints": total_physical,
        "populated_footprints": total_populated,
        "dnp_footprints": total_dnp,
    }
    for key, observed in observed_totals.items():
        if totals.get(key) != observed:
            errors.append(f"total {key} {observed} != contract {totals.get(key)}")

    programmed = contract.get("programmed_devices", [])
    if totals.get("programmed_devices") != len(programmed):
        errors.append("programmed-device total differs")
    jedecs = sum(item.get("format") == "JEDEC" for item in programmed)
    roms = len(programmed) - jedecs
    if totals.get("jedec_devices") != jedecs or totals.get("rom_devices") != roms:
        errors.append("JEDEC/ROM programmed-device split differs")
    seen: set[tuple[str, str]] = set()
    program_rows = []
    for item in programmed:
        card, ref = item.get("board"), item.get("ref")
        identity = (card, ref)
        if identity in seen:
            errors.append(f"duplicate programmed-device identity {card}/{ref}")
        seen.add(identity)
        if card not in rows:
            errors.append(f"programmed device {card}/{ref}: unknown card")
        else:
            source_refs = pcb_refs(FAB / f"{card}.kicad_pcb")
            if ref not in source_refs:
                errors.append(f"programmed device {card}/{ref}: footprint absent")
            if ref in rows[card]["dnp_refs"]:
                errors.append(f"programmed device {card}/{ref}: marked DNP")
        artifact = REPO / str(item.get("artifact", ""))
        if not artifact.is_file():
            errors.append(f"programmed device {card}/{ref}: artifact missing")
            continue
        data = artifact.read_bytes()
        digest = sha256(data)
        if len(data) != item.get("bytes") or digest != item.get("sha256"):
            errors.append(f"programmed device {card}/{ref}: artifact size/hash differs")
        if item.get("format") == "JEDEC" and not data.startswith(b"\x02"):
            errors.append(f"programmed device {card}/{ref}: JEDEC STX marker missing")
        program_rows.append({"board": card, "ref": ref, "format": item.get("format"),
                             "bytes": len(data), "sha256": digest})

    return errors, {"boards": rows, "totals": observed_totals,
                    "programmed_devices": program_rows}


def png_metrics(path: Path, identify: str) -> tuple[int, int, float, int]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 33:
        raise ValueError("missing PNG signature/header")
    width, height = struct.unpack(">II", data[16:24])
    result = subprocess.run(
        [identify, "-format", "%[fx:mean]", str(path)], text=True,
        capture_output=True, timeout=15, check=False,
    )
    if result.returncode:
        raise ValueError("ImageMagick identify failed")
    return width, height, float(result.stdout), len(data)


def gerbv_render(gerbv: str, identify: str, inputs: list[Path], output: Path,
                 colors: list[str], mirror: bool = False,
                 allow_blank: bool = False) -> dict:
    log = output.with_suffix(".gerbv.log")
    cmd = [gerbv, "-x", "png", "-a", "-w", "1200x1200", "-B", "3",
           "-b", "#FFFFFF", "-l", str(log), "-o", str(output)]
    if mirror:
        cmd += ["-m", "X"]
    for color in colors:
        cmd += ["-f", color]
    cmd += [str(path) for path in inputs]
    completed = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True,
                               timeout=60, check=False)
    if completed.returncode:
        detail = (completed.stderr.strip() or completed.stdout.strip()).splitlines()[-1:]
        raise ValueError(f"gerbv exit {completed.returncode}: {' '.join(detail)}")
    width, height, mean, size = png_metrics(output, identify)
    if width != 1200 or height != 1200:
        raise ValueError(f"unexpected raster size {width}x{height}")
    blank = not 0.000001 < mean < 0.999999
    if size < 500 or (blank and not allow_blank):
        raise ValueError(f"blank/suspicious raster: bytes={size}, mean={mean:.9f}")
    warning_text = "\n".join((completed.stdout, completed.stderr,
                               log.read_text(errors="replace") if log.exists() else ""))
    if log.exists():
        log.unlink()
    return {"file": output.name, "bytes": size, "width": width, "height": height,
            "mean": round(mean, 9),
            "blank_expected": bool(blank and allow_blank),
            "x2_attribute_warnings": warning_text.count("Unknown RS-274X extension")}


def verify_and_render(package_root: Path, render_root: Path) -> tuple[list[str], dict]:
    errors: list[str] = []
    results: dict[str, dict] = {}
    gerbv = shutil.which("gerbv")
    identify = shutil.which("identify")
    if not gerbv or not identify:
        return ["gerbv and ImageMagick identify are required"], results
    manifest = json.loads(MANIFEST.read_text())
    render_root.mkdir(parents=True, exist_ok=True)

    for card in CARDS:
        card_manifest = manifest.get("cards", {}).get(card, {})
        archive = package_root / f"{card}.zip"
        card_out = render_root / card
        card_out.mkdir(parents=True, exist_ok=True)
        for old in card_out.glob("*.png"):
            old.unlink()
        if not archive.is_file():
            errors.append(f"{card}: archive missing")
            continue
        archive_data = archive.read_bytes()
        if sha256(archive_data) != card_manifest.get("archive_sha256"):
            errors.append(f"{card}: archive hash differs from frozen manifest")
            continue
        card_result = {"archive_sha256": sha256(archive_data), "layers": [], "composites": []}
        results[card] = card_result
        try:
            zf = zipfile.ZipFile(archive)
        except zipfile.BadZipFile:
            errors.append(f"{card}: bad ZIP")
            continue
        with zf, tempfile.TemporaryDirectory(prefix=f"revb-{card}-review-") as temp_name:
            temp = Path(temp_name)
            names = sorted(card_manifest.get("members", {}))
            expected_members = {f"{card}/{name}" for name in names}
            actual_members = {name for name in zf.namelist() if not name.endswith("/")}
            if actual_members != expected_members or any(
                    PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
                    for name in actual_members):
                errors.append(f"{card}: unsafe or unexpected archive membership")
                continue
            extracted: dict[str, Path] = {}
            for name in names:
                data = zf.read(f"{card}/{name}")
                if sha256(data) != card_manifest["members"][name]["sha256"]:
                    errors.append(f"{card}/{name}: member hash differs")
                    continue
                path = temp / name
                path.write_bytes(data)
                extracted[name] = path

            for name in names:
                if not name.endswith(GRAPHIC_SUFFIXES) or name not in extracted:
                    continue
                output = card_out / f"{name}.png"
                try:
                    metric = gerbv_render(gerbv, identify, [extracted[name]], output,
                                          ["#000000"], allow_blank=name in INTENTIONALLY_EMPTY)
                    metric["source"] = name
                    card_result["layers"].append(metric)
                except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                    errors.append(f"{card}/{name}: render failed: {exc}")

            composites = {
                "top": ([f"{card}-Edge_Cuts.gm1", f"{card}-F_Cu.gtl",
                         f"{card}-F_Silkscreen.gto", f"{card}.drl"], False),
                "bottom": ([f"{card}-Edge_Cuts.gm1", f"{card}-B_Cu.gbl",
                            f"{card}-B_Silkscreen.gbo", f"{card}.drl"], True),
            }
            for side, (source_names, mirror) in composites.items():
                if not all(name in extracted for name in source_names):
                    errors.append(f"{card}: {side} composite inputs missing")
                    continue
                output = card_out / f"{card}-{side}-composite.png"
                try:
                    metric = gerbv_render(
                        gerbv, identify, [extracted[name] for name in source_names], output,
                        ["#202020", "#C02020CC", "#2060C0", "#000000"], mirror=mirror,
                    )
                    metric["sources"] = source_names
                    metric["mirrored_for_view"] = mirror
                    card_result["composites"].append(metric)
                except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
                    errors.append(f"{card}: {side} composite render failed: {exc}")

    viewer = command_identity([gerbv, "--version"]) if gerbv else "unavailable"
    if viewer.strip() == "gerbv version":
        package_version = command_identity(["dpkg-query", "-W", "-f=${Version}", "gerbv"])
        if package_version != "unavailable":
            viewer = f"gerbv {package_version}"
    return errors, {
        "viewer": viewer,
        "image_probe": command_identity([identify, "--version"]) if identify else "unavailable",
        "cards": results,
    }


def self_test(contract: dict) -> list[str]:
    failures: list[str] = []
    mutated = copy.deepcopy(contract)
    mutated["boards"]["io"]["physical_footprints"] += 1
    errors, _ = verify_bom(mutated)
    if not any("io: physical footprint count" in error for error in errors):
        failures.append("wrong footprint-count mutation was accepted")
    mutated = copy.deepcopy(contract)
    mutated["programmed_devices"][0]["sha256"] = "0" * 64
    errors, _ = verify_bom(mutated)
    if not any("mem/U1: artifact size/hash differs" in error for error in errors):
        failures.append("wrong programmed-artifact hash mutation was accepted")
    mutated = copy.deepcopy(contract)
    mutated["boards"]["io"]["dnp_refs"].append("U2")
    mutated["boards"]["io"]["populated_footprints"] -= 1
    mutated["totals"]["populated_footprints"] -= 1
    mutated["totals"]["dnp_footprints"] += 1
    errors, _ = verify_bom(mutated)
    if not any("io/U2: marked DNP" in error for error in errors):
        failures.append("programmed-device-as-DNP mutation was accepted")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--render-root", type=Path, default=DEFAULT_RENDER)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    contract = json.loads(BOM.read_text())
    errors, bom_result = verify_bom(contract)
    render_errors, render_result = verify_and_render(args.package_root, args.render_root)
    errors.extend(render_errors)
    if args.self_test:
        errors.extend(f"self-test: {failure}" for failure in self_test(contract))
    result = {
        "schema": 1,
        "status": "PASS" if not errors else "FAIL",
        "scope": "Independent R5.J3 archive render and first-system BOM/programming reconciliation; ORDER HOLD",
        "package_manifest": str(MANIFEST.relative_to(REPO)),
        "bom_contract": str(BOM.relative_to(REPO)),
        "bom": bom_result,
        "render": render_result,
        "errors": errors,
    }
    args.render_root.mkdir(parents=True, exist_ok=True)
    result_path = args.render_root / "review.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    if errors:
        print("R5.J3 independent release review FAILED:")
        for error in errors:
            print(f"- {error}")
        print(f"wrote {result_path}")
        return 1
    layer_count = sum(len(card["layers"]) for card in render_result["cards"].values())
    composite_count = sum(len(card["composites"]) for card in render_result["cards"].values())
    print(f"R5.J3 independent release review PASS: {layer_count} separate layers/drills + "
          f"{composite_count} composites rendered; 131 footprints (124 populated, 7 DNP); "
          "6 programmed devices (5 GAL + 1 ROM)")
    if args.self_test:
        print("R5.J3 negative controls PASS: footprint count, artifact hash and programmed-DNP mutations rejected")
    print(f"wrote {result_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
