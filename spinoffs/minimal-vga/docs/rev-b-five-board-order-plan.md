# VJUGA rev B — five-board first-article order plan

Status: **ACTIVE PLAN / ORDER HOLD**. Original owner direction recorded
2026-08-27; D57/POST expansion recorded 2026-08-28.

Silkscreen correction 2026-08-28: all five designs now use the pinned GOST Book
family and every physical footprint has a reference plus value/role assembly label.
The later D57/POST decision below changed the I/O netlist as well. R5.I1--R5.I7,
R5.J2 and R5.J3 have now qualified and independently reviewed the regenerated
five-archive candidate recorded below. R5.R1 remains deliberately held pending
explicit owner authorization. See `rev-b-silkscreen-audit.md`.

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
- The first article will contain a real D57-compatible 8253/82C54 at I/O ports
  `18h`--`1Bh`. Network-ROM PIT initialization, count latching, the 8251 clock and
  channel-1 sound must execute against that device; a VJUGA ROM must not fake or
  bypass those operations.
- POST observability is layered: power and `J_DIAG` activity require no working
  firmware; an independent eight-bit latched display preserves the last stage;
  D57 channel 1 supplies audible codes when available; and the existing TTL
  serial console supplies detailed text after the 8251 is alive.
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
| I/O | target 100x100 mm | target 2 | 1 | 8251, D57-compatible PIT, POST latch/display and expanded decode; 8255/8259 are populated in the C10-capable build |
| Backplane | 100x100 mm | 2 | 1 | Five slots, protected power, USB-TTL console boundary |
| Video | target 100x100 mm | 4 | 1 | VGA-ready card, local framebuffer, three programmed GALs |

Expect the vendor's normal minimum quantity (commonly five copies per design),
but use the live quote as the authority. Surplus bare boards are not permission
to populate duplicates before the first system passes bring-up.

## D57, POST and ROM expansion contract

Owner rationale: VJUGA is an experimental bridge to the faithful Juku clone. It
should test our understanding of real Juku hardware/firmware contracts, not make
those contracts disappear behind VJUGA-only ROM patches. The Z80 opcode/checksum
adaptation remains necessary and explicitly allowed. The D57 PIT dependency does
not: it moves into hardware in this revision.

### D57-compatible timer and serial clock

- Fit a socketed, 5 V, software-compatible 8253 or 82C54 and decode its four
  registers at `18h`--`1Bh`. The decode must require a real Z80 I/O cycle and
  exclude interrupt acknowledge. Replace the I/O ATF16V8 with an ATF22V10, or
  prove an equally simple decoded implementation; the preferred ATF22V10 route
  provides independent PIT-select and POST-write outputs with reproducible
  equations and a new programmed-device readback record.
- Drive channel 0 from the existing 4.9152 MHz baud oscillator divided by four
  at U7: 1.2288 MHz. C9/C10's programmed count of four must therefore produce
  307.2 kHz at `OUT0`, connected to both 8251 `RxC` and `TxC`, for exact
  19,200-baud x16 operation.
- Retain the existing direct `/16` and `/32` paths as 19,200/9,600 diagnostic
  fallbacks. A separate, clearly labelled clock-source jumper selects **PIT
  (normal)** or **DIRECT (recovery)**; normal C9/C10 acceptance uses PIT.
- Drive channel 1 from the socketed 2.000 MHz CPU clock. Route `OUT1` through a
  checked transistor/limiting network to a passive piezo or speaker header so
  the existing C9/C10 C1--C5 failure tones and sound ABI exercise real hardware.
- D57 channel 2 belongs to the original raster/sync chain replaced by VJUGA's
  autonomous VGA card. Give its clock/gate defined non-floating states and expose
  useful test points, but do not claim timing equivalence to the original
  D55-to-D57 `SYNC B` path. No required VJUGA boot or diagnostic may depend on
  `OUT2`.
- Add local 100 nF decoupling, socket/footprint checks, clock/output test points,
  exact-part sourcing and an updated five-card current budget.

### Layered POST observability

