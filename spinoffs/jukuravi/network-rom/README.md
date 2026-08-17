# Juku network-first ROM

Status: **CS00015 BENCH CANDIDATE C4 — PHYSICAL QUALIFICATION PENDING**

This directory is the from-scratch successor to the frozen Ekta4401 monitor
and physically qualified Ekta4402 direct-fastboot/service ROM. The product
goal is a network-only ROM which performs bounded POST, boots automatically at 19,200
baud, exposes common platform services from its resident 10 KiB, and gives
CP/M Plus a larger TPA. The accepted staged plan and budgets live in the
`cpm-plus-juku` repository.

The present image, named `network-first-abi1-cs00015-c4`, proves the versioned
ROM ABI, reset/POST path, keyless V15
boot, resident serial initialization, shared keyboard, and compact console. Its
dedicated CP/M Plus consumer reaches `A>`, accepts `DIR` and `DIAG CPU` through
that keyboard, and completes both commands. Its split files test exact EPROM
geometry. Resident services, reset-side hardware state, and the simulated
recovery matrix are complete, so its metadata now permits controlled
CS00015 bench qualification. It is not a generally qualified release until the physical
matrix passes.

C4 supersedes the immutable C3 package but keeps both ROM halves byte-identical.
The first blind C3 run on CS00015 proved automatic reset, V15 loading, resident
console output, and NetDisk operation, then exposed a bug in its matching
CP/M binding: it entered the resident ROM's blocking local `CONIN` before a
later N4 byte could be polled. The corrected binding checks resident `CONSTAT`
and keeps polling N4 while the local keyboard is idle. On the same installed
C3 ROM pair, the corrected C4 runtime completed remote `DIR`, `DIAG CPU`,
explicit `WBOOT`, and another `DIR` with no retry or overrun. Thus no EPROM
rewrite is required when moving from C3 to C4; the new candidate name freezes
the corrected matching runtime.

The separately named `network-first-abi1.1-cs00015-c5-desk` image is the next
desk-qualified candidate; it does not replace or mutate C4. ABI 1.1 places
licensed Estonian and CP866 Russian extensions plus the connected CP437 UI
bank in the reserved `F000h..F7FFh` region. S21 bits 4:3 select English,
Estonian, Russian, or the English/user fallback through one renderer. Two
appended vectors return the reset-latched S21 configuration and install up to
four persistent key substitutions. S21 bit 0 set enters network boot
immediately; clear waits at a concealed local `N` recovery gate. The C model
proves both policy branches, a `T` to `X` remap, and exact locale pixels in
all four S21 bits-2:1 geometries: 40x24, 53x24, 64x20, and 80x24. Physical
qualification remains before C5 can become a bench candidate.

C3 had superseded the immutable C2 package. C2 corrected the original sprite-sheet
extraction after a stock-ROM/manual-resume CS00015 run exposed deterministic
bad glyphs. C3 replaces that wide font with the MIT-licensed Creep 0.31 ASCII
adaptation used by the all-RAM CP/M console and halves the cursor phase from
1,024 to 512 idle polls. Its letters retain a blank separator column. The
all-RAM CP/M path additionally supports the S21-selected historical video
modes; ABI 1.0 intentionally keeps the immutable C4 baseline fixed at 80x24,
while ABI 1.1 C5 now applies the same selection in resident ROM.
C2 and C3 changed D15 only; C4 changes neither half. D16 remains
byte-identical to C1.

## Build and test

```sh
python3 spinoffs/jukuravi/network-rom/build_network_rom.py
sync/network_first_rom_abi_check.sh
sync/network_first_rom_hdl_check.sh
cd ../cpm-plus-juku && make network-rom-cosim-check
```

Committed deterministic artifacts:

- `juku-network-rom-abi1.bin`: combined 16 KiB image;
- `juku-network-rom-abi1-d15.bin`: exact low 8 KiB half;
- `juku-network-rom-abi1-d16.bin`: exact high 8 KiB half;
- `juku-network-rom-abi1.json`: candidate name, hashes, sizes, ABI identity,
  and physical-qualification status.
