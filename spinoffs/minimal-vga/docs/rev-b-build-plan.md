# VJUGA rev B build contract

The [five-board order plan](rev-b-five-board-order-plan.md) controls the current
first article and release gates. This document records durable design decisions;
[status](rev-b-status.md) and [execution](rev-b-execution-guide.md) provide the
current qualification boundary and commands. Completed task sequences and
routing experiments are available in Git.

Rev B uses Z80, SRAM and autonomous VGA to exercise Juku firmware contracts in a
modular machine. It retains the accepted memory/I/O interfaces and firmware
oracles; it does not establish physical equivalence to the original Juku PCB.

## System and card boundaries

- Five independent PCB designs: CPU, Memory, expanded I/O, Backplane and Video.
  The complete five-board candidate is reviewed and released together.
- The first-article CPU uses a socketed 2.000 MHz oscillator. Memory is ROM/SRAM;
  Video owns upper-window RAM accesses in modes 0/3, with a 9640-byte, 40×241
  framebuffer at `0xD800`. Memory serves the upper ROM overlay in modes 1/2.
- The I/O card contains the sole 8251, 8255, PIC, D57-compatible PIT and POST
  latch. Minimal bench population is a bring-up stage, not a different order.
- Video uses local SRAM and a 25.175 MHz clock on a four-layer board. It supplies
  `FRAME_TICK` and arbitrates CPU framebuffer accesses through `/WAIT`.
- A future FDC card would use extension `IRQ_A`/`IRQ_B` for INTRQ/DRQ. It is outside
  this order and has no completed hardware qualification.
- [The bus contract](rev-b-bus-contract.md) owns pin numbers, memory/I/O maps,
  defaults and interrupt wiring. Board specs and shared facts must agree with it.

## System decisions

Existing identifiers remain for references in source and qualification reports.

| ID | Current decision |
| --- | --- |
| S1 | CPU drives CLK from its socketed oscillator; first article is 2.000 MHz. Speed changes require firmware and timing requalification. |
| S2 | Video divides the VGA frame boundary by six for approximately 10 Hz `FRAME_TICK`, corresponding to the firmware's 200,000-cycle cadence. |
| S3 | The physical PIC is wired for the Z80 IM0/8080-compatible interrupt path. The assembled twin holds interrupts inactive, so it does not verify firmware interrupt-vector behavior. |
| S4 | Backplane owns pull-ups on shared active-low control lines; cards must not introduce opposing push-pull drivers. |
| S5 | `JP_S5` isolates the I/O-card 8251 from the backplane's board-relative `J_TTL`; no second UART or Serial card exists. |
| S6 | Regulated 5 V enters through the protected barrel jack only. USB-TTL is data-only; a future real-drive FDC supplies its own 12 V boundary. |
| S7 | Backplane supervisor/button is the sole reset authority. |
| S8 | Connector orientation is convention-only: silk marks and no hot-plug. The offset extension does not physically prevent every reversed insertion. |
| S9 | Analyzer headers and NOP free-run provision support staged diagnosis before firmware works. |
| S10 | Five slots; expansion beyond the planned card set needs a later backplane decision. |
| S11 | I/O drives MODE0/1 over USER2/3; backplane defaults them to boot mode when I/O is absent. |
| S12 | Serial ready interrupts stay on the I/O card; future FDC requests use the extension. Special clocks are local to their cards. |
| S13 | Minimal bench bring-up uses diagnostic firmware; EKTA requires the Video subsystem. The current three-ROM set is defined by R5.I3. |

## Component and interface decisions

| ID | Current decision |
| --- | --- |
| C1 | Main RAM uses AS6C1008-class 128K×8 5 V SRAM; decode exposes the accepted Juku map. |
| C2 | Socketed 27C256 with reproducible EKTA3.7, NETC10 and DIAG programming images; Memory ATF22V10 implements overlay decode. |
| C3 | Cards decode their own assigned ports. Root machine facts, the bus contract and the explicit PIT/POST extension define the map. |
| C4 | Double pixels horizontally and vertically; crop the final source row under the current video-timing contract. |
| C5 | Monochrome RGB uses independent drivers and resistor outputs into monitor-side terminations. Exact parts and levels belong to the Video power contract. |
| C6 | 8251-compatible UART preserves the firmware interface. |
| C7 | 8255 matrix scan and mode outputs preserve the accepted keyboard/overlay interface. |

## Construction and verification decisions

