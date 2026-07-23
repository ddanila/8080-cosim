# VJUGA rev B — status at a glance

Single-page state of the rev B (modular RC2014-bus) effort. Detail lives in
`rev-b-modular-design.md` (concept), `rev-b-build-plan.md` (decisions + phases),
`rev-b-execution-guide.md` (tasks + executor rules), `rev-b-bus-contract.md`
(interface). Last updated 2026-07-23.

## Phase ledger

| Phase | Scope | Status | Verified by |
|---|---|---|---|
| **B0** | facts file, commons guard, bus contract, modular HDL twin | ✅ done | `revb_boot_check.sh` byte-identical to cosim, both decode modes |
| **B1 — sim/firmware** | bring-up ROM, minimum-tier twin | ✅ done | `revb_bringup_check.sh`: TX stream == cosim via real 8251 |
| **B1-CAD Stage A** | four card netlists to schematic depth (TD.0–TD.5) | ✅ done | `check_revb_boards.py --completeness` green, in tier suite + CI |
| **B1-CAD Stage B** | mem-card pipeline: LVS → PCB → DRC → STEP (TD.6–TD.8, TE.1–TE.4) | ✅ done | LVS IN SYNC; placement-clean; **fully routed, DRC 0/0** (freerouting headless); STEP bbox 100×60; `check_revb_mem.sh` one-command green |
| **B1-CAD Stage C** | replicate pipeline: io → cpu → backplane (TD.9–TD.11, TF.1–TF.4) | ✅ done | **all four cards route DRC 0/0** — cpu A8 closed by the TF.1 sweep (U1 x=41); backplane via D1.29 column-route (245 generated columns + freerouted tail) |
| **B1-CAD Stage D** | mating contract + FreeCAD proof + fab package (TG.1–TG.4) | ✅ done | TG.1 mating contract+checker, TG.2 **all 4 route 0/0** at 4 mm offset, TG.3 FreeCAD clearance 4.16 mm + keying D1.32b, TG.4 fab packages + power re-check → **T1.10 armed** |
| **B1 order / bench** | T1.10 order, T1.11 bench bring-up | ⬜ T1.10 = purchasing decision; T1.11 hardware-blocked | see `rev-b-order-readiness.md` |
| **B2 / B3 / B4** | video / keyboard+PIC / FDC tiers | ⬜ B2 planned to task depth (TI.1–TI.8, D2.1–D2.5, 2026-07-18); B3 = populate-only; B4 future | TTL640x480 (MIT) adopted for the timing chain; TI.1–TI.4 desk-ready, TI.5+ tape-out held until T1.11 proves the bus |

## One-command gate

`spinoffs/minimal-vga/sim/revb_tier_suite.sh` runs the whole verified set:
commons guard, board connectivity + **D1.18 completeness** (all 4 cards), per-card
BFM TBs + negative control, bus-conflict + refresh-drive assertions, ekta37 banner
boot (both modes) byte-identical to cosim, and the minimum-tier bring-up TX stream.
All green as of the last commit.

## Key decisions (see build plan for the full register)

- Z80, SRAM (no DRAM), framebuffer on the Video card, RC2014-compatible bus.
- Bus: 39-pin base + 10-pin extension (D1.4 second-row keying); UART 0x08–0x0B.
- **D1.17** '245 /OE must gate on an active bus cycle (refresh+glitch safe).
- **D1.16** I/O selects + 8251 active-HIGH reset via an ATF16V8 on the I/O card.
- **D1.21** CPU card unbuffered in B1 (RC2014 precedent); '245/'244 optional margin.
- **D1.19** oracle-first: control equations pass the boot oracle before silicon.
- **D1.20** pipeline-prove on the mem card, then replicate.

## Tools

kicad-cli 10.0.4 + FreeCAD 1.1.1 installed; resolved by
`kicad/revb/env.sh` (skip-not-fail). Stage A needs none of them; Stage B onward does.

## Next action

Stages C/D and the pre-order correction pass are complete. All four boards are
recorded order-safe, including corrected package widths, through-hole USB-C,
power LED polarity, reset pull-up, input conditioning, mating, and physical
footprint contracts.

**T1.10 is an explicit owner purchasing decision.** If approved, order one
first-article B1 set and perform T1.11 bench bring-up. Record exact parts,
programmed images, jumper/orientation state, power, serial/RAM result, bus
timing, and the convention-only keying/16 mm slot-clearance observations.
Do not authorize duplicate boards or B2 video-card tape-out until the B1 bench
record passes and every discrepancy is dispositioned.

Rule: `git pull --rebase` before every push — the remote moves mid-session.
