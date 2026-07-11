#!/usr/bin/env python3
"""Create and validate durable registration records for the July 2026 photo grids.

The tool deliberately separates observations from accepted electrical evidence.
It inventories source files, checks their hashes, emits contact sheets, and
validates manual registration/endpoint records.  It never edits board.json.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import struct
import subprocess
import math
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTO_DIR = ROOT / "ref/photos/juku-pcb-2"
MANIFEST = PHOTO_DIR / "registration.json"
ENDPOINTS = PHOTO_DIR / "endpoints.csv"
REVIEW_DIR = ROOT / "docs/photo-registration"
PANORAMA_REGISTRATION = REVIEW_DIR / "panorama-registration.json"
BOARD_FIDUCIALS = PHOTO_DIR / "panorama-board-fiducials.json"

GROUPS = (
    ("component_grid", "component", 4, 3, "200354648", "200455512", False),
    ("solder_grid", "solder", 3, 3, "200506061", "200537608", True),
    ("vg93_removed", "component", 1, 7, "202708344", "202753536", False),
)
FIELDS = ("endpoint_id", "image", "x_px", "y_px", "refdes", "pin", "candidate_net",
          "confidence", "review_state", "reviewer", "note")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def jpeg_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:2] != b"\xff\xd8":
        raise ValueError(f"not JPEG: {path}")
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1; continue
        marker = data[i + 1]; i += 2
        if marker in (0xD8, 0xD9): continue
        n = struct.unpack(">H", data[i:i + 2])[0]
        if marker in range(0xC0, 0xC4):
            return struct.unpack(">HH", data[i + 3:i + 7])[::-1]
        i += n
    raise ValueError(f"no JPEG dimensions: {path}")


def selected(group) -> list[Path]:
    _, _, _, _, first, last, _ = group
    photos = sorted(PHOTO_DIR.glob("PXL_20260710_*.jpg"))
    def stamp(p):
        m = re.search(r"_(\d{9})", p.stem)
        return m.group(1) if m else ""
    return [p for p in photos if first <= stamp(p) <= last]


def init() -> None:
    groups, images = [], {}
    for name, side, rows, cols, first, last, mirror in GROUPS:
        paths = selected((name, side, rows, cols, first, last, mirror))
        expected = rows * cols
        if len(paths) != expected:
            raise SystemExit(f"{name}: expected {expected} photos, found {len(paths)}")
        names = []
        for order, path in enumerate(paths):
            w, h = jpeg_size(path)
            rel = path.relative_to(ROOT).as_posix(); names.append(rel)
            images[rel] = {"sha256": sha256(path), "width": w, "height": h,
                           "side": side, "order": order,
                           "row": order // cols, "column": order % cols,
                           "fiducials": [], "homography": None,
                           "held_out_error_px": None}
        groups.append({"id": name, "side": side, "rows": rows, "columns": cols,
                       "mirror_x_to_component": mirror, "images": names})
    document = {"schema_version": 1, "board_width_mm": 310, "board_height_mm": 266,
                "coordinate_system": "component-side: origin board top-left, +x right, +y down",
                "promotion_rule": "only review_state=accepted endpoints may be proposed to board.json",
                "groups": groups, "images": images}
    MANIFEST.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
    if not ENDPOINTS.exists():
        with ENDPOINTS.open("w", newline="") as f: csv.DictWriter(f, FIELDS).writeheader()
    print(f"wrote {MANIFEST.relative_to(ROOT)} ({len(images)} images)")


def validate() -> None:
    doc = json.loads(MANIFEST.read_text())
    errors = []
    for rel, rec in doc["images"].items():
        path = ROOT / rel
        if not path.exists(): errors.append(f"missing {rel}"); continue
        if sha256(path) != rec["sha256"]: errors.append(f"hash mismatch {rel}")
        if list(jpeg_size(path)) != [rec["width"], rec["height"]]: errors.append(f"size mismatch {rel}")
        fids = rec.get("fiducials", [])
        if fids and len(fids) < 4: errors.append(f"{rel}: registration needs >=4 fiducials")
        for n, fid in enumerate(fids):
            if sorted(fid.keys()) != sorted(("board_mm", "image_px", "landmark", "use")):
                errors.append(f"{rel}: fiducial {n} schema mismatch")
            if fid.get("use") not in ("fit", "check"):
                errors.append(f"{rel}: fiducial {n} use must be fit/check")
        if rec.get("homography") is not None and len(rec["homography"]) != 9:
            errors.append(f"{rel}: homography needs 9 values")
    with ENDPOINTS.open(newline="") as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != FIELDS: errors.append("endpoint CSV header/schema mismatch")
        ids = set()
        for line, row in enumerate(reader, 2):
            if row["endpoint_id"] in ids: errors.append(f"endpoint line {line}: duplicate id")
            ids.add(row["endpoint_id"])
            if row["image"] not in doc["images"]: errors.append(f"endpoint line {line}: unknown image")
            if row["review_state"] not in ("candidate", "accepted", "rejected", "measurement"):
                errors.append(f"endpoint line {line}: invalid review_state")
            if row["review_state"] == "accepted" and (not row["reviewer"] or not row["refdes"] or not row["pin"]):
                errors.append(f"endpoint line {line}: accepted record lacks reviewer/refdes/pin")
    if BOARD_FIDUCIALS.exists():
        board_fiducials = json.loads(BOARD_FIDUCIALS.read_text())
        for group_id in ("component_grid", "solder_grid"):
            group = board_fiducials.get("groups", {}).get(group_id, {})
            fids = group.get("fiducials", [])
            if len([item for item in fids if item.get("use") == "fit"]) != 4:
                errors.append(f"{group_id}: board registration needs exactly four fit fiducials")
            if not any(item.get("use") == "check" for item in fids):
                errors.append(f"{group_id}: board registration needs a held-out check")
    else:
        errors.append(f"missing {BOARD_FIDUCIALS.relative_to(ROOT)}")
    if errors: raise SystemExit("photo registration FAIL\n- " + "\n- ".join(errors))
    print(f"photo registration PASS: {len(doc['images'])} sources, {len(ids)} endpoints")


def solve_linear(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination for the small 8-variable homography fit."""
    m = [row[:] + [rhs] for row, rhs in zip(a, b)]
    n = len(b)
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(m[row][col]))
        if abs(m[pivot][col]) < 1e-12: raise ValueError("degenerate fiducials")
        m[col], m[pivot] = m[pivot], m[col]
        scale = m[col][col]; m[col] = [v / scale for v in m[col]]
        for row in range(n):
            if row == col: continue
            scale = m[row][col]
            m[row] = [x - scale * y for x, y in zip(m[row], m[col])]
    return [m[i][-1] for i in range(n)]


