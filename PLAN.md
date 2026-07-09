# PLAN — Road to a fully functional Juku clone

> The machine-level plan: what stands between today's repo and a **working physical
> recreation of the Juku E5101/E5104** (processor module ДГШ5.109.006, .009 FDC
> revision) validated by this repo's digital twin. Complements — does not replace —
> [`docs/vision.md`](docs/vision.md) (the schematic-as-source-of-truth north star,
> **reached** for the boot path) and [`docs/roadmap.md`](docs/roadmap.md) (the
> structural-track phases). Purely historical/preservation project, no commercial value.
>
> Status date: 2026-07-08. Update this file as milestones land.

## 1. Definition of done (tiered)

- **Tier 1 — "It's alive":** a fabricated recreation of the processor board powers
  on, boots the real ekta37 RomBios, draws the banner on a real display, and reacts
  to typed commands from a keyboard. (The digital twin already does all of this in
  simulation on the LVS-verified netlist.)
- **Tier 2 — "Fully functional":** boots jmon33 and BASIC, loads **EKDOS from
  floppy** (real drive or Gotek-class emulator), beeps, serial port works, powered
  by a proper PSU, original-style keyboard — a machine you could sit down and use
  as a 1980s schoolkid did.
- **Tier 3 — "Faithful":** populated with period Soviet ICs (КР580/К565/К556/К155),
  PROMs programmed from **dumped** (not reconstructed) contents, original peripherals
  (5.25" drive, original keyboard unit, МС6105-class monitor path), enclosure per
  the factory drawings. Museum-grade, cross-validated against a surviving machine.

Out of scope (explicitly, to guard focus): the .006 tape subsystem, the classroom
network protocol, the E4701 mouse, И41/Multibus expansion cards. These are the least
documented subsystems (also unemulated in MAME) and none block Tiers 1–3. Revisit
only after Tier 2.

## 2. Where we are (2026-07-08 snapshot)

| Track | State | Remaining to goal |
|---|---|---|
| **Digital twin** (`cosim/` + `hdl/` + `sync/`) | North star reached: die-accurate vm80a boots ekta37 **on the LVS-checked netlist**, byte-identical to cosim, interactive; 3-layer CI guard | Video output chain model, WD1793/EKDOS boot, jmon33-to-prompt, BASIC multi-ROM, sound; real PROM contents |
| **Replica PCB** (`kicad/`) | v76 fully placed + routed: 237 footprints, 1548/1548, 0 unconnected, 0 clearance/short DRC; power widened; Gerbers/drill/renders exported with KiCad 10.99 nightly; top-level manufacturing gate is **READY TO UPLOAD** with generated DRC disposition, external Gerber review, package geometry, sourcing, and bring-up verification evidence | Final vendor preview/payment evidence, **order** |
| **VJUGA spinoff** (`spinoffs/minimal-vga/`) | Gate-4 fabrication candidate: routed 4-layer, ERC/DRC clean, JLCPCB BOM/CPL drafted, 19 socketed ICs + owner-ordered Z80/DRAM | Close human sign-offs, **order Rev A**, assemble, bring-up |
| **Reference base** (`ref/`, `~/fun/juku3000`) | Full Э3+СБ+ВП read (11/11 ВП sheets), 219→317-net LVS, provenance-tagged; public-source coverage audited in `docs/source-coverage-audit.md`; vendored Arti `JUKU1.CPM` boots to `A>` in cosim; vendored disk catalog identifies disk-side `JBASIC.COM` / BASIC toolchain candidates; extracted BASIC candidates are guarded under `ref/extracted-software/`; EKDOS `JBASIC` reaches a visible `READY` prompt in cosim | Finish only the source items still material to board/twin proof: Baltijets programming disk or PROM dumps, disk-backed FDC + BASIC prompt path in `juku_top`, and a short owner measurement list |
| **Firmware/media** (`roms/`, `media/disks/`, `media/system/`) | Full canonical ROM set plus public Juku Monitor 2.2 vendored; Arti `JUKU1/JUKU2` raw disk images vendored and `JUKU1.CPM` boots to `A>` in cosim; visible CP/M directories are generated in `docs/vendored-disk-catalog.md`; disk BASIC candidates are extracted in `docs/basic-disk-extraction.md`; public CP/M/EKDOS system binaries from `JUKUSYS.ZIP` are vendored with checksums; `JUKPROG2.CPM` `JBASIC` reaches a visible `READY` prompt in cosim; checkpoint-resumed HDL proves the early `JBASIC` command/FDC-read boundary and late post-transfer `READY` boundary | РЕ3/РТ4 PROM binaries and uninterrupted HDL BASIC prompt bridge |

## 3. New external unlocks (ecosystem survey, 2026-07-06)

The July 2026 survey of the online ecosystem changes the plan materially:

1. **Baltijets factory documentation set** — 16 PDFs (~92 MB) uploaded to
   `elektroonikamuuseum.ee/failid/juku/tech_docs_from_baltijets/` on **2026-07-04**:
   technical specs & testing, schematics & components, adjustment instructions,
   **"007 ROM and ROM programming"**, mouse, FDDs, cables, PSU, keyboard, external
   storage, floppy. This is the factory техническое описание we assumed lost.
   Doc 007 confirms the programmed-part drawings, but the small-PROM byte tables
   are referenced as `на диске` rather than printed; it does **not** close the
   D2/D6/D8/D94 PROM-content blocker by itself. The referenced programming disk
   or hardware dumps remain the path to PROM truth.
2. **MAME driver is fully working** (no NOT_WORKING flag since 2024; latest
   hardware-validated fixes merged 2026-01) — including the discrete PIT-driven
   video timing (49.92 Hz frame, 241-line raster) that our video-chain model needs.
   MAME PR #9946/#14817 discussions are the timing reference.
3. **EKDOS is available in-tree**: Arti `JUKU1.7Z` / `JUKU2.7Z` public raw disk
   images are now vendored under `media/disks/`; `JUKU1.CPM` boots through
   ROMBIOS `TDD` to `A>` in cosim. The raw geometry is specified in
   juku3000's cpmtools `diskdefs` + MAME `FLOPPY_JUKU_FORMAT`; EKDOS 2.30
   **source** is now vendored under `ref/ekdos-source/`. The museum
   `JUKUSYS.ZIP` CP/M/EKDOS binaries are also vendored under `media/system/`.
   The visible CP/M directory catalog is generated in
   `docs/vendored-disk-catalog.md`, including `JBASIC.COM` on the default
   `JUKU1.CPM` boot disk and a fuller BASIC compiler/runtime set on
   `JUKPROG2.CPM`. `scripts/extract_basic_disk_files.py` now exports the
   strongest disk-side BASIC candidates under `ref/extracted-software/` and
   documents the `JUKU1.CPM` directory/raw-candidate mismatch in
   `docs/basic-disk-extraction.md`. Nothing blocks an FDC/EKDOS milestone in
   the twin except the HDL external-media path.
4. **No other recreation exists** — no FPGA core, no clone PCB, no replica project
   found anywhere. This is first-of-its-kind; publishing results back matters.
5. **Parts are obtainable**: КР580 family plentiful NOS on eBay; К565РУ5 ≡ 4164;
   КР1818ВГ93 scarcer but a western WD1793 is a drop-in. Whole machines surface on
   osta.ee/soov.ee. Community: Märt Põder (juku3000/MAME author), Arti Zirk
   (arti.ee), "Pehka1985" (real-hardware validator) — reachable via juku3000 issues.

Source-coverage sanity check: `docs/source-coverage-audit.md` records which
materials from Arti, Elektroonikamuuseum, infoaed/juku3000 ROMs, and
Arvutimuuseum are actually consumed. The board-critical drawings, ROM/BASIC
lineage, and Baltijets docs are covered; the remaining useful external sources
are the programming disk/PROM dumps, disk-backed FDC integration in
`juku_top`, and owner/community validation rather than more РФ2 ROM material.

## 4. Critical path

```
Baltijets doc mine (007/002/010) ──► PROM contents + last assumed nets closed
        │                                     │
        ▼                                     ▼
twin: FDC+EKDOS, video chain          netlist freeze (as-built grade)
        │                                     │
VJUGA Rev A order ► assemble ► bring-up      ▼
        │  (fab+bringup method proven)  replica fab package ► order ► PCB
        └────────────────┬───────────────────┘
                         ▼
        parts sourcing (parallel, long lead) ► assembly (sockets-first)
                         ▼
        staged bring-up (power→clock→ROM→RAM→video→kbd) vs twin as oracle
                         ▼
        Tier 1 ── then FDC/Gotek + PSU + keyboard + sound ──► Tier 2
                         ▼
        NOS parts swap + dumped PROMs + drive/monitor/case ──► Tier 3
```

The two long poles are **parts sourcing** (weeks of shipping from ex-USSR sellers —
start early, it parallelizes with everything) and **PROM truth** (resolved by doc
007, an owner dump session, or — worst case — boot-validated reconstructed tables,
which already boot the twin and are therefore Tier-1/2 sufficient).

## 5. Workstreams

### WS-A — Mine the Baltijets documentation (desk, do first)
Pull all 16 PDFs into `ref/` (plus arti.ee mirrors). Priority order:
1. **007 ROM and ROM programming** → triaged: РТ4/РЕ3/РТ5 programming-table
   drawings are present, but their byte tables are marked `на диске`; only РФ2
   EPROM listings are printed. Next step is locating the referenced disk files or
   dumping the physical PROMs. A Tier 1/2 fallback is now reproducible:
   `scripts/export_reconstructed_proms.py` exports boot-validated reconstructed
   D6 and D8 programming images under `ref/reconstructed-proms/`, with hashes and
   boundaries documented in `docs/reconstructed-prom-fallbacks.md`. These are not
   Tier 3 factory truth and must be replaced or checked when disk files/dumps
   arrive.
2. **002 Schematics and components** → settle .006-vs-.009 revision coverage; attack
   the short blocked-on-materials list (D6 V1/V2 feed, C99 far plate, FDC INTRQ/DRQ,
   D94 outputs, bypass per-position values) from paper before spending owner time.
   First pass done: doc 002 corroborates the `.009` processor-module applicability
   and interface/power connector drawings, but does not include the missing full
   processor schematic pages or PROM byte contents.
3. **010-class adjustment instructions** → RAS/CAS/refresh timing, RF/video
   alignment — feeds the video-chain model (WS-B) and physical bring-up (WS-G).
   First pass on doc 010 shows it is a parts-list/census packet, not the needed
   adjustment instructions. Doc 003 is the actual E5104 adjustment/check packet:
   it gives the factory `ROMBIOS 3.43` monitor-ready oracle, EKDOS boot sequence
   `<T>, <D>, <D>` to `A>` from `JUKU-1`, QRUN/BASIC/printer/manipulator/network
   checks, FDD PSU voltages, and burn-in/vibration cadence. It still does not
   print RAS/CAS timing or PROM byte contents.
4. 009/014 (FDD, external storage) → exact drive model + cable pinout for Tier 2/3.
   Doc 009 confirms the FDD unit packet and Shugart-style 34-pin map: INDEX 8,
   SEL0 10, SEL1 12, MOTOR ON 16, DIR 18, STEP 20, W.DATA 22, W.GATE 24, TR0 26,
   W.PROT 28, RD.DATA 30, SIDE SELECT 32, READY 34, odd pins grounded, with
   `НГМД ЕС 5323.01` drive labeling and +12/+5 power connector mapping. Doc 014
   is a removable 32K memory-expander packet, not FDD storage. Doc 015 names the
   `ДГШ5.106.105` disk label family as `JUKU-1`/`JUKU-2`/`JUKU-3`, but is not a
   disk image.
Exit criterion: updated provenance table; owner-measurement list reduced to items
genuinely requiring hardware.

### WS-B — Finish the digital twin (fidelity gaps)
The twin is the bring-up oracle; every subsystem modeled before fabrication is a
debugging session saved on real hardware.
1. **FDC + EKDOS boot** (all materials now available): WD1793 behavioral model +
   `.juk` image loader in cosim, then port to `juku_top` (D93 already netted);
   milestone: factory sequence `<T>, <D>, <D>` from `ROMBIOS 3.43` to **`A>`**
   with the `JUKU-1`/EKDOS disk image in drive A, cross-checked vs MAME.
   A cosim probe now exercises that exact `TDD` path and reports
   `READY FOR EXTERNAL EKDOS IMAGE` in its reproducible no-image mode: ROMBIOS
   writes WD1793 port `0x1C`, polls it, and reads 512 bytes from data port
   `0x1F`. The raw `.juk` sector backend is now
   implemented and tested against MAME's 80-track, 10-sector, 512-byte,
   1/2-sided geometry, and a minimal disk-backed WD1793 model now covers the
   ROMBIOS restore/seek prelude plus read-sector transfers behind
   `EKDOS_PROBE_DISK=/path/to/image` / `JUKU_DISK=/path/to/image`.
   Required public disk images are vendored in `media/disks/`, and the public
   EKDOS 2.30 BIOS source reference is vendored in `ref/ekdos-source/`;
   `docs/ekdos-media-acquisition.md` tracks the media gate. A transient run
   with the museum/juku3000
   `J3KUTIL4.JUK` EKDOS 2.30 image reaches the `A>` prompt in cosim, and the
   probe now has an optional VRAM bitmap oracle for that boundary. A stronger
   transient run with Arti `JUKU1.7Z` extracts `JUKU1.CPM`
   (`SHA256 859b627d1439c4137f62b5f977ea7d99202e6874fc48c8b818341a38a0f8cd27`)
   and reaches the same `A>` prompt after the factory `<T>, <D>, <D>` path.
   The first HDL-side WD1793 behavior slice is now guarded by
   `sync/fdc_check.sh` and documented in `docs/fdc-readiness.md`:
   restore/seek/step/read-sector/status/DRQ/INTRQ, side-select, and motor-off
   behavior are proven with synthetic sector contents, and the same HDL FDC can
   read real bytes from the vendored `media/disks/JUKU1.CPM` raw image via
   `+disk=...`.
   `docs/fdc-core-survey.md` records available upstream ВГ93/WD1793 cores and
   keeps this local block scoped as a boot/media shim rather than a full manual
   controller clone. `docs/emu80v4-survey.md` adds Emu80v4's GPL-3 software
   FDC1793 model as a reference checklist, but adopts no code and found no
   Juku-specific machine target there. `ref/wd1772-vg93/` now vendors the local
   WD1772 transistor schematic and PLA dump, with
   `docs/wd1772-vg93-reference.md` keeping them scoped as deep reference
   material rather than HDL-derived implementation input. The PLM dump is now
   normalized to guarded JSON/CSV under `ref/wd1772-vg93/`, and
   `docs/wd1772-pla-inspection.md` records the 120-row, 19-input/19-output
   shape plus the single ambiguous `9` row for future controller-equation work.
   `sync/juku_top_fdc_probe.sh` is now the bounded HDL diagnostic for the
   remaining top-level boundary: it enables vendored `JUKU1.CPM`, frame
   interrupts, and fixed `TDD` key stimulus, then stops on decoded WD1793 I/O.
   `sync/juku_top_io_decode_probe.sh` proves raw ROMBIOS I/O and settled D7/D9
   peripheral decode are visible in the fast pre-banner window, including
   mirrored PPI1 and PPI0 writes. `sync/juku_top_30000_state_probe.sh` proves
   the slow top-level run still matches cosim at PC `0x0484` after 30,000 VRAM
   writes, with a byte-identical 9,640-byte framebuffer dump and matching
   visible CPU/PPI/PIC/FDC register state, just before the fast cosim first-PIC
   point at 30,520 writes. The
   current full FDC run loads the disk and reaches BIOS VRAM progress, but the
   default 60-second bound times out before the proven post-banner
   keyboard/interrupt window; `JUKU_TOP_FDC_STOPPC=HEX` now provides exact
   CPU-address stops for narrowing that boundary. `docs/juku-top-30520-reachability.md`
   records that a 360-second exact-PC stop at `0x02B9` and a 900-second
   30,520-write comparison still do not produce an HDL post-banner dump, so the
   automation path moved to checkpoint/fast-forward rather than a larger wall
   timeout. `docs/ekdos-checkpoint-reference.md` now pins the
   full cosim machine checkpoint at that 30,000-write boundary: CPU
   registers/flags, 64 KiB RAM hash, banking, keyboard/PIC/PPI/FDC state, and
   framebuffer hash. This is the input evidence for the checkpoint/resume HDL
   diagnostics.
   `docs/juku-top-checkpoint-load.md` now proves the checkpoint's 64 KiB RAM
   image can be loaded into the LVS-checked `juku_top` D84..D91 bit-sliced
   DRAM planes and dumped back with matching full-RAM and framebuffer hashes;
   it also injects and verifies the checkpoint CPU architectural registers plus
   key PPI/PIC/FDC latches. `docs/juku-top-checkpoint-resume.md` now records a
   focused seeded M1-fetch resume from that checkpoint reaching the pinned first
   post-checkpoint PIC write (`OUT 0x00 = 0xD6` at PC `0x02B9`) and no-key
   keyboard read (`IN 0x05 = 0xCF` at PC `0x1213`) through decoded `juku_top`
   ports. This is not yet a mandatory CI invariant; the next hardening step is
   making the seeded vm80a microstate portable across CI runner schedules, then
   extending the checkpoint-run proof toward FDC I/O and EKDOS `A>`.
   `sync/juku_top_checkpoint_fdc_probe.py` now extends the same checkpointed
   run with frame IRQs and fixed `TDD` key stimulus enabled. Its default
   cycle-targeted cosim checkpoint at 8,711,550 cycles / 63,095 framebuffer
   writes / PC `0xE643` resumes `juku_top` and drains 13 full 512-byte sectors
   (6,656 `IN 0x1F` data-register reads) after the decoded WD1793/VG93
   command/setup sequence. A second clean late-sector checkpoint at 10,066,690
   cycles / 73,386 framebuffer writes / PC `0xE5A0` resumes immediately before
   the `OUT 0x1C = 0x80` read-sector command and drains the remaining 8 full
   sectors (4,096 more `IN 0x1F` reads). Together these checkpoint windows
   cover the full 10,752-byte FDC data-read count seen on the cosim `A>` path.
   The same late checkpoint now also runs past the final FDC sector burst and
   reaches the EKDOS `A>` prompt bitmap at `x=0`, `y=70` through
   checkpoint-resumed `juku_top` CPU execution. `sync/ekdos_checkpoint_prompt_check.sh`
   now provides a named local/deep guard for that late checkpoint prompt proof.
   A single uninterrupted 10,752-byte checkpoint target still times out after
   the first 6,656-byte boundary while looping through keyboard/IRQ service
   around VRAM write count 63,155, so the current proof is split across the
   first and late FDC windows. The older first-FDC
   checkpoint at 63,085 framebuffer writes remains available, and an earlier
   42,000-write key-window run carries the `TDD` stimulus state but still times
   out before FDC. A first narrow harness,
   `sync/juku_top_periph_bus_check.sh`, now proves the decoded top-level
   keyboard/PIC/PPI/FDC path directly, including the pinned no-key `0xCF` and
   shifted-`T` `0x88` keyboard reads, frame INTA vector `0xFED4`, exact
   ROMBIOS first FDC restore command `0x02`, and a vendored `JUKU1.CPM` sector
   byte, without waiting for ROMBIOS drawing. The fast cosim timing
   reference in `docs/ekdos-timing-reference.md` anchors that window: first
   frame IRQ at 33,812 VRAM writes and first FDC command at 63,085 VRAM writes
   on the vendored `JUKU1.CPM` `TDD` path. `docs/ekdos-ioseq-reference.md`
   now also pins the full cosim I/O event stream through the no-key read,
   shifted `T` key read, and first FDC command, tying the direct-bus harness to
   the real ROMBIOS sequence.
   `sync/juku_top_fdc_probe.sh` now also exposes `JUKU_TOP_FDC_STOPPROMPT=1`
   as the uninterrupted-run counterpart to the checkpoint prompt oracle, so a
   long top-level run can stop exactly when the EKDOS `A>` bitmap appears at
   `x=0`, `y=70` instead of relying on a coarse VRAM count. Remaining target:
   drive the uninterrupted full ROMBIOS `TDD` path through `juku_top` to the
   EKDOS prompt with that external media, without relying on checkpoint/resume
   acceleration.
2. **Video readout chain**: model the ИР16 shifters / sync counters / РЕ3 timing so
   the twin emits a real pixel+sync stream (not a VRAM dump); validate geometry
   against MAME's measured 49.92 Hz / 241-line timing. This is what makes the
   physical video path testable before power-on. The runnable V2 readout path is
   now guarded by `sync/video_readout_check.sh` and documented in
   `docs/video-readout-readiness.md`: standalone ИР16 serialization and
   `juku_top`'s `video_raster -> ir16_sr -> lp5_xor1` output reconstruct the
   booted framebuffer byte-identically. `sync/video_timing_check.sh` now pins
   the runnable `video_raster` geometry against MAME's 320 x 241 visible
   raster: 40 framebuffer bytes per line, 9,640 bytes total, one load phase
   followed by seven shift phases per byte, and wrap after 77,120 dot clocks.
   Remaining V3 target: replace the sim-only second framebuffer read with the
   real РЕ3/АГ3-gated shared-DRAM video slot timing once PROM truth is available.
3. **jmon33 to a live prompt** (interrupt-driven boot; frame-int machinery exists) and
   **multi-ROM** so `'B'` launches jbasic11. The first BASIC cartridge-window
   guard is now in `sync/basic_cart_check.sh` and documented in
   `docs/basic-cart-readiness.md`: cosim can load `JUKU_CART=roms/jbasic11.bin`,
   D8 selects D22 for the traced `0x4000..0x5FFF` window, and the optional D22
   sim socket drives `jbasic11.bin[0]` (`0xC3`). The `B` command boundary is now
   guarded in `sync/basic_launch_probe.py` and documented in
   `docs/basic-launch-probe.md`: Monitor 3.3 now probes both the canonical
   `roms/jbasic11.bin` and the legacy `ref/firmware/BAS0-3.HEX` media. Both
   images read through the cartridge overlay and then execute in the
   `0x4000..0xBFFF` RAM window, while that RAM window receives only zero-byte
   writes and remains zero-filled. The probe now records the compatibility
   signals behind that boundary: MAME's local source warns that Monitor 3.3 does
   not seem compatible with the JBASIC expansion cartridge, and both BASIC media
   images start with an absolute `JMP 0x0107` rather than a direct `0x4000`
   window entry. The factory doc 003 `A`-command BASIC clue is now guarded by
   `sync/basic_factory_command_probe.py` and documented in
   `docs/basic-factory-command-probe.md`: the matrix now covers all vendored
   public monitor ROMs (`jmon22`, `jmon33`, `ekta24`, `ekta31`, `ekta32`,
   `ekta35`, `ekta37`, `ekta43`) against both public BASIC payload shapes.
   Monitor 3.3 with `A` reaches the same zero-filled RAM execution boundary as
   `B`, several EktaSoft monitors touch or display while avoiding live BASIC
   cartridge execution, and no tested vendored ROM/media pairing reaches the
   documented BASIC banner/`READY` oracle. `sync/basic_entry_probe.py` also
   rejects the other tempting false path: running `jbasic11.bin` or the generated
   BAS0-3 image as a reset ROM stops at `PC=0x0038` after the first video write
   to `0xFFFE`, with the same framebuffer hash and no BASIC prompt. The EktaSoft
   3.43m #0037 boot ROM still does not select the cartridge overlay in the same
   bounded `B` run. `scripts/report_vendored_disk_catalog.py` now records an
   independent disk-side BASIC lead: `media/disks/JUKU1.CPM` contains
   `JBASIC.COM`, and `JUKPROG2.CPM` contains `JBASIC.COM`, `B80.COM`,
   `BRUN.COM`, `BASCOM.COM`, `BASCOM.DOK`, and `BASLIB.REL`.
   `docs/basic-disk-extraction.md` now preserves `JUKPROG2_JBASIC.COM` as the
   conservative directory-backed extraction lead,
   `JUKPROG2_JBASIC_live_candidate.COM` as the live EKDOS-loaded payload, and
   `JUKU1_JBASIC_raw_candidate.COM` as a raw-offset candidate with
   `BASIC`/`READY`/`ERROR` strings. `sync/ekdos_jbasic_command_probe.py` /
   `docs/ekdos-jbasic-command-probe.md` now pins the next disk-side boundary:
   after `TDD`, the cosim keyboard driver waits for the EKDOS `A>` prompt bitmap
   with `JUKU_KEYS=TDD|JBASIC\r`, consumes all command keys on
   `JUKPROG2.CPM`, and reaches 19,968 WD1793 data-register reads in a deeper
   900,000,000-cycle run plus final
   RAM evidence: the live candidate entry signature at `0x0100` and relocated
   `ERROR`, `READY`, and `BASIC` strings at `0x0469`, `0x0476`, and `0x04AD`.
   It also pins a positive fixed-`0xD800` framebuffer BASIC prompt oracle:
   exact 8x7 glyph matches prove visible `A>JBASIC` at scanline 71, `READY` at
   scanline 121, and a block cursor at scanline 130. The guarded framebuffer SHA256 is
   `60dcda06cf3402a1710e07eb38189518d6a3827c8279888bd8f0d927967ba90b`,
   with 1,175 lit pixels and 68 nonzero scanlines.
   The same report now records the final MAME-mapped video/PIT port state
   (`0x10..0x1B`), memory mode `0`, Port C `0x04`, and 77,306 VRAM writes so
   the rendered prompt has an auditable timing/control context. This proves
   deterministic post-prompt command entry into loaded BASIC code/data and a
   user-visible BASIC `READY` oracle in cosim. The first HDL bridge for that
   path is now tracked by `sync/juku_top_checkpoint_jbasic_probe.py` /
   `docs/juku-top-checkpoint-jbasic-probe.md`: it loads a generated
   `JUKPROG2.CPM` EKDOS `A>` prompt checkpoint into `juku_top`, injects the
   exact `JBASIC` + Enter command sequence with new `+jbasickeys=1` support,
   and adds a `+stopjbasicready=1` exact fixed-`0xD800` `READY` glyph
   oracle. The current tracked HDL run now applies the checkpoint-resume
   `state_pc_bias=-1` fetch alignment, uses frame-scale key holds/gaps to retime
   the `JBASIC` stimulus into the ROMBIOS scanner, observes the full visible
   `A>JBASIC` command oracle at scanline 71, completes the disk-backed FDC data
   path from `JUKPROG2.CPM`, and reaches `[RESUME-JBASIC] READY prompt reached`
   at mcyc 823,184 with 73,925 VRAM writes. The key FDC fix was to make
   WD1793/VG93 side effects latch on the decoded active I/O strobes instead of
   sampling raw `rd_n`/`wr_n` on the simulator clock; the former 4,096-read
   boundary now lands on the cosim-matched track/sector/data state and the
   default proof runs through to `READY`. The follow-on late checkpoint remains tracked by
   `sync/juku_top_checkpoint_jbasic_late_probe.py` /
   `docs/juku-top-checkpoint-jbasic-late-probe.md`: it generates the cosim
   `TDD|JBASIC\r` state after all 19,968 WD1793 data-register reads, resumes
   `juku_top` with no keyboard stimulus, and reaches `[RESUME-JBASIC] READY
   prompt reached` at mcyc 59,120 with the final fixed-`0xD800` `READY` glyph
   visible at scanline 121. The bounded mid-transfer run is tracked by
   `docs/juku-top-checkpoint-jbasic-mid-probe.md`: the same checkpoint-resume
   helper starts from the cosim state after 17,408 total WD1793 data-register
   reads and drains 10,752 additional decoded HDL `IN 0x1F` reads, stopping at
   mcyc 922,973 / VRAM writes 73,916. The remaining gap is now the uninterrupted
   reset-to-EKDOS-to-JBASIC run in `juku_top` without checkpoint/resume, not the
   BASIC prompt renderer.
   The jmon33
   interrupt path is now guarded in cosim by `sync/jmon33_interrupt_probe.py`
   and documented in
   `docs/jmon33-interrupt-probe.md`: Monitor 3.3 programs the 8259, takes the
   `0xFF54` frame interrupt, reads keyboard ports, and writes VRAM. The first
   HDL-side jmon33 probe is now guarded by `sync/jmon33_hdl_probe.sh` and
   documented in `docs/jmon33-hdl-probe.md`: cosim and `juku_top` both reach
   the first Monitor 3.3 video write at `0xFF40`, and their first-write VRAM
   dumps match. The cosim monitor-idle screen/RAM oracle is now guarded by
   `sync/jmon33_ready_probe.py` and documented in
   `docs/jmon33-ready-probe.md`: full VRAM SHA256
   `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397` plus
   the solid cursor block at `x=8`, `y=20`. The user-visible jmon33 command
   surface is now guarded by `sync/jmon33_command_probe.py` and documented in
   `docs/jmon33-command-probe.md`: with a jmon33-appropriate keyboard hold
   window, typed `A`, `T`, and `B` plus return are sampled through port `0x05`
   and produce deterministic visible cursor states. A second cosim guard,
   `sync/jmon33_idle_command_probe.py` / `docs/jmon33-idle-command-probe.md`,
   pins the commands typed after the monitor-idle cursor is already visible:
   delayed `A`, `T`, and `B` plus return reach framebuffer hashes
   `af3cfaefcc1f43604a02a2b2f95449a12c1b7a02a14581aea0bbfa06df51283a`,
   `9da43c195487eae0eeac8c65725a3251ff502642025b745a16691a1d7044bae3`,
   and `891fb09d78847a92e8417b1fb8ab81f160555725853b1d21bf29e25348bad0b0`.
   The HDL testbench now has a
   `+cursorstop=1` stop hook for that same cursor boundary, and
   `sync/jmon33_hdl_cursor_probe.py` documents the bounded `juku_top` state:
   first write still matches at `0xFF40`; a deeper uninterrupted diagnostic now
   stops cleanly at 400 VRAM writes / 579,068 M-cycles with a trustworthy
   nonblank framebuffer dump (64 visible pixels), but still does not reach the
   cursor oracle. The stronger checkpoint-resumed
   boundary is now guarded by `sync/jmon33_checkpoint_cursor_probe.py`: a late
   pre-cursor cosim checkpoint at 3,801,005 cycles / PC `0xF2C0` still has a
   blank framebuffer, and checkpoint-resumed `juku_top` services Monitor 3.3
   frame interrupts, scans the keyboard path, and reaches the same monitor-idle
   cursor framebuffer SHA256 as cosim
   (`f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`).
   `sync/jmon33_hdl_command_probe.py` now compares checkpoint-resumed HDL
   command stimulus against that delayed idle-command oracle. The resumed HDL
   `A` and `B` commands reach their framebuffer oracles, now pinned as named
   guards by `sync/jmon33_hdl_a_command_probe.py` and
   `sync/jmon33_hdl_b_command_probe.py`; the preserved
   `docs/jmon33-hdl-t-command-fdc-diagnostic.md` run shows `T` seeing keyboard
   samples but then entering heavy FDC I/O (`fdc_ios=109522`). The matching
   cosim boundary is now pinned by `sync/jmon33_fdc_command_probe.py` /
   `docs/jmon33-fdc-command-probe.md`: with `media/disks/JUKU1.CPM` attached,
   `T` issues FDC command `0xFD` and polls write-protect status. The C and HDL
   FDC shims now reject Type-III write-track with WRITE PROTECT instead of
   holding BUSY forever. `sync/jmon33_hdl_fdc_command_probe.py` now carries
   that boundary into checkpoint-resumed `juku_top`: with the vendored disk
   attached, the structural path reads FDC status `0x40` repeatedly at PC
   `0xE43C`, and the dedicated report is now marked as a pinned HDL FDC
   `T`-command oracle rather than a generic framebuffer diagnostic.
   Remaining targets: prove the full uninterrupted `juku_top` reset-to-cursor
   path, drive the pinned EKDOS `JBASIC` HDL path without checkpoint/resume,
   and then retire the checkpointed HDL gaps around disk-backed FDC/EKDOS.
4. **Sound**: digital beeper source is now guarded by
   `sync/beeper_check.sh` and documented in `docs/beeper-readiness.md`: D57
   PIT channel 1 accepts a programmed reload and toggles the traced `SOUND`
   output. Remaining physical boundary: the analog driver/current path
   (`SOUND -> R90 -> VT1/VD4/R91 -> R48 -> SPKR`) still needs bench-level
   speaker verification during bring-up.
Guards stay green throughout: LVS, boot_check, cosim_check.

### WS-C — VJUGA Rev A: order and bring up (de-risk the whole physical program)
The minimal Z80 board is deliberately the **first physical artifact**: it proves the
fab pipeline (KiCad→JLCPCB), the original-style DRAM refresh/timing and keyboard
decode on real silicon, and the bring-up methodology — on cheap western parts,
before any Soviet NOS is at risk.
1. Close the open human sign-offs for a **bare-PCB first sample** (gerber
   inspection in an independent viewer, visual routing confirmation, and vendor
   preview/settings capture) — the machine gates already pass.
   Independent Tracespace Gerber/drill render evidence is now generated in
   `fab/minimal-vga/external-gerber-review.md`; remaining sign-offs are
   schematic-symbol human review, order-time visual routing confirmation, and
   vendor preview/settings capture.
   Source-level schematic intent evidence is now generated in
   `fab/minimal-vga/schematic-intent-readiness.md` for the CPU/ROM/decode, DRAM,
   keyboard, VGA, power, clock, and reset contracts.
   Routing/plane disposition is now generated in
   `fab/minimal-vga/routing-disposition-readiness.md`, explicitly accepting the
   Rev A no-pour and 0.20 mm power-routing prototype tradeoff with measured
   limits.
   Manual-row disposition is now generated in
   `fab/minimal-vga/assembly/manual-install-disposition.md`, explicitly keeping
   D1/J30/R6/R15/U50/U51 out of the bare-PCB order path and preserving their
   manual/post-assembly CSVs for a later assembled-board package.
   Vendor/order checklist evidence is now generated in
   `fab/minimal-vga/assembly/vendor-order-checklist.md`, tying the upload BOM CPN
   set to the sourcing checklist, confirming the manual rows stay out of factory
   assembly, and preserving stock/price/alternative/assembly acceptance for a
   later assembled-board order. The exact first-sample upload procedure is now
   generated in `fab/minimal-vga/order-upload-runbook.md` and summarized in
   `spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md` plus
   `spinoffs/minimal-vga/docs/rev-a-bare-pcb-order.md`: upload only
   `fab/minimal-vga/upload/vjuga-rev-a-gerbers-drill.zip`, select PCB
   fabrication only / no assembly, verify the vendor preview, and save order
   evidence using
   `spinoffs/minimal-vga/docs/rev-a-bare-pcb-order-evidence-template.md`. The
   BOM/CPL files are retained as references, not uploaded for the bare-PCB
   order.
2. **Place the JLCPCB order** (bare PCB only, no factory assembly/components).
3. Bring-up ladder: power/LEDs → clock → ROM fetch (logic analyzer on M1) → DRAM
   test → keyboard scan → VGA header output. Each rung has a twin-side reference.
4. Bank learnings (footprints, socket fit, assembly quirks) into the replica plan.

### WS-D — Replica board: to a fab-ready package, then order
1. Finish v76: `widen_power_v2.py` power widening done under KiCad 10.99 nightly
   compatibility path; 704 power tracks evaluated, 377 widened; re-DRC remains
   at 0 unconnected / 0 clearance / 0 shorts. Renders regenerated.
2. Port the VJUGA order-readiness gate machinery (ERC/DRC/BOM/CPL/manifest/checksum
   reports) to the main `kicad/` board — first main-board gate is now in
   `kicad/report_fab_readiness.py` and `kicad/report_order_readiness.py`, emitting
   `fab/gerbers/fab-readiness.md`, `review-waivers.md`, `order-readiness.md`,
   and `SHA256SUMS`.
   Current machine status: electrical/routing PASS, fabrication-file inventory
   PASS, exact-count review waiver ACCEPTED, and order-readiness **ORDER READY**.
   The remaining 599 courtyard/PTH/silk/text findings are review-only and covered
   by the waiver gate. The routed power-envelope DFM check is now generated in
   `docs/replica-power-trace-readiness.md`: 704 routed power segments, 377
   widened beyond the 0.20 mm freerouter baseline, no segment below baseline or
   above the 1.00 mm clamp. Independent Tracespace Gerber/drill render evidence
   is now generated for the main board in `fab/gerbers/external-gerber-review.md`,
   and `kicad/report_order_readiness.py` requires that gate alongside the DRC
   waiver, dual-config BOM, power-trace, and upload-runbook gates.
   `kicad/report_replica_order_upload_runbook.py` generates
   `docs/replica-order-upload-runbook.md`; it builds the ignored
   `fab/gerbers/upload/juku-replica-gerbers-drill.zip`, records the exact upload
   file hashes, writes `fab/gerbers/upload/SHA256SUMS.txt` for the final
   deterministic upload ZIP, verifies every ZIP member against source bytes and
   fixed metadata, and lists the remaining vendor UI preview checks.
   `kicad/report_replica_package_geometry.py` generates
   `docs/replica-package-geometry-readiness.md`, gating the 2-layer job, 310 x
   266 mm Edge.Cuts coordinate box, 1.6 mm thickness, and mixed-plating Excellon
   drill tool/hit inventory.
   `kicad/report_replica_bringup_verification.py` generates
   `docs/replica-bringup-verification-points.md`, converting remaining
   assumed/boundary/pending source-risk annotations into explicit vendor-preview,
   owner-continuity, scope, and logic-analyzer checks for staged bring-up.
   `kicad/report_replica_manufacturing_readiness.py` writes the tracked top-level
   `docs/replica-manufacturing-readiness.md` packet with the final upload ZIP
   checksum, locked vendor options, and the single pre-payment gate command
   `kicad/check_replica_manufacturing_ready.sh`.
3. Silkscreen/mechanical disposition is now generated by
   `kicad/report_replica_drc_disposition.py` into
   `docs/replica-fab-drc-disposition.md`: connector footprint-library
   reproducibility is resolved by `kicad/juku.pretty/`; copper-edge findings are
   resolved by deferring two conflicting generated cutouts; courtyard/PTH/silk/text
   classes are exact-count gated with top repeated references and order-time visual
   checks. Continue with final vendor preview review.
4. Freeze the netlist only after WS-A closes the paper-resolvable unknowns; the few
   assumed nets that remain get flagged as bring-up verification points, not blockers.
5. **Order** (2-layer, 310×266 mm — the authenticity call stands). Consider ordering
   with the same vendor batch as spare boards; NRE is the cost driver, not quantity.

### WS-E — Parts, PROMs, assembly (replica)
1. Export a dual-config BOM from `kicad/` + ВП census: **authentic** (Soviet NOS
   types per ДГШ3.031.006) and **functional** (western substitutes per the existing
   ГОСТ↔Western table) — build can start functional and converge to authentic.
   First generated pass is now in `docs/replica-dual-config-bom.md` and
   `docs/replica-dual-config-bom.csv`, sourced from `kicad/juku.board.json`.
   It separates 226 board component positions into 196 current .009 populated
   parts plus 30 empty expansion/authentic-completeness sockets, with authentic
   markings, functional substitute classes, PROM/programming rows, and
   circuit/mechanical review rows called out.
2. Source early (long lead): КР580 set, 8× К565РУ5 (+spares), К556РТ4 ×2,
   К155РЕ3 ×1–2, КР1818ВГ93 (or WD1793), СНП59 connectors (the hard-to-substitute
   mechanical item), sockets, passives. Channels: eBay NOS lots, osta.ee/soov.ee,
   zx-pk.ru market. Acceptance-test jig for DRAM and CPU spares. A generated
   sourcing readiness gate is now in `docs/replica-sourcing-readiness.md`,
   derived from `docs/replica-dual-config-bom.csv`: it separates source-early
   rows, PROM/programming blockers, review-before-buying rows, and the minimum
   staged acceptance ladder.
3. **Program firmware parts**: 2× 2764 (ekta37/jmon33 split per the D15/D16 story),
   РТ4 ≈ 82S129-class and РЕ3 ≈ 74188-class on a universal programmer
   (`docs/prom-dump-procedure.md`) — contents from the Baltijets referenced
   programming disk, an owner dump, or the boot-validated reconstructed tables
   (in that preference order). The current reconstructed fallback exports are
   `ref/reconstructed-proms/d6_rt4_memory_decode_reconstructed.*` and
   `ref/reconstructed-proms/d8_re3_rom_pager_reconstructed.*`; D2, D94, and the
   video-timing РЕ3 truth remain dump/disk items.
4. Assemble sockets-first (factory or hand), power-rail checks before any IC seats.

### WS-F — Owner / hardware sessions (the short physical list)
Whatever WS-A doesn't close on paper: dump both РЕ3 sockets (D8 decode-cluster +
D94 top-center) and the two РТ4s; dump board-2's M2764 pair (settles the BIOS-pair
question); continuity beeps (D6 V1/V2, C99, FDC INTRQ/DRQ vs IR0/IR1, D100 OE/T);
beeper session sheet v2; macro photos (R6x refdes, bypass disc values). Also: a
**community ask** via infoaed/juku3000 — Pehka1985 has running hardware; a РЕ3/РТ4
dump request there may close this workstream without our own board time. A
ready-to-send request packet is now tracked in
`docs/community-prom-media-request.md`, covering the PROM dump list, the
`JUKU-1`/`ДГШ5.106.105` media request, deliverable names, and verification
commands.

