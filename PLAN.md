# PLAN — working physical Juku recreation

Status date: **2026-07-13**.

Release status: **DESIGN HOLD / PACKAGE INVALID**. The saved main-board ZIP is
a checksum-reproducible engineering snapshot, not fabrication authorization;
the current routed board is electrically DRC-clean, but the saved package still
predates accepted connectivity and has not passed the required regeneration
and review gates.

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
| Digital twin | `cosim` and `juku_top` boot ekta37; framebuffer and keyboard guards pass; uninterrupted HDL reaches EKDOS `A>` and disk BASIC `READY`; Monitor 3.3 reaches its cursor and selected commands; physical D6 remains structurally instantiated while an explicit non-LVS decoder preserves runnable memory-map equivalence | Retire the D6 functional decoder by completing joined-conductor D8/D13/D92 timing reconstruction; exact shared-DRAM video-slot timing, complete controller behavior, cartridge BASIC loading, and analog behavior |
| Connectivity | `sync/check.sh` reports 102 mapped instances and 266 matched nets; physical D2/D6 PROM tables, the measured D2/D30/D105/D13 READY/DBIN handoff, D41 timing rails 8/17, the X1.107C `-WREQ` endpoint, the D26.PC7-to-D35 `POF` path, D11 RXRDY/TXRDY into D10 IR2/IR3, D7.3 into physical D29.5/D29.15 `-AMWC`, D7.8 into physical D29.4/D29.16 `-IO/M`, D7.4 onto `MEMW`/D29.1, D7.12/D7.13 as the physical `SYNC`/pin11-feedback strobe, and the shared D7.5/D29.3 `-INHIB` source boundary are source-modeled and LVS-visible | Routed-snapshot parity, omitted remote endpoints, behavioral correctness, analog waveforms, and historical correctness of assumed nets |
| PCB package | The saved routed artifact has 240 footprints and zero KiCad copper clearance, crossing, short, or unconnected findings; MEMR uses a clearance-safe two-via back-layer bridge and the genuine `M5V_DERIVED` rail is complete without D105.10 | The saved 2-layer 310 x 266 mm Gerber/drill snapshot predates accepted D2/D94 and later harness/serial endpoint changes; regenerate and review the package before any order |
| Sources/media | Factory drawings, 16 Baltijets PDFs, ROMs, EKDOS source, raw disks, system binaries, 50 owner photographs, cross-machine physical D2 `.037`/D6 `.038`/D8 `.039`/D94 `.092` captures, 26 photographs of `ДГШ5.109.009 СБ` sheet 1, the ДУБЛИКАТ scan of its sheets 2-6 (таблица соединений), and owner RE3 scans are local and checksum-guarded | Baltijets programming-disk payloads, remaining continuity reads, and the cartridge BASIC loading procedure |

The two-page `.009 ПЭЗ` IC list is now fully transcribed and guarded as 82
factory positions plus 12 programming identities. This corrects the generated
part markings for D13 (`К555ТЛ2`), D41-D43 (`К555ИР16`), D52 (`К555КП14`),
and populated D84-D91 (`К565РУ5Г`), while retaining photo-proved substitutions
such as `КР1533ЛА3` and `К155АГ3`. D60-D83 remain explicit empty expansion
sockets rather than being misreported as factory-populated `.009` ICs.

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
2. **Finish D94 `.092` connectivity.** The validated repeated physical content
   table is adopted. The source model has power and the photo-proven
   D94.1/.2/.3 paths to D93.4/.3/.2
   (`FDC_RE_N`/`FDC_CS_N`/`FDC_WE_N`). Resolve pin 15 and D3-D7 destinations.
   Also continuity-map input pins 10-14: their former BA11..BA15 assignment was
   introduced by the original FDC scaffold only as a same-as-D8 analogy, not
   from `.009` scan or measurement evidence, and is now retired behind five
   explicit input boundaries.
   The corrected horizontal D94/D100/D98 placement must then be rerouted.
   All five remaining output pads and pin 15 now have explicit photo-grounded
   boundary nets, so they are no longer misreported as unused/unconnected;
   their far destinations/source remain unresolved; content no longer is.
