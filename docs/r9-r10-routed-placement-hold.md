# R9/R10 routed-placement hold

The source PCB has the photo-identified R9 and R10 2 kOhm footprints at
`(214.319,94.881)` and `(211.204,93.578)` mm, respectively. Both routed
variants still omit them. The source PCB also moved and rotated D12 to
`(224.535,67.630)` mm at 180°, while both routed variants retain D12 at
`(202.495,77.090)` mm at 0°.

A trial copy of `juku_routed.kicad_pcb` that duplicated the two source
footprints, without changing any other placement or copper, produced 23
shorting-item findings and 10 clearance findings. The contacts include
R9/R10 pads against existing P12V, P5V, WREQ_N, FRAME_INT, and IR7
copper, plus R10's upper pad against D12 pads 5 and 6. The same routed
board before the trial had zero shorts and clearances. The trial was not
applied to either routed variant.

Relocate D12 and review its existing routed connections first, then make
room for the two resistor footprints and reroute their +5 V and D3-side
connections. A direct footprint copy into the current routed copper is
electrically unsafe. The parity report separately counts the four absent
R9/R10 pad endpoints in each routed variant.
