# ДГШ5.109.009 СБ sheets 2-6 — wire/cable connection table

Source: `dgsh5_109_009_sb_sheets2-6.pdf`, SHA256
`779bca02a2b7d0aba9b170b39ab55ff5f980d06f3f324fd91958ece646ddfc2b`,
owner-supplied scan acquired 2026-07-11. The pages carry a «ДУБЛИКАТ» stamp,
duplicate inventory number `35661`, and a 13.04.89 signature date. They are
sheets 2-5 (таблица соединений) and sheet 6 (лист регистрации изменений) of
the same `ДГШ5.109.009 СБ` document whose sheet 1 is photographed in
`ref/photos/dgsh5-109-009-sb/`.

Reading convention (sheet-1 note 8): the processor board (плата, поз. 17) is
designated by the letter **А** in this table. `А:N` therefore means the board
point labelled `N` on the sheet-1 placement drawing. Rows whose начало and
конец are both `А:N` are the numbered on-board wire links: both solder points
carry the same point number on sheet 1. The leftmost `Провод` value is the
conductor's position within assembly item 155; it is **not** the board-point
number. For example, conductor position 3 joins the two points labelled
`А:7`, which owner continuity maps to D1.22-D35.10.

This file is a human transcription for review convenience; the scan is the
evidence. Lengths were revised in ink on the original (struck and rewritten);
the value given is the latest legible one, marked `~` where the strike-overs
make the reading uncertain. Connection columns are legible throughout.

## Sheet 2 — Кабели (cables)

Поз. 152 — X8 power cable, 6 conductors, all 30 cm:

| Провод | Начало | Конец |
| ---: | --- | --- |
| 1 | А:59 | X8:8 |
| 2 | А:60 | X8:3 |
| 3 | А:61 | X8:6 |
| 4 | А:61 | X8:2 |
| 5 | А:62 | X8:5 |
| 6 | А:62 | X8:1 |

This X8 cable is now promoted as four physical one-pad PCB landings `A59`..
`A62` plus a schematic-only bracket connector. The harness nets preserve the
single -12 V and +12 V conductors and both duplicated +5 V/GND conductors:
A59->X8.8, A60->X8.3, A61->X8.6/X8.2, and A62->X8.5/X8.1.

Поз. 153 — X9 ribbon cable, 14 conductors, all 30 cm, reversed pin order:

| Провод | Начало | Конец |
| ---: | --- | --- |
| 1 | А:45 | X9:14 |
| 2 | А:46 | X9:13 |
| 3 | А:47 | X9:12 |
| 4 | А:48 | X9:11 |
| 5 | А:49 | X9:10 |
| 6 | А:50 | X9:9 |
| 7 | А:51 | X9:8 |
| 8 | А:52 | X9:7 |
| 9 | А:53 | X9:6 |
| 10 | А:54 | X9:5 |
| 11 | А:55 | X9:4 |
| 12 | А:56 | X9:3 |
| 13 | А:57 | X9:2 |
| 14 | А:58 | X9:1 |

Position 6 directly proves `А:50` to `X9:9`. The exact `.009 Э3` sheet-1
E8.4 `CONTRDAT` continuation is marked `909`, so these two drawings close the
factory connector destination for the fitted E8 3–4 bridge. The owner-photo
15-site solder band still lacks a unique A50 hole assignment; its tentative
site-6 waypoint is recorded in
`ref/photos/juku-pcb-2/e8-bridge-photo-review.json`.

Native page 1 shows exactly these fourteen position-153 rows, each marked
30 cm. The table identifies numbered board points and connector contacts;
it does not name their electrical signals. Keyboard/control/+5 V signal
names come from the separate `.009` schematic reconstruction and board
model. In particular, the table itself cannot identify or exclude the
additional owner-board solder-band site now under review beside D26.

## Sheet 3 — Провода (wires)

Поз. 151 — shielded cable (sheet-1 note 11, ГОСТ 23585-79):

