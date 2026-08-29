#!/usr/bin/env python3
"""Build/check the three reproducible rev-B 27C256 programming images."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EKTA_STOCK = ROOT / "roms" / "ekta37.bin"
EKTA = HERE / "ekta37_z80.bin"
C10_SOURCE = ROOT / "spinoffs" / "jukuravi" / "network-rom" / "juku-network-rom-abi1.4-c10.bin"
C9_IMMUTABLE = ROOT / "spinoffs" / "jukuravi" / "network-rom" / "juku-network-rom-abi1.4-c9.bin"
DIAG_BUILDER = HERE / "revb-diag" / "build_diag.py"

OUTPUTS = {
    "EKTA3.7/VJUGA": HERE / "ekta37_z80-27c256.bin",
    "NETC10/VJUGA-16K": HERE / "netc10_vjuga.bin",
    "NETC10/VJUGA": HERE / "netc10_vjuga-27c256.bin",
    "DIAG/VJUGA-16K": HERE / "diag_vjuga.bin",
    "DIAG/VJUGA": HERE / "diag_vjuga-27c256.bin",
}
MANIFEST = HERE / "revb-rom-set.json"
DIAG_MAP = HERE / "diag_vjuga.map.json"

PINNED = {
    EKTA_STOCK: "fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27",
    EKTA: "343ef2e6f0e5358bdc52cab7117f54ec583c0dc754499f5518ff8933bbc7befa",
    C10_SOURCE: "fbf9baaad9027a5335e3549da3a396eb999bbaae1a1f3f5f6e2f36798848a6bc",
    C9_IMMUTABLE: "352417fafcf1ceaef40b8d39916acdaee6de03d914eafe2b54185ccbabe35530",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_diag() -> tuple[bytes, dict[str, object]]:
    spec = importlib.util.spec_from_file_location("revb_diag_builder", DIAG_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load DIAG builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    for path, expected_sha in PINNED.items():
        data = path.read_bytes()
        if len(data) != 16384 or sha(data) != expected_sha:
            raise SystemExit(f"unexpected source {path}: size={len(data)} sha256={sha(data)}")

    ekta_stock = EKTA_STOCK.read_bytes()
    ekta = EKTA.read_bytes()
    ekta_diff = [i for i, (left, right) in enumerate(zip(ekta_stock, ekta)) if left != right]
    if ekta_diff != [0x000A, 0x0021, 0x0024, 0x0026]:
        raise SystemExit(f"EKTA Z80 patch scope changed: {ekta_diff}")
    expected_ekta_changes = {
        "000A": [0x1A, 0xE2], "0021": [0x08, 0x00],
        "0024": [0x10, 0x00], "0026": [0x20, 0x00],
    }
    actual_ekta_changes = {f"{i:04X}": [ekta_stock[i], ekta[i]] for i in ekta_diff}
    if actual_ekta_changes != expected_ekta_changes:
        raise SystemExit(f"EKTA Z80 patch bytes changed: {actual_ekta_changes}")

    c10 = C10_SOURCE.read_bytes()
    diag, diag_metadata = load_diag()
    if len(diag) != 16384 or sum(diag) & 0xFF:
        raise SystemExit("DIAG image size/checksum contract failed")

    products = {
        "EKTA3.7/VJUGA": ekta + ekta,
        "NETC10/VJUGA-16K": c10,
        "NETC10/VJUGA": c10 + c10,
        "DIAG/VJUGA-16K": diag,
        "DIAG/VJUGA": diag + diag,
    }
    for role in ("EKTA3.7/VJUGA", "NETC10/VJUGA", "DIAG/VJUGA"):
        image = products[role]
        if len(image) != 32768 or image[:16384] != image[16384:]:
            raise SystemExit(f"{role} is not an exact duplicated 27C256 image")

    manifest = {
        "schema": 1,
        "status": "R5.I3 reproducible three-ROM set",
        "eprom": "27C256, 32768 bytes, A14 selects identical 16 KiB halves",
        "images": {
            "EKTA3.7/VJUGA": {
                "source": str(EKTA_STOCK.relative_to(ROOT)),
                "source_sha256": sha(ekta_stock),
                "derived_16k": str(EKTA.relative_to(ROOT)),
                "derived_16k_sha256": sha(ekta),
                "z80_changes": actual_ekta_changes,
                "output": str(OUTPUTS["EKTA3.7/VJUGA"].relative_to(ROOT)),
                "bytes": len(products["EKTA3.7/VJUGA"]),
                "sha256": sha(products["EKTA3.7/VJUGA"]),
                "duplication": "two byte-identical 16384-byte halves",
            },
            "NETC10/VJUGA": {
                "source": str(C10_SOURCE.relative_to(ROOT)),
                "source_sha256": sha(c10),
                "derived_16k": str(OUTPUTS["NETC10/VJUGA-16K"].relative_to(ROOT)),
                "derived_16k_sha256": sha(c10),
                "z80_changes": {},
                "z80_basis": "C10 is reproducibly assembled with zmac -8 from canonical 8080-subset source; native-Z80 system regression is the execution guard",
                "pit_policy": "unchanged: D57 channel-0 mode-2/count-4 initialization retained",
                "output": str(OUTPUTS["NETC10/VJUGA"].relative_to(ROOT)),
                "bytes": len(products["NETC10/VJUGA"]),
                "sha256": sha(products["NETC10/VJUGA"]),
                "duplication": "two byte-identical 16384-byte halves",
            },
            "DIAG/VJUGA": {
                "source": str(DIAG_BUILDER.relative_to(ROOT)),
                "derived_16k": str(OUTPUTS["DIAG/VJUGA-16K"].relative_to(ROOT)),
                "derived_16k_sha256": sha(diag),
                "map": str(DIAG_MAP.relative_to(ROOT)),
                "stack_ready_address": diag_metadata["stack_ready_address"],
                "early_forbidden_instructions": diag_metadata["early_forbidden_instructions"],
                "expected_post_sequence": diag_metadata["expected_post_sequence"],
                "output": str(OUTPUTS["DIAG/VJUGA"].relative_to(ROOT)),
                "bytes": len(products["DIAG/VJUGA"]),
                "sha256": sha(products["DIAG/VJUGA"]),
                "duplication": "two byte-identical 16384-byte halves",
            },
        },
        "immutable_comparison": {
            "C9": str(C9_IMMUTABLE.relative_to(ROOT)),
            "sha256": sha(C9_IMMUTABLE.read_bytes()),
            "modified": False,
        },
        "build": "python3 spinoffs/minimal-vga/roms/build_revb_rom.py",
        "check": "python3 spinoffs/minimal-vga/roms/build_revb_rom.py --check",
        "program_and_readback": [
            "select the exact 27C256 device and its established Willem adapter/DIP settings",
            "load the named 32768-byte artifact; do not split it into D15/D16 files",
            "program once and accept the programmer's full verify",
            "read the device back to a fresh file and compare its SHA-256 to this manifest before labelling",
            "label by role: EKTA3.7/VJUGA, NETC10/VJUGA, or DIAG/VJUGA",
        ],
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode()
    diag_map_bytes = (json.dumps(diag_metadata, indent=2) + "\n").encode()

    expected = {OUTPUTS[name]: data for name, data in products.items()}
    expected[MANIFEST] = manifest_bytes
    expected[DIAG_MAP] = diag_map_bytes
    if args.check:
        for path, data in expected.items():
            if not path.exists() or path.read_bytes() != data:
                raise SystemExit(f"REVB-ROM-SET: {path.name} is stale; rebuild without --check")
    else:
        for path, data in expected.items():
            path.write_bytes(data)

    print("REVB-ROM-SET: PASS")
    for role in ("EKTA3.7/VJUGA", "NETC10/VJUGA", "DIAG/VJUGA"):
        print(f"  {role}: 32768 bytes sha256={sha(products[role])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