| ID | Current decision |
| --- | --- |
| D1.1 | UART data/control at `0x08`/`0x09`, decoded window `0x08–0x0B`. |
| D1.2 | Bring-up byte-stream comparison uses cosim's modeled 8251 and the twin's UART data-port writes. It checks startup byte agreement, not exact wire timing or interactive monitor commands. |
| D1.3 | Minimal bring-up RAM test covers `0x4000–0xD6FF`; reserve `0xD700–0xD7FF` for stack/variables and exclude Video-owned space. |
| D1.4 | Separate base and offset extension rows; exact geometry is in `mating.json`. Orientation safety follows D1.32b. |
| D1.5 | Each card flows from board spec through generation, checks, routing and export. |
| D1.6 | Console path: I/O 8251 → bus TX/RX → `JP_S5` → `J_TTL` → USB-UART; connector direction is board-relative. |
| D1.7 | Minimal population may omit PPI/PIC during staged bench work; the first-system design includes them and PIT/POST. |
| D1.8 | Normal UART clock comes from PIT channel 0: 4.9152 MHz divided by four, then programmed count four. Direct `/16` and `/32` are recovery paths, selected separately. |
| D1.9 | Use the first-article bench template for measured acceptance, not a session work log. |
| D1.10 | Tool locators live in `kicad/revb/env.sh`; inspect skips and the actual artifact's tool-version record. |
| D1.11 | Independent structural LVS scopes Memory, I/O and Video. CPU/backplane connectivity also needs direct connector and completeness checks. |
| D1.12 | Board connector nets must agree with `cards.json` roles and `bus-pinout.json`. |
| D1.13 | Generator owns placement and assembly silk; every physical footprint has reference plus value/role under the pinned GOST rules. |
| D1.14 | All five release sources need total DRC 0/0, correct package contents and the encoded vendor-profile checks. |
| D1.15 | Numeric mating and FreeCAD component envelopes verify clearance; physical bench inspection remains required. |
| D1.16 | Expanded I/O uses ATF22V10 decode, including PIT/POST and active-high 8251 reset. |
| D1.17 | Any later CPU buffer must enable data drive only on an actual read/write cycle, excluding refresh; current CPU is unbuffered. |
| D1.18 | Non-bus internal nets need at least two endpoints or an explicit tie/NC/DNP classification; bus continuation is checked across cards. |
| D1.19 | Validate control terms in the behavioral twin, independent pin checks and applicable firmware oracles before release. |
| D1.20 | All cards use shared generation and routing verification. Structural LVS covers Memory, I/O and Video; CPU and Backplane use direct connectivity checks. |
| D1.21 | First-article CPU connects directly to the bus. Buffering requires a later qualified revision. |
| D1.22 | LVS pinmaps derive from generator chip definitions; mapped-chip checks do not replace connector/passive checks. |
| D1.23 | Memory outline is 100×60 mm; connector positions and package orientation are machine-checked. |
| D1.24 | Route through the repository-pinned freerouting DSN/SES flow, then fill zones and check DRC. |
| D1.25 | Generated PCB equivalence is checked semantically; UUID/timestamp differences are not circuit differences. Release records bind exact routed artifacts. |
| D1.26 | PPI/PIC and keyboard paths are fully wired on the shared I/O design; the expanded design also includes PIT/POST. |
| D1.27 | Before routing, reject placement-class errors. After routing, require zero total violations and unconnected items; review assembly renders too. |
| D1.28 | Use a bounded placement sweep for persistent routing failures; any manual exception must be generator-emitted and independently checked. |
| D1.29, D1.30, D1.33, D1.34 | Production uses mate-compatible socket pairs and routes from scratch. |
| D1.31 | `mating.json` owns paired-row geometry and 16 mm slot pitch; generators and checks consume it. |
| D1.32 / D1.32b | Reversed insertion remains physically possible. Use orientation marks and staged inspection; do not claim mechanical keying. |
| D1.35 | Backplane input has bulk/local decoupling, MF-R300 protection and SB560 reverse crowbar; no USB power branch. |
| D1.36 | Exact parts and physical footprint guards cover drills, pitch and package width; names alone do not qualify a footprint. |
| D1.37 | 100×100 mm backplane, five slots and top-side service tail. Video occupies slot 5 with slot 4 empty for this first article. |
| D1.38 | Mean Well GST25A05-P1J must be receipt-tested at the qualified load/rail/ripple limits. Use the actual-copper distribution solve and bench rail checks. |
| D1.39 | GCT USB4085 is omitted from the production power path; the frozen process does not qualify its exact lands. |

## Video decisions

| ID | Current decision |
| --- | --- |
| D2.1 | Adopt the attributed TTL640x480 counter/timing concepts; [adoption note](rev-b-video-adoption.md) preserves scope, pinned source and MIT attribution. |
| D2.2 | Four-layer 100×100 mm Video board with signal/GND/VCC/signal stack and checked return planes. |
| D2.3 | AS6C1008 framebuffer SRAM; 9640 firmware-visible bytes, with the accepted Video window decode. |
| D2.4 | `video-timing.json` freezes `crop_bottom`. Source row 240 is omitted from VGA; banner qualification proves that row blank only for that workload. |
| D2.5 / D2.9 | Cycle-steal arbitration: `/WAIT` covers CPU accesses colliding with scanout fetches, not the whole active raster. Phase and integrated-CPU checks must show no lost writes. |
| D2.6 | Discrete counters plus ATF22V10 horizontal/vertical decode and arbitration; exact chip/pin connectivity is checked independently. |
| D2.7 | Stride-40 row-base generation uses four loadable counters and two registers. Capture the completed row count and reload on doubled lines. U16's 74×283 adder adds the framebuffer's `0x1800` SRAM offset; row-stride generation needs no multiplier. |
| D2.8 | Autonomous timing needs no firmware CRTC initialization. A programmable CRTC redesign is outside the current contract. |

Numeric timings, parts, power corners and package identities belong to their
machine-readable contracts and qualification reports. Use the
[execution guide](rev-b-execution-guide.md) to reverify them. **ORDER HOLD** remains
until the exact release record has explicit owner upload authorization; vendor
review, order authorization and physical bring-up remain separate gates.
