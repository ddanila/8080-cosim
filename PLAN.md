# PLAN — working physical Juku recreation

Status date: **2026-07-16**.

Release status: **DESIGN HOLD / PACKAGE INVALID**. The recorded main-board ZIP
is a checksum-reproducible historical engineering snapshot, not fabrication
authorization. The accepted W14 topology invalidates its routed copper and DRC
disposition; a new package must wait for P0 netlist freeze and rerouting.

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
| Digital twin | `cosim` and `juku_top` boot ekta37; framebuffer and keyboard guards pass; uninterrupted HDL reaches EKDOS `A>` and disk BASIC `READY`; Monitor 3.3 reaches its cursor and selected commands; the cosim-referenced deep guard reaches `CTRACE-END` across 130,000 reads; runnable selection comes from the validated physical D6 table under the explicitly provisional `~D0`/`~D3` fit, while the old functional decoder is retained only as a diagnostic comparison | Confirm or remove the D6 per-output fit with the corrected-reader re-read or operating-level probe across the separate D6.12/D8 ROM-select and D6.9/D13/D37/D58 timing paths, and close its physical A7 driver; exact physical shared-DRAM video-slot/DOUT timing, complete controller behavior, cartridge BASIC loading, and analog behavior |
| Connectivity | `sync/check.sh` reports 108 mapped instances and 279 matched nets; the physical D2/D6 PROM tables, measured D2/D30/D105/D13 READY/DBIN handoff, D35 frame-interrupt inversion, D41 timing rails, reset/USART paths, D7 strobe topology, and the adopted photo/wire-table endpoints are source-modeled and LVS-visible | Routed-snapshot parity, omitted remote endpoints, behavioral correctness, analog waveforms, and historical correctness of assumed nets |
| PCB package | The tracked routed artifact was DRC-clean within its former modeled scope; the accepted W14 topology now deliberately invalidates that stale route and its saved manufacturing packet until the P0 netlist freezes. The preserved refresh checkpoint `kicad/juku_routed_candidate.kicad_pcb` has 296 footprints, all 2,383 pad identities, zero internal unconnected items, and zero shorts, clearance, crossing, hole, dangling, or edge findings | The routed artifact still predates accepted D2/D94, reset/USART, and harness endpoints. Its stale copper produces two W14-related shorts and two opens: old PHI2 copper still touches D35.12, and a D53_Y0_R49 track crosses W14.2. The refresh checkpoint is intentionally not current-source copper: later corrections leave 49 pad-net mismatches and 138 moved pads across D5/D7/D8/D9/D35/D37/D38/D50/D51/R13/R14; it also lacks the fourteen A:7/A:8/A:10/A:11/A:14/A:19/A:20 pads. It copper-routes all ten factory insulated-link nets. The source PCB now preserves A:7, A:8, A:10, A:11, A:14, A:19, and A:20 as landing-island pairs joined only by assembly wires W7/W8/W10/W11/W14/W19/W20; the other six `А:N` terminals and three island splits remain unmodeled. All twenty drawing-pixel endpoints are guarded, both A7/A8/A10/A11/A14/A19/A20 terminals plus the D38-side A9 and C96-side A12 joints are board-fitted/island-assigned, and the A7/A8/A11/A14 cut-length discrepancies are explicit. The other four PCB terminals remain unpromoted; a common raw solder image places A14B 58.911 mm from D41.1, and W14 now preserves the distinct PHI2 landing islands. Both routed artifacts are convergence evidence, not adoptable production copper (`docs/factory-wire-route-fidelity.md`). Register/split the remaining islands, then refresh/reroute and adopt the manufacturing packet only after the functional P0 netlist freezes |
| Sources/media | Factory drawings, 16 Baltijets PDFs, ROMs, EKDOS source, raw disks, system binaries, 50 owner photographs, validated physical D2 `.037`/D6 `.038`/D8 `.039`/D94 `.092` dumps, 26 photographs of `ДГШ5.109.009 СБ` sheet 1, the ДУБЛИКАТ scan of its sheets 2-6 (таблица соединений, transcribed), and owner RE3 scans are local and checksum-guarded | Baltijets programming-disk payloads, remaining continuity reads, and the cartridge BASIC loading procedure |

