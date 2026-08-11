# T31/T34/T35/T36 physical sessions on CS00024

Date: 2026-08-08
Board: Arvutimuuseum Juku `CS00024`
ROM: exact T31 `1A/72EF`

## Retained result

Two cold boots decoded the exact T31 identity and repeated diagnostic bitmap
`18`: historical D55 and D57 bits. PIC, PPI and D54 passed. Compact RAM bitmap
`83` proved both `4000h..4FFFh` and `C000h..CFFFh` windows. Loader API v2
reached READY.

PROBE did not complete. With the corrected host retry path, three attempts
returned the same strong-parser-CRC error payload
`0006373F000000000034`. No RAM upload occurred. A later resident attach sent
three solicited RESYNC attempts but received no framed response.

Primary retained captures are:

- `sessions/cs00024-t31-initial/20260808T213309.146201Z.*`
- `sessions/cs00024-t31-default/20260808T213454.577423Z.*`
- `sessions/cs00024-t31-retryfix/20260808T213825.856067Z.*`
- `sessions/cs00024-t31-attach-resync/20260808T214255.525497Z.*`

The timeout-only retry capture at `20260808T213741.612920Z` is chronology, not
positive evidence.

## D55 supersession

The 2026-08-09 desk audit proves that exact T31 produces a D55 bit on a clean
clock-faithful structural board: all four D55 latch commands occur before the
new Mode-0 counts receive their required D54/D56 clocks. Therefore bitmap
`18` is valid evidence for a T31 D57-path failure but **not** evidence that
CS00024 D55, or even its complete functional path, is bad.

At the end of the T31 session CS00024 had no valid D55 failure result, and the
next D55-specific action was a cold boot with clock-safe T34 `1C/A637`. That
action is completed below. Any future T34 `08` must still be interpreted as a
path result covering D55, D9 select, local bus/strobes, socket/power and
D54/D56 clock sources. See
[`../../docs/jukuravi-d55-diagnostic-audit.md`](../../docs/jukuravi-d55-diagnostic-audit.md).

## T34 cold boots and loader discriminator, 2026-08-09

The exact programmed T34 `1C/A637` image completed four cold boots. Corrected
D55 passed on all four, so CS00024 now has four valid clean D55 functional-path
results. PIC, PPI, D54 and both compact RAM windows also passed every time.
D57 was intermittent: the first boot returned peripheral bitmap `00`; the
next three returned `10`. Therefore neither the earlier T31 D57 indication nor
the first clean T34 result alone describes a stable state.

Evidence:

- `sessions/cs00024-t34-20260809/20260809T055628.869126Z.*` — bitmap `00`,
  zero handshake mismatches;
- `sessions/cs00024-t34-full/cold-loader-probe/20260809T060236.505488Z.*` —
  bitmap `10`, three identical strong-CRC results;
- `sessions/cs00024-t34-full/cold-loader-probe-g12/20260809T060417.872163Z.*`
  — bitmap `10`, 12 ms guard discriminator;
- `sessions/cs00024-t34-full/config-first-v1/20260809T060703.043231Z.*` —
  bitmap `10`, successful CONFIG-first/one-vote exact-cookie PROBE.

At the normal ordering, all three seven-vote PROBE attempts repeated exact
detail payload `0006373F000000000034`. Doubling the host guard from 6 to 12 ms
did not help; it returned `0006373F0000000000B4`. No upload occurred in either
case. A short CONFIG command at the same seven-vote bootstrap width succeeded,
then the complete eight-byte PROBE cookie passed at one vote. Both directions
of the USART link and the loader command surface are therefore operational;
the failure is length/time dependent rather than a dead serial interface.

The later host-driven work below proves this is a destructive elapsed-time/RAM
boundary. It does not yet identify a DRAM package or refresh-source component.

## Host-driven timing and retention result, 2026-08-09

The first full-batch attempt verified a 29-byte CALL/RET fixture, then lost the
link after a D57-touching CPU/PIT ratio snippet. The revised batch moved every
D57 operation last and replaced that measurement with a peripheral-free paired
CPU loop. On a fresh boot it measured **1.714065 MHz** effective execution
speed: 1,200,000 additional nominal T-states took 0.700090 s. This predicts a
nominal 500 ms CPU-timed tone near 583 ms and explains the owner's approximate
600 ms observation. It does not explain the separate near-990 Hz PIT tone,
whose clock remains close to nominal.

