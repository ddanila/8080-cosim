# Video-slot refresh experiment (pre-registered)

Status: **PREPARED, NOT PHYSICALLY QUALIFIED.** No completed physical stage
is recorded for this protocol. The commands require the firmware setup below.

## Question

In a normal Juku, DRAM refresh is a hardware side effect of the display:
the D44-D47 video counters read the shared DRAM through the D48-D52 mux
during the 1 MHz video slots, and every video read is an ordinary memory
cycle that refreshes its MK4564 row. EktaSoft contains **no CPU
software-refresh loop**; its only contribution is programming the D54/D55
raster PITs once at boot (`ekta37` offsets `01D4h..0221h`, decoded in
[`../../docs/video-pit-timing.md`](../../docs/video-pit-timing.md)).

The diagnostic ROMs never program that raster. Whether video-slot `/RAS`
cycles happen anyway — without the PIT-driven sync/blank chain — is exactly
the open "shared-DRAM video-slot schedule" boundary
([`../../docs/video-slot-timing-audit.md`](../../docs/video-slot-timing-audit.md)).
The CS00024 T34 holds showed decay after 5–17 s, while CS00015 survived
longer diagnostic idles. That contrast alone does not distinguish missing
refresh from natural retention differences. The controlled raster/no-raster
comparison below tests whether arming the timing chain changes retention.

This experiment arms the raster from the T36 loader and measures whether
that alone preserves RAM through an unrefreshed hold. Once the required
service firmware is fitted, the experiment uploads snippets and requires no
additional ROM programming. Initial retention measurements need no scope;
fault localization may require waveform capture.

## Mechanism

`--loader-refresh disable` cannot create the unrefreshed window: the
loader's fail-safe idle transport reset re-enables refresh after eight
bounded quiet receive periods. Instead the window is an **uploaded RUN
snippet**: arbitrary RUN code is never preempted, so while the hold snippet
executes, T36's software refresh provably does not. The hold is a
register-only busy wait whose instruction fetches keep only physical rows
`40h..54h` alive; every other row carries known, untouched content:

| Range | Rows (`address & 7Fh`) | Content |
| --- | --- | --- |
| `4D00h..4D3Fh` | `00h..3Fh` | 64-byte marker (retention.py pattern + complement) |
| `4040h..4054h` | `40h..54h` | hold code — **live, excluded from evidence** |
| `4055h..407Fh` | `55h..7Fh` | known fill law |
| `4080h..40BFh` | `00h..3Fh` | known fill law (second copy of those rows) |

All 128 rows are accounted for; 107 carry unrefreshed evidence.

The arm snippet replays the **exact** EktaSoft D54/D55 write sequence — the
14 `MVI A/OUT` pairs to ports `10h..17h` in ROM order (64 µs lines, 313-line
frames, both blank one-shots). All six vendored EktaSoft images boot with
these byte-identical raster values, and the Monitor family programs the
same timing chain with equivalent values (312-line BCD frame count instead
of 313 binary), independently corroborating them; see
[`../../docs/ektasoft-rombios-lineage.md`](../../docs/ektasoft-rombios-lineage.md). The D57 writes in the same ROM window are
deliberately excluded: channel 0 clocks the diagnostic USART and channel 1
drives the speaker, so replaying them could kill the live link. The optional
`raster-syncb` variant adds only EktaSoft's channel-2 write (`B0h` control,
`FFFFh` count, preserving the bare-OUT reuse): D57 `OUT2` is the traced
`SYNC_B` boundary with an unresolved consumer, and CS00024's one confirmed
legacy capture was on that channel. That `99/99` result is no longer a
confirmed fault: the old probe did not arm the raster or wait for D57 CLK2's
approximately 49.92 Hz `/VER RTR` source. If corrected testing later finds a
real `SYNC_B` fault, it and broken normal-mode refresh could still be one
fault.

Snippet construction, exact-byte extraction, and the row accounting live in
[`raster.py`](raster.py) and are guarded by
[`../../tests/jukuravi_raster_retention_test.py`](../../tests/jukuravi_raster_retention_test.py).
Deterministic cosim proves the staged flow end to end and proves the
negative control (a hold crossing the decay deadline yields the no-return
classification). The flat model implements no video-slot refresh, so
simulation deliberately cannot pass the armed long hold; only hardware can.