3. **Finish the measured WAIT/READY edge boundaries.** Three matching physical
   D2 `.037` reads, including a power-cycled capture, are adopted. Direct owner
   continuity proves D2.12/R6 -> D30.2, D30.5 -> R29 -> CPU READY,
   D30.10/.12 -> R5 pull-up, D1.17 DBIN + pulled-up edge `H` -> D105, and
   D105.6 -> D5.4; D105.12/.13 receive MEMW and D105.11 drives D30.13.
   The factory symbol draws only D2 D0/pin 12; D2 output pins 9-11 are now
   explicit no-connects in the board model (their programmed values remain
   preserved as internal PROM data). Resolve D30 pins 8/11 and the exact edge
   contact/pull-up for `H`. The former D2.12->D105.9 and D105.10->−5 V
   assignments are rejected.

The routed PCB/DSN/SES predate this measured topology. Do not locally restore
the obsolete WAIT copper. The source-placement collision gate is now clear,
but complete rerouting remains deferred until the functional netlist stops
changing; the remaining P0 connectivity work would otherwise invalidate it.

4. **Disposition all remaining source-risk nets and omitted endpoints.** The
   current generated evidence lists 240 source-risk nets and 9 official FDC
   devices with untraced functional pins. Anything affecting boot, memory, bus
   direction, interrupts, or video timing must be source-proven, measured, or
   explicitly redesigned before release.

The sheet-1 D10 SP/EN arrow is now modeled as a +5 V master-mode strap rather
than an unresolved PIC pin. Native-sheet review distinguishes D11's direct
RXRDY/TXRDY loops to IR2/IR3 from the separate off-sheet `(3)` RxRDY/TxRDY
arrows entering IR0/IR1; the latter remain superseded by the `.009` FDC
interrupt assignment.

The older sheet also proves D11 USART RESET pin 21 on the uninterrupted
D13.6 system-reset conductor and D11 main CLK pin 20 on the uninterrupted
D13.4/D105.2 conductor. Both are now modeled in the source PCB and HDL. On the
same sheet directly loops D11 RXRDY/TXRDY to PIC IR2/IR3, now modeled in the
source PCB and HDL. The separately labeled off-sheet arrows into IR0/IR1 are
not D11 and remain replaced by the FDC-era КР1818ВГ93 interrupt assignment.
Full-resolution review separately proves
D11.16 SYNDET on the lower S4 throw and omits D11.18 TXEMPTY from the drawn
USART symbol, so SYNDET is now modeled and TXEMPTY is an explicit NC.
Sheet-2 full-resolution review also closes `LATCH_B` without relying on MAME:
D40 QD/pin11 and D37.2 share conductor tag 7, while D54 CLK0/CLK1/CLK2
pins 9/15/18 are visibly tied on the labeled 1 MHz rail ending at tag 7.
5. **Restore source/routed parity.** The authoritative source PCB contains the
   accepted D2/D94, reset/USART, R94, serial-harness, keyboard-harness, and
   power-cable endpoint changes. The saved routed PCB predates that accumulated
   source work and retains three superseded D93 net names;
   `docs/replica-bringup-verification-points.md` must report full endpoint
   coverage before release.

The source PCB now passes all `2239/2239` net-assigned PCB-scoped board-JSON endpoints; the
off-board S1 and S4 switch contacts are intentionally excluded from PCB-pad coverage.
`docs/source-pcb-drc.md` is the separate physical-placement gate and now passes
with zero electrical pad/item collisions. The former ten pairs came from
carrying the `.006` dashed VT3/VT4 RF option into the `.009` FDC quadrant.
Complete factory-placement coverage and the complete owner component tile set
show only VT1/VT2, while the archived group BOM assigns the extra RF
transistors and adjustable trimmer to `.006`. Fifteen legacy-only parts are
therefore DNP; C9/C10/C11/C12/C15 retain their `.009` factory positions with
explicit target-continuity boundary nets. This clears placement, not the
remaining connectivity or routed-parity gates.
Sixty-one endpoints on bracket-mounted S1/S4/X3/X4/X8/X9 are correctly excluded in
favor of their physical A-point cable landings. The routed PCB remains the sole
endpoint-coverage failure.