- Retain the power indication and CPU `J_DIAG` header (`CLK`, `M1_N`, `RFSH_N`,
  `RESET_N`, `GND`) as the pre-instruction and no-fetch observability layer.
- Add a write-only eight-bit POST latch at a newly reserved, conflict-checked I/O
  address (preferred `20h`) with reset clear, a compact eight-LED display or LED
  bar, current limiting, and bit labels `7`--`0`. The display must retain the last
  code through a halt or failure. Its decode must not alias PIC `00h`--`01h`, PPI
  `04h`--`07h`, USART `08h`--`09h`, original PPI1 `0Ch`--`0Fh`, video PITs
  `10h`--`17h`, D57 `18h`--`1Bh`, or the future FDC `1Ch`--`1Fh`.
- Freeze a documented byte convention before firmware implementation: high
  nibble identifies the stage, low nibble `0` means entered, `1` means passed,
  and `F` means failed; `FFh` means ready. Required stages cover reset/entry, ROM,
  RAM-data, RAM-address, D57, USART, PPI/PIC, VGA/frame activity and final ready.
- The diagnostic ROM must not establish a RAM stack, call a RAM-dependent helper,
  or rely on initialized RAM before both RAM-data and RAM-address tests pass.
  Early stages write the latch directly. Once D57 channel 1 works, failures may
  add audible codes; once the 8251 works, detailed status goes to TTL serial.
- The LED latch is independent of D57 so a missing/bad PIT can still be reported.
  Serial is the rich diagnostic layer, not the only diagnostic layer.

### First-article ROM set

Maintain three independently named, reproducible 27C256 programming artifacts:

1. **EKTA3.7/VJUGA** -- the existing Ekta 3.7 image with only the demonstrated
   Z80 opcode/checksum adaptation.
2. **NETC10/VJUGA** -- C10 rather than immutable C9 as the source baseline, thus
   preserving the physically proved C9 ABI/network/CP/M behavior and the C10
   PC7/POF release fix. Apply the demonstrated Z80 adaptation and 27C256 image
   layout, but no PIT bypass or fixed-clock patch.
3. **DIAG/VJUGA** -- the bring-up ROM extended for the POST latch, no-stack early
   RAM tests, D57 channel/count checks, 8251 TX/RX, PPI/PIC checks, VGA/frame
   activity and final TTL detail. The existing textual output remains a late
   stage rather than proof that early POST is observable.

Each image needs a source/build recipe, exact size and duplication rule, SHA-256,
program/readback procedure and a simulation tied to its intended hardware mode.
The immutable C9 artifacts remain unchanged as comparison fixtures.

### Scope boundaries and physical policy

- Populate the already-routed 8255 and 8259 functions in the C10-capable first
  system; the minimal bring-up population may still omit them until its staged
  bench step. D54/D55 raster generation and D57 channel-2 `SYNC B` remain
  intentionally replaced by the VGA subsystem.
- Re-place and reroute the complete I/O card; do not patch the released Gerbers.
  First attempt remains a 100x100 mm two-layer through-hole card. If a bounded
  placement/routing study cannot achieve connectivity and DRC 0/0 with usable
  socket, jumper, LED and test-point access, stop for an explicit layer-count or
  outline decision instead of deleting PIT/POST features silently.
