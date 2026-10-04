# D30 section-B clock and output connections

Status: **OWNER CONTINUITY CLOSED / OLDER SCAN AMBIGUITY RETAINED**

Direct target-board continuity closes D30 section B's clock and output
connections. The older `.006` scan remains ambiguous at those conductors
and does not independently establish the measured `.009` routes.

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
- D30.9 is omitted from the factory symbol and remains an
  explicit no-connect. The visible section-B output is D30.8, so it cannot be
  dispositioned as an unused package half.
- Direct owner continuity remains authoritative for D30.1/.4/.10/.12/R5 and
  D105.11->D30.13; neither measured net is reopened by this older-sheet chase.

The exact `.009` sheet and direct target-board continuity agree: D30.1,
D30.4, D30.10, and D30.12 are one conductor with R5.2; R5.1 goes to
+5 V. D38.8 drives that common active-low STB conductor.

Direct owner continuity on the physical `.009` board closes both routes:
D30.11 reaches D105.2 on the D13.4/D11.20 clock conductor, and D30.8
reaches D29.7 on a conductor separate from raw IOWR.

## Model guards

| Check | Result |
| --- | --- |
| D30.11 joins the measured D13.4/D105.2/D11.20 clock conductor | PASS |
| D30.8 drives D29.7 on a dedicated measured conductor | PASS |
| D29.7 is removed from raw IOWR | PASS |
| Measured common D30 asynchronous-control and section-B D conductor is adopted | PASS |
| R5 provenance records agreement between the exact sheet and target board | PASS |
| Measured /CLR path from D105.11 is kept separate | PASS |

## Photo probe sites

The right-notched D30 2×7 package in component photo `200439607` has
D30.8/.11 on the lower row near `(875,1230)/(1040,1230)`.
In solder photo `200537608`, the corresponding lower-row joints are near
`(3040,730)/(2860,730)`. These registrations identify visual probe sites;
the independent chip-removed owner measurement proves the net continuity.
See `ref/photos/juku-pcb-2/d30-pin8-pin11-photo-registration.json` for the
image identities and registration evidence.

Run from the repository root with Python 3 (standard library only). The
generator checks board-JSON endpoints and R5 provenance, then replaces this
report after those checks pass. It reports the scan hash without comparing it
to a pinned identity. It does not reread the scan, validate photo fits, inspect
PCB copper, or repeat physical continuity measurements.

```sh
python3 scripts/report_d30_section_b_scan_chase.py
```