### WS-G — System integration (Tier 1 → Tier 2)
1. **Power**: bench supply on X8 (+5/+12/−12; −5 is board-derived) for bring-up;
   then PSU per `toiteplokk.pdf`/Baltijets 012 (recreate or adapt a modern supply
   in the original envelope).
2. **Video**: composite from the BNC/X7 path into a modern monitor or capture
   device (МС6105 is VR201-analog — composite-compatible); RF path optional/Tier 3.
3. **Keyboard**: adapter first (the 8255/74148 protocol is fully understood and
   twin-tested; a microcontroller adapter from PS/2/USB is a weekend project), the
   original keyboard unit per `klaviatuur.pdf`/Baltijets 013 as its own sub-project.
4. **Storage**: Gotek/HxC-class emulator with the vendored raw Juku disk images
   first (the format is fully specified); real 5.25" QD drive + E6502-style
   dual unit for Tier 3.
5. **Bring-up = twin lockstep**: reuse the staged ladder from VJUGA; at each stage
   the twin predicts bus/VRAM behavior — divergence localizes the fault. This is
   the payoff of the whole LVS/cosim discipline.
6. Speaker (ДГШ5.884.001 equivalent), case per `korpus.pdf` (Tier 3).

### WS-H — Community & stewardship (ongoing, low effort)
- Contact Märt Põder / Arti Zirk / Pehka1985: announce the project, request РЕ3/РТ4
  dumps, offer back the traced netlist + КиCad recreation (first of its kind).
