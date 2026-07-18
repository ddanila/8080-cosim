# VJUGA rev B — status at a glance

Single-page state of the rev B (modular RC2014-bus) effort. Detail lives in
`rev-b-modular-design.md` (concept), `rev-b-build-plan.md` (decisions + phases),
`rev-b-execution-guide.md` (tasks + executor rules), `rev-b-bus-contract.md`
(interface). Last updated 2026-07-17.

## Phase ledger

| Phase | Scope | Status | Verified by |
|---|---|---|---|
| **B0** | facts file, commons guard, bus contract, modular HDL twin | ✅ done | `revb_boot_check.sh` byte-identical to cosim, both decode modes |
| **B1 — sim/firmware** | bring-up ROM, minimum-tier twin | ✅ done | `revb_bringup_check.sh`: TX stream == cosim via real 8251 |
| **B1-CAD Stage A** | four card netlists to schematic depth (TD.0–TD.5) | ✅ done | `check_revb_boards.py --completeness` green, in tier suite + CI |
| **B1-CAD Stage B** | mem-card pipeline: LVS → PCB → DRC → STEP (TD.6–TD.8, TE.1–TE.4) | ✅ done | LVS IN SYNC; placement-clean; **fully routed, DRC 0/0** (freerouting headless); STEP bbox 100×60; `check_revb_mem.sh` one-command green |
| **B1-CAD Stage C** | replicate pipeline: io → cpu → backplane (TD.9–TD.11, TF.1–TF.4) | ✅ done | **all four cards route DRC 0/0** — cpu A8 closed by the TF.1 sweep (U1 x=41); backplane via D1.29 column-route (245 generated columns + freerouted tail) |
| **B1-CAD Stage D** | FreeCAD mating/keying + fab package (TD.12–TD.13) | ⬜ → arms T1.10 | next |
| **B1 order / bench** | T1.10 order, T1.11 bench bring-up | ⬜ hardware-blocked | |
| **B2 / B3 / B4** | video / keyboard+PIC / FDC tiers | ⬜ future | |

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

**Stage C is done (2026-07-18): all four cards route DRC 0/0.** TF.1 closed cpu A8 by
placement sweep (U1 x=41); TF.2 added multi-slot backplane placement; TF.3 routed the
backplane via D1.29 (245 generator-emitted bus columns + freerouted power tail); TF.4
verified the 4×0/0 exit gate.

**Stage D planned to task depth (2026-07-18): TG.1–TG.4** (execution guide). The
Stage-C exit review found the boards are route-perfect but **not mate-compatible**
(cards disagree 1 mm on connector edge offsets; the D1.30 two-bank backplane cannot
physically accept a card). So: **TG.1** mechanical mating contract `mating.json` +
`check_revb_mating.py` (must fail on today's geometry first — D1.31); **TG.2** align
generators to the contract, re-route all four (sweep tool ready if cpu regresses);
**TG.3** FreeCAD mating + reversed-card keying proof (D1.32 fallback if keying
doesn't self-enforce); **TG.4** power re-check + gerber fab packages → **arms T1.10**
(purchasing decision). Then T1.11 bench (hardware-blocked), B2/B3/B4 (plan at entry).
Rule: `git pull --rebase` before every push — the remote moves mid-session.
