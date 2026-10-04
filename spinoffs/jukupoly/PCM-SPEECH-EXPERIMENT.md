# Juku packed-PCM speech experiment

The dedicated player uses the D57 channel-1 mode-0 output as a pulse-width DAC
and stores two 4-bit samples per byte. At the default 1.70 MHz effective CPU
rate it averages 8,056.872 samples/s. The current 8080 cycle model takes 422
cycles per packed pair, including the final iteration; sample writes alternate
between 197- and 225-cycle spacing.
The implementation is `firmware/jukupoly-pcm-0100.asm` with the WAV converter
`firmware/build_jukupoly_pcm.py`.

The checked-in synthetic regression verifies playback mechanics. Speech
intelligibility and physical speaker quality remain unverified by retained
evidence.

## Build a new experiment

Run from the repository root with Python 3.10+, FFmpeg and a C compiler
available as `cc`. Initialize the zmac submodule; the builder uses `make`
if its executable is absent, or uses `ZMAC`.

Given an uncompressed integer PCM WAV, these commands apply pre-emphasis,
build the CP/M program and render its D57 output:

```sh
ffmpeg -i phrase.wav -af 'treble=g=9:f=2000' phrase-preemphasized.wav
python3 spinoffs/jukupoly/firmware/build_jukupoly_pcm.py \
  phrase-preemphasized.wav SPEECH.COM --preview phrase-u4.wav
spinoffs/jukupoly/render_jukupoly_wav.sh \
  --lead 0 --tail 0 --sample-rate 96000 \
  SPEECH.COM phrase-juku-render.wav
```

The converter derives its target rate from `--cpu-hz` (default 1700000), performs
a 32-tap band-limited resample, peak-normalises, and rejects images crossing
the conservative `8000h` TPA boundary. Use the same `--cpu-hz` when rendering.

Its pulse-code limit uses the average sample interval and a fixed 2 MHz PIT
clock. It does not guarantee non-overlap at the shorter interval: at defaults,
code 15 requests 120 microseconds while 197 CPU cycles take about 115.9
microseconds. The renderer merges overlapping pulses; the decoded `--preview`
WAV instead represents uniformly spaced quantized samples. Neither output
establishes the physical speaker response.

The checked-in regression assembles a synthetic WAV, executes
the resulting transient in the cycle-level 8080/D57 model, checks duration and
write count, and checks return to the renderer's simulated CP/M entry point. Run it with:

```sh
python3 tests/jukupoly_pcm_test.py
```