- Every new reference and value/role marking follows the already-frozen pinned
  GOST Book silkscreen rules. New top/bottom PNGs require human review. The
  revised board and all regenerated archives must pass the existing JLCPCB
  profile, exact-part, mechanical, power, DRC/LVS and independent-Gerber gates.

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
| **R5.P1 — DONE 2026-08-28** | Make programmable logic on the existing boards buildable: Memory ATF22V10 and I/O ATF16V8 equations, device declarations, compiler command, pinned tool/version, JEDEC outputs and fuse/checksum record. | R5.0 | Pinned Galette rebuild reproduces both JEDECs; exhaustive equations/pin-map checks pass; the full four-mode Memory map and complex-mode-safe I/O pinout are implemented; programming/readback procedure is documented. |
| **R5.V1 — DONE 2026-08-28** | Audit the video digital model against real silicon and convert scoped LVS into a full-card pin-level connectivity plan. Confirm logic families, fan-out, polarity, tied/unused inputs, reset states, bus ownership, SRAM timing and `WAIT_N`. | R5.0 | All 23 digital packages/398 pins close after R5.V2 added independent RGB drivers; post-V3 full-card LVS matches 106 nets; independent checker and LVS mutation controls reject swapped/missing pins; 29.166 ns guarded fetch margin and open-drain WAIT ownership are frozen. |
| **R5.V2 — DONE 2026-08-28; V4 exact-part correction** | Close video power and analogue-output details. Provide one 100 nF capacitor at every IC plus local bulk capacitance; model total five-card current; retain monitor-side 75 ohm loading and verify that the 470 ohm RGB series network produces the intended level. | R5.V1 | Board/checker prove 23/23 local 100 nF capacitors plus 47 uF bulk; three independent ACT outputs drive 470-ohm series parts into monitor-side 75 ohms at 0.606–0.688 V; exact ECS oscillator raises the five-card budget to 1351 mA with 32.45% headroom on 2 A. |
| **R5.V3 — DONE 2026-08-28** | Produce sources and reproducible JEDECs for all three Video GALs. Fix `FRAME_TICK` to divide by six for the 2.000 MHz first article and retain a documented way to retarget it if the CPU oscillator changes. | R5.V1 | Five-GAL clean rebuild passes; U5/U6/U7 pins and equations are exhaustively checked; exact fetch/WAIT and divide-six simulations pass; integrated TTL-card EKTA boot is byte-identical to cosim. |
| **R5.V4 — DONE 2026-08-28** | Pin exact orderable mechanical parts before layout: right-angle female DE-15 VGA connector, 25.175 MHz 5 V oscillator, SRAM, GAL packages, bus headers, sockets and tall/polarized parts. | R5.V1 | Exact MPN contract and availability snapshot are recorded; checked custom VGA land pattern rejects a generic HD15; all 23 sockets are package-derived; card/backplane bus orientation, mating rows, tall/polarized parts and corrected oscillator current are machine-checked. |
| **R5.V5 — DONE 2026-08-28** | Generate, place and route the Video PCB on four layers (`signal / solid GND / solid VCC5 / signal`). Keep the dot-clock chain and pixel path short, add source damping where the audit calls for it, and preserve a continuous return plane. | R5.V2, R5.V3, R5.V4 | Fresh generation and bounded attempt-1 routing pass full connectivity/LVS, total DRC 0/0, single-island plane/return-path, local-bypass, critical-route and exact connector checks; routed source and negative controls are committed. |
| **R5.V6 — DONE 2026-08-28** | Re-run the assembled five-card mechanical and power model: connector mating, 16 mm slot pitch, adjacent-card/tall-part clearance, VGA-cable access, orientation/keying, current path and supply drop. Qualify one regulated 5 V supply rated at least 2 A and protect every intended bench input. | R5.S2, R5.V5 | All four populated card STEP envelopes clear (4.16 mm minimum; Video in slot 5 with slot 4 empty); exact VGA face projects 5.80 mm beyond its edge. Mean Well GST25A05-P1J plus fused/reverse-protected barrel input is frozen; the R5.J2 release-source route gives 4.628 V minimum trough and rejects five physical/electrical mutations. |
| **R5.J1 — DONE 2026-08-28** | Encode a JLCPCB rule profile and preflight checks for both the four 2-layer boards and the 4-layer Video board. The audit removed the optional USB4085 power path rather than relying on a vendor exception. | R5.V5 | `jlcpcb-profile.json` and `check_revb_jlcpcb.py --self-test` cover stack-up/layers, outline, drills/slots, annular rings, clearances, silk, masks, filenames and archive contents; seven negative fixtures fail. Fresh backplane generation/routes DRC 0/0 on attempt 1. |
| **R5.I1 — DONE 2026-08-28** | Freeze the D57/POST electrical and I/O contract: exact timer part/footprint, `18h`--`1Bh` decode, 1.2288 MHz/2 MHz clock sources, channel gates, PIT/direct clock selection, sound load, POST address/code table and expanded GAL pinout. | R5.S3, R5.P1 | `io-expansion.json`, `check_revb_io_expansion.py` and `rev-b-io-expansion.md` exhaust all 256 ports and both IORQ/M1 states, prove no aliases/floating timer inputs, close exact baud/LED/sound/power arithmetic and fit 11 inputs/8 outputs in the preferred ATF22V10. |
| **R5.I2 — DONE 2026-08-28** | Extend the I/O-card HDL/twin with the real 8253/82C54 register/count/latch behavior, PIT-driven 8251 clocks, channel-1 sound observation, POST latch and direct-clock recovery mode. | R5.I1 | `revb_io_expansion_check.sh` proves count/latch reads, master/16 count-four `OUT0`, 5102-clock mode-3 sound, retained/reset/read-silent POST, M1 exclusion and real-8251 loopback in PIT-normal/direct-19,200/direct-9,600 modes; wrong-tap and POST-alias mutations fail. Existing card, bring-up, two-mode EKTA, TTL-video and serial-console regressions pass. |
| **R5.I3 — DONE 2026-08-28** | Produce the three-ROM VJUGA set and enhanced diagnostic POST flow without using RAM stack/helpers before RAM passes. | R5.I1 | `revb-rom-set.json` binds reproducible 32 KiB EKTA3.7/VJUGA, NETC10/VJUGA and DIAG/VJUGA hashes and programming/readback procedure. `check_revb_rom_set.py` proves EKTA's exact four-byte adaptation, zero-byte canonical-8080 NETC10 adaptation with PIT sequence retained, identical 16 KiB halves, immutable C9, no early DIAG stack/helper, and ordered LEDs → D57 tone → TTL detail → 40-byte VGA pattern. |
| **R5.I4 — DONE 2026-08-29** | Replace/expand the I/O decode GAL implementation, add PIT, clock-source selector, POST latch/display, sound driver, decoupling and test points to the generated I/O netlist and complete pin-level LVS. | R5.I1, R5.I2 | Five-device clean GAL rebuild passes with the replacement ATF22V10 JEDEC; exhaustive address/M1/POST-polarity controls reject five faults. `check_revb_io_board_expansion.py --self-test` closes U1--U9, clocks, jumpers, LEDs, sound and decoupling, while independent LVS matches all 9 mapped instances/30 nets with zero differences. |
| **R5.I5 — DONE 2026-08-29** | Re-place and route the revised I/O card, preserving assembly access and the 100x100 mm/two-layer target; apply complete GOST ref+value/role silk. | R5.I4 | Bounded attempt-1 FreeRouting reaches total DRC 0/0. `check_revb_io_pcb.py --self-test` proves two-layer route geometry, nine front/local bypasses, ordered POST LEDs, accessible service controls and six mutations. FreeCAD gives 3.24 mm minimum assembled clearance; reviewed top/bottom PNGs show complete GOST assembly labels, with the dense POST legends deliberately row-aligned. |
| **R5.I6 — DONE 2026-08-29** | Run integrated ROM/system regressions against the revised hardware, including PIT-normal and direct-recovery modes. | R5.I2, R5.I3, R5.I4 | `revb_rom_system_check.sh` proves EKTA framebuffer identity in both decode modes and the chip-level TTL `/WAIT` path; NETC10 reaches POST 00, performs real D57 count-four, releases POF, emits C7 and completes the exact ABI 1.4 exchange; DIAG retains all 16 ordered codes, tone, exact 60-byte TTL detail and 40-byte VGA pattern. RAM/PIT/USART plus POF/POST mutations fail at their intended layers, and all three clock-selector modes pass. |
| **R5.I7 — DONE 2026-08-29** | Requalify the changed five-card system and release pipeline: exact parts, power, mechanics, JLCPCB profile, bench runbook and package/release guards. | R5.I5, R5.I6, R5.V6, R5.J1 | `revb_i7_release_check.sh` passes 158/158 populated footprints, exact expanded-I/O parts, 1655 mA current and 4.574 V minimum routed trough, 3.24 mm STEP clearance, all-five DRC 0/0, JLC geometry and negative controls. The 16-stage bench log has an explicit measured PIT/POST table, and release-gate self-tests reject stale source-PCB hashes. |
| **R5.J2 — DONE 2026-08-29** | Regenerate all five fabrication ZIPs in one release run. Emit a manifest with source revision, tool versions, board dimensions/layers, file list and SHA-256 per archive. | R5.I7 | `export_fab.sh` emits the exact source-hash-bound five-archive set below; package structure, JLC profile and all-five DRC 0/0 pass. |
| **R5.J3 — DONE 2026-08-29** | Perform an independent pre-upload review and obtain a fresh live JLCPCB quote. Check every Gerber/drill rendering separately; reconcile the five designs with BOM quantities and programmed-device count. | R5.J2 | The archive-side review passes 42 separate layer/drill renders plus 10 composites, 158/158 populated footprints and six fitted programmed devices. A fresh no-upload/no-cart official quote records $38.50 fabrication subtotal. |
| **R5.R1** | Hold the final release review. | R5.J3 | All gates below are green, exact package hashes are recorded, the owner explicitly changes `ORDER HOLD` to `RELEASED FOR UPLOAD`, and `check_revb_release_gate.py --require-released --package-root fab/minimal-vga/revb/package` passes. |
| **R5.O1 — RUNBOOK READY / HELD** | After R5.R1, upload the five independent designs, inspect JLCPCB's generated production files, resolve rather than silently accept DFM edits, and place the order only after a separate owner order instruction. | R5.R1 | `rev-b-five-board-order-record.md` binds upload to the released hashes, records every preview/option/warning and final combined quote, and separates preview authorization from payment; completion requires the order ID. |
| **R5.B1 — LOG READY / HARDWARE PENDING** | After delivery, inspect and assemble in stages: bare backplane, CPU clock/reset, NOP free-run, Memory, I/O+serial, then Video. | R5.O1 | `rev-b-b1-bench-log.md` records receipt, three ROM-media plus five GAL readbacks, current/rails/logic at 16 gated stages, measured D57/POST evidence and failures before proceeding; final gate is repeatable EKTA VGA boot plus bidirectional NETC10 serial. |

