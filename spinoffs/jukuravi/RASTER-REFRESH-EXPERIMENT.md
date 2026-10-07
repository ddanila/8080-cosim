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

Diagnostic firmware can program the raster: the shared RAM-diagnostic builder
calls `emit_video_pit_init`, which emits the Ekta D54/D55 sequence. Later PIT
tests can change that state. Consequently, `--arm none` means no additional
raster writes by this experiment; it does not disable timing established by
boot or prove that video-slot refresh is absent. The actual shared-DRAM
video-slot schedule remains an open
[hardware boundary](../../docs/video-slot-timing-audit.md).

The CS00024 T34 holds showed decay after 5–17 s, while CS00015 survived
longer diagnostic idles. That contrast alone does not distinguish ineffective
refresh from natural retention differences. The controlled comparison below
tests whether explicitly replaying the raster setup changes retention.

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
`SYNC_B` boundary with an unresolved consumer, and its legacy channel-2 result does not establish a fault. Use the corrected
D57S probe described in [the T36 diagnosis](../../docs/cs00024-t36-diagnosis.md)
to qualify that path before attributing a retention failure to it.

Snippet construction, exact-byte extraction, and the row accounting live in
[`raster.py`](raster.py) and are guarded by
[`../../tests/jukuravi_raster_retention_test.py`](../../tests/jukuravi_raster_retention_test.py).
The cosim guard checks the short-hold staged flow through both entry paths.
Its short-decay-deadline control requires `no_return` or `decayed`, but does
not separately establish that the hold executed: `no_return` also covers
upload and verification failures. The flat model implements no video-slot
refresh and cannot qualify the physical raster's effect on retention.

## Stages

Run one stage per invocation and RESET the board between stages. For the default cold-diagnostic entry, fit the exact T36 firmware expected
by the runner (version `1Eh`, CRC16 `C617h`). The alternate entry requires
the archived Ekta4401 remix with its T36 resident engine: start
from its monitor and use `--attach-loader`; type `J`
once without Enter when the runner asks. Attach mode assumes a one-vote
bootstrap; it does not check a cold-boot ROM identity, so an arbitrary API-v2
loader is not a qualified substitute. The marker, arm snippet, hold code,
readback, and verdict are identical after entry. A stage that decays may leave
the loader unrecoverable until RESET — that outcome *is* the measurement,
recorded in the JSON capture. Run the commands below from the repository root
with Python 3 on Linux or macOS and permission to access the serial device;
the host uses the POSIX `termios`/`fcntl` backend.

```sh
# Control: no additional raster writes; existing timing is retained.
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
```

For the remaining CS00015 stages, use the same command with `--arm raster`
or `--arm raster-syncb` and a distinct `--log-dir` for each stage. RESET and
enter `J` between invocations.

On macOS select the adapter's actual `cu.*` node with `--port`; see
[the macOS acceptance record](MACOS-BENCH.md). The default 25 s hold exceeds
the recorded 5–17 s CS00024 decay interval; `--hold-seconds` adjusts it, and the
loop is sized from the measured effective rate (`--effective-mhz`,
default 1.702). Duration is rounded to the nearest outer-loop count and
clamped to 1–65535 outer loops. The JSON's `hold_seconds_estimated` describes
the sized duration, which can differ from the request. `hold_seconds_measured` also includes host upload, verification
and RUN/RETURN transport; it is not a direct measurement of the unrefreshed
interval.

## Pre-registered interpretation

| Stage | Survives | Decays / no RETURN |
| --- | --- | --- |
| `none` (control) | Measures retention without the explicit raster writes; survival may reflect natural retention or an already active refresh source | Establishes a decay-consistent baseline only after entry, transport and hold duration are validated |
| `raster` | A reproducible improvement over `none` supports raster-dependent refresh; it does not directly measure `/RAS` or qualify every refresh path | Arming alone did not preserve the sampled contents; verify actual raster outputs and repeat the cross-board control before locating a hardware fault |
| `raster-syncb` | Improvement over a failing `raster` stage supports a role for channel-2 programming | Does not distinguish an ineffective `SYNC_B` path from another refresh or transport failure; use the corrected D57S probe and cross-board control |

The runner's JSON verdicts have these limits:

| Verdict | Meaning |
| --- | --- |
| `pass` | RETURN with `A=52h` and byte-exact marker and hold-image readbacks |
| `decayed` | Both readbacks completed, but at least one byte differs; the per-row map records the differences |
| `no_return` | A host session error occurred during the hold upload/verification/RUN operation; execution of the hold is not established by this label alone |
| `incomplete` | The stage did not reach a verdict, for example because entry failed, RETURN had the wrong A, or later readback failed |

Exit status is `0` only for `pass` without a session error, `1` for other
outcomes or transport failures, and `130` for an operator interrupt. Argument
parsing errors exit `2`. Hold duration and effective CPU rate must be positive;
zero values fail before opening the transport, with exit `1` and no session log.
Read the session error and operation evidence alongside
the verdict. A mismatch
or missing RETURN alone does not prove DRAM decay: exclude setup and transport
failures, verify that the hold ran, and compare against the control stage
before drawing a raster conclusion. Whole-evidence inversion resembling the
cosim decay model is decay-consistent, not a unique physical signature.

## Reproduction

The static check needs Python 3 on a POSIX system: it imports `pty` and `tty`
even when no simulator is requested. The full Linux gate also needs Bash and
a C11 compiler (`CC`, default `cc`).

```sh
# Static snippet-exactness guards (no simulator):
python3 tests/jukuravi_raster_retention_test.py

# Full deterministic flow through cosim (Linux; part of jukuravi_t36_check):
sync/jukuravi_t36_check.sh
```