The recorded upload ZIP SHA256 is
`7df2a6e2927c62313275f3f5713e2b4cf3622c3c782b795cf41b27c8f3bfff46`.
Do not send this saved package to a fabricator. After the blockers below are
closed and the corrected board is rerouted and reviewed, regenerate every
fabrication file and gate again.

## Highest-priority work and evidence boundary

These are ordered. The automatic D6 analysis and corrected-reader firmware are
complete; item 1 now waits on the exact re-read or operating-level observation
named below. Items 2-3 remain preservation requirements while connectivity is
measurement-gated.

1. **Physical D6 `.038` firmware — PROVISIONALLY ADOPTED into the runnable twin
   (owner-directed 2026-07-15); pending a physical level-probe to confirm.** The
   runnable twin now runs its memory map from the physical `decode_prom` (not the
   oracle), with a per-output correction (`rom_sel_n=~D0`, `roe_n=~D3`; D1/D2
   direct; A7=0) that boots byte-identical to cosim across the full guard suite.
   This is a documented FUNCTIONAL FIT — the reader/dump are faithful and
   `D6.12->D8.15` is recorded direct, so the two inversions are not yet physically
   justified. The owner chose to adopt provisionally to unblock progress; the raw
   dump is preserved untouched and the reset-fetch level probe (below) will
   promote this from provisional to confirmed (or reveal the true cause). Bench
   experiment record (the basis):
   physical `decode_prom` with A7=0 boots **byte-identical** to the cosim value
   oracle across the full suite — `boot_check`, the 130,000-read `cosim_check`
   (`CTRACE-END`), EKDOS `A>`, disk-BASIC `READY`, jmon33 Monitor, BASIC-cart,
   `prom_fallback`, and LVS. So the chip's **contents encode the correct memory
   map**: with A7=0 the boot modes land in rows `011`/`010`, where word `1` is
   the ROM overlay and word `8` is RAM — matching cosim's PC1/PC0 banking. That
   de-risks the map and is the real progress here.
   **But** the byte-identical run required a *per-output polarity* with no clean
   physical basis: `rom_sel_n = ~D0`, `roe_n = ~D3` (inverted) while `rev = D2`,
   `ram_sel_n = D1` (direct). That mix contradicts measured evidence — continuity
   makes `D6.12->D8.15` a **direct** conductor into an active-low `E_N`, and the
   model already has `D13` inverting in the `roe_n->D58` chain, so a byte-correct
   boot needs an inversion between `D6.9`/`D13` (and `D6.12`/`D8`) that is neither
   measured nor modeled. A uniform complement (the `d6_038.asserted` table) does
   **not** work either: it flips `rev`, which disables the D9 io-decode the boot
   needs. So the earlier "the asserted complement resolves it in simulation"
   claim was wrong. Per the fixed decision that measured evidence outranks
   inference, this fit is committed only as an explicit, owner-directed
   PROVISIONAL adoption (labeled in `hdl/juku_top.v` and the D6 docs), not as a
   proven result; the level probe below is required to confirm it.
   Gate-chain audit (2026-07-15): D13 (К555ТЛ2) inverts and D37 (К555ЛА3) is a
   NAND, both datasheet-correct, so the modeled chain requires `D6.9`=0 for the
   `B37A` RAM read and `D6.12`=0 to select ROM — but the raw `.038` dump has both
   high in those regions, while `D6.10`->D9 (`rev`)=0 works direct. The mismatch
   is localized to the D6 pin-9 and pin-12 output paths only.
   D13 = К555ТЛ2 (inverter) is owner-confirmed (2026-07-15), so that hypothesis
   is closed and the model is right there. The РТ4 reader's logical contract
   was also audited: its address/data pin order matches the HDL model exactly
   (no permutation), and
   К556РТ4 = 82S126/3601/74S387 is a NON-INVERTING open-collector PROM (virgin=0,
   fuse=1; a pull-up reads the stored data directly), so the pull-up does not
   invert (datasheet vendored at
   `ref/datasheets/82s126-556rt4-256x4-oc-prom.pdf`; D8 РЕ3 also boots from its
   raw `.039`, excluding a universal raw/asserted convention error). The
   original RT4 capture's electrical loading is not yet independently closed.
   Consumer-side chip-polarity audit (2026-07-15,
   against the vendored datasheets) also closes the enable-polarity hypothesis:
   D8/РЕ3 = SN74188 has an active-low enable (as modeled), and D13 (К555ТЛ2
   inverter), D37 (К155ЛА3 NAND) and D58 (ИР82 active-low OE) are all
   datasheet-standard as modeled -- no chip is mis-modeled. With pin order, chip
   senses, and a uniform complement excluded, the remaining alternatives are a
   **series inverter on the `D6.12->D8` and `D6.9->D13` conductors, OR an
   electrical/provenance error in the D6 dump's D0/D3 bits**.
   **Sim narrowing (2026-07-15):** driving the runnable selects from the physical
   table under three transforms — only inverting **D0 (pin 12 -> D8) and D3
   (pin 9 -> D13)** while leaving D1/D2 direct boots byte-identical across the
   full guard suite; a uniform 4-bit complement fails (11.2 us) and inverting
   only D3 fails immediately (2.3 us). So the anomaly is genuinely per-pin on
   exactly the two РТ4 outputs feeding D8 and D13.
   **Decisive test:** since `D6.12->D8.15` is owner-recorded
   as DIRECT (`docs/owner-measured-facts.md`; a photo re-read also looks direct),
   the effective inversion is not visible in the known copper. The original reader wiring
   (`tools/rt4_dumper/rt4_dumper.ino`): PROM pin 9 (D3) is read on Arduino **D13,
   the on-board LED pin** (LED + series resistor to GND) -- a classic gotcha that
   can drag an open-collector HIGH down. That risk alone cannot explain a full
   per-pin complement: the D2 capture read all four channels identically in both
   states, and D6 D3 already reads high in 238/256 rows. Reader revision 2 now
   moves D3 to A0, controls /CE from A1, and refuses to dump unless all four
   disabled outputs release to a stable `F`. The decisive step is a **D6 re-read
   with that corrected reader**, after a byte-identical known-D2 check, compared
   against the current `d6_038.raw.bin`. A cheaper cross-check is measuring the D8.15/D6.12
   operating LEVELS during a ROM fetch (continuity is already done). If the
   re-read flips D0/D3 in the affected rows, the physical table then boots
   directly with no transform.
   **Status: provisionally adopted.** The runnable twin now boots from the
   physical table (with the `~D0`/`~D3` correction) byte-identically; the oracle
   is retired from the boot path (`decode_prom_functional` kept in `devices.v`
   only as the B37A-diagnostic reference). The level probe / corrected re-read
   promotes this to confirmed: if it shows D0/D3 flipped in the raw dump, the
   model correction can be dropped and the (corrected) table used directly; if it
   reveals a real consumer-side inversion, the correction becomes justified as-is.
   None of this changes copper; the only D6-area netlist ask remains the
   D105.1/A7 driver (P0 connectivity item 4). The same resolution promotes VJUGA
   workbench Phase 2, which routes its decode through the same physical D6 РТ4
   chip (`spinoffs/minimal-vga/docs/workbench-plan.md`).
