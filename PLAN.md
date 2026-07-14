# PLAN — working physical Juku recreation

Status date: **2026-07-14**.

Release status: **DESIGN HOLD / PACKAGE VERIFIED**. The recorded main-board ZIP
is a checksum-reproducible engineering snapshot, not fabrication authorization.
It passes package-integrity, DRC-disposition, geometry, checksum, and independent
render gates, but its routed board predates accepted functional connectivity.

This is the sole living project plan for the `ДГШ5.109.009` FDC-era processor
module (documented by its ПЭЗ parts list and СБ assembly drawing; the earlier
`.006` revision's Э3 scan remains the electrical-schematic evidence base).
Generated evidence belongs in `docs/`; completed experiments and debug history
belong in Git history.

## Definition of done

- **Tier 1 — boots:** a fabricated board powers safely, runs the real ROM,
  produces usable video, and accepts keyboard input.
- **Tier 2 — usable system:** Monitor 3.3, BASIC, EKDOS/floppy, beeper, serial,
  PSU, and keyboard work on physical hardware.
- **Tier 3 — historically faithful:** factory PROM contents, period parts,
  original-style peripherals/enclosure, and comparison with a surviving Juku.

Tape, classroom networking, mouse, and Multibus expansion are outside the
current critical path. The VJUGA/minimal-VGA board is a separate experiment and
is not a prerequisite for this replica.

## Verified repository state

| Area | What is proved | Open boundary |
| --- | --- | --- |
| Digital twin | `cosim` and `juku_top` boot ekta37; framebuffer and keyboard guards pass; uninterrupted HDL reaches EKDOS `A>` and disk BASIC `READY`; Monitor 3.3 reaches its cursor and selected commands; the cosim-referenced deep guard reaches `CTRACE-END` across 130,000 reads; physical D6 remains structurally instantiated while an explicit non-LVS decoder preserves runnable memory-map equivalence | Retire the D6 functional decoder via joined-conductor D8/D13/D92 timing reconstruction; exact physical shared-DRAM video-slot/DOUT timing, complete controller behavior, cartridge BASIC loading, and analog behavior |
| Connectivity | `sync/check.sh` reports 102 mapped instances and 266 matched nets; the physical D2/D6 PROM tables, measured D2/D30/D105/D13 READY/DBIN handoff, D41 timing rails, reset/USART paths, D7 strobe topology, and the adopted photo/wire-table endpoints are source-modeled and LVS-visible | Routed-snapshot parity, omitted remote endpoints, behavioral correctness, analog waveforms, and historical correctness of assumed nets |
| PCB package | The tracked routed artifact (240 footprints) is DRC-clean within its modeled scope; its KiCad-nightly 10.99 manufacturing packet is checksum/geometry/render verified under a design hold. The preserved source-complete refresh candidate `kicad/juku_routed_candidate.kicad_pcb` has 296 footprints, exact 2,383-pad/net parity, zero unconnected items, and zero shorts, clearance, crossing, hole, dangling, or edge findings | The routed artifact still predates accepted D2/D94, reset/USART, and harness endpoints. The refresh candidate also copper-routes all ten factory insulated-link nets because their twenty paired `А:N` landings are not yet geometrically modeled; all twenty drawing-pixel endpoints are guarded, but no PCB coordinate/island promotion is justified yet. The candidate is convergence evidence, not adoptable production copper (`docs/factory-wire-route-fidelity.md`). Register/split those islands, then adopt/regenerate copper and the manufacturing packet only after the functional P0 netlist freezes |
| Sources/media | Factory drawings, 16 Baltijets PDFs, ROMs, EKDOS source, raw disks, system binaries, 50 owner photographs, validated physical D2 `.037`/D6 `.038`/D8 `.039`/D94 `.092` dumps, 26 photographs of `ДГШ5.109.009 СБ` sheet 1, the ДУБЛИКАТ scan of its sheets 2-6 (таблица соединений, transcribed), and owner RE3 scans are local and checksum-guarded | Baltijets programming-disk payloads, remaining continuity reads, and the cartridge BASIC loading procedure |

The recorded upload ZIP SHA256 is
`7df2a6e2927c62313275f3f5713e2b4cf3622c3c782b795cf41b27c8f3bfff46`.
Do not send this saved package to a fabricator. After the blockers below are
closed and the corrected board is rerouted and reviewed, regenerate every
fabrication file and gate again.

## Actionable now — no new physical evidence required

These are ordered; each is completable with material already in the repo.

1. **Preserve routing convergence until netlist freeze.** The deterministic
   router and conflict-derived INTR rip-up workflow now produce the preserved
   source-complete candidate with zero opens and zero electrical-category DRC
   findings (`docs/routed-refresh-audit.md`). Its ten factory wire nets are
   held from adoption until the twenty paired A-point landing coordinates and
   copper-island splits are modeled. All twenty endpoints are now registered
   in original drawing pixels, while
   all twenty PCB coordinates/island assignments
   remain pending (`docs/factory-wire-route-fidelity.md`). Do not replace
   `kicad/juku_routed.kicad_pcb` yet: copper produced now survives later
   netlist changes through the per-net quarantine mechanism, but final
   production reroute/adoption waits for the P0 functional netlist to freeze,
   followed by repeated endpoint-parity, DRC, and visual review.
2. **Preserve the adopted factory wire-table construction through release.**
   The sheets 2-6 таблица соединений is transcribed and its two number spaces
   are now explicit: conductor positions are not `А:N` board-point labels
   (`ref/schematics/dgsh5-109-009-sb-wire-table.md`). X3/X4/X8/X9 landings,
   S1 links, R94.1, and all ten on-board insulated links are endpoint-mapped
   and guarded. Final copper adoption must retain `А:7-А:14` and
   `А:19-А:20` as assembly wire rather than silently replacing them with etch.

## Release blockers

### P0: physical connectivity (measurement-gated)

Every ask below is queued with exact deliverables in
`docs/owner-measurement-shortlist.md`; each item names its gate document.

1. **Complete FDC-era functional wiring.** D93's drive-interface pins plus
   D28, D95-D99, D101, D102, and D106 have package models but no complete
   functional signal closure (`docs/unmodeled-footprint-inventory.md`,
   `docs/fdc-hardware-handoff.md`). Trace each required pin end-to-end, or
   record a deliberate redesign/DNP decision. D93.40 `VDD_12V` must be proved
   against the +12 V rail before any power-up
   (`docs/d93-pin40-photo-chase.md`). D106.7 Q3 -> D93.26 RCLK is photo-closed;
   the remaining first probes are D106.11-D93.27, D106.14-D93.33 (test for
   hidden layer handoffs; direct same-layer paths are rejected), D106's six
   bounded strap/clock endpoints, and the D95/D101 select pins against
   D93.18/.17 for the period КП12 write-precompensation pattern.
   Probe predictions from period references (guides, not Juku proof): the
   Чеботарев Вектор-06Ц FDC schematic (Радиолюбитель 11/92) uses exactly this
   part family — ВГ93 + К555ИЕ7 separator + two К555КП12 + К555ТМ2 + К155ИР1 —
   with `/RAWR` (ТМ2-resynchronized) jamming ИЕ7 `/LOAD` pin 11 on the same
   node as ВГ93 pin 27, 8 MHz on pin 4, strapped load inputs, and precomp
   taps ИР1 Q1/Q2/Q4 selected by КП12 under EARLY/LATE pins 17/18; WD's
   June-1980 Figure 11 grounds CLR pin 14, while a VFOE-gated (D93.33)
   variant is also plausible — meter both.
2. **Finish D94 `.092` connectivity.** Content truth is closed; the photo
   proves D94.1/.2/.3 to D93.4/.3/.2. Resolve pin 15, output D3-D7
   destinations, and continuity-map input pins 10-14 — their former
   BA11..BA15 assignment was an unproved scaffold analogy and is retired
   behind five explicit input boundaries
   (`docs/d94-reconstruction-constraints.md`).
3. **Finish the measured WAIT/READY edge boundaries.** The D2/D30/D105 path
   is adopted; resolve D30 pins 8/11 and the exact edge contact/pull-up for
   `H` (`docs/d30-section-b-scan-chase.md` — sheet-1 scan review is
   exhausted; owner continuity is required).
4. **Retire the D6 memory-map oracle.** Chip-removed continuity now proves
   D6.12->D8.15, D6.11-/->D8.15, and D6.11-/->D6.12, invalidating the earlier
   installed-PROM joined reading; D6.11 instead reaches D2.15/-WREQ. Find the
   actual driver for the older-sheet D92.5/R12.2 RAM branch and confirm the
   D13.12->D6.13/.14 enable branch. The complete D6.9->D13.1,
   D13.2->D37.4, D37.6->D58.9 endpoint chain is owner-confirmed. Recheck the surprising D13.12->D16.13 report
   with D16 removed. Capture the five live RAM-read levels named by
   `docs/d6-runtime-path-diagnostic.md`. All eight raw A7..A5 rows leave pin 9
   high at the `B37A` RAM-read failure; resolve the endpoint/polarity path by
   measurement, not assumption.
5. **Map the factory Вид В modifications.** The solder-side trace cuts
   (poz. 150/159) at D56, D15, D14, and D11 are drawn design changes; exact
   modified pads, removed segments, and replacement nets remain a P0 mapping
   hold (`docs/factory-modification-disposition.md`).
6. **Disposition all remaining source-risk nets and omitted endpoints.**
   236 source-risk nets and 9 official FDC devices with untraced functional
   pins remain (`docs/replica-bringup-verification-points.md`,
   `docs/board-fidelity-gap-ledger.md`). Anything affecting boot, memory, bus
   direction, interrupts, or video timing must be source-proven, measured, or
   explicitly redesigned before release.

Source-model state feeding this work: the source PCB passes all 2239/2239
net-assigned PCB-scoped board-JSON endpoints and has zero electrical placement
collisions (`docs/source-pcb-drc.md`); 61 endpoints on bracket-mounted
S1/X3/X4/X8/X9 are intentionally excluded in favor of their physical A-point
cable landings, and off-board S4 is likewise outside PCB-pad scope while its
three switch contacts remain modeled nets (`docs/s4-interrupt-boundary.md`).
The routed PCB remains the sole endpoint-coverage failure. The July photo workflow is
complete as a registration/review scaffold: all
626 observations have dispositions, 36 rows are accepted evidence, and the
other 590 remain measurement requests (`docs/photo-registration.md`).

Exit criterion: every required functional endpoint is modeled in both source
and routed PCBs; LVS, DRC, boot, and cosim checks remain green; the generated
design-release reports contain no P0 blocker.

Active generated boundary/gate documents — each names its own pending hold,
and `docs/owner-measurement-shortlist.md` queues them for the next hardware
session: `replica-bringup-verification-points.md` (endpoint coverage),
`unmodeled-footprint-inventory.md` (9 FDC devices),
`factory-modification-disposition.md` (Вид В pad mapping),
`assembly-drawing-extraction.md` (wire-table pin mapping),
`d30-section-b-scan-chase.md` (D30 section B continuity),
`routed-refresh-audit.md` (routed-board convergence),
`io-decode-boundary.md`, `memory-timing-boundary.md`,
`d41-timing-boundary.md`, `s4-interrupt-boundary.md`,
`master-oscillator-boundary.md`, `video-analog-boundary.md`,
`main-board-erc-parity.md`, `board-fidelity-gap-ledger.md`,
`decap-value-fidelity.md`, and `firmware-gap-ledger.md` (PROM truth, also
gating the programmable-parts blocker below).

### P0: programmable parts

All four small-PROM dumps (D2 `.037`, D6 `.038`, D8 `.039`, D94 `.092`) are
validated physical raw tables backed by repeated matching captures including a
power cycle; `hdl/sim/prom_fallback_tb.v` pins each HDL table to its validated
hex, and the two capture validators (К556РТ4 and К155РЕ3) enforce the repeated-
read discipline (`docs/firmware-gap-ledger.md`). Compare against independent
reads or original programming files if those surface. The deterministic
D15/D16 `ekta37` split and 2764-class device decision are recorded in
`docs/eprom-programming-images.md`.

The runnable boot does not yet execute from all four physical tables. The
adoption road, in dependency order:

1. **D2 `.037` — already executes in boot.** `wait_prom_037` drives the
   measured D30/R29 READY path. The open D30 pins 8/11 and the `H` edge
   contact are P0 connectivity item 3, not a PROM gap.
2. **D8 `.039` — content executes, enable is still derived.** The physical
   table drives all eight ROM-socket selects; its `E_N` input is the joined
   D6 conductor, so full adoption completes with step 3.
3. **D6 `.038` — the one remaining memory-map stand-in.** The runnable
   selects still come from the non-LVS `decode_prom_functional` oracle; a
   direct substitution fails the checkpoint-resume boundary at RAM `B37A`
   (P0 connectivity item 4 holds the measurements). After the joined
   conductor's downstream D8/D13/D92 timing is reconstructed, switch the
   runnable selects to the physical `decode_prom` outputs, rerun the ekta37
   boot, EKDOS `A>`, disk-BASIC `READY`, Monitor 3.3, and checkpoint-resume
   guards byte-identically, then delete the functional oracle and its LVS
   exclusion. `docs/d6-firmware-mode-coverage.md` bounds what must be proved
   first (boot exercises only physical modes `000`/`001`).
4. **D94 `.092` — content adopted, boot still bypasses the quadrant.** The
   structural ВГ93 is inert and EKDOS boots on the behavioral `fdc_1793`.
   Adoption requires P0 connectivity item 2 plus D93 functional closure,
   after which the boot's FDC accesses move to the D94-decoded strobes and
   `fdc_1793` is retired.

Adoption exit criterion: `prom_fallback_tb` equality stays green and every
boot guard passes with zero functional PROM stand-ins.

Exit criterion: every populated programmable part has a burnable file,
checksum, device/pinout decision, and provenance. Any functional replacement
for an unavailable PROM must be documented and tested as a redesign.

### P1: fabrication review

After connectivity and programmable-part decisions stop changing:

1. Regenerate the schematic, source PCB, routed PCB, Gerbers, drill, renders,
   BOM, and checksum files on the CI toolchain.
2. Run LVS, behavioral guards, endpoint coverage, ERC/parity, DRC, package
   geometry, power-trace, and independent Gerber-render checks; also overlay
   the exported copper on the registered owner photographs (Mimeo-1-style
   artwork-over-photo validation) as an independent fidelity check.
3. Resolve changed DRC classes explicitly; do not carry blanket waivers across
   geometry changes.
4. Run `kicad/check_replica_manufacturing_ready.sh`. It must report a released
   design, not merely a coherent package.
5. Upload only the newly generated ZIP and preserve vendor preview/settings and
   order evidence using `docs/replica-order-evidence-template.md`.

## Blocked on external evidence

- **Owner measurement session:** `docs/owner-measurement-shortlist.md` is the
  queued, prioritized ask list for the next hardware session; it covers every
  P0 connectivity item above.
- **Community requests:** use `docs/community-prom-media-request.md` for
  independent PROM corroboration, Baltijets programming-disk payloads,
  JUKU-1 media provenance, and cartridge BASIC artifacts.
- **Document gap:** the remaining item for this drawing family is the
  `.009 Э3` electrical-schematic revision, if it survives. A 2026-07-14 web
  sweep confirms it is not public anywhere; the Arvutimuuseum team physically
  recovered the Baltijets archive in Narva (Nov 2024), so asking them whether
  unscanned sheets include the `.009 Э3` and the НГМД block `ДГШ3.065.008`
  documentation is the highest-value document lead.
- **Community coordination lead:** juku3000 issue #25
  (<https://github.com/infoaed/juku3000/issues/25>) shows the MAME driver
  maintainer hunting the same FDC-era schematic; the MAME driver's own TODO
  still reads "work out how the floppy interface really works", and the local
  validated К556РТ4/К155РЕ3 dumps appear to be published nowhere else —
  sharing them and the ИЕ7/КП12 findings is a two-way exchange opportunity.
- **Separator/precomp references:** WD FD179X Application Notes (June 1980),
  Рюмик's «Контроллер дисковода» survey, and the Чеботарев Радиолюбитель
  11/92 article — sources and URLs are recorded in
  `ref/wd1772-vg93/README.md`; see the probe predictions in P0 connectivity
  item 1.
- Recheck external sources only for a named blocker; the current inventory is
  `docs/source-coverage-audit.md` (2026-07-11 audit: MAME driver unchanged,
  museum `JUKUROMS.ZIP` duplicates local ROMs, `CASTOOLS.JUK` is cassette
  media, not the programming disk).

## Parallel work

### Parts and assembly preparation

- Use `docs/replica-dual-config-bom.csv` as a planning BOM, not a shopping
  cart. Programming, circuit-review, and mechanical-review rows remain gated.
- Verify candidate WD1793/4164-family parts for exact pinout, timing, voltage,
  footprint, and seller stock before buying.
- Buy/test long-lead parts early only when the choice cannot force a board
  change. Assemble sockets first and verify rails with no ICs installed.

### Digital-twin fidelity

The twin is already sufficient as a boot/FDC/BASIC oracle. Further work should
serve physical bring-up or historical fidelity:

1. Replace the simulation-only framebuffer read port after D41/shared-DRAM
   slot timing is evidence-complete.
2. Preserve reset-to-EKDOS and disk-BASIC guards while physical FDC wiring is
   corrected.
3. Revisit cartridge BASIC only when a complete artifact or documented loading
   procedure appears; do not invent missing pages.
4. Extend sound/serial behavior only to answer concrete bench questions.

## Physical bring-up sequence

Once a released board and programmed parts exist:

1. Bare-board shorts/continuity and connector polarity.
2. Current-limited rails, including derived -5 V, with no ICs seated.
3. Oscillator, reset, 8080 phases, READY/STSTB, then an 8080 free-run/NOP
   test (0x00 forced on the data bus, address lines counting) before trusting
   ROM/RAM, and first ROM fetch.
4. ROM decode and RAM write/read/refresh.
5. Video timing and composite output.
6. Keyboard scan and Monitor/ROM commands — **Tier 1**.
7. FDC with a floppy emulator, then beeper and serial — **Tier 2**.
8. Factory PROMs, period parts, original peripherals, and surviving-machine
   comparison — **Tier 3**.

## Milestones

- [x] Structural model boots and matches the software oracle.
- [x] EKDOS and disk BASIC reach visible prompts in uninterrupted HDL.
- [x] Current engineering PCB package is reproducible and DRC-clean within its
  modeled scope.
- [x] Deep value-level cosim guard reaches `CTRACE-END` across the default
  130,000-read window and fails on any address/data divergence.
- [ ] P0 physical connectivity is complete and rerouted.
- [ ] Every required PROM/EPROM has verified contents and programming evidence.
- [ ] Runnable boot executes from all four physical PROM tables; the D6
  memory-map oracle and the behavioral FDC bypass are retired.
- [ ] Main-board design release passes; board is ordered.
- [ ] Functional parts kit is received and tested.
- [ ] Replica completes Tier 1 bring-up.
- [ ] Replica completes Tier 2.
- [ ] Replica completes Tier 3.

## Fixed decisions

- Historical evidence outranks emulator inference; `kicad/juku.board.json`
  records the current interpretation and provenance.
- The replica remains a 2-layer, 310 x 266 mm board unless new physical
  measurement contradicts it.
- Functional substitutions are allowed for Tier 1/2 only when electrically
  verified; Tier 3 requires historically appropriate parts and dumped PROMs.
- DRC, package checksums, or LVS of the modeled subset cannot alone authorize
  fabrication.