The next 386-byte write-map image uploaded with exact per-chunk readback, but
did not return after RUN. Shorter probes then exposed non-repeatable result
corruption. The same 81-byte INX/DAD image produced three different outcomes:

- a wholly malformed result and returned `A=0A`;
- a valid header/completion and correct BC/DE/HL/DAD-D values, but `0000` for
  the SP-derived result plus one changed fill byte; and
- in-place, valid header/completion and DE/HL/DAD-D, but changing BC/SP/fill
  bytes.

A later control-only re-read, with no upload or execution, changed the existing
`4D00h` block from
`58313243A5FF00000000011A015A0000011AFFFFFFFF0000` to
`0000FFFFFFFF00000000FFFFFFFF00000000FFFFFFFF0000`. This invalidates a
deterministic CPU-INX interpretation of those malformed runs and directly
proves unstable retained RAM contents over the reattach interval.

The dedicated [`retention.py`](retention.py) runner then wrote one exact
32-byte marker at `4D00h` and kept one serial process open:

- verified write and read at 5.147 s: exact;
- reads approximately every 5.15 s: exact through 30.912 s;
- fresh sparse run: exact at 5.158 s, then after leaving RAM/loader untouched
  until the 45 s target, the next CONFIG timed out after three attempts;
- warm-board 6 ms bootstrap: two cold RESETs repeated CONFIG `strong_crc`;
  raw replies first corrupted echoed command `24->34`, then echoed `24`
  correctly but retained `strong_crc` status; and
- zero host guard restored bootstrap, marker verification and an exact read at
  3.423 s, but the next CONFIG still timed out after an untouched interval to
  the 20 s target (about 16.6 s since the preceding read).

This proves an **idle RAM/refresh failure** under T34: regular RAM-touching
loader operations preserve the tested rows, while an untouched interval
between roughly 5 and 17 seconds is sufficient to destroy mutable loader state
on the warm board. USART traffic continues during the failure, so this is not
a dead serial link. T34's compact 20 ms RAM result remains valid only for that
short interval and cannot clear long-term retention. Long verified uploads can
also decay at their early target addresses before RUN, explaining why payload
length changes execution behavior.

Primary new captures are:

- `sessions/cs00024-t34-batch-physical/20260809T071631.782572Z.*` — 1.714 MHz
  measurement followed by verified write-map upload and no RETURN;
- `sessions/cs00024-t34-increment-repeat-physical/20260809T180730.412858Z.*`
  and `sessions/cs00024-t34-increment-inplace-physical/20260809T180936.570451Z.*`
  — non-repeatable 81-byte probe results;
- `sessions/cs00024-t34-increment-reread-v1-physical/20260809T181240.980761Z.*`
  — control-only changed result block;
- `sessions/cs00024-t34-retention-cold-physical/20260809T181947.593033Z.*` —
  repeated-access exact pass through 30.912 s;
- `sessions/cs00024-t34-retention-sparse-cold-physical/20260809T182357.819924Z.*`
  — exact 5.158 s sample then post-idle CONFIG timeout; and
- `sessions/cs00024-t34-retention-midpoint-g0-cold-physical/20260809T202332.467525Z.*`
  — zero-guard exact 3.423 s sample then 20 s target CONFIG timeout.

That initial desk action was implemented as T35 `1D/45C4`, exact image SHA256
`ceb55556f11318dea5ef8c36b81f931813a139ce6ba6e07b607318571c6e1274`.
Its fail-safe loader was intended to sweep all 128 4164 refresh rows in 1.2339
ms at the measured CS00024 effective CPU rate, refreshes inside blocking serial waits, starts at one
vote, exposes cooperative `CALL 07A9h`, and is host-queryable/configurable.
Cycle-based DRAM-decay simulation proves long verified upload, idle survival,
reattach, all refresh commands, and torn-disable fallback; exact T34 fails the
same idle-decay discriminator and remains byte-identical.

