# VJUGA rev B — five-board first-article order plan

Status: **ACTIVE PLAN / ORDER HOLD**. Owner direction recorded 2026-08-27.

This is the controlling plan for the first VJUGA rev B order. The intended
machine is one complete five-card system: CPU, memory, I/O, backplane, and a
working VGA card. It must also expose the existing 8251 as a practical
bidirectional TTL serial console, and every fabrication package must be checked
against JLCPCB's current requirements before upload.

This direction supersedes the old sequence that would have ordered the four B1
boards before laying out the Video card. The four-board packages and hashes in
`rev-b-order-readiness.md` remain historical evidence only: **do not upload or
order them**. No PCB design work or purchase is authorized merely by recording
this plan.

## Fixed scope and first-article decisions

- Deliver five independent bare-PCB designs, not a panel: CPU, memory, I/O and
  backplane on two layers; Video on four layers.
- Finish and release all five together. The owner accepts that the physical bus
  is not yet bench-proven; stronger desk checks below compensate for that risk,
  and the boards will be assembled and powered in stages after arrival.
- The existing 8251 on the I/O card is the serial device. The backplane header
  and crossover/isolation path expose it; there is no second serial card or UART.
- Serial target is 19,200 baud, 8N1, with a selectable 9,600-baud fallback. It
  must be usable by the same ordinary USB-UART host workflow used for Juku.
- The first-article CPU clock is a socketed **2.000 MHz** oscillator. At that
  clock, divide the 59.94 Hz VGA frame boundary by six for the approximately
  10 Hz `FRAME_TICK` cadence corresponding to 200,000 CPU cycles.
- The VGA card uses a local 25.175 MHz oscillator and the already-verified
  640x480 timing/40x241 framebuffer model. Plan for a 100x100 mm four-layer
  signal/GND/VCC/signal board unless the footprint audit proves that outline
  impossible.
- Hand assembly remains the target. No JLCPCB PCBA, no panelization and no FDC
  card are in this order.

## Intended order matrix

| Design | Nominal size | Layers | First system uses | Release note |
|---|---:|---:|---:|---|
| CPU | 100x70 mm | 2 | 1 | 2.000 MHz oscillator fixed for first article |
| Memory | 100x60 mm | 2 | 1 | ROM/SRAM decode GAL must have reproducible JEDEC |
| I/O | 100x100 mm | 2 | 1 | Existing 8251 plus decode GAL; B3 parts remain DNP |
| Backplane | 100x100 mm | 2 | 1 | Five slots, protected power, USB-TTL console boundary |
| Video | target 100x100 mm | 4 | 1 | VGA-ready card, local framebuffer, three programmed GALs |

Expect the vendor's normal minimum quantity (commonly five copies per design),
but use the live quote as the authority. Surplus bare boards are not permission
to populate duplicates before the first system passes bring-up.

## Dependency-ordered work plan

Each row is one reviewable, commit-sized task. A task starts only when all named
dependencies are green. Its acceptance evidence must be committed alongside
the change; a prose assertion is not a pass.

