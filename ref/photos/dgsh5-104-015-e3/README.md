# Juku keyboard module — `ДГШ5.104.015 Э3`

Owner photographs (2026-07-18) of **ДГШ5.104.015 Э3 «Модуль клавиатуры /
Схема электрическая принципиальная»**, «Введён с 15.08.88 г.».

Contents: the key switch matrix (S11…S94 plus function/control keys —
CTRL, SHIFT, CAPS LOCK, TAB, RETURN, DEL, ESC, LAT/RUS, F1–F8, etc.), a diode
matrix, ЛА7 decoders (D1/D2), scan/return lines to connector **X1** (KO/K1/K2,
SC0–SC3, −FK, CONTRAST, POWER +5 V). Useful for validating keyboard-controller
behavior and the X1 pinout against the system schematic
(`ref/photos/dgsh3-031-011-e6/`).

The guarded transcription and model comparison are in
`docs/factory-keyboard-matrix.md`.  They fix the factory-line-to-model-column
offset, the non-binary row encoding, all 70 fitted matrix positions, X1 pins,
and the exact ASCII tuples consumed by the cosim keyboard injector.

## Photos

Overview first, then detail tiles in camera order:

- `PXL_20260718_122207428.jpg` — overview
- `PXL_20260718_122210592.jpg`, `PXL_20260718_122213927.jpg` — detail tiles
