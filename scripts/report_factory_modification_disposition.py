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
D14_CROSS_FACE = ROOT / "ref/photos/juku-pcb-2/d14-cross-face-contact-fit.json"
PANORAMA_REGISTRATION = ROOT / "docs/photo-registration/panorama-registration.json"
BOARD_REGISTRATION = ROOT / "docs/photo-registration/board-registration.json"
LOCAL_PACKAGE_REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
AFFECTED = {
    "D56": "АГ3 timing area: corrected marked-package component fit cross-checks the independently registered solder pads; D56.1/D56.9 are photo-closed to ground and D56.5/D56.12 functional nets are owner-closed; position-159 material remains held",
    "D15": "EPROM area: Разрезать cuts the auxiliary A2/A1 bridge between the D15.8- and D15.9-side landings; no replacement wire is drawn in the D15 detail",
    "D14": "АП2 serial-driver area: registered notch-up orientation maps both package rows; local copper closes D32.4/GND-to-D14.1 and D14.4-to-fifth auxiliary annulus, while the latter's remote conductor and remaining traces stay held",
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
    d14_cross_face = json.loads(D14_CROSS_FACE.read_text(encoding="utf-8"))
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
    d56_fits = {
        item["side"]: item
        for item in local_packages["fits"]
        if item["refdes"] == "D56"
    }
    d56_ok = True
    d56_ok &= set(d56_fits) == {"component", "solder"}
    d56_ok &= d56_fits.get("component", {}).get("model") == "affine"
    d56_ok &= d56_fits.get("solder", {}).get("model") == "similarity_reflected"
    d56_ok &= all(
        check["error_px"] <= 8.0
        for fit in d56_fits.values()
        for check in fit["checks"]
        if check["use"] == "check"
    )
    if set(d56_fits) == {"component", "solder"}:
        corrected_corners = {
            "1": ((3415, 1380), (807, 536)),
            "8": ((3415, 940), (807, 89)),
            "9": ((3215, 940), (990, 89)),
            "16": ((3215, 1380), (990, 536)),
        }
        d56_ok &= all(
            math.dist(d56_fits["component"]["projected_pins"][pin], component) <= 8
            and math.dist(d56_fits["solder"]["projected_pins"][pin], solder) <= 8
            for pin, (component, solder) in corrected_corners.items()
        )
    d56_observations = d56["callout_field"]["solder_observations"]
    d56_ok &= len(d56_observations) == 2
    d56_rows = []
    if set(d56_fits) == {"component", "solder"} and len(d56_observations) == 2:
        primary, overlap = d56_observations
        primary_errors = {
            "left_landing_px": 0.0,
            "d56_5_px": math.dist(
                primary["d56_5_px"], d56_fits["solder"]["projected_pins"]["5"]
            ),
            "d56_12_px": math.dist(
                primary["d56_12_px"], d56_fits["solder"]["projected_pins"]["12"]
            ),
        }
        d56_ok &= max(primary_errors.values()) <= 0.15
        primary_to_panorama = matrix(
            panorama["groups"]["solder_grid"]["images"][primary["image"]][
                "original_to_panorama_homography"
            ]
        )
        overlap_to_panorama = matrix(
            panorama["groups"]["solder_grid"]["images"][overlap["image"]][
                "original_to_panorama_homography"
            ]
        )
        primary_to_overlap = multiply(
            inverse3(overlap_to_panorama), primary_to_panorama
        )
        overlap_errors = {
            name: math.dist(project(primary_to_overlap, primary[name]), overlap[name])
            for name in ("left_landing_px", "d56_5_px", "d56_12_px")
        }
        d56_ok &= max(overlap_errors.values()) <= 20.0
        d56_rows = [(primary, primary_errors), (overlap, overlap_errors)]
    d56_ground = d56["trigger_ground_rail"]
    d56_ground_observations = d56_ground["solder_observations"]
    d56_ground_rows = []
    d56_ok &= d56_ground.get("review_state") == "accepted"
    d56_ok &= (
        d56_ground["source_net"] == "GND"
        and d56_ground["package_ground_pin"] == "8"
        and set(d56_ground["trigger_pins"]) == {"1", "9"}
        and len(d56_ground_observations) == 2
    )
    if set(d56_fits) == {"component", "solder"} and len(d56_ground_observations) == 2:
        primary_ground, overlap_ground = d56_ground_observations
        primary_ground_errors = {
            pin: math.dist(
                primary_ground[f"d56_{pin}_px"],
                d56_fits["solder"]["projected_pins"][pin],
            )
            for pin in ("1", "8", "9")
        }
        d56_ok &= max(primary_ground_errors.values()) <= 8.0
        primary_to_panorama = matrix(
            panorama["groups"]["solder_grid"]["images"][primary_ground["image"]][
                "original_to_panorama_homography"
            ]
        )
        overlap_to_panorama = matrix(
            panorama["groups"]["solder_grid"]["images"][overlap_ground["image"]][
                "original_to_panorama_homography"
            ]
        )
        primary_to_overlap = multiply(inverse3(overlap_to_panorama), primary_to_panorama)
        overlap_ground_errors = {
            pin: math.dist(
                project(primary_to_overlap, primary_ground[f"d56_{pin}_px"]),
                overlap_ground[f"d56_{pin}_px"],
            )
            for pin in ("1", "8", "9")
        }
        d56_ok &= max(overlap_ground_errors.values()) <= 0.01
        d56_ground_rows = [
            (primary_ground, primary_ground_errors),
            (overlap_ground, overlap_ground_errors),
        ]
    gnd_nodes = {tuple(node) for node in nets["GND"]["nodes"]}
    d56_ok &= {("D56", "1"), ("D56", "8"), ("D56", "9")} <= gnd_nodes
    d56_ok &= all(["D56", pin] not in board.get("no_connects", []) for pin in ("1", "9"))
    d56_ok &= ["D56", "13"] in board.get("no_connects", [])
    d56_ok &= {tuple(node) for node in nets["D56_Q2_D34"]["nodes"]} == {
        ("D56", "5"), ("D34", "9")
    }
    d56_ok &= {tuple(node) for node in nets["D56_Q2N_TAG16"]["nodes"]} == {
        ("D56", "12"), ("D55", "15"), ("D55", "18")
    }
    d56_ok &= (
        len(d56["package_identity"]["component_observations"]) >= 3
        and "tubing" in d56["drawing"]["observation"]
        and "no callout-row gap is promoted" in d56["remaining_boundary"]
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
    d14_ok &= {("D32", "4"), ("D14", "1"), ("D14", "4"), ("D29", "10")} <= gnd_nodes
    d14_ground_pin = d14_cross_face["fifth_auxiliary_landing"]["overlap_registration"]["registered_ground_pin"]
    d14_ok &= (d14_ground_pin["refdes"], d14_ground_pin["pin"]) == ("D29", "10")
    d14_ok &= d14_ground_pin["source_net"] == "GND"
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
        f"Status: **{status}**",
        "",
        "The `ДГШ5.109.009 СБ` Вид В detail marks local assembly work around",
        "D56, D15, D14, and D11. Assembly note 11 explicitly identifies position",
        "150 as tubing fitted at solder locations; position 159 is therefore kept",
        "as an unexpanded solder-location callout because its specification row",
        "was not photographed. Only the D15 detail explicitly says `Разрезать`.",
        "Three component views plus two overlapping solder views register D56's",
        "callout row. The same two solder views independently close D56.1 and",
        "D56.9 onto its pin-8 ground perimeter. Exact-revision `.009 E3` sheet 2",
        "plus owner continuity close D56.5->D34.9 and D56.12->D55.15/.18; these",
        "functional-net closures are separate from the still-held position-159 material",
        "and auxiliary-annulus disposition. Independent evidence also closes",
        "the D15 cut topology and local D14 ground link. D11 bridge endpoints and",
        "the remaining D14 auxiliary paths stay held.",
        "",
        "## Command and guard scope",
        "",
        "```sh",
        "python3 scripts/report_factory_modification_disposition.py",
        "```",
        "",
        "The generator checks selected board nodes, stored registration metadata,",
        "fit residuals, and cross-view projections. Photo checks use existence and",
        "file size, not image hashes. The reported copper and material observations",
        "come from retained reviews; generation does not reread pixels, repeat",
        "continuity measurements, validate drilled auxiliary holes, or run PCB DRC.",
        "",
        "## Disposition",
        "",
        "| Ref | Factory operation locality | Current disposition | Closure evidence |",
        "| --- | --- | --- | --- |",
    ]
    for ref, detail in AFFECTED.items():
        disposition = "PARTIAL OWNER-CLOSE — corrected D56 component fit retains D56.1/D56.9 ground and D56.5/D56.12 functional nets; item-159 material remains held"
        closure = "four marked-AG3 component corners cross-align with the solder package; two solder views show uninterrupted ground copper through pins 1/8/9; exact .009 E3 plus owner continuity close D56.5->D34.9 and D56.12->D55.15/.18"
        if ref == "D15":
            disposition = "PHOTO-CLOSED — cut separates the auxiliary D15.8/A2 and D15.9/A1 landings; the clean source net partition matches"
            closure = "two independent component views, reflected solder confirmation, and guarded source pin nets; original auxiliary-hole drill placement remains fabrication-held"
        elif ref == "D14":
            disposition = "PARTIAL PHOTO-CLOSE — local copper preserves D32.4/GND-to-D14.1 and D14.4-to-fifth annulus; remote conductor and remaining drawn traces are held"
            closure = "two independent component views plus notch-oriented factory row registration; map the fifth landing's opposite face and remote conductor, three long traces, and right-row dogleg before full release"
        elif ref == "D11":
            disposition = "GEOMETRY REGISTERED / ELECTRICAL HOLD — four position-159 solder locations identified; bridge and remote trace endpoints remain obscured"
            closure = "two component views register the L trace and four-landmark topology; corrected D11 solder registration shifts the projected field, and review of two complete plus two partial solder views finds no unique four-hole match; direct continuity is required"
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
        "`К155АГ3 8901` package beside the right board edge. Held-out-validated",
        "component and reflected local-package fits replace the displaced global",
        "endpoint seeds.",
        "The corrected component fit sits on the marked AG3 at x3215..3415;",
        "the former x2865..3050 component anchors were on neighboring D103.",
        "All four outer AG3 contacts align with the independent solder columns",
        "x807/990 and rows y89/536; see `d56-fit-correction.json`.",
        "The drawing's three leaders register as the separate left annulus,",
        "D56.5, and D56.12 at one physical level. Assembly note 11 says",
        "tubing positions 157 and 150 are fitted at solder locations. Position 150",
        "is therefore not a cut",
        "instruction, and the nearby visible wide-rail gap cannot be promoted as",
        "proof of the D56.12 net partition. Exact-revision `.009 E3` sheet 2 and",
        "owner continuity on 2026-07-21 independently close D56.5 to D34.9 and",
        "D56.12 to tied D55.15/.18. Position 159 remains an unexpanded",
        "solder-location/material callout until its specification identity is recovered.",
        "This callout hold is independent of the package trigger inputs: both",
        "overlapping solder views show D56.1 and D56.9 on the same uninterrupted",
        "wide perimeter conductor as ground pin D56.8, so the source model now",
        "grounds both active-low A inputs.",
        "",
        "| Solder view | Left-landing error | D56.5 error | D56.12 error | Result |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for observation, errors in d56_rows:
        lines.append(row([
            Path(observation["image"]).name,
            f"{errors['left_landing_px']:.3f} px",
            f"{errors['d56_5_px']:.3f} px",
            f"{errors['d56_12_px']:.3f} px",
            "package-local reference" if errors["left_landing_px"] == 0 else "independent overlap",
        ]))
    lines += [
        "",
        "Both solder views show small bare-board gaps between the D56.5/D56.12",
        "pads and the adjacent horizontal rail; the separate left annulus belongs",
        "to that rail. This closes the three-location geometry, not the installed",
        "assembly material. The package-pad functional nets are now continuity-closed;",
        "the complete position-159 specification or direct auxiliary-annulus probing is",
        "still required before changing that separate assembly disposition.",
        "",
        "| Ground-rail view | D56.1 registration error | D56.8 registration error | D56.9 registration error | Result |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for observation, errors in d56_ground_rows:
        lines.append(row([
            Path(observation["image"]).name,
            f"{errors['1']:.3f} px",
            f"{errors['8']:.3f} px",
            f"{errors['9']:.3f} px",
            "accepted uninterrupted GND perimeter",
        ]))
    lines += [
        "",
        "The primary view exposes the complete upper rail and left-edge return;",
        "the overlap independently repeats both pin levels. D56.1 and D56.9 are",
        "therefore closed to `GND` with D56.8 without inferring any position-159",
        "conductor or changing the D56.5/D56.12 callout-row partition.",
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
        "The fit coordinates below are witnesses on that strip beside the",
        "landings, not the physical D32.4 or D14.1 lead centres. Their small",
        "errors check the strip's local scale; they do not measure pin placement.",
        "",
        "| Component view | Upper witness fit error | Lower witness fit error | Witness-span error | Result |",
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
        "The open fifth left-field annulus below D14.4 is reproducible in",
        "both component views at corrected native coordinates. Its visible short",
        "front-copper stem joins the bottom left-row contact, D14.4. The",
        "exact `.009` sheet-1 IC power table assigns D14.4 to `GND`, so the",
        "annulus is a source-ground candidate; owner rail continuity is unmeasured.",
        "",
        "| Landing | Provisional board centre (mm) | Component-view agreement | Disposition |",
        "| --- | --- | ---: | --- |",
        row([
            "fifth auxiliary landing",
            f"({d14_aux_centre[0]:.3f}, {d14_aux_centre[1]:.3f})",
            f"{d14_aux_spread:.3f} mm",
            "D14.4 local stem, fifth same-hole, and strip to D29.10 photo-registered; owner continuity held",
        ]),
        "",
        "A D11-local cross-face fit puts all eight D14 contacts on the visible",
        "2×4 solder field in `200506061`: D14.2 near `(2426,1376)` and D14.7",
        "near `(2288,1376)`. It also maps the fifth component hole to the",
        "distinct solder drill near `(2424,1513)`. The older broad projection",
        "near `(2050,1565)` and geometry-only pin seeds near `(2279,1708)`/",
        "`(2141,1711)` are retired. See `d14-cross-face-contact-fit.json`.",
        "On that solder face, a bare-board gap separates the long tinned strip",
        "holding the fifth drill from D14.4's solder cap. Their observed local",
        "join is the component-face stem. The strip runs west to an exposed",
        "drilled terminal near `(2074,1521)` in the same native photo, a second",
        "probe site for its visible copper. Four native patch matches register",
        "that terminal near `(241,1656)` and the fifth drill near `(604,1644)`",
        "in overlapping `200509593`. There the strip has an uninterrupted",
        "neck to registered D29.10 near `(2057,1588)`, named `GND` by the",
        "exact sheet-1 power table. This closes a visible photo path from the",
        "fifth hole to a source-ground pin, not owner electrical continuity.",
        "Any other fifth-landing conductor, three long drawn traces, and",
        "right-row dogleg remain open. Confirm the same-hole pairs and meter",
        "D14.2 and D14.7 to remote endpoints before assigning nets. Their",
        "local solder caps have no readable back-face departures; adjacent",
        "east-west traces pass with visible gaps and cannot name those pins.",
        "",
        "## D11 position-159 field registration",
        "",
        "The component photographs correct the earlier interpretation of the",
        "factory detail. Its long hole column and unique L-shaped trace are the",
        "auxiliary drilled/copper field beside D11, not a drawn 14-pad package",
        "column. The four-landmark subfield is reproducible in two independent",
        "component views: a long vertical trace joins the upper landing to the",
        "position-159 junction, the drawing joins a left landing horizontally,",
        "and a lower landing departs on a separate trace. Native owner crops show",
        "bare substrate across the local left-to-junction front gap in both",
        "views, so that drawn bridge is not visible F.Cu there; B.Cu or a fitted",
        "conductor remains possible pending continuity. The earlier May owner",
        "photo `201922448` independently shows the same bare front gap. In",
        "`200506061`, the",
        "D11-local solder projections of bridge_left and position159_junction",
        "fall near two separate annuli with matching pair geometry, but no local",
        "B.Cu strip joins those annuli. The cross-face hole identities and any",
        "remote or fitted connection still require direct verification.",
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
        "particular, D27 and D11 two-face landmarks expose a four-joint error in",
        "the old D11 solder registration. The corrected 14-row D11 field starts",
        "near y=1610 rather than y=1425 in owner tile 200506061. The conspicuous",
        "scar is beside its upper rows and is not the factory position-159 bridge.",
        "The undimensioned `.009` detail draws lower_exit as an annulus on a",
        "separate downward trace below the position-159 junction, matching the",
        "corrected front-side topology rather than the retired bare-board point.",
        "The lower_exit front coordinate was corrected to its drilled annulus",
        "in both views, shifting its D11-local solder projection to about",
        "`(2771,2078)` in `200506061`. An open hole near `(2776,2094)` maps",
        "through the solder-tile overlap to `(973,2237)` and is observed near",
        "`(978,2234)` in `200509593`. The two solder views identify the same",
        "hole to about 6 px; its ≈17 px D11-local projection offset and missing",
        "front-to-solder shared-hole",
        "calibration leave it a candidate, not a same-hole match. The upper",
        "projection sits beside an isolated open via, and bridge/junction lie",
        "among several vias without a unique four-hole pattern. Two more partial",
        "views place the upper projection near their",
        "top boundaries and show no unique lower four-hole match. All four listed",
        "views have now been checked against shifted projections. The old upper-rail",
        "claim is retracted. D11 pin/net and both remote endpoints remain on",
        "hold for direct continuity; no source net or auxiliary drill is changed.",
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
    if d56_ground.get("review_state") == "rejected":
        start = lines.index("## D56 callout-field registration")
        end = lines.index("## D15 cut registration")
        lines[start:end] = [
            "## D56 callout-field registration",
            "",
            "The corrected owner component fit now lands on the marked К155АГ3",
            "at x3215..3415, rather than adjacent D103 К555ИЕ10 at the former",
            "x2865..3050 anchors. The old solder fit, D56.1/D56.9 ground",
            "promotion, and D56.5/D56.12 photo landing identities are withdrawn.",
            "Exact .009 sheet 2 and direct owner continuity still establish the",
            "D56.5/D34.9 and D56.12/D55.15/D55.18 functional nets. Register the",
            "actual D56 solder footprint before interpreting the position-159",
            "landings. Position 150 remains drawing-proved tubing.",
            "See `ref/photos/juku-pcb-2/d56-fit-correction.json`.",
            "",
        ]
        preface = lines.index("The `ДГШ5.109.009 СБ` Вид В detail marks local assembly work around")
        table = lines.index("| Ref | Factory operation locality | Current disposition | Closure evidence |")
        lines[preface:table] = [
            "The `ДГШ5.109.009 СБ` Вид В detail marks local assembly work around",
            "D56, D15, D14, and D11. The corrected marked-package D56 fit",
            "invalidates its former solder and trigger-ground photo promotions.",
            "Exact-sheet and owner-continuity D56 functional nets remain closed.",
            "D15's cut and D14's local ground link remain photo-closed; D11's",
            "bridge endpoints and the remaining D14 paths stay held.",
            "",
        ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Status: {status}")
    return 0 if guard_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
