# Factory modification disposition

Status date: **2026-07-15**.

Status: **FACTORY MODIFICATIONS GUARDED / PAD MAPPING REQUIRED**

The `ДГШ5.109.009 СБ` Вид В detail proves that positions 150/159
modify copper around D56, D15, D14, and D11. The unnumbered detail
mixes mounting-side context with solder-side artwork, so it does not
by itself prove package pin numbers or final net partitions.
Two independent component views plus the reflected solder panorama now
close the D15 cut topology and the D14 position-159 ground link. D56,
D11, and the remaining D14 auxiliary/replacement paths stay unproved.

| Ref | Factory operation locality | Current disposition | Closure evidence |
| --- | --- | --- | --- |
| D56 | АГ3 timing area: multiple drawn cuts/patches around the package fanout | DESIGN HOLD — affected footprint exists, exact modified pads/nets not mapped | registered two-sided copper overlay plus pad/via continuity (the acquired sheets 2-5 wire table covers wires/cables only, not cut pads) |
| D15 | EPROM area: Разрезать cuts the auxiliary A2/A1 bridge between the D15.8- and D15.9-side landings; no replacement wire is drawn in the D15 detail | PHOTO-CLOSED — cut separates the auxiliary D15.8/A2 and D15.9/A1 landings; the clean source net partition matches | two independent component views, reflected solder confirmation, and guarded source pin nets; original auxiliary-hole drill placement remains fabrication-held |
| D14 | АП2 serial-driver area: registered notch-up orientation maps the right row to D14.8-.5 and the first four left-row holes to D14.1-.4; position 159 closes the D32.4/GND-to-D14.1 link, while the fifth landing and remaining replacement traces stay held | PARTIAL PHOTO-CLOSE — position 159 preserves D32.4/GND-to-D14.1; remaining fifth landing and replacement traces are held | two independent component views plus notch-oriented factory row registration; map the fifth landing, three long traces, and right-row dogleg before full release |
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

## D14 position-159 registration

Both component photographs fix D14 and D32 notch-up. This maps the
factory detail's four-hole right row to D14.8 through D14.5 and the
first four holes of the five-hole left row to D14.1 through D14.4.
The position-159 leader reaches the D14.1-side stub. In both views, one
uninterrupted copper strip joins that landing directly to D32.4, already
a guarded `GND` pin. The clean source model therefore assigns D14.1 to
`GND` and preserves the executed factory topology without adding an
unmeasured auxiliary drill.

| Component view | D32.4 fit error | D14.1 fit error | Link-length error | Result |
| --- | ---: | ---: | ---: | --- |
| PXL_20260710_200358952.jpg | 0.002 mm | 0.002 mm | 0.003 mm | continuous D32.4/GND-to-D14.1 copper |
| PXL_20260710_200402344.jpg | 0.010 mm | 0.001 mm | 0.010 mm | continuous D32.4/GND-to-D14.1 copper |

The fifth left-row landing below D14.4, the three long replacement
traces, and the right-row dogleg are not electrically closed by these
views. D14.2 and D14.7 remain measurement boundaries, and no remote net
or fabrication geometry is inferred from the drawing alone.

## Guarded evidence

- `PXL_20260711_114626340.jpg`: full Вид В and all four local details.
- `PXL_20260711_114633498.jpg`: enlarged D15 Разрезать operation.
- `PXL_20260711_114638730.MP.jpg`: full-resolution positions 150/159 context.
- `factory-modification-registration.json`: two-face D15 cut-pair and two-view D14 position-159 registration.
- `ref/photos/juku-pcb-2/BODGE-TRIAGE.md`: factory-versus-owner disposition.

## Release rule

Do not release or reroute the board on netlist equivalence alone. For each
of D56/D11 and the remaining D14 detail, identify the modified pad/via pair(s), the cut original
segment, and the replacement connection; then prove the final source-PCB
net partition matches the factory result. D15 and the D14.1 ground link
are electrically closed; their unmeasured auxiliary-hole geometry remains
held only for an original-artwork replica.
