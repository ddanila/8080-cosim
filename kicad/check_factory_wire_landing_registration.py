#!/usr/bin/env python3
"""Guard image-space registration without promoting guessed PCB geometry."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from check_factory_wire_links import LINKS


ROOT = Path(__file__).resolve().parents[1]
RECORD = (
    ROOT
    / "ref/photos/dgsh5-109-009-sb/factory-wire-landing-registration.json"
)


def main() -> int:
    document = json.loads(RECORD.read_text(encoding="utf-8"))
    errors: list[str] = []
    if document.get("schema_version") != 1:
        errors.append("unsupported schema version")

    source_records = document.get("source_images", [])
    sources: dict[str, tuple[int, int]] = {}
    for record in source_records:
        path = record.get("path", "")
        size = record.get("size_px")
        if not path or path in sources:
            errors.append(f"missing or duplicate source-image path: {path!r}")
            continue
        if not (
            isinstance(size, list)
            and len(size) == 2
            and all(isinstance(value, int) and value > 0 for value in size)
        ):
            errors.append(f"{path} size_px must contain two positive integers")
            continue
        sources[path] = (size[0], size[1])
        source = ROOT / path
        if not source.is_file():
            errors.append(f"source image missing: {path}")
        else:
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest != record.get("sha256"):
                errors.append(f"source image SHA256 mismatch for {path}: {digest}")
    if not sources:
        errors.append("no source images registered")

    expected_points = {point for _, point, _, _, _ in LINKS}
    records = document.get("points", [])
    actual_points = {record.get("point") for record in records}
    if actual_points != expected_points:
        errors.append(
            "point inventory mismatch: "
            f"expected {sorted(expected_points)}, got {sorted(actual_points)}"
        )
    if len(records) != len(actual_points):
        errors.append("duplicate point records")

    registered = 0
    board_fitted = 0
    for record in records:
        point = record.get("point")
        endpoints = record.get("endpoints", [])
        status = record.get("status")
        if len(endpoints) not in (0, 2):
            errors.append(f"A:{point} must have zero or two endpoint records")
        expected_status = (
            "pending"
            if not endpoints
            else (
                "board-fitted"
                if all(endpoint.get("board_mm") is not None for endpoint in endpoints)
                else "image-registered/board-fit-pending"
            )
        )
        if status != expected_status:
            errors.append(f"A:{point} status does not match its endpoint records")
        expected_terminals = {f"A{point}A", f"A{point}B"}
        terminals = {endpoint.get("terminal") for endpoint in endpoints}
        if endpoints and terminals != expected_terminals:
            errors.append(
                f"A:{point} terminal names must be {sorted(expected_terminals)}"
            )
        for endpoint in endpoints:
            source_image = endpoint.get("source_image")
            width, height = sources.get(source_image, (0, 0))
            if source_image not in sources:
                errors.append(
                    f"{endpoint.get('terminal')} references unknown source image"
                )
            drawing = endpoint.get("drawing_px")
            uncertainty = endpoint.get("uncertainty_px")
            if not (
                isinstance(drawing, list)
                and len(drawing) == 2
                and all(isinstance(value, int) for value in drawing)
                and 0 <= drawing[0] < width
                and 0 <= drawing[1] < height
            ):
                errors.append(f"{endpoint.get('terminal')} has invalid drawing_px")
            if not isinstance(uncertainty, int) or not 1 <= uncertainty <= 25:
                errors.append(
                    f"{endpoint.get('terminal')} has invalid pixel uncertainty"
                )
            registered += 1
            board_mm = endpoint.get("board_mm")
            island = endpoint.get("island_assignment")
            if board_mm is None:
                if island is not None:
                    errors.append(
                        f"{endpoint.get('terminal')} assigns an island before board fit"
                    )
            elif (
                not isinstance(board_mm, list)
                or len(board_mm) != 2
                or not all(isinstance(value, (int, float)) for value in board_mm)
                or not isinstance(island, str)
                or not island
            ):
                errors.append(
                    f"{endpoint.get('terminal')} board fit lacks coordinates/island"
                )
            else:
                board_fitted += 1

    if errors:
        for error in errors:
            print(f"FACTORY-WIRE-LANDINGS: FAIL: {error}")
        return 1
    print(
        "FACTORY-WIRE-LANDINGS: PASS: "
        f"{registered}/{2 * len(LINKS)} image-registered, "
        f"{board_fitted}/{2 * len(LINKS)} board-fitted"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
