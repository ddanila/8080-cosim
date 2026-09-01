# JukuPoly compiled-pattern player

This is the editor-independent music engine experiment that follows the
physical three-tone proof in [`THREE-VOICE.md`](THREE-VOICE.md).  It plays compiled
tracker-style rows with three tonal channels and one genuinely concurrent
percussion channel through the unmodified Juku speaker.

The guarded design for preserving OPL envelopes, tremolo, vibrato, and related
articulation during VGZ reduction is in
[`OPL-REDUCTION-PLAN.md`](OPL-REDUCTION-PLAN.md).

Status on 2026-08-30: cycle-model and CS00000 physical-listening qualified.

JukuPoly is a standalone Juku CP/M music experiment within `spinoffs/`.  It
was developed initially through the Jukuravi upload/host environment, but the
player, score format, importers, generated music, renderer, regressions, and
physical evidence live here.  Jukuravi is only a historical delivery tool for
the earliest runs, not the project namespace or a runtime dependency.

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

## Disk library player

The same timing engine can also be built once as `JUKEBOX.COM` and reused for
many songs.  In this mode a small CP/M shell lists a fixed catalog, accepts
track numbers, loads the selected `.JPS` song at `1800h`, validates its header,
and calls the ordinary player entry point.  Playback still uses the exact
interrupt-disabled hot loop above; only the menu and disk loader are new.
After the finite VGM pass ends, the engine silences D57 and returns to the
menu.  A bare Return selects track 01, `L` advances through 11-track catalog
pages, and `Q` returns to CP/M.  During playback, physical Escape is sampled
once per approximately 20 ms frame and returns immediately to the menu.  This
single-column matrix read costs 48 idle-path 8080 cycles at the existing frame
boundary; it adds nothing to the audio-sample hot loop and deliberately avoids
the much slower CP/M/N4 console-status path.  This path was physically
qualified on CS00000 on 2026-08-31: Escape stopped “At Doom's Gate,” the menu
reported `Track stopped.`, and the operator confirmed that Escape worked.

`build_doom_library.py` converts all 23 DOOM and 21 DOOM II VGZ files from the
two vgmrips archives into fixed-address ABI-v1 `.JPS` files.  The resulting
800 KiB native Juku image contains 44 tracks totaling 2:13:28, `JUKEBOX.COM`,
and an on-disk credits/catalog text.  Music is by Robert Prince; DOOM and DOOM
II are id Software games; the OPL3 packs were prepared by NewRisingSun and
distributed by vgmrips.net.  These are three-tone-plus-percussion reductions,
not OPL3 emulation.

Juku media store side 0 and side 1 of each cylinder next to one another, while
CP/M and cpmtools view the sides as 160 side-major logical tracks.  The builder
uses the period full-disk DPB (two reserved tracks, 197 4 KiB blocks, and the
known final unallocated half-block), applies the ten-sector skew, then converts
the completed logical image to Juku's cylinder-interleaved native order.  The
result was booted through CPMish NetDisk mode 2 on 2026-08-31: `B:JUKEBOX`
listed the catalog, loaded and played track 01 from B:, returned to the menu,
and quit cleanly to CP/M.

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

For OPL-aware development, `--opl-trace-output TRACE.json` additionally emits
a lossless ordered record of every register write without changing the score.
The host-only `opl_trace.py` model retains the complete raw register file and
decodes both operators' AM, vibrato, EGT, KSR, multiplier, KSL, TL, AR, DR, SL,
RR, and waveform fields; channel frequency, block, key, feedback, connection,
and four stereo routes; key/pitch transitions; and global depth, rhythm,
OPL3-new-mode, and four-operator state.  Writes at the same VGM timestamp keep
their source order.  This trace is analysis evidence, not an OPL synthesizer
and not target-side code.

The behavioral oracle is unmodified [Nuked OPL3][nuked-opl3], pinned as the
`external/Nuked-OPL3` submodule at commit
`765ec962e473aeb767e4cba74ffdc8f588ffbfe8` and used under its
LGPL-2.1-or-later license.  `tools/jukupoly_opl_oracle.c` accepts the compact
timed stream emitted by `opl_oracle.py`, renders signed 16-bit stereo PCM at
the VGM 44.1 kHz clock, and records 50 Hz probes of channel pitch/key,
operator attenuation/stage, and the shared LFO phases.  The synthetic
agreement guard checks key and live-pitch timing, envelope attack/release
direction, an audible release tail, LFO progression, modulation changing the
PCM, and isolated two-operator rendering.  The oracle is compiled and run only
on the host; neither it nor its state structures enter `JUKEBOX.COM`.

`--opl-voice-output VOICES.json` adds a second analysis-only view.  It
reconstructs exact key spans and every held-note pitch write, then reports
same-pitch layer and same-patch cross-channel continuation candidates together
with the register-semantic evidence for each relation.  Candidate edges are
not yet logical-voice assignments: a complete two-pack run found enough
ambiguous continuation edges that adopting them locally would be unsafe for
chords.  This progressive M2 slice therefore changes neither generated scores
nor the target player.

The v2 evidence document also collapses the proven layer components and uses
a global one-to-one boundary match to form provisional logical-voice chains.
The matching order is explicit and deterministic: patch identity, hardware
channel continuity, known/small pitch motion, then key gap.  It does not yet
choose the three Juku voices.  Run `tools/report_opl_voices.py` on one or more
ZIP packs to get per-track counts, assignment fingerprints, and a complete
pack fingerprint without copying the copyrighted source streams.

The completed M2 analysis adds a provisional three-voice decision at every
relevant 50 Hz frame.  Each selected note records whether it is a protected
v1 onset, a new attack, retained logical-voice ownership, bass/lead role,
estimated level, and envelope evidence.  Current v1 source onsets are a
monotonic compatibility set: the provisional allocator may fill otherwise
lost capacity but may not remove one.  Across the two complete Doom packs it
retains all 53,286 v1 source onsets and adds 15,776, with no score or player
change.  `--opl-voice-output` contains the full inspectable decisions;
`report_opl_voices.py` fails if a protected onset regresses.

The v3 evidence policy closes a blind spot found while preparing the M3 Imp
fixture.  Four detuned, sustained OPL channels begin at sample zero in “The
Imp's Song,” but the v1 distinct-pitch signature classifier cannot label an
evolving patch used for only one keyed pitch.  A logical note may now also be
tone-eligible when at least two channels have passed the existing strict
pitch-layer tests, remain keyed for at least 50 analysis frames (one second),
have a finite pitch, and carry OPL sustained-envelope evidence.  Each reason
is written to `melodic_eligibility`; short layered percussion, long
single-channel effects, and non-sustained layers are guarded by regressions
and remain excluded.  This is a generic register-semantic rule, not an Imp
track, filename, or patch exception.

