# JukuPoly compiled-pattern player

This is the editor-independent music engine experiment that follows the
physical three-tone proof in [`JUKUPOLY.md`](JUKUPOLY.md).  It plays compiled
tracker-style rows with three tonal channels and one genuinely concurrent
percussion channel through the unmodified Juku speaker.

Status on 2026-08-30: cycle-model and CS00000 physical-listening qualified.

## Relationship to QChan24

The data model and several implementation choices are informed by shiru8bit's
[QChan24 description][qchan]: 16-bit phase accumulators, OR mixing, per-note
detune and legato, per-channel envelope settings, one sliding tone channel, and
compiled percussion descriptors.

There is one intentional architectural difference.  QChan24 retains four tone
channels, but its sample drums interrupt those tones because the Z80 hot loop
has exhausted its registers.  JukuPoly chooses three tones plus percussion and
keeps all four sources active.  The Juku's D57 mode-0 one-shot generates the
physical pulse width after a single `OUT`, leaving enough CPU time to fetch one
preprocessed percussion amplitude on every sample.

[qchan]: https://habr.com/ru/companies/ruvds/articles/843206/

## Hot loop

`BC`, `DE`, and `SP` hold the tone increments.  The three phase values remain
in the immediate operands of self-modifying `LXI H` instructions.  Each
overflow ORs that channel's current 4-bit volume into the mix.  An unpacked
percussion byte is then ORed from memory, the resulting nibble is shifted into
the upper half of the PIT count, and one write to port `19h` starts an
8–120 microsecond speaker impulse.

An 8-bit sample countdown enters the frame logic every 144 samples.  At the
measured 7.186 kHz loop rate that is almost exactly 20 ms.  Frame logic restores
the real CP/M stack, advances envelopes and channel-1 slide, optionally parses
a row, then lends `SP` back to tone channel 3.  Interrupts remain disabled until
the player silences D57, restores the stack, and returns to CP/M.

The percussion bank is unpacked 4-bit PCM.  This costs memory but makes the hot
path only `LXI`/`ORA M`/`INX`/`SHLD`; packed samples would spend too much of the
8080 budget shifting and tracking bits.  Drum tails span frame boundaries and
do not pause or reset any tone phase.  A new hit replaces an unfinished tail.

## Compiled row format

Each variable-size row begins with a duration byte and flags byte:

| Flag | Payload |
|---:|---|
| `01h`, `02h`, `04h` | tone 1, 2, or 3 packet |
| `08h` | signed channel-1 slide delta |
| `10h` | absolute pointer to a percussion descriptor |
| `80h` | end of score |

A nonzero tone packet holds a 15-bit phase increment with legato in bit 15,
followed by an envelope-speed mask and a mode/target-volume byte.  A zero phase
increment silences the channel and has no envelope word.  Percussion
descriptors hold a PCM pointer and duration in frames.

The JSON-to-score compiler exposes the QChan24-style fields as follows:

| Input field | Compiled meaning |
|---|---|
| note | equal-tempered phase increment, A4 = 440 Hz |
| detune `1..9` | increment adjustment `-4..+4`, centered on 5 |
| legato | change increment without phase/envelope restart |
| volume `1..16` | nonzero mix nibble `1..15` |
| envelope speed `1..8` | update masks `1,3,7,...255` |
| attack/decay/hold | start at zero, start at target, or retain target |
| slide up/down `0..9` | signed increment change per frame, tone 1 only |
| sample `1..99` | percussion-bank ID; the present demo defines 1–3 |
| percussion volume `1..4` | compile-time PCM amplitude scaling |
| filter `1..9` | compile-time moving-average window `9..1` |
| sample offset `1..9` | start position from 0% through 80% |

Envelope settings persist in the JSON compiler until changed.  Detune and
legato affect only the note where they appear.  The engine is independent of
the JSON representation: another editor or converter only needs to emit the
documented row packets and sample descriptors.

## Period demo score and credits

The first score is a hand reduction of the opening phrase of **“Trip Through
the Grand Canyon”** (`CANYON.MID`, internal marker “Canyon Music”), composed by
**George Stone**.  The MIDI was distributed with early Windows multimedia
installations; its embedded text credits **Copyright 1991 Passport Designs,
Inc.** and **Produced By The Music Data Company**.

Source consulted:

- [BitMidi archive page for the inspected file][canyon-midi]
- SHA-256 of the inspected 33,876-byte MIDI:
  `39ad41b8310bd7ce7e00accc017bb9cdb23e3d3d581478f295f215495931005c`
