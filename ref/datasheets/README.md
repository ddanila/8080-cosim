# Local chip pinout artifacts

For every chip whose connectivity is actively reconstructed, keep:

1. the original or closest manufacturer/period datasheet PDF;
2. its SHA256 and source URL;
3. a compact `*-pinout.txt` interpretation separating datasheet facts from
   Juku board measurements.

This is the standing convention for future chip work: add the artifacts when
the chip first becomes an active modeling or continuity-tracing subject, rather
than attempting an all-components datasheet import up front.

Current artifacts:

| Board chip | Device | PDF | Text interpretation |
| --- | --- | --- | --- |
| D104 | К170УП2 | `k170up2.pdf` | `k170up2-pinout.txt` |
| D94 | К155РЕ3 / SN74188-compatible | `sn74188-ti.pdf` | `k155re3-pinout.txt` |
| D93 | КР1818ВГ93 / FD179X family | `../wd1772-vg93/fd179x-01-datasheet.pdf` | `kr1818vg93-pinout.txt` |
| D27 | КР580ВВ55 / Intel 8255A | `intel-p8255a.pdf` | `kr580vv55-pinout.txt` |
| D29 | КР580ВА86 / Intel 8286 | `kr580va86.pdf` | `kr580va86-pinout.txt` |
| D101 | К555КП12 / SN74LS253 | `sn74ls253-ti.pdf` | `k555kp12-pinout.txt` |

Checksums:

```text
0094e9959ca825ea89c3b2a2e7b015a276be563e9f66ef1c2d9d3fe4b31635e6  k170up2.pdf
7d677a198664fe580e11d53f69a436f3d4e1bdf7f9a6bfb7c7acea386658a0db  sn74188-ti.pdf
e51aef0933d88e7705f6f774ffb3238e8e8096bd9b9d774a985d95ef5766e3ce  ../wd1772-vg93/fd179x-01-datasheet.pdf
f4efbeaaed2e19158e67640683407ac0dfd557ff29ef20a702532fddab2ceeef  intel-p8255a.pdf
44f3c77489e36b015038b8fdde724aa844e2252e554be8158531f6f1e01a614c  kr580va86.pdf
6dac6d83b154c40e39bf772ae3b144c8d5d7a42f7b31ddc49942223d6df6c47a  sn74ls253-ti.pdf
```

Sources:

- К170УП2 PDF: `https://www.km-cs.com/datasheet/_Other/k170up2.pdf`
- SN74188 Texas Instruments scan: `https://www.radioradar.net/en/files.html?fid=500816`
- FD179X PDF provenance is recorded in `../wd1772-vg93/README.md`.
- Intel P8255A scan: `https://datasheet4u.com/pdf/511194/P8255A.pdf`
- КР580ВА86/8286 scan: `https://datasheet4u.com/pdf/1529844/KR580VA86.pdf`
- SN74LS253 Texas Instruments PDF: `https://www.ti.com/lit/ds/symlink/sn54ls253.pdf`
