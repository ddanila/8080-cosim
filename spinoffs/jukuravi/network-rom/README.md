# Juku network-first ROM

Status: **AUTOMATIC-BOOT DESK IMAGE — DO NOT PROGRAM INTO D15/D16**

This directory is the from-scratch successor to the frozen Ekta4401 monitor
and simulator-only Ekta4402 direct-fastboot experiment. The product goal is a
network-only ROM which performs bounded POST, boots automatically at 19,200
baud, exposes common platform services from its resident 10 KiB, and gives
CP/M Plus a larger TPA. The accepted staged plan and budgets live in the
`cpm-plus-juku` repository.

The present image proves the versioned ROM ABI, reset/POST path, keyless V15
boot, resident serial initialization, shared keyboard, and compact console. Its
dedicated CP/M Plus consumer reaches `A>`, accepts `DIR` and `DIAG CPU` through
that keyboard, and completes both commands. Its split files test exact EPROM
geometry, but their metadata still says `not for physical programming`; they
are not bench candidates until resident services, reset-side hardware state,
and the physical qualification matrix are complete.

## Build and test

```sh
python3 spinoffs/jukuravi/network-rom/build_network_rom.py
sync/network_first_rom_abi_check.sh
cd ../cpm-plus-juku && make network-rom-cosim-check
```

Committed deterministic artifacts:

- `juku-network-rom-abi1.bin`: combined 16 KiB image;
- `juku-network-rom-abi1-d15.bin`: exact low 8 KiB half;
- `juku-network-rom-abi1-d16.bin`: exact high 8 KiB half;
- `juku-network-rom-abi1.json`: hashes, sizes, ABI identity, and prohibition.

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
delegates serial initialization, polled keyboard input, and the 80x24 console,
and uses the proven RAM NetDisk implementation for the remaining disk service. The normal
all-RAM image remains a byte-exact comparison baseline.

The resident advertises console, serial, keyboard, and diagnostic feature bits. It
programs the proven D57 mode-2/count-4 19,200-baud clock, supports bounded 8251
send/receive, reuses the shared 15-column keyboard scanner and translation
tables with three mutable bytes in low RAM, publishes build/workspace/helper
metadata, supplies the MODX 5x7 font/text policy, and calls a 119-byte copied
helper for mode-3 clear, scroll, and packed-row merges. NetDisk and sound
vectors remain unavailable until migrated and tested; POST and automatic
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
  all 13 matrix keystrokes for `DIR` and `DIAG CPU`, and completing both with
  36 NetDisk reads, no retries, and no USART overruns.
- byte-exact parity between the final resident-ROM and RAM-console framebuffers
  after the same `A>`, `DIR`, and `DIAG CPU` transcript, including the cursor.

The write rule matters: MAME maps the high window with `.rom()` and the C model
rejects writes into an active high-ROM overlay. Therefore **all** framebuffer
updates—not only packed read/modify/write—must execute in the copied low-RAM
helper while mode 3 is selected. Resident ROM code owns text policy and font
lookup but cannot paint directly.

## Desk invocation

Once a physical programming candidate is explicitly released, its matching
identity-free host command will be:

```sh
cd ~/fun/cpm-plus-juku && ../8080-cosim/tools/janet_disk_server.py \
  /dev/ttyUSB0 out/cpm-plus-juku-network-rom-system.bin \
  out/cpm-plus-juku.img \
  --fast-stage1 out/cpm-plus-juku-network-rom-fastboot-v15.bin --network-rom \
  --disk-baud 19200 --disk-protocol 3 --timeout 86400
```

Do not use that as authorization to burn the current files; the JSON status is
the machine-readable release gate.

## Next implementation boundary

Move the next common service behind ABI 1 as a whole NetDisk/bulk operation;
the resident transaction avoids a mode crossing per byte. Each ROM
service must match the retained RAM oracle before its RAM copy is removed.
Relink CP/M Plus after every meaningful saving and publish the exact TPA/map;
the automatic-boot milestone alone intentionally claims no additional RAM.