The July photo workflow is complete as a registration/review scaffold: all 50
photos are inventoried, the 28-image grid is registered on both sides, and all
626 observations have dispositions. 36 rows are accepted evidence for
five D2 address nets, three D94-to-D93 control nets, the two-sided А:17 and
D98.7/S1.2 wire landings, D98.3/R94.1, and D106.7/D93.26 RCLK; the
D96.8/D99.2 test landings and D99.3 ground observation are also preserved.
Six accepted rows now close the R92/R99 ladder onto D95.14, D101.4, and
D101.8/GND; the other 590 remain
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
4. D94/D100/D98 retain their corrected horizontal posture. Registered owner
   photographs now also identify and space the vertical D106 К555ИЕ7, D28
   К155ЛН3, and D96 КМ555ТМ2 row; the source PCB follows the measured
   D106->D28 `(15.064,-1.442)` mm and D28->D96 `(14.451,0.240)` mm centre
   offsets without promoting unresolved signals. The distinct D95/D101
   К555КП12 packages are also fitted with corrected top-view pin numbering.
   Their photographed right-facing notches, together with D99's, are now
   guarded as 270-degree footprints; D97/D102 retain their independently
   photographed left-facing 90-degree posture. This prevents the former
   centre-correct but physically pin-reversed D95/D99/D101 landings;
   the complete D95/D99 and D101/D97/D102 cluster is now fitted and placed
   from shared raw-image pitch plus the visible board edge. D97 and D102 are
   photo-read `К155АГ3 8901`; the cable-crossed D99 identity is fixed by its
   exposed row ends and factory drawing position. The four guarded centre
   offsets are D95->D99 `(23.895,+0.451)` mm, D95->D101
   `(-11.190,+17.380)` mm, D101->D97 `(23.794,-0.117)` mm, and D97->D102
   `(23.963,-0.249)` mm. A separate factory-drawing affine registration uses
   three of those centres and holds D99/D97 out at 0.910/0.851 mm. It corrects
   vertical C11 between D95/D99 and C15 between D97/D102, and records ten
   still-absent named passives without inventing their electrical endpoints.
   The upper drawing row independently places vertical C12 between D94/D100
   and C9 between D100/D98; a D94-to-D98 interpolation holds D100 within
   1.309 mm. Moving C9/C12 from the false y~95 mm placeholder row to y~34 mm
   removes 13 source-PCB DRC violations. C12's owner-photo site has no
   unambiguous fitted body and C9 is cable-hidden, so neither placement is
   promoted as connectivity evidence.
   Cross-revision reconciliation resolves the remaining collision placeholders
   without moving the proven IC row. The `.006` sheet-2 dashed RF option contains
   VT3/VT4, tapped L1, R73, and their dedicated C13/C14/R68-R77 network; the
   archived group BOM likewise assigns the extra transistors and 4.7 kΩ trimmer
   to `.006`. Neither the complete `.009` assembly placement nor the complete
   owner-board component tile set contains that option. Those fifteen refs are
   DNP on the target. The `.009` drawing instead reuses C9/C10/C11/C12/C15 in
   the D93-D102 quadrant, so those footprints remain with twelve explicit
   continuity boundaries including R67.2 and X6.1. This removes all ten source
   collision pairs while preserving unknown target connectivity rather than
   inventing an RF circuit. The adjacent yellow `680п` part remains C94, not L1.
   The same full-resolution sheet closes the former R66.1 source boundary:
   its `B` arrow is the power legend's `B (+12)`, so R66.1 is now on `P12V`
   rather than an invented PIT `SOUND` input.
   Owner-photo/assembly registration now also places the visibly marked red
   `2к` R67 at `(295.94,125.39)` mm, plus glass VD3 at
   `(299.38,128.40)` mm and the rightmost R66 at `(302.69,128.46)` mm.
   The factory drawing fixes the right-group identities independently of
   colour; these placements do not move the proven IC row. The same cross-source read restores the previously
   omitted populated C94 `680п` capacitor at `(287.07,132.26)` mm; its two
   unread lead destinations remain explicit continuity boundaries. Factory
   registration plus the populated owner photo also restores the complete
   right-edge resistor column R100/R102/R108/R86 at the projected `.009`
   centres; all eight unread endpoints remain explicit boundaries.
   The same factory/owner cross-registration restores populated grey axial C19
   immediately right of D99 at `(292.893,93.574)` mm on a vertical 10 mm lead
   span. Its photographed body leans across the resistor column, but the two
   landings and backside joints remain distinct; value and remote destinations
   are therefore explicit boundaries rather than inferred from that overlap.
   Registered component- and solder-side views now also restore the two grey
   axial C20/C22 capacitors immediately beyond D102 on adjacent 2.54 mm
   columns, each with a 10.00 mm vertical lead span. C20's enhanced body image
   reads `1Н5` verbatim; C22's value and their four remote destinations remain
   explicit continuity boundaries rather than guessed D102 connections.
   The same cross-registration restores populated grey horizontal C16 between
   the upper/lower FDC IC rows and the two red horizontal resistors R92/R99
   below D95. C16 uses the photo-corroborated 12.5 mm lead span; both resistors
   use 10.16 mm spans. Calibrated component copper now closes R92.2-D95.14,
   R92.1-R99.2-D101.4, and R99.1-D101.8/GND. R92/R99 markings and both C16
   destinations remain explicit boundaries rather than inferred from nearby rails.
   Direct raw-photo registration also corrects the marked КР531ИЕ17 D40 into
   the same horizontal row as D41 at `(258.56,140.99)` mm with its notch to the
   right; the former seed was about 15 mm too high. The factory C63 outline lies
   in the now-bracketed D41/D40 gap, but the owner component view shows neither
   a fitted body nor a coherent drilled axial span there. C63 therefore remains
   an explicit factory-intent versus `.009` DNP/removal conflict instead of
   being silently moved from its older generic decoupler seed.
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
   D93.40 is now chased as far as the photographs permit: its corrected solder
   pad has no same-layer departure, while component copper enters the adjacent
   clip-obscured region. `docs/d93-pin40-photo-chase.md` records the exact pad
   coordinates and the required continuity anchors; P12V is not yet promoted.
