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
    "roms/ekta24.bin": "e1bd9894134ee4085c14bde854780539d3b1e03cfc032c81ec352729e9d69287",
    "roms/ekta31.bin": "26f1f4161a547ea60312a250bde9df41c0b07a939c0b880628050eaec18ec4e4",
    "roms/ekta32.bin": "1826563e23b5d8bc23c61694ceccb923d6a31778077934ad0338772070671122",
    "roms/ekta35.bin": "e8fe5e657037b8f3203f57512cd01cc35f7eaa2a3f0dae8d0ae19378908bd518",
    "roms/ekta37.bin": "fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27",
    "roms/ekta43.bin": "39e3ca8978b369632d03c658300654445b898139009f188cb154e2f901238ba7",
}
RELATED_ROM_NAMES = (
    "roms/jmon33.bin",
    "roms/ekta24.bin",
    "roms/ekta31.bin",
    "roms/ekta32.bin",
    "roms/ekta35.bin",
    "roms/ekta37.bin",
    "roms/ekta43.bin",
)
PATCH_OFFSET = 0x1EFC
CARTRIDGE_OFFSET = 0x1C34
ORIGINAL = 0x9A
REPLACEMENT = 0xDA
CATALOG_URL = "https://j3k.infoaed.ee/tarkvara-kataloog/"
CATALOG_PROVENANCE_COMMIT = "31c74684a3e3f3b4c094a6881891e7f462a47406"
CATALOG_PROVENANCE_URL = (
    "https://github.com/infoaed/juku3000/commit/" + CATALOG_PROVENANCE_COMMIT
)


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


def contextual_donor_matches(
    source: bytes,
    block: int,
    checksum_delta: int,
    donors: dict[str, bytes],
    flank: int = 2,
) -> list[dict[str, str]]:
    """Find checksum-closing bytes with identical local context in another ROM."""
    matches: list[dict[str, str]] = []
    start = block * 0x800
    end = (block + 1) * 0x800
    for offset in range(start, end):
        if offset < flank or offset + flank >= len(source):
            continue
        replacement = (source[offset] + checksum_delta) & 0xFF
        needle = (
            source[offset - flank : offset]
            + bytes([replacement])
            + source[offset + 1 : offset + 1 + flank]
        )
        for name, donor in donors.items():
            donor_offset = donor.find(needle)
            while donor_offset >= 0:
                matches.append(
                    {
                        "source_offset": f"0x{offset:04X}",
                        "from": f"0x{source[offset]:02X}",
                        "to": f"0x{replacement:02X}",
                        "donor": name,
                        "donor_offset": f"0x{donor_offset + flank:04X}",
                    }
                )
                donor_offset = donor.find(needle, donor_offset + 1)
    return matches