def fit_homography(fids: list[dict]) -> list[float]:
    # board millimetres -> source-image pixels. Exactly four fit landmarks keep
    # the result auditable; additional landmarks are independent checks.
    fit = [f for f in fids if f["use"] == "fit"]
    if len(fit) != 4: raise ValueError(f"expected exactly 4 fit fiducials, got {len(fit)}")
    a, b = [], []
    for f in fit:
        x, y = map(float, f["board_mm"]); u, v = map(float, f["image_px"])
        a += [[x, y, 1, 0, 0, 0, -u*x, -u*y],
              [0, 0, 0, x, y, 1, -v*x, -v*y]]
        b += [u, v]
    return solve_linear(a, b) + [1.0]


def project(h: list[float], xy: list[float]) -> tuple[float, float]:
    x, y = xy; d = h[6]*x + h[7]*y + h[8]
    return ((h[0]*x + h[1]*y + h[2])/d, (h[3]*x + h[4]*y + h[5])/d)


def solve() -> None:
    doc = json.loads(MANIFEST.read_text()); solved = 0
    for rel, rec in doc["images"].items():
        fids = rec.get("fiducials", [])
        if not fids: continue
        try: h = fit_homography(fids)
        except ValueError as e: raise SystemExit(f"{rel}: {e}")
        checks = [f for f in fids if f["use"] == "check"]
        if not checks: raise SystemExit(f"{rel}: add at least one held-out check fiducial")
        errors = []
        for f in checks:
            u, v = project(h, f["board_mm"]); iu, iv = f["image_px"]
            errors.append(math.hypot(u-iu, v-iv))
        rec["homography"] = [round(x, 12) for x in h]
        rec["held_out_error_px"] = round(max(errors), 3); solved += 1
    MANIFEST.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"solved {solved} image registrations")


