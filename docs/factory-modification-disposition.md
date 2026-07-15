# Factory modification disposition

Status date: **2026-07-15**.

Status: **FACTORY MODIFICATIONS GUARDED / PAD MAPPING REQUIRED**

The `ДГШ5.109.009 СБ` Вид В detail proves that positions 150/159
modify copper around D56, D15, D14, and D11. The unnumbered detail
mixes mounting-side context with solder-side artwork, so it does not
by itself prove package pin numbers or final net partitions.
Two independent component views plus the reflected solder panorama now
close the D15 cut topology; D56, D14, and D11 remain unproved.

| Ref | Factory operation locality | Current disposition | Closure evidence |
| --- | --- | --- | --- |
| D56 | АГ3 timing area: multiple drawn cuts/patches around the package fanout | DESIGN HOLD — affected footprint exists, exact modified pads/nets not mapped | registered two-sided copper overlay plus pad/via continuity (the acquired sheets 2-5 wire table covers wires/cables only, not cut pads) |
| D15 | EPROM area: Разрезать cuts the auxiliary A2/A1 bridge between the D15.8- and D15.9-side landings; no replacement wire is drawn in the D15 detail | PHOTO-CLOSED — cut separates the auxiliary D15.8/A2 and D15.9/A1 landings; the clean source net partition matches | two independent component views, reflected solder confirmation, and guarded source pin nets; original auxiliary-hole drill placement remains fabrication-held |
| D14 | АП2 serial-driver area: position-159 leader enters a five-hole auxiliary/left field beside the four-pad package row; three long replacement traces and one right-row dogleg are drawn, but mirrored pin numbering is not proved | DESIGN HOLD — affected footprint exists, exact modified pads/nets not mapped | registered two-sided copper overlay plus pad/via continuity (the acquired sheets 2-5 wire table covers wires/cables only, not cut pads) |
| D11 | 8251 USART area: detail shows one 14-pad package column plus a four-hole auxiliary field and a position-159 bridge; a held-out-validated solder fit localizes the visible reworked copper beside D11 pins 4-6, but the obscured bridge endpoints remain unproved | DESIGN HOLD — affected footprint exists, exact modified pads/nets not mapped | registered two-sided copper overlay plus pad/via continuity (the acquired sheets 2-5 wire table covers wires/cables only, not cut pads) |

## D15 cut registration

The enlarged factory detail draws four holes on the auxiliary trace and
places `Разрезать` between the final pair, aligned between D15 pad levels
8 and 9. The same pair is visible with removed intervening copper in two
independent component photographs. Reflected solder copper connects the
upper landing to D15.8 (`A2`) and the lower landing to D15.9 (`A1`).
No replacement conductor is drawn in the D15 detail: the operation removes
an unwanted A2/A1 bridge, which is exactly the net partition already present
in the clean source PCB.

| Landing | Board centre (mm) | Component-view agreement | Solder-view error | Resulting source net |
| --- | --- | ---: | ---: | --- |
| upper | (14.129, 73.247) | 0.018 mm | 0.016 mm | D15.8 / `A2` |
| lower | (14.350, 75.515) | 0.030 mm | 0.023 mm | D15.9 / `A1` |

These centres prove local identity and topology, not fabrication-ready drill
placement. The source board therefore keeps its clean A2/A1 separation and
does not invent the two auxiliary holes until a direct dimension or
fabrication-grade local scale is available.

## Guarded evidence

- `PXL_20260711_114626340.jpg`: full Вид В and all four local details.
- `PXL_20260711_114633498.jpg`: enlarged D15 Разрезать operation.
- `PXL_20260711_114638730.MP.jpg`: full-resolution positions 150/159 context.
- `factory-modification-registration.json`: two-face D15 cut-pair registration.
- `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`: factory-versus-owner disposition.

## Release rule

Do not release or reroute the board on netlist equivalence alone. For each
of D56/D14/D11, identify the modified pad/via pair(s), the cut original
segment, and the replacement connection; then prove the final source-PCB
net partition matches the factory result. D15 is electrically closed; its
auxiliary-hole geometry remains held only for an original-artwork replica.
