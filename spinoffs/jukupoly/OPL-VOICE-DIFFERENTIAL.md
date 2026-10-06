# Isolated OPL voice differential

This is the normal diagnostic path for an OPL-to-Juku discrepancy. Whole-song
listening remains useful as a final test, but it is too ambiguous for deciding
which converter rule is wrong.

## Method

`tools/compare_jukupoly_opl_voice.py` starts with one unchanged VGM/VGZ and
performs the following host-only work:

1. reconstruct every keyed OPL segment and strict same-pitch logical layer;
2. select one logical note by stable identifier, or by time with an optional
   rounded MIDI-pitch filter;
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
or restart a selected envelope halfway through. The default window includes
250 ms before key-on (clipped at the source start) and 1.5 seconds after key-off,
then rounds both boundaries outward to the 20 ms analysis grid.

## Host/target boundary

The host parses OPL, reconstructs voices, chooses source members, fits envelope
and re-articulation packets, quantizes pitch, renders the reference, and creates
comparison evidence. Juku only reads precomputed 50 Hz packets, advances its
small 4-bit envelope state, and mixes at most three fixed-step pulse voices.
The differential work therefore adds no target opcode or per-sample cost.

When several source members quantize to one identical Juku phase step, their
direct amplitudes are summed and fitted as one composite target envelope.
This preserves complementary OPL envelopes without wasting a physical target
voice on an indistinguishable pitch. Genuinely different phase steps can use
the remaining voices.

## First case: The Imp's Song intro

The opening low F-sharp is logical note 0 in the pinned Doom source. Its
four keyed OPL members produce three distinct target phase steps. Channels 0
and 2 quantize to the same step but have complementary loudness contours;
selecting only one member would discard audible content. The converter fits
those equal-step members as a composite and uses the other two target voices
for the distinct steps.

The isolated score measures its C-cosim execution rate and regenerates phase
steps on the host for up to three calibration renders. Convergence is not an
exit condition after the final render; inspect `host_calibration`, the phase
table rate and the measured sample rate in `comparison.json`.
Use the generated `comparison.json` and contour CSV to
inspect pitch error, envelope fit and rendered loudness for the exact inputs.
For this note, directly audible source AM is folded into host-generated
envelopes and bounded re-articulations; the 8080 does not emulate an OPL LFO.

## Reproduction

Use Python 3.10+, Git and a C compiler available as `cc`. Initialize the
Nuked OPL3 and zmac submodules; the script verifies the pinned Nuked revision
and builds both host renderers. Follow the
[assembler setup](README.md#reproduce) for the zmac build requirements or
a compatible `ZMAC` override.

Extract the source from the pinned DOOM archive identified in
[the full-pack guide](FULL-DOOM-RENDERS.md). The archive is not committed.
From the repository root:

```sh
python3 -m zipfile -e '/path/to/Doom_(PC).zip' out/jukupoly-doom-source

python3 spinoffs/jukupoly/tools/compare_jukupoly_opl_voice.py \
  "out/jukupoly-doom-source/03 The Imp's Song.vgz" \
  out/jukupoly-imp-isolated-voice --logical-note 0
```

Use a fresh output directory for each comparison. The script overwrites named
files in an existing directory without clearing it; a failed run can leave
partial outputs.

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

The printed `JUKUPOLY-VOICE-DIFF: PASS` means evidence generation completed,
not that the conversion met a quality threshold. Inspect the pitch, envelope
and loudness metrics in `comparison.json`, the contour CSV and both audio
renders before accepting the candidate.

The final gate is still human comparison on the physical speaker. Only the
isolated candidate and then the corrected whole song should be taken to
CS00000; hardware listening is not used to choose arbitrary parameters.