## T35 burn and initial apparent refresh proof, 2026-08-10

The exact T35 image was programmed into the AT28C64 with Willem verification
and one complete post-write readback. The programmed and read-back bytes both
equal `1D/45C4`, SHA256
`ceb55556f11318dea5ef8c36b81f931813a139ce6ba6e07b607318571c6e1274`.
The programmer record is in the sibling `dosravi` repository at
`sessions/at28c64-t35-write-20260810/session.json`.

The first CS00024 cold boot decoded that exact identity. PIC, PPI, corrected
D54/D55/D57, and both compact RAM windows passed. The loader reported refresh
enabled, configured geometry 128, public API `07A9h`, and 1,752 receive-wait
refresh calls. That telemetry described the intended loop count, not verified
physical-row coverage.
A resident attach more than 20 seconds later completed normally and reported
40,414 calls. This crosses the destructive T34 5-to-17-second idle interval
and proved that frequently touched T35 loader state survived on this physical
board; it is no longer only a simulation claim.

Evidence:

- `sessions/cs00024-t35-first-physical/20260810T061734.589060Z.*`;
- `sessions/cs00024-t35-idle-reattach-physical/20260810T061834.464961Z.*`.

This remains a workaround and discriminator, not a DRAM-package diagnosis.

## T35 batch stop after RUN, 2026-08-10

Four later cold sessions passed verified upload/readback/CALL/RET at `4000h`
and the refresh-aware paired CPU-timebase test. They measured 1.702803,
1.702746, 1.708031, and 1.702367 MHz. Each then uploaded a target at `4000h`,
uploaded and read back the same 12-byte cooperative-refresh wrapper, and
received the valid RUN acknowledgement for that wrapper. None received RETURN.

The first three runs varied the target; the fourth repeated the shortest target
at an A12-low wrapper address:

| Capture | Cold D57 | Wrapped target | Last valid frame |
| --- | --- | --- | --- |
| `20260810T063013.783535Z` | fail, bit `10` | 386-byte all-RAM write map | RUN ACK `7F00` |
| `20260810T150610.267813Z` | **pass**, bitmap `00` | LHLD address classes | RUN ACK `7F00` |
| `20260810T151126.497325Z` | fail, bit `10` | register-only INX/DAD | RUN ACK `7F00` |
| `20260810T154931.444912Z` | **pass**, bitmap `00` | register-only INX/DAD | RUN ACK `6F00` |

The third and fourth runs deliberately skipped every all-RAM probe. Their
short target saves and restores SP, performs no I/O, does not select all-RAM
mode, and returns in clean simulation. Therefore an all-RAM side effect,
target length, and the individual target algorithm are excluded as the common
immediate cause. The common new operation is execution through the
pre/post-refresh wrapper. The fourth run moved it from `7F00h` to `6F00h`,
keeping the same D2 always-wait class while clearing A12, and failed
identically. This physically falsifies an A12-specific wrapper-location
explanation.

The raw receive streams end in a complete CRC-valid RUN ACK. The first two
contain no later byte. The operator-interrupted third and fourth have only
`F8 00` and `09 00`, respectively, after the ACK. Neither pair is a valid frame;
both were captured around operator power-off and may be serial corruption or
power-off noise. During both stops the board emitted a continuous low-frequency
tone. This is useful path evidence, but without a frequency or the preceding
grouped-pulse cadence it cannot distinguish the ROM's nominal 250 Hz
CPU-failure tone from the nominal 125 Hz UART terminal tone.

## Why this is not the proven CS00015 D1 fault

The initial similarity was A12-related: `7F00h` has A12 high, and the exact
CS00015 D1 defect loses an already-high A12 in the shared 16-bit increment
path. Full comparison excludes that exact mechanism on CS00024:

1. T35's public refresh primitive at `07A9h` is in low ROM, but its host QUERY
   command handler is at `1070h..1118h`. Every physical T35 session returned
   valid QUERY telemetry after executing that upper-ROM handler, whose ordinary
   multi-byte instructions increment a PC with A12 already high. The larger
   reported counters and the 501 timebase calls separately prove the low-ROM
   refresh primitive, not repeated execution of the upper handler.
