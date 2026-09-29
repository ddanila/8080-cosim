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
The source model includes D96.11 on that island. A native owner solder reread
of `PXL_20260710_200506061.jpg` crop `(580,1920)`–`(1150,2040)` shows a
continuous B.Cu line from the joint near registered D96.11 `(625,1994)`
through `(650,1963)` and `(820,1963)` to a filled joint near registered
D28.11 `(839,1996)`. The visible joint centres are about `(624,1988)` and
`(849,1990)`, within roughly 6/11 px of the package fits. Exact sheet 3
places D28.11 on raw DRQ with D93.38/R94.1, separate from D96.11 CLK2.
The photographed route is therefore a conditional owner-board/source
conflict, not grounds to merge the replica nets. With power off, check
D96.11↔D28.11 directly, then D96.11 against D94.2, D99.9, R89.1,
D93.38, and R94.1. Also check D96.11↔D96.10 to test the unmarked drawing
crossing, and revisit the photo pin registration if the apparent DRQ join
fails continuity.
The adjacent native solder tiles `PXL_20260710_200509593.jpg` and
`PXL_20260710_200514102.jpg` cover regions farther right on the board;
neither repeats these two joints. The route has only one photographic view.
