# PLAN — Road to a fully functional Juku clone

> The machine-level plan: what stands between today's repo and a **working physical
> recreation of the Juku E5101/E5104** (processor module ДГШ5.109.006, .009 FDC
> revision) validated by this repo's digital twin. Complements — does not replace —
> [`docs/vision.md`](docs/vision.md) (the schematic-as-source-of-truth north star,
> **reached** for the boot path) and [`docs/roadmap.md`](docs/roadmap.md) (the
> structural-track phases). Purely historical/preservation project, no commercial value.
>
> Status date: 2026-07-06. Update this file as milestones land.

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

## 2. Where we are (2026-07 snapshot)

| Track | State | Remaining to goal |
|---|---|---|
| **Digital twin** (`cosim/` + `hdl/` + `sync/`) | North star reached: die-accurate vm80a boots ekta37 **on the LVS-checked netlist**, byte-identical to cosim, interactive; 3-layer CI guard | Video output chain model, WD1793/EKDOS boot, jmon33-to-prompt, BASIC multi-ROM, sound; real PROM contents |
| **Replica PCB** (`kicad/`) | v76 fully placed + routed: 237 footprints, 1548/1548, 0 unconnected, 0 electrical DRC; placement СБ/photo-verified | Power widening, fab export + order-readiness gates, DFM/gerber review, **order** |
| **VJUGA spinoff** (`spinoffs/minimal-vga/`) | Gate-4 fabrication candidate: routed 4-layer, ERC/DRC clean, JLCPCB BOM/CPL drafted, 19 socketed ICs + owner-ordered Z80/DRAM | Close human sign-offs, **order Rev A**, assemble, bring-up |
| **Reference base** (`ref/`, `~/fun/juku3000`) | Full Э3+СБ+ВП read (11/11 ВП sheets), 219→317-net LVS, provenance-tagged | Mine the **new Baltijets factory doc set** (see §3); a short owner measurement list |
| **Firmware/media** (`roms/`) | Full canonical ROM set vendored (SHA-1 = MAME) | EKDOS/CP/M disk images (available online), РЕ3/РТ4 PROM binaries |

## 3. New external unlocks (ecosystem survey, 2026-07-06)

The July 2026 survey of the online ecosystem changes the plan materially:

1. **Baltijets factory documentation set** — 16 PDFs (~103 MB) uploaded to
   `elektroonikamuuseum.ee/failid/juku/tech_docs_from_baltijets/` on **2026-07-04**:
   technical specs & testing, schematics & components, adjustment instructions,
   **"007 ROM and ROM programming"**, mouse, FDDs, cables, PSU, keyboard, external
   storage, floppy. This is the factory техническое описание we assumed lost.
   Doc 007 may contain the К556РТ4/К155РЕ3 programming tables **on paper** —
   potentially closing the project's longest-standing blocker (D2/D6/D8/D94 PROM
   contents) without hardware dumps. Highest-leverage desk item in this plan.
2. **MAME driver is fully working** (no NOT_WORKING flag since 2024; latest
   hardware-validated fixes merged 2026-01) — including the discrete PIT-driven
   video timing (49.92 Hz frame, 241-line raster) that our video-chain model needs.
   MAME PR #9946/#14817 discussions are the timing reference.
3. **EKDOS is fully recoverable**: MAME `hash/juku.xml` ships EKDOS 2.29/2.30,
   CP/M 2.2 and system/games disks as 800 KB `.juk` images; the disk format is
   specified in juku3000's cpmtools `diskdefs` + MAME `FLOPPY_JUKU_FORMAT`; EKDOS
   3.0 **source** exists (`EKDOS30.ASM` in infoaed/juku3000). Nothing blocks an
   FDC/EKDOS milestone in the twin.
4. **No other recreation exists** — no FPGA core, no clone PCB, no replica project
   found anywhere. This is first-of-its-kind; publishing results back matters.
5. **Parts are obtainable**: КР580 family plentiful NOS on eBay; К565РУ5 ≡ 4164;
   КР1818ВГ93 scarcer but a western WD1793 is a drop-in. Whole machines surface on
   osta.ee/soov.ee. Community: Märt Põder (juku3000/MAME author), Arti Zirk
   (arti.ee), "Pehka1985" (real-hardware validator) — reachable via juku3000 issues.

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
1. **007 ROM and ROM programming** → РТ4/РЕ3 tables; compare against our
   emulator-recovered D2/D6 maps and the predicted D8 table (`docs/re3-decode.md`).
   Any confirmed table upgrades provenance `prom` → documented and unblocks WS-E PROM
   programming.
