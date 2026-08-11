# CS00024 T36 desk diagnosis

Status date: 2026-08-11.

Status: **COMPLETE 32 KIB RAM PROOF UNDER T36 REFRESH; LEGACY D57 CHANNEL-2
CAPTURE NEEDS THE CORRECTED `/VER RTR` RERUN; 12 MS LINK MARGIN IS SEPARATE**.

This note consolidates the completed T36 physical capture, the Juku drawings,
the exact EktaSoft 3.7 ROM, deterministic simulation, and contemporary
manufacturer documentation. It intentionally separates three effects that
looked related during live work but are not supported as one fault.

## Conclusions

1. There is currently **no evidence for a bad D84--D91 DRAM package** on
   CS00024. With T36 software refresh active, every byte of `4000h..BFFFh`
   passed zero, one, checkerboard, and address-XOR patterns after a six-second
   refresh-on hold. Both complementary resident-code locations passed, all
   eight data lanes passed, and no candidate package remained.
2. The earlier T34/T35 decay is explained by the diagnostic environment:
   T34 supplied no idle software refresh, and T35 accidentally refreshed only
   physical row zero. T36 corrected the address axis and survives the same
   deterministic decay model. This does not prove the normal EktaSoft/video
   refresh schedule; it proves the RAM array and Juku RAM-cycle path work when
   all rows are serviced correctly.
3. The recorded D57 `99/99` channel-2 bytes are repeatable raw evidence but
   **not a valid fault discriminator**. The old probe waited only microseconds,
   while the exact E3 drawing shows CLK2 is `/VER RTR` at about 49.92 Hz and
   T36 had not armed the raster. A corrected probe arms the raster and waits
   about 79 ms; it passes 8/8 on CS00015. CS00024 needs that same rerun before
   any D57 path or package conclusion.
4. The 12 ms parser-aging point is a separate serial/parser margin finding.
   It is not a 12 ms unrefreshed RAM hold: T36 refresh remained enabled while
   the host delayed every physical symbol, stretching one 16-byte cookie to
   2.528 seconds. The ROM reported an outer-frame bad CRC, and later exact
   upload/readback and execution recovered.

## Immutable physical evidence

The complete session is
[`20260810T205728.130960Z.json`](../spinoffs/jukuravi/sessions/cs00024-t36-local-full-physical/20260810T205728.130960Z.json)
with its matching raw RX/TX streams. It ran from `20:57:28Z` to `21:42:28Z`,
decoded 746 frames, received 165,161 bytes, and transmitted 139,550 bytes.
The exact ROM identity was T36 `1E/C617`.

| Evidence | Physical result | Supported claim |
| --- | --- | --- |
| Cold boot | PIC, PPI, D54, D55, D57, RAM4000, RAMC000 all clean | Short boot predicates passed at that instant |
| Native PROBE and verified CALL/RET | pass | Loader, both serial directions, RAM upload/readback, stack and return path operational |
| Paired CPU loop | 1.701558 MHz effective, 1,078,000 T-state delta in 0.633537 s | Stable RAM-loop throughput; not a crystal measurement |
| Six CPU/address probes | all pass | No persistent CS00015-style increment/A12 fault on this board |
| Local full-RAM sweep | four patterns, eight stage results, all pass | Complete 32 KiB union, zero mismatch, XOR `00`, no D84--D91 candidate |
| Execution separation | `4000h`/`5000h` pass, marker `50` returned | Both independently stored programs remained distinct and executable |
| Parser-aging, 6 ms/symbol | exact 16-byte echo and recovery in 1.298094 s | The long-cookie path still works at this margin point |
| Parser-aging, 12 ms/symbol | ROM `bad_crc`; recovery CONFIG timeout in 2.528204 s | A length/timing-dependent transport/parser boundary remains |
| Legacy raw D57 | ch0 `FD/3D`, ch1 `FC/3C`, ch2 `99/99`, repeated eight times | Channels 0/1 passed; channel-2 bytes were sampled before a guaranteed `/VER RTR` edge and do not diagnose a fault |

The local test used a 792-byte low-resident program to test
`5000h..BFFFh` and the same program relocated to `B000h` to test
`4000h..AFFFh`. Each stage touched 28,672 bytes and called the T36 refresh
entry every 128 tested bytes during both fill and verify. The overlap is
intentional; the union is exactly `4000h..BFFFh`, and each code home is tested
by the opposite stage. The six-second delay was **refresh-on**, so this proves
the refresh solution and RAM path rather than six-second raw cell retention.

