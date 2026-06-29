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

## Toolchain
`kicad-cli` at `/opt/homebrew/Caskroom/kicad/10.0.4/KiCad/KiCad.app/Contents/MacOS/kicad-cli`;
`yosys` + `iverilog` via Homebrew. LVS pipeline: `sync/check.sh` (KiCad-free `--board`
fallback path used in CI).