| ID | Work | Depends on | Acceptance evidence |
|---|---|---|---|
| **R5.0 — DONE 2026-08-27** | Freeze this five-board contract in the status/build/execution docs and mark the four-board ZIPs historical. | — | Docs agree on five boards, the order hold, serial ownership, 2 MHz clock and 4-layer Video card. |
| **R5.S1 — DONE 2026-08-27** | Audit the complete 8251-to-backplane serial net path. Correct stale `JP_S5` wording so it describes console isolation/crossover, not a nonexistent Serial card. Freeze a board-relative header pinout (`5V`, board TX, board RX, GND) and conspicuous `TTL ONLY — NOT RS-232` silk. | R5.0 | `check_revb_serial_contract.py` proves 8251 pin direction through bus pins 35/36 and `JP_S5` to `J_TTL`; generated placement passes content and placement DRC. |
| **R5.S2 — DONE 2026-08-27** | Fix the UART clock and electrical boundary: 307.2 kHz for 19,200x16, selectable 153.6 kHz for 9,600x16; 5 V logic must safely interoperate with ordinary 3.3/5 V USB-TTL adapters. Use a roughly 3.3 V board-TX high level, a 5 V HCT-compatible receive buffer, series resistors, isolation/loopback jumpers, and no default USB-adapter back-power path. | R5.S1 | `serial-electrical.json` plus `check_revb_serial_electrical.py` prove exact divider clocks, thresholds, 2.379–3.536 V board TX, defined unused inputs and the blocking-diode sense path; I/O and backplane placement DRC pass. |
| **R5.S3 — DONE 2026-08-27** | Extend simulation/host tests through the real 8251 and external connector boundary, including reset, both baud selections, TX and RX, loopback and no-contention cases. Add one VJUGA-adapted C10 host request/reply transaction after the low-level gate passes. | R5.S2 | `revb_serial_console_check.sh` proves 19,200 8N1 primary, 9,600 fallback, bidirectional bytes, external loopback, isolation negative control and one exact ABI 1.4 C10 request/reply without changing root behavior. |
| **R5.P1** | Make programmable logic on the existing boards buildable: Memory ATF22V10 and I/O ATF16V8 equations, device declarations, compiler command, pinned tool/version, JEDEC outputs and fuse/checksum record. | R5.0 | Clean rebuild reproduces both JEDECs; equations pass oracle and pin-map checks; programming/readback procedure is documented. |
| **R5.V1** | Audit the video digital model against real silicon and convert scoped LVS into a full-card pin-level connectivity plan. Confirm logic families, fan-out, polarity, tied/unused inputs, reset states, bus ownership, SRAM timing and `WAIT_N`. | R5.0 | Component-by-component audit closes every pin; mutation controls prove full-card LVS/checkers detect a swapped or missing connection. |
| **R5.V2** | Close video power and analogue-output details. Provide one 100 nF capacitor at every IC plus local bulk capacitance; model total five-card current; retain monitor-side 75 ohm loading and verify that the 470 ohm RGB series network produces the intended level. | R5.V1 | BOM/board/checker counts decouplers per IC; calculated current and voltage margins are recorded; docs no longer call the on-card 470 ohm parts 75 ohm terminations. |
| **R5.V3** | Produce sources and reproducible JEDECs for all three Video GALs. Fix `FRAME_TICK` to divide by six for the 2.000 MHz first article and retain a documented way to retarget it if the CPU oscillator changes. | R5.V1 | Three clean JEDEC rebuilds, pin/fuse checks, timing simulation and integrated EKTA boot all pass. |
| **R5.V4** | Pin exact orderable mechanical parts before layout: right-angle female DE-15 VGA connector, 25.175 MHz 5 V oscillator, SRAM, GAL packages, bus headers, sockets and tall/polarized parts. | R5.V1 | Manufacturer part numbers, datasheets, land patterns, drill/lead tolerances, courtyard and connector mating face are machine-checked. |
| **R5.V5** | Generate, place and route the Video PCB on four layers (`signal / solid GND / solid VCC5 / signal`). Keep the dot-clock chain and pixel path short, add source damping where the audit calls for it, and preserve a continuous return plane. | R5.V2, R5.V3, R5.V4 | Fresh generation passes full connectivity/LVS, total DRC 0/0, plane/return-path and mechanical checks; routed source is reproducible. |
| **R5.V6** | Re-run the assembled five-card mechanical and power model: connector mating, 16 mm slot pitch, adjacent-card/tall-part clearance, VGA-cable access, orientation/keying, current path and supply drop. Qualify one regulated 5 V supply rated at least 2 A and protect every intended bench input. | R5.S2, R5.V5 | Machine check plus 3-D/manual review pass; no unfused normal input remains; current/headroom and connector ratings are recorded. |
| **R5.J1** | Encode a JLCPCB rule profile and preflight checks for both the four 2-layer boards and the 4-layer Video board. | R5.V5 | Checks cover stack-up/layers, outline, drills/slots, annular rings, clearances, silk, masks, filenames and archive contents; negative fixtures fail. |
| **R5.J2** | Regenerate all five fabrication ZIPs in one release run. Emit a manifest with source revision, tool versions, board dimensions/layers, file list and SHA-256 per archive. | R5.P1, R5.S3, R5.V6, R5.J1 | One command regenerates and validates five safe archives; packages contain Gerber/Excellon production data only. |
| **R5.J3** | Perform an independent pre-upload review and obtain a fresh live JLCPCB quote. Check every Gerber/drill rendering separately; reconcile the five designs with BOM quantities and programmed-device count. | R5.J2 | Signed checklist has no unresolved findings; price, quantity, lead time, selected options and any vendor warnings are recorded. |
| **R5.R1** | Hold the final release review. | R5.J3 | All gates below are green, exact package hashes are recorded, and the owner explicitly changes `ORDER HOLD` to `RELEASED FOR UPLOAD`. |
| **R5.O1** | Upload the five independent designs, inspect JLCPCB's generated production files, resolve rather than silently accept DFM edits, and place the order. | R5.R1 | Order ID, accepted production-file screenshots/results, options, quantities and uploaded hashes are in a new five-board order record. |
| **R5.B1** | After delivery, inspect and assemble in stages: bare backplane, CPU clock/reset, NOP free-run, Memory, I/O+serial, then Video. | R5.O1 | Each stage records current, rails, logic evidence and failures before the next card is inserted; final gate is EKTA boot with VGA plus bidirectional C10 serial. |

