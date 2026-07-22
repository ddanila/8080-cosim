# CRT decoder fork baseline

Status date: **2026-07-22**.

Status: **UPSTREAM BASELINE REPRODUCED / FORK README AND CI PENDING**.

This generated report records CVBS-plan WP0 work performed in a temporary,
detached checkout. It proves that the recorded unmodified decoder fork point
builds and passes its upstream synthetic NTSC regression on the named host.
It makes no Juku baseband, X7, receiver-lock, or hardware claim.

## Command

```sh
python3 scripts/report_crt_decoder_baseline.py
```

## Provenance checks

| Check | Result | Evidence |
| --- | --- | --- |
| Fork URL and fork point match the CVBS plan | PASS | fork, upstream, and 40-hex commit are identical in plan and record |
| The 8080-cosim context commit exists | PASS | ae7918afe81024b462c8337dc23f509874e35e76 |
| Decoder source stayed unmodified | PASS | temporary detached checkout remained clean after build and test |
| Full fork build passed | PASS | CMake configured and built fam_dsp, famidec, and synth_ntsc |
| Upstream CTest passed | PASS | 1/1 synth_ntsc test passed |
| Direct synthetic NTSC result is internally complete | PASS | 29 frames; 7/7 bars |
| Temporary dependencies did not mutate host package state | PASS | development packages were extracted only below /tmp |

## Recorded environment

| Item | Value |
| --- | --- |
| Decoder fork | https://github.com/ddanila/famicom-rf-hackrf-decoder |
| Upstream | https://github.com/GOROman/famicom-rf-hackrf-decoder |
| Decoder commit | `6cce72d4a0e35ed364d086470191d61e3f6cd116` |
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

The direct run reported 87 coasted lines and still recovered all seven
golden color bars within the upstream tolerance.

## Compiler warnings

- GCC 15 warns that the channel HUD snprintf into an 8-byte buffer can truncate for an unconstrained integer channel.
- GCC 15 warns that the recording-time HUD snprintf into a 16-byte buffer can truncate for a sufficiently large or negative integer duration.

These HUD-format warnings do not affect `synth_ntsc`, but they should be
resolved in the decoder fork before treating GCC 15 warnings as a clean CI
baseline.

## Remaining WP0 work

- HackRF hardware access or RF reception
- Juku baseband ingestion or non-NTSC synchronization
- decoder-fork CI configuration
- fork README provenance changes
- any Juku X7 receiver or image claim

The fork's README provenance and CI are intentionally not changed from this
repository. Those are separate-repository writes and remain pending.
