# Project status & guiding principles

> Living summary of where the project is and the non-obvious facts worth keeping.
> (Mirrors the working notes; update as phases land.)

## What this is
A personal experiment (private repo `github.com/ddanila/8080-cosim`) to model the
Soviet/Estonian **Juku** 8080-based computer as **both** a KiCad PCB and a structural
Verilog "digital schematic", kept provably in sync by an **LVS-style connectivity
checker** (the novel value). Driven headlessly / by LLM — no GUI required.

## Source-of-truth principle (the project's spine)
The real scanned **schematic** (`ref/schematics/`, drawing ДГШ5.109.006 Э3, processor
module, ES101) is authoritative. The **MAME driver** (`ref/mame_juku.cpp`, E5104) is
only a draft to fill gaps. **Where they differ, the schematic wins** and we correct the
HDL/map. Provenance of every net is tagged (`scan`/`datasheet`/`prom`/`boundary`/…) so
nothing is silently invented — `sync/provenance.py` keeps it honest.

## North-star (`docs/vision.md`)
The two tracks should **merge on the schematic as single source of truth**: one
schematic-rooted model that is simultaneously the **PCB netlist**, the **LVS-checked
structure**, and a **runnable digital twin** (emulation running *on the digital
schematic*), with `cosim/` + MAME as validation oracles.

## Where we are (2026-07)
- **Replica package is repo-ready for vendor upload:** `docs/replica-manufacturing-readiness.md`
  is **READY TO UPLOAD** and `fab/gerbers/order-readiness.md` is **ORDER READY**.
  The final upload ZIP is `fab/gerbers/upload/juku-replica-gerbers-drill.zip`
  with SHA256 `93de3fc0a16b4bb31a4f613af69833ed24353d403d8870a774e365d534a7c815`.
  Remaining M7 proof is external vendor preview/order evidence.
- **Residual fabrication/bring-up risks are now explicit:** `docs/replica-bringup-verification-points.md`
  generates 41 source-risk verification points from `kicad/juku.board.json` and is
  required by the manufacturing readiness gate. `docs/fdc-hardware-handoff.md`
  further narrows the FDC subset to guarded D93/D100 bus-side wiring plus
  owner-continuity checks for INTRQ/DRQ, D93 MR/CLK, and D100 OE/T.
- **Digital-twin gaps are bounded:** EKDOS reaches `A>` in cosim and in the
  reset-driven `juku_top` Verilator path with external media; disk-side
  `JBASIC` on `JUKPROG2.CPM` reaches visible `A>JBASIC` and BASIC `READY` in
  uninterrupted HDL. jmon33 first-write HDL coverage passes and the stronger
  uninterrupted reset-to-cursor HDL diagnostic now reaches the exact cosim
  monitor-idle framebuffer hash. BASIC cartridge reads are proven for both
  `jbasic11.bin` and the legacy BAS0-3 image, but the Monitor 3.3 cartridge
  path is now documented as a compatibility boundary and the later RAM
  execution window remains zero-filled. The Baltijets factory `A` command BASIC
  clue is separately guarded and still has no public ROM/media pairing that
  reaches the cartridge BASIC banner/`READY` oracle.

Historical merge notes:

- **Phase A COMPLETE** — netlist hardened to **82/99 scan-grounded + 9 `prom`**
  (off-schematic decode tables = emulator-recovered maps) + 8 intricate-timing/boundary
  nets. 52 chips, **LVS green, CI-guarded**.
- **cosim boots the full banner** for ekta37 (`EktaSoft '88 … RomBios 3.43m / *`). The
  earlier "AT-keyboard handshake stall" was a **misdiagnosis** — it was the ROM
  self-test checksum (ekta43 has a stale block-1 checksum; ekta37 is clean).
