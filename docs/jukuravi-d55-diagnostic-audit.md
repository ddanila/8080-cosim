# Jukuravi D55 diagnostic audit

Status date: 2026-08-09
Verdict: **T15/T16/T31 D55 results are not valid evidence that either D55
package is bad. T34 corrects the clocking error and reports a D55 functional
path, not a package identity.**

## Bottom line

The earlier register predicate had the right data-polarity idea but an invalid
timing assumption. It programmed each 8253 counter in binary Mode 0, wrote an
MSB-only count, immediately latched the counter and read DB7. A real 8253
transfers the programmed count into the counting element on a counter clock.
The C cosim and default historical HDL abstraction made that transfer
immediate, so they could certify a sequence that had not supplied a physical
clock.

This matters uniquely for D55. The exact `.009` sheet makes its clocks
dependent on the video chain:

| D55 counter | Clock source | Functional use in standard ROMs |
| --- | --- | --- |
| 0 | D54 OUT0 (`PIT_HCHAIN`) | 313-line frame divider |
| 1 | D56 Q2_N | vertical interval / D35 frame-interrupt path |
| 2 | D56 Q2_N | vertical front porch / D56 vertical-sync path |

T31 finished the preceding D54 test by programming D54 counter 0 as Mode 0
with `3F00h`. Its OUT0 remains low until 16,128 direct 1 MHz clocks have
elapsed, about 16.1 ms. T31 reaches all four D55 latch/read predicates much
earlier. It also leaves D54 counter 2 unable to generate the horizontal-sync
triggers from which D56 Q2_N clocks are derived. Consequently, all four exact
T31 D55 latches can precede transfer of the newly written counts.

T15 uses the same immediate sequence. T16 adds eight NOPs around accesses but
does not start the D54/D56 source chain; spacing bus operations does not create
a missing D55 clock. Their varying D55 codes are therefore compatible with
old or power-up counting-element contents and cannot localize a bad D55.

## Primary evidence

The following sources agree:

- The owner photograph of exact drawing `ДГШ5.109.009 Э3`, sheet 2, shows
  D54/D55/D57 and their individual clock, gate and output pins. The detailed
  D54/D55 image is
  `ref/photos/dgsh5-109-009-e3/PXL_20260718_101914588.jpg`.
- Exact-sheet continuity closes D54.17 to D56.10, D55.17 to D56.2, and D56.12
  to tied D55.15/D55.18. The reviewed endpoints are in
  `docs/memory-timing-boundary.md` and `kicad/juku.board.json`.
- D55 has its own decoded select, `D9.10 -> D55.21`, while D54/D55/D57 share
  IORD and IOWR. See `docs/io-decode-boundary.md`.
- The Intel 8253 programming and timing diagrams distinguish loading the count
  register from the clocked counter operation. The audit used the Intel
  8253/8253-5 data sheet, pages 6-215 through 6-219:
  <https://sapr.asvcorp.ru/datasheets/64/05/00000000564.pdf>.

## Standard Juku ROM use

EKTA 3.7 is independent evidence that all three D55 channels are operationally
used. `scripts/report_video_pit_timing.py` extracts this exact sequence from
`roms/ekta37.bin` offsets `01D4h..0222h`:

```text
D55 controls: 17=73, 17=93, 17=34
D55 ch0:      14=39, 14=01    binary 0139h = 313
D55 ch1:      15=72, 15=00    BCD 0072
D55 ch2:      16=25           BCD 25
```

The independently retained JMON 3.3 trace also programs D54 and all three D55
channels and reaches the D55/D35 frame-interrupt vector. Thus D55 is a video
and frame-timing PIT; it is not used for the D57 baud or speaker functions.

Standard-ROM use proves relevance and topology. It does not make the old
diagnostic sequence valid and does not distinguish D55 silicon from its
select, bus, socket, supply or clock sources.

## Corrected T34 predicate

`firmware/diag-d0-clocked-pit.bin` preserves T31's low-4K loader and transport
policy, but changes the PIT diagnostic as follows:

1. D54 is tested using its direct clocks.
2. Before D55, T34 programs only D54 with the exact EKTA horizontal-chain
   controls and counts. It deliberately does not pre-program D55.