def main() -> int:
    inputs = {
        "roms/jmon22.bin": JMON22.read_bytes(),
        "roms/jmon33.bin": JMON33.read_bytes(),
        "roms/jbasic11.bin": JBASIC11.read_bytes(),
    }
    for name in RELATED_ROM_NAMES[1:]:
        inputs[name] = (ROOT / name).read_bytes()
    require(len(inputs["roms/jmon22.bin"]) == 0x4000, "jmon22 is not 16 KiB")
    require(len(inputs["roms/jmon33.bin"]) == 0x4000, "jmon33 is not 16 KiB")
    require(len(inputs["roms/jbasic11.bin"]) == 0x2000, "jbasic11 is not 8 KiB")
    for name in RELATED_ROM_NAMES:
        require(len(inputs[name]) == 0x4000, f"{name} is not 16 KiB")
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

    donors = {name: inputs[name] for name in RELATED_ROM_NAMES}
    unresolved_audits = []
    for block in (6, 7):
        checksum_delta = (int(after[block]["stored"]) - int(after[block]["computed"])) & 0xFF
        weak_context_matches = contextual_donor_matches(
            original, block, checksum_delta, donors, flank=2
        )
        contextual_matches = contextual_donor_matches(
            original, block, checksum_delta, donors, flank=3
        )
        block_start = block * 0x800
        block_end = (block + 1) * 0x800
        one_bit_candidates = sum(
            (
                original[offset]
                ^ ((original[offset] + checksum_delta) & 0xFF)
            ).bit_count()
            == 1
            for offset in range(block_start, block_end)
        )
        unresolved_audits.append(
            {
                "block": block,
                "checksum_delta": f"0x{checksum_delta:02X}",
                "single_byte_checksum_solutions": 0x800,
                "context_eligible_solutions": sum(
                    offset >= 3 and offset + 3 < len(original)
                    for offset in range(block_start, block_end)
                ),
                "single_bit_subset": one_bit_candidates,
                "exact_two_byte_flank_donor_matches": weak_context_matches,
                "exact_three_byte_flank_donor_matches": contextual_matches,
            }
        )
    require(
        all(not audit["exact_three_byte_flank_donor_matches"] for audit in unresolved_audits),
        "a related ROM now supplies a checksum-closing contextual donor; review it",
    )
    weak_block7 = unresolved_audits[1]["exact_two_byte_flank_donor_matches"]
    require(len(weak_block7) == 6, "the known block-7 short-context collision changed")
    require(
        all(
            match["source_offset"] == "0x3BAA"
            and match["from"] == "0x21"
            and match["to"] == "0xC4"
            and match["donor"].startswith("roms/ekta")
            for match in weak_block7
        ),
        "the known block-7 short-context donor disposition changed",
    )
    require(
        original[0x3BA9:0x3BAF] == bytes.fromhex("21 21 ff 22 31 00"),
        "Monitor 2.2 first-vector initializer changed",
    )
    for match in weak_block7:
        donor_offset = int(match["donor_offset"], 16)
        require(
            donors[match["donor"]][donor_offset - 1 : donor_offset + 5]
            == bytes.fromhex("21 c4 ff 22 01 00"),
            f"{match['donor']} short-context match is no longer the second vector initializer",
        )

    manifest = {
        "schema_version": 2,
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
        "unresolved_block_audit": {
            "related_roms": [
                {"path": name, "sha256": sha256(donors[name])}
                for name in RELATED_ROM_NAMES
            ],
            "context_rule": "replacement byte plus three exact source bytes on each side, searched at every offset in every related ROM; two-byte-flank collisions are retained for false-donor review",
            "blocks": unresolved_audits,
        },
        "provenance_note": {
            "url": CATALOG_URL,
            "first_detailed_commit": CATALOG_PROVENANCE_COMMIT,
            "first_detailed_commit_url": CATALOG_PROVENANCE_URL,
            "retrieved": "2026-07-15",
            "summary": "The JUKUROMS catalog says chip 7 was read with a couple of errors and chip 8 had 50 divergences across seven reads.",
            "public_artifact_boundary": "The public ZIP and upstream Git history contain only the final 16 KiB image, not the per-chip or per-read captures.",
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
            "The detailed warning first appears in upstream commit",
            f"[`{CATALOG_PROVENANCE_COMMIT[:8]}`]({CATALOG_PROVENANCE_URL}). An",
            "audit of that repository's complete path history and the current public",
            "JUKUROMS ZIP found only the final 16 KiB consensus image, not the original",
            "per-chip or per-read files. The highest-value recovery request is therefore",
            "the chip-7 reads and all seven chip-8 reads, including any reader logs or",
            "notes that identify which byte values diverged in each attempt.",
            "",
            "A checksum delta constrains only the sum of a 2 KiB block. It neither",
            "locates damaged bytes nor determines their values, particularly when the",
            "preservation source explicitly reports multiple unstable reads. Blocks 6",
            "and 7 therefore remain untouched until original per-read captures, a stable",
            "independent dump, or another byte-identical firmware source is recovered.",
            "",
            "## Related-ROM donor search",
            "",
            "The audit tests every one-byte checksum repair with three source bytes",
            "available on each side against all seven other tracked 16 KiB monitor/BIOS",
            "images. This covers all 2,048 block-6 positions and 2,045 block-7",
            "positions; only the ROM's final three bytes lack right-hand context. A donor",
            "must contain the proposed replacement byte with the same three bytes on each",
            "side, so a moved routine can match without assuming a fixed ROM address.",
            "",
            "| Block | Required delta | One-byte checksum solutions | Context-tested | One-bit subset | 2-byte-flank matches | 3-byte-flank donors |",
            "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for audit in unresolved_audits:
        lines.append(
            f"| `{audit['block']}` | `+{audit['checksum_delta']}` | "
            f"`{audit['single_byte_checksum_solutions']}` | "
            f"`{audit['context_eligible_solutions']}` | "
            f"`{audit['single_bit_subset']}` | "
            f"`{len(audit['exact_two_byte_flank_donor_matches'])}` | "
            f"`{len(audit['exact_three_byte_flank_donor_matches'])}` |"
        )

    lines.extend(
        [
            "",
            "Block 7's six short-context matches are one false donor repeated across all",
            "six EktaSoft images: changing `0x3BAA` from `0x21` to `0xC4` would close",
            "the checksum, but it would turn Monitor 2.2's first vector initializer from",
            "`LXI H,$FF21; SHLD $0031` into `$FFC4`. The EktaSoft match is its distinct",
            "second initializer, `LXI H,$FFC4; SHLD $0001`; extending the context from",
            "two to three bytes on each side correctly rejects the semantic misalignment.",
            "",
            "The zero three-byte-context result matters in both directions: no tracked",
            "related ROM supplies a checksum-closing byte in matching local code, while the",
            "checksum alone leaves 2,048 possible one-byte edits per block. Block 6 still",
            "has 898 checksum-closing edits that are literal one-bit changes. Choosing",
            "among them from opcode plausibility or later-version address relocation would",
            "be guesswork, and block 7 cannot be repaired by any single-bit edit at all.",
            "The original multi-read captures or a second Monitor 2.2 dump remain required.",
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