- Continue the ROM rights-holder contact (`roms/README.md` policy stands).
- Upstream what's generic: the freerouting fork fixes; possibly MAME corrections if
  the twin/schematic contradicts the driver anywhere.
- Keep `docs/project-status.md` and this PLAN current as milestones land.

## 6. Decisions

**Made (recorded so we stop re-deciding):**
- Sequencing: **harden-first** held; now **VJUGA-first** for physical work — prove
  fab + bring-up on western parts before committing NOS Soviet silicon.
- Replica stays a **2-layer** board at original 310×266 mm (authenticity over ease);
  VJUGA is 4-layer (correctness over authenticity). Both intentional.
- KiCad remains the single source of truth; every physical change goes through
  board.json → LVS → boot_check → cosim_check.
- PROM strategy preference order: Baltijets programming-disk files referenced by
  doc 007 → hardware dump → boot-validated reconstruction. Reconstructed tables
  are Tier-1/2 acceptable.
- KiCad 10.99/nightly is the active fabrication tool (`kicad-cli-nightly`). Do not
  depend on the legacy Python `pcbnew` module for main-board gates; use CLI JSON
  reports or file-preserving board transforms until the IPC API is worth adopting.
- Tape/network/mouse: out of scope until after Tier 2.

**Open (each blocks or shapes a workstream):**
1. Replica ROM split detail: final D15/D16 vs D8-window wiring sign-off once doc
   007 / dumps land (affects which EPROMs get burned). — WS-E3
