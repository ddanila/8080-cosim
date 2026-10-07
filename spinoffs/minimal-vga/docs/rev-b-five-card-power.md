# VJUGA rev B five-card power and VGA output — R5.V2 / R5.I7

Status: **PASS / R5.I7 SYSTEM MODEL FROZEN; PHYSICAL ACCEPTANCE PENDING.**
The desk budget, routed-board voltage drop, exact normal supply, protected inputs
and modeled assembly clearance form one machine-checked contract. Current draw,
supply ripple and assembled-board behavior still require physical acceptance.

## Video bypass and bulk capacitance

The populated digital set is U1-U23. The generated board contains exactly C1-C23,
each 100 nF from VCC5 to GND, with the numbering contract `Cn` local to `Un` at layout.
`C_BULK` is 47 uF from VCC5 to GND near the card power entry. The power guard checks
these populations and connections in `video.board.json`; physical placement is
covered by the separate [Video PCB gate](rev-b-video-pcb.md).

R5.V5 places every 100 nF VCC pad within 12.85 mm of its corresponding package
supply pad and gives it a short solid-ground-plane return. Seven constrained parts
(C5, C7-C11 and C21) sit on the card back directly between front-side socket rows;
their assembled height is included in the passing R5.V6 STEP clearance. The bulk part
handles card-scale transients; the solid four-layer GND/VCC planes supply the high-
frequency return path.

## VGA RGB electrical model

The monitor, not the card, supplies 75 ohms to ground on each RGB input. Each on-card
part is a **470 ohm series resistor**. U23 assigns a separate CD74ACT08 output to red,
green and blue, avoiding the previous 27 mA combined load on one logic gate.

At a 5.0 V ideal source, each monitor pin receives:

`5.0 × 75 / (470 + 75) = 0.688 V`

and its driver sources `5.0 / 545 = 9.174 mA`, below the ACT output's recommended
24 mA/channel limit. There are no on-card 75-ohm “terminations.”

