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
| D104 | К170УП2 | [k170up2.pdf](k170up2.pdf) | [k170up2-pinout.txt](k170up2-pinout.txt) |
| D94 | К155РЕ3 / SN74188-compatible | [sn74188-ti.pdf](sn74188-ti.pdf) | [k155re3-pinout.txt](k155re3-pinout.txt) |
| D93 | КР1818ВГ93 / FD179X family | [fd179x-01-datasheet.pdf](../wd1772-vg93/fd179x-01-datasheet.pdf) | [kr1818vg93-pinout.txt](kr1818vg93-pinout.txt) |
| D27 | КР580ВВ55 / Intel 8255A | [intel-p8255a.pdf](intel-p8255a.pdf) | [kr580vv55-pinout.txt](kr580vv55-pinout.txt) |
| D29 | КР580ВА86 / Intel 8286 | [kr580va86.pdf](kr580va86.pdf) | [kr580va86-pinout.txt](kr580va86-pinout.txt) |
| D101 | К555КП12 / SN74LS253 | [sn74ls253-ti.pdf](sn74ls253-ti.pdf) | [k555kp12-pinout.txt](k555kp12-pinout.txt) |
| D99 | К155АГ3 / SN74123-compatible | [sn74ls123-ti.pdf](sn74ls123-ti.pdf) | [k155ag3-pinout.txt](k155ag3-pinout.txt) |
| D96 | КМ555ТМ2 / SN74LS74A-compatible | [sn74ls74a-ti.pdf](sn74ls74a-ti.pdf) | [k555tm2-pinout.txt](k555tm2-pinout.txt) |
| D84-D91 | К565РУ5Г / 4164-class 64Kx1 DRAM | [mk4564-64kx1-dram.pdf](mk4564-64kx1-dram.pdf) | [k565ru5-pinout.txt](k565ru5-pinout.txt) |
| D2, D6 | К556РТ4 / 82S126 256x4 OC PROM | [82s126-556rt4-256x4-oc-prom.pdf](82s126-556rt4-256x4-oc-prom.pdf) | [k556rt4-pinout.txt](k556rt4-pinout.txt) |
| D34 | К555ЛП5, with SN74LS86A current-condition comparison | [k555lp5-eandc.pdf](k555lp5-eandc.pdf), [sn74ls86a-ti.pdf](sn74ls86a-ti.pdf) | [k555lp5-output-reference.txt](k555lp5-output-reference.txt) |
| VT2 | КТ315Б, old KT-13 package | [kt315-family-promelec.pdf](kt315-family-promelec.pdf) | [kt315b-output-reference.txt](kt315b-output-reference.txt) |
| D53 | КР531ИД7, with SN54S138 primary compatible-device timing comparison | [sn54s138-ti.pdf](sn54s138-ti.pdf) | [kr531id7-timing-reference.txt](kr531id7-timing-reference.txt) |
| VJUGA Rev-A J3 | HRO TYPE-C-31-M-17 USB-C receptacle | [hro-type-c-31-m-17.pdf](hro-type-c-31-m-17.pdf) | [hro-type-c-31-m-17-footprint.txt](hro-type-c-31-m-17-footprint.txt) |
| VJUGA Rev-A F1 | Bourns MF-RG300-0-14 resettable PTC | [bourns-mf-rg.pdf](bourns-mf-rg.pdf) | [bourns-mf-rg300-footprint.txt](bourns-mf-rg300-footprint.txt) |
| VJUGA Rev-A D1 | Littelfuse P4KE6.8A-B unidirectional TVS | [littelfuse-p4ke.pdf](littelfuse-p4ke.pdf) | [littelfuse-p4ke6v8a-footprint.txt](littelfuse-p4ke6v8a-footprint.txt) |

## Verify retained artifacts

The [checksum manifest](SHA256SUMS) records the PDF identities. From the
repository root, run:

```sh
(cd ref/datasheets && sha256sum -c SHA256SUMS)
```

`sync/reference_artifact_check.sh` includes this manifest. Matching hashes
establish retained-file identity; they do not prove fitted-chip equivalence,
board continuity or timing. Compatible-device references remain comparisons
unless the text interpretation identifies exact-device evidence.

## Sources

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
- Exact-device К555ЛП5 data sheet preserved from Electronics & Communications:
  `https://static.insales-cdn.com/files/1/1346/27395394/original/%D0%9A555%D0%9B%D0%9F5.pdf`
- Period КТ315-family reference scan preserved by Promelec:
  `https://cdn.promelec.ru/upload/items/2020/02/06/kt315_.pdf`
- SN54S138 Texas Instruments manufacturer PDF, used as a compatible-device
  timing comparison for D53 КР531ИД7:
  `https://www.ti.com/lit/ds/symlink/sn54s138.pdf`
- HRO TYPE-C-31-M-17 official product page and manufacturer drawing, used to
  guard the VJUGA Rev-A J3 six-contact power-only pin map and land pattern:
  `https://en.krhro.com/Product-Details/722.html` and
  `https://datasheet.lcsc.com/datasheet/pdf/26d9c5bff410f020782d77a1fd4062b2.pdf?productCode=C283540`
- Bourns MF-RG official product page and manufacturer series datasheet, used to
  guard the VJUGA Rev-A F1 exact suffix, electrical limits, thermal derating,
  and static fit:
  `https://www.bourns.com/products/circuit-protection/resettable-fuses-multifuse-pptc-aec-q200-compliant/product/MF-RG` and
  `https://www.bourns.com/docs/product-datasheets/mfrg.pdf`
- Littelfuse P4KE official product page and manufacturer series datasheet, used
  to guard the VJUGA Rev-A D1 exact suffix, pulse limits, polarity, DO-41 body,
  and lead dimensions:
  `https://www.littelfuse.com/products/overvoltage-protection/tvs-diodes/leaded/p4ke/p4ke6-8a` and
  `https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_p4ke_datasheet.pdf.pdf`
