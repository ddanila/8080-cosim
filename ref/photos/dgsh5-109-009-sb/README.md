# ДГШ5.109.009 СБ assembly-drawing photos

This directory contains 26 owner-supplied photographs of the original Baltijets
factory assembly drawing `ДГШ5.109.009 СБ` («Модуль процессора. Сборочный
чертёж», scale 2:1, лист 1 из 6, разраб. Петров). The sheet was photographed
folded, in overlapping sections; there is no single full-sheet shot, but the
set together covers the whole drawing. The board outline carries the same
`7.102.158` marking as the owner board photographed in
`ref/photos/juku-pcb-2/`.

The JPEGs are Git LFS objects. Run `git lfs pull` after cloning; pointer stubs
do not count as available visual evidence, and `sync/reference_artifact_check.sh`
rejects them.

What the drawing is authoritative for:

- Factory component placement and refdes positions (D/R/C/VT/VD/E designators,
  DRAM row D84–D91, PROM/logic rows), with note 6 stating positional
  designators follow `ДГШ5.109.009 Э3`.
- Edge-connector and cable positions `X1`–`X9`, `S1`, and the off-board cable
  assemblies (X8 lead 300 mm, X9 ribbon 400 mm, poz. 151 shielded cable).
- Per-component mounting details («Установка VT1/VT2/Z1/C73/C98,C100»).
- Factory local solder/copper details («Разрезать», «Вид В», «сторона монтажа»)
  around D56, D15, D14, and D11. Only D15 explicitly says «Разрезать»; note 11
  identifies position 150 as tubing fitted at solder locations, not a cut.
  The D15, D14, and D11 labels were verified
  against same-hand glyph references (Д15/Д16 socket labels, callouts
  150/159, Д56) at full photo resolution.
  Owner-board registration now closes D15's A2/A1 cut and D14's local
  D32.4/GND-to-D14.1 link and registers D14's fifth auxiliary landing; its
  conductor, the other D14 traces, and the D56/D11 details remain
  measurement-held. The D14 right-row dogleg is photo-exhausted across both
  component and reflected solder views and requires continuity. At D56 the
  three-leader level registers to D56.12/D56.5,
  but no net change is inferred. At D11, the unique L trace and four
  position-159 solder locations
  are registered in two component views; the earlier pins-4–6 solder scar is a
  different feature. Validated component and reflected package fits project the
  four landmarks into four overlapping solder views, but the upper location is
  rail-obscured and the lower three have no unique four-hole match; the photos
  are exhausted and direct continuity is required.
- Technical requirements 1–14 (ОСТ4.010.030-81 placement variants, ПОС61
  solder, marking, cable dressing, Z1 mounting on лакоткань/ВК-9).
- Revision history: change-table rows `ен147279`, `ен147160`, `ен147074`,
  `ен139546`, `ен164807`, `ен157459`, `ен157937` with dates and signatures
  (`ен147074` corrected from an earlier `ен47074` reading against the sheet-6
  registration list).

Sheets 2-6 of this document (the таблица соединений referenced by note 8 and
the change-registration sheet) were acquired on 2026-07-11 as an owner
«ДУБЛИКАТ» scan: `ref/schematics/dgsh5_109_009_sb_sheets2-6.pdf`, transcribed
in `ref/schematics/dgsh5-109-009-sb-wire-table.md`.

Photo index (`PXL_20260711_*`):

| Photo | Content |
| --- | --- |
| `114553710` | Upper-left placement: `X1`, rows `D23`–`D25`/`D29`, `D15`/`D16` sockets, `E71`, `D5`–`D9` row |
| `114556899` | Top-centre placement: `X2`, `X3`, `D27`, `D11`, `D94`, `D10`, 310 mm reference dimension |
| `114600417` | Top-right placement: `X4`, `X6`, `S1`, `D93`–`D102` region, `C17`/`C18`, `VT2`, `VD3` |
| `114604420` | Left placement: `D1`, `D4`, `D107`, `D30`, `D13`, `D105`, `C31`–`C33`, power terminal block |
| `114607591` | Centre placement: `D33`–`D57` region, `C100`, `D26`/`D54`, `X9` exit |
| `114611058` | Lower-left: `C31`–`C33`/`C93`, `X8` cable exit (300 mm), «Установка VT1», «Установка Z1» |
| `114615300` | Centre: `7.102.158` outline marking, DRAM row `D84`–`D91`, `D50`/`D51`, `C38`–`C50` row |
| `114617677` | Lower-centre: `Z1`, `D59`, `D42`/`D43`/`D58`, `C98`, «Установка VT2» |
| `114620466` | Lower-right: `D26`/`D54`/`D55`, `E8` wire fan, `X9` ribbon detail, «Установка C73/C98,C100» |
| `114626340` | «Вид В» solder-side detail: trace cuts at `D56`, patches at `D15`/`D14`/`D11` |
| `114633498` | Enlarged «Разрезать» cut detail at `D15` |
| `114638730.MP` | «Вид В» full detail, callouts 150/159, «сторона монтажа» |
| `114649169` | Technical requirements, items 1–14 |
| `114655078` | Title block: `ДГШ5.109.009 СБ`, «Модуль процессора. Сборочный чертёж», 2:1, лист 1/6, signatures |
| `114700250` | Revision/change table close-up (`ен…` rows, dates) |
| `114703874` | «Установка C98, C100» detail (25 mm) |
| `114706095` | «Установка C73» detail (1.0+0.5 mm) |
| `114708501` | «Установка VT2» detail (3±0.5 mm) |
| `114711315` | «Установка Z1» detail |
| `114714031` | «Установка VT1» detail (2.5/5/7.4 mm) |
| `114718331` | `X8` power-cable termination detail (300 mm, poz. 152/157) |
| `114721647` | `X9` ribbon termination detail (400 mm, poz. 140/153/156/158) |
| `114725830` | Folded bottom-right corner stamp `ДГШ5.109.009 СБ` |
| `114731214` | Board edge profile with connectors, 280.5 mm reference dimension |
| `114734104` | «Вид Б» connector-mounting cross-section |
| `114740861` | Edge-profile section, poz. 149 hardware |

The drawing shows factory-intended assembly, including the documented trace
cuts; it does not capture the copper artwork itself, so it complements rather
than replaces the `ref/schematics/` sheets and the `juku-pcb-2` board photos.

`factory-wire-landing-registration.json` records reviewed repeated `А:N`
wire endpoints in original-image pixels. Image-space registration is kept
separate from board millimetres and copper-island assignment; unset fields are
an explicit hold, not permission to infer geometry from the folded sheet.

`factory-modification-registration.json` cross-registers the D15 cut detail
with two independent component photographs and one reflected solder view. It
closes the A2/A1 net partition while explicitly withholding the auxiliary-hole
centres from fabrication use.