The complete two-pack v3 report covers the same 44 tracks and preserves all
53,286 v1-retained onsets.  It recognizes 156 additional sustained layered
logical notes, increases eligible source onsets from 75,703 to 75,846, and
retains 69,140 provisional onsets (15,854 gains and zero regressions).  The
Imp allocation now starts at frame zero on MIDI F#2, retains all 506 protected
onsets, and gains 14 instead of six.  The deterministic v3 report fingerprint
is `26f0e6d09848cbee34755b247057092dd9defea435781a9e5cedbd5acb939b55`.

[nuked-opl3]: https://github.com/nukeykt/Nuked-OPL3

The reducer preserves each source note's octave whenever its phase increment
fits the player's 15-bit tone word; only an unencodable note is moved down by
whole octaves.  An earlier “audible range” rule folded every note below E2 and
above B5 independently.  In “Suspense” this changed the source bass
D2–E2–F2–G2 into D3–E2–F2–G2, an octave error and interval reversal.  The two
complete DOOM packs span F0 through B7: every low note is directly encodable,
and only A#7/B7 require a downward octave.  The corrected policy is locked by
the importer regression.

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

## OPL feasibility baseline

The guarded [`OPL reduction plan`](OPL-REDUCTION-PLAN.md) starts from a
machine-generated [`ABI-v1 baseline`](OPL-BASELINE.json), reproduced by
`tools/report_jukupoly_baseline.py`.  It assembles the reusable library player,
builds fixed-address JPS images for four committed full-song fixtures, executes
them directly in the 1.70 MHz cycle model, and records sample-loop, whole-frame,
idle-boundary, and row-boundary cycle distributions.  It also locks the exact
sample-loop bytes, player/song/stack margins, observed mutable bytes, and two
deterministic 48 kHz reference-WAV hashes.

The 2026-09-01 baseline measures 7.070–7.132 kHz across the four songs at 143
samples per frame.  The 10% OPL budget is applied separately to each song's v1
rate; the conservative floor across these fixtures is 6.363 kHz.  The 64-byte
sample loop hashes to
`ccadb651e327f99e9fe8b54282a2d70d14609ff02d2b9fb1724708d26e42993f`.
The 3,312-byte library player ends at `0DF0h`, leaving 2,576 bytes before the
song at `1800h`; the hard 32,767-byte song limit leaves 1,022 bytes before the
test stack at `9BFEh`.  The largest reproducible committed-source fixture is
20,556 bytes.  The separately generated 44-track DOOM/DOOM II disk's largest
song is the 30,071-byte “The Dave D. Taylor Blues,” still below both the 30 KiB
soft ceiling and 32,767-byte hard limit.

The baseline guard does not demand that future enhanced songs match v1 sound.
It requires unchanged JPS v1 playback and gives every enhanced fixture its own
explicit rate floor.  A deliberate JPS v2 sound change must add separate
old/new evidence rather than overwrite these reference hashes.

## Guarded JPS v2 envelope checkpoint

The separate `-P2=1 -P4=1` library build now accepts both the unchanged JPS v1
format and the compact envelope-only JPS v2 capability described in
[`JPS2-ENVELOPE-DESIGN.md`](JPS2-ENVELOPE-DESIGN.md).  Three target-side state
machines implement fitted attack, decay, keyed sustain, percussive automatic
release, and key-off tails.  A released voice keeps its phase step until its
4-bit level reaches zero.  Tremolo, vibrato, live held-note pitch changes, FM
timbre, four-operator synthesis, and hardware rhythm are not part of this
checkpoint.

The 46-frame synthetic target regression runs all three envelopes with
concurrent percussion.  Its 141-sample batch measures 7.044 kHz and 49.958
music frames/s.  The enhanced player is 4,537 bytes, ends at `12B9h`, and
leaves 1,351 bytes before songs at `1800h`; the exact frozen 64-byte sample
loop remains unchanged.  Full measurements and gates are committed in
[`OPL-ENVELOPE-M3.json`](OPL-ENVELOPE-M3.json).

The enhanced loader validates the complete v2 variable-packet stream, drum
descriptors, and PCM extents before playback.  Regressions prove that reserved
packet bits, invalid levels, truncation, an invalid descriptor, and oversized
PCM are rejected without a single PIT write.  JPS v1 playback through the
enhanced player still matches the frozen Doomgate profile exactly.

This is a progressive checkpoint, not completed OPL conversion.  The host
fitter models the exact target state machine and finds the least-error packet
for a 50 Hz/4-bit pinned-Nuked curve.  The generic `opl_enhanced.py` path now
maps M2 logical voices to stable Juku channels, sums proven OPL layers, derives
absolute amplitude from post-EG attenuation, fits all selected notes, and
retains the v1 percussion timeline.  `--seconds 30 --enhanced-envelopes
--opl-oracle TOOL` emits the guarded real-song JPS v2 form.  Instrument
classification uses the complete source even for an excerpt, while emitted
events and oracle samples remain bounded to the requested interval.

The committed Imp comparison in [`OPL-IMP-M3.json`](OPL-IMP-M3.json) moves the
first F#2 tone from v1 frame 706 (14.12 s) to v2 frame zero and retains all 13
protected excerpt onsets, gaining two, with no regression.  Sixteen selected
logical notes fit at 0.601 mixer levels mean absolute error; the maximum is
eight levels on the evolving four-layer intro.  Two notes have significant
renewed keyed rises and more than two levels per-note mean error, so the new
generic delivery gate rejects this compact-ADSR candidate.  Significant
attack/decay/release directions still match after 4-bit quantization; that
weaker fact is no longer mistaken for a useful fit.  The experimental v2 JPS
is 1,341 bytes versus 1,290 for v1, while delivery remains unchanged v1.

The first 141-sample real-song attempt was rejected because it rendered 30 s
in 29.495 s, outside the 1% duration guard.  The measured 143-sample,
7,170-Hz-table build renders in 29.900 s at 50.168 frames/s and 7,174.0
samples/s, above its 6,480.8 Hz fixture floor.  The player remains 4,537 bytes
and the frozen hot-loop hash is unchanged.  Reproducible v1/v2 target WAV
hashes and the pinned-oracle reference WAV hash are in the report; listening
copies are under `out/jukupoly-opl-m3-imp-20260901/` locally.

The full 157.508-second Imp pass is recorded in
[`OPL-IMP-FULL-M3.json`](OPL-IMP-FULL-M3.json).  It fits 532 selected logical
notes, retains all 506 protected onsets, and gains 14.  A first unconstrained
pass exposed ten significant direction mismatches: nine short two-level decays
which least squares flattened and one release too slow to move inside its
observed tail.  The generic real-song fitter now ranks preservation of net
changes of at least two mixer levels ahead of squared error.  The guarded pass
has zero such mismatches, 0.655 levels mean error, and 14 levels maximum error.
Twelve notes nevertheless fail the re-articulation/error gate, which is the
reason the enhanced full-song candidate is not delivered.

The full v2 JPS is 9,978 bytes versus 8,537 for v1.  It measures 7,087.5
samples/s against a 6,460.3 Hz fixture floor, 49.563 frames/s, and 158.888 s
against the 157.508 s source, within the 1% duration gate.  The host conversion
consumes no target CPU or memory.  The exact player map and hot-loop hash remain
unchanged.