| Провод | Начало | Конец | Длина, см |
| ---: | --- | --- | ---: |
| 1 | А:3 | X6 | 12 |
| 2 | А:4 | X6⊥ (marked return terminal) | 12 |

The suffix mark is transcribed literally rather than treated as polarity evidence
by itself. The system cable map (`ДГШ3.031.011 Э6`) identifies X6 as the
two-conductor display connection. Exact `.009 Э3` sheet 2 labels output contact
3 VIDEO and contact 4 ground. The owner photo places the `А:3` cable joint
beside VT2, separate from VD3.2; its copper path to the output stage still
requires continuity confirmation. The separately insulated `А:4` return appears
to terminate on the wide ground strip. See
`ref/photos/juku-pcb-2/x6-cable-registration.json` and
`docs/x6-a3-video-source-conflict-review.md`.

Поз. 155 — on-board insulated links (sheet-1 note 10, mastic-fixed):

| Провод | Начало | Конец | Длина, см |
| ---: | --- | --- | ---: |
| 3 | А:7 | А:7 | ~24 |
| 4 | А:8 | А:8 | ~19 |
| 5 | А:9 | А:9 | ~12 |
| 6 | А:10 | А:10 | 13.5 |
| 7 | А:11 | А:11 | ~11.5 |
| 8 | А:12 | А:12 | ~20 |
| 9 | А:13 | А:13 | ~15 |
| 10 | А:14 | А:14 | ~23 |
| 11 | А:17 | S1:1 | ~19 |
| 12 | А:18 | S1:2 | ~3 |
| 13 | А:19 | А:19 | ~9.5 |
| 14 | А:20 | А:20 | ~6 |

The final handwritten values in all twelve rows above were checked against
the full 300 dpi rendering of PDF page 2 (printed sheet 3). Several cells
contain crossed-out earlier numbers; the table transcribes the surviving
number in each cell, not the crossed revision history. In particular, A9
ends at `12`, A10 at `13,5`, A11 at `11,5`, A12 at `20`, A13 at `15`,
and A14 at `23` cm.

The duplicate's conductor-6 length cell has an earlier value crossed out and
`13,5` written as the final value. The two-sided photo fit independently gives
a 131.355 mm straight A10 terminal chord, consistent with a 13.5 cm insulated
lead and impossible for the former tentative `~11.5` transcription.

For conductor 4/A8, a 300 dpi re-read of PDF page 2 (printed sheet 3) confirms
that the length cell has `20` crossed out and `19` written below it. Thus the
revised table value really is 19 cm. The two locally fitted surface terminals
have a 195.9 mm straight chord, already 5.9 mm longer than that value before
allowing for routing or stripped ends. Each landing has direct copper to its
owner-confirmed package pin, so the endpoint geometry is retained. The source
value cannot be used as an assembly cut length; measure the installed lead or
resolve the discrepancy against a physical original before fabrication.

The same re-read confirms conductor 7/A11 has an earlier value crossed out
with `11,5` written below. The crossed value is not reliably legible in this
scan. Its final table value is therefore 11.5 cm, despite the
119.177 mm fitted terminal chord. As with A8, this revised table value is
shorter than the straight span and must not be used to cut the replacement
wire until the installed lead or physical original has been checked.

All ten on-board link rows are now mapped to electrical endpoints. The owner
read for `А:20` was made through the installed X3 cable, so the table below
shows the intervening photographed PCB landing A23 as well as remote X3.3.
Full-resolution sheet 1 places its short diagonal beside D104 and D3/R18; the
vertical designator is `Д104`, not `Д14`, so it does not support moving the
link onto the separate D14.3/D3.11 `SER_TXD` net. These links are insulated
assembly wire, not replacement PCB etch.