2. Every functional pin of D28, D95-D99, D101, D102, and D106.
   Registered solder-side copper now closes D106.7 Q3 directly to D93.26 RCLK,
   choosing the Soviet IE7-only recovered-clock output over the Western
   Digital Figure-11 D96-toggle candidate on this target board. The remaining
   first probes are D106.11-D93.27 and D106.14-D93.33. Calibrated solder-crop
   review rejects uninterrupted same-layer paths for both pairs, so test for
   hidden layer handoffs rather than promoting either reference topology. The
   WD-only D106.3-D96.3 and D96.2-D96.6 paths are no longer assumed. The same
   calibrated tile has now been exhausted for D106's static straps and recovery-
   clock input: pins 9/10 remain rail-obscured, while pins 15/1/5 and pin 4 show
   only local copper or layer handoffs with no unbroken path to known P5V/GND/
   clock anchors. Meter those six bounded endpoints, then test the still-open
   D95/D101 select pins against D93.18/.17 and their pin-7 output destinations
   for the period KP12 write-
   precompensation pattern. Existing Juku photo evidence excludes D96 section 2
   and D99 section 1 from the WD roles; neither reference proves Juku continuity.
3. D94 inputs A0-A4/pins 10-14, pin 15, and output D3/pin 4 first; outputs
   D4-D7 still need copper reconstruction for PCB fidelity but are invariant
   released in the captured `.092` program. Then D30 section B and the D105
   WAIT handoff.
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
`master-oscillator-boundary.md`, `video-analog-boundary.md`, `main-board-erc-parity.md`,
`board-fidelity-gap-ledger.md`, `decap-value-fidelity.md`, and
`firmware-gap-ledger.md` (PROM truth, also gating the programmable-parts
blocker below).

### P0: programmable parts

- Compare the validated physical D2 `.037`, D6 `.038`, D8 `.039`, and D94 `.092`
  tables against independent reads or original programming files if those surface.
- The host-side К556РТ4 capture validator is now guarded by a self-test and
  rejects missing, duplicate, unstable, non-complementary, or repeat-mismatched
  D2/D6 reads. It exports raw pin-level and active-low views separately with
  hashes; `docs/rt4-dump-acquisition.md` records the physical provenance still
  required. The separate К155РЕ3 validator now applies the same repeated-read
  discipline to D8/D94 32-byte captures and preserves raw versus asserted
  bytes; the adopted D94 dump still does not replace its missing continuity.
