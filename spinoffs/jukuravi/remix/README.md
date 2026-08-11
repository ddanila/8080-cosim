# ekta4401 — the EktaSoft #0037 remix ROM

Phases 1 + 2 and the visual easter egg are complete, 2026-08-12. A derived 16 KiB image built deterministically
from the pinned `roms/ekta37.bin`. Plan and phase results:
[`../EKTA37-REMIX-PLAN.md`](../EKTA37-REMIX-PLAN.md).

- Image: [`ekta4401.bin`](ekta4401.bin), SHA256
  `452ecd09406f944162fa2a3e03d52035d86c28e3fc89e77e9abd740644131b18`
- D15 programming image: [`ekta4401-d15.bin`](ekta4401-d15.bin), low 8 KiB,
  SHA256 `f9e92e2032ead817e5d0dc6d42e1ffa8a4c8a71f41e39f36ed58173134be079c`
- D16 programming image: [`ekta4401-d16.bin`](ekta4401-d16.bin), high 8 KiB,
  SHA256 `bf3fca487b20c937c4b2e04c8f89a6ee1b46c49a52f2ea0ed9d56d713c92478b`
- Builder: [`build_ekta4401.py`](build_ekta4401.py) (`--check` verifies the
  committed image rebuilds identically)
- MAME launcher: [`run_mame.sh`](run_mame.sh) (run without arguments, then
  enter `V` at the monitor prompt; MAME's custom-ROM checksum warning is
  expected)
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
| CRC table | `0900-0A00` | ROM `3B18h` | `0900h` | 256 |
| refresh handler | `1070-1113` | ROM `3C18h` | `1070h` | 163 |

`J` (runtime `FCBBh`) disables interrupts, forces **memory mode 1**, copies
the five segments to the exact addresses T36 assembled them for, and jumps
to the loader entry (`0A0Ch`). Mode 1 is the trick that makes this work
with no relocation: it maps ROM only at `D800h-FFFFh`, so the whole low
half is RAM the engine can be copied into and executed from, while the
segments remain readable in mapped ROM during the copy. `J` calls the copied
T36 restore routine at `0CE1h` to program the 8251 and its 2400-baud D57
counter 0 before entering the loader. Service mode is one-way until RESET —
the same contract NetBios has.

Total Phase 2 footprint: 1,732 B in the reclaimed floppy region and 532 B
in the `F900h` gap. Together with Phase 1 and `V`, the image still has 395 B
free there.

## Phase 1 content

| Change | ROM bytes |
| --- | --- |
| Banner identity line | `00DF-00F9` (in place, same length) |
| Command dispatch table relocated + `H`, `J`, `V` added | `3900-3937` (runtime `F900h`) |
| `H` handler (`LXI B,text` / `CALL DA6Bh` / `RET`) | `3937-393E` |
| Help text, including `V ?` | `393E-39DF` |
| `V` diamond-tunnel demo + `JUKU 2026` mark | `39DF-3B18` |
| Table pointer repointed (`LXI H,F900h`) | `1924-1925` |
| Eight chunk checksums regenerated | `0008-000A`, `1806-180A` |

The table, help and visual block occupies 536 bytes of the `3900h` free gap.
The 313-byte high-ROM `V` block copies its 291-byte body to hidden low RAM at
`1200h`, disables interrupts, selects all-RAM mode 3, and paints twelve
generated 40x241 write-only frames. Explicit symmetric X distance and scaled
Y distance form moving concentric diamond rings; a dark plaque keeps the
centered `JUKU 2026` mark legible. The demo then clears, restores mode 1,
re-enables interrupts and returns to the monitor. This avoids the mode-1 ROM
overlay, whose high-window writes do not reach the framebuffer.

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
**every stock command still dispatching to its original handler**. The two
8 KiB programming images are guarded as the exact low/high split and their
concatenation must reproduce the 16 KiB image byte-for-byte.

Behavioral (cosim): four boots — a keyless control, `H`, `V`, and `J` — with
every count taken as a **difference from the control**. This matters: the
console renders through the same `D800h+` window the relocated code
occupies, so absolute read counts there are dominated by framebuffer
traffic and prove nothing on their own (an earlier version of this guard
was green for exactly that wrong reason). Two further harness facts are
load-bearing: the frame interrupt must be enabled (cosim `argv[4]`) or the
keyboard is never scanned and no command dispatches at all, and typing only
begins once the banner has been painted.

Current signals: `H` reads the help text region **+161 bytes** over control;
`V` adds **3,213** mapped-ROM reads, **1,988,036** copied-body reads and
**127,494 accepted framebuffer writes**;
`J` reads its handler region **+21,590** and produces
**22,178 USART events** where the control run produces exactly zero. The
transmitted bytes are the loader's own READY frame
(`A5 5A A3 0B 02 20 0A 00 7F FF ...` — API v2, capabilities, workspace,
one-vote bootstrap), and a PTY-attached run stops with the PC inside the
copied loader in memory mode 1.

The visual guard captures the first completed frame directly from C-cosim
bus writes after the demo selects mode 3. It compares every framebuffer byte
with the coordinate-based tunnel oracle and independently requires bilateral
symmetry, connected horizontal runs, balanced black/white coverage, the dark
plaque and the exact logo. This was added after MAME and C-cosim both exposed
the first address-hash implementation as a screen of repeated glyph-like
tiles; byte diversity alone had incorrectly accepted that version.

## Physical validation

The immediately preceding image (`20a9c25b...`) was programmed into both
AT28C64 devices on 2026-08-11 with the DOSRAVI/Willem controlled-write path.
D15 changed 8,167 bytes and D16 changed
8,173; Willem's built-in post-write read verified all 8,192 bytes of each
image with zero retries and left VCC/VPP off. The verified CRC32 values were
`5E306759` and `3B734DEC`, matching that image's D15/D16 halves. The current
image adds the deterministic `CALL 0CE1h` serial/PIT restore before loader
entry and therefore has not yet been programmed physically; both current
halves must be burned because the upper-ROM checksum byte also changes D15.
The first D15 operation took about 393 seconds, outlasting the host's former
300-second EXEC wait; its persistent execution ID allowed the completed result
to be retrieved without programming twice. D16 used a 900-second bound.

The pair then booted physically in CS00015. With no display attached, typing
`J` alone (no Enter) entered the resident service loader. The retained session
[`../sessions/cs00015-ekta4401-first-j-physical/`](../sessions/cs00015-ekta4401-first-j-physical/)
attached to API v2, passed PROBE without changing RAM, and reported 128-row
refresh enabled at `07A9h`, with no transport mismatch. Subsequent retained
sessions uploaded, read back, and executed D57 probes successfully, proving
the complete LOAD → READ → RUN → result path rather than only the READY frame.

The service design therefore has both deterministic desk validation and
physical validation of its preceding byte image. Burning always touches both
chips: D15 carries the
banner and table pointer, while D16 carries the copied loader segments and the
H/J/V code. Program the named D15/D16 files; never load the combined 16 KiB
image into either 8 KiB device.

## Still open

The prepared normal-raster retention experiment has not been run on either
CS00015 or CS00024. It remains the next cross-board control for deciding
whether the normal display slot path preserves DRAM when T36 software refresh
is suspended; see
[`../RASTER-REFRESH-EXPERIMENT.md`](../RASTER-REFRESH-EXPERIMENT.md).
