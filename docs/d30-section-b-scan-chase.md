# D30 section-B sheet-1 scan chase

Status: **SCAN EXHAUSTED / OWNER CONTINUITY REQUIRED**

The full-resolution `.006` electrical sheet was re-read specifically for the two
remaining D30 section-B conductors. This audit records what the scan proves and
why it does not justify a target-board net merge.

## Source

- Image: `ref/schematics/p3_sheet1.png`
- SHA256: `dd9eb45a8b9a6af5bbaf4677939f4b2db49661c1a536a07009e0fce9afa1bf53`
- Full image: `5150 x 3603` pixels
- Primary inspection box: `x=950..2850, y=1200..2150`
- West clock continuation box: `x=0..1700, y=1350..2100`

## Result

- D30.11 has a drawn westbound clock conductor. It crosses the vertical
  D13.4/WR:19 route in the crowded gate field without a junction dot; the scan
  therefore does not prove D30.11 on `D13_4_D105_2`, `D105_3`, or `WR:19`.
- D30.8 has a drawn east/north departure. It traverses the dense memory/data
  rail field, but no unique labeled destination or unambiguous junction survives
  in this scan. Apparent alignment with a bus rail is not evidence for tying a
  push-pull 7474 output to that bus.
- D30.9 is omitted from the factory symbol and remains the already-recorded
  explicit no-connect. The visible section-B output is D30.8, so it cannot be
  dispositioned as an unused package half.
- Direct owner continuity remains authoritative for D30.10/.12/R5 and
  D105.11->D30.13; neither measured net is reopened by this older-sheet chase.

The safe closure is a continuity measurement from D30.11 and D30.8 on the
physical `.009` board. Until then both singleton boundary nets are intentional.

## Model guards

| Check | Result |
| --- | --- |
| D30.11 remains a singleton clock boundary | PASS |
| D30.8 remains a singleton inverted-output boundary | PASS |
| Measured section-B D and /PRE pull-up is kept separate | PASS |
| Measured /CLR path from D105.11 is kept separate | PASS |
