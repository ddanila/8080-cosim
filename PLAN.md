# PLAN — working physical Juku recreation

Status date: **2026-07-11**.

Release status: **DESIGN HOLD**. The saved main-board package is an engineering
snapshot, not fabrication authorization.

This is the sole living project plan. It covers the ДГШ5.109.006 processor
module with the `.009` FDC-era population. Historical debug logs and completed
phase diaries belong in Git history, not in this file.

## Definition of done

- **Tier 1 — boots:** a fabricated board powers safely, runs the real ROM,
  produces a usable video signal, and accepts keyboard input.
- **Tier 2 — usable system:** Monitor 3.3, BASIC, EKDOS/floppy, beeper, serial,
  PSU, and keyboard work on physical hardware.
- **Tier 3 — historically faithful:** factory PROM contents, period parts,
  original-style peripherals/enclosure, and comparison with a surviving Juku.

Tape, classroom networking, mouse, and Multibus expansion are outside the
current critical path. The VJUGA/minimal-VGA board is a separate experiment and
is not a prerequisite for ordering or bringing up the replica.

## Verified repository state

| Area | What is proved | What is not proved |
| --- | --- | --- |
| Digital twin | `cosim` and `juku_top` boot ekta37; framebuffer/keyboard guards pass; uninterrupted HDL reaches EKDOS `A>` and disk BASIC `READY`; Monitor 3.3 reaches its cursor and selected checkpoint-resumed commands | Exact shared-DRAM video-slot timing, full controller fidelity, cartridge BASIC compatibility, and analog behavior |
| Connectivity | `sync/check.sh` reports 99 mapped instances and 230 matched nets | Unmapped footprints, pins absent from `board.json`, and the correctness of behavioral models |
| PCB package | 240-footprint routed artifact; no KiCad clearance/short/unconnected-item errors; reproducible 2-layer 310 x 266 mm Gerber/drill package | Electrical completeness or historical correctness of omitted/assumed nets |
| Sources/media | Factory schematic set, 16 Baltijets PDFs, ROMs, EKDOS source, raw disks, system binaries, 50 owner board photographs, and owner RE3 scans are local and artifact-guarded | Baltijets programming-disk payloads, D2/D94 dumps, and the missing cartridge BASIC page/procedure |

The current main-board ZIP is
`fab/gerbers/upload/juku-replica-gerbers-drill.zip`, SHA256
`341158da24c356940f763db416e0d54ee81de48bc84632ac97b844e3ea6129f4`.
It is retained as a reproducible engineering snapshot. **Do not send it to a
fabricator until the release blockers below are closed and the package is
regenerated.**

## Release blockers — close before main-board fabrication

### P0: physical connectivity

1. **D2 `.037` bus/wait PROM and WAIT revision handoff** — D2 D0/pin 12 is now
   routed into D105; A3 is the CAS/video-cycle rail, V1/V2 are grounded, and
   A5/A7 retain explicit `-XACK`/`-WREQ` boundaries. Paired D2/D4 local fits
   now trace D2 pins 1/3/5/6/7 to D4 pins 1/3/5/6/7
   (`A10/A14/A12/A15/A9`), closing every physical D2 input in the model and
   source PCB. The exhaustive non-burnable symbolic table
   `ref/reconstructed-proms/d2_037_symbolic_truth.csv` now fixes the PROM
   address order for all 256 rows while leaving every unknown D0 value as `?`.
   Recover the PROM truth table and reroute the saved snapshot.
   Reconcile the `.006` D95
   inverter after D105.6 with `.009`'s reassignment of D95 to an FDC К555КП12.
2. **FDC support IC signal closure** — D28, D95-D99, D101, D102,
   and D106 now have physical pin models and routed power endpoints; their
   functional signal pins remain explicit continuity boundaries. Trace and route
   each required function, or document a deliberate redesign/DNP decision and
   remove it from the released artifacts. D30 READY section A
   is now modeled through R5/R6/R29. In section B, pins 10 and 12 are visibly
   tied and pins 6 and 9 are documented no-connects; pins 8, 11, and 13 still
   require end-to-end tracing, as does the shared pin-10/pin-12 source;
   the remaining signal-boundary parts are FDC support logic. D105 is now modeled
   and routed, but that alone cannot release the board.
