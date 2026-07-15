#!/usr/bin/env python3
"""Guard the unresolved electrical disposition of factory Вид В modifications."""
from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.board.json"
BODGE = ROOT / "ref/photos/juku-pcb-2/BODGE-TRIAGE.md"
PHOTO_DIR = ROOT / "ref/photos/dgsh5-109-009-sb"
REPORT = ROOT / "docs/factory-modification-disposition.md"
MOD_REGISTRATION = PHOTO_DIR / "factory-modification-registration.json"
PANORAMA_REGISTRATION = ROOT / "docs/photo-registration/panorama-registration.json"
BOARD_REGISTRATION = ROOT / "docs/photo-registration/board-registration.json"
AFFECTED = {
    "D56": "АГ3 timing area: multiple drawn cuts/patches around the package fanout",
    "D15": "EPROM area: Разрезать cuts the auxiliary A2/A1 bridge between the D15.8- and D15.9-side landings; no replacement wire is drawn in the D15 detail",
    "D14": "АП2 serial-driver area: position-159 leader enters a five-hole auxiliary/left field beside the four-pad package row; three long replacement traces and one right-row dogleg are drawn, but mirrored pin numbering is not proved",
    "D11": "8251 USART area: detail shows one 14-pad package column plus a four-hole auxiliary field and a position-159 bridge; a held-out-validated solder fit localizes the visible reworked copper beside D11 pins 4-6, but the obscured bridge endpoints remain unproved",
}


def row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def matrix(values: list[float]) -> list[list[float]]:
    return [values[0:3], values[3:6], values[6:9]]


def inverse3(m: list[list[float]]) -> list[list[float]]:
    a, b, c = m[0]
    d, e, f = m[1]
    g, h, i = m[2]
    cofactors = [
        [e * i - f * h, c * h - b * i, b * f - c * e],
        [f * g - d * i, a * i - c * g, c * d - a * f],
        [d * h - e * g, b * g - a * h, a * e - b * d],
    ]
    det = a * cofactors[0][0] + b * cofactors[1][0] + c * cofactors[2][0]
    if abs(det) < 1e-12:
        raise ValueError("singular registration matrix")
    return [[value / det for value in row_values] for row_values in cofactors]


