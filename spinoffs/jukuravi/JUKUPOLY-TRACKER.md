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
| `20h` | optional MOD-effect packet |
| `40h` | end of compiled pattern; advance the order list |
| `80h` | end of score |

A nonzero tone packet holds a 15-bit phase increment with legato in bit 15,
followed by an envelope-speed mask and a mode/target-volume byte.  A zero phase
increment silences the channel and has no envelope word.  Percussion
descriptors hold a PCM pointer and duration in frames.

The optional MOD-effect packet starts with channel masks for absolute volume,
signed volume slide, signed phase-step slide, and target portamento.  Its
payload updates only the selected channels, and the slide state persists until
a later row replaces it.  This ABI-v2 path is assembled only for scores that
request it, so the original Canyon and Suspense player images remain unchanged.

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
[ym3812-manual]: https://c64.xentax.com/media/Yamaha_YM3812_Application_Manual.pdf
[opensupaplex-adlib]: https://github.com/sergiou87/open-supaplex/blob/master/resources/audio/music-adlib.xm

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

## Two-operator OPL VGM/VGZ conversion

### “At Doom's Gate”

`DOOMGATE.COM` is an automatic reduction of **“At Doom's Gate”**, DOOM E1M1
music composed by **Robert (Bobby) Prince**, from a YMF262/OPL3 VGZ capture.
The source's GD3 record identifies the game as DOOM, system as IBM PC/AT,
original file as `D_E1M1`, and VGM creator as NewRisingSun.  The exact source
is not committed:

- 31,414-byte VGZ SHA-256:
  `87c6620af71c04a73dd51bec06f7e849fb54a827373de9a1bf33173d7344109a`;
- 94,252-byte decompressed VGM SHA-256:
  `915176f25be1fb1f78c2caa613fe509e7fd52976439c5412ae5ccc0d1b971f6e`.

The VGM header and command stream agree on 4,256,232 samples at 44.1 kHz, or
96.513 seconds.  Its loop command points to byte `0581h`, after the time-zero
chip initialization but still at sample zero, and declares the same 4,256,232
samples as its loop length.  Thus the finite VGM stream is already exactly one
musical pass; following its loop pointer would merely repeat that 1:36.513
pass.  The converter deliberately stops at the VGM end command.

`import_jukupoly_vgz.py` accepts an uncompressed VGM or gzip-compressed VGZ,
parses sample-accurate waits and either YM3812/OPL2 or YMF262/OPL3 register
writes, and reconstructs all 9 or 18 two-operator channels.  It groups key-ons
by their OPL operator/register signature.  Instruments used at four or more
pitches and exact simultaneous three-pitch chords become melodic; fixed-pitch
and rare signatures become kick, snare/tom, or hat/cymbal reductions.  Exact
signature overrides are available when the register stream alone cannot
distinguish a deliberately narrow-pitch instrument from percussion.  Identical
stereo/unison pitches are collapsed, persistent notes retain their Juku channel
where possible, and key-on retriggers retain the riff's gating.  The current
boundary intentionally rejects OPL3 four-operator and hardware-rhythm modes
rather than pretending to convert them.

The converter originally treated the six-bit OPL total-level field as linear.
The [Yamaha YM3812 Application Manual][ym3812-manual] specifies logarithmic
attenuation in 0.75 dB steps, up to 47.25 dB.  The corrected reducer converts
that attenuation to linear amplitude before quantizing it to Juku's volume
range; for parallel connection mode it follows the manual's sum of both
operators and caps the result at Juku full scale.  A regression locks the
known TL values and chord classification.  The correction changes level only
for the two DOOM scores: their notes, drum identities, hit counts, and timing
remain identical.  Corrected renders of both DOOM scores and Supaplex passed
subjective A/B listening review on 2026-08-31.

This source contains three automatically recognized variable-pitch signatures.
They peak at five simultaneously allocated OPL voices, but duplicate-pitch
collapse normally leaves three or fewer useful notes.  Only 66 of 4,826 Juku
frames contain more than three distinct candidates and require a ranked
three-note choice.  OPL waveforms, FM modulation, feedback, stereo, and chip
envelopes cannot survive a three-pulse beeper reduction; the result preserves
notes, gates, approximate register volume, and percussion timing rather than
YMF262 timbre.