- D2 `.037`, D6 `.038`, D8 `.039`, and D94 `.092` now use validated physical
  raw tables backed by repeated matching captures including a power cycle.
  D8/D94 duplicate board-name files are provenance aliases, not extra reads.
  The owner `.113/.117` scans are not D8 `.039` or D94 `.092`.
- The deterministic low-D15/high-D16 `ekta37` split, image hashes, and
  2764-class device decision are recorded in `eprom-programming-images.md`;
  retain programmer verification and compare repeat physical dumps before
  assembly/Tier-3 claims.

#### Road: physical PROM tables into the full boot

All four small-PROM dumps are adopted as validated data and
`hdl/sim/prom_fallback_tb.v` pins each HDL table to its validated hex, but
the runnable boot does not yet execute from all of them. The explicit
adoption road, in dependency order:

1. **D2 `.037` — already executes in boot.** `wait_prom_037` drives the
   measured D30/R29 READY path in `juku_top`. No content work remains; the
   open D30 pins 8/11 and the `H` edge contact are P0 connectivity item 3,
   not a PROM gap.
2. **D8 `.039` — content executes, enable is still derived.** The physical
   table drives all eight ROM-socket selects in the runnable boot. Its `E_N`
   input is the joined D6 conductor, which the runnable path still derives
   functionally, so full D8 adoption completes with step 3.
3. **D6 `.038` — the one remaining memory-map stand-in.** The runnable
   `rom_sel/ram_sel/rev/roe` selects still come from the non-LVS
   `decode_prom_functional` oracle; the physical table only drives the
   structural join. A controlled direct substitution now passes the fast
   ekta37 boot suite but fails the mandatory checkpoint-resume boundary when
   execution calls RAM at `B37A`. Exhaustive evaluation now proves all eight
   physical modes emit word `8` or `F` there, leaving D6.9 high; disabling D6
   also releases pin 9 high. Mode selection and V1/V2 therefore cannot repair
   the currently modeled D6.9 -> D13 -> D37 path's inactive D58 OE. The focused
   `docs/d6-runtime-path-diagnostic.md` reproduces every tuple without replaying
   the long boot. It additionally proves that checkpoint PC `0484` and RAM target
   `B37A` both emit D6 word `8` in mode `000`, while D8 changes from `EF` (D15
   selected) to `FF` (all sockets released). No D6 output can distinguish those
   reads, and every modeled D8 output currently reaches only its socket CE, so an
   authentic address-sensitive RAM qualifier is still missing. The analysis also
   exposes a cross-revision evidence conflict:
   direct `.009` continuity reported D6.11/D6.12/D13.12 joined and no D8/D9
   continuation, while the source model still retains older-sheet D8/D92
   consumers on the joined conductor. Retirement order: isolate and
   resistance-map those pins and the three D6.9-to-D58 endpoint segments,
   capture the five live RAM-read levels named by
   the diagnostic, reconstruct the joined
   D6.11/D6.12/D13.12/D8.15 conductor's downstream D8/D13/D92 timing; use
   `docs/d6-firmware-mode-coverage.md` (boot exercises only physical modes
   `000`/`001`) to bound what must be proved first; switch the runnable
   selects to the physical `decode_prom` outputs; rerun the ekta37 boot,
   EKDOS `A>`, disk-BASIC `READY`, Monitor 3.3, and checkpoint-resume
   guards byte-identically; then delete the functional oracle and its LVS
   exclusion.
4. **D94 `.092` — content adopted, boot still bypasses the quadrant.** The
   physical table drives the three proved strobes into the structural ВГ93,
   but that instance is inert (`mr_n=1`, `clk=0`) and EKDOS boots on the
   behavioral `fdc_1793` selected by D9 `cs_fdc_n`. Adoption requires P0
   connectivity item 2 (D94 A0-A4 inputs, pin 15 enable source, and D3-D7
   destinations) plus
   D93 functional closure (the D106.7 -> D93.26 RCLK chain, clock/reset,
   drive interface, D100 buffer direction/enable), after which the boot's
   FDC accesses move to the D94-decoded strobes and `fdc_1793` is retired.

Adoption exit criterion: `prom_fallback_tb` equality stays green and every
boot guard passes with zero functional PROM stand-ins; the digital-twin open
boundary for the D6 functional decoder then closes.

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

- Use `docs/community-prom-media-request.md` for independent PROM
  corroboration, programming-disk, and cartridge BASIC requests.
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
