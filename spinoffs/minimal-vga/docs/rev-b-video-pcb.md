# VJUGA rev B Video PCB — R5.V5

Status: **PASS / ROUTED SOURCE FROZEN; PHYSICAL ACCEPTANCE PENDING.**
This qualifies the individual Video-card layout, not fabrication authorization.
The [five-board release plan](rev-b-five-board-order-plan.md) controls current
package, factory and order gates.

## Physical result

- 100 x 100 mm, four copper layers in the fixed order `F.Cu / In1.Cu / In2.Cu /
  B.Cu`; In1 is one filled GND island and In2 is one filled VCC5 island.
- 54 physical footprints and 185 modeled nets. The exact NorComp VGA connector is
  centred on the top edge; its two 2.10 mm board locks and staggered 7+8 solder-tail
  rows follow the manufacturer drawing. The 39-pin base bus header is front-side,
  the 10-pin extension is back-side, and both right-angle post sets point out of the
  bottom edge.
- 2,432 routed signal segments and 137 through vias. Ordinary tracks are 0.20 mm;
  exactly seven locked B.Cu segments use 0.15 mm in the `VID_G` and `HSYNC_N` VGA
  necks. Vias are 0.60/0.30 mm diameter/drill. No signal track uses either inner
  plane.
- All 23 bypass capacitors have their VCC pad within 12.85 mm of the corresponding
  IC supply pad. C5, C7-C11 and C21 are mounted on B.Cu between their front-side
  socket rows. The current five-card [mating report](rev-b-mating-report.md)
  records a 3.24 mm minimum assembled gap at Memory–I/O; the I/O–Video gap
  is 15.62 mm with slot 4 empty. The other bypass parts and 47 uF bulk capacitor
  are front-side.
- `R_CLK` is a 33 ohm source resistor 6.28 mm from oscillator U1.8. Its pre-resistor
  `DOTCLK_RAW` route is 6.56 mm; the seven-load `DOTCLK` tree is 174.05 mm over the
  continuous return plane.
- The active pixel chain remains within its audited bounds: `PIXEL` is
  25.28 mm and `VID_PIXEL` is
  41.77 mm. The three ACT-to-RGB-resistor routes are 15.84, 11.03 and 14.40 mm.
- The generator fixes the U22.9/U22.10 `V_END` tie as a locked 2.54-mm F.Cu
  under-socket strap.

Recorded KiCad 10.0.5 DRC: **0 violations and 0 unconnected items**.
Video structural LVS compares the HDL pin netlist with `video.board.json`: 23
mapped instances and 106 matched nets. It does not extract routed PCB copper.

## Machine-enforced contract

`check_revb_video_pcb.py` checks the four-layer stack, exact plane nets and names,
solid pad connections, isolated-island removal, one filled island per plane, absence
of signal tracks on the inner layers, track/via floors, the two-net 0.15 mm exception,
all 23 local bypasses, VGA and bus presentation, source-resistor proximity and bounded
clock/pixel/RGB route lengths. Its seven negative controls mutate the extracted
inspection data: two-layer stack, project-rule limit, split-plane count, inner-layer
signal, bypass side, thin-track net and pixel-route length. All must be rejected.
Without `pcbnew`, this checker exits successfully with a `SKIP` message.

## Check the retained layout

Run from the repository root. Inspect any `SKIP` output: missing tools do not
establish a passing layout. DRC needs KiCad CLI, the physical checker needs
KiCad Python, and LVS needs Yosys.

```sh
. spinoffs/minimal-vga/kicad/revb/env.sh
revb_have KICAD_CLI && revb_have KICAD_PYTHON && {
  python3 spinoffs/minimal-vga/kicad/revb/check_revb_drc.py video --total &&
  "$KICAD_PYTHON" spinoffs/minimal-vga/kicad/revb/check_revb_video_pcb.py --self-test
}
spinoffs/minimal-vga/sync/revb_lvs.sh video
spinoffs/minimal-vga/sync/revb_video_lvs_mutation_check.sh
```

## Regenerate for layout work

`gen_revb_pcb.py video` replaces the tracked board with generated placement;
`route_revb_pcb.sh video` imports a new route into that board. Use these only
when deliberately revising the layout. Routing requires FreeRouting and Java 25,
can skip when dependencies are absent, and does not promise an identical route.
A replacement layout needs placement/total DRC, physical/LVS checks, visual review
and package requalification under the five-board release plan.

The committed routed source pair is `fab/minimal-vga/revb/video.kicad_pcb` plus
`video.kicad_pro`; KiCad 10 stores the intentional 0.15 mm track and 0.30 mm edge
limits in the latter. The personal `video.kicad_prl` is deliberately not source.
Preview SVGs are review aids only; they do not replace the source, DRC report or
independent Gerber inspection required later.
