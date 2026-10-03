# К555КП14 / КР531КП14 primitive readiness

Status: **DATASHEET-EXACT INVERTING КП14 PRIMITIVE GUARDED / BOARD TIMING UNMEASURED**

The primitive implements the SN74LS/S258 contract. With /G low,
the selected A or B input is inverted at Y; with /G high, Y is high
impedance. The РУ5 model removes this physical inversion only at its
internal storage index so CPU-visible addresses remain linear.

## Command

```sh
sync/kp14_check.sh
```

The standalone test checks inverted selection for A=1010/B=0101 and
high impedance on disable. The script also checks contract metadata and
the five canonical JSON component types and output pin names. It does
not hash the PDF, inspect PCB pads, or test complete-board address timing.
The PDF hash below is recorded metadata.

## Checks

| Check | Result | Evidence |
| --- | --- | --- |
| Contract records the КП14 equivalence | PASS | Texas Instruments SDLS148, March 1988 revision; PDF SHA256 `00064b7ad7f3ac2753566d52a896235252ab2bf230aadb271ccfcbe4d62cef2b` |
| Selected data is inverted | PASS | standalone HDL test checks both select states |
| Output disable is active high | PASS | /G=1 produces Z on all four outputs |
| All five JSON mux entries declare КП14 | PASS | D48-D52 are КП14 in the board model |
| Physical output pin names retain inversion | PASS | pins 4/7/9/12 are Y_N0..Y_N3 |

## Boundary

The D40/D59 1 MHz enable conductor is source- and owner-closed; see
[the route review](d40-d59-d92-d95-1mhz-route.md). The structural model
applies complementary enables to D48-D51. Runnable simulation uses a
CPU-only address-bus scaffold and a separate video DRAM port, so it does
not prove physical slot timing. Measured mux timing and unresolved
serializer controls remain board boundaries; see
[video reconstruction](video-readout-readiness.md).

Source document: [Texas Instruments SDLS148, March 1988 revision](https://www.ti.com/lit/ds/symlink/sn74ls258b.pdf).
