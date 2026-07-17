#!/usr/bin/env python3
"""Guard the corrected lower-row D37 and intervening R57 placement."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "kicad/juku.kicad_pcb"
EVIDENCE = ROOT / "ref/photos/juku-pcb-2/cas-timing-row-registration.json"
LOCAL_REPORT = ROOT / "docs/photo-registration/local-packages/report.json"


def fail(message: str) -> None:
    raise SystemExit(f"D37/R57 PHOTO PLACEMENT: FAIL: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def centre(board: pcbnew.BOARD, refdes: str) -> tuple[float, float]:
    footprint = board.FindFootprintByReference(refdes)
    if footprint is None:
        fail(f"missing {refdes}")
    pads = list(footprint.Pads())
    return (
        sum(pcbnew.ToMM(pad.GetPosition().x) for pad in pads) / len(pads),
        sum(pcbnew.ToMM(pad.GetPosition().y) for pad in pads) / len(pads),
    )


evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
for source in evidence["sources"]:
    path = ROOT / source["path"]
    if not path.is_file() or sha256(path) != source["sha256"]:
        fail(f"source hash drifted: {source['path']}")

if evidence["assembly_order"] != ["D36", "R57", "D37", "D33"]:
    fail("assembly order drifted")

observations = evidence["lower_row"]["observations"]
anchor_left = observations["D36"]
anchor_right = observations["D33"]
pixel_span = anchor_right["centre_px"][0] - anchor_left["centre_px"][0]
board_span = anchor_right["board_centre_mm"][0] - anchor_left["board_centre_mm"][0]
if pixel_span <= 0 or board_span <= 0:
    fail("invalid bracketing anchors")


def interpolate_x(refdes: str) -> float:
    fraction = (
        observations[refdes]["centre_px"][0] - anchor_left["centre_px"][0]
    ) / pixel_span
    return anchor_left["board_centre_mm"][0] + fraction * board_span


if abs(interpolate_x("D37") - observations["D37"]["board_centre_mm"][0]) > 0.8:
    fail("D37 centre is inconsistent with the D36/D33 raw-photo interpolation")
if abs(interpolate_x("R57") - observations["R57"]["board_centre_mm"][0]) > 0.8:
    fail("R57 centre is inconsistent with the D36/D33 raw-photo interpolation")
if abs(interpolate_x("D103") - observations["D103"]["board_centre_mm"][0]) > 1.5:
    fail("held-out D103 row-order check exceeds 1.5 mm")
local = json.loads(LOCAL_REPORT.read_text(encoding="utf-8"))
fits = {(item["refdes"], item["side"]): item for item in local["fits"]}
fit = fits.get(("D37", "component"))
if fit is None or fit["image"] != evidence["lower_row"]["image"]:
    fail("lower-row D37 component fit is missing")
if fit["model"] != "similarity":
    fail("D37 component fit is not a similarity transform")
checks = {item["pin"]: item["error_px"] for item in fit["checks"]}
for pin in ("4", "8", "14"):
    if checks.get(pin, float("inf")) > 3.0:
        fail(f"D37 held-out pin {pin} exceeds 3 px")

board = pcbnew.LoadBoard(str(BOARD))
for refdes in ("D36", "D33", "D103"):
    actual = centre(board, refdes)
    expected = observations[refdes]["board_centre_mm"]
    if math.hypot(actual[0] - expected[0], actual[1] - expected[1]) > 0.02:
        fail(f"anchor {refdes} placement drifted")

for refdes in ("D37", "R57", "R46"):
    actual = centre(board, refdes)
    expected = observations[refdes]["board_centre_mm"]
    error = math.hypot(actual[0] - expected[0], actual[1] - expected[1])
    if error > 0.02:
        fail(f"{refdes} centre error {error:.3f} mm")

d37 = board.FindFootprintByReference("D37")
if abs(d37.GetOrientationDegrees() % 360 - 180.0) > 0.01:
    fail("D37 is not bottom-notched/180 degrees")

r57 = board.FindFootprintByReference("R57")
if abs(r57.GetOrientationDegrees() % 360 - 90.0) > 0.01:
    fail("R57 is not vertical")
if r57.GetValue() != "20":
    fail(f"R57 value is {r57.GetValue()!r}, expected '20'")
pads = list(r57.Pads())
span = math.hypot(
    pcbnew.ToMM(pads[0].GetPosition().x - pads[1].GetPosition().x),
    pcbnew.ToMM(pads[0].GetPosition().y - pads[1].GetPosition().y),
)
if abs(span - 10.16) > 0.01:
    fail(f"R57 lead span is {span:.3f} mm")

r46 = board.FindFootprintByReference("R46")
if abs(r46.GetOrientationDegrees() % 360 - 90.0) > 0.01:
    fail("R46 is not vertical")
if r46.GetValue() != "200":
    fail(f"R46 value is {r46.GetValue()!r}, expected '200'")

print(
    "D37/R57 PHOTO PLACEMENT: PASS — lower-row D37 identity, bottom notch, "
    "R57/R46 values and vertical placements, and bracketing anchors guarded"
)
