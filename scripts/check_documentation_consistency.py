#!/usr/bin/env python3
"""Guard public status in both a working tree and a clean Git checkout.

The fabrication tree is intentionally ignored.  Tracked status/checksum records
must therefore be internally consistent without it; byte-level package and
order-report checks are added when the local fabrication tree is available.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHA256_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", re.I)


def read(path: str) -> str:
    target = ROOT / path
    return target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    failures: list[str] = []
    core = {
        "README.md": read("README.md"),
        "PLAN.md": read("PLAN.md"),
        "docs/README.md": read("docs/README.md"),
    }
    evidence = {
        "D2": read("docs/d2-reconstruction-constraints.md"),
        "D94": read("docs/d94-reconstruction-constraints.md"),
        "unmodeled ICs": read("docs/unmodeled-footprint-inventory.md"),
        "source-risk nets": read("docs/replica-bringup-verification-points.md"),
        "sourcing": read("docs/replica-sourcing-readiness.md"),
    }

    blockers = {
        "D2": "Status: **D2 RECONSTRUCTION READY**" not in evidence["D2"],
        "D94": "Status: **D94 RECONSTRUCTION READY**" not in evidence["D94"],
        "unmodeled ICs": "Status: **READY FOR DESIGN RELEASE**" not in evidence["unmodeled ICs"],
        "source-risk nets": "Status: **DESIGN RELEASE RISKS CLOSED**" not in evidence["source-risk nets"],
        "sourcing": "Status: **SOURCING READY**" not in evidence["sourcing"],
    }
    design_held = any(blockers.values())

    for path, text in core.items():
        if not text:
            failures.append(f"missing core document: {path}")
            continue
        if design_held and "hold" not in text.lower() and "not released" not in text.lower():
            failures.append(f"{path} does not expose the active design hold")

    lvs_scope: dict[str, tuple[int, int]] = {}
    for path in ("README.md", "PLAN.md", "sync/README.md"):
        match = re.search(
            r"(\d+) mapped instances and (\d+) (?:matched |compared )?nets",
            read(path),
        )
        if not match:
            failures.append(f"{path} does not expose the current LVS scope")
        else:
            lvs_scope[path] = (int(match.group(1)), int(match.group(2)))
    if len(set(lvs_scope.values())) > 1:
        failures.append(
            "LVS scope disagrees across public docs: "
            + ", ".join(f"{path}={scope[0]}/{scope[1]}" for path, scope in lvs_scope.items())
        )

    manufacturing = read("docs/replica-manufacturing-readiness.md")
    recorded_package_digests: dict[str, set[str]] = {}
    for path in ("README.md", "PLAN.md", "docs/replica-manufacturing-readiness.md"):
        recorded_package_digests[path] = {digest.lower() for digest in SHA256_RE.findall(read(path))}
    shared_package_digests = set.intersection(*recorded_package_digests.values())
    if not shared_package_digests:
        failures.append("tracked release documents do not share a recorded package SHA256")

    fab_root = ROOT / "fab"
    upload_zip = fab_root / "gerbers/upload/juku-replica-gerbers-drill.zip"
    if fab_root.exists() and not upload_zip.exists():
        failures.append("local fabrication tree exists but main-board upload ZIP is missing")
    elif upload_zip.exists():
        digest = sha256(upload_zip)
        for path in ("README.md", "PLAN.md", "docs/replica-manufacturing-readiness.md"):
            if digest not in read(path):
                failures.append(f"{path} does not contain current upload ZIP SHA256 {digest}")

    order = read("fab/gerbers/order-readiness.md")
    if design_held:
        if "Status: **DESIGN HOLD / PACKAGE VERIFIED**" not in manufacturing:
            failures.append("manufacturing report does not distinguish package verification from design hold")
        if fab_root.exists() and "Status: **PACKAGE READY / DESIGN HOLD**" not in order:
            failures.append("order-readiness report does not expose the active design hold")
        for path, text in core.items():
            if "READY TO UPLOAD" in text or "ORDER READY" in text:
                failures.append(f"{path} contains obsolete release language")
    else:
        if "Status: **RELEASED FOR UPLOAD**" not in manufacturing:
            failures.append("all release evidence passes but manufacturing report is not released")
        if fab_root.exists() and "Status: **RELEASED FOR ORDER**" not in order:
            failures.append("all release evidence passes but order report is not released")

    removed_live_docs = [
        "docs/project-status.md",
        "docs/roadmap.md",
        "docs/milestone-ledger.md",
        "docs/grind-backlog.md",
        "docs/phase-b.md",
        "docs/digitization-plan.md",
        "docs/boot-findings.md",
        "docs/bom-toward-76.md",
        "docs/emaplaat-harvest.md",
        "docs/re3-decode.md",
        "docs/mame-interface-map.md",
        "docs/basic-low-stub-inspection.md",
        "docs/basic-cartridge-tail-hypotheses.md",
        "docs/basic-launch-probe.md",
        "docs/basic-factory-command-probe.md",
        "spinoffs/minimal-vga/docs/manufacturing-roadmap.md",
        "spinoffs/minimal-vga/docs/rev-a-bare-pcb-order.md",
    ]
    for path in removed_live_docs:
        if (ROOT / path).exists():
            failures.append(f"superseded live-status document still exists: {path}")

    board = read("kicad/juku.board.json")
    dual_bom = read("docs/replica-dual-config-bom.csv")
    if "D84-D91 are populated" not in board or "D60-D83 are empty" not in board:
        failures.append("board JSON does not state the .158/.009 D84-D91 population")
    if '"D84, D85, D86, D87, D88, D89, D90, D91"' not in dual_bom:
        failures.append("dual-config BOM does not select D84-D91 as the populated RAM row")

    unmodeled = evidence["unmodeled ICs"]
    expected_unmodeled = ("D28", "D95", "D96", "D97", "D98", "D99", "D101", "D102", "D106")
    unmodeled_count_match = re.search(r"and `(\d+)` promoted FDC devices", unmodeled)
    unmodeled_count = None
    if unmodeled_count_match:
        unmodeled_count = int(unmodeled_count_match.group(1))
        if unmodeled_count and not re.search(
            rf"{unmodeled_count}\s+official\s+FDC-support\s+ICs",
            core["README.md"],
        ):
            failures.append("README does not expose the current untraced FDC-device count")
    if unmodeled_count == len(expected_unmodeled):
        for ref in expected_unmodeled:
            if f"| `{ref}` |" not in unmodeled:
                failures.append(
                    f"unmodeled-footprint report count is {unmodeled_count} but omits {ref}"
                )
    if unmodeled_count and f"{unmodeled_count} official FDC devices with untraced functional pins" not in board:
        failures.append("board JSON does not expose all untraced FDC devices as a design boundary")

    risk_match = re.search(r"Verification-point nets: `(\d+)`", evidence["source-risk nets"])
    if risk_match:
        risk_count = int(risk_match.group(1))
        if risk_count and not re.search(
            rf"{risk_count}\s+modeled\s+nets retain source-risk annotations",
            core["README.md"],
        ):
            failures.append("README does not expose the current residual source-risk net count")
        for path in ("PLAN.md", "hdl/README.md"):
            if not re.search(rf"\b{risk_count}\b[^\n]*source-risk", read(path)):
                failures.append(f"{path} does not expose the current residual source-risk net count")

    vjuga = {
        "spinoffs/minimal-vga/README.md": read("spinoffs/minimal-vga/README.md"),
        "spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md": read(
            "spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md"
        ),
        "spinoffs/minimal-vga/kicad/fab-notes.md": read("spinoffs/minimal-vga/kicad/fab-notes.md"),
    }
    for path, text in vjuga.items():
        if "hold" not in text.lower():
            failures.append(f"{path} does not expose the VJUGA design hold")
        if "READY TO UPLOAD" in text or "READY FOR VENDOR PREVIEW" in text:
            failures.append(f"{path} contains obsolete VJUGA release language")
    if "No real Juku ROM has booted" not in vjuga["spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md"]:
        failures.append("VJUGA readiness does not state that real-ROM boot is unproven")
    vjuga_zip = ROOT / "fab" / "minimal-vga" / "upload" / "vjuga-rev-a-gerbers-drill.zip"
    if vjuga_zip.exists():
        vjuga_digest = sha256(vjuga_zip)
        if vjuga_digest not in vjuga["spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md"]:
            failures.append(f"VJUGA readiness does not contain current Gerber ZIP SHA256 {vjuga_digest}")

    cartridge = read("docs/cartridge-basic-boundary.md")
    cartridge_image = ROOT / "roms" / "jbasic11.bin"
    if "Status: **ARTIFACT OR DOCUMENTED PROCEDURE REQUIRED**" not in cartridge:
        failures.append("consolidated cartridge BASIC boundary is missing or stale")
    if cartridge_image.exists() and sha256(cartridge_image) not in cartridge:
        failures.append("cartridge BASIC boundary does not contain the current jbasic11 SHA256")

    if failures:
        print("Documentation consistency check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    held = ", ".join(name for name, active in blockers.items() if active)
    package_scope = "local package verified" if upload_zip.exists() else "tracked package record verified"
    print(f"Documentation status is consistent; design hold: {held or 'none'}; {package_scope}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