- [Passport Designs MIDI history and George Stone attribution][passport-midi]

[canyon-midi]: https://bitmidi.com/canyon-mid-1
[passport-midi]: https://en.wikipedia.org/wiki/Passport_Designs#MIDI

No vendor MIDI file is committed or required by the build.  The compact score
in `jukupoly-canyon-demo.json` is a manually entered three-voice reduction.  It
raises the lead one octave for the Juku speaker, follows the source kick/hat
outline, and documents two snare substitutions that exercise the demo sample
bank.  The original composition and recording credits remain with their
respective rights holders; this repository does not assert a new license for
them.

## DOOM “Suspense” arrangements and credits

`SUSPENSE.COM` is a 60-second arrangement of **“Suspense”**, the E1M5 music
from id Software's 1993 DOOM, composed by **Robert (Bobby) Prince**.  The
reference is the original `M_E1M5.mid` preserved from the OS/2 port in the
[VGMPF DOOM game-rip archive][doom-rip], rather than a later remaster:

- archive ZIP SHA-256:
  `e0a5f88e1d5c3fa1a145fd4f3196312ffafa77dee5f0c60d79e4a46860cf6e5d`;
- extracted 13,605-byte `M_E1M5.mid` SHA-256:
  `ae1d9201e623310ba16a317ff93f1fecd5d42b4efd24212bc2476080d23ea7ec`;
- the [VGMRips PC/AT pack][doom-vgmrips] independently identifies Robert
  Prince as composer and the original PC sound target as YMF262.

[doom-rip]: https://www.vgmpf.com/Wiki/index.php/Doom_(DOS)#Game_Rip
[doom-vgmrips]: https://vgmrips.net/packs/pack/doom-pc

The first minute is unusually well matched to JukuPoly.  The original MIDI
starts `String Bounce` at 0:00, adds `Bass Strings` at 0:08, and adds `String
Bounce 2` at 0:48.25, never exceeding three pitched parts in that interval.
The arrangement retains their event timing at 120 BPM, raises the very low
bass one octave for the Juku speaker, and maps the two `Fret Noise` accents to
a filtered noise sample.  It compiles to 480 rows and 4,047 bytes.

The full source is 2:44 and eventually exceeds three pitched voices: `String
Bounce 3` enters at 1:28.25 and `String Bounce 4` at 2:08.25 without retiring
the older layers.  The prepared 3+1 reduction keeps lead and bass, while tone
3 follows the newest entering string layer at each transition.  Fret noise,
reverse cymbal, and floor tom are approximated by the three synthesized drum
samples.  `SUSPFULL.COM` contains 1,316 rows, 8,200 frames, and is 10,701
bytes.  It is build-, bounded-smoke-, and CS00000 physical-listening
qualified.

No DOOM MIDI or VGM data is committed.  The repository retains only the
credited compiled arrangements and an importer locked to the exact source
MIDI hash; the original composition and game assets remain the property of
their respective rights holders.

## Reproduce

Source and generated files:

- `firmware/jukupoly-player-0100.asm` — strict-8080 runtime;
- `firmware/jukupoly-canyon-demo.json` — credited human-readable score;
- `firmware/build_jukupoly.py` — score, envelope, and percussion compiler;
- `firmware/jukupoly-song-generated.inc` — generated row/PCM bank;
- `firmware/jukupoly.com` — generated CP/M transient;
- `firmware/import_jukupoly_suspense.py` — hash-locked original-MIDI importer;
- `firmware/jukupoly-suspense.json` — generated one-minute score;
- `firmware/suspense.com` — physically qualified one-minute CP/M image;
- `firmware/jukupoly-suspense-full.json` — generated 2:44 reduction;
- `firmware/suspfull.com` — prepared full-song CP/M image;
- `tests/jukuravi_jukupoly_test.c` — manifest-driven cycle regression;
- `tests/jukuravi_jukupoly_suspense_test.c` — bounded-window regression.

Build or verify everything with:

```sh
python3 spinoffs/jukuravi/firmware/build_jukupoly.py
bash sync/jukuravi_jukupoly_check.sh
```

If the uncommitted, hash-matching `M_E1M5.mid` is available, regenerate both
Suspense score files with:

