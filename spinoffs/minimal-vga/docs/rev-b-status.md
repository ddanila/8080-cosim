# VJUGA rev B — status at a glance

Single-page state of the rev B (modular RC2014-bus) effort. Detail lives in
`rev-b-modular-design.md` (concept), `rev-b-build-plan.md` (decisions + phases),
`rev-b-execution-guide.md` (tasks + executor rules), `rev-b-bus-contract.md`
(interface), and `rev-b-five-board-order-plan.md` (controlling pre-order plan).
Last updated 2026-08-29.

**Owner direction (2026-08-27, expanded 2026-08-28): finish a VGA-ready five-board
machine with TTL serial, real D57-compatible PIT behavior and layered POST
observability before ordering.** This supersedes the four-board-first T1.10/T1.11
sequence and the pre-D57 five-board packages. Existing packages are historical
evidence, not upload candidates; the active work and release gates are R5.0–R5.R1,
including new R5.I1--R5.I7, in `rev-b-five-board-order-plan.md`.

## Phase ledger

| Phase | Scope | Status | Verified by |
|---|---|---|---|
| **B0** | facts file, commons guard, bus contract, modular HDL twin | ✅ done | `revb_boot_check.sh` byte-identical to cosim, both decode modes |
| **B1 — sim/firmware** | bring-up ROM, minimum-tier twin | ✅ done | `revb_bringup_check.sh`: TX stream == cosim via real 8251 |
| **B1-CAD Stage A** | four card netlists to schematic depth (TD.0–TD.5) | ✅ done | `check_revb_boards.py --completeness` green, in tier suite + CI |
| **B1-CAD Stage B** | mem-card pipeline: LVS → PCB → DRC → STEP (TD.6–TD.8, TE.1–TE.4) | ✅ done | LVS IN SYNC; placement-clean; **fully routed, DRC 0/0** (freerouting headless); STEP bbox 100×60; `check_revb_mem.sh` one-command green |
| **B1-CAD Stage C** | replicate pipeline: io → cpu → backplane (TD.9–TD.11, TF.1–TF.4) | ✅ pre-D57 baseline done | **all four baseline boards route DRC 0/0**; the I/O result is now historical input to R5.I5, while CPU/backplane remain current |
| **B1-CAD Stage D** | mating contract + FreeCAD proof + fab package (TG.1–TG.4) | ✅ done | TG.1 mating contract+checker, TG.2 **all 4 route 0/0** at 4 mm offset, TG.3 FreeCAD clearance 4.16 mm + keying D1.32b, TG.4 fab packages + power re-check → historical T1.10 evidence |
| **Five-board order** | CPU + memory + expanded I/O + backplane + ready VGA card; hardened TTL serial | ⬜ **ORDER HOLD**; D57/POST R5.I1--I7 and refreshed R5.J2/J3 candidate complete | `rev-b-five-board-order-plan.md` |
| **B2 video desk model** | TTL VGA + framebuffer through TI.3 | ✅ done | licensed timing adoption, chip-level twin, crop policy, row-base address generator, cycle-steal `/WAIT`, integrated ekta37 boot, `video.board.json`, completeness, and scoped LVS all guarded |
| **B2 physical card** | exact parts, GALs, full LVS, power, 4-layer PCB/package | ✅ R5.V1–V6 and J1 retained; prior J2/J3 historical | Video routed source passes DRC 0/0, plane/critical-route guards and JLC profile; five-card package/power/mechanical evidence must be refreshed after the I/O change |
| **B3 / B4** | full C10-capable I/O / FDC tier | ⬜ B3 redesign planned; B4 future | B3 now populates 8255/8259 and adds real D57 PIT plus layered POST under R5.I1--I7; no B4 tape-out work yet |

## One-command gate

`spinoffs/minimal-vga/sim/revb_tier_suite.sh` runs the retained baseline plus the
R5.I1--I7 PIT, POST, three-ROM, routed-source and negative-control gates below:
commons guard, board connectivity + **D1.18 completeness** (all six card specs),
serial contract/electrical/C10 gates, five reproducible GALs, five-card mating,
exact Video parts/footprints/power, routed stack/plane/critical-path negative controls,
assembled R5.V6 mechanics/protected-power solve, JLCPCB R5.J1 profile/negative controls,
hash-bound R5.R1 technical-pass/owner-hold enforcement,
mem/io/video scoped LVS,
per-card BFM TBs +
negative control, bus-conflict + refresh-drive assertions, ekta37 banner boot (both
modes) byte-identical to cosim, the minimum-tier bring-up TX stream, and the B2 video
timing/crop/scanout/`WAIT` gates.

## Key decisions (see build plan for the full register)

- Z80, SRAM (no DRAM), framebuffer on the Video card, RC2014-compatible bus.
- Bus: 39-pin base + 10-pin extension (D1.4 second-row keying); UART 0x08–0x0B.
- **D1.17** '245 /OE must gate on an active bus cycle (refresh+glitch safe).
- **D1.16** I/O selects + 8251 active-HIGH reset via an ATF16V8 on the I/O card.
- **R5.I1** supersedes the final D1.16 device choice: expand I/O decode for a
  D57-compatible PIT at `18h`--`1Bh` and independent POST latch, preferably with
  an ATF22V10; retain PIT-normal and direct-recovery UART clock modes.
- **R5.I3** freezes three VJUGA ROM roles: Z80-adapted EKTA3.7, Z80-adapted C10
  with no PIT bypass, and an enhanced no-stack-early diagnostic ROM.
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

The pre-D57 sources remain useful green regression evidence, but their routed I/O
card, renders, packages, hashes, power total and release record are superseded.
R5.I1 freezes the timer, decode, sound and POST electrical contract; R5.I2's
real PIT/8251/POST twin plus fault controls pass; R5.I3 produces the hash-bound
three-ROM set; and R5.I4/I5 close the expanded GAL/netlist/LVS and the routed,
mechanically cleared 100x100 mm two-layer I/O card. R5.I6 now proves integrated
EKTA3.7, NETC10 and DIAG behavior against the PIT-normal/direct-recovery hardware,
including the chip-level TTL-video path and layer-specific fault controls. The
R5.I7 closes exact parts, the 1.655 A budget, MF-R300 protection, routed voltage
drop, STEP clearance, all-five DRC/JLC checks, the 16-stage bench runbook and stale
source-hash rejection. R5.J2 has regenerated the five exact source-bound fabrication
archives and R5.J3 has independently rendered and reviewed them, reconciled the
158-part first-system BOM and captured the current no-upload quote. The next action
is the held **R5.R1 owner review**; it is not permission to upload or order.

**R5.0, R5.S1–S3, R5.P1, R5.V1–V6, R5.J1–J3 and R5.I1–I7 are complete.** Follow the
dependency-ordered tasks in `rev-b-five-board-order-plan.md`.
Do not upload the historical four-board packages. Ordering stays on hold until all
five packages pass R5.R1 and the owner explicitly releases them. The held R5.O1
upload/DFM/order record and R5.B1 five-card bench log are prepared; they are runbooks,
not evidence that either physical stage has begun.

Rule: `git pull --rebase` before every push — the remote moves mid-session.
