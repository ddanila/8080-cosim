# PLAN — working physical Juku recreation

Status date: **2026-07-11**.

Release status: **DESIGN HOLD**. The saved main-board package is a reproducible
engineering snapshot, not fabrication authorization.

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
| Digital twin | `cosim` and `juku_top` boot ekta37; framebuffer and keyboard guards pass; uninterrupted HDL reaches EKDOS `A>` and disk BASIC `READY`; Monitor 3.3 reaches its cursor and selected commands | Exact shared-DRAM video-slot timing, complete controller behavior, cartridge BASIC loading, and analog behavior |
| Connectivity | `sync/check.sh` reports 99 mapped instances and 234 matched nets | Unmapped footprints, omitted pins, behavioral correctness, and historical correctness of assumed nets |
| PCB package | The saved routed artifact has 240 footprints, no KiCad clearance/short/unconnected-item errors, and a reproducible 2-layer 310 x 266 mm Gerber/drill package | The routed snapshot predates accepted D2/D94 endpoint changes and is not electrically complete |
| Sources/media | Factory drawings, 16 Baltijets PDFs, ROMs, EKDOS source, raw disks, system binaries, 50 owner photographs, 26 photographs of `ДГШ5.109.009 СБ` sheet 1, the ДУБЛИКАТ scan of its sheets 2-6 (таблица соединений), and owner RE3 scans are local and checksum-guarded | Baltijets programming-disk payloads, D2/D94 dumps, remaining continuity reads, and the cartridge BASIC loading procedure |

The saved upload ZIP is
`fab/gerbers/upload/juku-replica-gerbers-drill.zip`, SHA256
`341158da24c356940f763db416e0d54ee81de48bc84632ac97b844e3ea6129f4`.
Do not send it to a fabricator. Regenerate it only after the blockers below are
closed and the corrected board has been rerouted and reviewed.

## Release blockers

### P0: physical connectivity

1. **Complete FDC-era functional wiring.** D93's restored drive-interface pins,
   plus D28, D95-D99, D101, D102, and D106, have package models but no complete
   functional signal closure. Trace each
   required pin end-to-end, or record a deliberate redesign/DNP decision and
   remove the unused function from released artifacts. D93.40 `VDD_12V` must be
   proved against the board's +12 V rail before any power-up.
2. **Finish D94 `.092`.** The source model now has BA11..BA15, power, and the
   photo-proven D94.1/.2/.3 paths to D93.4/.3/.2
   (`FDC_RE_N`/`FDC_CS_N`/`FDC_WE_N`). Resolve pin 15 and D3-D7 destinations.
   The corrected horizontal D94/D100/D98 placement must then be rerouted.
3. **Close the WAIT/READY revision boundary.** D2 inputs and D0/pin 12 are now
   modeled, D105 is modeled and routed, and D30 section A is closed. Resolve
   D30 section B pins 8/11/13 and the pin-10/pin-12 source, then reconcile the
   `.006` D95 inverter after D105.6 with `.009`'s FDC use of D95.
4. **Disposition all remaining source-risk nets and omitted endpoints.** The
   current generated evidence lists 43 source-risk nets and 9 official FDC
   devices with untraced functional pins. Anything affecting boot, memory, bus
   direction, interrupts, or video timing must be source-proven, measured, or
   explicitly redesigned before release.

The sheet-1 D10 SP/EN arrow is now modeled as a +5 V master-mode strap rather
than an unresolved PIC pin. The older RxRDY/TxRDY-to-IR0/IR1 paths are not
promoted because they conflict with the `.009` FDC interrupt assignment and
remain a target-revision continuity question.

The older sheet also proves D11 USART RESET pin 21 on the uninterrupted
D13.6 system-reset conductor and D11 main CLK pin 20 on the uninterrupted
D13.4/D105.2 conductor. Both are now modeled in the source PCB and HDL. On the
older sheet RxRDY/TxRDY explicitly feed PIC IR0/IR1, while D11 SYNDET/TXEMPTY
are omitted from the USART symbol with no conductor. None of those four is
promoted onto the `.009` board: the first pair conflicts with the FDC-era
КР1818ВГ93 interrupt assignment, and the latter pair still needs target-board
NC/continuity proof.
5. **Restore source/routed parity.** The authoritative source PCB contains the
   accepted D2 address inputs and D94 control outputs. The saved routed PCB
   still lacks those eight endpoints and retains three superseded D93 net
   names; `docs/replica-bringup-verification-points.md` must report full
   endpoint coverage before release.