3. **D94 `.092` PROM** — BA11..BA15, power, and photo-traced outputs
   pin 1/D0 -> D93.4/`FDC_RE_N`, pin 2/D1 -> D93.3/`FDC_CS_N`, and
   pin 3/D2 -> D93.2/`FDC_WE_N` are now connected in the model and
   authoritative source PCB. The photographs show no branch from these three
   local PROM outputs to the formerly assumed global I/O-control rails.
   The photo overlay has now corrected horizontal/notch-left D94 and the
   separately identified horizontal/notch-left D100 КР580ВА87 immediately
   right of D94 in the
   authoritative PCB generator; the
   saved routed snapshot still needs that dense bus region rerouted. Resolve
   pin 15 and the remaining D3/D4/D5/D6/D7 destinations, update the model,
   and reroute the corrected cluster in the saved routed PCB.
4. **Release-risk net review** — disposition the remaining source-risk rows in
   `docs/board-fidelity-gap-ledger.md` and
   `docs/owner-measurement-shortlist.md`. Assumptions that affect boot, memory,
   bus direction, interrupts, or video timing must be measured or explicitly
   redesigned; they cannot be deferred as generic “bring-up” items.

#### Queued July photo grind — evidence adopted, registration scaffold complete

The 28-photo 2026-07-10 intake is retained under
`ref/photos/juku-pcb-2/` through Git LFS. It contains a 4x3 component-side grid
followed by a 3x3 solder-side grid, each photographed left-to-right and then
top-to-bottom, plus 7 later component-side views with the КР1818ВГ93
temporarily removed. Intake review confirms that the physical board contains a
КР1818ВГ93 FDC and the populated eight-chip КР565РУ5 bank; the former
non-FDC/unpopulated-RAM photo classification is retired. The removed-package
views expose normally hidden VG93 footprint copper but do not promote a single
new net yet.

