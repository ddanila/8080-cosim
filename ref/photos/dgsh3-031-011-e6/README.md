# Juku terminal — system general schematic `ДГШ3.031.011 Э6`

Owner photographs (2026-07-18) of **ДГШ3.031.011 Э6 «Схема электрическая
общая»** for the intelligent editorial-system terminal (ИТСРВ), showing how the
subsystems interconnect. This is the top-level block/interconnect drawing (Э6 =
general schematic), not a component-level one.

## Why this matters

It enumerates the **inter-module connectors X1–X6** and which unit lands on
each — the map for cross-checking every card-edge / cable connector against the
individual module schematics. Useful for the bus-connector reconciliation.

Referenced units (with their own drawing numbers):

| Ref | Unit | Drawing |
| --- | --- | --- |
| A1 | Интеллектуальный пульт оператора Е5101 | `ДГШ3.031.007` |
| A2.1 | Устройство управления клавиатурой Е4701 | `ДГШ3.049.040` |
| A2.2 | Сменный расширитель памяти Е6201 | `ДГШ5.106.102` |
| A3 | Устройство печатающее | СМ6329.02 / К6312М |
| A4 | Блок НГМД Е6502 | `ДГШ3.065.008` → `ref/photos/dgsh3-065-008-e3/` |
| A5 | Устройство отображения | МС6105.09 |

The main processor board itself is `ДГШ3.031.007` (A1's internals include the
`ДГШ5.109.009` module documented under `ref/photos/dgsh5-109-009-e3/`).

## Photos

Overview first, then detail tiles in camera order:

- `PXL_20260718_121242143.jpg` — overview
- `PXL_20260718_121246801.jpg`, `PXL_20260718_121250335.jpg` — detail tiles

## Reviewed result

The complete block/cable map is transcribed in
`ref/schematics/system-bus-connector-map.md`: A1/X1 selects the alternative
A2.1 or A2.2 module, while X2, X4, and X6 reach the printer, НГМД block, and
display respectively. X3 contact 12 belongs to the mains/switch harness; the
drawing shows no X5 signal cable.