The July photo workflow is complete as a registration/review scaffold: all 50
photos are inventoried, the 28-image grid is registered on both sides, and all
612 observations have dispositions. Twenty-two rows are accepted evidence for
five D2 address nets, three D94-to-D93 control nets, and the two-sided А:17
and D98.7/S1.2 wire landings plus D98.3/R94.1; the other 590 remain
measurement requests. This closes the automated review queue, not the P0
connectivity work. `docs/photo-registration.md` records the method and
`docs/owner-measurement-shortlist.md` is the current hardware-session queue.

The 2026-07-11 photographs of the original `ДГШ5.109.009 СБ` assembly drawing
(`ref/photos/dgsh5-109-009-sb/`) are FDC-era factory assembly evidence, one
document revision closer to the target than the `.006` Э3 scan. Pending
extraction work from that set:

1. Confirm the board model reflects the factory solder-side trace cuts
   («Вид В», poz. 150/159) at D56, D15, D14, and D11 — these are drawn design
   changes, not board-specific repairs. Their existence/locality is guarded by
   `docs/factory-modification-disposition.md`; exact modified pads/vias, removed
   segments, and replacement nets remain a P0 mapping hold. A validated D11
   solder fit has narrowed its visible rework to the area beside pins 4-6, but
   the obscured bridge endpoints are not yet electrically proved.
2. Wires 17 and 18 have documented far ends at S1:1/S1:2 from the sheets 2-5
   wire table. Package-local component evidence maps А:18 directly to D98.7;
   two-sided labeled-pad evidence maps А:17 to a dedicated `A17` footprint on
   `RES_RC`. S1 remains in the schematic/off-board harness but is excluded from
   the generated PCB; the former fictitious on-board S1 header is removed.
3. The assembly drawing and owner component photo identify R94 as the vertical
   220-ohm resistor below-left of D98. Registered package-local copper closes
   its upper terminal to D98.3; `R94.1` is now modeled on `D98_Y1_R94`, while
   the lower `R94.2` endpoint remains an explicit continuity target.
4. Cross-check the corrected D94/D100/D98 placement and connector/off-board
   geometry (X8 300 mm lead, X9 400 mm ribbon, poz. 151 shielded cable)
   before the reroute.
5. Sheets 2-6 (the note-8 таблица соединений plus change registration) are
   acquired as `ref/schematics/dgsh5_109_009_sb_sheets2-6.pdf` and
   transcribed in `ref/schematics/dgsh5-109-009-sb-wire-table.md`. The X9
   X8 power cable and X9 ribbon are promoted as physical A59..A62 and
   A45..A58 PCB landings feeding schematic-only bracket connectors; duplicated
   X8 +5 V/GND conductors and X9's reversed pin order are explicit. Promote
   X3 is likewise promoted as the photo-fitted A21..A32 row; six serial signals
   and CTS/DSR are electrically closed, and photographed R104 closes A21 to
   +5 V through 120 ohms; source junctions also close A22 onto the OC SOUT
   node shared with A32. A27/A28 are source-undrawn, photo-proved cable-only
   reserved contacts. Photo-fitted R18/R30 now restore the source-drawn 33k
   SER_TXD feedback and ground bias on OC SOUT; the physical D3.9->8
   pre-inverter and tied D12.1/.2 inputs replace the former direct-D12 shortcut,
   completing the X3 harness
   disposition. Promote X4 and
   the remaining numbered links only after
   each А:N point is mapped to a package pin.

Next tracing order:

1. D93 pins 15-19, 22-40 and D100 pins 9/11, including the complete drive
   interface, +12 V supply, DRQ/INTRQ, reset, clock, density, output enable,
   and direction.
2. Every functional pin of D28, D95-D99, D101, D102, and D106.
3. D94 pin 15 and outputs D3-D7, then D30 section B and the D105 WAIT handoff.
4. D41/memory timing, factory-wire endpoints (documented in
   `ref/schematics/dgsh5-109-009-sb-wire-table.md`; confirm by continuity),
   connector geometry, and the remaining analog/passive boundaries.