2. **Preserve routing convergence until netlist freeze.** The deterministic
   router and conflict-derived INTR rip-up workflow produced the preserved
   routing checkpoint with zero opens and zero electrical-category DRC
   findings (`docs/routed-refresh-audit.md`). Its ten factory wire nets are
   held from adoption until the twenty paired A-point landing coordinates and
   copper-island splits are modeled. A:7, A:8, A:10, A:11, A:14, A:19, and A:20 are the first
   historically faithful splits: registered landings on separate PHI1, STSTB,
   W10_QA_SEL, MEMR, PHI2, MEMW, and S_TTL islands joined only by W7/W8/W10/W11/W14/W19/W20.
   All twenty endpoints are now registered
   in original drawing pixels. Both A8/A10/A11/A19/A20 terminals and the
   D38-side A9 terminal are now fitted to their physical joints and copper
   islands; both A7/A14 remote-joint pairs and the C96-side A12 joint are now
   fitted too, leaving four PCB coordinates/island assignments pending. A14B,
   A7B, and D41.1 now share one raw solder image and calibrated frame: A14B is
   58.911 mm from D41.1, clearing the former 0.784 mm collision. The source now
   preserves separate PHI2 landing islands joined only by W14. Both
   A13 ends have now been exhausted across registered component/solder
   panoramas: D13.1/D92.1 are bare at both faces, the C95-side and post-D38
   remote corridors lie under the factory-wire bundle/mastic junctions, and no
   printed 13 or unassigned third backside joint is exposed. They remain null
   deliberately rather than borrowing nearby A8/A9 joints. The
   D40-side photo frame beside the printed A7/A14 joints is now fitted on both
   faces, and legacy endpoint seeds that mislabeled the visibly marked
   КР531ИЕ17 as D35 have been withdrawn. The marked D1 CPU and its complete
   2x20 pad field are likewise fitted on both faces, isolating the separately
   printed D1-side A7/A14 joints below the package. The remaining D51-side A9
   joint has been chased across six overlapping
   component tiles and is consistently hidden beneath the factory-wire bundle
   and mastic, so its visible wire approach is not promoted as a landing.
   (`docs/factory-wire-route-fidelity.md`). Do not replace
   `kicad/juku_routed.kicad_pcb` yet: copper produced now survives later
   netlist changes through the per-net quarantine mechanism, but final
   production reroute/adoption waits for the P0 functional netlist to freeze,
   followed by repeated endpoint-parity, DRC, and visual review.