Physical CS00000 listening on 2026-09-01 confirmed the limitation: the low
lead entered immediately, but sounded constant in volume instead of fading
quickly like the OPL source.  M3 therefore closes as a useful negative result
for this one-ADSR reduction and retains the qualified unchanged-v1 fallback.
Any future Imp enhancement must first pass the same generic fit gate using a
bounded multi-articulation representation.

The audit also corrected the generic direction diagnostic: the oracle sample
at `key_off_frame` already belongs to release and must not be included in the
keyed decay interval.  A focused regression now proves that a flat held
envelope followed by an immediate release is not mislabeled as keyed decay.
This changes qualification metadata only; no target hot-loop instruction or
runtime cost changed.

## Tremolo evidence and synthetic target slice

`opl_tremolo.py` models a shared 3.7 Hz, 16-step attenuation triangle with a fractional phase
accumulator and only four possible depths: off or one through three mixer
levels.  Tests lock the 37-cycle/10-second rate, exact quantized fitting, and
the rule that depth zero wins a tie.

The oracle probe now reports both operators' AM-enable state.  Carrier AM and
additive-modulator AM are direct amplitude evidence; AM only on an FM
modulator is a timbre effect and cannot enable Juku volume tremolo.  A
pinned-Nuked test proves this distinction.  The complete two-pack report
[`OPL-TREMOLO-M4.json`](OPL-TREMOLO-M4.json) finds 20,772 direct-AM melodic
key-ons in 27 tracks and 12,071 modulator-only key-ons which must be rejected
without separate output evidence.

The 30-second Imp analysis finds only one valid depth-one candidate, with a
small 9-point squared-error improvement over 88 frames; another numerical
candidate is rejected by the direct-path guard.  This is not enough to spend
target cycles yet.  Representative direct-AM tracks must show useful
quantized benefit before a JPS/8080 tremolo experiment begins.

The v2 pack report performs the stronger test by removing Nuked's exact live
AM attenuation and independently quantizing with/without-AM amplitudes.  AM
changes 69,978 of 405,454 direct channel-frames, by at most two mixer levels;
all 232,212 modulator-only channel-frames remain identical.  Thus the effect
survives the speaker's level resolution, but only shallowly.

Envelope and tremolo must be fitted jointly: a sequential fit can hide average
AM inside the sustain level.  The guarded joint search recovers exact synthetic
fixtures.  The real representative report
[`OPL-TREMOLO-CANDIDATE-M4.json`](OPL-TREMOLO-CANDIDATE-M4.json) selects depth
one for an “Opening to Hell” note at 62 seconds: 53 of 114 frames change in the
source and squared error falls 222→180.  Mean absolute error rises 0.842→0.930
while maximum error falls 5→4, so this is evidence for a reversible target
experiment, not yet evidence for default enablement.

That reversible experiment is now implemented behind a separate `-P5=1`
build and JPS v2 capability `03h`.  Depth occupies two formerly reserved tone
packet bits, the packet stays five bytes, and the disabled v1/envelope paths
retain their exact M3 execution profiles.  The synthetic target report
[`OPL-TREMOLO-TARGET-M4.json`](OPL-TREMOLO-TARGET-M4.json) measures 374 added
boundary cycles for three modulated voices.  At 140 samples/frame the result
is 6,962.7 Hz and 49.734 music frames/s, above the 6,401.1 Hz guard; the player
ends at `13FFh` with 1,025 bytes left.  Target traces match the host model for
200 frames.  CS00000 listening remains required, so general conversion still
emits no tremolo by default.

The next real checkpoint uses the first 66 seconds of “Opening to Hell.”  The
generic opt-in converter emits tremolo on ten of 61 selected logical notes;
each has a direct AM path, an exact 4-bit source change, and positive joint-fit
improvement.  The envelope-only and tremolo JPS comparisons are both 2,090
bytes.  [`OPL-TREMOLO-REAL-M4.json`](OPL-TREMOLO-REAL-M4.json) records
7,100.2 Hz, 49.652 frames/s, 66.463 seconds, and a 40,943-cycle worst frame for
the tremolo version, plus hashes for both target WAVs and the accurate Nuked
reference.  Local listening files are generated under
`out/jukupoly-opening-tremolo-m4/`.  This passes the bounded real C-cosim and
render gate, not the CS00000 gate.

`import_jukupoly_vgz.py --enhanced-envelopes --enhanced-tremolo` enables this
experimental policy.  `--enhanced-frame-samples` and
`--enhanced-sample-rate` record the measured per-song timing choice; omitting
`--enhanced-tremolo` retains the envelope-only default.
The exhaustive host fitter shares candidate-envelope simulation across all
four depths; tests prove the result is identical to separate searches.  This
reduces conversion time only and consumes no target cycles or bytes.

The complete 279.98-second “Opening to Hell” conversion closes M4's long-track
size and timing gate.  The generic policy selects 592 logical notes and emits
shallow tremolo for 38 of them; 43 indirect numerical candidates remain
rejected, and the independently identified note 100 is retained.  The
controlled envelope-only and tremolo JPS files are both 10,504 bytes, well
below the 30 KiB soft ceiling.  With the measured 142-sample batch and 7,100 Hz
phase table, [`OPL-TREMOLO-FULL-M4.json`](OPL-TREMOLO-FULL-M4.json) records
7,059.7 Hz, 49.716 frames/s, 281.577 seconds (0.57% long), and a 43,141-cycle
worst frame.  The full target comparison and accurate Nuked WAVs are generated
under `out/jukupoly-opening-full-tremolo-m4/`.  Automated M4 qualification is
complete; physical A/B and default enablement remain deliberately open.

## Pitch and vibrato host evidence

M5 begins without changing the target player.  `opl_vibrato.py` implements the
pinned Nuked eight-step F-number contour and derives temporary Juku phase-step
deltas from an immutable base, so repeated cycles cannot accumulate pitch
drift.  At the DOOM packs' 14,318,180 Hz OPL clock, the clock-derived shared
LFO is 6.068835788 Hz and the corresponding 50 Hz 16-bit phase increment is
7,955.

The oracle probe exports operator VIB enables and both effective F-numbers;
synthetic tests compare these against the host model exactly.

[`OPL-PITCH-M5.json`](OPL-PITCH-M5.json) records the first two-pack semantic
gate.  Of 102,172 melodic key-ons, 30,118 in 30 tracks have a conservative
direct common-pitch path.  It rejects 13,466 FM-modulator-only key-ons as
timbre effects and 270 one-sided additive key-ons as partial two-pitch
mixtures.  Same-timestamp frequency writes which end in key-off or retrigger
are excluded because they have no held-note duration.  The resulting nine
tracks contain 7,264 coalesced melodic changes; most (6,034) move by 5--50
cents.

The existing M2 three-voice allocation retains 21,017 of 22,829 conservative
direct-vibrato logical notes at some point and 6,495 of 7,264 held-pitch events
at the exact event frame, while missing zero protected v1 onsets.  This closes
the allocation-survival gate and justifies a bounded ABI/cycle design, but it
still adds no JPS capability or 8080 work.  Representation size, cycles,
full-song timing, and physical listening remain open gates.