- `juku-network-rom-abi1.1-c5{,-d15,-d16}.bin` and matching JSON: separate
  locale/remap/boot-policy desk candidate; never aliases the immutable C4
  files.

The builder stores a 196-byte gate and 119-byte mode-3 helper for C4, or a
214-byte gate and exactly 128-byte geometry-aware helper for C5, in boot-only
ROM. Reset configures D27 as all-input, D26 as keyboard/memory-mode I/O with
PC7 safely high, the stock D54/D55/D57 raster/refresh chain, and the 8259 in
the original MCS-80 vector form with every source masked. It then runs CPU,
RAM-data, RAM-address, complete-ROM, and D57/D11 checks. Status `00h` or
distinct failure `C1h`..`C5h` is retained at `D610h`.
The complete 16 KiB image has a zero additive checksum, including the boot
code, stored loaders, gate, helper, and resident window.

On success the ROM copies the gate to `D620h`, the helper to `D700h`, and a
141-byte V15 receive core to `0100h`. A transition stub at `D600h` selects
mode 1 and enters the core. It configures proven D57 mode 2/count 4 and D11
19,200/8N1, emits target-ready byte `C4h`, accepts the checked extension, and
hands it the compressed CP/M Plus system. The host observes C4 under normal
reset timing; if a restarted server missed it, synchronized V15 probes recover
without another RESET.

The resident manifest is fixed at `FF00h`; stable three-byte vectors begin at
`FF20h`. The dedicated CP/M Plus image remains in mode 1, validates the ABI,
delegates serial initialization, polled keyboard input, the selected console, and
bounded NetDisk-v3 read-ahead and synchronous write-through transactions. The
normal all-RAM image remains a byte-exact comparison baseline. The relinked
consumer exposes a measured 39,168-byte transient span, exactly 8 KiB above
that baseline.

The resident advertises console, serial, keyboard, NetDisk, and diagnostic feature bits. It
programs the proven D57 mode-2/count-4 19,200-baud clock, supports bounded 8251
send/receive, reuses the shared 15-column keyboard scanner and translation
tables with three mutable bytes in low RAM, publishes build/workspace/helper
metadata, supplies the Creep-derived 5x7 text policy, and calls the copied
helper for mode-3 clear, scroll, and packed-row merges. Its versioned
10-byte NetDisk request owns complete three-attempt read and write transactions
and a caller-supplied DMA/cache. Writes invalidate read-ahead before their first
attempt and use synchronous write-through; an uncertain outcome never leaves
cache data valid. Sound remains unavailable until migrated; POST and automatic
boot are reset-only facilities rather than runtime service vectors.

## What the regression proves

The ABI test, automatic-boot test, host protocol test, and CP/M Plus cosim
check together prove:

- deterministic combined/D15/D16 images and exact `JUKUABI` 1.0 manifest;
- byte-exact gate/helper installation and successful signature/version init;
- reset mode 0 to resident mode 1 transition;
- a nested mode 1 -> mode 3 -> mode 1 framebuffer helper call;
- the corrected overlay rule: a direct mode-1 write at `D864h` is rejected,
  while the helper reaches and reads back underlying RAM at `D800h`;
- accumulator, BC, DE, and HL preservation around the crossing test;
- low/high stack sentinels, final SP, disabled interrupts, and masked PIC;
- D57/D11 state, four transmitted `ABI1` bytes, and a queued receive byte
  consumed after manifest/video/diagnostic/transmit calls;
- a shifted physical `T` through D26 ports 4/5, translated and consumed by the
  shared resident keyboard with its debounce state retained in low RAM;
- exact resident rendering of `Z` and the next-cell underline against a
  9,600-byte framebuffer oracle, plus rejection of a direct overlay write;
- test-only resident variants around the byte-identical C4 image: exactly
  512 console-status polls erase the underline and 1,024 restore it, proving
  a complete visible/hidden/visible cursor cycle;
- all five POST classes through real firmware paths: a changed CPU vector,
  stuck RAM bit, address alias, complete-ROM bit flip, D57 count fault, and D11
  ready-state fault;
- a bounded successful POST: target-ready C4 appears after 725,602 cycles,
  about 427 ms at CS00015's measured 1.70 MHz;