2. Gotek vs real drive for first EKDOS boot (recommendation: Gotek; real drive is
   Tier 3). — WS-G4
3. PSU: recreate original vs modern supply in original form factor (recommendation:
   bench first, decide after Tier 1). — WS-G1
4. Whether VJUGA gets a Rev B (8080-native bus adapter, onboard VGA logic) or the
   effort jumps straight to the replica after Rev A learnings. Decide on Rev A
   bring-up results. — WS-C/WS-D

## 7. Sequencing

**Now → next few weeks (parallel):**
- WS-A: pull + mine Baltijets docs (007 first triage done; small-PROM bits still
  need disk files or dumps).
- WS-C: close VJUGA sign-offs, order Rev A.
- WS-D1/2: v76 power widening + fab-export/readiness/upload gates done; machine blockers
  are clear and the exact-count waiver gate accepts the 599 review-only
  courtyard/PTH/silk/text findings. Do final order-time visual/vendor review.
- WS-B1: WD1793 + EKDOS boot in cosim.
- WS-E2: start parts sourcing from `docs/replica-sourcing-readiness.md` (long
  lead); copy `docs/replica-bringup-verification-points.md` into the private
  build record as parts/assembly evidence accumulates. WS-H: first community
  contact using `docs/community-prom-media-request.md`.

