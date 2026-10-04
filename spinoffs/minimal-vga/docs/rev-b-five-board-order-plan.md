# VJUGA rev B — five-board first-article order plan

Status: **ACTIVE PLAN / ORDER HOLD**. The reviewed five-archive candidate includes
D57/POST and complete GOST assembly markings. Owner upload authorization is absent.
See [current status](rev-b-status.md) and the
[silkscreen contract](rev-b-silkscreen-audit.md).

This is the controlling plan for the first VJUGA rev B order. The intended
machine is one complete five-card system: CPU, memory, I/O, backplane, and a
working VGA card. It must also expose the existing 8251 as a practical
bidirectional TTL serial console, and every fabrication package must be checked
against JLCPCB's current requirements before upload.

Only the exact five-archive candidate identified by the release record may
proceed through the gates below. **Do not upload or order superseded packages.**
No PCB design work or purchase is authorized merely by recording this plan.

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

1. **EKTA3.7/VJUGA** -- the retained label for archive-0037 RomBios 3.43m,
   with only the demonstrated four-byte Z80 opcode/checksum adaptation.
2. **NETC10/VJUGA** -- C10 rather than immutable C9 as the source baseline, thus
   preserving the physically proved C9 ABI/network/CP/M behavior and the C10
   PC7/POF release fix. The canonical 8080 source requires no Z80 opcode
   substitutions; duplicate its 16 KiB image into the 27C256 halves without
   a PIT bypass or fixed-clock patch.
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

## Desk qualification and remaining steps

The entries below retain the gate IDs required by `check_revb_release_gate.py`.
They identify the held candidate's desk qualification and maintained evidence;
they do not establish physical acceptance or a fresh execution of the checks.
The [execution guide](rev-b-execution-guide.md) lists verification commands.

| Gate | Scope and maintained evidence |
|---|---|
| **R5.S1 — DESK QUALIFIED** | Serial connector direction and continuity; [serial console](rev-b-serial-console.md) |
| **R5.S2 — DESK QUALIFIED** | Serial clocks and protected electrical boundary; [serial console](rev-b-serial-console.md) |
| **R5.S3 — DESK QUALIFIED** | 8251 TX/RX, loopback, isolation and loader byte-pattern tests; actual NETC10 execution is covered by R5.I6 |
| **R5.P1 — DESK QUALIFIED** | Reproducible programmable logic; [current GAL equations](rev-b-gal-equations.md), including the R5.I4 I/O replacement |
| **R5.V1 — DESK QUALIFIED** | Video pin connectivity and timing; [digital audit](rev-b-video-digital-audit.md) |
| **R5.V2 — DESK QUALIFIED** | Video decoupling and RGB loads; [power model](rev-b-five-card-power.md) |
| **R5.V3 — DESK QUALIFIED** | Video GAL equations, fetch/WAIT and divide-six frame tick; [GAL equations](rev-b-gal-equations.md) |
| **R5.V4 — DESK QUALIFIED** | Exact Video parts and footprints; [parts contract](rev-b-video-parts.md) |
| **R5.V5 — DESK QUALIFIED** | Four-layer Video routing, planes and DRC; [PCB qualification](rev-b-video-pcb.md) |
| **R5.V6 — DESK QUALIFIED** | Assembled clearance and protected power; [mating report](rev-b-mating-report.md) and [power model](rev-b-five-card-power.md) |
| **R5.J1 — DESK QUALIFIED** | Encoded fabrication rules and exceptions; [JLCPCB profile](rev-b-jlcpcb-profile.md) |
| **R5.I1 — DESK QUALIFIED** | PIT/POST electrical and I/O contract; [I/O expansion](rev-b-io-expansion.md) |
| **R5.I2 — DESK QUALIFIED** | PIT register/count/latch, sound, POST and clock-selector simulation; `sim/revb_io_expansion_check.sh` |
| **R5.I3 — DESK QUALIFIED** | Three-ROM builds and early no-stack POST; [ROM guide](../roms/README.md) |
| **R5.I4 — DESK QUALIFIED** | Expanded I/O netlist, ATF22V10 and pin-level LVS; [I/O expansion](rev-b-io-expansion.md) |
| **R5.I5 — DESK QUALIFIED** | Routed I/O geometry and assembly markings; `kicad/revb/check_revb_io_pcb.py` |
| **R5.I6 — DESK QUALIFIED** | Integrated EKTA, NETC10 and DIAG simulation, including PIT-normal and direct recovery; `sim/revb_rom_system_check.sh` |
| **R5.I7 — DESK QUALIFIED** | Expanded system parts, power, mechanics and release checks; `kicad/revb/revb_i7_release_check.sh` |
| **R5.J2 — DESK QUALIFIED** | Five source-bound fabrication archives; [package manifest](rev-b-five-board-package-manifest.json) |
| **R5.J3 — DESK QUALIFIED** | Archive render/BOM review and dated quote; [signed pre-upload review](rev-b-five-board-preupload-review.md) |