The reversible packet/state/cycle proposal is recorded in
[`JPS2-PITCH-DESIGN.md`](JPS2-PITCH-DESIGN.md).  Its cheapest first slice uses
existing JPS2 legato packets for held-note pitch and therefore needs no new
8080 code.  Runtime vibrato remains a later conditional-byte experiment with
explicit map, combined-cycle, file-size, and rollback gates.

The first host-format slice is implemented: strict score validation emits
capability `05h`/`07h`, mode bits, and one conditional `delta-1` byte while
proving both 15-bit phase-step bounds.  Omitted vibrato remains byte-identical,
standalone target assembly is explicitly blocked, and the current M4 library
player rejects the new capability with zero PIT writes.  This is format
evidence only; no new player claims support yet.

The independently useful held-pitch slice is now implemented behind
`--enhanced-held-pitch`.  It derives every selected logical note's raw phase
step from the declared target sample rate and emits an existing JPS2 legato
packet only when the same note remains on the same target channel and its
quantized step changes.  The generated metadata records the rate used for
phase-step generation, preventing a timing-only calibration from silently
detuning the score.  Normal enhanced conversion is unchanged unless the flag
is supplied.

[`OPL-PITCH-REAL-M5.json`](OPL-PITCH-REAL-M5.json) qualifies the complete
96.513-second “At Doom's Gate” conversion against a fixed-pitch control.  The
generic policy emits 566 held-key packets while retaining all 1,080 source
onsets and missing zero protected onsets.  The JPS grows from 14,073 to 17,215
bytes, remains below 30 KiB, and still advertises capability `01h`: this slice
adds zero player bytes and zero target-state bytes.  At 137 samples per frame
and a correctly regenerated 6,850 Hz phase table, C-cosim measures 6,859.2
samples/s, 50.067 frames/s, 96.391 seconds (0.13% short), and a 43,380-cycle
worst frame.  The frozen sample-loop hash remains exact.

The first 143-sample calibration was rejected rather than rationalized: it
measured 48.118 frames/s and 100.296 seconds, 3.92% long.  Reducing the batch
to 137 stays above the combined 6,401.1 Hz floor and restores timing without
changing the player.  Automated full-track size, timing, and render gates now
pass; physical CS00000 A/B and runtime vibrato remain open, so held pitch is
still opt-in.

The next experimental `-P6=1` checkpoint implements only the variable-length
vibrato parser, library preflight, and bounded state.  It does not yet modulate
a sample batch.  [`OPL-VIBRATO-PARSER-M5.json`](OPL-VIBRATO-PARSER-M5.json)
records a 4,993-byte pitch-only player with 54 state bytes and a 5,349-byte
combined parser with exactly 56 state bytes; both end below `1800h`, and the
combined build retains 539 bytes of margin.  V1, capability `01h`, and the M4
`03h` path remain execution-identical, with the frozen sample loop unchanged.

The preflight accepts valid `05h`/`07h` conditional packets and rejects mode
3, missing delta bytes, unadvertised feature fields, and both 15-bit bounds
before any PIT or keyboard I/O.  A target trace covers delta values 1 and 256,
legato replacement, disable, and release clearing/retention.  The trace also
asserts that the shared phase stays zero: normal target assembly remains
refused until the separate exact LFO/temporary-step and combined-cycle gates
pass.

That next target experiment now passes its synthetic gates behind the
additional `-P7=1` define.  It computes the OPL-shaped
`0,+half,+full,+half,0,-half,-full,-half` offsets once per music frame from an
immutable channel base, advances the shared `1F13h` phase only after all three
temporary steps are ready, and leaves the sample loop byte-for-byte frozen.
The execution trace also preloads stale prior-song bases and proves that song
initialization clears them before the first row.

[`OPL-VIBRATO-TARGET-M5.json`](OPL-VIBRATO-TARGET-M5.json) records a 5,255-byte
pitch-only experimental player with 633 bytes of song-window margin, and a
5,632-byte combined tremolo+vibrato player ending at `1700h` with 256 bytes of
margin.  Declared state remains 54/56 bytes.  Matched controls show about
1,359 added boundary cycles per frame.  The high-step three-voice fixture with
percussion and Escape polling measures 6,532.9 samples/s and 49.869 frames/s
at 131 samples/frame; the combined tremolo-depth-1/2/3 fixture measures
6,455.4 samples/s and 50.042 frames/s at the accepted 129-sample boundary.
Both stay above the shared 6,401.1 Hz floor, with 42,713 and 42,696-cycle
worst rows respectively.

This is deliberately not normal playback support yet.  The compiler still
refuses to assemble capability bit 2, so existing v1, envelope, tremolo, and
host-baked held-pitch paths remain the usable fallbacks.  A representative
real-song conversion/render and physical CS00000 A/B are the next gates.

The first of those real-song gates now passes on a 30-second “At Doom's Gate”
excerpt.  `--enhanced-vibrato` is deliberately generic and requires both
measured timing overrides: every active audible operator/layer must have a
direct common-pitch VIB path and resolve to the same bounded target delta.
Mixed, indirect, inconsistent, sub-step, and unsafe paths are reported and
omitted; a changed setting on a retained note becomes an ordinary legato
packet.  No filename, track number, or instrument identifier participates in
the decision.

[`OPL-VIBRATO-REAL-M5.json`](OPL-VIBRATO-REAL-M5.json) records 251 emitted
logical notes, 289 vibrato packets, 156 held-setting updates, and zero missed
protected onsets.  The 7,065-byte capability-`05h` JPS uses 133 samples/frame
and a phase table regenerated at 6,650 Hz; C-cosim measures 6,657.4 samples/s,
50.055 frames/s, 29.967 seconds, a 6.076 Hz LFO, and a 43,628-cycle worst row.
That stays above the shared 6,401.1 Hz floor with percussion and Escape still
active.  A separately calibrated capability-`01h` envelope control measures
6,971.2 samples/s and 50.153 frames/s.  Distinct target WAVs and a pinned-Nuked
reference hash are recorded under `out/jukupoly-doomgate-30s-vibrato-m5/`.

Normal target assembly is still refused.  This checkpoint qualifies one
bounded real render; physical CS00000 A/B is also still required.  Failure
there leaves envelope playback and the already-qualified host-baked pitch
path intact.

The same generic policy now passes the complete 96.520-second track in
[`OPL-VIBRATO-FULL-M5.json`](OPL-VIBRATO-FULL-M5.json).  It emits 908 logical
notes through 1,018 vibrato packets, including 520 held-setting updates, while
retaining all 1,080 source onsets and missing no protected onset.  The
capability-`05h` JPS is 18,133 bytes, below G5's 30 KiB soft ceiling.  At the
same 133-sample/6,650 Hz calibration, C-cosim measures 6,605.7 samples/s,
49.667 frames/s, 97.167 seconds, a 6.029 Hz LFO, and a 44,481-cycle worst
frame.  The frozen sample loop, percussion, and 4,827 Escape polls remain.