2. **002 Schematics and components** → settle .006-vs-.009 revision coverage; attack
   the short blocked-on-materials list (D6 V1/V2 feed, C99 far plate, FDC INTRQ/DRQ,
   D94 outputs, bypass per-position values) from paper before spending owner time.
3. **010-class adjustment instructions** → RAS/CAS/refresh timing, RF/video
   alignment — feeds the video-chain model (WS-B) and physical bring-up (WS-G).
4. 009/014 (FDD, external storage) → exact drive model + cable pinout for Tier 2/3.
Exit criterion: updated provenance table; owner-measurement list reduced to items
genuinely requiring hardware.

### WS-B — Finish the digital twin (fidelity gaps)
The twin is the bring-up oracle; every subsystem modeled before fabrication is a
debugging session saved on real hardware.
1. **FDC + EKDOS boot** (all materials now available): WD1793 behavioral model +
   `.juk` image loader in cosim, then port to `juku_top` (D93 already netted);
   milestone: `'T'` → `<D>isk` → **EKDOS prompt** in the twin, cross-checked vs MAME.
2. **Video readout chain**: model the ИР16 shifters / sync counters / РЕ3 timing so
   the twin emits a real pixel+sync stream (not a VRAM dump); validate geometry
   against MAME's measured 49.92 Hz / 241-line timing. This is what makes the
   physical video path testable before power-on.
3. **jmon33 to a live prompt** (interrupt-driven boot; frame-int machinery exists) and
   **multi-ROM** so `'B'` launches jbasic11.
4. **Sound**: beeper path is fully traced; low-cost model, low priority.
Guards stay green throughout: LVS, boot_check, cosim_check.

### WS-C — VJUGA Rev A: order and bring up (de-risk the whole physical program)
The minimal Z80 board is deliberately the **first physical artifact**: it proves the
fab pipeline (KiCad→JLCPCB), the original-style DRAM refresh/timing and keyboard
decode on real silicon, and the bring-up methodology — on cheap western parts,
before any Soviet NOS is at risk.
1. Close the open human sign-offs (gerber inspection in an independent viewer,
   socket/connector assembly confirmation, final CPN re-check, manual-row
   disposition D1/J30/R6/R15/U50/U51) — the machine gates already pass.
2. **Place the JLCPCB order** (board + factory assembly of sockets/passives).
3. Bring-up ladder: power/LEDs → clock → ROM fetch (logic analyzer on M1) → DRAM
   test → keyboard scan → VGA header output. Each rung has a twin-side reference.
4. Bank learnings (footprints, socket fit, assembly quirks) into the replica plan.

### WS-D — Replica board: to a fab-ready package, then order
1. Finish v76: run `widen_power_v2.py` power widening, re-DRC, regenerate renders.
2. Port the VJUGA order-readiness gate machinery (ERC/DRC/BOM/CPL/manifest/checksum
   reports) to the main `kicad/` board — same discipline, bigger board.
3. Silkscreen cosmetics pass (398 silk / 75 text nits), DFM review vs the original's
   thick-power-trace style, independent gerber viewer review.
4. Freeze the netlist only after WS-A closes the paper-resolvable unknowns; the few
   assumed nets that remain get flagged as bring-up verification points, not blockers.
5. **Order** (2-layer, 310×266 mm — the authenticity call stands). Consider ordering
   with the same vendor batch as spare boards; NRE is the cost driver, not quantity.

### WS-E — Parts, PROMs, assembly (replica)
1. Export a dual-config BOM from `kicad/` + ВП census: **authentic** (Soviet NOS
   types per ДГШ3.031.006) and **functional** (western substitutes per the existing
   ГОСТ↔Western table) — build can start functional and converge to authentic.
2. Source early (long lead): КР580 set, 8× К565РУ5 (+spares), К556РТ4 ×2,
   К155РЕ3 ×1–2, КР1818ВГ93 (or WD1793), СНП59 connectors (the hard-to-substitute
   mechanical item), sockets, passives. Channels: eBay NOS lots, osta.ee/soov.ee,
   zx-pk.ru market. Acceptance-test jig for DRAM and CPU spares.
3. **Program firmware parts**: 2× 2764 (ekta37/jmon33 split per the D15/D16 story),
   РТ4 ≈ 82S129-class and РЕ3 ≈ 74188-class on a universal programmer
   (`docs/prom-dump-procedure.md`) — contents from WS-A doc 007, an owner dump, or
   the boot-validated reconstructed tables (in that preference order).
