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
LOCAL_PACKAGE_REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
AFFECTED = {
    "D56": "АГ3 timing area: position-150 tubing and three position-159 solder locations register at the D56.12/D56.5 level; their electrical topology remains held",
    "D15": "EPROM area: Разрезать cuts the auxiliary A2/A1 bridge between the D15.8- and D15.9-side landings; no replacement wire is drawn in the D15 detail",
    "D14": "АП2 serial-driver area: registered notch-up orientation maps both package rows; local copper closes the D32.4/GND-to-D14.1 link and the fifth auxiliary landing is geometry-registered, while its conductor and remaining traces stay held",
    "D11": "8251 USART area: the unique L trace registers the long hole column as an auxiliary drilled/copper field, not a package row; four component-side position-159 solder locations are photo-registered, while package-local cross-side review finds no unique matching four-hole field",
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


def reflected_cross_side(
    component_fit: dict, solder_fit: dict, point: list[float]
) -> tuple[float, float]:
    """Map one component-image point through matching package-local fits."""
    component_1 = complex(*component_fit["projected_pins"]["1"])
    component_15 = complex(*component_fit["projected_pins"]["15"])
    solder_1 = complex(*solder_fit["projected_pins"]["1"])
    solder_15 = complex(*solder_fit["projected_pins"]["15"])
    factor = (solder_15 - solder_1) / (
        component_15.conjugate() - component_1.conjugate()
    )
    offset = solder_1 - factor * component_1.conjugate()
    result = offset + factor * complex(*point).conjugate()
    return result.real, result.imag


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
    local_packages = json.loads(LOCAL_PACKAGE_REPORT.read_text(encoding="utf-8"))
    nets = board["nets"]
    detail_photos = [
        PHOTO_DIR / "PXL_20260711_114626340.jpg",
        PHOTO_DIR / "PXL_20260711_114633498.jpg",
        PHOTO_DIR / "PXL_20260711_114638730.MP.jpg",
        PHOTO_DIR / "PXL_20260711_114649169.jpg",
    ]
    d56 = modification["d56"]
    d56_expected = {"d56_12_px": (291.615, 181.270), "d56_5_px": (283.995, 181.270)}
    d56_rows = []
    d56_ok = True
    for observation in d56["callout_field"]["solder_observations"]:
        errors = {}
        for pixel_name, expected in d56_expected.items():
            observed = image_to_board(
                observation["image"],
                observation[pixel_name],
                "solder_grid",
                panorama,
                board_registration,
            )
            errors[pixel_name] = math.dist(observed, expected)
            d56_ok &= errors[pixel_name] <= 0.20
        d56_rows.append((observation, errors))
    d56_ok &= (
        len(d56["package_identity"]["component_observations"]) >= 3
        and "tubing" in d56["drawing"]["observation"]
        and "not promoted" in d56["remaining_boundary"]
    )
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
    d14_aux_points = [
        image_to_board(
            observation["image"],
            observation["image_px"],
            "component_grid",
            panorama,
            board_registration,
        )
        for observation in d14["auxiliary_fifth_landing"]["component_observations"]
    ]
    d14_aux_centre = tuple(
        sum(point[axis] for point in d14_aux_points) / len(d14_aux_points)
        for axis in range(2)
    )
    d14_aux_spread = max(math.dist(d14_aux_centre, point) for point in d14_aux_points)
    d14_ok &= d14_aux_spread <= 0.15
    d14_solder_images = [ROOT / image for image in d14["solder_exclusion"]["images"]]
    d14_ok &= all(path.exists() and path.stat().st_size > 1_000_000 for path in d14_solder_images)

    d11 = modification["d11"]
    d11_rows = []
    d11_ok = True
    for name, landing in d11["landings"].items():
        points = [
            image_to_board(
                observation["image"],
                observation["image_px"],
                "component_grid",
                panorama,
                board_registration,
            )
            for observation in landing["component_observations"]
        ]
        centre = tuple(
            sum(point[axis] for point in points) / len(points) for axis in range(2)
        )
        spread = max(math.dist(centre, point) for point in points)
        d11_ok &= spread <= 0.15
        d11_rows.append((name, centre, spread))
    d11_pin4_6 = [(177.88, 56.81), (177.88, 59.35), (177.88, 61.89)]
    d11_scar_separation = min(
        math.dist(centre, pin_point)
        for _, centre, _ in d11_rows
        for pin_point in d11_pin4_6
    )
    component_fit_ceiling = (
        board_registration["groups"]["component_grid"]["max_held_out_error_px"]
        / board_registration["pixels_per_mm"]
    )
    d11_ok &= d11_scar_separation > 2 * component_fit_ceiling
    d11_fits = {
        item["side"]: item
        for item in local_packages["fits"]
        if item["refdes"] == "D11"
    }
    d11_ok &= set(d11_fits) == {"component", "solder"}
    d11_ok &= d11_fits.get("component", {}).get("model") == "similarity"
    d11_ok &= d11_fits.get("solder", {}).get("model") == "similarity_reflected"
    d11_ok &= all(
        check["error_px"] <= 8.0
        for fit in d11_fits.values()
        for check in fit["checks"]
        if check["use"] == "check"
    )
    d11_projected = d11["solder_photo_exhaustion"]["projected_points_px"]
    if set(d11_fits) == {"component", "solder"}:
        for name, landing in d11["landings"].items():
            calculated = reflected_cross_side(
                d11_fits["component"],
                d11_fits["solder"],
                landing["component_observations"][0]["image_px"],
            )
            d11_ok &= math.dist(calculated, d11_projected[name]) <= 0.15
    d11_solder_images = [
        ROOT / image for image in d11["solder_photo_exhaustion"]["overlap_images"]
    ]
    d11_ok &= len(d11_solder_images) == 4
    d11_ok &= all(path.exists() and path.stat().st_size > 1_000_000 for path in d11_solder_images)

    guard_ok = (
        all(ref in chips for ref in AFFECTED)
        and all(path.exists() and path.stat().st_size > 1_000_000 for path in detail_photos)
        and MOD_REGISTRATION.exists()
        and all(ref in bodge for ref in AFFECTED)
        and "Factory solder-side cuts and patches" in bodge
        and d56_ok
        and d15_ok
        and d14_ok
        and d11_ok
    )
    status = "FACTORY MODIFICATIONS GUARDED / PAD MAPPING REQUIRED" if guard_ok else "FACTORY MODIFICATION GUARD FAILED"

    lines = [
        "# Factory modification disposition",
        "",
        "Status date: **2026-07-16**.",
        "",
        f"Status: **{status}**",
        "",
        "The `ДГШ5.109.009 СБ` Вид В detail marks local assembly work around",
        "D56, D15, D14, and D11. Assembly note 11 explicitly identifies position",
        "150 as tubing fitted at solder locations; position 159 is therefore kept",
        "as an unexpanded solder-location callout because its specification row",
        "was not photographed. Only the D15 detail explicitly says `Разрезать`.",
        "Three component views plus two overlapping solder views register D56's",
        "callout row; independent evidence closes the D15 cut topology and the",
        "local D14 ground link. D56 electrical endpoints, D11 bridge endpoints,",
        "and the remaining D14 auxiliary paths stay held.",
        "",
        "| Ref | Factory operation locality | Current disposition | Closure evidence |",
        "| --- | --- | --- | --- |",
    ]
    for ref, detail in AFFECTED.items():
        disposition = "GEOMETRY REGISTERED / ELECTRICAL HOLD — the callout row is fixed at D56.12/D56.5; no cut or merge is inferred"
        closure = "three component views identify the package; two overlapping solder views fix the reflected pin field; note 11 identifies position 150 as tubing"
        if ref == "D15":
            disposition = "PHOTO-CLOSED — cut separates the auxiliary D15.8/A2 and D15.9/A1 landings; the clean source net partition matches"
            closure = "two independent component views, reflected solder confirmation, and guarded source pin nets; original auxiliary-hole drill placement remains fabrication-held"
        elif ref == "D14":
            disposition = "PARTIAL PHOTO-CLOSE — local copper preserves D32.4/GND-to-D14.1 and the fifth landing is registered; its conductor and remaining drawn traces are held"
            closure = "two independent component views plus notch-oriented factory row registration; map the fifth landing conductor, three long traces, and right-row dogleg before full release"
        elif ref == "D11":
            disposition = "GEOMETRY REGISTERED / ELECTRICAL HOLD — four position-159 solder locations identified; bridge and remote trace endpoints remain obscured"
            closure = "two component views register the L trace and four-landmark topology; validated two-sided package fits exhaust four solder views, so direct continuity is required to assign any D11 pin/net"
        lines.append(row([
            ref,
            detail,
            disposition,
            closure,
        ]))
    lines += [
        "",
        "## D56 callout-field registration",
        "",
        "Three overlapping component photographs identify the same notch-down",
        "`К155АГ3 8901` package beside the right board edge. The coherent reflected",
        "16-pin solder field fixes the drawing's three-leader level at the",
        "D56.12/D56.5 row. Assembly note 11 says tubing positions 157 and 150",
        "are fitted at solder locations. Position 150 is therefore not a cut",
        "instruction, and the nearby visible wide-rail gap cannot be promoted as",
        "proof of the D56.12 net partition. Position 159 remains an unexpanded",
        "solder-location callout until its specification identity is recovered.",
        "",
        "| Solder view | D56.12 fit error | D56.5 fit error | Result |",
        "| --- | ---: | ---: | --- |",
    ]
    for observation, errors in d56_rows:
        lines.append(row([
            Path(observation["image"]).name,
            f"{errors['d56_12_px']:.3f} mm",
            f"{errors['d56_5_px']:.3f} mm",
            "registered three-callout package level",
        ]))
    lines += [
        "",
        "The separate left landing, the nearby rail stub, and every conductor at",
        "this level remain electrically and fabrication-held. Direct continuity",
        "or the complete position-159 specification is required before changing",
        "the clean source net partition.",
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
        "The open fifth left-field annulus below D14.4 is also reproducible in",
        "both component views.",
        "",
        "| Landing | Provisional board centre (mm) | Component-view agreement | Disposition |",
        "| --- | --- | ---: | --- |",
        row([
            "fifth auxiliary landing",
            f"({d14_aux_centre[0]:.3f}, {d14_aux_centre[1]:.3f})",
            f"{d14_aux_spread:.3f} mm",
            "geometry registered; conductor and fabrication drill held",
        ]),
        "",
        "The landing's conductor, the three long drawn traces, and the right-row",
        "dogleg are not electrically closed by these views. Reflected registration",
        "into `200506061` and `200509593` places the same locality inside a heavily",
        "scraped/reworked two-row solder field; the component face hides the immediate",
        "dogleg under the package body. The available photographs are therefore",
        "exhausted for D14.7 rather than evidence for a guessed path. D14.2 and D14.7",
        "require direct continuity, and no remote net or fabrication geometry is",
        "inferred from the drawing alone.",
        "",
        "## D11 position-159 field registration",
        "",
        "The component photographs correct the earlier interpretation of the",
        "factory detail. Its long hole column and unique L-shaped trace are the",
        "auxiliary drilled/copper field beside D11, not a drawn 14-pad package",
        "column. The four-landmark subfield is reproducible in two independent",
        "component views: a long vertical trace joins the upper landing to the",
        "position-159 junction, a left landing approaches that junction through",
        "the obscured bridge, and a lower landing departs on a separate trace.",
        "",
        "| Landing | Provisional board centre (mm) | Component-view agreement | Disposition |",
        "| --- | --- | ---: | --- |",
    ]
    for name, centre, spread in d11_rows:
        lines.append(row([
            name,
            f"({centre[0]:.3f}, {centre[1]:.3f})",
            f"{spread:.3f} mm",
            "registered topology; fabrication drill held",
        ]))
    lines += [
        "",
        "These board centres use the panorama's coarse component-grid fit and are",
        "topology locators, not pin- or fabrication-grade coordinates. In",
        "particular, the validated D11 solder overlay localizes a conspicuous scar",
        "beside pins 4 through 6, but cross-registration shows that scar is a",
        "different feature and cannot identify the factory position-159 bridge.",
        f"The nearest provisional field centre is {d11_scar_separation:.3f} mm",
        f"from the nominal D11.4-.6 column, more than twice the component-grid",
        f"held-out error ceiling ({component_fit_ceiling:.3f} mm); the exclusion",
        "therefore survives the coarse global-fit uncertainty.",
        "A newly validated D11 component package fit now pairs with that reflected",
        "solder fit. Their package-local transform projects the upper landing under",
        "the wide tinned rail and the lower three landmarks among repeated joints",
        "and parallel traces without a unique four-hole match. All four overlapping",
        "solder photos repeat the lower-field ambiguity; the second complete view",
        "also repeats the upper rail obstruction. The available photographs are",
        "therefore exhausted for through-hole identity rather than evidence for a",
        "guessed snap. D11 pin/net and both remote endpoints require direct",
        "continuity, and no source net or auxiliary drill is changed.",
    ]
    lines += [
        "",
        "## Guarded evidence",
        "",
        "- `PXL_20260711_114626340.jpg`: full Вид В and all four local details.",
        "- `PXL_20260711_114633498.jpg`: enlarged D15 Разрезать operation.",
        "- `PXL_20260711_114638730.MP.jpg`: full-resolution positions 150/159 context.",
        "- `PXL_20260711_114649169.jpg`: assembly note 11 identifies position 150 as tubing at solder locations.",
        "- `factory-modification-registration.json`: D56 field registration, D15/D14 closures, and two-view D11 registration.",
        "- `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`: factory-versus-owner disposition.",
        "",
        "## Release rule",
        "",
        "Do not release or reroute the board on netlist equivalence alone. For each",
        "of the D56 three-callout field, the obscured D11 bridge, and the remaining",
        "D14 detail, identify the pad/via pair(s) and conductor topology; then",
        "prove the final source-PCB net partition matches the factory result.",
        "D15 and the D14.1 ground link are electrically closed; their unmeasured",
        "auxiliary-hole geometry remains",
        "held only for an original-artwork replica.",
        "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if guard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
