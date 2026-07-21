# К155АГ3 / 74123 one-shot readiness

Status: **PACKAGE BEHAVIOR AND D56 TRIGGER GROUNDING GUARDED**

The `ag3_oneshot` primitive now implements the two К155АГ3/74123
retriggerable monostable sections instead of releasing all four outputs as
high-impedance placeholders. D56 uses the traced R59/C8 and R47/C7 timing
networks, giving typical modeled pulses of about 223 us and 5.04 us.

## Primary specification

Texas Instruments, *SN54122/SN54123/SN54130/SN54LS122/SN54LS123 and
SN74122/SN74123/SN74130/SN74LS122/SN74LS123 — Retriggerable Monostable
Multivibrators*, SDLS043, December 1983, revised March 1988:

<https://www.ti.com/lit/ds/symlink/sn74ls123.pdf>

The guard covers:

- active-low overriding clear and complementary Q/Q-bar outputs;
- B rising with A low, A falling with B high, and valid clear-release triggers;
- independent dual sections and parameterized RC pulse durations;
- retrigger extension after the documented 0.22-Cext inhibit interval; and
- immediate clear termination and cancellation of stale delayed completions.

## Installed-board trigger closure

The native sheet leaves D56.1 and D56.9 unstubbed, but two overlapping owner
solder photographs resolve the installed `.009` target. The reflected local
package fit places D56.9 directly on D56.8's upper ground rail; D56.1 joins the
same rail through the uninterrupted wide left-edge return. Both active-low A
inputs are therefore grounded. Exact-revision .009 E3 sheet 2 and direct owner
continuity on 2026-07-21 close the active-high trigger inputs separately:
D54.17 H.SYNC DSL drives D56.10/B2, while D55.17 VERT SYNC DSL drives D56.2/B.
D56.12/Q2_N drives the tied D55.15/CLK1 and D55.18/CLK2 inputs. D57.17/SYNC B
is a separate boundary, correcting the older scan chase that merged both D56
triggers onto it. The position-159 callout material itself remains held.

## Command

```sh
sync/ag3_check.sh
```

## Result

```text
AG3-ONESHOT: PASS triggers clear complements inhibit retrigger dual-sections
```

## Evidence boundary

The RC-derived widths are datasheet-typical behavioral values, not a substitute
for measuring the installed К155АГ3 across component tolerance and temperature.
D56.12's printed tag-16 destination is owner-closed to D55.15/.18. The exact
position-159 assembly material and installed auxiliary-annulus disposition remain
physical boundaries.
