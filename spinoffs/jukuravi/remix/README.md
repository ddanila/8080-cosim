# ekta4401/ekta4402 — EktaSoft #0037 remix ROMs

These implemented 16 KiB images are built deterministically from the pinned
`roms/ekta37.bin`. The design and remaining physical boundary are in:
[`../EKTA37-REMIX-PLAN.md`](../EKTA37-REMIX-PLAN.md).

- Image: [`ekta4401.bin`](ekta4401.bin), SHA256
  `452ecd09406f944162fa2a3e03d52035d86c28e3fc89e77e9abd740644131b18`
- D15 programming image: [`ekta4401-d15.bin`](ekta4401-d15.bin), low 8 KiB,
  SHA256 `f9e92e2032ead817e5d0dc6d42e1ffa8a4c8a71f41e39f36ed58173134be079c`
- D16 programming image: [`ekta4401-d16.bin`](ekta4401-d16.bin), high 8 KiB,
  SHA256 `bf3fca487b20c937c4b2e04c8f89a6ee1b46c49a52f2ea0ed9d56d713c92478b`
- Builder: [`build_ekta4401.py`](build_ekta4401.py) (`--check` verifies the
  committed image rebuilds identically)
- MAME launcher: [`run_mame.sh`](run_mame.sh) selects Ekta4401 with BIOS
  `3.43m_37`; it requires MAME and `roms/jbasic11.bin`. Enter `V` at the
  monitor prompt. The custom-ROM checksum warning is expected. Extra
  arguments are passed to MAME, not used to select Ekta4402.
- Guard: `sync/ekta4401_check.sh`, test
  [`../../../tests/ekta4401_remix_test.py`](../../../tests/ekta4401_remix_test.py)

