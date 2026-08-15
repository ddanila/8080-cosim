#!/usr/bin/env python3
"""Guard cosim's optional real-time pacing (JUKU_REALTIME_HZ).

Unset, the simulator runs as fast as the host allows -- the right default for
tests. Set, it paces execution so wall-clock time equals machine time, which
is what makes a simulated session comparable with a stopwatch on the bench.

The checks are deliberately loose on the fast side and tight on the slow
side: a pacer may never make a session finish early (that would mean the
model is not actually waiting), while a busy CI host is allowed to run late.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "roms" / "ekta37.bin"
NOMINAL_HZ = 2_000_000          # Juku clock; ref/juku-machine-facts.json
CYCLES = 4_000_000              # 2.0 s of machine time


def fail(message: str) -> None:
    print(f"COSIM-REALTIME-TEST: FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def run(trace: Path, hz: str | None) -> float:
    environment = os.environ.copy()
    environment.pop("JUKU_REALTIME_HZ", None)
    if hz is not None:
        environment["JUKU_REALTIME_HZ"] = hz
    started = time.monotonic()
    completed = subprocess.run(
        [str(trace), str(ROM), str(CYCLES)],
        cwd=ROOT, env=environment, capture_output=True, text=True,
        timeout=300, check=False,
    )
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        fail(f"cosim exited {completed.returncode}: {completed.stderr[-300:]}")
    return elapsed


def main() -> int:
    if len(sys.argv) != 2:
        fail("usage: test.py /path/to/cosim-trace")
    trace = Path(sys.argv[1]).resolve()
    if not trace.is_file():
        fail("missing cosim executable")

    expected = CYCLES / NOMINAL_HZ

    unpaced = run(trace, None)
    if unpaced > expected / 2:
        fail(
            f"unpaced run took {unpaced:.2f}s; pacing must stay opt-in so the "
            "test suite keeps running at full speed"
        )

    for value in ("1", str(NOMINAL_HZ)):
        paced = run(trace, value)
        if paced < expected * 0.95:
            fail(
                f"JUKU_REALTIME_HZ={value} finished in {paced:.2f}s, faster "
                f"than the {expected:.2f}s of machine time it represents"
            )
        if paced > expected * 3:
            fail(f"JUKU_REALTIME_HZ={value} took {paced:.2f}s, far over "
                 f"{expected:.2f}s (host too loaded, or pacing is wrong)")

    # A rate an order of magnitude faster must take proportionally less time.
    fast = run(trace, str(NOMINAL_HZ * 10))
    if fast > expected * 0.75:
        fail(f"a 10x rate took {fast:.2f}s; pacing does not scale with the rate")

    bad = subprocess.run(
        [str(trace), str(ROM), "1000"],
        cwd=ROOT, env={**os.environ, "JUKU_REALTIME_HZ": "banana"},
        capture_output=True, text=True, timeout=60, check=False,
    )
    if bad.returncode != 2 or "invalid JUKU_REALTIME_HZ" not in bad.stderr:
        fail("a malformed rate must be rejected with exit code 2")

    history = subprocess.run(
        [str(trace), str(ROM), "1000"], cwd=ROOT,
        env={**os.environ, "JUKU_PC_HISTORY": "1"},
        capture_output=True, text=True, timeout=60, check=False,
    )
    marker = "[EXEC] recent PCs:"
    lines = [line for line in history.stderr.splitlines()
             if line.startswith(marker)]
    if history.returncode != 0 or len(lines) != 1:
        fail("JUKU_PC_HISTORY did not emit one bounded execution history")
    addresses = lines[0][len(marker):].split()
    if not addresses or len(addresses) > 256 or any(
            len(address) != 4 for address in addresses):
        fail("JUKU_PC_HISTORY emitted malformed or unbounded addresses")

    print(
        f"COSIM-REALTIME-TEST: PASS (unpaced {unpaced:.2f}s, "
        f"paced {expected:.2f}s of machine time honoured)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