The generated score has 1,375 rows and seven compiled percussion descriptors.
`DOOMGATE.COM` is 12,886 bytes.  A 143-sample frame and phase steps calibrated
for 7.12 kHz make its complete cycle-model run 96.872 seconds—0.37% longer
than the 96.513-second VGM pass—after which it silences D57 and returns cleanly
to CP/M.  Its corrected render passed subjective listening review on
2026-08-31.  Physical CS00000 listening remains pending.

### “The Demons from Adrian's Pen”

`DEMONS.COM` applies the same automatic reducer to **“The Demons from Adrian's
Pen”**, Robert Prince's DOOM E2M2 music.  Its GD3 record identifies the game as
DOOM, system as IBM PC/AT, original file as `D_E2M2`, level as E2M2
“Containment Area,” year as 1993, and VGM creator as NewRisingSun.  The exact
source is not committed:

- 44,276-byte VGZ SHA-256:
  `5883ddd0b0ea3f22eb98a5dd83339a5b96fe20b0e82ed811db49e922fc818376`;
- 138,313-byte decompressed VGM SHA-256:
  `fdbdf8e4a6285b1bc48b602d462c302011623a33a31c4bf2728def85de29f45c`.

The command stream contains 6,858,540 samples, or 155.522 seconds
(2:35.522), and declares its loop at sample zero with exactly the same loop
length.  The finite stream is therefore one complete pass; following the loop
would only repeat it.

This busier source has four recognized melodic signatures and peaks at eight
simultaneously allocated OPL voices.  After duplicate-pitch collapse, 354 of
7,776 Juku frames still have more than three candidates and need the ranked
three-note reduction.  The generated score has 2,041 rows and eight compiled
percussion descriptors.  `DEMONS.COM` is 17,255 bytes.  Its complete calibrated
cycle-model run takes 157.028 seconds, 0.97% longer than the VGM pass, then
silences D57 and returns cleanly to CP/M.  Its corrected render passed
subjective listening review on 2026-08-31.  Physical CS00000 listening remains
pending.

### Supaplex main theme

`SUPAPLEX.COM` reduces the **Supaplex main theme**, composed by **David
Whittaker**, from a YM3812/OPL2 VGZ capture.  The source's GD3 record identifies
the game as Supaplex, the system as IBM PC/AT, and whitequark as VGM creator.
The exact source is not committed:

- 8,088-byte VGZ SHA-256:
  `6ebffd8be6674f1567b51b4b9fd7438abfe29009636c77dd29167086857d6f2b`;
- 74,417-byte decompressed VGM SHA-256:
  `b5f01e7eb9dfe89665333d9a6ce0c548e5a1bf6eb73895ac96b01863d2f3b974`.

The command stream contains 13,441,856 samples, or 304.804 seconds, and has no
VGM loop.  Five signatures are melodic.  They peak at four simultaneously
active OPL voices, but duplicate-pitch collapse leaves no frame with more than
three distinct Juku candidates.

The first automatic reduction exposed two independent classification errors.
A 408-key-on synth signature appears as synchronous pitched harmony across
three OPL channels but uses only three distinct pitches, so the original
four-pitch rule called it percussion.  More importantly, all three real drum
patches are played at the same OPL pitch; pitch thresholds therefore collapsed
them into one synthetic drum sound.  The maintained, 1:1
[OpenSupaplex AdLib tracker resource][opensupaplex-adlib] independently names
its corresponding instruments “Closed Hi-Hat,” “Snare,” and “Bass Drum.”  Its
event totals match the VGM exactly: 988, 264, and 488 respectively.  The score
therefore records one explicit melodic signature and three audited percussion
signature mappings rather than attempting a timbre guess.

The corrected OPL level conversion is especially audible here.  The hi-hat's
carrier TL of 6 becomes Juku editor volume 10 and percussion level 2, the
snare's TL of 3 becomes 13 and level 3, and the unattenuated bass drum remains
16 and level 4.  The resulting score has 2,142 rows, exactly 988 hi-hats, 264
snares, and 488 bass drums.  `SUPAPLEX.COM` is 21,332 bytes with three compiled
percussion descriptors.  Its full cycle-model run takes 305.572 seconds,
silences D57, and returns cleanly to CP/M.  The corrected render received the
operator assessment “sounds much better” on 2026-08-31.  Physical CS00000
listening remains pending.

## AY/YM VGM/VGZ conversion and Arkanoid “Ending”