| Conductor position | Board point | Guarded endpoints | Net |
| ---: | ---: | --- | --- |
| 3 | А:7 | D1.22 - D35.10 | `PHI1` |
| 4 | А:8 | D5.1 - D38.8 | `STSTB` |
| 5 | А:9 | D1.19 - D38.12 | `SYNC` |
| 6 | А:10 | D41.13 - D50.1 | `W10_QA_SEL` |
| 7 | А:11 | D7.1 - D92.13 | `MEMR` |
| 8 | А:12 | D13.2 - D37.4 | `RAM_OUT_EN` |
| 9 | А:13 | D13.1 - D92.1 | `ROE` |
| 10 | А:14 | D1.15 - D35.12 | `PHI2` |
| 13 | А:19 | D5.26 - D7.2 | `MEMW` |
| 14 | А:20 | D3.10 - A23.1 - X3.3 | `S_TTL` |

`kicad/check_factory_wire_links.py` guards these mappings against the
authoritative board model. The mapping does not authorize a routed-copper
substitution: the final assembly output must retain these as insulated links.

Rows 11 and 12 are the previously open factory links at board points 17 and
18: their far ends terminate on switch `S1` pins 1 and 2. The 3 cm length of
conductor 12 is
consistent with board point 18 sitting in the D98 quadrant directly beside
S1 on the sheet-1 placement.

S1 is bracket-mounted, not soldered into the processor PCB. Sheet 1 draws the
pushbutton on the top connector bracket, and owner component photograph
`PXL_20260710_200402344.jpg` shows the same physical button at the upper-right
bracket edge. Consequently, `А:17` and `А:18` must become separate PCB wire
landings while S1 remains an off-board schematic/mechanical part. The validated
D98 package fit places the visible white wire-18 lead directly on D98.7, so
`А:18` is that package pad rather than a separate header pad. Two-sided owner
photos identify `А:17` as the dedicated pad
printed `17`, at approximately `(115.8,27.1)` mm. The former generated two-pin
S1 header was therefore removed; S1 is retained only in the schematic and
off-board harness contract, while `A17` is a one-pad PCB footprint.

## Sheets 4-5 — Провода to X3 and X4

Поз. 155, wires 15-26: the repeated length cells read an earlier `3,5`
crossed out and a final `4,5` cm written below. The decimal comma is visible
on the full-resolution scan; these are centimetres, not 35/45 cm.

| Провод | Начало | Конец |
| ---: | --- | --- |
| 15-26 | А:21 … А:32 (in order) | X3:1 … X3:12 (in order) |

Поз. 155, wires 27-49 (the same repeated `3,5` to `4,5` cm revision on
both continuation sheets). The начало column writes the
board points as `А Х4:n`, i.e. sheet-1 placement points labelled `X4:1` …
`X4:23` on board А:

| Провод | Начало | Конец |
| ---: | --- | --- |
| 27-40 | А Х4:1 … А Х4:14 (in order) | X4:1 … X4:14 (in order) |
| 41-49 | А Х4:15 … А Х4:23 (in order) | X4:15 … X4:23 (in order) |

So X3 (12 lines) and X4 (23 lines) are bracket-mounted connectors wired to
numbered board pads rather than board-edge-soldered; this is direct evidence
for the connector-harness geometry items in `PLAN.md`.

The older `.006` electrical sheet provides a partial circuit cross-reference
for five X4 contacts through its explicit exit codes. The open-collector
К155ЛН3 D28 outputs are drawn as follows:

| X4 contact / exit code | Signal | `.006` source pin |
| ---: | --- | --- |
| 1 / 401 | `-FF` | D28.8 |
| 2 / 402 | `-REC` | D28.10 |
| 3 / 403 | `-PLAY` | D28.12 |
| 4 / 404 | `-RN` | D28.4 |
| 5 / 405 | `-STOP` | D28.2 |

The `.009` cable table promotes all 23 board-edge landings and their direct
wires to the bracket connector. The first five circuit-side paths are retained
as cross-revision, owner-verify nets because D28 is present in the FDC-era
population and MAME independently assigns the same Port-C functions; actual
`.009` D28-to-landing copper must still confirm they were not reassigned.
X4.6-X4.23 are promoted only as landing-to-connector harness nets: their
on-board circuit destinations remain explicit boundaries.