The repo-native registration inventory now hashes and orders all 28 images,
records the solder-side mirror convention, validates the endpoint-review schema,
generates three navigation contact sheets, and reproducibly feature-stitches all
12 component and all 9 solder tiles into full-board review panoramas with
source-image projection homographies. Both panoramas are now rectified into a
shared 310 x 266 mm component-coordinate frame and the current 245 unresolved
pads are rendered as refdes/pin overlays on both sides. The historical review CSV contains 496
observations (one original component JPEG and one original solder JPEG per
pad): 490 are explicit measurements, six are accepted two-sided D94
observations, and none remains a candidate; 48
solder observations originally retained geometrically unique nearby circular-
hole snaps as cautionary registration metadata. D94 and D2 now have 28 two-sided
`local-package-fit` observations; the remaining confidence split is 423
`registration-only` and 45 unique-hole snaps. The accepted D94.1/.2/.3 pairs
are the first electrical promotions. Manual
review has classified the two-sided
D93.19/D93.24, D100.9/D100.11, D46.1/D46.15, D54.13, D55.17, D57.9/D57.11,
and D58.11 observations as measurements because package occlusion, parallel
traces, displaced projections, or nearby-hole ambiguity cannot be resolved
photographically. D100.9/.11 now have a validated component fit, but OE ends at
a layer handoff and T remains wire-obscured, so both stay measurements. The
five D2 address-input pairs were subsequently promoted
through the independent D4 solder-row fit described below.
A component-side vertical-socket fit holds out pin 4 at 0.43 px; a reflected
solder fit lands on both 8-pad columns and holds out pin 4 at 1.86 px. Their
corrected coordinates now establish pad identity. An independent D4 solder-row
fit holds out pin 5 at 2.14 px and identifies five pitch-matched continuous
routes: D2.1/.3/.5/.6/.7 to D4.1/.3/.5/.6/.7. All ten D2 observations are now
accepted as `A10/A14/A12/A15/A9`. The authoritative PCB generator and source PCB
now also use the photo-proven vertical D2 posture with pin 1 above pin 8; the
saved routed manufacturing snapshot deliberately retains the old posture until
the remaining D2 inputs are identified and that cluster can be rerouted once.
The solder-side extended crop shows all five inputs remaining distinct and
reaching those D4 input-row landings. D30.8 and
D30.11 are likewise measurement-only because
the component view is hidden by factory wires and the solder projections land
on a broad rail rather than identifiable package pads. D36.2 is hidden by
factory wiring/adhesive, while D39.2/D39.9/D39.10 have displaced or non-unique
solder landings; those four physical endpoints are also measurement-only.
D6.13/D6.14 project onto the package body and parallel solder rails, while the
six D7 endpoints have offset component landings and solder projections on the
bus-rail field; all eight physical endpoints therefore require local
registration or continuity measurements rather than photographic promotion.
The corrected D94 component posture now aligns with the horizontal socket. A
package-local similarity fit uses independently marked pins 1/8 and holds out
pin 4 at 0.01 px; a mirrored solder-side fit uses pins 1/8 and holds out pin 5
at 0.32 px. Both overlays land on all 16 physical socket pads, giving all 18
reviewed D94 observations defensible pad identity and corrected original-image
coordinates.
Continuous component-side copper plus the D93 local pin fit now accepts
D94.1->D93.4/`FDC_RE_N`, D94.2->D93.3/`FDC_CS_N`, and
D94.3->D93.2/`FDC_WE_N`. The source PCB
contains nine idempotently generated F.Cu segments for those three routes;
KiCad DRC adds no clearance, short, or unconnected-item class violation beyond
the deliberately unrouted source-board baseline. The routed snapshot remains
unchanged pending the rest of the local cluster.
D93.1 is now an explicit no-connect: the primary Western Digital handbook says
its internal back-bias node must be left open, which rules out a visually nearby
D94.6 trace as a junction. D94.4 is followed to an approximately
`(1789,2750)` component-photo layer handoff. An exact original-resolution crop
proves that terminal is distinct from D93.19's separate upper fanout via; the
projected solder region remains too crowded to select an onward branch. The
validated D93 component fit now also supplies exact pin-19 and pin-24 pad
coordinates without claiming either destination.
D28 is also locally misregistered: pins 1-6 project left of the photographed
vertical package while pins 8-13 project onto its body. Its 24 observations are
measurements until the package is fitted, regardless of four nearby-hole snaps.
`kicad/classify_photo_endpoint_group.py` now records these explicit whole-ref or
pin-subset decisions reproducibly without treating them as inferred copper.
D95 has locally visible component contacts/fanout, but pins 1-2 are resistor-
obscured, the opposite row is offset, and no unresolved path reaches a unique
destination. All solder projections land on intervening rails instead of the
package-pad rows, so its 28 observations are measurements as well.
D96 is likewise not locally reliable: several component projections fall on
the package body or adjacent resistor field, and solder projections sit between
the physical pad rows. Its 24 observations are retained as measurements.
D97-D99 add 84 measurement observations: D97 crosses resistor/body/parallel-
trace areas without a coherent package row. D98 now has a 0.20 px held-out
component fit on its marked horizontal К155ЛП11 package and corrected source
placement, but its solder paths remain unregistered. D99 is wire-obscured or
offset. Their solder points
likewise fall between package rows or on broad rails, so ten hole snaps remain
geometry-only cautions rather than electrical evidence.
D101/D102/D106 contribute the final 84 large-group measurements. D101 projects
onto wire bundles and bare trace fields, D102 alternates between adjacent
packages and fanout, and D106 lands on body/neighboring trace regions; all
three solder sets fall between physical package rows or on ambiguous rails.
D41's nine physical memory-timing boundaries are also measurement-only: the
component projections lie on long parallel traces or under factory wires, and
the solder projections sit between physical rows. This completes review-state
disposition of every P0 photo observation, but does **not** close any P0 net:
the evidence remains measurement/continuity work rather than accepted copper.
The compact P1 passive/connector batch C12/C73/E1/E14/R66/R73/S4/Z1 adds 22
measurements: its projections fall on adjacent packages, silkscreen, broad
rails, or multi-junction fields rather than uniquely identifiable landings.
D10/D12/D14/D33 add 12 compact-logic measurements because their component
points lie under a wire, on package bodies, or on an adjacent resistor, while
the corresponding solder holes/rails lack a valid package-side identity.
D37/D42/D51/D59 add 18 measurements: projections fall beside packages, under
wires, on a shield, or in mounting-hole/rail/junction fields; two nearby-hole
snaps lack a matching component-side pin identity.
D13/D34/D40 add 50 measurements: their projections alternate across package
bodies, resistors, mounting-hole fields, offset contacts, and wire-covered
fanout; six hole snaps have no matching package-side identity.
D26/D29/D38 add 24 measurements from body/boundary/parallel-trace projections;
D43/D52/D56 add the final 30 from package-body, resistor, sparse-joint, and
inter-row-rail fields. Every seeded photo observation now has an explicit
review disposition. This closes the automated crop-review queue only: zero
electrical paths were accepted, so local package fits or owner continuity
measurements remain necessary before changing connectivity.
Copper-path
extraction and review remain to be performed; 98
priority/side/refdes crop atlases now make that queue directly reviewable while
preserving original-image coordinates. The grouped placement-residual audit
finds no additional three-pin coherent translation safe to promote
automatically. See
`docs/photo-registration.md`.