**Then (VJUGA transit + assembly window):**
- WS-B2/3: video chain model; jmon33 + BASIC. WS-D3/4: replica DFM + netlist freeze.
- WS-F: owner session for whatever paper didn't close.

**Then:**
- WS-C3: VJUGA bring-up → bank learnings → WS-D5 replica order → WS-E assembly →
  WS-G staged bring-up → **Tier 1**.
- WS-G2–6 peripherals → **Tier 2**. NOS convergence + originals → **Tier 3**.

## 8. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| РЕ3/РТ4 reconstructed tables subtly wrong on real HW | boot failure hard to localize | Baltijets disk files / dumps before burning; socketed PROMs; twin-predicted bus traces at bring-up |
| Replica 2-layer routing (ours ≠ original copper) has SI/crosstalk issues at 16 MHz dot clock | flaky video/DRAM | VJUGA proves the timing approach first; original worked on 2 layers — keep power widening + DFM review honest; socketed staged bring-up |
| NOS Soviet parts dead/counterfeit | schedule slip | spares + acceptance-test jig; western functional config as fallback (Tier 2 doesn't require NOS) |
| Residual source-risk nets wrong | localized rework | 41 generated bring-up verification points in `docs/replica-bringup-verification-points.md`; bodge-friendly (the original board had factory wires too) |
| СНП59 connectors unobtainable | mechanical infidelity | adapters/substitutes for Tier 1–2; hunt originals for Tier 3 |
| ROM/software rights question resurfaces | takedown of `roms/` | policy already in `roms/README.md`; images re-fetchable from MAME/museum archives |
| Solo-project stall on the long grind | — | keep milestones small and CI-guarded (the repo's proven loop discipline); community engagement adds pull |

## 9. Milestone ledger

Generated current-state audit: `docs/milestone-ledger.md`
(`python3 scripts/report_milestone_ledger.py`). The audit is conservative:
vendor orders, received parts, programmed PROMs, and bench bring-up only count
when tracked evidence exists.

- [ ] M1 Baltijets docs mined; PROM-truth status resolved (disk/dump/reconstructed)
- [ ] M2 EKDOS boots in the twin (cosim reaches `A>` with external media; `juku_top` FDC remains)
- [ ] M3 VJUGA Rev A ordered
- [ ] M4 Twin emits real video timing (pixel+sync stream validated vs MAME)
- [ ] M5 jmon33 to live prompt + BASIC launches in the twin
- [ ] M6 VJUGA Rev A boots real Juku ROM on the bench
- [ ] M7 Replica fab package passes order-readiness gates; boards ordered
- [ ] M8 Full parts kit in hand (functional config), firmware/PROMs programmed
- [ ] M9 Replica board assembled; staged bring-up complete → **Tier 1**
- [ ] M10 EKDOS boots from floppy(-emulator) on real hardware, keyboard + sound + PSU → **Tier 2**
- [ ] M11 Authentic-parts config + dumped PROMs + original peripherals → **Tier 3**
