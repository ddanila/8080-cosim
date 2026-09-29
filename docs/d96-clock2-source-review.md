# D96 section-2 clock source on exact `.009 Э3` sheet 3

The native full-sheet overview
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101633062.jpg`
(SHA256 `5f58dff9c2e1f8237f1c54e44a7ff5db2381b7c503d5e25466fcd219915f7047`)
shows D94 output 1/pin 2 rising to the upper conductor that reaches
D96 section-2 CLK/pin 11. The native detail
`PXL_20260718_101641055.jpg` shows pin 11's lead turning upward. It
crosses the local D28.10-to-D96.10 `/PRE2` conductor without a filled dot;
the two conductors are separate in the drawing.
In original overview pixels, follow D94.2 upward near `x≈1200` to the
upper run near `y≈616`, then right to the filled junction above D96.11 near
`(1580,616)`. D96.11 descends from that junction and crosses the D28.10
output stroke near `(1580,915)` without a dot. D94 output-0/pin-1
uses a different parallel conductor; this trace starts at pin 2.

Owner chip-removed continuity already joins D94.2 to D99.9 and R89.1.
The source model now adds D96.11 to that island. The archived component and
reflected solder views identify the D96.11 pad but cannot follow its obscured
F.Cu path to D94.2. Thus the D96.11 branch is drawing-closed and physically
unconfirmed. With D94 and D96 removed and power off, check D96.11 against
D94.2, D99.9, and R89.1. Also check D96.11 against D96.10 to test the
unmarked crossing without assuming a join.
