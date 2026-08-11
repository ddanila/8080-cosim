# Video-slot refresh experiment (pre-registered)

Status: **PREPARED, NOT YET RUN.** This protocol was designed 2026-08-11;
no physical stage below has been executed.

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
That single unknown separates two readings of the recorded CS00024 evidence:

- if video-slot refresh runs regardless of ROM state, then CS00015 surviving
  multi-minute unrefreshed idles means its refresh hardware works, and
  CS00024's 5-17 s T34 decay is a **real refresh-path fault**;
- if video-slot refresh requires the armed raster, the diagnostic
  environment truly had zero refresh on any board, CS00015's survival was
  out-of-spec retention luck, and CS00024's decay was datasheet-permitted.

This experiment arms the raster from the T36 loader and measures whether
that alone preserves RAM through an unrefreshed hold. No ROM burn, no scope.

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
frames, both blank one-shots). Both vendored RomBios lines (3.43m and the
2.43 family) boot with these byte-identical raster values, independently
corroborating them; see
[`../../docs/ektasoft-rombios-lineage.md`](../../docs/ektasoft-rombios-lineage.md). The D57 writes in the same ROM window are
deliberately excluded: channel 0 clocks the diagnostic USART and channel 1
drives the speaker, so replaying them could kill the live link. The optional
`raster-syncb` variant adds only EktaSoft's channel-2 write (`B0h` control,
`FFFFh` count, preserving the bare-OUT reuse): D57 `OUT2` is the traced
`SYNC_B` boundary with an unresolved consumer, and CS00024's one confirmed
fault is that channel. If `SYNC_B` participates in slot gating, the dead
channel 2 and a broken normal-mode refresh could be one fault.

Snippet construction, exact-byte extraction, and the row accounting live in
[`raster.py`](raster.py) and are guarded by
[`../../tests/jukuravi_raster_retention_test.py`](../../tests/jukuravi_raster_retention_test.py).
Deterministic cosim proves the staged flow end to end and proves the
negative control (a hold crossing the decay deadline yields the no-return
classification). The flat model implements no video-slot refresh, so
simulation deliberately cannot pass the armed long hold; only hardware can.

## Stages

One invocation = one cold T36 boot = one stage. Hardware RESET between
stages. A stage that decays may leave the loader unrecoverable until RESET —
that outcome *is* the measurement, recorded in the JSON capture.

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

On the macOS bench use `--port /dev/cu.usbserial-0001`
([`MACOS-BENCH.md`](MACOS-BENCH.md)). Run the same three stages on CS00015
as the cross-board control when practical. The default 25 s hold sits past
the proven 5-17 s CS00024 boundary; `--hold-seconds` adjusts it, and the
loop is sized from the measured effective rate (`--effective-mhz`,
default 1.702).

## Pre-registered interpretation

| Stage | Survives | Decays / no RETURN |
| --- | --- | --- |
| `none` (control) | CS00024: contradicts the recorded T34 boundary — investigate before trusting the run. CS00015: consistent with its long recorded idles; still ambiguous between retention luck and always-on slot refresh | CS00024: expected; confirms sensitivity. CS00015: natural retention is shorter than its recorded idle survivals suggest — favors an active refresh source on CS00015 |
| `raster` | Video-slot refresh works once the raster is armed: the board's refresh hardware is healthy and the diagnostic ROMs simply never armed it. Also closes the slot-schedule question with physical evidence: slots strobe `/RAS` when the raster runs | The armed raster does not refresh this board: a real hardware refresh-path fault upstream of the DRAMs (slot gating, mux enables, or their timing sources) |
| `raster-syncb` | (given `raster` decayed) `SYNC_B` participates in refresh gating — but note CS00024's broken channel 2 may prevent `OUT2` from ever asserting, so a *decay* here does not clear `SYNC_B` | Consistent with either a `SYNC_B` role blocked by the dead channel 2, or `SYNC_B` irrelevance; distinguish on CS00015, whose channel 2 works |

A `pass` verdict requires RETURN with `A=52h` plus byte-exact marker and
hold-image readbacks. Partial decay (some rows failed) is reported with the
per-row map; whole-evidence inversion resembling the cosim decay model
suggests the hold simply crossed natural retention — compare against the
control stage before concluding anything about the raster.

## Reproduction

```sh
# Static snippet-exactness guards (any machine):
python3 tests/jukuravi_raster_retention_test.py

# Full deterministic flow through cosim (Linux; part of jukuravi_t36_check):
sync/jukuravi_t36_check.sh
```
