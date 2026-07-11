# Factory modification disposition

Status date: **2026-07-11**.

Status: **FACTORY MODIFICATIONS GUARDED / PAD MAPPING REQUIRED**

The `ДГШ5.109.009 СБ` Вид В detail proves that positions 150/159
modify copper around D56, D15, D14, and D11. The unnumbered detail
mixes mounting-side context with solder-side artwork, so it does not
yet prove package pin numbers or final net partitions. The generated
clean PCB may be electrically equivalent, but equivalence is unproved.

| Ref | Factory operation locality | Current disposition | Closure evidence |
| --- | --- | --- | --- |
| D56 | АГ3 timing area: multiple drawn cuts/patches around the package fanout | DESIGN HOLD — affected footprint exists, exact modified pads/nets not mapped | sheets 2-6 connection table, or registered two-sided copper overlay plus pad/via continuity |
| D15 | EPROM area: Разрезать is on the auxiliary vertical trace between its second/third shown vias, aligned roughly between the eighth/ninth visible package-pad levels; position-159 patch detail is separate | DESIGN HOLD — affected footprint exists, exact modified pads/nets not mapped | sheets 2-6 connection table, or registered two-sided copper overlay plus pad/via continuity |
| D14 | АП2 serial-driver area: position-159 leader enters a five-hole auxiliary/left field beside the four-pad package row; three long replacement traces and one right-row dogleg are drawn, but mirrored pin numbering is not proved | DESIGN HOLD — affected footprint exists, exact modified pads/nets not mapped | sheets 2-6 connection table, or registered two-sided copper overlay plus pad/via continuity |
| D11 | 8251 USART area: detail shows one 14-pad package column plus a four-hole auxiliary field and a position-159 bridge; owner solder photo 200506061 shows reworked copper in this area, but D11 lacks a package-local fit | DESIGN HOLD — affected footprint exists, exact modified pads/nets not mapped | sheets 2-6 connection table, or registered two-sided copper overlay plus pad/via continuity |

## Guarded evidence

- `PXL_20260711_114626340.jpg`: full Вид В and all four local details.
- `PXL_20260711_114633498.jpg`: enlarged D15 Разрезать operation.
- `PXL_20260711_114638730.MP.jpg`: full-resolution positions 150/159 context.
- `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`: factory-versus-owner disposition.

## Release rule

Do not release or reroute the board on netlist equivalence alone. For each
of D56/D15/D14/D11, identify the modified pad/via pair(s), the cut original
segment, and the replacement connection; then prove the final source-PCB
net partition matches the factory result.