This closes the complete-track automated gate, not M6: pack-wide regression,
normal target enablement, and physical CS00000 A/B remain deliberately open.
The full target/control WAV pair and pinned-Nuked reference live under the
untracked `out/jukupoly-doomgate-full-vibrato-m5/` directory.

The exact envelope fitter now deduplicates parameter tuples only after they
produce an identical simulated 4-bit trace, retaining the exhaustive search's
full deterministic tie-break.  This roughly halves a representative fit's
host time.  A bounded exact-result cache additionally reuses only complete
reference/search keys and the target counter's sufficient low six bits;
out-of-range counters are rejected before lookup.  Cache-enabled regeneration
of the 30-second enhanced score remains byte-identical.  Neither optimization
changes conversion policy or target runtime behavior; they prepare the same
guarded search for the M6 pack run.

The first M6 representative conversion/profile now covers the complete Imp,
Dark Halls, Suspense, and rhythm-heavy Dave D. Taylor Blues streams.  The
committed [`OPL-M6-REPRESENTATIVE-PROFILE.json`](OPL-M6-REPRESENTATIVE-PROFILE.json)
records two fully passing enhanced tracks: Dark Halls at 6,854.0 samples/s and
50.029 frames/s, and Suspense at 6,858.5/50.062.  Their JPS files are 20,151
and 12,969 bytes and conservatively emit six and 29 tremolo notes.  Both retain
every protected onset, percussion, Escape polling, and the frozen sample loop.

The Imp candidate retains all onsets and meets the target timing/size limits,
but 12 of its 532 fitted logical notes contain significant renewed keyed
articulation that one ADSR approximates with more than two levels mean error.
It therefore receives the 8,537-byte unchanged-v1 fit fallback.  This is a
generic signal-shape guard, not an Imp-specific exception.

Dave Taylor is the intended useful failure: its enhanced candidate is 40,983
bytes, above the 32,767-byte hard limit, while the unchanged v1 track remains
30,071 bytes.  The report therefore selects v1 as a generic hard-size
fallback; it does not weaken G5 or add a track-specific converter exception.
At that profile checkpoint the render/reference and physical gates remained
open; their later results are recorded below.

The representative render gate is now committed in
[`OPL-M6-REPRESENTATIVE-RENDERS.json`](OPL-M6-REPRESENTATIVE-RENDERS.json).
Separate source-aware 1,500-frame scores use measured settings `143/7170`,
`138/6950`, `139/6980`, and `135/6750`; their C-cosim clocks are all within
1%, and effective rates range from 6,760.4 to 7,174.0 samples/s.  For every
track the v1, enhanced, and exact first-30-second pinned-Nuked WAV hashes are
distinct.  The twelve listening files are generated under
`out/jukupoly-m6-representative/renders/` and remain untracked.  The complete
two-pack disk and physical A/B gates remain open.

A complete guarded mixed disk is now built from the same evidence.  The
generic optional replacement manifest verifies each qualified payload before
substitution and leaves the ordinary builder unchanged when omitted.  The
disk contains At Doom's Gate as capability `05h` and Dark Halls, Suspense,
and Opening to Hell as `03h`, plus 40 unchanged v1 tracks including Imp.  Its
combined player is 5,632 bytes and supports the union capability `07h`.

[`OPL-M6-MIXED-LIBRARY.json`](OPL-M6-MIXED-LIBRARY.json) records an exact
819,200-byte disk with SHA-256 `af0f4486...0015bf9` and 630,447 song bytes.  All
44 catalog songs complete full C-cosim playback under that player; catalog
hashes, capability distribution, enhanced timing/rate gates, Escape polling,
and the frozen loop all pass.  Its exact distribution is `00h:40, 03h:3,
05h:1`.

The preceding five-enhanced disk was then exercised on physical CS00000.  At
Doom's Gate sounded decent; Dark Halls and Suspense were acceptable but hard
to assess precisely; Opening to Hell and the unchanged-v1 Kitchen Ace control
completed without an operator present.  The Imp low lead entered immediately
but failed listening because its volume remained nearly constant instead of
fading like the OPL reference.  Escape, quit, and return to CP/M all worked,
with zero host retries, resets, writes, or UART errors.  Exact tested/corrected
disk hashes and the listening matrix are in
[`sessions/cs00000-jukupoly-m6-physical/`](sessions/cs00000-jukupoly-m6-physical/README.md).
The corrected disk changes only Imp back to v1; its player and other four
enhanced payloads are byte-identical to the physical run.  This is a usable
progressive stopping point, not a claim that all 44 songs are enhanced.

An offline M7 follow-up now tests the smallest hardware-compatible answer to
the failed Imp shape: re-send the existing same-pitch non-legato ADSR packet
at a bounded significant rise.  The opt-in host policy requires a fall and
renewed rise of at least four mixer levels, caps a note at six extra packets,
and excludes tremolo-bearing notes.  It introduces no opcode, player byte,
state byte, or per-sample cycle.

The committed 30-second result in
[`OPL-IMP-REARTICULATION-M7.json`](OPL-IMP-REARTICULATION-M7.json) emits six
extra packets across two logical notes.  Mean envelope error improves from
0.601 to 0.404 levels; the intro improves from 2.833 to 1.119, leaving zero
notes above the re-articulation delivery guard.  Its 1,383-byte JPS runs under
the unchanged 4,537-byte player at 7,170.9 samples/s, 50.146 frames/s, and
29.913 seconds with the frozen loop hash exact.  A local listening render is
`out/jukupoly-imp-rearticulation-m7/imp-reart.wav`.  This remains an
experimental candidate pending full-song and physical qualification; the
library still delivers Imp v1.

The complete-track follow-up in
[`OPL-IMP-REARTICULATION-FULL-M7.json`](OPL-IMP-REARTICULATION-FULL-M7.json)
emits 49 extra packets across 20 of 532 notes and produces a 10,293-byte JPS.
It leaves zero notes above the generic fit guard and measures 7,083.9
samples/s, 49.538 frames/s, and 158.970 seconds in C-cosim, with a 42,197-cycle
worst frame and the same frozen sample loop.  Full-song automated size and
timing therefore pass; physical listening remains open and Imp v1 remains the
delivered fallback.

The reproducible two-pack discovery report
[`OPL-M7-PACK-SCAN.json`](OPL-M7-PACK-SCAN.json) applies the bounded policy to
the opening 30 seconds of all 44 DOOM tracks.  Only Imp and “Nobody Told Me
About id” emit packets.  The latter needs up to six re-attacks, establishing
the current general cap from pack evidence; after that bounded change the
opening scan has zero unrepresented notes.  The report deliberately retains
35 failures from its one-size `143/7170` timing calibration, because a scan is
not authority to ship a track without individual timing measurements.

