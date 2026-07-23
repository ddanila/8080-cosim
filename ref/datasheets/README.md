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
| D99 | К155АГ3 / SN74123-compatible | `sn74ls123-ti.pdf` | `k155ag3-pinout.txt` |
| D96 | КМ555ТМ2 / SN74LS74A-compatible | `sn74ls74a-ti.pdf` | `k555tm2-pinout.txt` |
| D84-D91 | К565РУ5Г / 4164-class 64Kx1 DRAM | `mk4564-64kx1-dram.pdf` | `k565ru5-pinout.txt` |
| D2, D6 | К556РТ4 / 82S126 256x4 OC PROM | `82s126-556rt4-256x4-oc-prom.pdf` | `k556rt4-pinout.txt` |
| D34 | К555ЛП5, with SN74LS86A current-condition comparison | `k555lp5-eandc.pdf`, `sn74ls86a-ti.pdf` | `k555lp5-output-reference.txt` |
| VT2 | КТ315Б, old KT-13 package | `kt315-family-promelec.pdf` | `kt315b-output-reference.txt` |
| D53 | КР531ИД7, with SN54S138 primary compatible-device timing comparison | `sn54s138-ti.pdf` | `kr531id7-timing-reference.txt` |
| VJUGA Rev-A J3 | HRO TYPE-C-31-M-17 USB-C receptacle | `hro-type-c-31-m-17.pdf` | `hro-type-c-31-m-17-footprint.txt` |

Checksums:

```text
0094e9959ca825ea89c3b2a2e7b015a276be563e9f66ef1c2d9d3fe4b31635e6  k170up2.pdf
7d677a198664fe580e11d53f69a436f3d4e1bdf7f9a6bfb7c7acea386658a0db  sn74188-ti.pdf
e51aef0933d88e7705f6f774ffb3238e8e8096bd9b9d774a985d95ef5766e3ce  ../wd1772-vg93/fd179x-01-datasheet.pdf
f4efbeaaed2e19158e67640683407ac0dfd557ff29ef20a702532fddab2ceeef  intel-p8255a.pdf
44f3c77489e36b015038b8fdde724aa844e2252e554be8158531f6f1e01a614c  kr580va86.pdf
6dac6d83b154c40e39bf772ae3b144c8d5d7a42f7b31ddc49942223d6df6c47a  sn74ls253-ti.pdf
abe37431fa9098d0230544c83e4490cc3e788f6be92ef23e99124047f2b59707  sn74ls123-ti.pdf
d162b65235d894394a5438eef01cc890b0a95b38d3cdd1931eb8c5ed532c697d  sn74ls74a-ti.pdf
8a6169963c020c1ff8b3c413356ed8f354b9963b77dab8f9bd2af22560c44093  mk4564-64kx1-dram.pdf
63938c06d5c4645aaa462bb8c87dd8555f324056a64fca3585f5f725320b5223  82s126-556rt4-256x4-oc-prom.pdf
0552f028f377ad641659bd44d671e420db08839bd45adbcf8c04de7bf11795ad  sn74ls86a-ti.pdf
03d48a8503d9693d23081b9a42c278abbbae94245cbb8e3d76ad584d950d89ca  k555lp5-eandc.pdf
22c783f99350b178b11a3f33269d24bb9f36c5634215ed39040fef0736500e99  kt315-family-promelec.pdf
9c33e08a3bfb7ab3b685848eee0d80457774918ce0bd3224e17cd0c1970a20a9  sn54s138-ti.pdf
e38df7ca56f6fa10a78f0c84ee40d26c90af25a1c6c3a692508e46bee2ee11d1  hro-type-c-31-m-17.pdf
```

Sources:

- К170УП2 PDF: `https://www.km-cs.com/datasheet/_Other/k170up2.pdf`
- SN74188 Texas Instruments scan: `https://www.radioradar.net/en/files.html?fid=500816`
- FD179X PDF provenance is recorded in `../wd1772-vg93/README.md`.
- Intel P8255A scan: `https://datasheet4u.com/pdf/511194/P8255A.pdf`
- КР580ВА86/8286 scan: `https://datasheet4u.com/pdf/1529844/KR580VA86.pdf`
- SN74LS253 Texas Instruments PDF: `https://www.ti.com/lit/ds/symlink/sn54ls253.pdf`
- SN74LS123 Texas Instruments PDF: `https://www.ti.com/lit/ds/symlink/sn74ls123.pdf`
- SN74LS74A Texas Instruments PDF: `https://www.ti.com/lit/ds/symlink/sn74ls74a.pdf`
- MK4564 (4164-class 64Kx1 DRAM, closest AC-timing reference for the К565РУ5Г
  bank D84-D91): `https://www.minuszerodegrees.net/memory/4164/datasheet_MK4564-12.pdf`
- Signetics 82S126 (К556РТ4 = 82S126/3601/74S387 equivalent, the D2/D6 OC PROM):
  `https://www.retrotechnology.com/restore/82S126_signetics.pdf`
- SN74LS86A Texas Instruments PDF, used only as an LS-TTL XOR output-current
  comparison for exact-revision D34 К555ЛП5:
  `https://www.ti.com/lit/ds/symlink/sn74ls86a.pdf`
- Exact-device К555ЛП5 data sheet preserved from Electronics & Communications;
  it supplies the Soviet-device voltage, fanout, input-current, and timing limits
  (the fanout/input currents imply 0.4 mA source and 8 mA sink full-fanout
  loads) but no explicit output-current test condition or nonlinear output curve:
  `https://static.insales-cdn.com/files/1/1346/27395394/original/%D0%9A555%D0%9B%D0%9F5.pdf`
- Period КТ315-family reference scan preserved by Promelec. Its old KT-13
  outline and E-C-B lead order match the installed КТ315Б package:
  `https://cdn.promelec.ru/upload/items/2020/02/06/kt315_.pdf`
- SN54S138 Texas Instruments primary manufacturer PDF, used only as the
  pin/function-compatible Schottky-TTL timing comparison for exact-revision
  D53 КР531ИД7; its 12 ns maximum at the published 5 V/25 C/15 pF test point
  is not promoted into an exact Soviet-part guarantee or an HDL delay:
  `https://www.ti.com/lit/ds/symlink/sn54s138.pdf`
- HRO TYPE-C-31-M-17 official product page and manufacturer drawing, used to
  guard the VJUGA Rev-A J3 six-contact power-only pin map and land pattern:
  `https://en.krhro.com/Product-Details/722.html` and
  `https://datasheet.lcsc.com/datasheet/pdf/26d9c5bff410f020782d77a1fd4062b2.pdf?productCode=C283540`
