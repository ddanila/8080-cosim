# CRT decoder fork baseline

Baseline recorded: **2026-07-22**.

Status: **WP0-WP2 + EVIDENCE-LINKED SYNTHETIC JUKU WP3 GUARDED**.

This generated report records the CVBS-plan WP0 clean-checkout baseline and
the later fork-owned WP1/WP2 receiver follow-ups and the bounded WP3
synthetic Juku-timing fixture. The recorded unmodified fork point built
and passed its upstream synthetic NTSC
regression, then pins the float32/headless and explicit-profile E2E paths.
The WP3 fixture consumes exact Juku raster evidence, but it makes no
physical-VIDEO_OUT, framebuffer-agreement, or hardware claim.

## Command

```sh
python3 scripts/report_crt_decoder_baseline.py
```

This command validates fields in the retained
[baseline record](../ref/video/decoder-fork-baseline.json) and their agreement
with the CVBS plan. Artifact digests are checked for syntax, not recomputed
from a decoder checkout. Recorded build/test and CI outcomes are not rerun
or fetched here. The context commit is checked for ancestry only when it
exists in local Git history; a shallow checkout may skip that check.

## Recorded evidence checks

| Check | Result | Evidence |
| --- | --- | --- |
| Fork URL and fork point match the CVBS plan | PASS | fork, upstream, and 40-hex commit are identical in plan and record |
| The 8080-cosim context is a valid recorded revision | PASS | ae7918afe81024b462c8337dc23f509874e35e76; ancestry checked when history is present (CI checkout may be shallow) |
| Decoder source stayed unmodified | PASS | temporary detached checkout remained clean after build and test |
| Full fork build passed | PASS | CMake configured and built fam_dsp, famidec, and synth_ntsc |
| Upstream CTest passed | PASS | 1/1 synth_ntsc test passed |
| Direct synthetic NTSC result is internally complete | PASS | 29 frames; 7/7 bars |
| Temporary dependencies did not mutate host package state | PASS | development packages were extracted only below /tmp |
| Fork README provenance and deterministic-fixture policy are committed | PASS | fork `175cb65d`; upstream remained `6cce72d4` |
| Fork Linux CI builds RF/IQ and passes both test entry points | PASS | run 29885055666 at `feec5d7a`: full build + CTest + synth_ntsc |
| WP1 fork tip and bounded commits are pinned | PASS | five bounded commits ending at `d383beb3` |
| WP1 float32 source contract is explicit | PASS | LE f32; explicit rate; polarity/gain/offset; structural and finite checks |
| WP1 source and generated end-to-end tests pass | PASS | 999093 samples; 5/5 bars; 5 CLI failures |
| WP1 CI keeps the full RF/IQ route and all CTests green | PASS | run 29886015187 at `d383beb3`: full build + 3 CTests + synth_ntsc |
| WP2 profile receiver tip and artifacts are pinned | PASS | five bounded commits ending at `10bfa4b9` |
| WP2 independent non-NTSC fixture passes exactly | PASS | 768000 samples; 12500 Hz; 5/5 bars |
| WP2 telemetry guards measured lock, timing, and levels | PASS | line/frame lock; 12.5 kHz, 62.5 Hz, 6 us, blank and 0..100 IRE bounds |
| WP2 negative fixtures distinguish horizontal and frame loss | PASS | five generated failures; malformed vsync uniquely retains horizontal lock |
| WP2 CI keeps all receiver paths green | PASS | run 29886839537 at `10bfa4b9`: full build + 5 CTests + synth_ntsc |
| WP3 synthetic Juku fixture is source-pinned | PASS | decoder `b1d62c08` consumes raster evidence `eb4d6ab6` |
| WP3 ideal fixture carries the exact guarded raster contract | PASS | 64 us x 313; 5.04/223 us sync; 320x241; 5/5 bars |
| WP3 synthetic receiver CI preserves every route | PASS | run 29888769589 at `b1d62c08`: full build + 6 CTests + synth_ntsc |

## Pinned revisions

| Item | Value |
| --- | --- |
| Decoder fork | https://github.com/ddanila/famicom-rf-hackrf-decoder |
| Upstream | https://github.com/GOROman/famicom-rf-hackrf-decoder |
| Decoder commit | `6cce72d4a0e35ed364d086470191d61e3f6cd116` |
| Fork WP0 head | `feec5d7ac173fdc6389cd03a7da87eb175ccfc2e` |
| Fork WP1 head | `d383beb3dd038154364fb76f993ad32d12fe2d44` |
| Fork WP2 head | `10bfa4b9ae6c1ce071633459170b067fe3e2d91f` |
| Fork WP3 synthetic head | `b1d62c085e416c80cff35d8a77a8fbc397eead51` |
| WP3 raster source | `eb4d6ab6777db3f97306c9111e9c723c97dcf750` |
| 8080-cosim context | `ae7918afe81024b462c8337dc23f509874e35e76` |

## Recorded CI

- [WP0 build and synthetic NTSC](https://github.com/ddanila/famicom-rf-hackrf-decoder/actions/runs/29885055666)
- [WP1 float32/baseband](https://github.com/ddanila/famicom-rf-hackrf-decoder/actions/runs/29886015187)
- [WP2 explicit profiles and negative fixtures](https://github.com/ddanila/famicom-rf-hackrf-decoder/actions/runs/29886839537)
- [WP3 synthetic Juku timing](https://github.com/ddanila/famicom-rf-hackrf-decoder/actions/runs/29888769589)

Exact build/test measurements and environment details remain in the
[baseline record](../ref/video/decoder-fork-baseline.json). These are
recorded results; this report generator does not rerun the decoder.

## Compiler warnings

- GCC 15 warns that the channel HUD snprintf into an 8-byte buffer can truncate for an unconstrained integer channel.
- GCC 15 warns that the recording-time HUD snprintf into a 16-byte buffer can truncate for a sufficiently large or negative integer duration.

These HUD-format warnings do not affect `synth_ntsc`, but they should be
resolved in the decoder fork before treating GCC 15 warnings as a clean CI
baseline.

## Boundaries after the synthetic WP3 checkpoint

- the unresolved shared-DRAM video-slot schedule or physical Juku pixels
- D34_SIG, physical VIDEO_OUT voltage, or loaded analog behavior
- agreement with a Juku framebuffer or physical capture
- a built-in guessed Juku receiver preset

WP0-WP2 are complete at their generic boundaries: the fork owns provenance,
strict raw-float input, explicit timing profiles, measured lock telemetry,
positive/negative generated fixtures, and successful recorded build/test CI. The
bounded WP3 fixture additionally proves receiver lock at the exact guarded
Juku raster timing without promoting it to a built-in preset. Physical pixel
slots, D34_SIG/VIDEO_OUT integration, and framebuffer validation remain open.