3. **Preserve the adopted factory wire-table construction through release.**
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
   record a deliberate redesign/DNP decision. D93.40 `VDD_12V` is now
   owner-confirmed on the +12 V rail (`docs/d93-pin40-photo-chase.md`).
   D106.7 Q3 -> D93.26 RCLK is photo-closed;
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
2. **Finish D94 `.092` connectivity.** Content truth is closed; direct owner
   continuity proves D94.15->D93.3, D94.2->D99.8/GND, D94.3->D93.4,
   D94.4->D93.2, and D94.13->D104.7 plus a +5 V pull-up. An exposed-socket
   component view now closes D94 D4/pin5 to the internally NC/back-bias D93.1
   socket contact. D5/pin6 is photo-bounded to a plated layer handoff, but the
   available cross-side fits do not uniquely identify its continuation. Resolve
   the D5-D7 destinations, D104.10, both pull-up resistor references (D94.13 and
   the apparently pull-up-only D94.1),
   and later recheck the D29.4/IORD conflict noted in the source model. The
   former BA11..BA15 assignment was an unproved scaffold analogy and is retired;
   all five actual D94 inputs are now owner-mapped
   (`docs/d94-reconstruction-constraints.md`). A reflected D104 photo fit now
   proves that pin 10 has no B.Cu departure in two backside views; its possible
   F.Cu departure is hidden by the same vertical white wire in both component
   overlaps. The functional output is retained on an explicit singleton
   boundary, reducing the remaining D104.10 ask to targeted continuity rather
   than permitting an inferred no-connect.
3. **Finish the measured WAIT/READY edge boundaries.** The D2/D30/D105 path
   is adopted; D30.11->D105.2/D13.4/D11.20 and D30.8->D29.7 are now
   owner-confirmed. Resolve only the exact edge contact/pull-up for `H`
   (`docs/d30-section-b-scan-chase.md`, `docs/d105-h-boundary.md`).