When physical tracing resumes, process the batch in this order:

1. Register both grids to a shared board coordinate system, mirror the
   solder-side X axis, and attach refdes/pin overlays using the assembly drawing
   and unambiguous socket/component landmarks. Record every accepted read with
   filename and crop coordinates.
2. Register the temporarily uncovered VG93 footprint against the populated and
   solder-side views, then trace the highest-risk FDC handoff first: D93 pins
   19/24/37/38/39 and D100 pins 9/11, including DRQ/INTRQ ordering, reset,
   clock, density, output enable, and direction.
3. Grind every functional pin of D28, D95-D99, D101, D102, and D106. Require a
   matching component-side landing and solder-side copper path; queue continuity
   measurements wherever glare, a socket, a via transition, or a crossing makes
   the photographic read non-unique.
4. Trace D94 pin 15 and pins 1-7/9, but keep PROM contents independently blocked
   on a `.092` dump or programming artifact. Then trace the remaining D2,
   D30-section-B, and D105 WAIT-handoff endpoints.
5. Use the remaining grid coverage for D41/memory-timing boundaries, factory
   wire endpoints, connector geometry, and passive/refdes mapping. Do not infer
   absent C35-C72 values from aggregate part counts.
6. Review the extracted endpoint table before changing `juku.board.json`.
   Only reviewed, unambiguous paths may enter the model; regenerate/reroute and
   run the release audits after the evidence pass is complete, not tile by tile.

Exit criterion: regenerated source and routed PCBs contain every required
functional endpoint; the design-release audit reports no P0 blocker; LVS,
DRC, boot, and cosim checks remain green.

### P0: programmable parts

- Acquire repeated dumps or the Baltijets programming-disk files for D2 `.037`
  and D94 `.092`.
- Keep the reconstructed D6/D8 images clearly labeled as Tier-1/2 fallbacks.
  Do not relabel the `.113/.117` owner scans as D8 `.039` or D94 `.092`.
- Record the final D15/D16 EPROM split and programmer verification before
  assembly.

Exit criterion: every populated programmable part has a burnable file,
checksum, device/pinout decision, and provenance record. If a functional
replacement circuit is used instead of an unavailable PROM, document and test
that redesign explicitly.

### P1: fabrication review

After the netlist changes stop:

1. Regenerate the schematic, source PCB, route, Gerbers, drill, renders, BOM,
   and checksum files.
2. Re-run the independent Gerber render and inspect copper, mask, drill,
   silkscreen, connector orientation, mounting holes, and board outline.