The previous `TI.5 held until T1.11` dependency is therefore replaced by the
R5 chain above. The new D57/POST decision inserts R5.I1--R5.I7 before any package
refresh. The physical risk is not erased; it is addressed by the revised desk
models, R5.I5/I7, R5.J3 and the deliberately staged R5.B1 bring-up.

## JLCPCB fabrication profile and checks

Capability snapshot: 2026-08-27. Recheck the vendor pages and live quote at
R5.J3 because manufacturing options can change.

- Common: FR-4 TG135, 1.6 mm, 1 oz outer copper, green solder mask, white silk,
  lead-free HASL; enable production-file confirmation. Use Tented vias for the
  four 2-layer designs. The current standard 4-layer form disables Tented, so use
  Plugged vias and its default 0.5 oz inner copper for Video.
- Two-layer cards: plan ordinary routing at 0.20/0.20 mm or larger even though
  JLCPCB currently lists a 0.10/0.10 mm ordinary 1 oz minimum.
- Video: use a listed standard four-layer stack-up without controlled impedance;
  do not invent dielectric dimensions. Inner GND and VCC layers must appear as
  copper layers in both archive and preview.
- Through holes: design the finished hole at least 0.10 mm over the maximum lead
  dimension and account for the listed +0.13/-0.08 mm PTH tolerance. Prefer at
  least 0.25 mm annular ring on two-layer boards and 0.20 mm on four-layer.
