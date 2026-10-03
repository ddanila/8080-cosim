# Juku keyboard module — `ДГШ5.104.015 Э3`

Owner photographs (2026-07-18) of **ДГШ5.104.015 Э3 «Модуль клавиатуры /
Схема электрическая принципиальная»**, «Введён с 15.08.88 г.».

The drawing contains the switch matrix, separate SHIFT/CTRL contacts,
D1/D2 row-encoding logic, scan decoders and the eight-position S21
configuration bank. X1 carries `K0–K2`, `SC0–SC3`, active-low `-FK`,
SHIFT/CTRL, serialized `CONTRDAT`, +5 V and ground.

The [guarded transcription](../../../docs/factory-keyboard-matrix.md)
records all 70 fitted matrix positions and X1 pins, the factory-line-to-model
column offset and the non-binary row encoding. Its generator checks the
photo hashes and cosim ASCII mapping tuples; it does not verify physical
continuity or complete host-byte coverage of every national/mode contact.

The archived `ekta37.bin` configuration scan reads PB5, while the photographed
`.009` E8 3–4 bridge selects PB4. The model preserves the ROM's PB5 profile;
physical S21 operation on this board revision remains unverified. See the
[NetBios notes](../../../docs/ekta37-netbios-notes.md).

## Photos

Overview first, then detail tiles in camera order:

- `PXL_20260718_122207428.jpg` — overview
- `PXL_20260718_122210592.jpg`, `PXL_20260718_122213927.jpg` — detail tiles
