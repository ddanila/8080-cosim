# К555КП14 / КР531КП14 primitive readiness

Status: **DATASHEET-EXACT INVERTING КП14 PRIMITIVE GUARDED / SLOT ENABLES OPEN**

This guard corrects D48-D52 to the SN74LS/S258 contract. With /G low,
the selected A or B input is inverted at Y; with /G high, Y is high
impedance. The РУ5 model removes this physical inversion only at its
internal storage index so CPU-visible addresses remain linear.

## Command

```sh
sync/kp14_check.sh
```

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| КП14 equivalence is pinned | PASS | Texas Instruments SDLS148, March 1988 revision; PDF SHA256 `00064b7ad7f3ac2753566d52a896235252ab2bf230aadb271ccfcbe4d62cef2b` |
| Selected data is inverted | PASS | standalone HDL test checks both select states |
| Output disable is active high | PASS | /G=1 produces Z on all four outputs |
| All five board muxes use the corrected primitive | PASS | D48-D52 are КП14 in the board model |
| Physical output pin names retain inversion | PASS | pins 4/7/9/12 are Y_N0..Y_N3 |

## Boundary

The mux truth table and address polarity are now exact. The physical timing
that alternates the CPU D48/D49 pair with the video D50/D51 pair remains
open, as do the remote sources of the video serializer control rails.

Source document: [Texas Instruments SDLS148, March 1988 revision](https://www.ti.com/lit/ds/symlink/sn74ls258b.pdf).
