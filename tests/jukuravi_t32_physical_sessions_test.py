#!/usr/bin/env python3
"""Pin the curated CS00015 T32 result blocks used by the diagnosis."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "spinoffs" / "jukuravi" / "sessions"

EXPECTED = {
    "t32-ram-a12-write-map-physical":
        "5731324DA5040000102166C7101166C71011202110111011101110112011201120112011"
        "708166C7708180817071808170717071707170718071807180718071",
    "t32-ram-a12-lhld-classes-physical":
        "4C313243A504000010112021101110111011101120112011201120113031404130313031"
        "3031303140314031403140315051606150515051505150516051605160516051707180"
        "8170717071707170718071807180718071",
    "t32-ram-a12-instruction-classes-physical":
        "49313243A555555510112011303140315051606150BBAA615555555555555555",
    "t32-ram-a12-boundary-physical":
        "42313243A55555551F202F4055555555",
    "t32-ram-a12-ready-classes-low-result-physical":
        "52313243A5045555101120212011201120112011303140414031403140314031505160"
        "616051605160516051707180818071807180718071",
    "t32-rom-overlay-source-repeat-sameboot-physical":
        "4F564C5908A5B1B33E1A66C76621668166C766C73E433E433E433E433E433E433E43"
        "3E433E813E813E813E813E813E813E813E8166216681",
    "t32-rom-overlay-source-repeat2-sameboot-physical":
        "4F564C5908A5B1B33E1A66C76621668166C766C73E433E433E433E433E433E433E43"
        "3E433E813E813E813E813E813E813E813E8166216681",
    "t32-ram-a12-increment-registers-physical":
        "58313243A55555550010010A014A018A011A555555555555",
    "t32-ram-a12-increment-registers-repeat-physical":
        "58313243A55555550010010A014A018A011A555555555555",
    "t32-ram-a12-increment-registers-cpu-replacement-physical":
        "58313243A55555550010011A015A019A011A555555555555",
    "t32-rom-read-pair-1000-physical":
        "50414952100000C010A5" + "000B" * 16,
    "t32-rom-read-pair-1100-physical":
        "5041495211003E1110A5" + "3E17" * 16,
    "t32-rom-read-pair-1200-physical":
        "5041495212003E1210A5" + "3E02" * 16,
    "t32-rom-read-pair-1400-physical":
        "5041495214003E1410A5" + "3EE6" * 16,
}


def main() -> int:
    for name, expected in EXPECTED.items():
        session_dir = SESSIONS / name
        summaries = list(session_dir.glob("*.json"))
        if len(summaries) != 1:
            raise SystemExit(f"JUKURAVI-T32-PHYSICAL: {name} has {len(summaries)} summaries")
        summary = json.loads(summaries[0].read_text())
        if summary.get("status") != "ok":
            raise SystemExit(f"JUKURAVI-T32-PHYSICAL: {name} is not successful")
        mismatches = summary.get("host_transport", {}).get("handshake_mismatches")
        if mismatches != []:
            raise SystemExit(f"JUKURAVI-T32-PHYSICAL: {name} has transport mismatches")
        observed = summary.get("loader", {}).get("run", {}).get("result", {}).get("hex")
        if observed != expected:
            raise SystemExit(
                f"JUKURAVI-T32-PHYSICAL: {name} differs: "
                f"expected {expected}, got {observed}"
            )
        for log_key in ("rx_log", "tx_log"):
            log_name = summary.get(log_key)
            log_path = session_dir / log_name if isinstance(log_name, str) else None
            if log_path is None or not log_path.is_file() or not log_path.stat().st_size:
                raise SystemExit(
                    f"JUKURAVI-T32-PHYSICAL: {name} lacks nonempty {log_key}"
                )

    increment_names = (
        "t32-ram-a12-increment-registers-physical",
        "t32-ram-a12-increment-registers-repeat-physical",
        "t32-ram-a12-increment-registers-cpu-replacement-physical",
    )
    increment_summaries = [
        json.loads(next((SESSIONS / name).glob("*.json")).read_text())
        for name in increment_names
    ]
    for summary in increment_summaries:
        image = summary.get("image", {})
        if image.get("rom_version") != 0x1B or image.get("crc16") != "D62B":
            raise SystemExit("JUKURAVI-T32-PHYSICAL: direct probe identity differs")
    probe_hashes = {summary.get("loader", {}).get("sha256")
                    for summary in increment_summaries}
    if probe_hashes != {
        "531aac5aa6678a31e62aef43dc36bb47a8be398a5adb9dd3d714d57f468418ea"
    }:
        raise SystemExit("JUKURAVI-T32-PHYSICAL: direct probe hash differs")
    print(f"JUKURAVI-T32-PHYSICAL: PASS ({len(EXPECTED)} curated sessions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
