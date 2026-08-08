# VJUGA rev B — status at a glance

Single-page state of the rev B (modular RC2014-bus) effort. Detail lives in
`rev-b-modular-design.md` (concept), `rev-b-build-plan.md` (decisions + phases),
`rev-b-execution-guide.md` (tasks + executor rules), `rev-b-bus-contract.md`
(interface). Last updated 2026-08-08.

## Phase ledger

| Phase | Scope | Status | Verified by |
|---|---|---|---|
| **B0** | facts file, commons guard, bus contract, modular HDL twin | ✅ done | `revb_boot_check.sh` byte-identical to cosim, both decode modes |
| **B1 — sim/firmware** | bring-up ROM, minimum-tier twin | ✅ done | `revb_bringup_check.sh`: TX stream == cosim via real 8251 |
| **B1-CAD Stage A** | four card netlists to schematic depth (TD.0–TD.5) | ✅ done | `check_revb_boards.py --completeness` green, in tier suite + CI |
| **B1-CAD Stage B** | mem-card pipeline: LVS → PCB → DRC → STEP (TD.6–TD.8, TE.1–TE.4) | ✅ done | LVS IN SYNC; placement-clean; **fully routed, DRC 0/0** (freerouting headless); STEP bbox 100×60; `check_revb_mem.sh` one-command green |
| **B1-CAD Stage C** | replicate pipeline: io → cpu → backplane (TD.9–TD.11, TF.1–TF.4) | ✅ done | **all four boards route DRC 0/0** — cpu A8 closed by the TF.1 sweep (U1 x=41); backplane uses the D1.34 clean-slate freerouting path |
| **B1-CAD Stage D** | mating contract + FreeCAD proof + fab package (TG.1–TG.4) | ✅ done | TG.1 mating contract+checker, TG.2 **all 4 route 0/0** at 4 mm offset, TG.3 FreeCAD clearance 4.16 mm + keying D1.32b, TG.4 fab packages + power re-check → **T1.10 armed** |
| **B1 order / bench** | T1.10 order, T1.11 bench bring-up | ⬜ T1.10 = purchasing decision; T1.11 hardware-blocked | see `rev-b-order-readiness.md` and `rev-b-b1-bench-log.md` |
| **B2 video desk model** | TTL VGA + framebuffer through TI.3 | ✅ done | licensed timing adoption, chip-level twin, crop policy, row-base address generator, cycle-steal `/WAIT`, integrated ekta37 boot, `video.board.json`, completeness, and scoped LVS all guarded |
| **B2 physical card** | TI.4 footprints, then TI.5–TI.8 PCB/package | ⬜ TI.4 next; TI.5+ held | exact DSUB/oscillator footprint contracts may proceed; placement/routing/tape-out remains held until T1.11 proves the B1 bus |
| **B3 / B4** | keyboard+PIC / FDC tiers | ⬜ B3 = populate-only; B4 future | B3 parts are already wired as DNP on the I/O card; no B4 tape-out work yet |

## One-command gate

`spinoffs/minimal-vga/sim/revb_tier_suite.sh` runs the whole verified set:
commons guard, board connectivity + **D1.18 completeness** (all six card specs),
B1 footprint guards + negative controls, mem/io/video scoped LVS, per-card BFM TBs +
negative control, bus-conflict + refresh-drive assertions, ekta37 banner boot (both
modes) byte-identical to cosim, the minimum-tier bring-up TX stream, and the B2 video
timing/crop/scanout/`WAIT` gates.

## Key decisions (see build plan for the full register)

- Z80, SRAM (no DRAM), framebuffer on the Video card, RC2014-compatible bus.
- Bus: 39-pin base + 10-pin extension (D1.4 second-row keying); UART 0x08–0x0B.
- **D1.17** '245 /OE must gate on an active bus cycle (refresh+glitch safe).
- **D1.16** I/O selects + 8251 active-HIGH reset via an ATF16V8 on the I/O card.
- **D1.21** CPU card unbuffered in B1 (RC2014 precedent); '245/'244 optional margin.
- **D1.19** oracle-first: control equations pass the boot oracle before silicon.
- **D1.20** pipeline-prove on the mem card, then replicate.
- **D1.37** five slots at 16 mm on a 100×100 backplane; complete planned system,
  no spare slot, service components retained top-side outside the card envelope.

## Tools

The 2026-08-08 pre-order run used KiCad/pcbnew 9.0.8, Yosys 0.52, FreeCAD 1.1.3,
and the repository-pinned custom freerouting build under Java 25. `kicad/revb/env.sh`
also retains its platform locators and skip-not-fail behavior for desks/CI without
those tools.

## Next action

Stages C/D and the pre-order correction pass are complete. All four boards are
recorded order-safe, including the five-slot 100×100 backplane, corrected package
widths, through-hole USB-C, power LED polarity, reset pull-up, input conditioning, mating, and physical
footprint contracts.

**T1.10 is an explicit owner purchasing decision.** The four fabrication packages
were freshly regenerated and machine-validated on 2026-08-08. If approved, upload
those exact ZIPs, inspect the vendor previews/DFM, record the accepted hashes and
stack-up, then order one first-article B1 set and perform T1.11 bench bring-up. Record exact parts,
programmed images, jumper/orientation state, power, serial/RAM result, bus
timing, and the convention-only keying/16 mm slot-clearance observations.
Do not authorize duplicate boards or B2 video-card tape-out until the B1 bench
record passes and every discrepancy is dispositioned.

Rule: `git pull --rebase` before every push — the remote moves mid-session.