2. The wrapper's 12 bytes at `7F00h` were independently read back exactly.
   That readback increments a high-A12 HL address; the CS00015 defect affects
   INX/paired reads as well as PC and would not preserve this operation.
3. Injecting `JUKU_CPU_A12_INCREMENT_FAULT=1` into exact T35 simulation does
   **not** reproduce the physical trace. It loses execution in the upper-ROM
   refresh handler immediately after READY, before PROBE or any RUN ACK.
   `tests/jukuravi_t35_wrapper_a12_test.py` guards this negative result.

It remains logically possible that CS00024 has a different, RAM-cycle- or
address-combination-dependent CPU/timing fault. It is not correct to call the
present result a second instance of CS00015's rare internal D1 defect.

The public material found in the desk search gives no matching VM80A erratum.
The die-derived `1801BM1/vm80a` project describes a close 580ВМ80А/8080A
topology, reports successful thorough i8080 exercisers, and publishes no
A12-increment exception. Its electrical description does emphasize the real
NMOS requirements: separate +12 V and negative substrate supply plus 12 V
clock phases. Those rails and clocks are worthwhile general health checks, but
the present captures do not identify one as the cause. References:

- <https://github.com/1801BM1/vm80a>;
- <https://habr.com/ru/articles/249613/>;
- <https://tec.org.ru/board/kr580vm80a/104-1-0-5266>.

## Simulation matches and current localization

Clean cosim passes the same wrapper at both `7F00h` and `6F00h` under the T35
per-row decay model. A deliberately execution-only corruption of byte
`7F02h`, changing the first `CALL 07A9h` to `CALL 00A9h` while leaving ordinary
readback intact, produces the physical protocol signature: valid RUN ACK and
no RETURN. It then reaches the ROM CPU-failure path and programs D57 channel 1
with divisor 8000, a continuous nominal 250 Hz tone. This is not a fitted
component fault; it proves that a RAM instruction-fetch/misexecution event can
explain both observations without a serial failure.

D57 remains an independent intermittent finding. Its OUT0 is the traced clock
for both D11 TxC and RxC, while OUT1 drives the speaker. A D57/D11/clock-path
failure can explain loss or corruption of RETURN, but it does not by itself
explain why three different targets all stopped only after entering the same
`7F00h` wrapper. The middle failure also followed a clean cold D57 test. The
boot predicate is only a momentary sample, so it cannot fully exclude a later
D57 dropout.

Ranking after the `6F00h` physical run:

1. **The wrapper control-flow pattern**, especially returning from the low-ROM
   `CALL 07A9h` into code in `6000h..7FFFh`, or the wrapper's nested stack/CALL
   sequence on this board. Clean simulation and exact readback exclude a
   software encoding error, but this remains the only operation common to all
   four stops.
2. **D57/D11 serial path changing after RUN.** Supported by the independently
   intermittent D57 result, malformed tail bytes, and low tone, but weakened by
   two clean-D57 cold results and by the wrapper-specific repetition.
3. **General DRAM decay.** Initially appeared reduced because T35 survived the
   old idle boundary. The later row-lane capture supersedes this interpretation:
   T35 retained only the row it actually refreshed plus actively touched state.
4. **Exact CS00015 D1 increment fault.** Simulation- and capture-excluded.

Static or dynamic A12 loss in D1, the address buffer, D49 RAM mux, or board
conductor is now inconsistent with both exact high-A12 wrapper readback and the
identical A12-low `6F00h` stop. D2 READY cannot distinguish opcode fetch from
data read, and `6F00h` and `7F00h` both have A10=1 and therefore occupy D2's
same always-wait class. A broader `6000h..7FFFh` RAM-execution effect remains
possible; A12 itself is no longer the discriminator.

## Direct `4000h` register result, 2026-08-10

The next cold run removed the refresh wrapper entirely. All boot predicates,
including D57, passed; verified-return passed; and the paired timebase measured
1.703357 MHz. The 81-byte target was uploaded in three independently exact
readback-verified chunks. A direct RUN at `4000h` acknowledged and returned in
47.981 ms with no replay. This rules out the wrapper as a prerequisite for the
fault.