Across all recorded uploads, 282 verified chunks carried 8,642 bytes. Sixteen
LOAD chunks and two independent readbacks needed more than one transaction,
but all finished exact, no chunk needed a store retry, and the maximum was
three attempts. That pattern, plus the explicit 12 ms outer-CRC rejection,
supports a recoverable link/parser margin issue rather than failed RAM writes.
The exact host/PTTY regression now uses the same 6 and 12 ms symbol guards
under deterministic DRAM decay; both points pass and the model observes all
128 rows inside the retention deadline. Thus neither correct T36 refresh nor
the guard delay by itself reproduces the physical 12 ms failure. The remaining
unmodeled variables are the real 8251/baud path, analog link, and ROM/host
timing at physical speed.

## Refresh interpretation

The Juku drawing routes CPU BA0..BA7 through D48/D49 to MA0..MA7 during the
populated-bank RAS phase. The MK4564 manufacturer contract requires a memory
cycle at every one of 128 row addresses inside 2 ms, says any normal memory
cycle performs refresh, and specifies A0--A6 for RAS-only refresh. Pin 9/A7 is
not required. The exact implications are:

- T35's `4000h,4100h,...,BF00h` reads kept A0--A6 at zero and refreshed one
  physical row 128 times;
- T36's `4000h..407Fh` reads enumerate every A0--A6 combination; and
- the corrected deterministic model groups decay by `address & 7Fh`, where
  exact T35 decays and exact T36 covers all rows inside the same deadline.

