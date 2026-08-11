# ekta4401 — the EktaSoft #0037 remix ROM

Phase 1 + 2 complete, 2026-08-11. A derived 16 KiB image built deterministically
from the pinned `roms/ekta37.bin`. Plan and phase results:
[`../EKTA37-REMIX-PLAN.md`](../EKTA37-REMIX-PLAN.md).

- Image: [`ekta4401.bin`](ekta4401.bin), SHA256
  `1b6f5c752c438c0b9bafbe78c4db7b789468e46036ec5b7ea77b86d8190f70b5`
- Builder: [`build_ekta4401.py`](build_ekta4401.py) (`--check` verifies the
  committed image rebuilds identically)
- Guard: `sync/ekta4401_check.sh`, test
  [`../../../tests/ekta4401_remix_test.py`](../../../tests/ekta4401_remix_test.py)

**This is not a factory image.** Its banner says so: the stock identity line
`'EktaSoft '88  Serial #0037` is replaced, same length, by
`'EktaSoft&D.Sukharev '26#01` — the co-author is named in the banner and the
year is '26. The file name encodes serial **44** (one past #0043, the highest
known factory serial) and build **01**; 44 is this project's convention, not
a factory-assigned number. No byte of the archival #0037 pair is affected;
that image remains the replica content truth.

## Phase 2 content — the `J` service command

The floppy subsystem (`2325h-29FFh`) is removed; a Net-only machine. Its
`FF50h+` vectors now point at a `NO DISK - NET ONLY` stub, so the EKDOS
vector contract keeps its shape. The reclaimed space stores the **T36
loader engine verbatim** — never relocated, never re-assembled:

| Segment | T36 source | stored at | copied to | bytes |
| --- | --- | --- | --- | ---: |
| engine | `0A00-0FFD` | ROM `2325h` | `0A00h` | 1533 |
| halt helpers | `06E8-0748` | ROM `2922h` | `06E8h` | 96 |
| refresh + frames | `07A9-0810` | ROM `2982h` | `07A9h` | 103 |
| CRC table | `0900-0A00` | ROM `39D7h` | `0900h` | 256 |
| refresh handler | `1070-1113` | ROM `3AD7h` | `1070h` | 163 |

`J` (runtime `FB7Ah`) disables interrupts, forces **memory mode 1**, copies
the five segments to the exact addresses T36 assembled them for, and jumps
to the loader entry (`0A0Ch`). Mode 1 is the trick that makes this work
with no relocation: it maps ROM only at `D800h-FFFFh`, so the whole low
half is RAM the engine can be copied into and executed from, while the
segments remain readable in mapped ROM during the copy. The engine brings
up the 8251 and its 2400-baud D57 counter 0 itself (T36 `0CE0h`), so `J`
hands over nothing but the machine. Service mode is one-way until RESET —
the same contract NetBios has.

Total Phase 2 footprint: 1,732 B in the reclaimed floppy region and 500 B
in the `F900h` gap, which still leaves 719 B free.

## Phase 1 content

| Change | ROM bytes |
| --- | --- |
| Banner identity line | `00DF-00F9` (in place, same length) |
| Command dispatch table relocated + `H` added | `3900-3937` (runtime `F900h`) |
| `H` handler (`LXI B,text` / `CALL DA6Bh` / `RET`) | `3931-3937` |
| Help text | `3938-39CB` |
| Table pointer repointed (`LXI H,F900h`) | `1924-1925` |
| Eight chunk checksums regenerated | `0008-000A`, `1806-180A` |

Everything else is byte-identical to ekta37. Total footprint of the new
code and data: 203 bytes in the `3900h` free gap, leaving 1,263 bytes of it
for the Phase 2 Jukuravi module.

## Checksum convention (recovered here)

The boot verifier checks **eight 2 KiB chunks in two regions**, with stored
bytes *descending* from a header byte — not the single block-1 sum of the
Jukuravi-era convention:

| Region | Chunks | Stored bytes |
| --- | --- | --- |
| low | `000B-07FF`, `0800-0FFF`, `1000-17FF` | `000A`, `0009`, `0008` |
| upper | `180B-1FFF`, `2000-27FF`, `2800-2FFF`, `3000-37FF`, `3800-3FFF` | `180A`, `1809`, `1808`, `1807`, `1806` |

All eight sums verify against stock ekta37, and the builder regenerates all
eight. A patched image that updates only the block-1 byte fails the ROM's
own verifier and never reaches the command prompt — observed during Phase 1.

## Validation

Static: rebuild identity, a bounded patch set (any byte changed outside the
listed ranges fails), all eight chunk checksums, the banner identity, and
**every stock command still dispatching to its original handler**.

Behavioral (cosim): three boots — a keyless control, `H`, and `J` — with
every count taken as a **difference from the control**. This matters: the
console renders through the same `D800h+` window the relocated code
occupies, so absolute read counts there are dominated by framebuffer
traffic and prove nothing on their own (an earlier version of this guard
was green for exactly that wrong reason). Two further harness facts are
load-bearing: the frame interrupt must be enabled (cosim `argv[4]`) or the
keyboard is never scanned and no command dispatches at all, and typing only
begins once the banner has been painted.

Current signals: `H` reads the help text region **+156 bytes** over control
(its length is 148), `J` reads its handler region **+21,587** and produces
**21,932 USART events** where the control run produces exactly zero. The
transmitted bytes are the loader's own READY frame
(`A5 5A A3 0B 02 20 0A 00 7F FF ...` — API v2, capabilities, workspace,
one-vote bootstrap), and a PTY-attached run stops with the PC inside the
copied loader in memory mode 1.

## Not yet done

A complete `host.py` session against the `J` service inside cosim (PROBE →
CONFIG → LOAD → RUN) has **not** been demonstrated yet: the loader is
proven alive and transmitting, but the PTY orchestration in the harness
still needs work (the host must attach only after `J` has been typed, and
the detector must not consume the frames the host needs). Until that lands,
treat the loader path as *starts and speaks*, not *fully handshakes*.

No physical burn has happened; the image is desk-validated only. Burning
touches both chips: D15 carries the banner and table pointer, D16 the
segments, the H/J code and the stubs.
