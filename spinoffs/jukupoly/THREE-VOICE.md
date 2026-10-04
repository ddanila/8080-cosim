# JukuPoly: three-voice pin-pulse synthesis

On 2026-08-29, a 163-byte strict-8080 CP/M transient produced three
simultaneous pitched voices through an unmodified Juku speaker on physical
board CS00000.  The final program averaged approximately 10.97 kHz in the
cycle model and was judged clearly audible and musically convincing at the
bench.

This experiment was inspired by shiru8bit's 2024 article
[“Секреты Тима Фоллина, бипер, Спектрум и QChan”][qchan].  It is an independent
Juku implementation, not a port of the article's Z80 code.  In particular,
Juku has a KR580VM80A-compatible CPU and an 8253 channel between software and
the speaker, rather than the Spectrum's directly toggled beeper bit.

[qchan]: https://habr.com/ru/companies/ruvds/articles/843206/

## Project scope

JukuPoly is a standalone experiment under `spinoffs/jukupoly`, using this
repository's strict-8080 assembler, calibrated cycle model, D57 speaker path
and physical evidence conventions. Jukuravi supplied early delivery tooling;
it is not a runtime dependency. The compiled-pattern player, importers and
library are described in [the project overview](README.md).

## Signal generation

D57 channel 1 is programmed through control port `1Bh` as an LSB-only mode-0
one-shot.  Writing a count to data port `19h` immediately drives `SOUND` low;
the independent 2 MHz PIT clock returns it high after the requested count.
Consequently the CPU emits one `OUT`, not an explicit low/write-delay/high
sequence, for each audible impulse.  D57 channel 0 and the serial clock remain
untouched.

Three 16-bit phase accumulators implement A3, C-sharp4, and E4.  Their
increments are held in `BC`, `DE`, and `SP`; the phases occupy the immediate
operands of three self-modifying `LXI H` instructions.  Interrupts are disabled
while `SP` is borrowed. Before the CP/M `RET`, the program restores the saved
stack pointer and executes `EI`; it does not preserve a disabled interrupt
state from entry.

The timeline is deliberately simple:

| Time | Voices |
|---:|---|
| 0–2 s | A3, 220.00 Hz |
| 2–4 s | A3 + C-sharp4, 277.18 Hz |
| 4–9 s | A3 + C-sharp4 + E4, 329.63 Hz |

Transitions count 440, 440, and 1,100 A3 phase overflows. The approximately
2, 4, and 9 second boundaries assume the calibrated effective execution rate;
changes in READY timing also change pitch and elapsed playback time.  Playback deliberately owns the CPU: console, keyboard, disk service,
and CP/M processing pause until the nine-second transient returns.

## Loudness

The first physical image used pulse widths of 16, 8, and 4 microseconds, with
28 microseconds for a coincident three-voice event.  It worked, but the bench
assessment was “very interesting and not that bad” at very low volume.

The retained final version ORs a `C0h` drive bias into every nonzero voice mask.
At the 2 MHz PIT input this produces approximately 100–124 microsecond pulses.
It makes the three voices more even and materially louder.  Their combined
average low time remains below roughly 10%, comfortably below the 50% square
wave used by the existing ROM melody player.  The louder physical run was
assessed at the bench as a “Fantastic result!”.

## Reproducible result

The cycle regression uses the repository's 8080 core and scales its cycle
counts by the approximately 1.70 MHz effective RAM execution rate measured on
the Juku.  This is a software/cycle result, not an oscilloscope measurement.

```text
JUKUPOLY-THREE-VOICE: PASS sample=10968.2Hz A3=219.77Hz
C#4=276.44Hz E4=328.71Hz entrances=2.001/4.013/9.075s outputs=5485
```

Build or verify the committed 163-byte CP/M image with:

```sh
python3 spinoffs/jukupoly/firmware/build_three_voice.py
bash sync/jukupoly_three_voice_check.sh
```

The implementation is
[`firmware/three-voice-0100.asm`](firmware/three-voice-0100.asm), the CP/M image
is [`firmware/three-voice.com`](firmware/three-voice.com), and the cycle
regression is
[`../../tests/jukupoly_three_voice_test.c`](../../tests/jukupoly_three_voice_test.c).

## Cycle-model WAV rendering

`tools/render_jukupoly_wav.c` executes a self-contained JukuPoly CP/M
transient in the same 8080 core and turns its timestamped D57 channel-1 Mode-0
writes into 16-bit mono PCM.  The default 1.70 MHz effective CPU rate is the
same calibrated approximation used by the cycle regressions; D57 remains at
its independently sourced 2 MHz rate.  Each active-low interval is integrated
over the exact extent of an output sample, so an impulse shorter than one WAV
sample retains its proportional energy rather than being lost.  Retriggered
or overlapping intervals are merged.

The wrapper requires a C11-capable `cc` and compiles the renderer in temporary
storage on each invocation. It changes to the repository root before running,
so relative input/output paths are interpreted there; use absolute paths for
files elsewhere. Produce a 96 kHz reference WAV with:

```sh
spinoffs/jukupoly/render_jukupoly_wav.sh \
  spinoffs/jukupoly/firmware/three-voice.com /tmp/three-voice.wav
```

`--max-seconds` defaults to 300 seconds of modeled CPU execution. The
transient must return before that limit; a timeout exits with an error before
writing the WAV. Increase the limit for longer scores; it is not an excerpt
length option.

The default 20 Hz DC blocker converts the unipolar electrical impulses into a
playback-safe acoustic reference.  `--dc-block 0` retains the raw, idle-zero
pin-pulse representation.  `--cpu-hz`, `--pit-hz`, and `--sample-rate` expose
the timing assumptions for comparison experiments.  The renderer deliberately
does not claim an analogue model of R90/VT1/VD4/R91/R48, the speaker unit, or
its enclosure; its pulse edges also inherit up to one 2 MHz PIT tick of
CPU-to-PIT phase uncertainty from the effective-rate cycle model.

The deterministic three-voice rendering guard is:

```sh
sync/jukupoly_wav_check.sh
```

## Physical qualification

The quiet and loud images both ran on CS00000 with C10 JukuNet,
Fastboot V16, NetDisk v3 at 19,200 baud and CP/M Plus 3.1. Both returned
cleanly; physical listening found the quiet image too soft and the loud
image substantially stronger.

Console captures establish delivery and return to a fresh `A>` prompt.
Listening supplies the physical audio observation. The source and cycle
regression establish stack restoration and final PIT silence writes;
command-to-prompt timing does not measure audio duration.

The [physical session record](sessions/cs00000-three-voice-physical/README.md)
retains exact quiet/loud binaries, hashes, timings, transcripts, raw host
captures and operator observations.

## Compiled-pattern continuation

[`README.md`](README.md) develops the physical proof into
an editor-independent player: three tonal channels with per-note detune,
legato, persistent attack/decay/hold envelopes, channel-1 slide, and one
concurrent filtered-sample percussion channel.  Its first score is a credited
seven-second reduction of George Stone's 1991 Windows MIDI demonstration
“Trip Through the Grand Canyon.” See the project overview for current player
measurements and the
[retained Canyon listening record](sessions/cs00000-jukupoly-canyon-physical/README.md)
for the exact image tested on CS00000.