The X9 row is now promoted without changing its already traced keyboard nets:
the source PCB contains fourteen one-pad `A45` through `A58` placeholders,
and the off-board X9 connector remains schematic-only. Each net contains its
D26 endpoint, numbered A:N landing, and reversed X9 pin; A53/A54 carry the
two +5 V conductors. The placeholder pad coordinates are not photo-registered:
owner solder photos locate a candidate fourteen-site cable row beneath D26,
farther right than the model. One site near (2505,2375) joins the photographed
D26.26/+5 V rail, but its A53/A54 number and the other slots' A numbers are
open. The evidence is in `ref/photos/juku-pcb-2/x9-solder-row-registration.json`
and `ref/photos/juku-pcb-2/x9-plus5-rail-site-review.json`.

X3 is now promoted as the photographed single-row `A21`..`A32` PCB landings
feeding schematic-only connector pins 1..12. The older `.006` schematic closes
A23/TTL SOUT, A24/SIN, A25/CTS, A26/DSR, A29/SOUT, A30/RTS, A31/DTP, and
A32/OC SOUT; the `.009` table supplies the connector-pin mapping. Sheet 1 and
the registered component photo additionally close A21 through R101 120 ohms
to +5 V. Junction dots on the same source sheet tie A22/X3.2 directly to the
OC SOUT node shared by A32/X3.12 and D12.3. The identified A27/A28 solder
joints have no PCB-copper departure and the older circuit sheet omits both;
their installed wires to X3.7/.8 are therefore recorded as intentional
cable-only reserved contacts. The former provisional 2x8 on-board X3 body is
removed.

The adjacent source-drawn OC SOUT network is now complete as well: R18 33k
returns `S_OC` to `SER_TXD`/D3.11, and R30 33k biases `S_OC` to ground.
Assembly and owner photos identify and fit both physical resistor bodies.
SER_TXD also feeds D3.9; D3.8 drives the tied D12.1/.2 inputs, restoring the
source-drawn pre-inverter rather than a direct behavioral shortcut.

## Sheet 6 — Лист регистрации изменений (change registration)

The full-resolution page-5 re-read separates the handwritten revision rows.
The list places revision 9 above revision 8; the document number and date
columns should be read on those same horizontal lines. Revision 5 has a date
but no legible document number, and the 1994 document row has no revision
number entered.

| Изм. | № докум. | Дата |
| ---: | --- | --- |
| 2 | ДГШ19… (sheets 2-6 introduced, всего 6) | — |
| 4 | ен139546 | 14.04.89 |
| 5 | — | 25.08.89 |
| 9 | ен147074 | 25.10.89 |
| 8 | ен152153 | 25.07.90 |
| 10 | ен151937 | 14.05.90 |
| 11 | ен157459 | 07.06.91 |
| — | ен164807 | 05.12.94 |

The `ен` numbers overlap the sheet-1 title-block change table
(`ref/photos/dgsh5-109-009-sb/`), cross-dating the `.009`-era revisions from
1989 through 1994.

## Promotion boundary

These rows document factory intent for the off-board harness and the
numbered wire links. Before board-model promotion, each `А:N` point must be
mapped to a package pin via the sheet-1 placement plus owner continuity;
the table gives point numbers, not pin numbers. In particular, do not route a
single on-board S1 footprint: first model the physically separate `А:17` and
`А:18` wire landings and their proved local copper. For wire 18, the proved
landing is D98.7 itself; for wire 17, it is the dedicated `A17` pad.
The X3, X4, X8, and X9 cables are promoted as physical numbered landings plus
schematic-only bracket connectors. X4 contacts 1-5 carry the guarded `.006`
D28.8/.10/.12/.4/.2 cross-revision reconstruction; contacts 6-23 stop at
explicit board-side boundaries until their circuit destinations are traced.
These are not claims of target-board copper proof.
