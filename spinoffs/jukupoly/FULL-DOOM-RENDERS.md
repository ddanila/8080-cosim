# Generic full-pack DOOM renders

## Result (2026-09-02)

Both pinned vgmrips DOOM packs now have a complete current-best JukuPoly
collection: 44 finite reusable-player executions, 44 48 kHz mono WAV files,
and 44 tagged MP3 files. The library delivers 23 guarded JPS v2 envelope
tracks and 21 explicit generic JPS v1 fallbacks. It contains no song-name,
track-number, source-hash, OPL-signature, or renderer exception.

The artifacts are intentionally untracked:

- library and native Juku floppy:
  `out/jukupoly-doom-library-current-best-20260902/`;
- WAV and MP3 collection:
  `out/jukupoly-doom-full-renders-current-best-20260902/`;
- full host-fit scores, accepted payloads, and replacement manifest:
  `out/jukupoly-doom-enhanced-generic-20260902/`.

The exact native 819,200-byte floppy SHA-256 is
`388564ead96cbc773ef02dfe5e46ff587284315e78f2e29fff155b558b990fe4`.
The library catalog SHA-256 is
`7598e1e791a58c6325acb1c12ec897def3b55ec291a8dd7c866b8d6b98d41eaa`.
[`DOOM-GENERIC-ENHANCED-PACK.json`](DOOM-GENERIC-ENHANCED-PACK.json) records
every candidate, timing choice, delivery gate, and fallback reason;
[`DOOM-FULL-RENDERS.json`](DOOM-FULL-RENDERS.json) records every JPS, WAV,
and MP3 hash plus the complete cycle-render profile.

## The apparent Imp regression

An intermediate directory named
`out/jukupoly-doom-full-renders-generic-20260902/` was rendered from the
all-v1 control library. Its catalog truthfully identifies Imp as
`unchanged-v1`, capability `00h`; that old reduction is known to omit the
opening low lead. Pointing to that directory as the full-pack result was a
workflow/artifact-selection mistake, not a regression in the enhanced
converter.

The independently generated generic full Imp candidate has no melodic
signature override. It starts three detuned members in frame zero, retains
all 506 protected onsets, and has the same row commands as the previously
working DETNEW excerpt through frame 1411 (28.22 seconds). The first later
difference is expected: the complete-source envelope fitter can see beyond
the old 30-second excerpt boundary. After generic host calibration, Imp uses
141 samples per frame and a 7,054 Hz phase table; C-cosim measures 7,053.08
samples/s, 50.0218 music frames/s, and 157.431 seconds. Its 11,705-byte JPS
SHA-256 is
`78bab88bbfd3bb14d6326c2299c19419c1ad3ddb922a4b323c4b3a19f0a5ca48`.
The final MP3 is:

`out/jukupoly-doom-full-renders-current-best-20260902/mp3/03-doom1-03-the-imp-s-song.mp3`

It has SHA-256
`3e9a70288857344841343b15d2a168e16e9433b952f74985b5c069e05fb4c464`;
after the intentional 250 ms lead silence, measured audio begins at 250.27 ms.

`render_jukupoly_library.py --minimum-enhanced-tracks N` is the workflow
guard added after this mistake. A current-best render now refuses an all-v1
control catalog before executing or encoding any track.

## Generic conversion and fallback policy

Every source receives the same host-side candidate policy:

1. reconstruct logical OPL voices and fit 4-bit envelopes;
2. allow only bounded ordinary-ADSR re-articulation;
3. choose the better existing target sustain state machine from oracle shape;
4. use fixed source-derived detuned members only on persistently spare voices;
5. profile the complete candidate in the cycle-level 8080 model;
6. search the hardware-supported 129–143 samples-per-frame range for the batch
   closest to 50 Hz and regenerate source-aware phase steps;
7. deliver v2 only when all shared onset, envelope, re-articulation, memory,
   sample-rate, pitch-table, duration, Escape-polling, and clock gates pass.

Failure never weakens a gate and never selects a hand-authored alternative.
The exact generic v1 conversion for that source is delivered instead. Across
the two packs, 16 candidates exceed the two-level per-note mean-envelope
error limit, three lose a significant envelope direction, one has an
unrepresentable bounded re-articulation, and five exceed the 32,767-byte JPS
hard limit; reasons can overlap. No final candidate failed timing.

The only new automatic fixed-patch classification rule is source-agnostic.
When the primary variable-pitch/chord classifier finds nothing, at least eight
repeated simultaneous attacks on three channels, containing at least two
pitches within one octave, constitute fixed-harmony evidence. This replaces
the old DOOM-title signature-ID list while rejecting the usual wide-pitch
kick/snare/cymbal cluster.

## Reproduction

Build the pinned oracle, candidates, library, and renders with:

```sh
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -Ispinoffs/jukupoly/external/Nuked-OPL3 \
  -o /tmp/jukupoly_opl_oracle \
  spinoffs/jukupoly/tools/jukupoly_opl_oracle.c \
  spinoffs/jukupoly/external/Nuked-OPL3/opl3.c

python3 spinoffs/jukupoly/tools/build_jukupoly_generic_pack.py \
  --doom '/path/to/Doom_(PC).zip' \
  --doom2 '/path/to/Doom_II_-_Hell_on_Earth_(IBM_PC_AT).zip' \
  --opl-oracle /tmp/jukupoly_opl_oracle \
  --output-dir out/jukupoly-doom-enhanced-generic-20260902 \
  --report spinoffs/jukupoly/DOOM-GENERIC-ENHANCED-PACK.json

python3 spinoffs/jukupoly/firmware/build_doom_library.py \
  --doom '/path/to/Doom_(PC).zip' \
  --doom2 '/path/to/Doom_II_-_Hell_on_Earth_(IBM_PC_AT).zip' \
  --generic-conversion \
  --replacement-manifest \
    out/jukupoly-doom-enhanced-generic-20260902/replacement-manifest.json \
  --replacement-dir out/jukupoly-doom-enhanced-generic-20260902/payloads \
  --output-dir out/jukupoly-doom-library-current-best-20260902

python3 spinoffs/jukupoly/tools/render_jukupoly_library.py \
  --library out/jukupoly-doom-library-current-best-20260902 \
  --output-dir out/jukupoly-doom-full-renders-current-best-20260902 \
  --minimum-enhanced-tracks 23 \
  --report spinoffs/jukupoly/DOOM-FULL-RENDERS.json
```

The two source archive SHA-256 values remain
`04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a`
and
`3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365`.
