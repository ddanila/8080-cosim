# EktaSoft remix plan: ekta37 + Jukuravi service module

Status: **EKTA4401 COMPLETE AND FROZEN; EKTA4402 PHYSICALLY QUALIFIED ON
CS00015, 2026-08-16** —
`ekta4401.bin` boots with the banner identity, `H` help, a guarded `V`
diamond-tunnel demo carrying the `JUKU 2026` mark, the floppy subsystem stripped,
and a `J` command that starts the Jukuravi loader from RAM; all guarded
([`remix/README.md`](remix/README.md)). The D15/D16 pair was physically
programmed, booted in CS00015, and exercised through API-v2 PROBE, verified
LOAD/READ, and RUN. Open: the pre-registered normal-raster retention control,
not the service-loader handshake. Measurements below are byte-verified
against the pinned `roms/ekta37.bin` and the exact T36 build; phase results
are at the end.

The separately versioned `ekta4402.bin` preserves all of that behavior and
adds `N fastboot`: a 128-byte ROM-resident V15 core enters 19200/8N1 directly,
eliminating the stock 9600-baud Janet stage. It is fully simulator-qualified
through both CP/Mish and the separately maintained
[`cpm-plus-juku`](https://github.com/ddanila/cpm-plus-juku) non-banked CP/M
Plus 3.1 baseline: each reaches `A>` and completes NetDisk-v3 `DIR` with zero
stock bootstrap frames; CP/M Plus also loads and passes the shared `DIAG CPU`
transient. CP/M Plus sources, images, and its end-to-end regression belong to
that repository; this tree owns Ekta4402 and the common host/model side. It is
now fitted in CS00015 and physically qualifies direct `N`, CP/M Plus,
NetDisk-v3, N4, live stateless host replacement, and its inherited `J`
API-v2 PROBE/refresh/READ path. `ekta4401` remains byte-exact as the frozen
preceding hardware baseline.

## Goal

A new EktaSoft-derived 16 KiB ROM based on Serial #0037 (RomBios 3.43m):

1. keep the stock machine personality (banner, console, monitor, NetBios);
2. add the Jukuravi loader API v2 as a resident service, entered by a new
   monitor command `J` (DI, take the 8251, one-way service mode until
   RESET — the same contract as NetBios entry);
3. add a new monitor command `H` printing the command list with short
   comments;
4. add a compact visual easter egg (`V ?`) which exercises the framebuffer;
5. a personalized identity line in the boot banner, with an honest identity:
   its own serial/name so it can never masquerade as a factory image;
6. optionally strip the floppy subsystem (Net-only boot) — only if space
   demands it;
7. regenerate the block-1 checksum at `000Ah` properly.

## Measured facts the plan stands on

- Command set `FDSXGMCEKTBRWPA`: **`H`, `J`, and `V` are free.** The parser
  references its dispatch table via a single `LXI H,D977h` at ROM `1923h`,
  so the table relocates into free space with a one-word patch
  ([`../../docs/juku-rom-monitor-commands.md`](../../docs/juku-rom-monitor-commands.md)).
- Free space ([`../../docs/ekta37-rom-map.md`](../../docs/ekta37-rom-map.md)):
  `1700h-17FFh` (256 B, in-place half) + `3900h-3EB9h` (1,466 B, relocated
  half, zero RAM cost) = **1,722 B** without removing anything.
- Reclaimable: disk subsystem `2325h-29FFh` = **1,755 B** (minus small
  FLOPPY/START/RWFLOPPY error stubs to keep the `FF50h+` vector contract
  shaped); the hedged expansion/RamDisk driver `3600h-38FFh` = **768 B**.
- Jukuravi cost (from the exact T36 build metadata): loader API v2 engine
  `0A00h-0FFDh` = **1,533 B**, CRC table 256 B, protocol frames ~350 B,
  refresh extension ~256 B, plus low-ROM serial helpers the engine calls
  (~200-500 B, exact inventory is Phase 0). Estimate: **~2.3-2.6 KiB
  full-fidelity, ~1.6-2.0 KiB trimmed** (refresh extension droppable here:
  EktaSoft arms the raster at boot, and if
  [`RASTER-REFRESH-EXPERIMENT.md`](RASTER-REFRESH-EXPERIMENT.md) proves
  video-slot refresh, software refresh is redundant in this ROM).
- `H` command: ~60 B code + ~300-450 B help strings.
- Banner line: same-length in-place string edit is free; an extra printed
  line costs ~40 B of hook.
- ekta37 console is polled, not interrupt-driven — favorable for the
  loader's blocking serial protocol. The 8251 clock (D57 counter 0) is
  already the loader's 2400 baud.
- RAM map: Jukuravi's workspace convention is `C000h-CFFFh`; EktaSoft's
  variables observed in this work live at `D4xxh-D7xxh`. Coexistence is
  plausible but is a Phase 0 verification item, not an assumption.

Space verdict: full-fidelity Jukuravi plus `H` does not fit in 1,722 B;
either trim the core or strip one subsystem. Preference order if space is
needed: (1) trim (drop refresh extension first), (2) strip floppy — which
also matches the Net/service-machine concept, (3) the expansion driver only
if its boundaries are confirmed un-hedged in Phase 0.

## Phases (each independently shippable)

**Phase 0 — desk inventory, no ROM changes.** Trace the loader engine's
exact call graph into T36's low ROM (from the builder's label graph) for a
hard port-size number; verify the EktaSoft-vs-Jukuravi RAM map overlap;
confirm the expansion-driver boundaries. Output: exact byte budget and the
trim/strip decision.