`ARKANOID.COM` is an automatic reduction of **“Ending”** from the 1986
Arkanoid arcade soundtrack, composed by **Hisayoshi Ogura** (小倉 久佳).  The
recognizable score contains Arkanoid's main-theme material.  Its GD3 record
identifies a YM2149 register capture for an arcade machine and credits the VGM
conversion to Sonic of 8!.  The exact source is not committed:

- 818-byte VGZ SHA-256:
  `909b71ae07cf968bde9f6e63091be1d280e98b8d1de21825e88fe7e92de04c19`;
- 4,162-byte decompressed VGM SHA-256:
  `13ab3b7b43c08309fc43711584177fdac1359b94a8b1c38011c248e9e55357a5`.

The VGM stream contains 811,011 samples, or 18.390 seconds.  Its loop begins
at sample 89,889 after a 2.038-second intro and spans the remaining 721,122
samples, or 16.352 seconds.  Stopping at the end command therefore retains the
intro and exactly one loop pass.

`import_jukupoly_ay_vgz.py` parses AY-family register writes and sample-accurate
VGM waits.  This source declares a 1.5 MHz YM2149 with its `/SEL` divider flag,
giving a 750 kHz effective clock.  Each of its three native tone periods maps
directly to a Juku phase increment instead of being rounded to a tracker note;
this preserves the close detuning and audible beating of the doubled lead.
Hardware-envelope retriggers become Juku decay retriggers.  The generic path
can reduce AY noise gates to percussion, although this capture keeps noise
disabled and needs none.

The generated score has 170 rows and 920 frames, including 557 frames with all
three tones active and 156 envelope retriggers.  `ARKANOID.COM` is only 2,513
bytes and contains no PCM bank.  Its complete calibrated cycle-model run takes
18.416 seconds, then silences D57 and returns cleanly to CP/M.  The rendered
reduction passed subjective listening review on 2026-08-30.  Physical CS00000
listening remains pending.

## TDK “The Robots” MOD adaptation

`TDK60.COM` and `TDKROBOT.COM` adapt the four-channel ProTracker module
**“The Robots”** by **Mark Knight / T.D.K.** ([Mod Archive module
59396][tdk-mod]).  It is a tracker arrangement of Kraftwerk's song, whose
[credited writers][robots-credit] are **Ralf Hütter, Florian Schneider, and
Karl Bartos**.  The Juku work retains both levels of credit; it does not claim
ownership or a new license for the composition, arrangement, or sampled
material.

The exact inspected 356,298-byte module is deliberately not committed.  Its
hashes are:

- SHA-256 `c9d89b05ed00ba80a93ec5f3c6448a40d925d0b65ad1eba3beb27234c7878c3e`;
- MD5 `d1b288d964ac4f7acb3216d0d9dfab77`.

The importer maps MOD channels 1, 2, and 4 to Juku tone channels 1–3.  Channel
3 of the MOD supplies most percussion.  The source uses only effects that are
practical in the frame-rate part of the 8080 player: `1xx`/`2xx` pitch slide,
`3xx` target portamento, `9xx` sample offset, `Axy` volume slide, `Cxx`
absolute volume, and `Fxx` speed.  It contains no arpeggio, vibrato, tremolo,
pattern jump, or pattern break.  Speed changes are compiled into row lengths;
the other effects use the ABI-v2 state described above.

The common synthesized kick, snare, and hat stand in for source samples 1, 2,
and 13.  Two pieces of real module PCM also fit:

- the complete 7,384-byte source sample 6, resampled and normalized to about
  one second of unpacked 4-bit PCM;
- the first 167 ms after source sample 3's `95B` offset, followed by a 20 ms
  click-suppressing ramp.

The several roughly four-second voice/effect samples would exceed the CP/M
transient program area and are omitted.  Pattern-order reuse is what makes the
complete score possible: the 66 source order positions compile into 45
state-correct pattern variants.  The full image is 38,591 bytes and loads only
through `97BEh`, leaving 1,087 bytes before the renderer/test stack at `9BFEh`.

The one-minute image contains 436 compiled rows and 3,000 nominal 50 Hz
frames.  The full image contains 2,880 stored rows, expands through its order
list to 25,728 frames (8:34.56 nominal).  ABI-v2 frame work is heavier than the
original player, so this score uses 139 samples per frame and phase increments
calibrated for a 6.94 kHz effective rate.  The one-minute image completes in
60.266 seconds and the full image in 8:36.10 under the 1.70 MHz cycle model,
within 0.45% and 0.30% of the source clock respectively.  Both pass complete,
rather than windowed, simulations; physical CS00000 listening remains to be
done.

