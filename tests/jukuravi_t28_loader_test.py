#!/usr/bin/env python3
"""Exercise the exact T28 ROM through the real host CLI and PTY model."""

from __future__ import annotations

import json
import os
import pty
import subprocess
import sys
import tempfile
import tty
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "spinoffs" / "jukuravi" / "host.py"
FIRMWARE = ROOT / "spinoffs" / "jukuravi" / "firmware"
sys.path[:0] = [str(FIRMWARE), str(FIRMWARE.parent)]
import build_d0_buffer_verified as firmware  # noqa: E402


def fail(message: str) -> None:
    print(f"JUKURAVI-T28-LOADER: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 3:
        fail("usage: test.py /path/to/trace diag-d0-buffer-verified.bin")
    trace, rom_arg = (Path(value).resolve() for value in sys.argv[1:])
    image, metadata = firmware.build()
    if not trace.is_file() or rom_arg.read_bytes() != image:
        fail("trace or exact T28 image differs")

    with tempfile.TemporaryDirectory(prefix="jukuravi-t28-") as temp_name:
        temp = Path(temp_name)
        rom = temp / "t28.bin"
        payload = temp / "heartbeat.bin"
        logs = temp / "logs"
        rom.write_bytes(image)
        payload.write_bytes((FIRMWARE / "heartbeat-4000.bin").read_bytes())

        master, slave = pty.openpty()
        tty.setraw(slave)
        environment = os.environ.copy()
        environment.update(
            JUKU_USART_PTY=os.ttyname(slave),
            JUKU_USART_TRANSFER_CYCLES="64",
            JUKU_USART_BYTE_CYCLES="512",
            JUKU_RAM_DROP_WRITE="C000:25:1",
        )
        with (temp / "cosim.stdout").open("wb") as stdout, (
            temp / "cosim.stderr"
        ).open("wb") as stderr:
            cosim = subprocess.Popen(
                [str(trace), str(rom), "5000000000"],
                cwd=temp,
                env=environment,
                stdout=stdout,
                stderr=stderr,
            )
        try:
            host = subprocess.run(
                [
                    sys.executable,
                    str(HOST),
                    "--fd",
                    str(master),
                    "--timeout",
                    "60",
                    "--banner-timeout",
                    "30",
                    "--loader-timeout",
                    "30",
                    "--loader-guard-ms",
                    "0",
                    "--loader-chunk-size",
                    "17",
                    "--loader-votes",
                    "3",
                    "--expect-rom-version",
                    f"{firmware.ROM_VERSION:02X}",
                    "--expect-crc16",
                    f"{int(metadata['checksum']):04X}",
                    "--load",
                    str(payload),
                    "--load-address",
                    "4000",
                    "--run-address",
                    "4000",
                    "--run-mode",
                    "jump",
                    "--heartbeat-count",
                    "3",
                    "--heartbeat-timeout",
                    "5",
                    "--log-dir",
                    str(logs),
                ],
                cwd=ROOT,
                pass_fds=(master,),
                text=True,
                capture_output=True,
                timeout=300,
            )
        finally:
            cosim.terminate()
            try:
                cosim.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cosim.kill()
                cosim.wait()
            os.close(master)
            os.close(slave)

        if host.returncode:
            fail(f"real CLI failed:\n{host.stdout}{host.stderr}")
        summaries = list(logs.glob("*.json"))
        if len(summaries) != 1:
            fail("real CLI did not retain one evidence summary")
        summary = json.loads(summaries[0].read_text())
        loader = summary.get("loader")
        if not isinstance(loader, dict):
            fail("loader evidence is missing")
        ready = loader.get("ready")
        if not isinstance(ready, dict) or ready.get("api_version") != 2:
            fail(f"T28 capability evidence differs: {ready!r}")
        if loader.get("probe", {}).get("cookie_hex") != "5432380055AAC6C7":
            fail("exact PROBE echo evidence is absent")
        if loader.get("config", {}).get("votes") != 3:
            fail("host-selected vote count was not acknowledged")
        chunks = loader.get("chunks")
        if not isinstance(chunks, list) or len(chunks) != 7:
            fail(f"17-byte chunking evidence differs: {chunks!r}")
        if any(
            chunk.get("status") != "ok"
            or chunk.get("verified") is not True
            or chunk.get("bytes", 0) > 17
            for chunk in chunks
        ):
            fail(f"LOAD/readback evidence differs: {chunks!r}")
        if chunks[0].get("store_retries") != 1 or any(
            chunk.get("store_retries") for chunk in chunks[1:]
        ):
            fail(f"one-shot parser-store recovery evidence differs: {chunks!r}")
        if not loader.get("run", {}).get("acknowledged"):
            fail("transaction-correlated RUN was not acknowledged")
        if loader.get("heartbeat", {}).get("received") != 3:
            fail("uploaded arbitrary code did not emit three heartbeats")

    print(
        "JUKURAVI-T28-LOADER: PASS "
        "(PROBE; CONFIG; chunked LOAD; exact READ; RUN; heartbeats)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
