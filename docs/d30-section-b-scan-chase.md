# D30 section-B sheet-1 scan chase

Status: **OWNER CONTINUITY CLOSED / OLDER SCAN AMBIGUITY RETAINED**

The full-resolution `.006` electrical sheet was re-read specifically for the two
formerly unresolved D30 section-B conductors. This audit records why the scan
alone was ambiguous and how direct target-board continuity closes both routes.

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

Direct owner continuity on the physical `.009` board now closes both routes:
D30.11 reaches D105.2 on the D13.4/D11.20 clock conductor, and D30.8
reaches D29.7. The latter supersedes the prior raw-IOWR assignment at D29.7.

## Model guards

| Check | Result |
| --- | --- |
| D30.11 joins the measured D13.4/D105.2/D11.20 clock conductor | PASS |
| D30.8 drives D29.7 on a dedicated measured conductor | PASS |
| D29.7 is removed from raw IOWR | PASS |
| Measured section-B D and /PRE pull-up is kept separate | PASS |
| Measured /CLR path from D105.11 is kept separate | PASS |
