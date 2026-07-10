# PLAN — working physical Juku recreation

Status date: **2026-07-10**.

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
| Connectivity | `sync/check.sh` reports 97 mapped instances and 227 matched nets | Unmapped footprints, pins absent from `board.json`, and the correctness of behavioral models |
| PCB package | 240-footprint routed artifact; no KiCad clearance/short/unconnected-item errors; reproducible 2-layer 310 x 266 mm Gerber/drill package | Electrical completeness or historical correctness of omitted/assumed nets |
| Sources/media | Factory schematic set, 16 Baltijets PDFs, ROMs, EKDOS source, raw disks, system binaries, photographs, and owner RE3 scans are local and checksum-guarded | Baltijets programming-disk payloads, D2/D94 dumps, and the missing cartridge BASIC page/procedure |

The current main-board ZIP is
`fab/gerbers/upload/juku-replica-gerbers-drill.zip`, SHA256
`261db032c3301d5604feca84ee3cd581aaa5dc924d8a183a921c4b0d180de0a1`.
It is retained as a reproducible engineering snapshot. **Do not send it to a
fabricator until the release blockers below are closed and the package is
regenerated.**

## Release blockers — close before main-board fabrication

### P0: physical connectivity

1. **D2 `.037` bus/wait PROM and D105 wait logic** — D2's signal pins are
   unnetted, while the official D105 К155ЛА3 footprint is placement-only.
   Trace the D2 input rails and D0 destination, including D105.10's source and
   D105.6's destination, then update the model and reroute.
2. **All placement-only official ICs** — D28, D95-D99, D101, D102, D105,
   and D106 exist in the source PCB, routed PCB, and DSN but have no pin model.
   Trace and route each required function, or document a deliberate redesign/
   DNP decision and remove it from the released artifacts. D30 READY section A
   is now modeled through R5/R6/R29. In section B, pins 10 and 12 are visibly
   tied and pins 6 and 9 are documented no-connects; pins 8, 11, and 13 still
   require end-to-end tracing, as does the shared pin-10/pin-12 source;
   most of the placement-only parts are FDC support logic. Closing D105 alone
   cannot release the board.
3. **D94 `.092` PROM** — only BA11..BA15 and power are currently connected.
   Resolve pin 15 and D0..D7 destinations, update the model, and reroute.
4. **Release-risk net review** — disposition the remaining source-risk rows in
   `docs/board-fidelity-gap-ledger.md` and
   `docs/owner-measurement-shortlist.md`. Assumptions that affect boot, memory,
   bus direction, interrupts, or video timing must be measured or explicitly
   redesigned; they cannot be deferred as generic “bring-up” items.

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