5. Update `kicad/juku.board.json` only from reviewed unambiguous evidence;
   regenerate and reroute after a coherent batch, then rerun all release gates.

Exit criterion: every required functional endpoint is modeled in both source
and routed PCBs; LVS, DRC, boot, and cosim checks remain green; the generated
design-release reports contain no P0 blocker.

Active generated boundary/gate documents — each names its own pending hold,
and `docs/owner-measurement-shortlist.md` queues them for the next hardware
session: `replica-bringup-verification-points.md` (endpoint coverage),
`unmodeled-footprint-inventory.md` (9 FDC devices),
`factory-modification-disposition.md` (Вид В pad mapping),
`assembly-drawing-extraction.md` (wire-table pin mapping),
`io-decode-boundary.md`, `memory-timing-boundary.md`,
`d41-timing-boundary.md`, `s4-interrupt-boundary.md`,
`video-analog-boundary.md`, `main-board-erc-parity.md`,
`board-fidelity-gap-ledger.md`, `decap-value-fidelity.md`, and
`firmware-gap-ledger.md` (PROM truth, also gating the programmable-parts
blocker below).

### P0: programmable parts

- Acquire repeated dumps or the Baltijets programming files for D2 `.037` and
  D94 `.092`.
- Keep reconstructed D6/D8 images labeled as Tier-1/2 fallbacks. The owner
  `.113/.117` scans are not D8 `.039` or D94 `.092`.
- Record the final D15/D16 EPROM split, image hashes, device choice, and
  programmer verification before assembly.

Exit criterion: every populated programmable part has a burnable file,
checksum, device/pinout decision, and provenance. Any functional replacement
for an unavailable PROM must be documented and tested as a redesign.

### P1: fabrication review

After connectivity and programmable-part decisions stop changing:

1. Regenerate the schematic, source PCB, routed PCB, Gerbers, drill, renders,
   BOM, and checksum files.
2. Run LVS, behavioral guards, endpoint coverage, ERC/parity, DRC, package
   geometry, power-trace, and independent Gerber-render checks.
3. Resolve changed DRC classes explicitly; do not carry blanket waivers across
   geometry changes.
4. Run `kicad/check_replica_manufacturing_ready.sh`. It must report a released
   design, not merely a coherent package.
5. Upload only the newly generated ZIP and preserve vendor preview/settings and
   order evidence using `docs/replica-order-evidence-template.md`.

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
   slot timing is evidence-complete. D94's proved outputs belong to FDC control,
   not the video-slot schedule.
2. Preserve reset-to-EKDOS and disk-BASIC guards while physical FDC wiring is
   corrected.
3. Revisit cartridge BASIC only when a complete artifact or documented loading
   procedure appears; do not invent missing pages.
4. Extend sound/serial behavior only to answer concrete bench questions.

### External evidence

- Use `docs/community-prom-media-request.md` for D2, D94, programming-disk, and
  cartridge BASIC requests.
- Use `docs/owner-measurement-shortlist.md` for the next hardware session.
- Sheets 2-6 of `ДГШ5.109.009 СБ` (the таблица соединений) are acquired and
  transcribed; the remaining document gap for this drawing family is the
  `.009 Э3` electrical schematic revision, if it survives.
- Recheck external sources only for a named blocker. The 2026-07-11 audit found
  that the current MAME driver still matches the vendored copy; the museum's
  new `JUKUROMS.ZIP` duplicates the nine local ROMs, and `CASTOOLS.JUK` is
  cassette utility media rather than the missing PROM-programming disk. See
  `docs/source-coverage-audit.md`.

## Physical bring-up sequence

Once a released board and programmed parts exist:

1. Bare-board shorts/continuity and connector polarity.
2. Current-limited rails, including derived -5 V, with no ICs seated.
3. Oscillator, reset, 8080 phases, READY/STSTB, and first ROM fetch.
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
- [ ] P0 physical connectivity is complete and rerouted.
- [ ] Every required PROM/EPROM has verified contents and programming evidence.
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
