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
- **LVS** (`sync/check.sh`) — KiCad↔HDL connectivity stays in sync.
- **Boot regression** (`sync/boot_check.sh`) — every HDL sim level (juku_sim/chips/struct)
  must boot the real ekta37 **byte-identical to cosim**, bounded to 6000 video writes
  (~30s, not the slow full banner). Protects the merge from silent breakage.

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