- **Phase C STARTED — the merge:**
  - *Step 1* — vendored **vm80a** (die-accurate КР580ВМ80А Verilog replica, 1801BM1,
    CC-BY 3.0, `hdl/vendor/`); validated in iverilog.
  - *Step 2* — vm80a **boots the real BIOS in iverilog** (`hdl/sim/juku_sim_tb.v`) and
    its framebuffer is **byte-for-byte identical to cosim** (full 42623-write banner,
    `docs/boot-banner-ekta37-hdl.png`). The sim's memory/banking/I-O is behavioral
    (mirrors cosim); *step 3* decomposes it into actual chip instances wired per the
    LVS netlist.
  - *Step 4 (STARTED) — unify the two copies into one runnable LVS model.* Today `juku_top.v`
    (the LVS netlist) instantiates the **`devices.v` STUBS** (drive `z`/const → can't boot), while
    `juku_struct_tb.v` is a **separate parallel copy** with functional `_b` bodies that does boot.
    The merge = functionalize `devices.v` so the **LVS-checked `juku_top.v` itself boots** ekta37
    byte-identical to cosim (then retire the `_b` duplicate). **Step-1 landed:** the combinational
    glue (8286 buffer, 74138 I/O decode, clock gates ЛН1/ЛА12/ЛА1) is now functional in `devices.v`;
    `juku_top` elaborates and **LVS stays IN SYNC** (100/100). **Step-2 landed:** `cpu_8080` now
    wraps the **vm80a die-replica** (real core) and `sysctl_8238` is functional (status latch on
    STSTB → MEMR/MEMW/IORD/IOWR/INTA strobes + D↔DB bridge). The vm80a sampling `osc` is a sim-only
    `juku_top` input wired to nothing else, so LVS drops it (1-endpoint net); vm80a is blackboxed in
    the LVS yosys read (sim compiles `vm80a.v` for the boot). Added `proc` to the LVS yosys cmd so
    `write_json` handles the new register logic. LVS still **IN SYNC** (100/100); sim elaborates.
    **Boot is now gated on the clock subsystem** (functional Φ1/Φ2 + STSTB) — the next step: the
    discrete clock mesh (D59/D40/D33/D36/D38/D35) is still stubbed, and its gate inputs are a
    documented un-traced boundary. Then memory (EPROM/decode/DRAM), peripherals, and a boot harness.
  - *Step-3 landed:* `clk_phase` (D35) now generates a live non-overlapping **Φ1/Φ2** (a sim clock
    realized to functional intent — the mesh feeding it is the un-traced boundary). KEY trick: it
    sets only the simulated VALUE; the D35→CPU net *wiring* (what LVS compares) is unchanged, so LVS
    stays **IN SYNC** (100/100). Probe (`juku_top` + vm80a): Φ1/Φ2 toggle and **vm80a starts cycling**
    (sync pulses) — the clocking path runs through the real `juku_top` structure. (Added a `timescale`
    to `devices.v` so the phase delays are ns.) Remaining boot blockers: **STSTB** (the 8238 needs a
    SYNC-qualified strobe to latch status — D13/D38 path, an assumed-wiring sub-step) and **memory**
    (EPROM/decode/DRAM bodies). Then peripherals + a boot harness. 
  - *STSTB sub-step landed:* the 8238 needs a SYNC-qualified strobe to latch the CPU status byte. Realized it: D38 (ЛА1) now outputs `ststb_n = ~sync` (its deferred inputs set so clkg_d33/d39_y don't gate; SYNC fed into one input [assumed]). Added the **SYNC net** (D1.19→D38.12, src=`assumed`) to board.json so it matches; **LVS IN SYNC 101/101** (provenance now 86 scan + 9 prom + 6 assumed/boundary). Probe: STSTB strobes, the 8238 latches status, and **MEMR asserts on the first fetch** — vm80a runs one machine cycle then stalls only because **memory still returns z** (blocker #2). So STSTB is done; **memory (EPROM/decode/DRAM bodies) is the last thing between here and a boot**. 
  - *Memory part 1 (EPROM+decode) landed — vm80a EXECUTES the real BIOS through `juku_top`.* `decode_prom` (D6) realizes the recovered mode-0 map (ROM 0x0000-0x3FFF, split D15 low 8K / D16 high 8K by A13, RAM elsewhere); `eprom_8k` loads ekta37 with sample-and-hold reads. Rewired the EPROM split: D16's CE = the decode's `rev` output (new **REV** net, src=`assumed`), both OE = **MEMR** (read strobe; 2764 convention). Also: LVS yosys now reads `devices.v` as a **`-lib` blackbox** (connectivity only) so it doesn't mis-resolve the now-functional tri-state buses; `$readmemh` guarded by `` `ifndef YOSYS ``. **LVS IN SYNC 101/101** (86 scan + 9 prom + 7 assumed/boundary). Probe: vm80a fetches `C3 17 00` @0x0000 → **JMPs to 0x0017** → executes 100 instructions sustained (114 machine cycles) — real control flow on the LVS-checked netlist. Remaining for a full boot: **DRAM** (RAM + the 0xD800 video writes) — the bit-sliced РУ5 array + its multiplexed MA/RAS/CAS addressing (the deepest boundary). Then a boot harness + the byte-identical-to-cosim guard.
  - **★ Memory part 2 (DRAM) + peripherals landed — `juku_top` BOOTS ekta37 BYTE-IDENTICAL TO
    COSIM. The merge's north-star is reached.** The LVS-checked structural netlist *itself* is
    now a runnable digital twin: one model = PCB netlist + LVS structure + emulation, all at once.
    - `dram_64kx1` (8× bit-sliced К565РУ5, D60–67): row latch on RAS, col on CAS, sample-held
      read driven during the access; `kp14_mux` (D48/49) multiplexes BA[15:8]/BA[7:0] onto MA by
      Φ1; `rascas_dec` (D53 ИД7) makes RAS=~(RAMsel&Φ1), CAS=~(RAMsel&Φ2). board.json reconciled
      (the row-address taps + Φ→sel/D53 + a RAM_SEL net, tagged assumed/boundary); the video
      counters go dangling (video *readout* path is the remaining un-modeled boundary).
    - Peripherals (8255×2, 8253×3, 8251, 8259, 1793) functionalized as IN=last-OUT (the model
      that boots ekta37 in juku_struct); PPI0 Port C low → banking mode.
    - **THE decisive sim-fidelity fix:** the data buses must be `tri1` (pull-up, like the real
      open bus) — as plain `wire` they float to z/x and *poison the die-accurate vm80a's internal
      capture*, so register ops/flags compute wrong (every conditional loop exited after 1 pass;
      the BIOS RAM-test then hung at its error handler). With `tri1` the RAM test passes (2000+11520
      iters) and the full boot is byte-identical. yosys has no `tri1`, so it's `` `ifdef YOSYS ``-guarded
      to a plain wire (connectivity is unchanged → LVS untouched). Also: the harness must drive the
      precise non-overlapping Φ1/Φ2 + mid-phase `osc` lockstep the replica needs (clock mesh = boundary).
    - **LVS IN SYNC** (86 scan + 9 prom + 8 assumed/boundary). `hdl/sim/juku_top_tb.v` is the boot
      harness; **`sync/boot_check.sh` now guards `juku_top` too** (== cosim @ 6000 writes, sha1
      `f9163d30…`). Remaining: retire the duplicate `_b` bodies (Step 5); model the video readout chain.
  - **Video readout V2 guarded:** `sync/video_readout_check.sh` now regenerates a
    booted `juku_top` framebuffer, serializes it through the standalone ИР16 path,
    then captures `juku_top`'s own `vid_out` path. Both reconstructed streams must
    compare byte-identically against the source framebuffer. Report:
    `docs/video-readout-readiness.md`. `sync/video_timing_check.sh` also guards
    the MAME-matched runnable raster geometry: 320 x 241 visible pixels, 40 bytes
    per line, 9,640 framebuffer bytes, and an 8-dot load/shift cadence. V3
    remains the РЕ3/АГ3-gated shared-DRAM video slot timing boundary; the D94
    `.092` text/photo trail is audited, but still lacks pin-level `E_N`/D0-D7
    closure or PROM contents.
  - **★★ CONSOLIDATION COMPLETE — one model, fully interactive, + a new value-level guard.**
    - **Correction to the earlier claim:** the "byte-identical boot" (6000 writes) only ever covered
      the **RAM-test fill** (all mode-0). The real banner needs banking mode-switching, which the
      mode-0-only decode ignored → `juku_top` diverged the instant the banner drawing began. Fixed
      `decode_prom` to honor the mode via `v_en_n` (D7 ЛА3 fed by PPI0 Port C bit 0): mode-0 ROM
      overlay ↔ mode-1 high-ROM fold. Now `juku_top` runs the full banner path.
    - **Keyboard + interrupts ported onto `juku_top`** (were only in the `_b` copy): `ppi_8255` gains
      the 74148 keyboard + Port-C/BSR; a sim-only `intr_ctl` adjunct drives INT + injects the 0xFED4
      CALL vector on INTA. Sim stimulus (kbd/frame) are 1-endpoint nets the LVS drops.
    - **THE bug — DRAM write hazard:** the bit-sliced РУ5 captured writes on the CAS-falling edge,
      but DB isn't settled there, so occasional writes stored the stale bus (silent — the RAM test
      checks only 0xD300, the VRAM guard only 0xD800+). Symptom: banner ran but text never reached
      video RAM. **Found with a co-sim diff** (juku_top vs the juku_struct oracle, lockstepped, first
      divergent read = a write to 0xD441 storing 0x00 not 0x4A). Fix: sample the DRAM write on the
      **osc master clock** while CAS & WE low (like juku_struct). Result: **co-sim runs 9.3M reads with
      ZERO divergence — juku_top ≡ juku_struct bit-identically** through boot + full banner + idle loop.
      `juku_top` renders the banner AND reacts to a typed **'T'** → `System from <D>isk, <N>et ?` + cursor
      (`docs/boot-ekta37-T-command-juku_top.png`). **`juku_top` fully replaces `juku_struct`.**
    - **`juku_struct` repurposed → reference ORACLE** (`hdl/sim/juku_struct.v`); the `_b` testbench
      retired. **New guard `sync/cosim_check.sh`** locksteps the two models and fails on the first
      divergent read — a **value-level** check stronger than LVS (connectivity) or boot_check (sampled
      RAM). It's what caught the 0xD441 bug. `boot_check.sh` drops the redundant `juku_struct_tb` level.
    - Sim-only sampling clock renamed `osc`→`sclk` on cpu_8080/dram (avoids colliding with the real
      crystal-osc pins); `lvs.py` gains an explicit `SIM_ONLY` allowlist (drops those pins by name,
      still flags any other unmapped pin — verified). **LVS IN SYNC (94).** Remaining: video readout chain.

## Interactive-emulation track (the original "react to commands" goal — MET)
- **Frame interrupt (opt-in):** cosim (`cosim/trace.c`, argv[4]=period-in-cycles, 0=off →
  boot-identical) + the HDL `intr_ctl` adjunct model the MAME wiring (8253 VER-RTR → 8259 IR5
  → CPU, MCS-80 3-byte `CALL` vector). jmon33's ICW=0x56/0xFF → IR5 vector **0xFF54**; ekta37's
  → **0xFED4**. Injected onto DB during the exact 3 INTA reads (PC frozen).
- **jmon33** (Monitor v3.3, MAME `ROM_BIOS(0)`) is **interrupt+input-driven** (dispatches its ISR
  through a RAM vector, needs keyboard/serial) — does NOT self-paint, so it's not the easy target.
  `sync/jmon33_interrupt_probe.py` now proves the cosim path through 8259 setup, frame interrupt
  vector `0xFF54`, keyboard-port reads, and VRAM writes. `sync/jmon33_hdl_probe.sh` now compares
  cosim and `juku_top` at the first Monitor 3.3 video write (`0xFF40`) and requires matching
  first-write VRAM dumps. `sync/jmon33_ready_probe.py` now records a stronger cosim
  monitor-idle oracle: VRAM SHA256 `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
  plus the solid cursor block at `x=8`, `y=20`. `juku_top` now has an optional
  `+cursorstop=1` testbench stop hook for that cursor boundary, and
  `sync/jmon33_hdl_cursor_probe.py` now records the uninterrupted HDL state:
  first write still matches at `0xFF40`; with the cursor hook sampled after the
  bit-sliced DRAM write settles, Verilator reaches the full 10/10-row cursor at
  402 VRAM writes / 710,291 M-cycles and dumps the exact cosim framebuffer
  SHA256. The stronger checkpoint-resumed
  proof in `sync/jmon33_checkpoint_cursor_probe.py` now starts from a blank
  late cosim checkpoint and reaches the same monitor-idle cursor framebuffer
  SHA256 in `juku_top`. `sync/jmon33_command_probe.py` now proves the cosim
  user-visible command surface: typed `A`, `T`, and `B` plus return are sampled
  through the keyboard port and move the visible command cursor to deterministic
  screen positions. `sync/jmon33_idle_command_probe.py` separately pins the
  same commands typed after the monitor-idle cursor is already visible, giving
  the checkpoint-resumed HDL path the correct delayed-command reference hashes.
  `sync/jmon33_hdl_command_probe.py` now compares checkpoint-resumed HDL
  command stimulus against that delayed idle-command oracle. The HDL `A` and
  `B` commands reach their framebuffer oracles, with
  `sync/jmon33_hdl_a_command_probe.py` and
  `sync/jmon33_hdl_b_command_probe.py` pinning the late-phase checkpoint
  parameters as named guards; the preserved
  `docs/jmon33-hdl-t-command-fdc-diagnostic.md` run shows the `T` path sees
  keyboard samples but then enters heavy FDC I/O. `sync/jmon33_fdc_command_probe.py`
  now pins the corresponding cosim boundary: with `media/disks/JUKU1.CPM`
  attached, `T` issues FDC command `0xFD` and polls write-protect status. The
  local FDC shims now reject Type-III write-track with WRITE PROTECT instead of
  leaving BUSY stuck forever. `sync/jmon33_hdl_fdc_command_probe.py` carries the
  same boundary into checkpoint-resumed `juku_top`: with the vendored disk
  attached, the structural path reads FDC status `0x40` repeatedly at PC
  `0xE43C`, and the dedicated report is now marked as a pinned HDL FDC
  `T`-command oracle rather than a generic framebuffer diagnostic. BASIC prompt
  discovery and HDL coverage remain separate from the now-pinned uninterrupted
  monitor cursor and command rows.
- **BASIC under jmon33:** `sync/basic_launch_probe.py` proves Monitor 3.3's `B`
  command reads both `jbasic11.bin` and the legacy BAS0-3 image through the
  expansion-cartridge overlay and later executes in the `0x4000..0xBFFF` RAM
  window. The current boundary is sharper: Monitor 3.3 validates the cartridge
  header in high ROM, sets up a copy from the `0x4000` cartridge window into
  low RAM at `0x0100`, jumps to the cartridge bootstrap at `0x0100`, which
  jumps through `0x0107` to a `0x2000` relocation loop, and only later falls
  linearly from `0x3FFF` into the zero-filled `0x4000` RAM window. The loader
  copies the cartridge body from
  `0x0200` into matching low RAM for 7,680 bytes with 0 body mismatches, but
  the low entry/control area has exactly 14 byte mismatches.
  `docs/basic-low-stub-inspection.md`
  groups those 14 deltas: the loaded low image changes the `0x0100` stack
  pointer to `0xFFFE`, keeps the first `0x0200` bytes identical across both
  public BASIC media shapes, and leaves the body exact. The later `0x4000`
  execution fetches a zero-filled NOP sled from mode-1 RAM, not live cartridge
  opcodes or a cartridge-overlay jump, and no user-visible BASIC prompt is produced. The
  probe also records why this is a compatibility
  boundary: MAME's local source warns that Monitor 3.3 does not seem compatible
  with the JBASIC expansion cartridge, and both tested BASIC images start with
  absolute `JMP 0x0107`, not a direct `0x4000` entry.
  `docs/basic-cartridge-length-audit.md` pins the remaining media shape gap:
  the public 8 KiB payload leaves `0x2100..0x21FF` unsupplied for the relocation
  source, and neither the extracted BASIC candidates nor the vendored raw
  `*.CPM`/`*.JUK` images provide a direct tail-page donor.
  `sync/basic_factory_command_probe.py` covers the Baltijets doc 003 factory
  BASIC command `A` across all vendored public monitor ROMs: Monitor 3.3
  reaches the same zero-filled RAM boundary, the EktaSoft monitors still do not
  execute live BASIC cartridge opcodes, and no tested vendored ROM/media pairing
  reaches the documented BASIC banner/`READY` oracle.
  `sync/basic_entry_probe.py` additionally proves both BASIC images are not
  standalone reset ROMs: direct low-ROM execution stops at `PC=0x0038` after
  the first video write to `0xFFFE`, with no BASIC prompt.
- **EKDOS disk BASIC boundary:** `sync/ekdos_jbasic_command_probe.py` now
  drives `TDD|JBASIC\r` against `media/disks/JUKPROG2.CPM`. The `|` marker
  waits for the EKDOS `A>` bitmap before typing `JBASIC`; the run consumes all
  command keys and reaches 19,968 WD1793 data reads in a deeper 900,000,000-cycle
  run. The final RAM contains the raw live-load `JBASIC.COM` candidate's entry
  signature at `0x0100` plus relocated `ERROR`, `READY`, and `BASIC` strings.
  The fixed-`0xD800` framebuffer is now a positive BASIC prompt oracle:
  exact 8x7 glyph matches prove visible `A>JBASIC` at scanline 71, `READY` at
  scanline 121, and a block cursor at scanline 130. The same generated report
  records the final framebuffer hash
  (`60dcda06cf3402a1710e07eb38189518d6a3827c8279888bd8f0d927967ba90b`),
  final video/PIT port state (`0x10..0x1B`), memory mode `0`, Port C `0x04`,
  and 77,306 VRAM writes.
- **HDL EKDOS JBASIC bridge:** `sync/juku_top_checkpoint_jbasic_probe.py` now
  starts from a generated `JUKPROG2.CPM` EKDOS `A>` prompt checkpoint, loads it
  into `juku_top`, and injects the exact `JBASIC` + Enter sequence through new
  checkpoint-resume `+jbasickeys=1` support. The same HDL bench now has
  `+stopjbasicready=1` for the exact fixed-`0xD800` `READY` glyph oracle. The
  prompt-checkpoint report now proves the checkpoint-resumed HDL bridge reaches
  `[RESUME-JBASIC] READY prompt reached` at mcyc 823,184 / 73,925 VRAM writes,
  with visible `A>JBASIC`, disk-backed FDC data reads, and the final `READY`
  glyph rendered. The FDC model now latches side effects on decoded active I/O
  strobes, fixing the stale-register 4,096-read boundary.
  `sync/ekdos_jbasic_checkpoint_check.sh` is the named local/deep guard for
  this checkpoint-resumed BASIC `READY` proof. The follow-on
  `sync/juku_top_checkpoint_jbasic_late_probe.py` report starts from the cosim
  state after all 19,968 WD1793 data-register reads and proves checkpoint-
  resumed HDL reaches `[RESUME-JBASIC]` with the visible `READY` glyph at
  scanline 121. The same helper now has an opt-in FDC data-read stop mode;
  `docs/juku-top-checkpoint-jbasic-mid-probe.md` starts from the 17,408-read
  cosim checkpoint and drains 10,752 additional HDL `IN 0x1F` reads. The
  checkpoint split is now superseded by
  `docs/juku-top-jbasic-verilator-probe.md`: an uninterrupted reset-driven
  `juku_top` run on `JUKPROG2.CPM` reaches EKDOS `A>`, visible `A>JBASIC`,
  BASIC `READY`, and the expected 19,968 WD1793 data-register reads.
  `sync/juku_top_jbasic_prompt_check.sh` guards the committed evidence, with an
  opt-in deep rerun mode for local proof refresh.
- **ekta37 is the interactive target** — it displays and is **polled**: at idle it hammers 8255
  **Port C (0x06)** scanning the keyboard, and reads **Port A/B (0x04/0x05)** only on a key.
- **Keyboard protocol** (matrix → 74148 encoder): **Port A(0x04) low-nibble = column select**;
  **Port B(0x05) read = {SHIFT b7-6 active-LOW, 74148 code b3-1, GS b0 active-LOW}**. In cosim it's
  driven by env `JUKU_KEYS`; in HDL by plusargs `+keyat/+kcol/+kbit/+kshift`. (Watch the SHIFT
  polarity — the 8255 SPECIAL bits 6/7 are active-LOW.)
- **North-star MET on both tracks:** die-accurate 8080 → real BIOS on the LVS-verified structure →
  banner → **reacts to typed commands**. `'T'` → the OS-boot loader `System from <D>isk, <N>et ?`;
  `'B'` → ROM BASIC (separate `jbasic11.bin`; the optional cartridge window is guarded by
  `sync/basic_cart_check.sh`, and `sync/basic_launch_probe.py` now records that Monitor 3.3
  reads both `jbasic11.bin` and the legacy BAS0-3 image before executing in the
  `0x4000..0xBFFF` RAM window while the Monitor 3.3/JBASIC pairing itself remains
  a compatibility boundary; `sync/basic_factory_command_probe.py` separately
  pins the factory doc 003 BASIC `A` command boundary; `sync/basic_entry_probe.py`
  rejects direct reset-ROM execution of the same images);
  `'A'` → mini-assembler
  (`*`-monitor commands, per `juku3000/docs/juku-käsud.md`). Now running on **`juku_top` itself**
  (`ppi_8255` keyboard + `intr_ctl`), not just cosim/the oracle. Evidence:
  `docs/boot-ekta37-T-command*.png`, `docs/basic-cart-readiness.md`,
  `docs/basic-launch-probe.md`,
  `docs/basic-factory-command-probe.md`,
  `docs/jmon33-interrupt-probe.md`, `docs/jmon33-ready-probe.md`,
  `docs/jmon33-hdl-probe.md`.
- **EKDOS cosim milestone:** `sync/ekdos_fdc_probe.py` now treats disk-backed
  runs as successful only when the framebuffer contains the EKDOS `A>` prompt
  bitmap. The museum/juku3000 `J3KUTIL4.JUK` EKDOS 2.30 image is now vendored
  under `media/disks/` and reaches `52K EKDOS 2.30` and `A>` in cosim. Arti
  `JUKU1.7Z` extracts `JUKU1.CPM`
  (`SHA256 859b627d1439c4137f62b5f977ea7d99202e6874fc48c8b818341a38a0f8cd27`)
  and reaches `A>` through the factory `TDD` path. `juku_top` now reaches the
  same disk-backed EKDOS prompt from reset in the committed uninterrupted
  Verilator proof: `docs/juku-top-fdc-verilator-probe.md` records decoded PIC
  setup, 10,752 FDC data-register reads, and the EKDOS `A>` bitmap at VRAM
  write 73,405 / PC `0x097A`. `sync/juku_top_fdc_prompt_check.sh` is the
  routine guard for that evidence, with an opt-in deep rerun mode; the older
  checkpoint guard in `sync/ekdos_checkpoint_prompt_check.sh` remains useful
  for late-window diagnostics.
- **Public software inventory classified:** `docs/public-software-archive-inventory.md`
  records the observed Arti and Elektroonikamuuseum `tarkvara/` listings,
  vendors the required binary/media inputs, confirms museum `JUKUROMS.ZIP` is
  byte-identical to the tracked `roms/` payloads, and leaves only user/classroom/game
  disks plus large tape/flux archives as optional preservation inputs.
- **Owner measurement shortlist:** `docs/owner-measurement-shortlist.md`
  reduces the remaining physical-owner request to P0 programming/PROM/media
  truth plus P1 continuity items. `docs/fdc-hardware-handoff.md` is the exact
  FDC continuity handoff; broad analog/video/sound captures stay in the bring-up
  checklist.
- **Beeper digital source + board handoff guarded:** D57 PIT channel 1 (`OUT1`)
  now has a runnable guard (`sync/beeper_check.sh`) that programs a reload,
  proves the traced `SOUND` source toggles, and checks the board JSON handoff
  through `R90`, `VT1`/`VD4`/`R91`, `R48`, and `SPKR`. The speaker current path
  remains a physical bring-up check, documented in `docs/beeper-readiness.md`.
- **Serial behavior guarded:** `docs/serial-handoff.md` now records D11 8251
  host-bus wiring, D57 baud-clock handoff, the D14/D32/D3/D12/D104 line
  driver/receiver chain, X3 signal nets, and a minimal 8251-style Tx/Rx loopback
  slice. `sync/serial_check.sh` proves mode/command writes, status bits,
  RTS/DTR, and one 8N1 byte through digital loopback. External X3 loopback and
  full 8251 protocol modes remain Tier-2 bring-up work.
- **D2 PROM boundary pinned:** `docs/d2-reconstruction-constraints.md` records
  D2 as the `.037` К556РТ4 bus-arbitration/wait PROM, not the old behavioral
  I/O-decode stand-in. No D2 signal nets or burnable `.037` table are derivable
  from current repo evidence.

## Gotchas worth remembering
- **8080 status-byte latch timing (HDL sim):** latch the status byte on a `clk` edge
  *inside* the sync window, NOT at `posedge sync` — `sync` and the data bus update on
  the same f2 edge, so a posedge-sync read gets the **stale** bus. Symptom when wrong:
  every fetch mis-read as an I/O read → CPU executes all-NOPs (PC just increments 1,2,3…).
- **The banking is PROM-decoded**, not the 8255 "memory_view" MAME abstracts: D6 (К556РТ4)
  decodes A8–A15 + a mode enable (from 8255#0 Port C via the D7 ЛА3 gate). The decode
  *table* lives in off-schematic PROM contents = the emulator-recovered map. The I/O
  chip-select decoder is D9 (К555ИД7); D2 is a separate К556РТ4 bus/wait PROM
  (`ДГШ5.106.037`, dump pending), not a burnable I/O-decode image.
- **ROMs are kept out of git** (copyright + size). `cosim` reads the `.bin` from an
  external path; `hdl/sim/ekta37.hex` is ROM-derived and **gitignored** (generate
  locally — see the `juku_sim_tb.v` header).
- **Structural-sim read data must be sample-and-held** (latch at the read strobe, hold
  through DBIN) — a combinational drive on the multi-hop bus violates the 8080 `tOS1`/
  `tOS2` data-setup-stability spec and corrupts vm80a's fixed-phase capture.
- **The data buses (D/DB) must be `tri1`** (pull-up, like the real open bus), not plain
  `wire`. As `wire` the idle bus floats to z/x and **poisons the die-accurate vm80a's
  internal capture** → register ops/flags compute wrong (symptom: every conditional loop
  exits after 1 pass; the BIOS RAM-test hangs at its error handler). yosys has no `tri1`
  → `` `ifdef YOSYS ``-guard it to `wire` (connectivity identical, LVS untouched).
- **The boot harness drives the Φ1/Φ2 + `sclk` lockstep the replica needs:** non-overlapping
  Φ1 then Φ2, with the fast sampling clock rising in the **middle of each active phase**.
- **DRAM writes must be sampled on the `sclk` master clock while CAS & WE are low, NOT on
  the CAS edge.** DB isn't settled at CAS-fall (8238 bridge timing), so an edge-capture
  stores the *stale bus* on some writes — a silent corruption invisible to LVS (connectivity)
  and boot_check (samples only 0xD300 + 0xD800+). The **co-sim diff** (`sync/cosim_check.sh`)
  is what catches this class; it found the 0xD441 dropped write.
- **The sim sampling clock is named `sclk`, not `osc`,** on cpu_8080/dram — so it can't
  collide with the real crystal-oscillator pins (D59/D35 `.OSC`). `sync/lvs.py` drops the
  sim-only pins via an explicit `SIM_ONLY` allowlist (SCLK/KBD_*/KCOL/KBIT/FRAME_TICK) — by
  name, so any *other* unmapped pin is still flagged (the check is not weakened).
- **`cell` is a reserved word in Icarus Verilog** (Verilog-AMS/config). Don't name a
  reg/memory `cell` — it errors with a cryptic "Syntax error in variable list".

## Firmware / ROMs
The full Juku ROM set is vendored in `roms/` (SHA-1s match MAME; abandonware — see
`roms/README.md`). Two matter for us:
- **ekta37** — EktaSoft BIOS, **polled**: clears the screen and draws its banner inline
  (no interrupts), so it renders in cosim and is the **boot we cross-validate**.
- **jmon33** — the **default** Juku Monitor v3.3 (MAME `ROM_BIOS(0)`), **interrupt-driven**:
  inits the same hardware, enables interrupts, then waits on an ISR-set RAM flag (e.g.
  `0xD704`) and shows nothing under cosim (no interrupts modeled). **jmon33 is the natural
  target for the interactive-emulation track** — booting it to a live prompt requires
  modeling the frame interrupt (8259 → INT/INTA → RST) + keyboard input via the 8255.

## CI guards
- **Status audit** (`scripts/report_milestone_ledger.py`) — regenerated milestone
  evidence stays in sync with tracked repo state, and readiness/audit scripts
  compile in a clean checkout.
- **LVS** (`sync/check.sh`) — KiCad↔HDL **connectivity** stays in sync (does not check values).
- **FDC/media regression** (`sync/juk_disk_check.sh`, `sync/ekdos_fdc_probe.py`,
  `sync/fdc_check.sh`) — raw disk checksums/loader behavior, vendored
  `media/disks/JUKU1.CPM` ROMBIOS `TDD` to EKDOS `A>`, and HDL WD1793
  synthetic-sector behavior stay green.
- **Boot regression** (`sync/boot_check.sh`) — HDL sim levels (juku_sim/chips/**top**) boot the real
  ekta37 **byte-identical to cosim**, bounded to 6000 video writes (~fast). Samples only the framebuffer
  (0xD800+) + the RAM-test byte (0xD300) — so a write bug elsewhere is invisible to it.
- **Co-sim diff** (`sync/cosim_check.sh`) — **value-level**: locksteps `juku_top` (structural) against
  `juku_struct` (behavioral oracle, `hdl/sim/juku_struct.v`) on one clock+ROM and fails on the first
  divergent read. Catches datapath value bugs the other two miss (found the DRAM 0xD441 write bug).
  Slower (two DUTs) → thorough/nightly, not every commit. `WINDOW=<ns>` bounds the run.

## Toolchain
Main-board fabrication gates use KiCad nightly CLI at `/usr/bin/kicad-cli-nightly`
(`10.99.0` in the current reports). `yosys` + `iverilog` run the LVS/HDL guards.
LVS pipeline: `sync/check.sh` (KiCad-free `--board` fallback path used in CI).

## Reference archive + physical ground-truth (2026-06)
`~/fun/juku3000` (fork of **infoaed/juku3000**) is the definitive Juku archive: full ES101
schematic set (processor module = `ДГШ5.109.006`, motherboard/assembly drawing, keyboard,
PSU), the **assembly/placement drawing** (refdes→position — gold for Phase B), component
list (ДГШ3.031.006 ВП), drawing index, a **286-page Russian service manual**, ROMs, source.

Physical ground-truth (owner + archive), now in the model provenance + `transcription/memory.md`:
- **76 chips total, all on the mainboard** (= the processor-module board ДГШ5.109.006).
- **ROM:** 8 sockets, **2 populated** (M2764, 16 KB). **RAM:** 32 sockets, **8 populated**
  (К565РУ5Г = one 64 KB bank); the rest are expansion. **No separate video plane** (video
  shares the bank via the КП14 mux) — corrects an earlier assumption.
- **4 decode/timing PROMs:** 2× К556РТ4 (memory + I/O decode, recovered map) + **2× К155РЕ3
  (DRAM/video timing-state, drawing ДГШ5.106.009)**. The РЕ3 are pure hardware timing —
  MAME omits them, twin boots byte-identical without them; bits **pending a PROM dump**
  (drop-in later; РЕ3=32×8≈74188/82S23, РТ4=256×4≈82S129 — universal programmer reads both).
- Cluster #1 (DRAM/video timing) traced from the scan: D53 ИД7 RAS/CAS decoder pinned,
  ИЕ7→КП14→РУ5 MA video address, 8253→video sync, clock subsystem. See `dram-video-timing.md`.

The model is now an **honest 34-chip baseline** (was 52; removed 18 invented chips — 6
unpopulated EPROM sockets + 12 unpopulated/phantom-video RU5; dropped the 4 phantom VD
video-plane nets → 95 nets, 82 scan + 9 prom + 4 boundary). Every chip now corresponds to
a real *populated* part. It's still **~42 chips short of the real 76** — the unmodeled
glue: bus transceivers (3×ВА86+4×ВА87+170-series), the video chain (ИР16/АГ3/counters),
the 2 РЕ3, and misc gates. **Converging to 76 is now purely additive** (trace each cluster
from the archive schematic + placement drawing → add with scan provenance) — the next
structural sub-passes, which also produce the full Phase-B BOM.

## PCB track status (2026-07) — Phase B manufacturing package ready
The physical-board recreation caught up with (and fed back into) the netlist track:
- **Board fully placed and routed**: v76 has 237 footprints, a 2-layer authentic
  310×266 mm outline, **1548/1548 routed connections**, 0 unconnected items, and
  0 clearance/short blockers in the order-readiness gate. Power nets are widened
  to the guarded 0.20–1.00 mm envelope (`docs/replica-power-trace-readiness.md`:
  704 power segments, 377 widened). The final manufacturing gate is
  `kicad/check_replica_manufacturing_ready.sh`; it regenerates the upload ZIP and
  currently reports **READY TO UPLOAD**.

- **Placement is photo-verified** against the owner's board-#2 photos (22, git-lfs), with two
  systematic calibration bugs found and fixed along the way (photo-1 y-scale 9.50 vs 9.87 px/mm;
  the "10xx = 8x01 upside-down" date-code rule). The ВГ93 quadrant follows the owner's
  authoritative 4-row layout; its refdes are provisional pending etch reads (incl. AG3B/AG3C).
- **Bodge-wire triage complete at photo level** (`ref/photos/juku-pcb-2/BODGE-TRIAGE.md`, 53
  iterations): the top-bracket looms (X3/X4/BNC/RESET) classified LEGIT; the ECO set is confined
  to the clock/timing harnesses — story: **Φ2 tap (E18, etched net "2") → D37 spare NAND (E1/E2)
  → frame-int/STB corner (E7)**, plus H1 = net-11 (CLKG_D36) ↔ ВК38 zone (E15), H2 = cut
  (reverted patch?). 18 endpoints cataloged; **beeper session sheet v2** (7 priority pairs) is the
  closing step — owner-gated, as are the РЕ3/РТ4/2764 dumps and 3 eyeball IDs (row-3 "АП3"=СА3?,
  quadrant etch refdes, the X9-corner TO-126 transistor).
- **freerouting toolchain hardened**: PolylineTrace.combine infinite recursion root-caused and
  fixed on the fork's `custom` branch (ddanila/freerouting, rebased on master); the silent
  GUI-persisted `max_passes=20` cap and the hand-pre-route livelock class are documented in the
  triage log. Renders auto-refresh on commit (`.githooks/pre-commit` → `renders/`).

## Manufacturing milestone audit (2026-07)
The plan-level M1-M11 ledger is now generated into
`docs/milestone-ledger.md` by `scripts/report_milestone_ledger.py`. Current
tracked evidence marks the replica main-board package as
**REPO READY / EXTERNAL PENDING** for M7: `docs/replica-manufacturing-readiness.md`
is **READY TO UPLOAD**, `fab/gerbers/order-readiness.md` is **ORDER READY**, and
`docs/replica-bringup-verification-points.md` tracks the residual source-risk nets
for staged bring-up, with `docs/fdc-hardware-handoff.md` splitting the FDC bus
facts from owner-only continuity points. The remaining M7 proof is external vendor upload/order
evidence. The same audit keeps PROM truth, exact EKDOS media, VJUGA
ordering/bring-up, parts receipt, assembly, and Tier 1-3 hardware validation open
until tracked evidence exists.