The frozen JSON model assumes a 4.4 V driver-high and calculates 0.606 V at the
monitor, giving a modeled range of 0.606-0.688 V. This is not a datasheet-guaranteed
loaded range: [TI's electrical characteristics](https://www.ti.com/lit/ds/symlink/cd74act08.pdf)
specify 4.4 V minimum at only 50 µA, and 3.8 V minimum at 24 mA with a 4.5 V
supply over −40 to 85 °C. The arithmetic guard does not establish the output voltage
at the actual roughly 9 mA load. Measure all three RGB highs into 75-ohm loads,
including the lowest accepted card rail, before accepting the VGA level.

## Conservative +5 V current budget

The budget uses actual first-article population, conservative datasheet/planning
ceilings and explicit per-card allowances. In particular, each non-low-power
ATF22V10 is allowed 125 mA, matching Microchip's 15 MHz maximum-current revision;
Video has three. RGB assumes all three channels continuously high.

| Card/block | Budget |
|---|---:|
| CPU complete card | 250 mA |
| Memory complete card | 235 mA |
| I/O complete C10 tier, including D57, POST and sound | 454 mA |
| Backplane/reset/console/pulls | 30 mA |
| Video oscillator (`ECS-100A-251.7`, 25.175 MHz band maximum) | 70 mA |
| Video 3 x ATF22V10 | 375 mA |
| Video 3 x M74HC393 | 24 mA |
| Video 4 x CD74ACT157 | 20 mA |
| Video 4 x CD74ACT161 | 40 mA |
| Video CD74HC283 | 5 mA |
| Video 2 x CD74ACT273 | 10 mA |
| Video SN74ALS166 | 24 mA |
| Video CD74HCT245 | 10 mA |
| Video HCT08 + ACT08 | 10 mA |
| Video AS6C1008 | 40 mA |
| Video three RGB loads | 28 mA |
| Video card allowance | 30 mA |
| **Video subtotal** | **686 mA** |
| **Five-card total** | **1655 mA** |

A regulated 5 V, 2 A design limit leaves 345 mA (17.25%) planning headroom. The exact
4 A adapter therefore has 2.345 A of nameplate headroom. The production
backplane has no USB power branch and must not be presented as USB-powered. First
power-up still uses a current limit and staged card insertion.

## R5.V6 protected normal input and supply

Normal operation uses a center-positive **Mean Well GST25A05-P1J**, rated 5 V/4 A,
through exact Wurth `694106301002` barrel jack `J_PWR` (5 A). `F_MAIN` is a Bourns
MF-R300 in series between `PWR_RAW` and `VCC_BUS`; it holds 3.00 A at 23 C, 2.49 A at
40 C and 1.83 A at 70 C, all above the 1.655 A frozen load. The recorded nominal trip current is 6 A. `D_REV` is a 5 A Vishay SB560
crowbar after that fuse, cathode to `VCC_BUS` and anode to `GND_BUS`. This topology
is intended to clamp a reversed input; the desk gate does not qualify its fault
response with the selected adapter.

The barrel jack is the sole power input; the USB-TTL console is data-only.
`W_VCC` and `W_GND` are fitted insulated 22-AWG links that join the high-current
bus rails to the backplane's local logic rails.

The selected adapter publishes a broad +/-5% voltage tolerance, so its nameplate
alone is insufficient for this conservative TTL corner. Receipt acceptance is an
electronic-load test at **1.655 A**: at the plug, require at least **4.90 V average**
and no more than **80 mV peak-to-peak** ripple. A delivered unit that misses either
limit is not qualified for this machine.

## Routed voltage-drop result

The backplane routes `VCC_BUS` and `GND_BUS` at 0.80 mm on 1 oz copper and the short
barrel-to-fuse `PWR_RAW` link at 2.00 mm. The checker turns every actual routed segment
into a resistor, bridges plated pads/vias, and solves all occupied-slot currents. It
also charges maximum initial fuse resistance, both barrel contacts, one VCC and one
GND bus contact per card, and half the adapter ripple limit.

| Slot / card | routed copper drop | modeled rail trough | margin over 4.50 V |
|---|---:|---:|---:|
| 1 / CPU | 90.40 mV | 4.574 V | 74 mV |
| 2 / Memory | 85.48 mV | 4.580 V | 80 mV |
| 3 / I/O | 75.96 mV | 4.582 V | 82 mV |
| 5 / Video | 38.85 mV | 4.613 V | 113 mV |

The routed effective raw-path resistance is 3.554 mOhm and the shared worst-case
input drop is 187.93 mV. At the adapter's unqualified published -5% corner the
modeled trough would be only 4.424 V; this is why the delivered-unit
receipt test is mandatory.

## Machine gate

`check_revb_video_power.py` checks JSON capacitor/RGB connectivity and the
arithmetic in `video-power-audit.json`. It does not derive current allowances
or driver ratings from datasheets.

`check_revb_system_physical.py` uses the retained routed backplane and
`five-board-physical.json` for DC drop calculations, with fixed allowances for
plated connections and contacts. Reported troughs are at card bus connectors;
the solver does not include each card's internal rail distribution or transient
loads. It checks the protected-input topology and recorded ratings, not fuse-trip
or crowbar dynamics. Clearance is calculated from stored STEP envelope bounds;
it does not regenerate or inspect STEP models. See the
[mating report](rev-b-mating-report.md) for the assembly scope.

Run from the repository root; the system guard requires KiCad Python and NumPy:

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_video_power.py --self-test
. spinoffs/minimal-vga/kicad/revb/env.sh
"$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_system_physical.py --self-test
```

The power guard rejects two mutations: a missing C23 and shared RGB outputs.
The system guard rejects a narrowed routed VCC segment, a raw-path width
requirement raised above the retained track width, 12 mm slot pitch, low supply
voltage and a stale current total. These are software checks of the model;
physical acceptance remains pending.

Primary sources: [Microchip ATF22V10C](https://ww1.microchip.com/downloads/en/DeviceDoc/doc0735.pdf),
[TI CD74ACT08](https://www.ti.com/lit/ds/symlink/cd74act08.pdf), and
[Alliance AS6C1008](https://www.alliancememory.com/wp-content/uploads/pdf/AS6C1008_Mar_2023V1.2.pdf).