The individually recalibrated “Nobody Told Me About id” excerpt passes, but
its complete track does not.  The full report
[`OPL-NOBODY-REARTICULATION-M7.json`](OPL-NOBODY-REARTICULATION-M7.json)
records 724 extra packets and a 13,297-byte candidate with otherwise valid
6,912.8 samples/s, 49.732 frames/s, and 179.381-second timing.  Forty-five
later notes still exceed the error limit and one significant attack direction
is lost, so the qualified delivery remains its exact 8,311-byte v1 payload.
This is the intended progressive fallback behavior, not a reason to loosen
the quality gate or packet bound.

[`OPL-M7-MODES.json`](OPL-M7-MODES.json) audits every timed register stream
for the remaining structural OPL modes.  All 44 tracks enable ordinary OPL3
new mode, while zero tracks enable a four-operator pair or hardware rhythm for
any sample.  Those two optional reductions would improve none of these packs,
so they deliberately add no Juku code or data.  Unsupported future sources
remain explicitly rejected.

The detune opportunity report
[`OPL-M7-DETUNED-SPARES.json`](OPL-M7-DETUNED-SPARES.json) finds a much more
promising optional reduction.  Across the same allocation, 33 tracks and
5,303 selected logical notes have source layers that quantize to distinct
target phase steps while a physical tone channel is spare, totaling 84,709
duplicate-voice frame slots.  Imp accounts for 9,157 slots with up to 19.0
cents of source separation.

The first guarded score checkpoint is
[`OPL-IMP-DETUNED-M7.json`](OPL-IMP-DETUNED-M7.json).  During the contiguous
Imp intro it replaces one merged logical voice with three independently fitted
source members at fixed phase steps 839, 845, and 848.  Persistent spare
capacity is required for the complete episode, so no duplicate can displace a
real selected onset; all member voices are released through the ordinary
allocator at the boundary.  Six member-envelope re-triggers compose with the
existing bounded ADSR policy, while a later non-layered voice uses its normal
re-triggers.  No song-specific mapping or target opcode was added.

The resulting 1,405-byte JPS passes every 30-second delivery gate under the
unchanged 4,537-byte player: 7,159.9 samples/s, 50.069 frames/s, 29.958-second
duration, 40,690 worst-frame cycles, and the exact frozen sample loop.  The
three selected member fits have sample-weighted mean error below one mixer
level and maximum error three.  The local comparison render is
`out/jukupoly-imp-detuned-m7/imp-detuned-reart-30s.wav`.  Full-song and
physical listening remain open, so the library continues to deliver Imp v1.

The complete candidate is recorded compactly in
[`OPL-IMP-DETUNED-FULL-M7.json`](OPL-IMP-DETUNED-FULL-M7.json).  A global
per-frame reservation ledger fixes an overlap found by the full conversion:
episodes are considered in deterministic first-onset order, and later ones
are reduced or rejected rather than sharing a physical channel already
reserved by an earlier layer.  The compiler retains a separate hard
three-tone assertion, and a synthetic two-episode collision is covered.

Across the full Imp source, 216 episodes reserve 217 extra voices and fit 433
members at 0.322 sample-weighted mean envelope error.  All 506 protected
onsets and all envelope quality gates pass.  The exact `141/7050` score is
11,692 bytes and runs at 7,049.2 samples/s, 49.994 frames/s, and 157.518
seconds, with a 42,597-cycle worst frame and the unchanged 4,537-byte player.
The complete local render is
`out/jukupoly-imp-detuned-m7/imp-detuned-reart-full.wav`.  This closes the
offline gate only; Imp v1 remains in the library until physical A/B listening.

## Reproduce

Source and generated files:

- `firmware/jukupoly-player-0100.asm` — strict-8080 runtime;
- `firmware/jukupoly-library-shell.inc` — reusable CP/M catalog and JPS loader;
- `firmware/build_doom_library.py` — two-pack converter and native disk builder;
- `diskdefs` — logical Juku full-disk geometry for cpmtools;
- `tools/render_jukupoly_wav.c` — calibrated cycle-model Mode-0 WAV renderer;
- `tools/jukupoly_opl_oracle.c` — pinned Nuked OPL3 timed-stream bridge;
- `tools/report_opl_voices.py` — deterministic whole-pack M2 evidence report;
- `tools/report_jukupoly_baseline.py` — reproducible OPL feasibility profiler;
- `tools/report_jukupoly_envelope.py` — guarded M3 target timing/map report;
- `tools/report_jukupoly_imp_m3.py` — real Imp v1/v2/reference M3 report;
- `tools/report_jukupoly_full_m3.py` — compact full-song M3 feasibility report;
- `tools/report_opl_tremolo.py` — direct versus FM-modulator-only AM pack report;
- `tools/report_opl_tremolo_candidate.py` — reproducible joint-fit M4 candidate;
- `tools/report_jukupoly_tremolo_target.py` — synthetic M4 target budget report;
- `tools/report_jukupoly_tremolo_real.py` — real M4 old/new/reference report;
- `tools/report_opl_pitch.py` — two-pack M5 vibrato/held-pitch semantic report;
- `tools/report_jukupoly_pitch_real.py` — complete-track held-pitch control,
  timing, size, and WAV report;
- `tools/report_jukupoly_vibrato_parser.py` — experimental capability
  `05h`/`07h` parser, preflight, map, state, and compatibility report;
- `tools/report_jukupoly_vibrato_target.py` — synthetic M5 temporary-step,
  no-drift, combined-cycle, map, timing, and compatibility report;
- `tools/report_jukupoly_vibrato_real.py` — bounded real capability-`05h`
  control, size, C-cosim timing, target-WAV, and oracle-reference report;
- `tools/report_jukupoly_m6_representative.py` — four-track enhanced/fallback
  size, envelope error, full C-cosim timing, and delivery report;
- `tools/build_jukupoly_m6_representative.py` — hash-locked, parallel rebuild
  of the four exact-oracle M6 inputs and their committed profile;
- `tools/report_jukupoly_m6_renders.py` — exact 30-second v1/enhanced/Nuked
  render hashes and excerpt timing/concurrency gates;
- `tools/report_jukupoly_m6_mixed_library.py` — complete 44-song mixed-disk
  hash, capability, and full C-cosim compatibility report;
- `tools/build_jukupoly_m7_pack_scan.py` — hash-locked, parallel two-pack
  re-articulation discovery conversion and C-cosim report;
- `tools/report_opl_modes.py` — exact two-pack OPL3/four-operator/hardware-
  rhythm state-duration audit;
- `tools/report_opl_detuned_spares.py` — pack-wide selected-layer versus spare-
  voice phase-step opportunity audit;
- `tools/recalibrate_jukupoly_enhanced.py` — guarded timing-only symbolic-note
  score recalibration which refuses every explicit phase step;
- `OPL-BASELINE.json` — committed pre-OPL timing/memory/WAV evidence;
- `OPL-ENVELOPE-M3.json` — committed synthetic v2 timing/memory evidence;
- `OPL-IMP-REARTICULATION-M7.json` — bounded same-pitch articulation fit,
  timing, size, and unchanged-player evidence;