```sh
python3 spinoffs/jukuravi/firmware/import_jukupoly_suspense.py \
  /path/to/M_E1M5.mid spinoffs/jukuravi/firmware/jukupoly-suspense.json
python3 spinoffs/jukuravi/firmware/import_jukupoly_suspense.py \
  /path/to/M_E1M5.mid spinoffs/jukuravi/firmware/jukupoly-suspense-full.json \
  --seconds 164
```

The qualified result is:

```text
JUKUPOLY: checked jukupoly.com bytes=4327 rows=40 drums=7 pcm=3024
JUKUPOLY: PASS sample=7185.9Hz pitches=260.94/195.45/65.02Hz
duration=7.440s frames=369 pulses=4246 simultaneous=50
```

The first-row pitches are the arranged C4/G3/C2 chord.  `simultaneous=50`
counts iterations in which at least one tone accumulator overflowed while the
percussion PCM value was nonzero and all three tone increments were active.
The regression also requires exact frame/sample counts, attack and decay
steps, a changing slide increment, valid PIT counts, clean silence, restored
stack/interrupt state, and an ordinary CP/M return.

The Suspense checks deliberately simulate only representative nine-second
windows, not the complete scores:

```text
JUKUPOLY: checked suspense.com bytes=4047 rows=480 drums=1 pcm=432
JUKUPOLY-SUSPENSE: PASS window=48.000-57.000s sample=7131.8Hz
tones=3 drum-samples=864 pulses=4417
JUKUPOLY: checked suspfull.com bytes=10701 rows=1316 drums=3 pcm=1152
JUKUPOLY-SUSPENSE: PASS window=128.000-137.000s sample=7121.9Hz
tones=3 drum-samples=2160 pulses=5053
```

## Physical qualification

On 2026-08-30, the exact 4,327-byte image above ran through the unmodified
internal speaker of physical Juku CS00000.  `jukuhost` reattached to the live
resident NetDisk session without a hardware reset.  A `WBOOT` refreshed the
directory after the private volume was substituted; `JUKUPOLY` then loaded,
played, and returned to a fresh `A>` prompt.

The prompt returned 13.152 seconds after the command.  This includes CP/M file
lookup/load and CCP reload, whereas the cycle-qualified music interval is
7.440 seconds.  The operator assessed the result as “not bad; player ok.”
Together, the listening observation and clean return qualify the engine on the
physical speaker.  The cycle regression—not the listening run—is the evidence
for true concurrent three-tone-plus-percussion execution.

The exact player, console transcript, raw host capture, command, log, and
hashes are retained in
[`sessions/cs00000-jukupoly-canyon-physical/`](sessions/cs00000-jukupoly-canyon-physical/README.md).

The one-minute Suspense image was also physically qualified on 2026-08-30.
It returned to CP/M 64.541 seconds after the command and received the operator
assessment “sounds good.”  Exact evidence and hashes are retained in
[`sessions/cs00000-jukupoly-suspense-physical/`](sessions/cs00000-jukupoly-suspense-physical/README.md).

The complete 2:44 `SUSPFULL.COM` reduction then cold-booted and played on the
same machine.  It remained stable through the later layer transitions and
returned to CP/M 170.108 seconds after the command.  The operator assessed it
as “works very good.”  Exact full-song evidence and hashes are retained in
[`sessions/cs00000-jukupoly-suspense-full-physical/`](sessions/cs00000-jukupoly-suspense-full-physical/README.md).

## Five-tone feasibility

Five concurrent tone accumulators are credible on this engine, but remain an
unimplemented cycle-budget result.  `BC`, `DE`, and `SP` can retain the first
three increments as today.  After those phases have been processed, tones 4
and 5 can temporarily reuse `BC` and `DE`; two immediate reloads restore the
first pair before the next sample.  Self-modifying phase and step operands
avoid consuming the CP/M stack while `SP` belongs to tone 3.

Against the measured 3+percussion loop, the two phase paths and four register
loads add approximately 132 8080 cycles per sample.  At the measured 1.70 MHz
effective RAM rate, that predicts about **5.1 kHz for five tones alone** or
**4.6 kHz for five tones plus the current percussion fetch**.  All five
original Suspense string parts remain below 700 Hz, so the per-voice pitch
range is adequate.  Code and state memory are also modest.

The likely limit is mix quality rather than execution: OR mixing five pulse
trains makes coincident events louder and can mask quiet voices as aggregate
pitch density rises.  Per-channel level reduction, sparse pulse masks, or a
small nonlinear mix table may be needed.  A physical five-tone chord sweep
and measured cycle regression are required before promoting this estimate to
a JukuPoly capability claim.