4. **Close the remaining D6-area netlist asks.** Chip-removed continuity now
   proves D6.12->D8.15, D6.11-/->D8.15, and D6.11-/->D6.12, invalidating the
   earlier installed-PROM joined reading; D6.11 instead reaches D2.15/-WREQ.
   The D6.11->D92.5/R12.2 branch is now owner-confirmed, joining the already
   measured D6.11->D2.15/-WREQ conductor. D13.12->D6.14
   continuity plus visually confirmed bottom-layer D6.13<->D6.14 copper closes
   the enable branch. The complete D6.9->D13.1,
   D13.2->D37.4, D37.6->D58.9 endpoint chain is owner-confirmed. The remaining
   copper-truth asks are: identify the driver or pull of the D6.15/D105.1
   conductor (the only D6-area net still missing an endpoint), recheck the
   surprising D13.12->D16.13 report with D16 removed. The D37.5 second NAND
   input is already source-closed by the native sheet-2 route
   MEMR->D33.3/.4->D37.5 and is now regression-guarded together with
   D13.2->D37.4 and D37.6->D58.9. Simulation has narrowed the former
   all-mode `B37A` contradiction to the exact D0/D3 transform, but source truth
   still waits on the corrected-reader D6 re-read or the operating-level
   alternative in highest-priority item 1. The five live RAM-read levels named
   by `docs/d6-runtime-path-diagnostic.md` become Tier-3 confirmation asks once
   that gate closes and the guarded adoption run is green.
5. **Map the factory Вид В modifications.** The local Вид В details at D56,
   D15, D14, and D11 mix solder/copper context with assembly callouts. Note 11
   proves position 150 is tubing fitted at solder locations, not a cut; only
   the D15 detail explicitly says `Разрезать`. D15 is
   now photo-closed: two independent component views register the executed cut
   between the auxiliary D15.8/A2 and D15.9/A1 landings, and reflected solder
   copper confirms both pin destinations. The clean source already preserves
   the resulting separate A2/A1 nets; the unmeasured auxiliary-hole geometry is
   not invented. D14 is now partially photo-closed: notch-oriented registration
   maps both package rows, and two component views prove the position-159
   D32.4/GND-to-D14.1 copper link now preserved by the source model. Exact
   D56 geometry is now registered: three component views identify the actual
   notch-down К155АГ3 package, held-out-validated component/reflected local fits
   replace the displaced global seeds, and two solder views map all three
   callout locations as the separate left annulus plus D56.5/D56.12. Visible
   bare-board gaps separate both package pads from the adjacent rail, but the
   installed item-159 conductor/material is not electrically assigned and no
   D56 net change is inferred. D14's fifth landing
   is now registered in two component views at `(207.887, 49.900) mm` with
   `0.011 mm` cross-view disagreement; its conductor, three long traces, and
   right-row dogleg remain held. Both reflected solder overlaps place the D14
   locality inside the same scraped/reworked two-row field, while the component
   views hide the immediate dogleg under the body; D14.2/.7 are therefore
   photo-exhausted direct-continuity asks. At D11,
   two component views now register the L trace and four position-159 solder
   locations and exclude the previously cited pins-4–6 solder scar as a
   different feature;
   held-out-validated component and reflected package fits now project the field
   into four overlapping solder photos. The upper point is rail-obscured and the
   lower three do not form a unique four-hole match, so imagery is exhausted and
   direct continuity of the bridge, D11 pin/net, and remote endpoints remains
   the P0 hold
   (`docs/factory-modification-disposition.md`).
6. **Disposition all remaining source-risk nets and omitted endpoints.**
   217 source-risk nets and 9 official FDC devices with untraced functional
   pins remain (`docs/replica-bringup-verification-points.md`,
   `docs/board-fidelity-gap-ledger.md`). Anything affecting boot, memory, bus
   direction, interrupts, or video timing must be source-proven, measured, or
   explicitly redesigned before release.