3. Resolve rather than blanket-waive any DRC class whose geometry changed.
4. Run `kicad/check_replica_manufacturing_ready.sh`. It must report a released
   design, not merely a coherent package.
5. Upload only the newly generated ZIP and save vendor preview/settings/order
   evidence using `docs/replica-order-evidence-template.md`.

## Parallel work that does not block PCB tracing

### Tooling preparation

`docs/tooling-roadmap.md` records the evaluated open-source additions. No new
tool is yet a project dependency, and this documentation phase does not start
photo tracing, net promotion, powered capture, formal proof, or analog
simulation.

The intended adoption order is:

1. Continue the implemented repo-native VG93/photo registration workflow; pilot
   PCB ReTrace only if it materially improves landmark or endpoint review.
2. Add main-board KiCad ERC and schematic/PCB parity gates after the first
   reviewed photo-derived endpoints enter the model.
3. Add a Juku/8080 sigrok decoder when powered-board captures begin.
4. Use `minipro` only for explicitly supported EPROMs; keep the documented MCU
   sweep for unsupported bipolar PROMs.
5. Defer targeted SymbiYosys and ngspice/Qucs-S work until the corresponding
   digital and analog connectivity is evidence-complete.

### Parts and assembly preparation

- Use `docs/replica-dual-config-bom.csv` as a planning BOM, not a ready shopping
  cart. Mechanical/circuit-review and programming rows remain blocked.
- Treat WD1793 and 4164-family parts as candidates whose pinout, timing,
  voltage, footprint, and actual seller stock must be verified at order time.
- Source sockets and test long-lead ICs early only where the exact device choice
  cannot force a board change.
- Assemble sockets-first; verify rails with no ICs installed.

### Digital-twin fidelity

The twin is already sufficient as a boot/FDC/BASIC oracle. Further work should
serve physical bring-up or historical fidelity:

1. Replace the sim-only framebuffer read port with the traced shared-DRAM
   video arbitration once D41/D94/timing evidence exists.
2. Preserve the passing reset-to-EKDOS and disk-BASIC guards while physical FDC
   wiring is corrected.
3. Resolve Monitor 3.3 cartridge BASIC only when a complete cartridge artifact
   or documented loading procedure appears; do not keep inventing tail pages.
4. Extend sound/serial behavior only to support concrete bench measurements.

### External evidence/community

- Send the concise request in `docs/community-prom-media-request.md` for D2,
  D94, programming-disk, and cartridge BASIC evidence.
- Use `docs/owner-measurement-shortlist.md` for the next hardware session.
- Recheck external sources only when a current blocker names the expected
  artifact. Broad archive and market sweeps are not recurring work.

## External-source status

The 2026-07-10 recheck found no unadopted source that closes a current blocker:

- The [Baltijets factory-document directory](https://elektroonikamuuseum.ee/failid/juku/tech_docs_from_baltijets/)
  still contains the 16 files already mirrored under `ref/baltijets-tech-docs/`.
  Doc 007 references programming data on disk but does not contain the missing
  D2/D94 bytes.
- The vendored [MAME Juku driver](https://github.com/mamedev/mame/blob/master/src/mame/ussr/juku.cpp)
  is byte-identical to current master. MAME marks the machine working, and
  [PR #14817](https://github.com/mamedev/mame/pull/14817) records the
  real-hardware-tested 241st line and JBASIC correction already reflected here.
- `infoaed/juku3000`, Arti, and the museum software sources already represented
  in `roms/`, `media/`, and `ref/` add no public D2/D94 programming payload.

Claims about being the only recreation or about live NOS availability were
removed: neither is a stable, exhaustively provable planning fact.

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

## Decisions that remain fixed

- Historical evidence outranks emulator inference; `board.json` records the
  current interpretation and provenance.
- The replica remains a 2-layer, 310 x 266 mm board unless new physical
  measurement contradicts it.
- Functional substitutions are allowed for Tier 1/2 but must be electrically
  verified; Tier 3 requires historically appropriate parts and dumped PROMs.
- No fabrication-release claim may be based only on DRC, package checksums, or
  LVS of the modeled subset.
