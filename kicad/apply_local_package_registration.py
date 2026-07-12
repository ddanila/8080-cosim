#!/usr/bin/env python3
"""Apply validated local package coordinates to measurement observations.

Review state is deliberately preserved.  A local fit proves pad identity in a
photo, not where its copper terminates.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENDPOINTS = ROOT / "ref/photos/juku-pcb-2/endpoints.csv"
REPORT = ROOT / "docs/photo-registration/local-packages/report.json"
FIELDS = ("endpoint_id", "image", "x_px", "y_px", "refdes", "pin",
          "candidate_net", "confidence", "review_state", "reviewer", "note")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--side", choices=("component", "solder", "both"), default="both",
                        help="apply one validated side or require both (default: both)")
    parser.add_argument("refdes", nargs="+", help="references whose validated fits should be applied")
    args = parser.parse_args(); requested = set(args.refdes)
    sides = ("component", "solder") if args.side == "both" else (args.side,)
    report = json.loads(REPORT.read_text())
    fits = {(item["refdes"], item["side"]): item for item in report["fits"]
            if item["refdes"] in requested}
    missing = [ref for ref in requested
               if not all((ref, side) in fits for side in sides)]
    if missing:
        raise SystemExit(f"missing two-sided validated fits for {', '.join(sorted(missing))}")
    with ENDPOINTS.open(newline="") as source:
        rows = list(csv.DictReader(source))
    changed = 0
    for row in rows:
        if row["refdes"] not in requested or not row["endpoint_id"].startswith("seed-"):
            continue
        side = "component" if row["endpoint_id"].startswith("seed-component-") else "solder"
        if side not in sides:
            continue
        fit = fits[(row["refdes"], side)]
        if row["image"] != fit["image"]:
            replaceable_seed = (
                row["review_state"] == "candidate"
                or (
                    row["review_state"] == "measurement"
                    and row["confidence"].startswith("registration")
                )
            )
            if not replaceable_seed:
                raise SystemExit(f"{row['endpoint_id']}: fit image differs from reviewed observation image")
            # Newly seeded candidates and explicitly rejected registration-only
            # measurements may select a different overlapping tile. A validated
            # package-local fit is the stronger pad-identity record; accepted or
            # genuinely reviewed electrical observations are never moved.
            row["image"] = fit["image"]
        point = fit["projected_pins"].get(row["pin"])
        if point is None:
            raise SystemExit(f"{row['endpoint_id']}: pin absent from local fit")
        row["x_px"], row["y_px"] = f"{point[0]:.3f}", f"{point[1]:.3f}"
        row["confidence"] = "local-package-fit"
        stale = ("Board-level solder projection is registration-only among the dense "
                 "USART/bus fanout; a local fit or continuity measurement is required "
                 "before assigning a destination or NC state")
        replacement = ("Package-local solder fit corrects the displaced board-level "
                       "projection and identifies this physical pad; continuity is still "
                       "required before assigning a destination or NC state")
        row["note"] = row["note"].replace(stale, replacement)
        stale_d28 = ("Generated D28 landings do not follow the photographed vertical package: "
                     "pins 1-6 fall left of its contacts and pins 8-13 fall on the body; "
                     "local package registration is required")
        corrected_d28 = ("Validated D28 component fit replaces the displaced generated landing "
                         "and identifies the photographed package contact")
        row["note"] = row["note"].replace(stale_d28, corrected_d28)
        stale_d28_solder = ("Without a valid D28 package fit, nearby solder holes and trace "
                            "junctions cannot be assigned to a pin or destination safely")
        corrected_d28_solder = ("Validated reflected D28 fit identifies the photographed solder "
                                "joint, distinct from the adjacent open vias; the visible local "
                                "copper does not reach an identified remote package pad")
        row["note"] = row["note"].replace(stale_d28_solder, corrected_d28_solder)
        stale_d106 = ("D106 projections land on the package body or neighboring trace/via field "
                      "instead of a coherent pin row, so the physical posture is unresolved")
        corrected_d106 = ("Validated D106 component fit identifies the photographed К555ИЕ7 "
                          "package contact and replaces the displaced generated landing")
        row["note"] = row["note"].replace(stale_d106, corrected_d106)
        stale_d95 = ("D95 package-side crops show only local contacts/fanout, with pins 1-2 "
                     "resistor-obscured and opposite-row projections offset; no unresolved pin "
                     "reaches a unique destination")
        corrected_d95 = ("Validated D95 component fit corrects the reversed/offset projection "
                         "and identifies the photographed К555КП12 package contact")
        row["note"] = row["note"].replace(stale_d95, corrected_d95)
        stale_d95_solder = ("D95 solder projections lie on intervening trace rails rather than "
                            "the photographed package-pad rows; local two-side registration is "
                            "required")
        corrected_d95_solder = ("Validated reflected D95 fit identifies the physical solder "
                                "joint in the left eight-pad package group and rejects the "
                                "former projection spanning the adjacent package")
        row["note"] = row["note"].replace(stale_d95_solder, corrected_d95_solder)
        stale_d96_solder = ("D96 solder projections fall between the physical pad rows at trace "
                            "junctions and holes; none proves a pin-to-destination path without "
                            "local registration")
        corrected_d96_solder = ("Validated reflected D96 fit identifies the physical solder "
                                "joint, distinct from the adjacent open vias")
        row["note"] = row["note"].replace(stale_d96_solder, corrected_d96_solder)
        stale_d101 = ("D101 projections fall on factory-wire bundles and bare trace fields "
                      "rather than a coherent package contact row; the modeled placement is "
                      "not locally registered")
        corrected_d101 = ("Validated D101 component fit identifies the distinct 8812-marked "
                          "К555КП12 package contact and replaces the displaced projection")
        row["note"] = row["note"].replace(stale_d101, corrected_d101)
        stale_d97 = ("D97 generated landings cross resistor, body, and parallel-trace areas "
                     "instead of following a coherent package row; pin identity and "
                     "destinations are not locally reliable")
        corrected_d97 = ("Validated D97 component fit identifies the first К155АГ3 right "
                         "of D101 and replaces the displaced generated landing")
        row["note"] = row["note"].replace(stale_d97, corrected_d97)
        stale_d102 = ("D102 projections alternate between adjacent package bodies, contacts, "
                      "and bare fanout, demonstrating an unreliable local package fit with no "
                      "complete destination")
        corrected_d102 = ("Validated D102 component fit identifies the cable-partly-obscured "
                          "К155АГ3 package right of D97 and replaces the displaced projection")
        row["note"] = row["note"].replace(stale_d102, corrected_d102)
        stale_d99 = ("D99 component landings are crossed by a factory wire or offset from "
                     "package contacts, and none exposes a unique complete fanout")
        corrected_d99 = ("Validated D99 component fit identifies the cable-crossed notch-right "
                         "К155АГ3 package beside D95 and replaces the displaced projection")
        row["note"] = row["note"].replace(stale_d99, corrected_d99)
        if row["refdes"] == "D93" and side == "component":
            if row["pin"] == "40":
                row["note"] = (
                    "FD179X-01 defines D93.40 as the +12 V VDD supply; the corrected "
                    "exposed-socket fit identifies the spring contact, while P12V "
                    "continuity remains unproved"
                )
            row["note"] = row["note"].replace(
                "identifies MR_N/pin19 on the exposed socket and shows its "
                "component-side departure; the trace leaves the close-up without a "
                "proved source, so reset continuity remains a measurement item",
                "identifies the MR_N/pin19 spring contact; the socket body obscures "
                "its component-side departure, so only the separate solder fit can "
                "seed a reset-continuity chase",
            )
            row["note"] = row["note"].replace(
                "identifies CLK/pin24 on the exposed socket and shows its "
                "component-side fanout through the socket window; the far clock "
                "source remains outside proved continuity",
                "identifies the CLK/pin24 spring contact; the socket body obscures "
                "its component-side departure, and the separate solder fit still "
                "does not prove the far clock source",
            )
            row["note"] = row["note"].replace(
                "identifies this drive-interface pin on the exposed ВГ93 socket; "
                "visible local fanout does not prove its complete target-board "
                "destination or intentional NC state",
                "identifies this drive-interface spring contact on the exposed "
                "КР1818ВГ93 socket; the socket body obscures component-side copper, "
                "so the target-board destination or intentional NC state remains "
                "unproved",
            )
        if row["refdes"] == "D93" and side == "solder" and row["review_state"] != "accepted":
            if row["pin"] == "19":
                row["note"] = (
                    "Corrected two-column D93 orientation identifies MR_N/pin19 "
                    "on the physical D94-side solder column; its far reset source "
                    "remains unproved"
                )
            elif row["pin"] == "24":
                row["note"] = (
                    "Corrected two-column D93 orientation identifies CLK/pin24 on "
                    "the opposite solder column and exposes a westbound local trace; "
                    "the far 1 MHz source remains unproved"
                )
            elif row["pin"] == "40":
                row["note"] = (
                    "Corrected two-column D93 orientation identifies VDD_12V/pin40 "
                    "on the opposite top solder joint; the former westbound +12 V "
                    "photo chase started from a falsely projected pad and is withdrawn"
                )
        rail_obscured_d106 = (
            row["refdes"] == "D106"
            and side == "solder"
            and row["pin"] in {"7", "8", "9", "10"}
        )
        visible_d106_joint = (
            row["refdes"] == "D106"
            and side == "solder"
            and not rail_obscured_d106
        )
        if visible_d106_joint and row["review_state"] != "accepted":
            row["note"] = (
                f"Corrected D106 fit identifies the physical pin{row['pin']} solder-joint "
                "centre; the solder cap hides its copper departure, so no destination "
                "or intentional strap is accepted"
            )
        if rail_obscured_d106 and row["review_state"] != "accepted":
            role = "candidate Q3 clock path" if row["pin"] == "7" else "unresolved functional path"
            row["note"] = (
                f"Corrected D106 fit extrapolates pin{row['pin']} into the rail-obscured "
                f"package end; this solder coordinate is not electrical evidence for the {role}"
            )
        rail_obscured_d96 = (
            row["refdes"] == "D96"
            and side == "solder"
            and row["pin"] in {"7", "8"}
        )
        if rail_obscured_d96 and row["review_state"] != "accepted":
            row["note"] = (
                f"Validated D96 fit extrapolates pin{row['pin']} into the broad-rail-obscured "
                "package end; this coordinate is not electrical evidence for a destination"
            )
        suffix = f"local {side} package fit establishes pad identity only; no electrical path accepted"
        if (row["review_state"] != "accepted" and not rail_obscured_d106
                and not rail_obscured_d96 and suffix not in row["note"]):
            row["note"] = (row["note"].rstrip("; ") + "; " + suffix).lstrip("; ")
        changed += 1
    expected = sum(len(item["projected_pins"]) for key, item in fits.items() if key[1] in sides)
    # Only unresolved pins have endpoint rows, so require two rows per distinct
    # unresolved pin rather than every projected package pad.
    unresolved = {(row["refdes"], row["pin"]) for row in rows if row["refdes"] in requested}
    expected_changed = len(sides) * len(unresolved)
    if changed != expected_changed:
        raise SystemExit(f"expected {expected_changed} unresolved observations, changed {changed}; fits expose {expected} pads")
    with ENDPOINTS.open("w", newline="") as destination:
        writer = csv.DictWriter(destination, FIELDS); writer.writeheader(); writer.writerows(rows)
    print(f"applied {args.side} local fits to {changed} measurement observations")


if __name__ == "__main__":
    main()