Source-model state feeding this work: the source PCB passes all 2263/2263
net-assigned PCB-scoped board-JSON endpoints, with 61 endpoints on
bracket-mounted S1/X3/X4/X8/X9 intentionally excluded in favor of their
physical A-point cable landings
(`docs/replica-bringup-verification-points.md`); it has zero electrical
placement collisions (`docs/source-pcb-drc.md`) and no undeclared non-power
package endpoints (`docs/package-endpoint-coverage.md`). Off-board S4 is
likewise outside PCB-pad scope while its three switch contacts remain modeled
nets (`docs/s4-interrupt-boundary.md`).
The routed PCB remains the sole endpoint-coverage failure. The July photo workflow is
complete as a registration/review scaffold: all
614 observations have dispositions, 33 rows are accepted evidence, and the
other 581 remain measurement requests (`docs/photo-registration.md`).

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

1. **D2 `.037` — executes in boot, polarity not yet pinned.** `wait_prom_037`
   drives the measured D30/R29 READY path. D30 pins 8/11 are owner-closed; the
   `H` edge contact is P0 connectivity item 3, not a PROM gap. Because wait
   states are invisible to the value-level guards, the boot pass does not
   decide raw-vs-asserted polarity for the РТ4 reader; highest-priority item 1
   decides it together with D6.
2. **D8 `.039` — content executes, enable is still derived.** The physical
   table drives all eight ROM-socket selects; its `E_N` input is the separate
   D6.12 ROM-select conductor, so full adoption completes with step 3.
3. **D6 `.038` — physical table provisionally executes; output polarity remains
   unconfirmed.** Runnable selects come from `decode_prom U_DECODE` and the
   validated physical table, with the sim-only `~D0`/`~D3` correction documented
   in highest-priority item 1; `decode_prom_functional` is no longer instantiated
   by `juku_top` and remains only a diagnostic comparison. A direct uncorrected
   raw-table substitution fails the checkpoint-resume boundary at RAM `B37A`.
   The firmware-anchored analysis shows that the
   raw capture contradicts two independent working functional anchors, an exact
   D0/D3-only transform passes the full suite, and a uniform asserted complement
   fails. Reader revision 2 and its known-D2 control make the next D6 re-read a
   decisive electrical/provenance gate; a reset-fetch level comparison is the
   alternative consumer-side gate that promotes the current provisional fit to
   confirmed physical adoption or removes it. `docs/d6-firmware-mode-coverage.md` bounds
   what the trace proves: boot firmware observes A6/A5 suffixes `11` and `10`;
   A7 is functionally forced to `0`
   for all firmware-reachable maps (A7=1 rows emit only words `D`/`F` and can
   express neither observed banking map), while its physical driver on the
   D105.1 conductor remains the P0 connectivity item 4 netlist ask.
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
  independent PROM corroboration, JUKU-1 media provenance, and cartridge
  BASIC artifacts. The Baltijets programming-disk payloads are presumed lost;
  keep the ask open opportunistically, but nothing on the critical path may
  wait on them. The targeted corrected-reader D6 experiment in highest-priority
  item 1 is on the critical path because it resolves a known contradiction;
  unrelated independent reads remain Tier-3 corroboration only.
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

### VJUGA spin-off — status and Linux-box handoff

VJUGA (the +5 V Z80 bench fixture for the scarce Juku РУ5/РТ4/РЕ3 parts) is a
separate experiment; details in `spinoffs/minimal-vga/docs/workbench-plan.md`
and `docs/phase4-bench-bringup.md`. Status as of 2026-07-16:

- **Simulation + board model DONE.** The Verilog twin boots the real firmware on
  tv80 through the real К565РУ5 + D6 К556РТ4 + D8 К155РЕ3 models; **both decode
  modes** (real РТ4 vs GAL-internal baseline) are byte-identical to cosim
  (`sim/vjuga_boot_check.sh`). Rev-A schematic is 119 refs / 135 nets with the
  decode sockets, mode inverter, jumpers, and observability headers; the
  socket↔twin and observability contracts are enforced
  (`kicad/check_rev_a_physical.py`).