**Phase 1 — build pipeline + minimal remix.** Deterministic patch-based
builder (pinned ekta37 in, structured patches, checksum regen, pinned
output image); relocated command table; `H` command; the banner identity
line. Guard: cosim boot test (banner renders, `H` lists, all 15 stock
commands still dispatch) plus a disasm ctl and round-trip entry in
`sync/disasm_check.sh`. Already a burnable ROM.

**Phase 2 — `J` command + Jukuravi core.** DONE, but not by relocation:
the loader is stored verbatim and copied at `J` time into the RAM addresses
it was assembled for, exploiting memory mode 1 (ROM only at `D800h+`, low
half RAM). See the Phase 2 results below.

**Phase 3 — floppy strip.** DONE as part of Phase 2: the disk region is
reclaimed for the loader segments and the `FF50h+` vectors point at a
`NO DISK - NET ONLY` stub.

**Visual easter egg.** DONE: `V` copies its linked body to hidden low RAM,
disables interrupts, selects all-RAM mode 3, generates twelve full-screen
write-only moving diamond-tunnel frames, overlays `JUKU 2026`, clears, restores mode 1
and returns. `H` advertises it only as `V ?`.

## Risks / notes

- Relocated-half additions must be assembled for fixed `F9xxh` runtime
  addresses; the in-place/relocated split (`1800h`) and the chip split
  (`2000h`) both matter for burn planning (table+banner edits land in D15,
  the module in D16 — both chips re-burn). The builder emits guarded named
  low/high 8 KiB programming images so the combined image is never loaded
  accidentally into one device.
- `J` must DI and own the 8251 exclusively; NetBios and Jukuravi are
  mutually exclusive resident modes, which is the stock machine's own
  pattern.
- `V` must keep interrupts disabled while mode 3 hides the high-ROM interrupt
  handler, restore mode 1 before returning, and stay write-only. A direct
  mode-1 framebuffer write is discarded, while a read-modify-write algorithm
  would read mapped ROM rather than framebuffer RAM.
- The new image gets its own identity (banner serial/name) and its own
  pinned SHA; it must never be confused with the archival #0037 pair, which
  remains the replica content truth.

## Phase 0 results (2026-08-11)

1. **Port size is now a hard number.** Transitive call-graph closure of the
   T36 loader engine (entries: the four public API vectors, loader entry,
   loader loop, refresh API, refresh command handler): **1,836 code bytes**,
   of which only **96 B** are low-ROM helpers — the engine is essentially
   self-contained. Plus the 256 B CRC table (computed access, outside the
   closure) and ~100 B of fixed protocol frames: **~2,192 B full-fidelity,
   ~1,960 B with the refresh extension dropped.**
2. **Strip decision: strip the floppy subsystem.** Even the trimmed core
   plus the `H` command (~2,400-2,500 B) exceeds the 1,722 B of free space,
   and the expansion-driver alternative (+768 B) is razor-thin and hedged.
   The floppy strip yields a ~3.5 KiB budget and matches the Net/service
   concept. Phase 3 therefore folds into Phase 2.
3. **Memory-model correction (affects the mechanism, not the budget).**
   The `+C000h` execution of ROM `1800h-3FFFh` is memory-mode **banking**,
   not a boot-time copy: MAME's driver maps modes 1/2 as ROM reads at
   `D800h-FFFFh` with writes falling through to the RAM underneath — which
   is the framebuffer (`D800h..FDA7h`). Consequences for the module:
   it executes from mapped ROM at `F9xxh` (zero RAM cost confirmed, by
   mapping rather than copy); it must be strictly non-self-modifying (the
   T36 engine already is — workspace-based by design); and a stray write
   into its own address range would silently paint the framebuffer, so
   Phase 2 adds a cosim guard asserting no `D800h+` writes from the engine.
   `J` must also leave the memory mode at 1.
