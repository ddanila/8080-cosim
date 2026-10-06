# К155АГ3 / 74123 one-shot readiness

Status: **PACKAGE BEHAVIOR AND D56 TRIGGER GROUNDING GUARDED**

The `ag3_oneshot` primitive implements two К155АГ3/74123 retriggerable
monostable sections. Its default pulse parameters are 223000 ns and 5040 ns,
chosen from the traced D56 R59/C8 and R47/C7 timing networks. They are fixed
model parameters, not values computed from board JSON at runtime.
This timed behavior is simulation-only. With `YOSYS` defined, the primitive
drives high-impedance outputs for the LVS library; it is not a synthesized
one-shot implementation.

## Primary specification

Texas Instruments, *SN54122/SN54123/SN54130/SN54LS122/SN54LS123 and
SN74122/SN74123/SN74130/SN74LS122/SN74LS123 — Retriggerable Monostable
Multivibrators*, SDLS043, December 1983, revised March 1988:

<https://www.ti.com/lit/ds/symlink/sn74ls123.pdf>

The Icarus test uses shortened pulse widths of 100/40 ns and retrigger
inhibit intervals of 10/5 ns. It checks:

- active-low overriding clear and complementary Q/Q-bar outputs;
- B rising with A low, A falling with B high, and valid clear-release triggers;
- independent dual sections and the configured test pulse durations;
- retrigger extension after the configured inhibit interval; and
- immediate clear termination.

## Installed-board trigger closure

The native sheet leaves D56.1 and D56.9 unstubbed, but two overlapping owner
solder photographs resolve the installed `.009` target. The reflected local
package fit places D56.9 directly on D56.8's upper ground rail; D56.1 joins the
same rail through the uninterrupted wide left-edge return. Both active-low A
inputs are therefore grounded. Exact-revision .009 E3 sheet 2 and direct owner
continuity on 2026-07-21 close the active-high trigger inputs separately:
D54.17 H.SYNC DSL drives D56.10/B2, while D55.17 VERT SYNC DSL drives D56.2/B.
D56.12/Q2_N drives the tied D55.15/CLK1 and D55.18/CLK2 inputs. D57.17/SYNC B
is a separate boundary. The position-159 callout material itself remains held.

## Command

Run from the repository root with Bash, Python 3, and Icarus Verilog
(`iverilog` and `vvp`). The command overwrites this report; set `AG3_REPORT`
to select another output path. Simulation files are temporary.

```sh
sync/ag3_check.sh
```

## Result

```text
AG3-ONESHOT: PASS triggers clear complements inhibit retrigger dual-sections
```

## Evidence boundary

The script also checks selected D56 JSON nets and no-connect entries, plus
registration metadata for the two photographed ground observations. It does
not recheck photo hashes, inspect copper, or simulate D56 in the complete
board. The shortened device test does not verify the default D56 pulse widths.

The RC-derived widths are fixed model estimates. The preserved TI document
covers both standard and LS families; its LS timing characteristics do not
qualify the installed К155АГ3. Measure the fitted part across component
tolerance and temperature before using these widths as hardware limits.
D56.12's printed tag-16 destination is owner-closed to D55.15/.18. The exact
position-159 assembly material and installed auxiliary-annulus disposition remain
physical boundaries.
