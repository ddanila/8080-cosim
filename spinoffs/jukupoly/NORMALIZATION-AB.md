# Experimental peak normalization A/B — 2026-09-05

The baseline 44-track library does not normalize each song to its own peak.
Its converter maps OPL total-level attenuation (0.75 dB steps) to a linear
editor volume, then to Juku's 1..15 tone levels. The source register settings
are not rendered waveform measurements: FM modulation, envelopes and summing
also affect the original sound.

The exact library built from the two pinned DOOM archives has only two tracks
whose selected melodic notes reach 15/15: Running From Evil and Shawn's Got
the Shotgun. Their full-scale levels occupy approximately 0.62% and 0.31% of
active tone-channel frame time respectively. No DOOM I melodic track reaches
15. Percussion PCM reaches 15 in 23 of 44 tracks. See
[NORMALIZATION-LEVELS.json](NORMALIZATION-LEVELS.json) for every track, source
register-derived melodic peak estimates and exact JPS identities.

## Trial policy

`tools/build_normalization_ab.py` accepts the baseline flat, held-envelope JPS
v1 format. It finds the largest tone-level nibble or filtered PCM sample, then
applies one fixed gain `15 / peak` to every tone level and PCM sample in that
song, rounding to the nearest integer with halves upward. This keeps zero
samples silent and avoids clipping either component. If either the tones or
drums already reach 15, the song remains byte-identical. It does not adjust
individual instruments independently or compress dynamics.

This is component peak normalization, not waveform peak normalization or
perceived-loudness matching. JukuPoly combines components with bitwise OR, not
linear addition; increasing individual levels can therefore change the blend.
Quantization also changes ratios slightly. No claim of lossless quality or
physical loudness improvement is made before listening. Pitch, row durations,
envelope flags, drum lengths, pointers and the playback engine are unchanged.

## Listening disk

| Menu | Song | Version | Shared gain |
| --- | --- | --- | --- |
| 01 | At Doom's Gate | Original | 1 |
| 02 | At Doom's Gate | Normalized | 15/9 = 1.667 |
| 03 | Suspense | Original | 1 |
| 04 | Suspense | Normalized | 15/8 = 1.875 |
| 05 | They're Going to Get You | Original | 1 |
| 06 | They're Going to Get You | Normalized | 15/4 = 3.75 |

Use physical Escape to stop, then select the paired track. Keep the hardware
volume unchanged during comparison. Listen for loudness, preserved melody/drum
balance, lost quieter details and roughness. Q returns to CP/M.

Build from a previously generated baseline library:

```sh
python3 spinoffs/jukupoly/tools/build_normalization_ab.py \
  --library build/jukupoly-doom-library \
  --output build/jukupoly-normalization-ab
```

Use Python 3.10+ for the preceding full DOOM library builder. On this macOS
machine the cpmtools binaries without libdsk autodetection are under
`../cpm-plus-juku/build/cpmtools-install/bin`; prepend that directory to PATH.
The resulting `normalization-ab.cpm` is a read-only native B: disk. The exact
[prepared disk](sessions/cs00014-normalization-ab/normalization-ab.cpm) is also
retained for use without rebuilding. Warm-boot
CP/M after exchanging media, then run `B:JUKEBOX`.

## Validation and physical boundary

The normalization regression covers exact shared scaling, untouched structure
and silence, idempotence, full-scale no-op behavior and corrupt/unsupported
input refusal. All 44 baseline payloads normalize without size changes and
reach a component peak of 15; a second normalization leaves them unchanged.

All six A/B payloads completed full 8080 cycle simulation under the exact
trial player. Each pair has identical frame counts, frame timing, sample-loop
timing, PIT-write counts and Escape-poll counts. Simulated durations are
97.051225, 174.639148 and 256.727122 seconds per pair. Detailed measurements,
payload identities and the disk hash are in
[NORMALIZATION-AB.json](NORMALIZATION-AB.json).

The disk was mounted on CS00014 with stock JF17 / 9600 recovery hosting.
A CP/M warm boot refreshed the changed B: media, and `B:JUKEBOX` reached
the six-entry selection prompt over N4. The machine was left waiting there;
[menu-console.bin](sessions/cs00014-normalization-ab/menu-console.bin) records
the warm boot, launch and menu. No trial song was started automatically.
The physical monitor was off during preparation; subjective listening and
normalization acceptance remain pending. The original 44-track disk remains
available separately and normalization is not enabled in the production build.
