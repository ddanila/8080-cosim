# D99 motor-pulse source review

The exact `.009 Э3` sheet-3 photo
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101641055.jpg` (SHA256
`86740a80fb494cdb08f4de3a120cab83e4f6638cf5885d4c83418a4a94c881a7`)
shows D99 section-2 Q/pin5 branching at a filled dot to E12 post 1. The
same conductor continues downward to D100 A7/pin7. D100 B7/pin13 then
drives X4.419, labeled `-MOTOR ON` on the drawing. The separate `MOTOR EN`
continuation from sheet 1 enters D99 section-2 `/CLR2`/pin11. It does not
join D100.7. The old model tied D26.16, D99.11, and D100.7 together and
therefore bypassed the drawn D99 motor-pulse stage.

The corrected source model has `FDC_MOTOR_EN` at D26.16/D99.11 and
`D99_Q2_BOUNDARY` at D99.5/D100.7. It keeps the selected E12 2-3 B1/HLD
path and D99.12 Q2_N-to-D100.9 OE_N path distinct. Original-board
D26.16↔D99.11 and D99.5↔D100.7 continuity still require direct checks;
the fitted R97/C17 timing predicts a nominal pulse, not proven motor
behavior on a powered board.

The corrected source topology does not establish routed copper continuity.
Source/routed drift and open connections remain in
[the routed audit](routed-refresh-audit.md); fabrication remains held under
[manufacturing readiness](replica-manufacturing-readiness.md). The retired
D26-to-D100 connection must not be reused when routing these branches.