`ekta4401` is frozen. `ekta4402` adds direct fastboot; both have scoped
CS00015 qualification described under [physical validation](#physical-validation).

- Image: [`ekta4402.bin`](ekta4402.bin), SHA256
  `20ff871307b65523428b6ce21e8153842b54c070cd897826154735af6cea6378`
- D15: [`ekta4402-d15.bin`](ekta4402-d15.bin), SHA256
  `ee87c5b199b409c97909f0eb2b7cfd24cbee2537569bbcdec378631ec8fc85d5`
- D16: [`ekta4402-d16.bin`](ekta4402-d16.bin), SHA256
  `e76587d94189ce8d1cf33ee95cb50f68f5d62280a9dd675ded006eb32232e6e7`
- Builder: [`build_ekta4402.py`](build_ekta4402.py); readable core:
  [`direct-fastboot-v15-core.asm`](direct-fastboot-v15-core.asm)
- Guard:
  [`../../../tests/ekta4402_direct_fastboot_test.py`](../../../tests/ekta4402_direct_fastboot_test.py),
  plus CP/Mish's full V15/NetDisk-v3 prompt and `DIR` regression

Its `#02` banner and new `N fastboot` command identify the change. `N` needs
no Enter: it copies the pinned V15 core to `0100h`, selects D57 mode 2/count 4
and D11 19200/8N1, then receives the normal checked V15 extension and ZX0
stream directly. No stock Janet station request or 9600-baud stage occurs.
Both named halves were fitted and qualified on CS00015. The machine now
uses C8; see [its service record](../../../docs/cs00015-service-record.md).
Direct `N` has booted
CP/M Plus through NetDisk-v3 and N4, and the inherited `J` service has passed
two physical API-v2 attaches with zero transport mismatch.

**These are not factory images.** The stock identity line
`'EktaSoft '88  Serial #0037` is replaced, same length, by
`'EktaSoft&D.Sukharev '26#01` for Ekta4401 or the corresponding `#02` line
for Ekta4402. The file names encode serial **44** (one past #0043, the highest
known factory serial) and build **01** or **02**; 44 is this project's convention, not
a factory-assigned number. No byte of the archival #0037 pair is affected;
that image remains the replica content truth.

## The `J` service command

The floppy subsystem (`2325h-29FFh`) is removed; a Net-only machine. Its
`FF50h+` vectors now point at a `NO DISK - NET ONLY` stub, so the EKDOS
vector contract keeps its shape. The reclaimed space stores the **T36
loader engine verbatim** at its original RAM addresses. The remix builder
rebuilds T36 and copies these segments without modifying their instructions:

The stored ROM addresses below are for **Ekta4401**. Source ranges include
the start and exclude the end; both releases use the same RAM destinations
and copied T36 bytes.

| Segment | T36 source | stored at | copied to | bytes |
| --- | --- | --- | --- | ---: |
| engine | `0A00-0FFD` | ROM `2325h` | `0A00h` | 1533 |
| halt helpers | `06E8-0748` | ROM `2922h` | `06E8h` | 96 |
| refresh + frames | `07A9-0810` | ROM `2982h` | `07A9h` | 103 |
| CRC table | `0900-0A00` | ROM `3B18h` | `0900h` | 256 |
| refresh handler | `1070-1113` | ROM `3C18h` | `1070h` | 67 |

Ekta4402 stores the CRC table at `3B27h` and refresh handler at `3C27h`;
the first three segments remain at the addresses above. Its `J` handler is
at runtime `FCCAh`, versus `FCBBh` in Ekta4401.

`J` disables interrupts, forces **memory mode 1**, copies
the five segments to the exact addresses T36 assembled them for, and jumps
to the loader entry (`0A0Ch`). Mode 1 is the trick that makes this work
with no relocation: it maps ROM only at `D800h-FFFFh`, so the whole low
half is RAM the engine can be copied into and executed from, while the
segments remain readable in mapped ROM during the copy. `J` calls the copied
T36 restore routine at `0CE1h` to program the 8251 and its 2400-baud D57
counter 0 before entering the loader. Service mode is one-way until RESET —
the same contract NetBios has.

## Monitor additions

`H` lists the expanded command set; `V` runs the visual demo. Ekta4402 also
adds `N` for direct fastboot. The builders' metadata records each release's
handler addresses and patch layout.

The 313-byte high-ROM `V` block copies its 291-byte body to hidden low RAM at
`1200h`, disables interrupts, selects all-RAM mode 3, and paints twelve
generated 40x241 write-only frames. Explicit symmetric X distance and scaled
Y distance form moving concentric diamond rings; a dark plaque keeps the
centered `JUKU 2026` mark legible. The demo then clears, restores mode 1,
re-enables interrupts and returns to the monitor. This avoids the mode-1 ROM
overlay, whose high-window writes do not reach the framebuffer.

## Checksum convention

The boot verifier checks **eight 2 KiB chunks in two regions**, with stored
bytes *descending* from a header byte — not the single block-1 sum of the
Jukuravi-era convention:

| Region | Chunks | Stored bytes |
| --- | --- | --- |
| low | `000B-07FF`, `0800-0FFF`, `1000-17FF` | `000A`, `0009`, `0008` |
| upper | `180B-1FFF`, `2000-27FF`, `2800-2FFF`, `3000-37FF`, `3800-3FFF` | `180A`, `1809`, `1808`, `1807`, `1806` |

All eight sums verify against stock ekta37, and the builder regenerates all
eight. A patched image that updates only the block-1 byte fails the ROM's
own verifier and never reaches the command prompt.

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
traffic and do not prove command execution on their own. Enable the frame interrupt (cosim `argv[4]`) so the keyboard is scanned,
and begin typing only after the banner has been painted.

The guard requires `H` to walk the help text, `V` to execute its copied body
and produce accepted framebuffer writes, and `J` to run the service handler
and emit USART traffic against a silent control. It prints the measured
deltas; these are workload observations rather than fixed API values. The
service emits the loader's API-v2 READY frame with a one-vote bootstrap, and
a PTY-attached run stops with the PC inside the copied loader in memory mode 1.

The visual guard captures the first completed frame directly from C-cosim
bus writes after the demo selects mode 3. It compares every framebuffer byte
with the coordinate-based tunnel oracle and independently requires bilateral
symmetry, connected horizontal runs, balanced black/white coverage, the dark
plaque and the exact logo. Byte diversity alone does not establish the
intended image.

## Physical validation

Both named pairs have scoped physical qualification on CS00015. The
Ekta4402 pair was programmed with the Willem's built-in full read/verify;
use the programming-image hashes above to identify the exact halves.

The Ekta4401 pair first booted physically in CS00015. With no display attached,
typing `J` alone (no Enter) entered the resident service loader. The retained session
[`../sessions/cs00015-ekta4401-first-j-physical/`](../sessions/cs00015-ekta4401-first-j-physical/)
attached to API v2, passed PROBE without uploading a payload, and reported 128-row
refresh enabled at `07A9h`, with no transport mismatch. Subsequent retained
sessions uploaded, read back, and executed D57 probes successfully, proving
the complete LOAD → READ → RUN → result path rather than only the READY frame.

Ekta4402's fitted pair passed two no-reset API-v2 attaches, PROBE, and
128-row refresh queries; the second also read 32 bytes from `4000h`.
The [capture record](../sessions/cs00015-ekta4402-j-physical/README.md)
owns the accepted RX/TX and JSON evidence. This qualification
does not independently rerun Ekta4401's uploaded probe matrix.

Direct `N` on the same fitted pair also physically boots the separately
maintained CP/M Plus image, reaches NetDisk-v3/N4 service, and recovers from a
fresh stateless host replacement without resetting the machine. Those system
and timing records belong to `cpm-plus-juku`.

Program both named D15/D16 files: D15 carries the banner and table pointer,
while D16 carries the copied loader segments and H/J/V code. Never load the
combined 16 KiB image into either 8 KiB device.

## Still open

The prepared normal-raster retention experiment has not been run on either
CS00015 or CS00024. It remains the next cross-board control for deciding
whether the normal display slot path preserves DRAM when T36 software refresh
is suspended; see
[`../RASTER-REFRESH-EXPERIMENT.md`](../RASTER-REFRESH-EXPERIMENT.md).