[tdk-mod]: https://modarchive.org/index.php?request=view_by_moduleid&query=59396
[robots-credit]: https://www.easysong.com/search/songs/song-copyright-holder-information.aspx?s=2287555

## Reproduce

Source and generated files:

- `firmware/jukupoly-player-0100.asm` — strict-8080 runtime;
- `tools/render_jukupoly_wav.c` — calibrated cycle-model Mode-0 WAV renderer;
- `firmware/jukupoly-canyon-demo.json` — credited human-readable score;
- `firmware/build_jukupoly.py` — score, envelope, and percussion compiler;
- `firmware/jukupoly-song-generated.inc` — generated row/PCM bank;
- `firmware/jukupoly.com` — generated CP/M transient;
- `firmware/import_jukupoly_suspense.py` — hash-locked original-MIDI importer;
- `firmware/jukupoly-suspense.json` — generated one-minute score;
- `firmware/suspense.com` — physically qualified one-minute CP/M image;
- `firmware/jukupoly-suspense-full.json` — generated 2:44 reduction;
- `firmware/suspfull.com` — prepared full-song CP/M image;
- `firmware/import_jukupoly_mod.py` — hash-locked four-channel MOD importer;
- `firmware/jukupoly-tdk-robots-60s.json` — one-minute generated score;
- `firmware/tdk60.com` — one-minute MOD adaptation;
- `firmware/jukupoly-tdk-robots.json` — pattern-reused full score;
- `firmware/tdkrobot.com` — complete MOD adaptation;
- `firmware/import_jukupoly_vgz.py` — general two-operator OPL2/OPL3 VGM/VGZ reducer;
- `firmware/jukupoly-doomgate-vgz.json` — generated one-pass E1M1 reduction;
- `firmware/doomgate.com` — complete 1:37 E1M1 CP/M image;
- `firmware/jukupoly-demons-vgz.json` — generated one-pass E2M2 reduction;
- `firmware/demons.com` — complete 2:36 E2M2 CP/M image;
- `firmware/jukupoly-supaplex-main-vgz.json` — audited full Supaplex reduction;
- `firmware/supaplex.com` — complete 5:05 Supaplex CP/M image;
- `firmware/import_jukupoly_ay_vgz.py` — AY/YM three-tone VGM/VGZ reducer;
- `firmware/jukupoly-arkanoid-ending-vgz.json` — generated Arkanoid reduction;
- `firmware/arkanoid.com` — complete 18.4-second Arkanoid CP/M image;
- `tests/jukuravi_jukupoly_test.c` — manifest-driven cycle regression;
- `tests/jukuravi_jukupoly_suspense_test.c` — bounded-window regression;
- `tests/jukuravi_jukupoly_mod_test.c` — full-order/effect/PCM regression;
- `tests/jukuravi_jukupoly_vgz_import_test.py` — OPL level/classification regression;
- `tests/jukuravi_jukupoly_vgz_test.c` — complete VGM-reduction regression.

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

If the hash-matching TDK module is available, regenerate the one-minute and
complete adaptations with:

```sh
python3 spinoffs/jukuravi/firmware/import_jukupoly_mod.py \
  /path/to/tdk-the_robots.mod \
  spinoffs/jukuravi/firmware/jukupoly-tdk-robots-60s.json --seconds 60
python3 spinoffs/jukuravi/firmware/import_jukupoly_mod.py \
  /path/to/tdk-the_robots.mod \
  spinoffs/jukuravi/firmware/jukupoly-tdk-robots.json
```

Convert a supported one-pass YM3812 or YMF262 VGM/VGZ and build its CP/M image
with:

```sh
python3 spinoffs/jukuravi/firmware/import_jukupoly_vgz.py \
  /path/to/source.vgz spinoffs/jukuravi/firmware/jukupoly-doomgate-vgz.json
python3 spinoffs/jukuravi/firmware/build_jukupoly.py \
  --song spinoffs/jukuravi/firmware/jukupoly-doomgate-vgz.json \
  --generated spinoffs/jukuravi/firmware/jukupoly-doomgate-vgz-generated.inc \
  --output spinoffs/jukuravi/firmware/doomgate.com
```

For the exact Supaplex source above, preserve the independently audited narrow-
pitch synth and drum identities with explicit signature mappings:

