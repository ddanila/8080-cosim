# Juku packed-PCM speech experiment

Date: 2026-09-05

## Result

Standalone speech was reported intelligible in a calibrated 1.70 MHz cycle-model
trial. Its audio and recognition inputs were not retained, so the repository
does not independently establish intelligibility or physical speaker quality.
The dedicated player uses the D57 channel-1 mode-0 output as a pulse-width DAC,
stores two 4-bit samples per byte, and emits 8,056.872 samples/s.  Its hot loop
is strict Intel 8080 code and takes 422 cycles per packed pair.  The generic
implementation is `firmware/jukupoly-pcm-0100.asm` with the WAV converter
`firmware/build_jukupoly_pcm.py`.

The phrase tested was:

> Я твой слуга, я твой работник.

The trial used an independently resynthesized Russian voice, not the original
Kraftwerk recording. After high-frequency pre-emphasis and an eight-semitone
pitch reduction preserving duration, it produced a 2.803-second, 11,350-byte
program. The cycle-level D57 render was reported to transcribe as the exact
sentence above using the `turbo` Whisper model without a text prompt.

The source audio, program and rendered extracts were not committed, so this
recognition result cannot be rechecked from the repository. The checked-in
synthetic regression verifies playback mechanics; it does not establish speech
intelligibility or physical speaker quality.

## Build a new experiment

Given a PCM WAV you may use, these commands apply pre-emphasis, build the
transient and render its D57 output. They do not recreate the uncommitted
voice synthesis or pitch-shifted trial input:

```sh
ffmpeg -i phrase.wav -af 'treble=g=9:f=2000' phrase-preemphasized.wav
python3 spinoffs/jukupoly/firmware/build_jukupoly_pcm.py \
  phrase-preemphasized.wav SLUGA.COM --preview phrase-u4.wav
spinoffs/jukupoly/render_jukupoly_wav.sh \
  --lead 0 --tail 0 --sample-rate 96000 \
  SLUGA.COM phrase-juku-render.wav
```

The converter derives its target rate from the measured CPU clock, performs a
32-tap band-limited resample, peak-normalises, limits D57 codes so consecutive
pulses cannot overlap, and rejects images crossing the conservative `8000h`
TPA boundary.  The checked-in regression assembles a synthetic WAV, executes
the resulting transient in the cycle-level 8080/D57 model, checks duration and
write count, and checks return to the renderer's simulated CP/M entry point. Run it with:

```sh
python3 tests/jukupoly_pcm_test.py
```