- Prefer vias of at least 0.20 mm finished hole; the routed Video card uses
  0.30/0.60 mm drill/diameter vias, leaving a 0.15 mm annular ring. R5.J1 must
  explicitly qualify that local four-layer geometry. Any plated slot must be at least 0.50 mm wide
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

## Current R5.J2 release-candidate identity

The machine-readable record is `rev-b-five-board-package-manifest.json`. These
archives were generated from reviewed routed sources based at Git revision
`5f0a523b2e0bc176f58bb22856b27ce8c165701e`; the manifest also binds each exact
routed PCB SHA-256. The ZIP files remain untracked under
`fab/minimal-vga/revb/package/`. They are the current technically reviewed
candidate, but remain **not authorized for upload**.

| Design | Layers | Production members | ZIP bytes | SHA-256 |
|---|---:|---:|---:|---|
| CPU | 2 | 9 | 47,759 | `abb9db95173d30fd5aeae7bce8d5a52cbdeba84bc2771722746e5d3e19b7b325` |
| Memory | 2 | 9 | 65,229 | `741aebf2a7d87e5473fc2b7efbb0cef343034239f63dcde41153034471c7bf70` |
| I/O | 2 | 9 | 236,336 | `a3cc2f2509c28799542e99a12279eafa25754f91c5ae601e28b99dcb05883a4f` |
| Backplane | 2 | 9 | 220,515 | `c6d15a55cd56c5f1114bb831fbf57868b0c37204fab162ca6ace45322fe4456d` |
| Video | 4 | 11 | 589,084 | `44b3a8df5d3e5d1ebb3258ed6151151502c898ec342761c041381842a8483b44` |