- `OPL-IMP-REARTICULATION-FULL-M7.json` — complete-track articulation fit,
  file-size, and C-cosim timing evidence;
- `OPL-M7-PACK-SCAN.json` — all-44-track bounded opening-window discovery
  evidence;
- `OPL-NOBODY-REARTICULATION-M7.json` — complete-track rejected-candidate and
  qualified-v1-fallback evidence;
- `OPL-M7-MODES.json` — pack-wide four-operator and hardware-rhythm no-demand
  evidence;
- `OPL-M7-DETUNED-SPARES.json` — pack-wide source demand and capacity evidence
  for optional detuned duplicate voices;
- `OPL-IMP-DETUNED-M7.json` — guarded Imp detuned-member/re-articulation
  excerpt, timing, size, and unchanged-player evidence;
- `OPL-IMP-DETUNED-FULL-M7.json` — complete Imp detuned-member candidate,
  overlap arbitration, size, and full C-cosim timing evidence;
- `OPL-IMP-M3.json` — committed 30-second real-song fit/timing/WAV evidence;
- `OPL-IMP-FULL-M3.json` — committed full-song size/timing/fit evidence;
- `OPL-TREMOLO-M4.json` — committed two-pack semantic and exact-oracle M4 report;
- `OPL-TREMOLO-CANDIDATE-M4.json` — real joint envelope+tremolo evidence;
- `OPL-TREMOLO-TARGET-M4.json` — target ABI/map/state/cycle evidence;
- `OPL-TREMOLO-REAL-M4.json` — 66-second real target/render evidence;
- `OPL-TREMOLO-FULL-M4.json` — complete-track M4 size/timing/render evidence;
- `OPL-PITCH-M5.json` — committed two-pack vibrato and held-pitch evidence;
- `OPL-PITCH-REAL-M5.json` — committed complete-track host-baked pitch report;
- `OPL-VIBRATO-PARSER-M5.json` — committed parser/state-only M5 target report;
- `OPL-VIBRATO-TARGET-M5.json` — committed synthetic runtime-vibrato report;
- `OPL-VIBRATO-REAL-M5.json` — committed bounded real runtime-vibrato report;
- `OPL-VIBRATO-FULL-M5.json` — committed complete-track runtime-vibrato report;
- `OPL-M6-REPRESENTATIVE-PROFILE.json` — committed first M6 four-track profile;
- `OPL-M6-REPRESENTATIVE-RENDERS.json` — committed M6 three-way excerpt report;
- `M6-REPRESENTATIVE-DELIVERY.json` — hash-locked qualified JPS2 replacements;
- `OPL-M6-MIXED-LIBRARY.json` — committed 44-track mixed-disk C-cosim report;
- `JPS2-ENVELOPE-DESIGN.md` — guarded M3 packet/state implementation contract;
- `JPS2-TREMOLO-DESIGN.md` — guarded M4 ABI/state/cycle and rollback contract;
- `JPS2-PITCH-DESIGN.md` — guarded M5 pitch/vibrato and rollback contract;
- `firmware/jukupoly-envelope-v2.inc` — isolated 8080 v2 parser/state machine;
- `firmware/jukupoly-envelope-v2-test.json` — three-envelope target fixture;
- `firmware/jukupoly-tremolo-v2-test.json` — exact shared-phase/depth fixture;
- `firmware/jukupoly-opening-66s-tremolo-m4.json` — bounded real M4 fixture;
- `firmware/jukupoly-opening-full-tremolo-m4.json` — complete-track M4 fixture;
- `firmware/jukupoly-doomgate-held-pitch-m5.json` — compact complete-track M5
  held-pitch fixture;
- `firmware/jukupoly-vibrato-parser-v2-test.json` — conditional-byte and
  release-state M5 parser fixture;
- `firmware/jukupoly-vibrato-v2-test.json` — three-channel runtime-vibrato,
  percussion, and timing stress fixture;
- `firmware/jukupoly-vibrato-tremolo-v2-test.json` — combined M4+M5 stress
  fixture at the shared 10% iteration-count boundary;
- `firmware/jukupoly-doomgate-30s-vibrato-m5.json` — guarded real M5 direct-
  vibrato excerpt with complete host evidence;
- `firmware/jukupoly-doomgate-full-vibrato-m5.json` — guarded complete-track
  M5 direct-vibrato fixture;
- `firmware/jukupoly-library-v1-test.json` — compact v1 loader fixture;
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
- `firmware/opl_trace.py` — lossless timed OPL register/semantic host model;
- `firmware/opl_oracle.py` — per-channel oracle stream and post-EG probe helpers;
- `firmware/opl_envelope.py` — exact-target fitter and semantic attenuation mapper;
- `firmware/opl_enhanced.py` — generic M2-to-JPS-v2 real-song reducer;
- `firmware/opl_tremolo.py` — bounded shared-phase M4 host model/fitter;
- `firmware/opl_vibrato.py` — exact source-shape and bounded M5 step model;
- `firmware/opl_voices.py` — keyed-segment and logical-voice evidence model;
- `firmware/jukupoly-imp-30s-v1.json` — frozen Imp excerpt comparison score;
- `firmware/jukupoly-imp-30s-v2.json` — guarded fitted Imp excerpt score;
- `firmware/jukupoly-imp-30s-rearticulation-m7.json` — opt-in bounded
  same-pitch multi-articulation candidate;
- `firmware/jukupoly-imp-30s-detuned-m7.json` — guarded detuned spare-member
  plus bounded re-articulation excerpt candidate;
- `firmware/jukupoly-doomgate-vgz.json` — generated one-pass E1M1 reduction;
- `firmware/doomgate.com` — complete 1:37 E1M1 CP/M image;
- `firmware/jukupoly-demons-vgz.json` — generated one-pass E2M2 reduction;
- `firmware/demons.com` — complete 2:36 E2M2 CP/M image;
- `firmware/jukupoly-supaplex-main-vgz.json` — audited full Supaplex reduction;
- `firmware/supaplex.com` — complete 5:05 Supaplex CP/M image;
- `firmware/import_jukupoly_ay_vgz.py` — AY/YM three-tone VGM/VGZ reducer;
- `firmware/jukupoly-arkanoid-ending-vgz.json` — generated Arkanoid reduction;
- `firmware/arkanoid.com` — complete 18.4-second Arkanoid CP/M image;
- `tests/jukupoly_test.c` — manifest-driven cycle regression;
- `tests/jukupoly_suspense_test.c` — bounded-window regression;
- `tests/jukupoly_mod_test.c` — full-order/effect/PCM regression;
- `tests/jukupoly_vgz_import_test.py` — OPL level/classification regression;
- `tests/jukupoly_opl_trace_test.py` — synthetic envelope/LFO/rhythm/four-op trace fixture;
- `tests/jukupoly_opl_oracle_test.py` — pinned oracle agreement and isolation regression;
- `tests/jukupoly_opl_envelope_test.py` — exact-target and oracle-fit regression;
- `tests/jukupoly_opl_enhanced_test.py` — real-score allocation/fitting regression;
- `tests/jukupoly_opl_tremolo_test.py` — fractional-rate/depth/false-AM guard;
- `tests/jukupoly_opl_vibrato_test.py` — exact rate/shape/range/no-drift guard;
- `tests/jukupoly_opl_pitch_test.py` — conservative path and held-write guard;
- `tests/jukupoly_vibrato_parser_test.c` — exact parser state/legato/release
  target trace;
