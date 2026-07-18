# Juku 32K memory module — `ДГШ5.106.103 Э3`

Owner photographs (2026-07-18) of **ДГШ5.106.103 Э3 «Модуль ЗУ-32к / Схема
электрическая принципиальная»** — a 32K memory (ЗУ) expander card, «Введён с
15.08.88 г.».

Contents: К565РУ-family DRAM/SRAM array with К555-series address decoders/latches
(РА3/РА13/555 buffers), a РЕ3 ROM, and the **card-edge bus connector XP** exposing
the full system bus — address `-ADR0…-ADR17`, data `-D0…-D7`, and control
(`-MRDC`, `-IORD`, `-AMWTC`, `-ADRSTB`, `-INHIBIT`, etc.).

## Why this matters

The XP pinout here is the **system-bus (backplane) connector** as seen by a
peripheral card — directly relevant to the bus-connector cross-check and to the
rev-B RC2014-style backplane work (`spinoffs/minimal-vga`). Reconcile XP against
the processor board's bus connector and the system schematic
(`ref/photos/dgsh3-031-011-e6/`).

## Photos

Overview first, then detail tiles in camera order:

- `PXL_20260718_122444769.MP.jpg` — overview
- `PXL_20260718_122448921.jpg`, `PXL_20260718_122451372.MP.jpg`,
  `PXL_20260718_122454044.jpg`, `PXL_20260718_122456943.jpg` — detail tiles
