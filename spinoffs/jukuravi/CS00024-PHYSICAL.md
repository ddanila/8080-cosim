# CS00024 physical evidence

Board: Arvutimuuseum Juku `CS00024`.

The [current diagnosis](../../docs/cs00024-t36-diagnosis.md) owns conclusions
and next bench actions. This record identifies the captures supporting those
conclusions and preserves their measurement limits. Earlier diagnostic bits
and superseded interpretations are not current component diagnoses.

## T31 and D55 supersession

Two cold T31 `1A/72EF` boots returned peripheral bitmap `18` and compact RAM
bitmap `83`. The D55 bit is invalid as a fault discriminator: exact T31 also
produces it on the clean clock-faithful model because it latches the new Mode-0
counts before their required clocks. See the
[D55 audit](../../docs/jukuravi-d55-diagnostic-audit.md).

All capture paths below are relative to this directory. T31 captures are in
`sessions/cs00024-t31-initial/`, `sessions/cs00024-t31-default/`,
`sessions/cs00024-t31-retryfix/` and `sessions/cs00024-t31-attach-resync/`. They preserve the failed PROBE/RESYNC attempts;
no upload occurred.

## T34 cold boots and loader discriminator, 2026-08-09

Exact T34 `1C/A637` passed corrected D55, PIC, PPI, D54 and both compact RAM
windows on four cold boots. Peripheral bitmaps were `00`, then `10` three
times; the historical D57 indication was intermittent.

Seven-vote PROBE failed with strong-parser CRC errors at both 6 and 12 ms
host guards. CONFIG-first followed by a one-vote exact-cookie PROBE passed.
These captures establish a length/time boundary rather than a dead USART:

- `sessions/cs00024-t34-20260809/20260809T055628.869126Z.*`;
- `sessions/cs00024-t34-full/cold-loader-probe/20260809T060236.505488Z.*`;
- `sessions/cs00024-t34-full/cold-loader-probe-g12/20260809T060417.872163Z.*`;
- `sessions/cs00024-t34-full/config-first-v1/20260809T060703.043231Z.*`.

T34 retention tests kept a verified 32-byte marker at `4D00h` exact through
30.912 seconds when read about every 5.15 seconds. Sparse tests instead lost
CONFIG after untouched intervals: an exact read at 5.158 seconds preceded the
45-second target timeout; a zero-guard exact read at 3.423 seconds preceded
the 20-second target timeout. The short boot RAM test therefore does not
qualify idle retention. Captures:

- `sessions/cs00024-t34-retention-cold-physical/20260809T181947.593033Z.*`;
- `sessions/cs00024-t34-retention-sparse-cold-physical/20260809T182357.819924Z.*`;
- `sessions/cs00024-t34-retention-midpoint-g0-cold-physical/20260809T202332.467525Z.*`.

## T35 refresh correction

T35 `1D/45C4` was programmed and read back exactly, SHA256
`ceb55556f11318dea5ef8c36b81f931813a139ce6ba6e07b607318571c6e1274`.
The sibling `dosravi` record is
`sessions/at28c64-t35-write-20260810/session.json`.

T35 initially preserved loader state across an idle reattach, but its reported
128-row geometry was not proof of physical coverage. The six-second lane
capture found 14/32 bad zero bytes, 3/32 bad one bytes and 28/32 bad alternating
bytes after exact immediate verification. Errors spanned the data lanes;
this did not identify an individual D84--D91 package.

| Retained evidence | Scope |
| --- | --- |
| `sessions/cs00024-t35-first-physical/20260810T061734.589060Z.*` and `sessions/cs00024-t35-idle-reattach-physical/20260810T061834.464961Z.*` | Initial boot and surviving loader state, not full-row refresh |
| `tests/jukuravi_t35_physical_sessions_test.py` and its named captures | Four wrapper RUN-ACK/no-RETURN stops, direct `4000h` wrong-register result, and delayed lane corruption |
| `sessions/cs00024-t35-ram-lanes-physical/20260810T161602.033997Z.json` | Delayed known-pattern corruption after immediate verification |

The physical row uses CPU A0..A6: D48/D49 select the low address byte during
RAS, and the [MK4564 contract](../../ref/datasheets/mk4564-64kx1-dram.pdf)
requires 128 rows inside 2 ms. T35's `INR H` sweep held those bits at zero.
T36 changes the sweep to `4000h..407Fh` with `INR L`; the corrected decay
model uses `address & 7Fh`. The old high-byte-row cosim pass does not prove
physical refresh. The [diagnosis](../../docs/cs00024-t36-diagnosis.md#refresh-interpretation)
contains the source and model interpretation.

The earlier wrong-register results and wrapper stops are superseded as
persistent CPU findings by the complete T36 probes below. The measured
1.70–1.71 MHz rates are effective RAM-loop throughput including READY waits,
not CPU oscillator measurements. Detailed session chronology remains in Git
and the retained JSON/raw streams.

## T36 programming and first physical run, 2026-08-10

The exact T36 artifact was
`firmware/dos/T36HOST.BIN`, ROM `1E/C617`, SHA256
`32264641836ce914a0fc706c916e2847d542d83b05d6737f1d6272b76d78dedb`.
A replacement 28C64 was programmed and internally verified across all
8,192 bytes. One fresh full read matched the source SHA256 above. The
programmer record is in the sibling `dosravi` session
`at28c64-t36-chip2-write-20260810`; the unsuccessful first-chip attempt is
retained as `at28c64-t36-write-20260810` and did not establish a T36 image.

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

At 2400 baud each 32-byte LOAD and its independent READ verification in the
wire-forensic sweep are bit-symbol encoded. The zero write
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

The complete local-sweep capture below uses the same programmed T36 image.
Current commands and the cooperative probe contract are in the
[diagnostic guide](README.md).

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

The [current diagnosis](../../docs/cs00024-t36-diagnosis.md#d57-channel-2-timing-correction)
owns the corrected `D57S` probe, CS00015 positive control and source evidence.
Its [next physical checks](../../docs/cs00024-t36-diagnosis.md#ranked-diagnosis-and-next-physical-checks)
require the corrected CS00024 rerun before electrical localization or component
replacement.