3. Every D55 channel is written and read with both a DB7-high and DB7-low
   Mode-0 count. After each write, a register-only loop waits nominally 300 us.
   The factory line period is 64 us, so more than four complete worst-phase
   source periods occur before the latch command. Opposite predicates ensure
   that a missing clock or ignored write cannot pass on a coincidental stale
   counting-element value. In Mode 0, a low GATE inhibits decrementing; it does
   not eliminate the clocked count-register-to-counting-element load. Therefore
   D55 channel 0's low OUT/GATE state does not invalidate the channel-1/2
   register predicates.
4. D57 is then tested using its independent direct clock sources.

The image is T34, ROM version `1Ch`, self-CRC16 `A637`, SHA-256
`63f69281e632324083bd5e7040d19a7939936b98a4d5cb245e008ea491d45cb5`.
T31 remains byte-for-byte unchanged so its physical evidence is not confused
with the corrected test.

## Structural simulation matrix

`sync/jukuravi_d55_clock_audit.sh` enables clocked Mode-0 count transfers in
all three structural PITs, drives the physical 16 MHz and 2 MHz timing ratio,
executes the complete ROM through the CPU, and stops at the first post-PIT
USART write. `unclocked` counts D55 latch commands issued while the newly
written count is still waiting for a D55 clock.

| Image / injected boundary | Bitmap E | D55 reads | D55 latches | Unclocked | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| exact T31, otherwise clean | `08` | 4 | 4 | 4 | negative control passes |
| T34, clean | `00` | 6 | 6 | 0 | passes |
| T34, D55 channel-2 DB7 forced low | `08` | 6 | 6 | 0 | detects data-path fault |
| T34, D54 OUT0/horizontal chain held low | `08` | 6 | 6 | 6 | detects upstream clock-path fault |
| T34, D56 Q2_N held low | `08` | 6 | 6 | 4 | detects channel-1/2 clock-path fault |
| T34, D9/CS_D55 disabled | `08` | 6 | 6 | 0 | detects select-path fault |

The clean and all five adversarial cases passed on 2026-08-09. The matrix
proves the corrected predicate is sensitive to the intended functional path
and no longer creates a clean-board D55 failure solely from missing setup
clocks. It also proves why the result must not be labeled “D55 package bad.”

## Board conclusions

### CS00015

There is **no longer sufficient desk evidence to call D55 bad or marginal**.
T15, T16, T31 and T32 all inherit the unclocked predicate. The repeatable T16
code 3 remains useful historical behavior, but it is not a valid channel-2
package localization. No substitution result was recorded. CS00015 is now
classified as **D55 path unverified; rerun T34 before component substitution**.

### CS00024

Two cold T31 boots repeated bitmap `18` (D55 plus D57), while PIC, PPI, D54 and
the two compact RAM windows passed. Exact T31's D55 bit is explained by the
diagnostic clocking defect on a clean structural board. Four later exact T34
`1C/A637` cold boots all cleared corrected D55. CS00024 is therefore classified
as **D55 functional path clean in four T34 boots and the first T36 boot; no
D55 package-fault evidence**. The T36 `1E/C617` capture also cleared D57 and
both compact RAM predicates before every uploaded CPU/address probe passed.

D57 was not stable across the T34 boots: the first bitmap was `00`, and the
next three were `10`; the later T36 bitmap was `00`. Long seven-vote loader
PROBE commands also repeated a
strong-CRC parser-buffer result, while a short seven-vote CONFIG followed by
the same PROBE at one vote passed exactly. Later same-process marker tests
proved an idle RAM/refresh failure: regular roughly five-second accesses kept
the tested state exact, while an untouched interval between roughly 5 and 17
seconds destroyed mutable loader state. Those are separate D57/refresh
findings and do not weaken the corrected D55 result. Exact captures and limits
are recorded in
[`../spinoffs/jukuravi/CS00024-PHYSICAL.md`](../spinoffs/jukuravi/CS00024-PHYSICAL.md).

## What a future result means

A clean T34 result clears the tested D55 register/clock/select path under the
diagnostic conditions. A T34 `08` result proves that the functional path
failed, but the remaining candidates include:

- D55 package, socket, local power or bypass;
- D9/CS_D55 decode;
- D55-local IORD/IOWR or data-bus continuity;
- D54 OUT0 and D54 OUT2 output paths; and
- D56 and the D56 Q2_N route to D55.15/D55.18.

Package confirmation still requires controlled substitution with the same T34
image before and after, or direct signal measurements that separately prove
select, strobes, data and all three clocks. Software alone cannot make that
package-level claim 100% unique.
