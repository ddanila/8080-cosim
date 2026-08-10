#!/usr/bin/env python3
"""Pin the curated CS00024 T34 boot and CONFIG-first discriminator evidence."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "spinoffs" / "jukuravi" / "sessions"
CASES = (
    (
        "cs00024-t34-20260809",
        "20260809T055628.869126Z.json",
        "ok",
        "00",
        (),
    ),
    (
        "cs00024-t34-full/cold-loader-probe",
        "20260809T060236.505488Z.json",
        "error",
        "10",
        ("0006373F000000000034",) * 3,
    ),
    (
        "cs00024-t34-full/cold-loader-probe-g12",
        "20260809T060417.872163Z.json",
        "error",
        "10",
        ("0006373F0000000000B4",),
    ),
    (
        "cs00024-t34-full/config-first-v1",
        "20260809T060703.043231Z.json",
        "ok",
        "10",
        (),
    ),
)


def main() -> int:
    d57_results: list[bool] = []
    for relative, filename, status, bitmap, strong_crc in CASES:
        directory = SESSIONS / relative
        path = directory / filename
        if not path.is_file():
            raise SystemExit(f"JUKURAVI-T34-PHYSICAL: missing {path}")
        summary = json.loads(path.read_text())
        if summary.get("status") != status:
            raise SystemExit(f"JUKURAVI-T34-PHYSICAL: {relative} status differs")
        image = summary.get("image", {})
        if image.get("rom_version") != 0x1C or image.get("crc16") != "A637":
            raise SystemExit(f"JUKURAVI-T34-PHYSICAL: {relative} identity differs")
        diagnostic = summary.get("diagnostic_status", {})
        if diagnostic.get("peripheral_fault_mask_hex") != bitmap:
            raise SystemExit(f"JUKURAVI-T34-PHYSICAL: {relative} bitmap differs")
        for name in ("pic", "ppi", "d54", "d55", "ram_4000", "ram_c000"):
            if diagnostic.get(name) is not True:
                raise SystemExit(
                    f"JUKURAVI-T34-PHYSICAL: {relative} {name} did not pass"
                )
        d57_results.append(diagnostic.get("d57") is True)
        observed_strong = tuple(
            frame["payload_hex"]
            for frame in summary.get("frames", [])
            if frame.get("type") == "0xB0"
            and str(frame.get("payload_hex", "")).startswith("0006")
        )
        if observed_strong != strong_crc:
            raise SystemExit(
                f"JUKURAVI-T34-PHYSICAL: {relative} strong CRC differs: "
                f"{observed_strong!r}"
            )
        for key in ("rx_log", "tx_log"):
            log_name = summary.get(key)
            log = directory / log_name if isinstance(log_name, str) else None
            if log is None or not log.is_file() or not log.stat().st_size:
                raise SystemExit(
                    f"JUKURAVI-T34-PHYSICAL: {relative} lacks nonempty {key}"
                )

    config = json.loads((SESSIONS / CASES[-1][0] / CASES[-1][1]).read_text())
    frames = {
        (frame.get("type"), frame.get("payload_hex"))
        for frame in config.get("frames", [])
    }
    if ("0xB0", "FE002404000001000000") not in frames:
        raise SystemExit("JUKURAVI-T34-PHYSICAL: seven-vote CONFIG success is absent")
    if ("0xB1", "0000230000085432380055AAC6C7") not in frames:
        raise SystemExit("JUKURAVI-T34-PHYSICAL: one-vote exact PROBE is absent")
    if d57_results != [True, False, False, False]:
        raise SystemExit(f"JUKURAVI-T34-PHYSICAL: D57 sequence differs: {d57_results}")

    print(
        "JUKURAVI-T34-PHYSICAL: PASS "
        "(4 corrected-D55 passes; intermittent D57; repeated long-command CRC; "
        "CONFIG-first exact PROBE)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
