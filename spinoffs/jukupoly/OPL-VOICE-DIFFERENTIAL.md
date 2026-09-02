# Isolated OPL voice differential

This is the normal diagnostic path for an OPL-to-Juku discrepancy. Whole-song
listening remains useful as a final test, but it is too ambiguous for deciding
which converter rule is wrong.

## Method

`tools/compare_jukupoly_opl_voice.py` starts with one unchanged VGM/VGZ and
performs the following host-only work:

1. reconstruct every keyed OPL segment and strict same-pitch logical layer;
2. select one logical note by stable identifier, time, and optionally MIDI
   pitch;
3. retain all operator, pitch, key, feedback, connection, waveform, and global
   LFO-depth writes affecting its physical members;
4. force every unrelated key and hardware-rhythm trigger off;
5. render that register stream with pinned Nuked OPL3;
6. reduce the same selected members to at most three Juku pulse voices;
7. compile a standalone 8080 player and render its real D57 writes with the
   cycle-level C model; and
8. compare semantic pitch, oracle-derived 4-bit envelopes, and a normalized
   50 Hz loudness contour.

The loudness comparison intentionally uses 20 ms RMS blocks, 100 ms smoothing,
independent level normalization, and onset alignment. It never compares FM
PCM and pulse-wave PCM sample-for-sample: their timbre and harmonics cannot be
meaningfully equal. The generated CSV remains available when aggregate
statistics hide a local problem.

For a late note, the extractor collapses preceding writes into a sample-zero
register-state prime with every key off. It does not replay the preceding song
or restart a selected envelope halfway through. The default window starts up
to 250 ms before the actual key-on and ends 1.5 seconds after key-off.

## Host/target boundary

The host parses OPL, reconstructs voices, chooses source members, fits envelope
and re-articulation packets, quantizes pitch, renders the reference, and creates
comparison evidence. Juku only reads precomputed 50 Hz packets, advances its
small 4-bit envelope state, and mixes at most three fixed-step pulse voices.
The differential work therefore adds no target opcode or per-sample cost.

When several source members quantize to one identical Juku phase step, their
direct amplitudes are now summed and fitted as one composite target envelope.
This preserves complementary OPL envelopes without wasting a physical target
voice on an indistinguishable pitch. Genuinely different phase steps can use
the remaining voices.

## First case: The Imp's Song intro

The hash-pinned Doom source reconstructs the opening low F-sharp as logical
note 0, MIDI pitch 41.974, from four OPL channels keyed continuously from
0.000 to 14.120 seconds. It has three distinct target phase steps. OPL
channels 0 and 2 quantize to the same step but have complementary loudness
lobes; channels 0/1 dominate alternating lobes while channel 2 fills their
gaps. The old policy retained only the highest-total-energy member for each
step, so it discarded channel 2 and created long silent gaps.

The generic equal-step grouping fixes that policy error. The target now uses:

- step 845 for the composite of source channels 0 and 2;
- step 839 for source channel 1; and
- step 848 for source channel 3.

The isolated score first measures its exact C-cosim execution rate and then
regenerates phase steps on the host; it converges from the full-song 7,170 Hz
seed to 7,188 Hz in two passes. The worst measured pitch error is 0.969 cents.
Relative to the previous static-member selection, rendered-contour median
absolute error fell from 2.99 to 0.97 dB, 90th-percentile error fell from
54.22 to 6.17 dB, and correlation rose from 0.557 to 0.832. The large silent
gaps disappeared. The current composite
member fit has 0.365 levels sample-weighted mean error; its brief maximum error
is three of fifteen levels.

The source uses AM on a directly audible path and no directly audible vibrato
for this note. In the detuned-member reduction its post-AM 50 Hz contour is
folded into host-generated envelopes and bounded re-articulations. No OPL LFO
is emulated by the 8080 for this case.

## Reproduction

From the repository root:

```sh
python3 spinoffs/jukupoly/tools/compare_jukupoly_opl_voice.py \
  "out/jukupoly-m6-representative/sources/03 The Imp's Song.vgz" \
  out/jukupoly-imp-isolated-voice --logical-note 0
```

Important outputs are:

- `source-logical-notes.json` — selectable source-note catalog;
- `source-voice.jop` and `source-voice-probes.csv` — auditable isolated OPL
  register stream and 50 Hz oracle state;
- `01-opl-reference.wav` — pinned Nuked OPL3 reference;
- `juku-voice-score.json` and `juku-voice.com` — host-reduced target data;
- `02-juku-cosim.wav` — actual 8080/D57 execution render;
- `03-opl-then-juku.wav` — level-matched listening pair; and
- `comparison.json` plus `envelope-contours.csv` — semantic and perceptual
  evidence.

The final gate is still human comparison on the physical speaker. Only the
isolated candidate and then the corrected whole song should be taken to
CS00000; hardware listening is not used to choose arbitrary parameters.
