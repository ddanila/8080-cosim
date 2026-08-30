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

## Why this belongs here

JukuPoly is currently a small Jukuravi subproject rather than a separate
repository.  Its useful claims depend on facilities already maintained here:

- the strict Intel 8080 assembler path;
- the cycle-level 8080 model and Juku's measured effective RAM execution rate;
- the documented D57 speaker path;
- JukuNet/C10, `jukuhost`, and CP/M Plus for repeatable physical delivery;
- the repository's physical-session evidence conventions.

A separate repository would make sense if JukuPoly grows into a tracker,
song-data format, reusable playback library, or a multi-machine beeper engine.
The current demonstration is better kept beside the machine model that makes
it reproducible.

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
while `SP` is borrowed, then the original stack and interrupt state are
restored before the CP/M `RET`.

The timeline is deliberately simple:

| Time | Voices |
|---:|---|
| 0–2 s | A3, 220.00 Hz |
| 2–4 s | A3 + C-sharp4, 277.18 Hz |
| 4–9 s | A3 + C-sharp4 + E4, 329.63 Hz |

Transitions are counted from A3 phase overflows rather than from every sample,
so they remain near 2, 4, and 9 seconds when READY timing changes the loop
rate.  Playback deliberately owns the CPU: console, keyboard, disk service,
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
JUKURAVI-THREE-VOICE: PASS sample=10968.2Hz A3=219.77Hz
C#4=276.44Hz E4=328.71Hz entrances=2.001/4.013/9.075s outputs=5485
```

Build or verify the committed 163-byte CP/M image with:

```sh
python3 spinoffs/jukuravi/firmware/build_three_voice.py
bash sync/jukuravi_three_voice_check.sh
```

The implementation is
[`firmware/three-voice-0100.asm`](firmware/three-voice-0100.asm), the CP/M image
is [`firmware/three-voice.com`](firmware/three-voice.com), and the cycle
regression is
[`../../tests/jukuravi_three_voice_test.c`](../../tests/jukuravi_three_voice_test.c).

## Physical qualification

Both images ran on CS00000 with the C10 JukuNet ROM, Fastboot V16, NetDisk v3
at 19200 baud, and CP/M Plus 3.1:

| Run | Image | Delivery | Cycle-model music interval | Host command-to-prompt | Result |
|---|---:|---|---:|---:|---|
| quiet | 161 bytes | cold network boot | 9.052 s | 11.949 s | clean return; low volume |
| loud | 163 bytes | live N4 reattach | 9.075 s | 13.677 s | clean return; strong bench result |

The host intervals include CP/M directory lookup, COM loading, and CCP reload;
they are not presented as audio-duration measurements.  In both cases the N4
console shows `TRIVOICE` followed by a fresh `A>` prompt, proving that the
transient restored the stack, silenced the PIT, and returned to CP/M.  The
operator's listening result supplies the physical audio observation.

Exact quiet/loud binaries, console transcripts, raw host captures, commands,
logs, and hashes are retained in
[`sessions/cs00000-three-voice-physical/`](sessions/cs00000-three-voice-physical/README.md).

## Compiled-pattern continuation

[`JUKUPOLY-TRACKER.md`](JUKUPOLY-TRACKER.md) develops the physical proof into
an editor-independent player: three tonal channels with per-note detune,
legato, persistent attack/decay/hold envelopes, channel-1 slide, and one
concurrent filtered-sample percussion channel.  Its first score is a credited
seven-second reduction of George Stone's 1991 Windows MIDI demonstration
“Trip Through the Grand Canyon.”  The 4,327-byte player currently passes the
cycle model at 7.186 kHz and passed a CS00000 physical listening run on
2026-08-30, returning cleanly to CP/M after playback.