```sh
python3 spinoffs/jukuravi/firmware/import_jukupoly_vgz.py \
  '/path/to/01 Main Theme.vgz' \
  spinoffs/jukuravi/firmware/jukupoly-supaplex-main-vgz.json \
  --melodic-signature b43be9c081e8 \
  --percussion-signature d2e3fbb1ef11=1 \
  --percussion-signature 0abd18bd72b2=2 \
  --percussion-signature 6236af03ec23=3
python3 spinoffs/jukuravi/firmware/build_jukupoly.py \
  --song spinoffs/jukuravi/firmware/jukupoly-supaplex-main-vgz.json \
  --generated spinoffs/jukuravi/firmware/jukupoly-supaplex-main-vgz-generated.inc \
  --output spinoffs/jukuravi/firmware/supaplex.com
```

Convert a supported AY/YM VGM/VGZ with:

```sh
python3 spinoffs/jukuravi/firmware/import_jukupoly_ay_vgz.py \
  /path/to/source.vgz \
  spinoffs/jukuravi/firmware/jukupoly-arkanoid-ending-vgz.json
python3 spinoffs/jukuravi/firmware/build_jukupoly.py \
  --song spinoffs/jukuravi/firmware/jukupoly-arkanoid-ending-vgz.json \
  --generated spinoffs/jukuravi/firmware/jukupoly-arkanoid-ending-vgz-generated.inc \
  --output spinoffs/jukuravi/firmware/arkanoid.com
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

The MOD regression traverses both complete generated order lists and observes
live volume slides, pitch slides, target portamento (in the full score), and a
51-frame real-PCM descriptor:

```text
JUKUPOLY-MOD: PASS bytes=12812 frames=3000 tones=3 volume-slide=1
pitch-slide=1 porta=0 pcm-frames=51 writes=66759
JUKUPOLY-MOD: PASS bytes=38591 frames=25728 tones=3 volume-slide=1
pitch-slide=1 porta=1 pcm-frames=51 writes=460217
```

The VGM/VGZ regressions execute all complete, non-repeated register-score
reductions:

```text
JUKUPOLY-VGZ: PASS bytes=12886 frames=4826 duration=96.872s tones=3
simultaneous=91377 drum-samples=182182 writes=55927
JUKUPOLY-VGZ: PASS bytes=17255 frames=7776 duration=157.028s tones=3
simultaneous=245817 drum-samples=199771 writes=139256
JUKUPOLY-VGZ: PASS bytes=21332 frames=15240 duration=305.572s tones=3
simultaneous=696410 drum-samples=533676 writes=198786
JUKUPOLY-VGZ: PASS bytes=2513 frames=920 duration=18.416s tones=3
simultaneous=79651 drum-samples=0 writes=8122
```

Render the exact one-minute or full-song transient through the calibrated C
cycle model with:

```sh
spinoffs/jukuravi/render_jukupoly_wav.sh \
  spinoffs/jukuravi/firmware/suspense.com /tmp/suspense.wav
spinoffs/jukuravi/render_jukupoly_wav.sh \
  spinoffs/jukuravi/firmware/suspfull.com /tmp/suspfull.wav
spinoffs/jukuravi/render_jukupoly_wav.sh --max-seconds 600 \
  spinoffs/jukuravi/firmware/tdkrobot.com /tmp/tdk-robots.wav
spinoffs/jukuravi/render_jukupoly_wav.sh --max-seconds 110 \
  spinoffs/jukuravi/firmware/doomgate.com /tmp/doomgate.wav
spinoffs/jukuravi/render_jukupoly_wav.sh --max-seconds 175 \
  spinoffs/jukuravi/firmware/demons.com /tmp/demons.wav
spinoffs/jukuravi/render_jukupoly_wav.sh --max-seconds 320 \
  spinoffs/jukuravi/firmware/supaplex.com /tmp/supaplex.wav
spinoffs/jukuravi/render_jukupoly_wav.sh --max-seconds 25 \
  spinoffs/jukuravi/firmware/arkanoid.com /tmp/arkanoid.wav
```

The WAV is a timing-calibrated digital/acoustic reference, not a fitted model
of the CS00000 transistor driver, speaker, or enclosure.  See
[`JUKUPOLY.md`](JUKUPOLY.md#cycle-model-wav-rendering) for its exact timing and
filter boundary.

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