The result marker and completion byte were intact, but three of five words
were wrong:

| Operation | Expected | Observed |
| --- | --- | --- |
| `INX B`, `0FFFh` | `1000h` | `5555h` (result slot unchanged) |
| `INX D`, `1A00h` | `1A01h` | `1A01h` |
| `INX H`, `5A00h` | `5A01h` | `5555h` (result slot unchanged) |
| `INX SP`, `9A00h` | `9A01h` | `2020h` |
| `DAD D`, `1A00h+1` | `1A01h` | `1A01h` |

This is not the exact CS00015 D1 signature, which is
`1000,0A01,4A01,8A01,1A01`. It is also not evidence for one DRAM data package:
comparing the six wrong result bytes produces aggregate XOR mask `FF`, with
both 1-to-0 and 0-to-1 differences. Some bad words may represent skipped or
misexecuted `SHLD`, rather than individual corrupt data bits.

The drawing closes the populated bank's bit-lane mapping:

| Data bit | DRAM |
| --- | --- |
| DB0 | D84 |
| DB1 | D85 |
| DB2 | D86 |
| DB3 | D87 |
| DB4 | D88 |
| DB5 | D89 |
| DB6 | D90 |
| DB7 | D91 |

This mapping permits a package candidate only when repeated known-pattern
readbacks show a stable single-bit mask. Alternating `00/FF/AA/55`, walking-one,
and walking-zero patterns can distinguish stuck-low, stuck-high, and
intermittent lanes. Errors spanning many bits or whole bytes instead implicate
shared RAS/CAS/write/refresh/address timing and must not be blamed on eight
packages at once.

The next CPU discriminator should use separate one-chunk programs that return
each INX result byte directly in A. That removes the result-buffer stores,
avoids multi-chunk target aging, and retains the loader's protocol-level RETURN
evidence.

The host-driven lane test is now available. It writes four 32-byte patterns at
`4D00h`, verifies each write, leaves T35 refreshing for six seconds, then READs
the exact bytes and reports per-direction mismatch counts with the D84-D91
mapping. It executes no test code from RAM:

```sh
python3 spinoffs/jukuravi/batch.py --port /dev/ttyUSB0 --rom t35 \
  --only-ram-lanes --ram-lane-address 4D00 --ram-lane-hold-ms 6000 \
  --log-dir spinoffs/jukuravi/sessions/cs00024-t35-ram-lanes-physical
```

The test is destructive only to its 32-byte scratch range. The original T35
cosim pass used the now-corrected high-byte row model and is not valid evidence.

Evidence:
`sessions/cs00024-t35-increment-direct-physical/20260810T155952.521638Z.*`.

## T35 row-lane capture and T36 correction, 2026-08-10

The completed six-second lane capture is
`sessions/cs00024-t35-ram-lanes-physical/20260810T161602.033997Z.json`.
Immediate write verification passed for zero, one, and alternating patterns.
The CRC-valid delayed reads then showed:

- zeros: 14/32 bad bytes, predominantly `00 -> FF`, across every data lane;
- ones: three bad bytes, XOR `15`, affecting DB0/DB2/DB4 once each;
- alternating: 28/32 bad bytes, predominantly whole-byte inversions, across
  every data lane;
- the loader stopped before the walking pattern could begin.

This is a shared row-refresh failure, not evidence that all eight DRAM packages
failed independently. The row structure is particularly decisive: scratch
offset is also CPU A0..A6, and offset zero survived while many other offsets
decayed.

The drawings and manufacturer contract explain it. D48/D49 select CPU
BA0..BA7 onto MA0..MA7 during the populated-bank D53 Y0 `/RAS` phase; later
`/CAS` selects the upper address byte. MK4564-class DRAM requires 128 refresh
cycles per 2 ms and does not use pin 9/MA7 for refresh. Thus physical row is
CPU address bits A0..A6. T35's `INR H` loop holds those bits at zero and
refreshes one row 128 times.