def multiply(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return [
        [sum(a[r][k] * b[k][c] for k in range(3)) for c in range(3)]
        for r in range(3)
    ]


def project(h: list[list[float]], point: list[float]) -> tuple[float, float]:
    x, y = point
    result = [sum(h[r][k] * (x, y, 1.0)[k] for k in range(3)) for r in range(3)]
    return result[0] / result[2], result[1] / result[2]


def image_to_board(
    image: str,
    point: list[float],
    side: str,
    panorama: dict,
    board_registration: dict,
) -> tuple[float, float]:
    image_to_panorama = matrix(
        panorama["groups"][side]["images"][image][
            "original_to_panorama_homography"
        ]
    )
    board_to_panorama = matrix(
        board_registration["groups"][side]["board_to_panorama_homography"]
    )
    return project(multiply(inverse3(board_to_panorama), image_to_panorama), point)


def main() -> int:
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    chips = {chip["ref"]: chip for chip in board["chips"]}
    bodge = BODGE.read_text(encoding="utf-8")
    modification = json.loads(MOD_REGISTRATION.read_text(encoding="utf-8"))
    panorama = json.loads(PANORAMA_REGISTRATION.read_text(encoding="utf-8"))
    board_registration = json.loads(BOARD_REGISTRATION.read_text(encoding="utf-8"))
    detail_photos = [
        PHOTO_DIR / "PXL_20260711_114626340.jpg",
        PHOTO_DIR / "PXL_20260711_114633498.jpg",
        PHOTO_DIR / "PXL_20260711_114638730.MP.jpg",
    ]
    d15_rows = []
    d15_ok = chips["D15"]["pins"].get("8") == "A2" and chips["D15"]["pins"].get("9") == "A1"
    for name in ("upper", "lower"):
        landing = modification["d15"]["landings"][name]
        component_points = [
            image_to_board(
                observation["image"],
                observation["image_px"],
                "component_grid",
                panorama,
                board_registration,
            )
            for observation in landing["component_observations"]
        ]
        centre = tuple(sum(point[axis] for point in component_points) / len(component_points) for axis in range(2))
        spread = max(math.dist(centre, point) for point in component_points)
        solder = landing["solder_confirmation"]
        solder_point = image_to_board(
            solder["image"], solder["image_px"], "solder_grid", panorama, board_registration
        )
        solder_error = math.dist(centre, solder_point)
        d15_ok &= spread <= 0.10 and solder_error <= 0.15
        d15_rows.append((name, landing, centre, spread, solder_error))

    guard_ok = (
        all(ref in chips for ref in AFFECTED)
        and all(path.exists() and path.stat().st_size > 1_000_000 for path in detail_photos)
        and MOD_REGISTRATION.exists()
        and all(ref in bodge for ref in AFFECTED)
        and "Factory solder-side cuts and patches" in bodge
        and d15_ok
    )
    status = "FACTORY MODIFICATIONS GUARDED / PAD MAPPING REQUIRED" if guard_ok else "FACTORY MODIFICATION GUARD FAILED"

    lines = [
        "# Factory modification disposition",
        "",
        "Status date: **2026-07-15**.",
        "",
        f"Status: **{status}**",
        "",
        "The `ДГШ5.109.009 СБ` Вид В detail proves that positions 150/159",
        "modify copper around D56, D15, D14, and D11. The unnumbered detail",
        "mixes mounting-side context with solder-side artwork, so it does not",
        "by itself prove package pin numbers or final net partitions.",
        "Two independent component views plus the reflected solder panorama now",
        "close the D15 cut topology; D56, D14, and D11 remain unproved.",
        "",
        "| Ref | Factory operation locality | Current disposition | Closure evidence |",
        "| --- | --- | --- | --- |",
    ]
    for ref, detail in AFFECTED.items():
        disposition = "DESIGN HOLD — affected footprint exists, exact modified pads/nets not mapped"
        closure = "registered two-sided copper overlay plus pad/via continuity (the acquired sheets 2-5 wire table covers wires/cables only, not cut pads)"
        if ref == "D15":
            disposition = "PHOTO-CLOSED — cut separates the auxiliary D15.8/A2 and D15.9/A1 landings; the clean source net partition matches"
            closure = "two independent component views, reflected solder confirmation, and guarded source pin nets; original auxiliary-hole drill placement remains fabrication-held"
        lines.append(row([
            ref,
            detail,
            disposition,
            closure,
        ]))
    lines += [
        "",
        "## D15 cut registration",
        "",
        "The enlarged factory detail draws four holes on the auxiliary trace and",
        "places `Разрезать` between the final pair, aligned between D15 pad levels",
        "8 and 9. The same pair is visible with removed intervening copper in two",
        "independent component photographs. Reflected solder copper connects the",
        "upper landing to D15.8 (`A2`) and the lower landing to D15.9 (`A1`).",
        "No replacement conductor is drawn in the D15 detail: the operation removes",
        "an unwanted A2/A1 bridge, which is exactly the net partition already present",
        "in the clean source PCB.",
        "",
        "| Landing | Board centre (mm) | Component-view agreement | Solder-view error | Resulting source net |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for name, landing, centre, spread, solder_error in d15_rows:
        lines.append(row([
            name,
            f"({centre[0]:.3f}, {centre[1]:.3f})",
            f"{spread:.3f} mm",
            f"{solder_error:.3f} mm",
            f"D15.{landing['d15_pin']} / `{landing['source_net']}`",
        ]))
    lines += [
        "",
        "These centres prove local identity and topology, not fabrication-ready drill",
        "placement. The source board therefore keeps its clean A2/A1 separation and",
        "does not invent the two auxiliary holes until a direct dimension or",
        "fabrication-grade local scale is available.",
    ]
    lines += [
        "",
        "## Guarded evidence",
        "",
        "- `PXL_20260711_114626340.jpg`: full Вид В and all four local details.",
        "- `PXL_20260711_114633498.jpg`: enlarged D15 Разрезать operation.",
        "- `PXL_20260711_114638730.MP.jpg`: full-resolution positions 150/159 context.",
        "- `factory-modification-registration.json`: two-face D15 cut-pair registration.",
        "- `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`: factory-versus-owner disposition.",
        "",
        "## Release rule",
        "",
        "Do not release or reroute the board on netlist equivalence alone. For each",
        "of D56/D14/D11, identify the modified pad/via pair(s), the cut original",
        "segment, and the replacement connection; then prove the final source-PCB",
        "net partition matches the factory result. D15 is electrically closed; its",
        "auxiliary-hole geometry remains held only for an original-artwork replica.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if guard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