The previous `TI.5 held until T1.11` dependency is therefore replaced by the
R5 chain above. The physical risk is not erased; it moves into R5.V6/R5.J3 and
the deliberately staged R5.B1 bring-up.

## JLCPCB fabrication profile and checks

Capability snapshot: 2026-08-27. Recheck the vendor pages and live quote at
R5.J3 because manufacturing options can change.

- Common: FR-4, 1.6 mm, 1 oz finished copper, green solder mask, white silk,
  lead-free HASL, tented vias; enable production-file confirmation.
- Two-layer cards: plan ordinary routing at 0.20/0.20 mm or larger even though
  JLCPCB currently lists a 0.10/0.10 mm ordinary 1 oz minimum.
- Video: use a listed standard four-layer stack-up without controlled impedance;
  do not invent dielectric dimensions. Inner GND and VCC layers must appear as
  copper layers in both archive and preview.
- Through holes: design the finished hole at least 0.10 mm over the maximum lead
  dimension and account for the listed +0.13/-0.08 mm PTH tolerance. Prefer at
  least 0.25 mm annular ring on two-layer boards and 0.20 mm on four-layer.
- Prefer vias of at least 0.20 mm finished hole; the existing 0.40/0.80 mm vias
  are comfortably conservative. Any plated slot must be at least 0.50 mm wide
  and at least twice as long as it is wide.
- Keep silk strokes and spacing at least 0.15 mm and text height at least 1.0 mm.
  No silk may cover pads or disappear under sockets where it is needed for safe
  insertion.
- Each ZIP has exactly one closed board outline, correctly named copper/mask/
  silk layers and Excellon drills. Do not upload fab, courtyard, user drawing,
  paste, adhesive, assembly or STEP files.

Vendor references:

- [PCB capabilities](https://jlcpcb.com/capabilities/Capabilities)
- [Gerber preparation](https://jlcpcb.com/help/article/gerber-files-preparation)
- [PCB dimensions](https://jlcpcb.com/help/article/pcb-dimensions)
- [Impedance and standard stack-ups](https://jlcpcb.com/impedance)
- [Ordering instructions](https://jlcpcb.com/help/article/instructions-for-ordering)
- [Production-file confirmation](https://jlcpcb.com/help/article/how-to-confirm-the-production-file)
- [Surface finishes](https://jlcpcb.com/help/article/jlcpcb-surface-finish)
- [Hole tolerances](https://jlcpcb.com/help/article/difference-and-tolerance-explanation-between-via-and-pad-holes)

## Final release gate

R5.R1 cannot pass until all of the following are true:

- **PENDING:** All five board sources regenerate from a clean checkout.
- **PENDING:** All five pass full net/pin checks, total DRC 0/0 and mechanical mating.
- **PENDING:** The five-card simulation boots EKTA byte-identically and passes VGA timing,
      framebuffer, `WAIT_N`, reset, `FRAME_TICK` and serial request/reply gates.
- **PENDING:** All five GALs (Memory, I/O and three Video) have reproducible, pin-checked
      JEDECs and a recorded programming/readback procedure.
- **PENDING:** Exact connectors, oscillators, sockets and other footprint-critical parts
      are orderable and tied to checked datasheets.
- **PENDING:** Decoupling, five-card current, regulated 5 V/2 A supply, input protection,
      voltage drop and USB-TTL electrical compatibility are closed.
- **PENDING:** Five JLCPCB-ready ZIPs and their hashes pass the encoded vendor profile.
- **PENDING:** An independent layer/drill/mechanical review and current live quote pass.
- **PENDING:** The owner explicitly authorizes upload after seeing the final evidence.

Until then, the correct next actions are the dependency-ready R5.P1 and R5.V1
tasks, not an order and not a partial four-board upload.