Remaining steps, in order:

1. **R5.R1 — HELD:** review the exact candidate and obtain owner upload
   authorization under the final release gate below.
2. **R5.O1 — RUNBOOK READY / HELD:** after R5.R1, follow the
   [order record](rev-b-five-board-order-record.md) for upload, vendor production
   previews, DFM review and the combined quote. Placing the order requires a
   separate owner instruction; completion requires an order ID.
3. **R5.B1 — HARDWARE PENDING:** after delivery, use the
   [bench template](rev-b-b1-bench-log.md) for receipt, three ROM-media and five
   GAL readbacks, and 16 gated assembly/power-up stages. Final acceptance requires
   repeatable EKTA VGA boot and bidirectional NETC10 serial.

## JLCPCB fabrication profile and checks

Use the frozen [fabrication profile](rev-b-jlcpcb-profile.md) and its
`kicad/revb/jlcpcb-profile.json` contract for layer counts, stack-up, holes,
clearances, silk, allowed exceptions and archive membership. All five designs
are independent bare boards for hand assembly. The project's GOST text minimum
is 1.5 mm; assembly labels are 1.6 mm, as specified in the
[silkscreen contract](rev-b-silkscreen-audit.md).

The vendor capability references and quote are dated evidence. Recheck them
before release/upload; the retained quote does not establish current price,
availability or acceptance of the production files. Use production-file
confirmation and resolve any vendor changes through the order record.

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

To create a new export from the reviewed routed sources, run from the repository
root:

```sh
spinoffs/minimal-vga/kicad/revb/export_fab.sh
```

The exporter replaces the local package directory and rewrites the tracked
manifest with the new archive hashes, source revision and tool versions. It does
not promise byte-identical reproduction of the recorded ZIPs. A new package
requires review and reconciliation with the release record before upload.
Inspect tool-skip messages: without KiCad CLI or its Python module the exporter
exits successfully without producing a package. To verify the retained candidate
without replacing it, use the release checker below.

## Final release gate

Before release, establish that the exact candidate still meets these requirements:

- D57/POST hardware, all three ROMs and the complete five-card system match the
  maintained contracts and pass their behavioral, net/pin and GAL checks.
- Routed sources pass total DRC, mechanical, power and exact-part checks;
  fabrication archives match those sources and the encoded vendor profile.
- Independent layer/drill/composite review, BOM/programming reconciliation and
  a fresh quote cover that exact package. Recheck part availability before purchase.
- **PENDING:** The owner explicitly authorizes upload after seeing the final evidence.

The qualification index records the retained desk results. The release checker
cross-checks hashes, files, recorded PASS states and plan markers; it does not rerun
behavioral, CAD or vendor checks, or perform a new visual review.

The machine-readable hold is `rev-b-five-board-release-gate.json`. The ordinary
checker verifies the recorded evidence identities, current routed-source hashes
and (with `--package-root`) exact archive hashes while authorization is absent:

```sh
spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py \
  --self-test --package-root fab/minimal-vga/revb/package
```

Before any upload, the stricter command below must pass. It deliberately exits 3
when the held record is otherwise valid (validation errors exit 1). It requires
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