- `tests/jukupoly_vibrato_test.c` — exact temporary-step, shared-phase,
  release, immutable-base, and cross-song initialization target trace;
- `tests/jukupoly_opl_voices_test.py` — layer/continuation evidence regression;
- `tests/jukupoly_envelope_format_test.py` — strict JPS v2 envelope packet regression;
- `tests/jukupoly_envelope_test.c` — v2 stage-transition execution regression;
- `tests/jukupoly_tremolo_test.c` — v2 shared-phase target execution regression;
- `tests/jukupoly_vgz_test.c` — complete VGM-reduction regression;
- `tests/jukupoly_library_test.c` — menu, BDOS loading, playback, and return regression;
- `tests/jukupoly_library_test.py` — native two-sided track-order regression;
- `tests/jukupoly_baseline_test.c` — full-song frame and hot-loop cycle profiler.

Build or verify everything with:

```sh
python3 spinoffs/jukupoly/firmware/build_jukupoly.py
bash sync/jukupoly_check.sh
bash sync/jukupoly_library_check.sh
bash sync/jukupoly_baseline_check.sh
bash sync/jukupoly_envelope_check.sh
```

Build the complete DOOM library (requires `cpmtools`) with:

```sh
python3 spinoffs/jukupoly/firmware/build_doom_library.py \
  --doom '/path/to/Doom_(PC).zip' \
  --doom2 '/path/to/Doom_II_-_Hell_on_Earth_(IBM_PC_AT).zip' \
  --output-dir out/jukupoly-doom-library
```

Mount `jukupoly-doom-library.cpm` as native drive B and run `B:JUKEBOX`.
The output directory also retains the individual `.JPS` files, JSON catalog,
CP/M directory listing, and `README.TXT` used to construct the image.

If the uncommitted, hash-matching `M_E1M5.mid` is available, regenerate both
Suspense score files with:

```sh
python3 spinoffs/jukupoly/firmware/import_jukupoly_suspense.py \
  /path/to/M_E1M5.mid spinoffs/jukupoly/firmware/jukupoly-suspense.json
python3 spinoffs/jukupoly/firmware/import_jukupoly_suspense.py \
  /path/to/M_E1M5.mid spinoffs/jukupoly/firmware/jukupoly-suspense-full.json \
  --seconds 164
```

If the hash-matching TDK module is available, regenerate the one-minute and
complete adaptations with:

```sh
python3 spinoffs/jukupoly/firmware/import_jukupoly_mod.py \
  /path/to/tdk-the_robots.mod \
  spinoffs/jukupoly/firmware/jukupoly-tdk-robots-60s.json --seconds 60
python3 spinoffs/jukupoly/firmware/import_jukupoly_mod.py \
  /path/to/tdk-the_robots.mod \
  spinoffs/jukupoly/firmware/jukupoly-tdk-robots.json
```

Convert a supported one-pass YM3812 or YMF262 VGM/VGZ and build its CP/M image
with:

```sh
python3 spinoffs/jukupoly/firmware/import_jukupoly_vgz.py \
  /path/to/source.vgz spinoffs/jukupoly/firmware/jukupoly-doomgate-vgz.json
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-doomgate-vgz.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-doomgate-vgz-generated.inc \
  --output spinoffs/jukupoly/firmware/doomgate.com
```

For the exact Supaplex source above, preserve the independently audited narrow-
pitch synth and drum identities with explicit signature mappings:

```sh
python3 spinoffs/jukupoly/firmware/import_jukupoly_vgz.py \
  '/path/to/01 Main Theme.vgz' \
  spinoffs/jukupoly/firmware/jukupoly-supaplex-main-vgz.json \
  --melodic-signature b43be9c081e8 \
  --percussion-signature d2e3fbb1ef11=1 \
  --percussion-signature 0abd18bd72b2=2 \
  --percussion-signature 6236af03ec23=3
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-supaplex-main-vgz.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-supaplex-main-vgz-generated.inc \
  --output spinoffs/jukupoly/firmware/supaplex.com
```

Convert a supported AY/YM VGM/VGZ with:

```sh
python3 spinoffs/jukupoly/firmware/import_jukupoly_ay_vgz.py \
  /path/to/source.vgz \
  spinoffs/jukupoly/firmware/jukupoly-arkanoid-ending-vgz.json
python3 spinoffs/jukupoly/firmware/build_jukupoly.py \
  --song spinoffs/jukupoly/firmware/jukupoly-arkanoid-ending-vgz.json \
  --generated spinoffs/jukupoly/firmware/jukupoly-arkanoid-ending-vgz-generated.inc \
  --output spinoffs/jukupoly/firmware/arkanoid.com
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
spinoffs/jukupoly/render_jukupoly_wav.sh \
  spinoffs/jukupoly/firmware/suspense.com /tmp/suspense.wav
spinoffs/jukupoly/render_jukupoly_wav.sh \
  spinoffs/jukupoly/firmware/suspfull.com /tmp/suspfull.wav
spinoffs/jukupoly/render_jukupoly_wav.sh --max-seconds 600 \
  spinoffs/jukupoly/firmware/tdkrobot.com /tmp/tdk-robots.wav
spinoffs/jukupoly/render_jukupoly_wav.sh --max-seconds 110 \
  spinoffs/jukupoly/firmware/doomgate.com /tmp/doomgate.wav
spinoffs/jukupoly/render_jukupoly_wav.sh --max-seconds 175 \
  spinoffs/jukupoly/firmware/demons.com /tmp/demons.wav
spinoffs/jukupoly/render_jukupoly_wav.sh --max-seconds 320 \
  spinoffs/jukupoly/firmware/supaplex.com /tmp/supaplex.wav
spinoffs/jukupoly/render_jukupoly_wav.sh --max-seconds 25 \
  spinoffs/jukupoly/firmware/arkanoid.com /tmp/arkanoid.wav
```

The WAV is a timing-calibrated digital/acoustic reference, not a fitted model
of the CS00000 transistor driver, speaker, or enclosure.  See
[`THREE-VOICE.md`](THREE-VOICE.md#cycle-model-wav-rendering) for its exact timing and
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

The guarded M6 mixed DOOM library was physically exercised on 2026-09-01.
Four enhanced tracks, one unchanged-v1 control, Escape, library quit, and the
clean CP/M return executed on CS00000.  The session also supplied the decisive
negative result for the Imp compact-envelope candidate, which now selects a
generic fit fallback.  The listening matrix, exact tested and corrected disk
hashes, host statistics, and raw-capture hashes are retained in
[`sessions/cs00000-jukupoly-m6-physical/`](sessions/cs00000-jukupoly-m6-physical/README.md).

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
