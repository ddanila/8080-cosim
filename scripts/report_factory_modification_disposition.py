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
    "D14": "АП2 serial-driver area: registered notch-up orientation maps the right row to D14.8-.5 and the first four left-row holes to D14.1-.4; position 159 closes the D32.4/GND-to-D14.1 link, while the fifth landing and remaining replacement traces stay held",
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
    nets = board["nets"]
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

    d14 = modification["d14"]
    d14_link = d14["ground_link"]
    d14_rows = []
    d14_ok = True
    for observation in d14_link["component_observations"]:
        endpoint_rows = []
        for endpoint_name, pixel_name in (
            ("upper_endpoint", "upper_endpoint_px"),
            ("lower_endpoint", "lower_endpoint_px"),
        ):
            endpoint = d14_link[endpoint_name]
            observed = image_to_board(
                observation["image"],
                observation[pixel_name],
                "component_grid",
                panorama,
                board_registration,
            )
            error = math.dist(observed, endpoint["board_mm"])
            endpoint_rows.append((endpoint, observed, error))
            d14_ok &= error <= 0.15
        observed_length = math.dist(endpoint_rows[0][1], endpoint_rows[1][1])
        expected_length = math.dist(
            d14_link["upper_endpoint"]["board_mm"],
            d14_link["lower_endpoint"]["board_mm"],
        )
        length_error = abs(observed_length - expected_length)
        d14_ok &= length_error <= 0.15
        d14_rows.append((observation, endpoint_rows, length_error))
    gnd_nodes = {tuple(node) for node in nets["GND"]["nodes"]}
    d14_ok &= {("D32", "4"), ("D14", "1")} <= gnd_nodes

    guard_ok = (
        all(ref in chips for ref in AFFECTED)
        and all(path.exists() and path.stat().st_size > 1_000_000 for path in detail_photos)
        and MOD_REGISTRATION.exists()
        and all(ref in bodge for ref in AFFECTED)
        and "Factory solder-side cuts and patches" in bodge
        and d15_ok
        and d14_ok
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
        "close the D15 cut topology and the D14 position-159 ground link. D56,",
        "D11, and the remaining D14 auxiliary/replacement paths stay unproved.",
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
        elif ref == "D14":
            disposition = "PARTIAL PHOTO-CLOSE — position 159 preserves D32.4/GND-to-D14.1; remaining fifth landing and replacement traces are held"
            closure = "two independent component views plus notch-oriented factory row registration; map the fifth landing, three long traces, and right-row dogleg before full release"
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
        "",
        "## D14 position-159 registration",
        "",
        "Both component photographs fix D14 and D32 notch-up. This maps the",
        "factory detail's four-hole right row to D14.8 through D14.5 and the",
        "first four holes of the five-hole left row to D14.1 through D14.4.",
        "The position-159 leader reaches the D14.1-side stub. In both views, one",
        "uninterrupted copper strip joins that landing directly to D32.4, already",
        "a guarded `GND` pin. The clean source model therefore assigns D14.1 to",
        "`GND` and preserves the executed factory topology without adding an",
        "unmeasured auxiliary drill.",
        "",
        "| Component view | D32.4 fit error | D14.1 fit error | Link-length error | Result |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for observation, endpoint_rows, length_error in d14_rows:
        lines.append(row([
            Path(observation["image"]).name,
            f"{endpoint_rows[0][2]:.3f} mm",
            f"{endpoint_rows[1][2]:.3f} mm",
            f"{length_error:.3f} mm",
            "continuous D32.4/GND-to-D14.1 copper",
        ]))
    lines += [
        "",
        "The fifth left-row landing below D14.4, the three long replacement",
        "traces, and the right-row dogleg are not electrically closed by these",
        "views. D14.2 and D14.7 remain measurement boundaries, and no remote net",
        "or fabrication geometry is inferred from the drawing alone.",
    ]
    lines += [
        "",
        "## Guarded evidence",
        "",
        "- `PXL_20260711_114626340.jpg`: full Вид В and all four local details.",
        "- `PXL_20260711_114633498.jpg`: enlarged D15 Разрезать operation.",
        "- `PXL_20260711_114638730.MP.jpg`: full-resolution positions 150/159 context.",
        "- `factory-modification-registration.json`: two-face D15 cut-pair and two-view D14 position-159 registration.",
        "- `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`: factory-versus-owner disposition.",
        "",
        "## Release rule",
        "",
        "Do not release or reroute the board on netlist equivalence alone. For each",
        "of D56/D11 and the remaining D14 detail, identify the modified pad/via pair(s), the cut original",
        "segment, and the replacement connection; then prove the final source-PCB",
        "net partition matches the factory result. D15 and the D14.1 ground link",
        "are electrically closed; their unmeasured auxiliary-hole geometry remains",
        "held only for an original-artwork replica.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if guard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