Reproduce and validate them with:

```sh
spinoffs/minimal-vga/kicad/revb/export_fab.sh
```

## Final release gate

R5.R1 cannot pass until all of the following are true:

- **DONE 2026-08-29:** R5.I1--R5.I7 implement and qualify the D57/POST contract,
      all three VJUGA ROMs and the changed I/O/system release source. The pre-D57
      archives remain historical evidence, not release evidence.
- **DONE 2026-08-29:** All five revised routed board sources are present, bound by
      exact source hashes, pass full net/pin checks, total DRC 0/0 and mechanical mating, and
      feed the one-command fabrication release.
- **DONE 2026-08-29:** The five-card simulation boots EKTA3.7/VJUGA byte-identically,
      boots NETC10/VJUGA through the real PIT path, runs DIAG/VJUGA's layered POST,
      and passes VGA timing, framebuffer, `WAIT_N`, reset, `FRAME_TICK`, sound and
      serial request/reply gates.
- **DONE 2026-08-29:** Memory, expanded I/O and all three Video GALs have reproducible,
      pin-checked JEDECs and a recorded programming/readback procedure.
- **DONE 2026-08-29:** Exact timer, display, sound, connectors, oscillators, sockets and
      other footprint-critical parts are orderable and tied to checked datasheets.
- **DONE 2026-08-29:** Revised decoupling, five-card current, protected supply path, routed
      voltage drop and USB-TTL electrical compatibility are closed.
- **DONE 2026-08-29:** Five regenerated JLCPCB-ready ZIPs and their new hashes pass the
      encoded vendor profile and exact package-content checks.
- **DONE 2026-08-29:** A new independent layer/drill/composite review, first-system
      BOM/programming reconciliation and current no-upload JLCPCB quote pass;
      combined checkout price and upload-derived warnings remain R5.O1.
- **PENDING:** The owner explicitly authorizes upload after seeing the final evidence.

The machine-readable hold is `rev-b-five-board-release-gate.json`. The ordinary
checker proves that current evidence, routed sources and exact archive hashes agree
while authorization is absent:

```sh
spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py \
  --self-test --package-root fab/minimal-vga/revb/package
```

Before any upload, the stricter command below must pass. It deliberately exits 3
while held and cannot pass merely because the technical gates are green: it requires
an explicit owner identity, ISO timestamp, exact authorization phrase and a second
copy of all five hashes, plus matching `RELEASED FOR UPLOAD` state in this plan.

```sh
spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py \
  --require-released --package-root fab/minimal-vga/revb/package
```

The correct next action is the held R5.R1 owner review, not an upload or order.
The post-release procedure is already frozen in
`rev-b-five-board-order-record.md`; the after-delivery procedure is already frozen
in `rev-b-b1-bench-log.md`, including the R5.I7 PIT/POST measurement stages.
Neither prepared template changes its dependency or authorizes the physical step.
