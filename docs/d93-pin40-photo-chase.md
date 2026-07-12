# D93 pin-40 power-trace chase

Status: **PAD IDENTIFIED / P12V DESTINATION STILL UNPROVED**

The physical D93 is a populated КР1818ВГ93 in the normal board state. The
2026-07-10 maintenance close-up temporarily removes it from its socket, which
exposes the contacts for a more reliable power-pad chase.

## Registered evidence

- `ref/photos/juku-pcb-2/PXL_20260710_202708344.jpg`: the corrected exposed-
  socket affine fit places D93.40 at `(2206,2201)` px, the rightmost lower-row
  contact beside the socket's printed `40`.
- `ref/photos/juku-pcb-2/PXL_20260710_200506061.jpg`: the reflected solder fit
  places the same physical pad at `(1559.5,1479.8)` px.
- The solder joint has no same-layer trace departure. This agrees with the
  component close-up, where copper leaves the socket contact on the component
  side toward the immediately adjacent region hidden by the green clip.
- The overlapping populated component tile
  `PXL_20260710_200402344.jpg` confirms the trace continues away from the
  D93 corner, but the intervening landing/path is obscured by the cable/clip
  area. It does not establish a connection to D100 or any other package.

The earlier westbound solder chase was based on a falsely projected pad and
remains rejected. The new evidence proves pad identity and which copper side
must be followed, but not continuity to `P12V`. Therefore D93.40 stays unnetted
in the authoritative board model.

## Closure requirement

Use continuity mode between the exposed D93.40 socket contact and a known
`P12V` anchor (`X8.3`, `A60`, or another already-proved +12 V point), or obtain
an unobscured component-side macro photograph of the adjacent landing. A
datasheet requirement alone is insufficient for the power-safety release gate.
