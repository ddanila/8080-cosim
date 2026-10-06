# D26 PA6 to D101 enable: IMDRG source review

The exact `.009 Э3` sheet 1 native frame
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101824181.MP.jpg`
(SHA256 `55ead8fd296762bd14a6efe80ccffc191884897153ca92702a4777c4eac40b38`)
labels D26 PA6/pin 38 `(IMDRG)` and sends that conductor to sheet 3.
The adjacent PA4 and PA7 rows read `AUDC` and `STB`; PA5 is omitted.

The sheet 3 native frame
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101648508.jpg`
(SHA256 `ef04482bdd7f15a20e132034709bb7b6dfab54d6ac9d4efe2f6510575b4aa641`)
labels the sheet-1 arrival `IMDRG` immediately before D101 К555КП12
VA/`OE0_N` pin 1. The matching names and reciprocal `(3)`/`(1)` sheet
numbers close the drawing path D26.38 → D101.1. They do not prove
original-board continuity.

The source model has `FDC_IMDRG` at both pins. Structural HDL uses
PPI0 PA6 for D101's section-A active-low enable; the runnable model still
holds D101's unmeasured first-half input joins outside its active precomp
behavior. The source and routed PCB pad nets agree, while the routed PCB
has no copper connecting these pads. Check D26.38↔D101.1 with both chips
removed before routing or using the original board for runtime interpretation.
