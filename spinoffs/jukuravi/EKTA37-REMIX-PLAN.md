# EktaSoft remix plan: ekta37 + Jukuravi service module

Status: **PHASE 1 COMPLETE, 2026-08-11** — a booting `ekta4401.bin` with the
banner identity and the `H` command exists and is guarded
([`remix/README.md`](remix/README.md)). Phase 2 (Jukuravi module + `J`,
with the floppy strip) is not started. Measurements below are byte-verified
against the pinned `roms/ekta37.bin` and the exact T36 build; phase results
are at the end.

## Goal

A new EktaSoft-derived 16 KiB ROM based on Serial #0037 (RomBios 3.43m):

1. keep the stock machine personality (banner, console, monitor, NetBios);
2. add the Jukuravi loader API v2 as a resident service, entered by a new
   monitor command `J` (DI, take the 8251, one-way service mode until
   RESET — the same contract as NetBios entry);
3. add a new monitor command `H` printing the command list with short
   comments;
4. a personalized identity line in the boot banner, with an honest identity:
   its own serial/name so it can never masquerade as a factory image;
5. optionally strip the floppy subsystem (Net-only boot) — only if space
   demands it;
6. regenerate the block-1 checksum at `000Ah` properly.

## Measured facts the plan stands on

- Command set `FDSXGMCEKTBRWPA`: **`H` and `J` are free.** The parser
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

**Phase 2 — `J` command + Jukuravi core.** Port the loader into the
`3900h` gap (runtime `F9xxh`). Validation reuses the existing `host.py`/PTY
harness: PROBE/CONFIG/LOAD/READ/RUN against the new image in cosim — the
entire Jukuravi regression fleet applies. Physical smoke on CS00015 after.

**Phase 3 (conditional) — floppy strip.** Net-only boot variant: `T`
prompt reduces to Net, vectors get error stubs, disk region reclaimed.

## Risks / notes

- Relocated-half additions must be assembled for fixed `F9xxh` runtime
  addresses; the in-place/relocated split (`1800h`) and the chip split
  (`2000h`) both matter for burn planning (table+banner edits land in D15,
  the module in D16 — both chips re-burn).
- `J` must DI and own the 8251 exclusively; NetBios and Jukuravi are
  mutually exclusive resident modes, which is the stock machine's own
  pattern.
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