def contact_sheets() -> None:
    if not shutil.which("magick"): raise SystemExit("ImageMagick 'magick' is required")
    doc = json.loads(MANIFEST.read_text()); REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for group in doc["groups"]:
        out = REVIEW_DIR / f"{group['id']}.jpg"
        cmd = ["magick", "montage", *[str(ROOT / p) for p in group["images"]],
               "-auto-orient", "-thumbnail", "900x700", "-geometry", "+8+8",
               "-tile", f"{group['columns']}x{group['rows']}", str(out)]
        subprocess.run(cmd, check=True)
        print(f"wrote {out.relative_to(ROOT)}")


def panoramas() -> None:
    """Feature-stitch every tile in each overlapping board grid.

    OpenCV is deliberately optional because the source photos and manifest,
    rather than these lossy navigation renders, remain the evidence record.
    The stock OpenCV panorama stitcher is not used: it may silently discard
    peripheral tiles.  Grid-adjacent homographies retain all declared inputs.
    """
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise SystemExit(
            "OpenCV is required for panoramas; install opencv-python-headless "
            "in a virtual environment"
        ) from exc
    doc = json.loads(MANIFEST.read_text()); REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    registration = {"schema_version": 1, "coordinate_system": "panorama pixels",
                    "groups": {}}
    for group in doc["groups"]:
        if group["id"] == "vg93_removed":
            continue
        images = []
        for rel in group["images"]:
            image = cv2.imread(str(ROOT / rel))
            if image is None:
                raise SystemExit(f"could not read {rel}")
            images.append(cv2.resize(image, None, fx=0.22, fy=0.22,
                                     interpolation=cv2.INTER_AREA))
        rows, columns = group["rows"], group["columns"]
        sift = cv2.SIFT_create(nfeatures=10000)
        features = [sift.detectAndCompute(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), None)
                    for image in images]
        edges = {}
        for index in range(len(images)):
            row, column = divmod(index, columns)
            neighbours = ([index + 1] if column + 1 < columns else [])
            neighbours += ([index + columns] if row + 1 < rows else [])
            for neighbour in neighbours:
                keys_a, desc_a = features[index]
                keys_b, desc_b = features[neighbour]
                matches = cv2.BFMatcher().knnMatch(desc_b, desc_a, k=2)
                good = [first for first, second in matches
                        if first.distance < 0.70 * second.distance]
                if len(good) < 4:
                    continue
                source = np.float32([keys_b[item.queryIdx].pt for item in good])
                target = np.float32([keys_a[item.trainIdx].pt for item in good])
                transform, mask = cv2.findHomography(source, target, cv2.RANSAC, 3)
                inliers = int(mask.sum()) if mask is not None else 0
                if transform is not None and inliers >= 15:
                    edges[index, neighbour] = transform
                    edges[neighbour, index] = np.linalg.inv(transform)

        root = (rows // 2) * columns + columns // 2
        transforms = {root: np.eye(3)}
        queue = deque([root])
        while queue:
            current = queue.popleft()
            for (source, target), transform in edges.items():
                if source == current and target not in transforms:
                    transforms[target] = transforms[current] @ transform
                    queue.append(target)
        if len(transforms) != len(images):
            missing = sorted(set(range(len(images))) - set(transforms))
            raise SystemExit(f"{group['id']}: disconnected tiles {missing}")

        corners = []
        for index, image in enumerate(images):
            height, width = image.shape[:2]
            box = np.float32([[0, 0], [width, 0], [width, height], [0, height]])[None]
            corners.extend(cv2.perspectiveTransform(box, transforms[index])[0])
        corners = np.array(corners)
        minimum = np.floor(corners.min(axis=0)); maximum = np.ceil(corners.max(axis=0))
        width, height = (maximum - minimum).astype(int)
        shift = np.array([[1, 0, -minimum[0]], [0, 1, -minimum[1]], [0, 0, 1]])
        accumulator = np.zeros((height, width, 3), np.float32)
        weights = np.zeros((height, width), np.float32)
        for index, image in enumerate(images):
            source_height, source_width = image.shape[:2]
            mask = np.full((source_height, source_width), 255, np.uint8)
            transform = shift @ transforms[index]
            warped = cv2.warpPerspective(image, transform, (width, height))
            weight = cv2.warpPerspective(mask, transform, (width, height)).astype(np.float32) / 255
            accumulator += warped * weight[:, :, None]
            weights += weight
        panorama = (accumulator / np.maximum(weights[:, :, None], 1)).astype(np.uint8)
        out = REVIEW_DIR / f"{group['id']}-panorama.jpg"
        if not cv2.imwrite(str(out), panorama, [cv2.IMWRITE_JPEG_QUALITY, 95]):
            raise SystemExit(f"could not write {out}")
        scale = np.array([[0.22, 0, 0], [0, 0.22, 0], [0, 0, 1]])
        registration["groups"][group["id"]] = {
            "panorama": out.relative_to(ROOT).as_posix(),
            "width": int(width), "height": int(height),
            "all_tiles_connected": True,
            "images": {
                rel: {"original_to_panorama_homography":
                      [round(float(value), 12) for value in (shift @ transforms[index] @ scale).flat]}
                for index, rel in enumerate(group["images"])
            },
        }
        print(f"wrote {out.relative_to(ROOT)} ({panorama.shape[1]}x{panorama.shape[0]})")
    PANORAMA_REGISTRATION.write_text(json.dumps(registration, indent=2) + "\n")
    print(f"wrote {PANORAMA_REGISTRATION.relative_to(ROOT)}")


def project_panorama(group_id: str, x: float, y: float) -> None:
    """Project a panorama review point back into every covering source JPEG."""
    try:
        import numpy as np
    except ImportError as exc:
        raise SystemExit("NumPy is required for panorama projection") from exc
    registration = json.loads(PANORAMA_REGISTRATION.read_text())
    manifest = json.loads(MANIFEST.read_text())
    group = registration["groups"].get(group_id)
    if group is None:
        raise SystemExit(f"unknown panorama group {group_id!r}")
    point = np.array([x, y, 1.0])
    found = 0
    for rel, record in group["images"].items():
        transform = np.array(record["original_to_panorama_homography"]).reshape(3, 3)
        source = np.linalg.inv(transform) @ point
        source /= source[2]
        width = manifest["images"][rel]["width"]
        height = manifest["images"][rel]["height"]
        if 0 <= source[0] < width and 0 <= source[1] < height:
            print(f"{rel},{source[0]:.3f},{source[1]:.3f}")
            found += 1
    if not found:
        raise SystemExit("point is not covered by any source image")


def rectify() -> None:
    """Rectify both panoramas into common component-side board coordinates."""
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise SystemExit("OpenCV and NumPy are required for rectification") from exc
    config = json.loads(BOARD_FIDUCIALS.read_text())
    derived = {"schema_version": 1, "pixels_per_mm": 5,
               "coordinate_system": "component-side board coordinates", "groups": {}}
    width, height = 310 * 5, 266 * 5
    board_to_output = np.array([[5, 0, 0], [0, 5, 0], [0, 0, 1]], dtype=float)
    for group_id, group in config["groups"].items():
        h = fit_homography(group["fiducials"])
        checks = [item for item in group["fiducials"] if item["use"] == "check"]
        errors = []
        for item in checks:
            projected = project(h, item["board_mm"])
            errors.append(math.hypot(projected[0] - item["image_px"][0],
                                     projected[1] - item["image_px"][1]))
        source = cv2.imread(str(REVIEW_DIR / f"{group_id}-panorama.jpg"))
        panorama_to_output = board_to_output @ np.linalg.inv(np.array(h).reshape(3, 3))
        output = cv2.warpPerspective(source, panorama_to_output, (width, height))
        destination = REVIEW_DIR / f"{group_id}-rectified.jpg"
        cv2.imwrite(str(destination), output, [cv2.IMWRITE_JPEG_QUALITY, 95])
        derived["groups"][group_id] = {
            "board_to_panorama_homography": h,
            "max_held_out_error_px": round(max(errors), 3),
            "rectified_image": destination.relative_to(ROOT).as_posix(),
        }
        print(f"wrote {destination.relative_to(ROOT)}; held-out error {max(errors):.2f}px")
    destination = REVIEW_DIR / "board-registration.json"
    destination.write_text(json.dumps(derived, indent=2) + "\n")
    print(f"wrote {destination.relative_to(ROOT)}")


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument(
        "command", choices=("init", "validate", "solve", "contact-sheets", "panoramas", "project", "rectify"))
    p.add_argument("--group", choices=("component_grid", "solder_grid"))
    p.add_argument("--x", type=float); p.add_argument("--y", type=float)
    args = p.parse_args(); command = args.command
    if command == "project":
        if args.group is None or args.x is None or args.y is None:
            p.error("project requires --group, --x, and --y")
        project_panorama(args.group, args.x, args.y)
        return
    {"init": init, "validate": validate, "solve": solve,
     "contact-sheets": contact_sheets, "panoramas": panoramas,
     "rectify": rectify}[command]()


if __name__ == "__main__": main()