4. Assemble sockets-first (factory or hand), power-rail checks before any IC seats.

### WS-F — Owner / hardware sessions (the short physical list)
Whatever WS-A doesn't close on paper: dump both РЕ3 sockets (D8 decode-cluster +
D94 top-center) and the two РТ4s; dump board-2's M2764 pair (settles the BIOS-pair
question); continuity beeps (D6 V1/V2, C99, FDC INTRQ/DRQ vs IR0/IR1, D100 OE/T);
beeper session sheet v2; macro photos (R6x refdes, bypass disc values). Also: a
**community ask** via infoaed/juku3000 — Pehka1985 has running hardware; a РЕ3/РТ4
dump request there may close this workstream without our own board time.

### WS-G — System integration (Tier 1 → Tier 2)
1. **Power**: bench supply on X8 (+5/+12/−12; −5 is board-derived) for bring-up;
   then PSU per `toiteplokk.pdf`/Baltijets 012 (recreate or adapt a modern supply
   in the original envelope).
2. **Video**: composite from the BNC/X7 path into a modern monitor or capture
   device (МС6105 is VR201-analog — composite-compatible); RF path optional/Tier 3.
3. **Keyboard**: adapter first (the 8255/74148 protocol is fully understood and
   twin-tested; a microcontroller adapter from PS/2/USB is a weekend project), the
   original keyboard unit per `klaviatuur.pdf`/Baltijets 013 as its own sub-project.
4. **Storage**: Gotek/HxC-class emulator with `.juk` images first (the format is
   fully specified); real 5.25" QD drive + E6502-style dual unit for Tier 3.
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
- PROM strategy preference order: paper tables (doc 007) → hardware dump →
  boot-validated reconstruction. Reconstructed tables are Tier-1/2 acceptable.
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
- WS-A: pull + mine Baltijets docs (007 first). ← highest leverage per hour
- WS-C: close VJUGA sign-offs, order Rev A.
- WS-D1/2: v76 power widening + fab-export gates.
- WS-B1: WD1793 + EKDOS boot in cosim.
- WS-E2: start parts sourcing (long lead). WS-H: first community contact.

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
| РЕ3/РТ4 reconstructed tables subtly wrong on real HW | boot failure hard to localize | doc 007 / dumps before burning; socketed PROMs; twin-predicted bus traces at bring-up |
| Replica 2-layer routing (ours ≠ original copper) has SI/crosstalk issues at 16 MHz dot clock | flaky video/DRAM | VJUGA proves the timing approach first; original worked on 2 layers — keep power widening + DFM review honest; socketed staged bring-up |
| NOS Soviet parts dead/counterfeit | schedule slip | spares + acceptance-test jig; western functional config as fallback (Tier 2 doesn't require NOS) |
| Remaining `assumed`/`boundary` nets (8 + FDC INTRQ/DRQ) wrong | localized rework | flagged as explicit bring-up verification points; bodge-friendly (the original board had factory wires too) |
| СНП59 connectors unobtainable | mechanical infidelity | adapters/substitutes for Tier 1–2; hunt originals for Tier 3 |
| ROM/software rights question resurfaces | takedown of `roms/` | policy already in `roms/README.md`; images re-fetchable from MAME/museum archives |
| Solo-project stall on the long grind | — | keep milestones small and CI-guarded (the repo's proven loop discipline); community engagement adds pull |

## 9. Milestone ledger

- [ ] M1 Baltijets docs mined; PROM-truth status resolved (paper/dump/reconstructed)
- [ ] M2 EKDOS boots in the twin (cosim, then juku_top)
- [ ] M3 VJUGA Rev A ordered
- [ ] M4 Twin emits real video timing (pixel+sync stream validated vs MAME)
- [ ] M5 jmon33 to live prompt + BASIC launches in the twin
- [ ] M6 VJUGA Rev A boots real Juku ROM on the bench
- [ ] M7 Replica fab package passes order-readiness gates; boards ordered
- [ ] M8 Full parts kit in hand (functional config), firmware/PROMs programmed
- [ ] M9 Replica board assembled; staged bring-up complete → **Tier 1**
- [ ] M10 EKDOS boots from floppy(-emulator) on real hardware, keyboard + sound + PSU → **Tier 2**
- [ ] M11 Authentic-parts config + dumped PROMs + original peripherals → **Tier 3**