Primary source: [Mostek MK4564-12 data sheet](https://minuszerodegrees.net/memory/4164/datasheet_MK4564-12.pdf).
The repository keeps the exact reviewed copy at
[`ref/datasheets/mk4564-64kx1-dram.pdf`](../ref/datasheets/mk4564-64kx1-dram.pdf).

The completed physical result demotes these diagnoses:

- a stable stuck-low or stuck-high D84--D91 data lane;
- one consistently weak package under the tested patterns and conditions;
- a missing physical refresh-row address under T36;
- a broad row/column alias detectable by the address-XOR pattern; and
- the earlier persistent CPU/A12 hypothesis.

It does not yet validate normal-ROM refresh coverage, operation over
temperature, or signal integrity at the DRAM pins. Contemporary memory-system
guidance emphasizes that shared RAS/CAS/address capacitance, trace inductance,
overshoot/undershoot, switching current, and local decoupling can create
intermittent common-path errors even when individual data lanes are healthy.
Those are sensible oscilloscope checks only if failures return; they are not a
reason to replace all eight RAMs now. Primary background:
[National Semiconductor AN-305, in the 1986 Memory Support handbook](https://www.bitsavers.org/components/national/_dataBooks/1986_National_APPS_Handbook_Vol_2_Memory_Support.pdf)
and the [Hitachi 1987 IC Memories data book](https://www.bitsavers.org/components/hitachi/_dataBooks/1987_M11_Hitachi_IC_Memories_Data_Book.pdf).

## D57 channel-2 timing correction

The legacy expanded test selected MSB-only Mode 0, wrote `FFh`, waited a few
hundred microseconds, latched and read, then repeated with `3Fh`. It called T36
refresh before each sample. The CS00024 physical result was:

```text
D57R A5 01 08 00
FD 3D  FC 3C  99 99
FD 3D  FC 3C  99 99
... the same six bytes for all eight repetitions
```

The exact E3 drawing and the board photograph correct the topology used in the
first analysis:

- D57 pin 9/CLK0 receives `1,23M` tag 13 from D103.11.
- D57 pin 15/CLK1 receives `2M` tag 8.
- D57 pin 18/CLK2 receives active-low `/VER RTR` tag 2 from D55 pin 13/OUT1,
  approximately 49.92 Hz under the Ekta raster settings.
- D57 pin 17/OUT2 is the separately traced `SYNC_B` boundary.

Intel's 8253 contract says a newly written count is not transferred until the
write is followed by a rising and falling clock edge; a read before that edge
may be invalid. The legacy delay was far shorter than one `/VER RTR` period,
and T36 did not program D54/D55 into the normal Ekta raster. Consequently the
channel-2 `99/99` bytes do not establish whether D57 accepted either count.
They remain preserved because the capture itself is valid; its interpretation
was wrong.

The corrected `D57S` v2 probe replays the exact 14-write Ekta D54/D55 raster
sequence and waits 64 T36 refresh sweeps, about 79 ms or roughly four vertical
retrace periods, after each channel-2 count write. On CS00015 it returned this
record in all eight repetitions:

```text
D57S A5 02 08 40
FD 3D  FC 3C  FE 3E
```

The complete API-v2 upload/readback/RUN session had no transport mismatch.
This is a physical positive control for D57 channel 2 and the D55.13 →
D57.18 `/VER RTR` path. The simulator and `batch.py` now validate channel 2
only for `D57S` v2; they retain but do not score legacy `D57R` v1 channel-2
bytes. The exact-signature fault injection remains useful for testing the
software discriminator after valid timing, not as proof that CS00024 has that
fault. Primary source: [Intel 1979 Peripheral Design Handbook, 8253 section](https://www.bitsavers.org/components/intel/_dataBooks/1979_Intel_Peripheral_Design_Handbook.pdf).

The correction is already present in the authoritative board JSON and HDL.
It deliberately reopens one replica-layout gate: the current source and routed
KiCad PCBs still assign D57.18 to `CLK_123M`. Their copper must be rerouted and
reviewed against `/VER RTR` before fabrication; the generated bring-up report
lists the mismatch rather than hiding it behind a pad-only edit.

The exact `ekta37.bin` also uses this channel. At ROM offsets `01FCh..020Dh`
it writes D57 control `B0h`, then sends `FFh,FFh` to port `1Ah`. An executed
cosim trace observes those writes at PCs `0200h`, `020Ch`, and `020Eh`.
Therefore the fault is relevant to the stock initialization even though
`SYNC_B`'s final consumer is still an explicit drawing boundary.

## Ranked diagnosis and next physical checks

1. **Corrected D57 rerun — required before electrical localization.** Run the
   current `batch.py --only-d57` on CS00024. A pass clears the old `99/99`
   interpretation. A repeatable corrected failure would justify comparing
   D57.18 `/VER RTR` with D55.13, checking D57.16/GATE2, observing D57.17
   `SYNC_B`, and only then distinguishing socket/path from package.
2. **Normal-raster DRAM refresh — still open.** Run the pre-registered
   `none`, `raster`, and if needed `raster-syncb` retention stages, with
   CS00015 as the cross-board control. This is independent of the completed
   RAM-array proof under T36 software refresh.
3. **Serial/parser timing margin — real but secondary.** The 12 ms/symbol
   rejection and sporadic bounded retries merit protocol timing work, but do
   not explain the old T35 row pattern.
4. **DRAM common timing/power issue — currently low priority.** If normal-ROM
   or hot/cold failures recur, scope populated-bank `/RAS` at D53.15 through
   R49, shared `/CAS` from D36.11, MA0--MA6, and supply/ground at D84--D91.
   Preserve simultaneous traces before replacing RAM packages.

There is no justified instruction to replace D84--D91, D55, or D57 from desk
evidence alone. In particular, do not compare D57 pins 18 and 9 as though they
were the same clock: they are `/VER RTR` and 1.23 MHz respectively. The next
bench action is the corrected D57 software rerun; pin-level work follows only
if that valid discriminator fails.

A prepared, not yet executed host-driven experiment can additionally decide
whether the board's normal video-slot refresh works at all: it replays the
exact EktaSoft D54/D55 raster programming from the T36 loader and holds RAM
unrefreshed past the proven decay boundary. Its protocol, mechanism, and
pre-registered interpretation are in
[`../spinoffs/jukuravi/RASTER-REFRESH-EXPERIMENT.md`](../spinoffs/jukuravi/RASTER-REFRESH-EXPERIMENT.md).
Because it needs no scope and no ROM burn, it is a sensible companion to the
D57 pin checks on the same bench visit; its `raster-syncb` stage also
physically probes whether `SYNC_B` participates in refresh gating.

## Reproduction

```sh
# Exact firmware, drawings, physical-session, decay and D57 signature guards
sync/jukuravi_t36_check.sh

# Focused physical D57 follow-up after starting the host, then one RESET
python3 spinoffs/jukuravi/batch.py --port /dev/ttyUSB0 --rom t36 \
  --only-d57 --log-dir spinoffs/jukuravi/sessions/cs00024-t36-d57-followup
```

The full physical claims are pinned by
[`jukuravi_t36_physical_sessions_test.py`](../tests/jukuravi_t36_physical_sessions_test.py).
