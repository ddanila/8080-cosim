# VJUGA rev B expanded I/O exact parts — R5.I7

Status: **PASS / FROZEN 2026-08-29 / ORDER HOLD**. The machine-readable authority
is `kicad/revb/io-parts.json`; stock figures are dated evidence and must be
refreshed before purchase.

The exact first-article core is Rochester `MD8251A/B`, `MD82C55A/B` and
`MD82C59A/B`, Renesas `ID82C54`, TI `SN74LS148N` and `CD74ACT273E`, and Microchip
`ATF22V10C-15PU`. These parts preserve the required 8251/8255/8259/8253 register
contracts in socketed 5 V through-hole packages. The ceramic/legacy peripherals
are intentionally expensive but auditable; cheaper Soviet or NOS substitutions
must be read-marked, pin-checked and bench-qualified rather than silently mixed.

The observable layer uses eight Kingbright `WP710A10LGD` LEDs, Same Sky
`CPT-1207-5LTH-T`, and onsemi `P2N3904ABU`. The transistor contract fixes the
board's E/B/C order. The exact MPN remains authoritative here and in
`io-parts.json`; the GOST top silk uses the shorter, unambiguous family/value or
role (for example `U8 82C54 D57` and `D_POST0 GREEN`) so every fitted part is
identified without turning the assembly face into an unreadable distributor
label.

Run:

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_io_parts.py --self-test
```

The gate cross-checks every reference/type/footprint, timer supply/package/pins,
sound transistor nets, and complete assembly markings. It rejects wrong timer
package, missing latch and an ambiguous generic-timer silk mutation.

Primary/current sources: [Renesas ID82C54](https://www.renesas.com/en/products/82c54/part-details/id82c54),
[Rochester MD8251A/B stock](https://www.digikey.com/en/products/detail/rochester-electronics-llc/MD8251A-B/15641804),
[TI CD74ACT273E](https://www.ti.com/product/CD74ACT273/part-details/CD74ACT273E),
[Microchip ATF22V10C](https://www.microchip.com/en-us/product/atf22v10c),
[Kingbright WP710A10LGD](https://www.kingbrightusa.com/distyPNInv.asp?match=1&sltSearch=distyInv&txtPartNo=WP710A10LGD), and
[Same Sky CPT-1207-5LTH-T](https://www.sameskydevices.com/product/resource/cpt-1207-5lth-t.pdf).
