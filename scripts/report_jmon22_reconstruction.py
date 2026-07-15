#!/usr/bin/env python3
"""Audit the bounded, source-backed reconstruction of Monitor 2.2."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "jmon22-reconstruction.md"
MANIFEST = ROOT / "ref" / "reconstructed-firmware" / "jmon22-consensus-patch.json"
JMON22 = ROOT / "roms" / "jmon22.bin"
JMON33 = ROOT / "roms" / "jmon33.bin"
JBASIC11 = ROOT / "roms" / "jbasic11.bin"

EXPECTED_SHA256 = {
    "roms/jmon22.bin": "1b68f89ae4355391f434b3fae34e95cb4b150bf4bbcb967b5b177d48cd390589",
    "roms/jmon33.bin": "ce9e9c63abbb1780566423a871081bd0bf048a2f3c79e370b465ea9869ff51b8",
    "roms/jbasic11.bin": "ff86e17c7ce6de177e18bc0468d23cee7ed2ecd6e8adc56950138cdf6ee5ba60",
}
PATCH_OFFSET = 0x1EFC
CARTRIDGE_OFFSET = 0x1C34
ORIGINAL = 0x9A
REPLACEMENT = 0xDA
CATALOG_URL = "https://j3k.infoaed.ee/tarkvara-kataloog/"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checksum_rows(data: bytes) -> list[dict[str, int | bool]]:
    rows: list[dict[str, int | bool]] = []
    for block in range(8):
        start = 4 if block == 0 else block * 0x800
        end = (block + 1) * 0x800
        stored = data[3 + block]
        computed = sum(data[start:end]) & 0xFF
        rows.append(
            {
                "block": block,
                "start": start,
                "end": end - 1,
                "stored": stored,
                "computed": computed,
                "passes": stored == computed,
            }
        )
    return rows


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    inputs = {
        "roms/jmon22.bin": JMON22.read_bytes(),
        "roms/jmon33.bin": JMON33.read_bytes(),
        "roms/jbasic11.bin": JBASIC11.read_bytes(),
    }
    require(len(inputs["roms/jmon22.bin"]) == 0x4000, "jmon22 is not 16 KiB")
    require(len(inputs["roms/jmon33.bin"]) == 0x4000, "jmon33 is not 16 KiB")
    require(len(inputs["roms/jbasic11.bin"]) == 0x2000, "jbasic11 is not 8 KiB")
    for name, data in inputs.items():
        require(sha256(data) == EXPECTED_SHA256[name], f"unexpected SHA256 for {name}")

    original = inputs["roms/jmon22.bin"]
    require(original[PATCH_OFFSET] == ORIGINAL, "jmon22 candidate byte changed")
    require(inputs["roms/jmon33.bin"][PATCH_OFFSET] == REPLACEMENT, "jmon33 donor byte changed")
    require(inputs["roms/jbasic11.bin"][CARTRIDGE_OFFSET] == REPLACEMENT, "jbasic11 donor byte changed")

    body22 = original[0x03C8:0x2000]
    body33 = inputs["roms/jmon33.bin"][0x03C8:0x2000]
    cart_body = inputs["roms/jbasic11.bin"][0x0100:0x1D38]
    mismatches = [index for index, pair in enumerate(zip(body22, body33, strict=True)) if pair[0] != pair[1]]
    require(body33 == cart_body, "jmon33 and cartridge BASIC bodies no longer agree")
    require(mismatches == [PATCH_OFFSET - 0x03C8], "jmon22 BASIC body no longer has the expected sole mismatch")

    before = checksum_rows(original)
    repaired = bytearray(original)
    repaired[PATCH_OFFSET] = REPLACEMENT
    repaired_bytes = bytes(repaired)
    after = checksum_rows(repaired_bytes)
    require([row["block"] for row in before if not row["passes"]] == [3, 6, 7], "unexpected original checksum failures")
    require([row["block"] for row in after if not row["passes"]] == [6, 7], "bounded patch did not isolate failures to blocks 6 and 7")
    require(before[3]["computed"] == 0xF3 and after[3]["computed"] == 0x33, "block 3 checksum proof changed")

    manifest = {
        "schema_version": 1,
        "status": "partial-consensus-repair; no binary exported",
        "source": {
            "path": "roms/jmon22.bin",
            "sha256": sha256(original),
            "size": len(original),
        },
        "patches": [
            {
                "offset": "0x1EFC",
                "from": "0x9A",
                "to": "0xDA",
                "evidence": [
                    {
                        "artifact": "roms/jmon33.bin",
                        "sha256": sha256(inputs["roms/jmon33.bin"]),
                        "offset": "0x1EFC",
                        "value": "0xDA",
                    },
                    {
                        "artifact": "roms/jbasic11.bin",
                        "sha256": sha256(inputs["roms/jbasic11.bin"]),
                        "offset": "0x1C34",
                        "value": "0xDA",
                    },
                    {
                        "constraint": "Monitor 2.2 block 3 additive checksum",
                        "stored": "0x33",
                        "computed_before": "0xF3",
                        "computed_after": "0x33",
                    },
                ],
            }
        ],
        "candidate_sha256_if_applied": sha256(repaired_bytes),
        "unresolved_zero_based_blocks": [6, 7],
        "provenance_note": {
            "url": CATALOG_URL,
            "retrieved": "2026-07-15",
            "summary": "The JUKUROMS catalog says chip 7 was read with a couple of errors and chip 8 had 50 divergences across seven reads.",
        },
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# Monitor 2.2 reconstruction audit",
        "",
        "Status: **ONE BYTE PROVEN / ROM BLOCKS 6-7 UNRESOLVED**",
        "",
        "This generated audit identifies the only Monitor 2.2 byte that current",
        "repository evidence can reconstruct without guesswork. It preserves",
        "`roms/jmon22.bin` unchanged and exports only a machine-readable patch",
        "manifest; no partially repaired ROM binary is published.",
        "",
        "## Command",
        "",
        "```sh",
        "python3 scripts/report_jmon22_reconstruction.py",
        "```",
        "",
        "## Source guard",
        "",
        "| Artifact | Size | SHA256 |",
        "| --- | ---: | --- |",
    ]
    for name, data in inputs.items():
        lines.append(f"| `{name}` | `{len(data)}` | `{sha256(data)}` |")

    lines.extend(
        [
            "",
            "## Proven correction",
            "",
            "| Candidate | Monitor 2.2 | Monitor 3.3 | BASIC 1.1 cartridge | Checksum effect |",
            "| --- | --- | --- | --- | --- |",
            "| Monitor offset `0x1EFC` | `0x9A` | `0xDA` at `0x1EFC` | "
            "`0xDA` at mapped offset `0x1C34` | block 3 `0xF3` -> stored `0x33` |",
            "",
            "Monitor 3.3 and the separately packaged cartridge agree on `0xDA` across",
            "their otherwise byte-identical 7,224-byte BASIC body. Substituting that",
            "value for Monitor 2.2's sole body mismatch adds `0x40`, exactly closing",
            "the stored additive checksum. These three constraints converge on one",
            "correction; the manifest records it without rewriting the source image.",
            "",
            "## Checksum boundary",
            "",
            "| Block | Covered bytes | Stored | Before | After | Disposition |",
            "| ---: | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for old, new in zip(before, after, strict=True):
        disposition = "PASS"
        if not new["passes"]:
            needed = (int(new["stored"]) - int(new["computed"])) & 0xFF
            disposition = f"UNRESOLVED (checksum delta `+0x{needed:02X}`)"
        elif not old["passes"]:
            disposition = "REPAIRED BY PROVEN BYTE"
        lines.append(
            f"| `{old['block']}` | `0x{old['start']:04X}..0x{old['end']:04X}` | "
            f"`0x{old['stored']:02X}` | `0x{old['computed']:02X}` | "
            f"`0x{new['computed']:02X}` | {disposition} |"
        )

    lines.extend(
        [
            "",
            "The public JUKUROMS catalog says the seventh physical chip was read with",
            "a couple of errors and the eighth produced 50 divergences over seven read",
            f"attempts ([source]({CATALOG_URL}), checked 2026-07-15). Those are",
            "zero-based blocks 6 and 7 in this concatenated image—the same two blocks",
            "that remain bad after the proven correction.",
            "",
            "A checksum delta constrains only the sum of a 2 KiB block. It neither",
            "locates damaged bytes nor determines their values, particularly when the",
            "preservation source explicitly reports multiple unstable reads. Blocks 6",
            "and 7 therefore remain untouched until original per-read captures, a stable",
            "independent dump, or another byte-identical firmware source is recovered.",
            "",
            "## Preservation rule",
            "",
            f"- Original SHA256: `{sha256(original)}`.",
            f"- Hypothetical one-byte-patched SHA256: `{sha256(repaired_bytes)}`.",
            "- Patch manifest: `ref/reconstructed-firmware/jmon22-consensus-patch.json`.",
            "- Do not treat the hypothetical hash as a runnable or complete Monitor 2.2",
            "  release: its final two ROM blocks still fail their own checksums.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Wrote {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
