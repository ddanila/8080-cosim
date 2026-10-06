# Generic full-pack DOOM renders

## Offline render set (2026-09-02)

The recorded render set for both pinned vgmrips DOOM packs contains
44 finite reusable-player executions, 44 48 kHz mono WAV files,
and 44 tagged MP3 files. The library delivers 23 guarded JPS v2 envelope
tracks and 21 explicit generic JPS v1 fallbacks. It contains no song-name,
track-number, source-hash, OPL-signature, or renderer exception.

Audio and library outputs are untracked.
[`DOOM-GENERIC-ENHANCED-PACK.json`](DOOM-GENERIC-ENHANCED-PACK.json) records
every candidate, timing choice, delivery gate, and fallback reason;
[`DOOM-FULL-RENDERS.json`](DOOM-FULL-RENDERS.json) records every JPS, WAV,
and MP3 hash plus the complete cycle-render profile.

## Qualification boundary

This offline render set contains 23 capability-01 envelope candidates and 21
JPS1 fallbacks. It is separate from the physically exercised M6 mixed library
with four enhanced tracks and 40 fallbacks, recorded in
[OPL-PLAN-STATUS.json](OPL-PLAN-STATUS.json). The offline count does not expand
physical listening qualification. Corrected M7 Imp candidates still require
CS00000 A/B before promotion.

`render_jukupoly_library.py --minimum-enhanced-tracks N` checks the catalog's
declared enhanced count. It separately verifies song hashes and compares
`JUKEBOX.COM` with a fresh player build for the declared capabilities; it does
not independently recount enhanced payloads. Exact JPS and render identities
are in the linked JSON reports. WAVs are cycle-model references, not an analogue
model of the physical speaker or enclosure.

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
The exact generic v1 conversion for that source is delivered instead. Per-track
failure reasons and gate totals belong to
[the recorded pack report](DOOM-GENERIC-ENHANCED-PACK.json).

Fixed-harmony classification is source-agnostic and distinguishes repeated
chord attacks from wide-pitch percussion clusters. The exact thresholds are
implemented by [the generic converter](tools/build_jukupoly_generic_pack.py)
and its voice-classification helpers.

## Reproduction

Run from the repository root with Python 3.10+, a C11 compiler available as
`cc`, cpmtools,
FFmpeg with `libmp3lame`, and `ffprobe`. Initialize the Nuked OPL3 submodule
and follow the [assembler setup](README.md#reproduce) for zmac.

These commands write rerun artifacts and reports under `out/`, preserving
both tracked snapshot reports. Use a new output directory for each comparison.
The renderer does not clear old files; failures can leave partial audio, and
aggregate checks occur after writing `manifest.json` and `--report`.
Check the exit status and report gates before accepting a set.

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
  --output-dir out/jukupoly-doom-enhanced-generic \
  --report out/jukupoly-doom-enhanced-generic/report.json

python3 spinoffs/jukupoly/firmware/build_doom_library.py \
  --doom '/path/to/Doom_(PC).zip' \
  --doom2 '/path/to/Doom_II_-_Hell_on_Earth_(IBM_PC_AT).zip' \
  --generic-conversion \
  --replacement-manifest \
    out/jukupoly-doom-enhanced-generic/replacement-manifest.json \
  --replacement-dir out/jukupoly-doom-enhanced-generic/payloads \
  --output-dir out/jukupoly-doom-library

python3 spinoffs/jukupoly/tools/render_jukupoly_library.py \
  --library out/jukupoly-doom-library \
  --output-dir out/jukupoly-doom-full-renders \
  --minimum-enhanced-tracks 23 \
  --report out/jukupoly-doom-full-renders/report.json
```

The two source archive SHA-256 values remain
`04ffbf72e47727b3e93c1e99a68311a460b85fc31fd9a1645e3d872231c0e12a`
and
`3d255c644e52adc2967df8394086d99d7995da71c4adf83bec0fe3bccc51c365`.