4. **Checksum convention correction (blocking, found in Phase 1).** The boot
   verifier checks **eight 2 KiB chunks across two regions**, stored
   descending from `000Ah` (low: 3 chunks) and `180Ah` (upper: 5 chunks) —
   not the single block-1 sum of the Jukuravi-era convention. All eight
   verify against stock ekta37. An image that regenerates only the block-1
   byte fails the ROM's own verifier and never reaches the command prompt
   (observed). The builder regenerates all eight.
5. **Workspace verdict.** `C000h-CFFFh` is plain RAM in mode 1. EktaSoft/
   EKDOS do use parts of `C0xxh-CDxxh` (37 operand references), so the
   `J` command is one-way service mode until RESET — the documented
   contract — and keeping the loader workspace at its native `C000h`
   preserves bit-exact compatibility with every existing host tool. The
   loader's workspace and stack stay below `D800h`, so the screen contents
   remain intact during service mode: `J` can leave a visible banner.

## Phase 2 results (2026-08-11)

1. **No relocation was needed.** In memory mode 1 the ROM is mapped only at
   `D800h-FFFFh`, so the entire low half is RAM. `J` forces mode 1, copies
   the five T36 segments from mapped ROM into the exact addresses they were
   assembled for, and enters the loader — the engine runs byte-identical to
   the diagnostic ROM, keeping all of its guarantees.
2. **`J` initializes the link through the engine.** The handler calls T36
   `0CE1h`, which programs the 8251 (mode `4Eh`, command `37h`) and its
   2400-baud D57 counter 0, so `J` hands
   over nothing but the machine. Confirmed: the first byte out of port 08h
   after `J` is `A5h`, the loader's frame sync.
3. **Two harness facts invalidated the earlier Phase 1 evidence.** The
   cosim frame interrupt (`argv[4]`) must be on or the keyboard is never
   scanned and *no* command dispatches; and absolute bus-trace read counts
   in the `D800h+` window are framebuffer traffic, identical with or without
   a keypress. The Phase 1 guard passed for that wrong reason and has been
   replaced with control-differenced counts. Any future guard in this ROM
   must difference against a keyless control run.
4. **Visual demo guard.** A control-differenced `V` cosim run records 3,213
   mapped-ROM reads, 1,988,036 reads from the copied low-RAM body, and 127,494
   framebuffer writes accepted while mode 3 is active. It also proves mode 1
   is restored after twelve 40x241 frames, repeated `JUKU 2026` overlays and
   the final clear/return path. The first completed frame is reconstructed
   directly from C-cosim bus writes and checked byte-for-byte against the
   coordinate-based tunnel, plus independent symmetry, connected-run,
   black/white-balance, plaque and logo invariants. This guard replaced the
   original byte-diversity check after MAME and C-cosim showed that an address
   hash could be byte-diverse yet look like one glyph tiled over the screen.
5. **Space after both phases and the demo:** 395 B still free in the `F900h`
   gap.

## Direct-fastboot successor results (ekta4402, 2026-08-15)

1. `N` disables interrupts, selects mode 1, masks the PIC and shadow latch,
   copies a pinned 128-byte V15 core to `0100h`, and jumps there. The core
   programs D57 mode 2/count 4 and D11 x16/8N1, acknowledges the overlap-safe
   `A5 3A` extension header, verifies the 267-byte extension with Fletcher-16,
   and enters it at `0300h`.
2. The core assembles from `remix/direct-fastboot-v15-core.asm` and is
   byte-identical to the first record of CP/Mish's proven
   `juku-fastboot-v15-netdisk-v3.bin`; its padded SHA-256 is
   `a3a073f3f8f0e5c4e68964952c8ed636c66436904bba9d96184a183e4517713d`.
3. `tests/ekta4402_direct_fastboot_test.py` proves the complete ROM command,
   D57/D11 state, byte-exact core copy, checked extension load, and extension
   execution. The CP/Mish V15 matrix then uses the real artifact and system,
   reaches the prompt, and completes NetDisk-v3 `DIR` in 12 exchanges with
   zero stock Janet frames.
4. That integration exposed a cosim artifact: PTY bytes sent while RxEnable
   was clear survived until D11 was enabled. Real wire bytes are gone by then.
   The USART model now drains and counts disabled-receiver bytes, preventing an
   emulator-only stale prefix without weakening enabled-RX timing or overrun.
5. The new image uses the banner `#02`, commands
   `FDSXGMCEKTBRWPAHJNV`, and ends at ROM `3DE4h`, leaving 214 bytes in the
   mapped high-ROM gap. Its SHA-256 is
   `20ff871307b65523428b6ce21e8153842b54c070cd897826154735af6cea6378`.