- **Placement DONE and collision-clean.** All 119 parts are placed in
  `kicad/gen_rev_a_pcb.py`; `kicad/check_rev_a_placement.sh` (silk/overlap) and
  `kicad/check_rev_a_footprints.sh` (every modelled pin lands on a real pad)
  both pass. GOST-font silk preview via `kicad/render_silk_preview.sh`.
- **Routing DONE and DRC-clean.** The current 119-ref/135-net board contains
  2,394 tracks on F.Cu/B.Cu, with In1.Cu reserved/fill-checked as GND and In2.Cu
  as VCC. KiCad reports zero violations and zero unconnected items; the Phase 3
  sockets and all observability headers are in the routed artifact.
- **Phase 4 bench tooling DONE in software:** framebuffer-readback oracle
  (`sim/vjuga_readback_check.sh`, validated vs twin + cosim) and the UNO
  single-step sketch + twin reference trace (`tools/vjuga_single_step/`).

**Remaining before the first bare PCB:**

1. **Footprint review items** automation cannot close: physical pin-1 orientation
   of the socketed parts, and confirming the real part variants (USB-C
   receptacle, PTC, TVS) against datasheets.
2. **Run vendor DFM/preview.** The current fab package is regenerated and
   machine-verified; its Gerber/drill ZIP SHA256 is frozen in
   `docs/rev-a-manufacturing-readiness.md`. Vendor preview, live stock, and
   assembly-capability review remain order-time human gates.

Not blocking the bare board, but settle before populating: U24's corrected
GAL22V10 pinout and Gray-coded DRAM timing now pass the slower MK4564-12 limits
at 4 MHz; device-specific compilation/programming remains. Also decide whether
to formally waive the VGA release-gate item for the bench fixture. The formerly
stale real-ROM boot wording and guard are synchronized with the passing proof.
Full order-readiness checklist: `docs/rev-a-manufacturing-readiness.md`.

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
   procedure appears; do not invent missing pages. The 2026-07-15 generated
   firmware-lineage audit proves that 7,224 bytes of the cartridge body are
   byte-identical inside Monitor 3.3 (and differ once in Monitor 2.2), so the
   BASIC implementation itself is recovered; the exact correspondence ends
   before the missing page. The Monitor 2.2 audit source-proves its sole BASIC
   byte correction and closes block 3, but the preservation catalog confirms
   unstable reads for the still-bad final two ROM blocks. An exhaustive bounded
   donor search across all seven related 16 KiB ROMs finds no checksum-closing
   three-byte-context donor and rejects the tempting `0x3BAA` EktaSoft match as
   a different restart-vector initializer; blocks 6 and 7 remain unpatched.
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
- [ ] Current engineering PCB package is regenerated and DRC-clean for the
  accepted topology. The archived ZIP remains reproducible but is invalidated
  by the W14 split and intentionally awaits the P0 netlist freeze.
- [x] Deep value-level cosim guard reaches `CTRACE-END` across the default
  130,000-read window and fails on any address/data divergence.
- [ ] P0 physical connectivity is complete and rerouted.
- [x] Every populated PROM/EPROM has an exact-hash-guarded burnable Tier-1/2
  image, a device/pinout decision, and an explicit provenance boundary.
- [ ] Independent programming files/reads corroborate the four factory PROMs
  and original D15/D16 contents for Tier 3.
- [ ] Runnable boot executes from all four physical PROM tables; the D6
  memory-map oracle and the behavioral FDC bypass are retired. (D6 oracle is
  provisionally retired 2026-07-15 — runnable boot runs from the physical D6
  table under a documented `~D0`/`~D3` fit pending the level probe; the D94/FDC
  behavioral bypass and its `.092` quadrant remain.)
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
