# Juku 32K memory module — `ДГШ5.106.103 Э3`

Owner photographs (2026-07-18) of **ДГШ5.106.103 Э3 «Модуль ЗУ-32к / Схема
электрическая принципиальная»** — a 32K memory (ЗУ) expander card, «Введён с
15.08.88 г.».

Contents: memory array, address decoding/buffering, a РЕ3 PROM, and the
**card-edge bus connector XP** exposing
the system-bus core — address `-ADR0…-ADRF`, data `-D0…-D7`, and control
(`-MRDC`, `-IORD`, `-AMWTC`, `-ADRSTB`, `-INHIBIT`, etc.).

## Connector scope

The XP pinout records the system bus as drawn for this peripheral card. It
is comparison evidence, not a VJUGA Rev B bus specification. The
[connector cross-check](../../schematics/system-bus-connector-map.md) compares
XP with the processor connector and terminal-level interconnect drawing; the
rail conflict below prevents treating it as a compatible expansion card.

## Photos

Overview first, then detail tiles in camera order:

- `PXL_20260718_122444769.MP.jpg` — overview
- `PXL_20260718_122448921.jpg`, `PXL_20260718_122451372.MP.jpg`,
  `PXL_20260718_122454044.jpg`, `PXL_20260718_122456943.jpg` — detail tiles

## Reviewed result

The XP signal core matches processor connector X1 at every shown data,
address, and control contact. Its power map does not: the card grounds A1-A3,
where the exact `.009` processor drawing supplies +5 V. This is a documented
variant incompatibility, not a rail correction. See
`ref/schematics/system-bus-connector-map.md`.