Sources: [`kicad/juku.board.json`](../../kicad/juku.board.json), the vendored
[`MK4564 datasheet`](../../ref/datasheets/mk4564-64kx1-dram.pdf), and the
[1984 Mostek data book](https://www.bitsavers.org/components/mostek/_dataBooks/1984_Mostek.pdf).

T36 (`1E/C617`, SHA256
`32264641836ce914a0fc706c916e2847d542d83b05d6737f1d6272b76d78dedb`)
changes only the physical sweep axis: `4000h..407Fh` via `INR L`. Corrected
cosim models row as `address & 7Fh`; T36 covers all 128 rows inside the decay
window while exact T35, armed at the same `07A9h` entry, decays without full
coverage. T36 was subsequently programmed and physically exercised as recorded
below.

The measured 1.70–1.71 MHz values are effective RAM-loop throughput including
READY waits. They do not establish a low CPU oscillator; the measured
approximately 990 Hz startup tone is consistent with the nominal 1 kHz PIT
programming.

## T36 programming and first physical run, 2026-08-10

The exact T36 artifact was
`firmware/dos/T36HOST.BIN`, ROM `1E/C617`, SHA256
`32264641836ce914a0fc706c916e2847d542d83b05d6737f1d6272b76d78dedb`.
The first AT28C64B attempt stopped safely at the first differing byte,
address `000Ah`: three SDP attempts continued to read T35 byte `0E` instead
of T36 byte `CB`. The writer reported zero changed bytes, ten unchanged bytes,
skipped post-write verification, and shut VCC/VPP down. That chip was not
treated as T36.

A replacement 28C64 accepted T36. Willem programmed 3,177 bytes, skipped
5,015 already matching bytes, reported no retry or late byte, verified all
8,192 bytes internally, and shut VCC/VPP down safely. The one fresh full read
matched the exact source SHA256 above. The controlled programmer evidence is
in the sibling `dosravi` session
`at28c64-t36-chip2-write-20260810`; the failed first attempt is retained as
`at28c64-t36-write-20260810`.

The physical host capture is
`sessions/cs00024-t36-full-physical/20260810T174121.361256Z.json` plus its raw
RX/TX files. T36 identified itself exactly as `1E/C617`. Its boot bitmap was
fully clean: PIC, PPI, D54, D55, D57, `4000h` RAM, and `C000h` RAM all passed.
The native one-vote PROBE and verified upload/CALL/RET passed. The paired
refresh-safe timebase measured 1.702797 MHz effective execution rate. Every
completed host probe passed:

- A12 write map;
- LHLD classes;
- instruction classes;
- READY classes;
- A12 boundary;
- direct CPU increment registers.

This removes the earlier T35-era wrong INX result as a persistent CPU finding.
Under T36 refresh, CS00024 executed the same discriminator correctly. It also
strengthens the conclusion that neither a static A12 fault nor a D55 failure
explains this board.

The requested wire-forensic 32 KiB sweep proved more expensive than its old
documentation implied. At 2400 baud each 32-byte LOAD and its independent
READ verification are bit-symbol encoded. The zero write nevertheless
completed all 1,024 chunks over `4000h..BFFFh`: 32,768 bytes loaded, 32,768
bytes immediately read back exactly, zero store retries, and no duplicate
result frames. T36 then kept refresh enabled for the six-second hold.

The final delayed READ was deliberately interrupted after the projected
four-pattern runtime grew to roughly 16 hours. The preserved prefix is still
strong bounded evidence: 54 consecutive 32-byte reads, `4000h..46BFh`, all
returned zero. Those 1,728 addresses contain every physical MA0..MA6 row 13 or
14 times. The unobserved `46C0h..BFFFh` suffix and the one/checkerboard/address
wire patterns did **not** pass or fail; they were not read. Recover the exact
counts from the immutable JSON with:

```sh
python3 scripts/analyze_jukuravi_partial_full_ram.py \
  spinoffs/jukuravi/sessions/cs00024-t36-full-physical/\
20260810T174121.361256Z.json --json
```

The replacement routine path is `--local-full-ram-sweep`. It uploads a
792-byte cooperative test at `4000h` to cover `5000h..BFFFh`, relocates it to
`B000h` to cover `4000h..AFFFh`, refreshes every 128 tested bytes, and returns
compact mismatch/XOR/first-address evidence. The two ranges overlap, but their
union is exactly the full 32 KiB and both code homes are tested by the opposite
stage. Four-pattern decay-enabled simulation passes. This changes only the
host tooling; the physically programmed T36 image remains exact.

## T36 complete local RAM and D57 result, 2026-08-10/11

The replacement run completed in 45 minutes. Its immutable capture is
`sessions/cs00024-t36-local-full-physical/20260810T205728.130960Z.json`
with the matching raw RX/TX files. Exact T36 `1E/C617` booted with a fully
clean bitmap. Native one-vote PROBE, verified upload/CALL/RET, all six
CPU/address probes, and `4000h`/`5000h` execution separation passed. The
paired loop measured 1.701558 MHz effective RAM execution rate, stable against
the first T36 run's 1.702797 MHz.

The complete local RAM result passed all four patterns:

| Pattern | Low-resident test | High-resident test | Union result |
| --- | --- | --- | --- |
| zero | `5000h..BFFFh`, 28,672 bytes, zero mismatch | `4000h..AFFFh`, 28,672 bytes, zero mismatch | pass |
| one | same, zero mismatch | same, zero mismatch | pass |
| checkerboard | same, zero mismatch | same, zero mismatch | pass |
| address-XOR | same, zero mismatch | same, zero mismatch | pass |

Every fill and verify refreshed after 128 tested bytes, and every verify
followed a six-second refresh-on hold. Aggregate XOR was `00` for every stage
and no D84--D91 package candidate remained. The test therefore proves the full
32 KiB array and every data lane under T36 refresh; it is not a six-second
unrefreshed-retention claim. It supersedes the first run's bounded 1,728-byte
delayed prefix as the routine four-pattern physical result.

The parser-aging sweep passed a 6 ms delay after every physical symbol,
echoing the exact 16-byte cookie and recovering CONFIG in 1.298094 seconds.
At 12 ms per symbol the ROM returned outer-frame `bad_crc`, then the short
recovery CONFIG timed out; the complete point took 2.528204 seconds. T36
refresh remained active throughout each receive wait. This is therefore not a
12 ms RAM hold or positive DRAM-decay result. Later uploads and readbacks
recovered and remained exact. Across 282 verified chunks in the session,
sixteen LOADs and two readbacks needed a bounded retry, but all completed,
there were zero store retries, and the maximum was three attempts. The
remaining finding is a serial/parser timing margin.

The final legacy raw D57 operation uploaded and read back exactly, returned in
0.127933 seconds, and then repeated one stable channel-specific result eight
times:

```text
D57R A5 01 08 00
FD 3D  FC 3C  99 99    ; repeated eight times
```

Channels 0 and 1 passed their fast discriminator. The original channel-2
failure interpretation is superseded: the exact E3 drawing shows D57.18/CLK2
is active-low `/VER RTR` from D55.13 at about 49.92 Hz, while D57.9/CLK0 alone
uses D103.11's 1.23 MHz source. The legacy probe waited only microseconds and
T36 did not arm the raster, so its `99/99` reads occurred before a guaranteed
CLK2 edge. They are retained raw evidence, not proof of a D57 fault.

The corrected `D57S` probe arms the exact Ekta raster and waits 64 refresh
sweeps (about 79 ms) after each channel-2 write. Its CS00015 positive control
passed all eight repetitions with `FD/3D FC/3C FE/3E`, validating both D57
channel 2 and the D55.13 → D57.18 `/VER RTR` path there. CS00024 must run this
corrected probe before any socket, board-path, or package localization.

The exact EktaSoft 3.7 ROM does use the channel: offsets `01FCh..020Dh` write
control `B0h`, followed by `FFh,FFh` to port `1Ah`. The immediate bench action
is `batch.py --only-d57` with the corrected source. Only a corrected failure
justifies tracing D55.13 to D57.18, verifying pin 16 high, observing pin 17
while reprogramming, and then considering a controlled PIT substitution.

The consolidated evidence, primary-source research, simulator boundaries, and
ranked diagnosis are in
[`../../docs/cs00024-t36-diagnosis.md`](../../docs/cs00024-t36-diagnosis.md).
