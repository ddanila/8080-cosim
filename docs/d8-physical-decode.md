# D8 `.039` physical ROM-pager decode

Status: **PHYSICAL D8 TABLE MINIMIZED AND EXECUTED**

This generated report reduces the validated 32 x 8 К155РЕ3 image to
exact active-low socket-select equations and guards them against every
captured bit. `S(Dn)=1` means output Dn sinks its open-collector rail.

## Artifact and mapping

- Raw image: `ref/physical-proms/validated/d8_039.raw.bin`
- SHA256: `345b67e66562741dd48e70f30e7862d4e3fc19d3a113f21c999d6ec497af59cc`
- Address mapping: `A4..A0 = BA15..BA11`.
- Enable: D8.15 `/E` is the measured D6.12 `ROM_SEL` conductor.

## Exact minimized equations

Define `Q = (BA15 == BA14)`. Exhaustive comparison of all 32 rows and
all 256 output bits gives:

| Output | Exact asserted equation | Meaning |
| --- | --- | --- |
| `S(D4)` | `Q & !BA13` | select populated BIOS-low socket D15 |
| `S(D5)` | `Q & BA13` | select populated BIOS-high socket D16 |
| `S(D0..D3,D6,D7)` | `0` | always released |

BA12 and BA11 are complete don't-cares. D4 and D5 are mutually exclusive;
when `Q` is false every output releases. D6's separate `ROM_SEL` enable
provides the mode/region qualifier around this address-only pager.

## Physical output destinations

| Pin | Output | Board destination | Asserted rows | Net guard |
| ---: | --- | --- | --- | --- |
| 1 | `D0` | `ROM_CS_A000` -> `D19` | never | PASS |
| 2 | `D1` | `ROM_CS_8000` -> `D20` | never | PASS |
| 3 | `D2` | `ROM_CS_6000` -> `D21` | never | PASS |
| 4 | `D3` | `ROM_CS_4000` -> `D22` | never | PASS |
| 5 | `D4` | `ROM_CS_D15` -> `D15` | 00, 01, 02, 03, 24, 25, 26, 27 | PASS |
| 6 | `D5` | `ROM_CS_D16` -> `D16` | 04, 05, 06, 07, 28, 29, 30, 31 | PASS |
| 7 | `D6` | `ROM_CS_EXP17` -> `D17` | never | PASS |
| 9 | `D7` | `ROM_CS_EXP18` -> `D18` | never | PASS |

The six invariant outputs remain physical fidelity obligations: their copper
to D17-D22 is preserved even though this factory program never selects those
sockets. The `.009` populated build uses only D15 and D16.

## Evidence checks

| Check | Result |
| --- | --- |
| Board identity is D8 `.039` | PASS |
| All five address inputs map to BA11..BA15 | PASS |
| Enable maps to measured D6.12 ROM select | PASS |
| All eight output-to-socket nets are present | PASS |
| All 256 captured bits match the equations | PASS |
| HDL executes open-collector table and release checks | PASS |

## Remaining boundary

D8 content, address equations, output activity, and socket destinations are
closed. Full physical adoption still follows D6: its `/E` source is measured
to D6.12, but the runnable D6 D0 polarity fit awaits the corrected re-read or
operating-level probe. No replacement D8 firmware remains to reconstruct.