## Stages

One invocation = one cold loader entry = one stage. Hardware RESET between
stages. For the default cold-diagnostic entry, fit the exact T36 firmware expected
by the runner (version `1Eh`, CRC16 `C617h`). The alternate entry requires
an API-v2 service loader, tested with the archived Ekta4401 remix: start
from its monitor and use `--attach-loader`; type `J`
once without Enter when the runner asks. The marker, arm snippet, hold code,
readback, and verdict are identical after entry. A stage that decays may leave
the loader unrecoverable until RESET — that outcome *is* the measurement,
recorded in the JSON capture.

```sh
# Control: no raster. CS00024 prediction: decay (validates sensitivity).
python3 spinoffs/jukuravi/raster_retention.py --port /dev/ttyUSB0 \
  --arm none --log-dir spinoffs/jukuravi/sessions/cs00024-raster-control

# Raster armed: the question.
python3 spinoffs/jukuravi/raster_retention.py --port /dev/ttyUSB0 \
  --arm raster --log-dir spinoffs/jukuravi/sessions/cs00024-raster-armed

# Raster + SYNC_B armed: only if the armed stage still decays.
python3 spinoffs/jukuravi/raster_retention.py --port /dev/ttyUSB0 \
  --arm raster-syncb --log-dir spinoffs/jukuravi/sessions/cs00024-raster-syncb
```

CS00015 cross-board control requires the Ekta4401 service setup (RESET and
`J` between invocations). Its currently fitted network ROM is a separate
configuration; see [the service record](../../docs/cs00015-service-record.md).

```sh
python3 spinoffs/jukuravi/raster_retention.py --port /dev/ttyUSB0 \
  --attach-loader --arm none \
  --log-dir spinoffs/jukuravi/sessions/cs00015-ekta4401-raster-control

python3 spinoffs/jukuravi/raster_retention.py --port /dev/ttyUSB0 \
  --attach-loader --arm raster \
  --log-dir spinoffs/jukuravi/sessions/cs00015-ekta4401-raster-armed

python3 spinoffs/jukuravi/raster_retention.py --port /dev/ttyUSB0 \
  --attach-loader --arm raster-syncb \
  --log-dir spinoffs/jukuravi/sessions/cs00015-ekta4401-raster-syncb
```

On the macOS bench use `--port /dev/cu.usbserial-0001`
([`MACOS-BENCH.md`](MACOS-BENCH.md)). Run the same three stages on CS00015
as the cross-board control when practical. The default 25 s hold sits past
the proven 5-17 s CS00024 boundary; `--hold-seconds` adjusts it, and the
loop is sized from the measured effective rate (`--effective-mhz`,
default 1.702).

## Pre-registered interpretation

| Stage | Survives | Decays / no RETURN |
| --- | --- | --- |
| `none` (control) | Measures retention without the explicit raster writes; survival may reflect natural retention or an already active refresh source | Establishes a decay-consistent baseline only after entry, transport and hold duration are validated |
| `raster` | A reproducible improvement over `none` supports raster-dependent refresh; it does not directly measure `/RAS` or qualify every refresh path | Arming alone did not preserve the sampled contents; verify actual raster outputs and repeat the cross-board control before locating a hardware fault |
| `raster-syncb` | Improvement over a failing `raster` stage supports a role for channel-2 programming | Does not distinguish an ineffective `SYNC_B` path from another refresh or transport failure; use the corrected D57S probe and cross-board control |

A `pass` verdict requires RETURN with `A=52h` plus byte-exact marker and
hold-image readbacks. Partial decay (some rows failed) is reported with the
per-row map; whole-evidence inversion resembling the cosim decay model
is decay-consistent. Compare against the control stage before drawing a
raster conclusion. A missing RETURN or transport loss is also classified by
the runner as decay-consistent, but does not itself prove DRAM decay. Capture
setup and serial failures must be excluded before using that outcome as a
hardware diagnosis.

## Reproduction

```sh
# Static snippet-exactness guards (any machine):
python3 tests/jukuravi_raster_retention_test.py

# Full deterministic flow through cosim (Linux; part of jukuravi_t36_check):
sync/jukuravi_t36_check.sh
```
