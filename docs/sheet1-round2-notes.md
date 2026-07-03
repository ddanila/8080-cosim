# Sheet-1 (p3_sheet1.png, 5150x3603) zone map for round-2 crops (orig px)
- D9/ИД7 + CS4-CS7 outputs (ROM selects?): crop (1890,540)-(2340,960)
- D2 РТ4 decode PROM (V1/V2 outs) + REV/ROE/RAM_SEL logic: crop (690,1770)-(1260,2340)
- D8 РЕ3 (top, R41 pullups, E-pin): crop (1650,240)-(2100,560)
- D10 PIC IR row (FRAME INT/TAPE RUN INT/RxRDY/TxRDY/IR7/IR6): crop (1620,2340)-(1980,2700)
- D26 PPI keyboard zone W/ X9 PIN CODES (FK/K1/K2/SHIFT/CTRL/SC0-3/AUDC/PREN/STB -> 904/903/803/507/508/511-516/540 + X2 codes on PA): crop (2880,1800)-(3510,2880)
- D27 PPI (PB/PC -> X2 codes 213-225): same column below
- Sheet note: "D2,D6,D8,D15-D22 устанавливаются в панелях" (socketed) ✓ matches photos
- IO CS decode source for D10/D26/D11/D27/PITs: NOT yet located on this sheet -- check
  D105 zone (300,745 display) and mid-left АЛ5/ЛА3 gates; possibly sheet 2.
Next: crop D9 zone first (decode conflict), then D26 (X9 grounding).
FINDING: D9 = DC symbol, sel ins pins 1,2,3 <- driver pins 11,12,13 (NOT РЕ3 outs -- those are
inputs on РЕ3; РТ4 outs = 9-12 partial match only). D8_D0-D2 nets confirmed SUSPECT. V1=4,V2=5
tied (& enable), V3=6, E=15 top. Outputs 0-7 = pins 15,14,13,12,11,10,9,7 -> right w/ codes.
Driver chip = in crop s1_d9drv.png (left of D9).
RESOLUTION (crop s1_d9drv.png): the chip driving the ИД7 selects is **D6 РТ4** (A0-A7 on
5,6,7,4,3,2,1,15; V1=13,V2=14 tied enable; outs D0=12->net"ROM"(1K pullups, up to РЕ3 zone),
D1=11, D2=10 ("REV"), D3=9 ("ROE")). So board.json D8_D0/D1/D2 nets are WRONG refdes -- should
be D6 outputs -> D9.1/2/3 (exact out-pin->sel-pin mapping needs one cleaner crop: first crop
showed labels 11,12,13 at D9 pins 1,2,3; D6 outs are 12,11,10,9 -- verify which three).
ALSO: sheet-1's D9/ИД7 outputs 0-3 go via a resistor box, 4-7 -> CS4-CS7 rails (ROM bank
selects?) -- reconcile with our CS_D10/CS_D26.. IO-select nets (moved from 'old D2 misassign').
Check whether IO CS decode is actually D9 outs 0-6 (pins 15..9) and CS4-7 = ROM banks on the
SAME decoder or a second decode stage. Next crops: D9 outputs' destinations (right of
(2340,540)-(2800,960)); D6 V1/V2 enable source (pins 13,14 <- wires from left).
Then: rewire board.json (D8_Dx -> D6_Dx nets), flip io_dec138/rom decode HDL accordingly,
LVS+boot, commit. Then D26/X9 harvest (codes crop (2880,1800)-(3510,2880)).
FINDING 2 (crop s1_d9out.png): sheet-1 D9/ИД7 outputs = the 8 EPROM SOCKET SELECTS:
locals -> D15-D18 CS(pin 20; OE 22 tied to CS on D15) via R21-R28 1K pullups (the 8x pack we
placed at (79-98,104-112) -- physical corroboration), CS4(2) CS5(2) CS6(2) CS7(3) cross-sheet
for D19-D22. => our board.json CS_D10/CS_D26/CS_D11/CS_D27/CS_D54/CS_D55/CS_D57 nets on
D9.7-14 are POSSIBLY MISATTRIBUTED (that's 7 more outputs than the chip has left). To find:
the real IO-select decode source (D10.CS wire origin; check mid-left D105/D103 gate zone and
whether an ИД7 section or РТ4/РЕ3 output drives the peripheral CS pins). Also verify: does
BOM-x1 К555ИД7 mean sheet's ROM decoder = board D9, and IO selects come from elsewhere
(D8 РЕ3 .117? second half of something?). NEXT CROPS: D10 CS origin (trace left from D10.1);
D6 V1/V2 enable source; then D26/X9 codes harvest (2880,1800)-(3510,2880).
CHECK (crop s1_d10cs.png): D10 ВН59 IR pin row verified = our netting (25:IR7 24:IR6 23:IR5
22:IR4 18:IR0 19:IR1 21:IR3 20:IR2), D0-D7=11..4 ✓, D11 below w/ CS=11 ✓. D10.CS(pin 1) row is
just ABOVE this crop -- next crop (1450,2100)-(2050,2350) to catch the CS pin + trace the select
rail left to its source chip (candidates: D105/D103 gate pair at display~(300-330,745) =
orig ~(900-990,2235)). IO-select source still UNRESOLVED.
