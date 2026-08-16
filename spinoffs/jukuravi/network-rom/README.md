# Juku network-first ROM

Status: **CS00015 BENCH CANDIDATE C1 — PHYSICAL QUALIFICATION PENDING**

This directory is the from-scratch successor to the frozen Ekta4401 monitor
and simulator-only Ekta4402 direct-fastboot experiment. The product goal is a
network-only ROM which performs bounded POST, boots automatically at 19,200
baud, exposes common platform services from its resident 10 KiB, and gives
CP/M Plus a larger TPA. The accepted staged plan and budgets live in the
`cpm-plus-juku` repository.

The present image, named `network-first-abi1-cs00015-c1`, proves the versioned
ROM ABI, reset/POST path, keyless V15
boot, resident serial initialization, shared keyboard, and compact console. Its
dedicated CP/M Plus consumer reaches `A>`, accepts `DIR` and `DIAG CPU` through
that keyboard, and completes both commands. Its split files test exact EPROM
geometry. Resident services, reset-side hardware state, and the simulated
recovery matrix are complete, so its metadata now permits a controlled
CS00015 bench burn. It is not a generally qualified release until the physical
matrix passes.

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

The builder stores a 196-byte gate and 119-byte mode-3 helper in the boot-only
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
delegates serial initialization, polled keyboard input, the 80x24 console, and
bounded NetDisk-v3 read-ahead and synchronous write-through transactions. The
normal all-RAM image remains a byte-exact comparison baseline. The relinked
consumer exposes a measured 39,168-byte transient span, exactly 8 KiB above
that baseline.

The resident advertises console, serial, keyboard, NetDisk, and diagnostic feature bits. It
programs the proven D57 mode-2/count-4 19,200-baud clock, supports bounded 8251
send/receive, reuses the shared 15-column keyboard scanner and translation
tables with three mutable bytes in low RAM, publishes build/workspace/helper
metadata, supplies the MODX 5x7 font/text policy, and calls a 119-byte copied
helper for mode-3 clear, scroll, and packed-row merges. Its versioned 10-byte
NetDisk request owns complete three-attempt read and write transactions and a
caller-supplied DMA/cache. Writes invalidate read-ahead before their first
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
- the corrected overlay rule: a direct mode-1 write at `D801h` is rejected,
  while the helper reaches and reads back underlying RAM at `D800h`;
- accumulator, BC, DE, and HL preservation around the crossing test;
- low/high stack sentinels, final SP, disabled interrupts, and masked PIC;
- D57/D11 state, four transmitted `ABI1` bytes, and a queued receive byte
  consumed after manifest/video/diagnostic/transmit calls;
- a shifted physical `T` through D26 ports 4/5, translated and consumed by the
  shared resident keyboard with its debounce state retained in low RAM;
- exact resident rendering of `Z` and the next-cell underline against a
  9,600-byte framebuffer oracle, plus rejection of a direct overlay write;
- test-only resident variants around the byte-identical C1 image: exactly
  1,024 console-status polls erase the underline and 2,048 restore it, proving
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

The focused [structural HDL gate](../../../docs/network-first-rom-hdl.md) also
boots the exact C1 production image through `juku_top`/`vm80a`, exercises the
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

Use this command only with the matching C1 D15/D16 pair. The JSON status is the
machine-readable release gate and still records that physical qualification is
pending.

## Next implementation boundary

The desk recovery matrix is complete. It covers target reset halfway through a
bootstrap extension while stale bytes remain on the same PTY, plus CP/M Plus
recovery from truncated, 50 ms delayed, duplicated, and bad-CRC NetDisk-v3
replies. The duplicate reply causes modeled 8251 overruns. A fresh stateless
disk server also takes over after its predecessor receives a request but exits
before replying. Clean and faulted paths all reach the real prompt and complete
directory, diagnostic, and write-through operations without a manual reset.

The next boundary is to qualify the named D15/D16 candidate physically on
CS00015, then either promote these exact hashes or record and fix the observed
failure before producing C2.