- no-host waiting, corrupted-extension rejection/resynchronization, and a
  valid keyless 19,200 handoff into a test payload;
- host restart fallback when C4 was missed;
- D26 Port C readback that includes BSR-updated upper hardware bits, proving
  mode changes preserve PC7 instead of relying on the direct-write shadow;
- the real CP/M Plus ROM consumer remaining in mode 1, reaching `A>`, accepting
  matrix input for `DIR`, `DIAG CPU`, and `ERA README.TXT`, and completing the
  sequence with 38 NetDisk reads, one write, no retries, and no USART overruns;
- byte-exact parity between the final resident-ROM and RAM-console framebuffers
  after the same `A>`, `DIR`, and `DIAG CPU` transcript, including the cursor.

The additional ABI 1.1 regression verifies its 214-byte gate, 128-byte helper,
feature/vector manifest, all four reset-latched video modes, exact Estonian
`Ä` framebuffer pixels in each geometry, copied `T` to `X` remap, immediate
bit-0 autoboot, bit-0-clear waiting, and release of that wait by a local `N`.
The ordinary ABI 1.0 regression continues to rebuild and execute the
byte-exact C4 image in the same check.

The focused [structural HDL gate](../../../docs/network-first-rom-hdl.md) also
boots the exact C4 production image through `juku_top`/`vm80a`, exercises the
resident ABI and framebuffer helper, accepts a shifted matrix key, and
completes one CRC-checked NetDisk-v3 read into a 128-byte DMA record. The full
CP/M, recovery, cursor-pixel, and soak oracles remain in the faster C model.

The write rule matters: MAME maps the high window with `.rom()` and the C model
rejects writes into an active high-ROM overlay. Therefore **all** framebuffer
updates—not only packed read/modify/write—must execute in the copied low-RAM
helper while mode 3 is selected. Resident ROM code owns text policy and font
lookup but cannot paint directly.

## Desk invocation

The candidate's matching identity-free host command is:

```sh
cd ~/fun/cpm-plus-juku && ../8080-cosim/tools/janet_disk_server.py \
  /dev/ttyUSB0 out/cpm-plus-juku-network-rom-system.bin \
  out/cpm-plus-juku.img \
  --fast-stage1 out/cpm-plus-juku-network-rom-fastboot-v15.bin --network-rom \
  --disk-baud 19200 --disk-protocol 3 --writable --timeout 86400
```

Use this command only with the matching C4 runtime and the byte-identical
C3/C4 D15/D16 pair. The JSON status is the
machine-readable release gate and still records that physical qualification is
pending.

To qualify recovery after deliberately stopping that host while CP/M remains
running, start a replacement at the disk layer only:

```sh
cd ~/fun/cpm-plus-juku && ../8080-cosim/tools/janet_disk_server.py \
  /dev/ttyUSB0 out/network-first-abi1-cs00015-c4/cpm-plus-system.bin \
  out/physical-CS00015-C4/working-network-disk.img \
  --resume-disk --disk-baud 19200 --disk-protocol 3 --writable \
  --disk-timeout 86400
```

This sends no bootstrap marker or payload. It waits for a retried NetDisk-v3
request from the live target; a subsequent successful `DIR` proves reattachment
without RESET. The CP/M Plus repository's physical-qualification runner wraps
both commands and preserves the required logs.

## Next implementation boundary

The desk recovery matrix is complete. It covers target reset halfway through a
bootstrap extension while stale bytes remain on the same PTY, plus CP/M Plus
recovery from truncated, 50 ms delayed, duplicated, and bad-CRC NetDisk-v3
replies. The duplicate reply causes modeled 8251 overruns. A fresh stateless
disk server also takes over after its predecessor receives a request but exits
before replying. Clean and faulted paths all reach the real prompt and complete
directory, diagnostic, and write-through operations without a manual reset.

The next boundary is to complete the C4 physical matrix on CS00015. Automatic
boot, N4 input/output, `DIR`, `DIAG CPU`, warm boot, and post-warm-boot `DIR`
already pass blindly with the C3/C4-identical EPROM pair; display, local
keyboard, write, repeated cold boot, and live host-loss/reconnect observations
remain before promotion.
