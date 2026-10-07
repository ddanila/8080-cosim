# VJUGA rev B expanded I/O exact parts — R5.I7

Status: **PASS / FROZEN 2026-08-29 / ORDER HOLD**. The machine-readable authority
is [`io-parts.json`](../kicad/revb/io-parts.json); stock figures are dated evidence and must be
refreshed before purchase.

The exact first-article core is Rochester `MD8251A/B`, `MD82C55A/B` and
`MD82C59A/B`, Renesas `ID82C54`, TI `SN74LS148N` and `CD74ACT273E`, and Microchip
`ATF22V10C-15PU`. These parts preserve the required 8251/8255/8259/8253 register
contracts in socketed 5 V through-hole packages. Substitutions require part-marking identification, pin/package checks and bench
qualification before they can replace these exact parts.

The observable layer uses eight Kingbright `WP710A10LGD` LEDs, Same Sky
`CPT-1207-5LTH-T`, and onsemi `P2N3904ABU`. The transistor contract fixes the
board's E/B/C order. The exact MPN remains authoritative here and in
`io-parts.json`; the GOST top silk uses the shorter, unambiguous family/value or
role (for example `U8 82C54 D57` and `D_POST0 GREEN`) so every fitted part is
identified without turning the assembly face into an unreadable distributor
label.

## Keyboard pinout mismatch — release blocker

The retained I/O design does not yet match the selected SN74LS148N.
[TI's DIP pinout](https://www.ti.com/lit/ds/symlink/sn74ls148.pdf) assigns
pin 5 to enable input `EI` and pin 14 to group-select output `GS`. The generator,
`io.board.json`, `revb_io_map.json`, and routed `io.kicad_pcb` instead connect
U5.5 to `KBD_ENC_GS` and U5.14 to GND. The intended connections are U5.5 to GND
and U5.14 to `KBD_ENC_GS`.

Correct the pin map and regenerate/requalify the I/O source, route and fabrication
package before release. Existing LVS uses the same incorrect map, and the
assembled behavioral twin does not model keyboard scanning; their passing
results do not qualify this path.

## Verification

Run from the repository root:

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_io_parts.py --self-test
```

The gate checks the references, types and footprint-map entries for the ten
part groups in `io-parts.json`, requires MPN and HTTPS datasheet fields, and pins
the ID82C54 package/supply/clock contract. It also checks U8's ground/supply pins,
Q1's E/B/C nets and ten expected assembly-value strings. Its negative controls
reject a wrong timer pin count, missing POST latch and generic timer label.

These checks use the JSON contracts; they do not inspect the routed PCB,
rendered labels, supplier stock or delivered components. The
[silkscreen checker](rev-b-silkscreen-audit.md) checks label presence and placement;
physical part acceptance remains in the [bench procedure](rev-b-b1-bench-log.md).

Manufacturer and supplier references (availability requires rechecking): [Renesas ID82C54](https://www.renesas.com/en/products/82c54/part-details/id82c54),
[Rochester MD8251A/B stock](https://www.digikey.com/en/products/detail/rochester-electronics-llc/MD8251A-B/15641804),
[TI CD74ACT273E](https://www.ti.com/product/CD74ACT273/part-details/CD74ACT273E),
[Microchip ATF22V10C](https://www.microchip.com/en-us/product/atf22v10c),
[Kingbright WP710A10LGD](https://www.kingbrightusa.com/distyPNInv.asp?match=1&sltSearch=distyInv&txtPartNo=WP710A10LGD), and
[Same Sky CPT-1207-5LTH-T](https://www.sameskydevices.com/product/resource/cpt-1207-5lth-t.pdf).
