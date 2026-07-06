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

## Where we are (2026-06)
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
    `docs/video-readout-readiness.md`. V3 remains the РЕ3/АГ3-gated shared-DRAM
    video slot timing boundary.
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
  plus the solid cursor block at `x=8`, `y=20`; porting `juku_top` to that boundary
  and proving the user-visible command prompt remain pending.
- **ekta37 is the interactive target** — it displays and is **polled**: at idle it hammers 8255
  **Port C (0x06)** scanning the keyboard, and reads **Port A/B (0x04/0x05)** only on a key.
- **Keyboard protocol** (matrix → 74148 encoder): **Port A(0x04) low-nibble = column select**;
  **Port B(0x05) read = {SHIFT b7-6 active-LOW, 74148 code b3-1, GS b0 active-LOW}**. In cosim it's
  driven by env `JUKU_KEYS`; in HDL by plusargs `+keyat/+kcol/+kbit/+kshift`. (Watch the SHIFT
  polarity — the 8255 SPECIAL bits 6/7 are active-LOW.)
- **North-star MET on both tracks:** die-accurate 8080 → real BIOS on the LVS-verified structure →
  banner → **reacts to typed commands**. `'T'` → the OS-boot loader `System from <D>isk, <N>et ?`;
  `'B'` → ROM BASIC (separate `jbasic11.bin`; the optional cartridge window is now guarded by
  `sync/basic_cart_check.sh`, but the full `B`→BASIC prompt path is still pending); `'A'` → mini-assembler
  (`*`-monitor commands, per `juku3000/docs/juku-käsud.md`). Now running on **`juku_top` itself**
  (`ppi_8255` keyboard + `intr_ctl`), not just cosim/the oracle. Evidence:
  `docs/boot-ekta37-T-command*.png`, `docs/basic-cart-readiness.md`,
  `docs/jmon33-interrupt-probe.md`, `docs/jmon33-ready-probe.md`,
  `docs/jmon33-hdl-probe.md`.
- **EKDOS cosim milestone:** `sync/ekdos_fdc_probe.py` now treats disk-backed
  runs as successful only when the framebuffer contains the EKDOS `A>` prompt
  bitmap. A transient run with the external museum/juku3000 `J3KUTIL4.JUK`
  EKDOS 2.30 image reaches `52K EKDOS 2.30` and `A>` in cosim. The repo still
  does not vendor disk media; exact factory `JUKU-1` confirmation and the
  `juku_top` FDC port remain open.
- **Beeper digital source guarded:** D57 PIT channel 1 (`OUT1`) now has a
  runnable guard (`sync/beeper_check.sh`) that programs a reload and proves the
  traced `SOUND` source toggles. The downstream VT1/R48 speaker driver remains
  a physical bring-up check, documented in `docs/beeper-readiness.md`.

## Gotchas worth remembering
- **8080 status-byte latch timing (HDL sim):** latch the status byte on a `clk` edge
  *inside* the sync window, NOT at `posedge sync` — `sync` and the data bus update on
  the same f2 edge, so a posedge-sync read gets the **stale** bus. Symptom when wrong:
  every fetch mis-read as an I/O read → CPU executes all-NOPs (PC just increments 1,2,3…).
- **The banking is PROM-decoded**, not the 8255 "memory_view" MAME abstracts: D6 (К556РТ4)
  decodes A8–A15 + a mode enable (from 8255#0 Port C via the D7 ЛА3 gate). The decode
  *table* lives in off-schematic PROM contents = the emulator-recovered map. Same for
  the I/O decode (D2 РТ4).
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

## CI guards (three layers, increasing strength)
- **LVS** (`sync/check.sh`) — KiCad↔HDL **connectivity** stays in sync (does not check values).
- **Boot regression** (`sync/boot_check.sh`) — HDL sim levels (juku_sim/chips/**top**) boot the real
  ekta37 **byte-identical to cosim**, bounded to 6000 video writes (~fast). Samples only the framebuffer
  (0xD800+) + the RAM-test byte (0xD300) — so a write bug elsewhere is invisible to it.
- **Co-sim diff** (`sync/cosim_check.sh`) — **value-level**: locksteps `juku_top` (structural) against
  `juku_struct` (behavioral oracle, `hdl/sim/juku_struct.v`) on one clock+ROM and fails on the first
  divergent read. Catches datapath value bugs the other two miss (found the DRAM 0xD441 write bug).
  Slower (two DUTs) → thorough/nightly, not every commit. `WINDOW=<ns>` bounds the run.

## Toolchain
`kicad-cli` at `/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/MacOS/kicad-cli`;
`yosys` + `iverilog` via Homebrew. LVS pipeline: `sync/check.sh` (KiCad-free `--board`
fallback path used in CI).

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

## PCB track status (2026-07-03) — Phase B substantially complete
The physical-board recreation caught up with (and fed back into) the netlist track:
- **Board fully placed and routed**: 162 real footprints, **0 placement outlines left** — every
  BOM IC + connectors (X1 СНП59-96 / X2 / X3 / X8 / X9) + passives stage 1 + Z1 РК-171 crystal +
  CT1 trimmer. 2-layer (authenticity call), 310×266 mm, 0.25 mm clearance, **1151/1151 connections,
  0 unconnected, 0 electrical DRC**; power nets widened to ≤1.0 mm (geometric method,
  `kicad/widen_power_v2.py`). The routed power envelope is now guarded by
  `docs/replica-power-trace-readiness.md`: 704 power segments, 377 widened beyond
  the 0.20 mm baseline, no segment below baseline or above the 1.00 mm clamp.
  Gerbers + drill export clean (`kicad/export_fab.sh`).
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
