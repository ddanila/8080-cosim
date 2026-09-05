# Juku packed-PCM speech experiment

Date: 2026-09-05

## Result

Short speech is practical on the stock 1.70 MHz Juku when it is played alone.
The dedicated player uses the D57 channel-1 mode-0 output as a pulse-width DAC,
stores two 4-bit samples per byte, and emits 8,056.872 samples/s.  Its hot loop
is strict Intel 8080 code and takes 422 cycles per packed pair.  The generic
implementation is `firmware/jukupoly-pcm-0100.asm` with the WAV converter
`firmware/build_jukupoly_pcm.py`.

The phrase tested was:

> Я твой слуга, я твой работник.

The original Kraftwerk recording was located and the bridge voice was
separated locally.  Unprompted speech recognition recovered the exact phrase
from the 16 kHz separation, but the vocoder carrier and backing are entangled:
vocal-only separation loses essential speech information, while retaining the
carrier also retains some music.  No publicly indexed standalone original
sample or stem was found in targeted Russian, English, and German searches.
The original recording and all derived extracts remain uncommitted.

For a clean playback proof, the exact recognized text was independently
resynthesized in Russian, given a broad high-frequency pre-emphasis, and
shifted down eight semitones while preserving duration before conversion.
This is explicitly a resynthesis, not a claim that the generated voice is the
Kraftwerk master sample.  The generated 2.803-second program is
11,350 bytes.  The complete cycle-level D57 render was transcribed without a
text prompt as the exact sentence above by the `turbo` Whisper model.  The
rendered phrase's average log probability was -0.154; the recognizer assigned
0.946 probability to `слуга` and 0.975 to `работник` in the final check.  The
decoded pre-D57 4-bit preview was not used as the acceptance gate because its
recognition was less stable than the actual pulse render.

## Reproduction

The source WAV is intentionally local.  Given an allowed PCM WAV:

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
write count, and proves clean return to CP/M.

## Rejected paths

- The music-contaminated original separation was not represented as a clean
  sample even though its full-band recognition passed.
- 11.26 kHz was rejected because the shorter period permits only eleven safe
  D57 pulse widths and reduced recognition accuracy.
- A packed one-bit sigma-delta prototype fit easily and ran at about 30.6 kHz,
  but its cycle-rendered output failed the recognition gate.
