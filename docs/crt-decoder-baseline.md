# CRT decoder fork baseline

Status date: **2026-07-22**.

Status: **WP0 BASELINE + GENERIC BASEBAND WP1 GUARDED**.

This generated report records the CVBS-plan WP0 clean-checkout baseline and
the later fork-owned WP1 generic baseband follow-up. It proves that the
recorded unmodified fork point builds and passes its upstream synthetic NTSC
regression, then pins the separate float32/headless E2E implementation.
It makes no Juku-timing, physical-X7, framebuffer-agreement, or hardware claim.

## Command

```sh
python3 scripts/report_crt_decoder_baseline.py
```

## Provenance checks

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

## Recorded environment

| Item | Value |
| --- | --- |
| Decoder fork | https://github.com/ddanila/famicom-rf-hackrf-decoder |
| Upstream | https://github.com/GOROman/famicom-rf-hackrf-decoder |
| Decoder commit | `6cce72d4a0e35ed364d086470191d61e3f6cd116` |
| Fork WP0 head | `feec5d7ac173fdc6389cd03a7da87eb175ccfc2e` |
| Fork WP1 head | `d383beb3dd038154364fb76f993ad32d12fe2d44` |
| 8080-cosim context | `ae7918afe81024b462c8337dc23f509874e35e76` |
| Host | Ubuntu resolute amd64 |
| CMake | 4.2.3 |
| Compiler | g++ 15.2.0 |
| Dependency isolation | No host packages installed. Ubuntu packages libhackrf-dev 2026.01.3-1, libhackrf0 2026.01.3-1, and libsdl2-dev 2.32.10+dfsg-6 were downloaded and extracted under /tmp; the already-installed libsdl2-2.0-0 2.32.10+dfsg-6 runtime was copied into that temporary sysroot. |

## Results

| Test | Result | Time | Max RSS |
| --- | --- | ---: | ---: |
| CTest | 1/1 passed | 0.61 s | 20604 KiB |
| direct synth_ntsc | 29 frames; 7854 lines; 7/7 bars | 0.62 s | 19128 KiB |
| fork Linux CI | full RF/IQ build + CTest + synth_ntsc PASS ([run 29885055666](https://github.com/ddanila/famicom-rf-hackrf-decoder/actions/runs/29885055666)) | 42 s | GitHub-hosted runner |
| baseband source CTest | PASS; 5 validation/transform cases | included in CI | GitHub-hosted runner |
| generated baseband E2E | 5 frames; 5/5 exact grayscale bars | included in CI | GitHub-hosted runner |
| WP1 fork Linux CI | full build + 3 CTests + synth_ntsc PASS ([run 29886015187](https://github.com/ddanila/famicom-rf-hackrf-decoder/actions/runs/29886015187)) | 27 s | GitHub-hosted runner |

The direct run reported 87 coasted lines and still recovered all seven
golden color bars within the upstream tolerance.

## Compiler warnings

- GCC 15 warns that the channel HUD snprintf into an 8-byte buffer can truncate for an unconstrained integer channel.
- GCC 15 warns that the recording-time HUD snprintf into a 16-byte buffer can truncate for a sufficiently large or negative integer duration.

These HUD-format warnings do not affect `synth_ntsc`, but they should be
resolved in the decoder fork before treating GCC 15 warnings as a clean CI
baseline.

## Boundaries after WP1

- non-NTSC or Juku timing-profile synchronization
- physical Juku X7 voltage or loaded analog behavior
- agreement with a Juku framebuffer or physical capture

WP0 and generic-input WP1 are complete: the fork owns its provenance,
deterministic-fixture policy, strict raw-float source, headless E2E path, and
green full-build/test CI. The remaining items belong to WP2-WP5 or physical
validation.
