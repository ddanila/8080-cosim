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
carry the same number on sheet 1 (this matches the owner-measured pairs in
`ref/photos/juku-pcb-2/BODGE-TRIAGE.md`, e.g. wire 7 = D1.22-D35.10).

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

## Sheet 3 — Провода (wires)

Поз. 151 — shielded cable (sheet-1 note 11, ГОСТ 23585-79):

| Провод | Начало | Конец | Длина, см |
| ---: | --- | --- | ---: |
| 1 | А:3 | X6 | 12 |
| 2 | А:4 | X6⊥ (shield/body) | 12 |

Поз. 155 — on-board insulated links (sheet-1 note 10, mastic-fixed):

| Провод | Начало | Конец | Длина, см |
| ---: | --- | --- | ---: |
| 3 | А:7 | А:7 | ~24 |
| 4 | А:8 | А:8 | ~19 |
| 5 | А:9 | А:9 | ~12 |
| 6 | А:10 | А:10 | ~11.5 |
| 7 | А:11 | А:11 | ~11.5 |
| 8 | А:12 | А:12 | ~20 |
| 9 | А:13 | А:13 | ~15 |
| 10 | А:14 | А:14 | ~23 |
| 11 | А:17 | S1:1 | ~19 |
| 12 | А:18 | S1:2 | ~3 |
| 13 | А:19 | А:19 | ~9.5 |
| 14 | А:20 | А:20 | ~6 |

Rows 11 and 12 are the previously open factory wires 17 and 18: their far
ends terminate on switch `S1` pins 1 and 2. The 3 cm length of wire 12 is
consistent with board point 18 sitting in the D98 quadrant directly beside
S1 on the sheet-1 placement.

S1 is bracket-mounted, not soldered into the processor PCB. Sheet 1 draws the
pushbutton on the top connector bracket, and owner component photograph
`PXL_20260710_200402344.jpg` shows the same physical button at the upper-right
bracket edge. Consequently, `А:17` and `А:18` must become separate PCB wire
landings while S1 remains an off-board schematic/mechanical part. The validated
D98 package fit places the visible white wire-18 lead directly on D98.7, so
`А:18` is that package pad rather than a separate header pad. `А:17` remains to
be localized. The former generated two-pin S1 header was therefore removed;
S1 is retained only in the schematic and off-board harness contract.

## Sheets 4-5 — Провода to X3 and X4

Поз. 155, wires 15-26 (lengths struck and revised; original ~35, revised
value not confidently legible):

| Провод | Начало | Конец |
| ---: | --- | --- |
| 15-26 | А:21 … А:32 (in order) | X3:1 … X3:12 (in order) |

Поз. 155, wires 27-49 (same struck lengths). The начало column writes the
board points as `А Х4:n`, i.e. sheet-1 placement points labelled `X4:1` …
`X4:23` on board А:

| Провод | Начало | Конец |
| ---: | --- | --- |
| 27-40 | А Х4:1 … А Х4:14 (in order) | X4:1 … X4:14 (in order) |
| 41-49 | А Х4:15 … А Х4:23 (in order) | X4:15 … X4:23 (in order) |

So X3 (12 lines) and X4 (23 lines) are bracket-mounted connectors wired to
numbered board pads rather than board-edge-soldered; this is direct evidence
for the connector-harness geometry items in `PLAN.md`.

## Sheet 6 — Лист регистрации изменений (change registration)

Row alignment between изм. numbers, document numbers, and dates is partly
uncertain in the scan; the legible entries are:

| Изм. | № докум. | Дата |
| ---: | --- | --- |
| 2 | ДГШ19… (sheets 2-6 introduced, всего 6) | — |
| 4 | ен139546 | 14.04.89 |
| 5 | ен147074 | 25.08.89 |
| 8/9 | ен152153 | 25.10.89 / 25.07.90 |
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
landing is D98.7 itself.
