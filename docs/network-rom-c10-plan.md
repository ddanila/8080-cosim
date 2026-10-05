# JukuNet C10 video-release contract

Status: **IMPLEMENTED AND DESK-QUALIFIED; D15/D16 PAIR READY TO PROGRAM;
PHYSICAL ACCEPTANCE PENDING**.

C9 / ABI 1.4 is immutable. Its physical evaluation on CS00000 proved the
network boot, CP/M, NetDisk, resident N4 console, diagnostics, writes, warm
boot, and host-replacement paths, but also found one release-blocking local
video initialization defect. C10 is the separately named successor that corrects
that defect and adds a guard for the full Port C state.

## Implemented candidate and desk qualification

C10 retains ABI 1.4 and the exact C9 loaded CP/M system and Fastboot V16
artifacts. Its successful boot emits PPI0 writes `82h, 0Fh, 0Eh`, verifies
PC7 low, and records final Port C `01h`. `STATUS 1.5` reports the complete
Port C value and POF state; `DIAG 0.7 VIDEO` fails if PC7 is high.

The immutable programming artifacts are:

| artifact | SHA-256 |
| --- | --- |
| combined C10 | `fbf9baaad9027a5335e3549da3a396eb999bbaae1a1f3f5f6e2f36798848a6bc` |
| D15 low | `a8e54e8ffac5b2654ba23f3dbff8acee17dd857d05f3654fa0fa9d23fdd58c7c` |
| D16 high | `e4c423a0d3bf2dea6ff69170787f67d6c481a07b246727625906293e5aea618e` |

The complete ABI/C-model fault matrix, C9-negative/C10-positive visible-frame
regression, structural HDL/POF gate, CP/M local and remote checks, production
native-host normal and replacement runs, media/layout checks, manifest-bound
physical-profile dry runs, and byte-reproducible package test pass. The
burn-ready package archive SHA-256 is
`d50a669101a87e7eb82994f94a3780a856c8451175451e93a89da287cfbde25f`.
Programming and physical promotion are distinct: the pair is ready for the
writer, while CS00000 cold-video, attended `VIDTEST`, and full workload
acceptance remain required after installation.

## PC7/POF release after POST

### Physical proof

The following sequence isolates the fault without inference from the screen
alone:

1. CS00000 displays correctly with RomBios 3.43m and the tested CP/M Plus 3.1 image in
   MODX mode. This controls the monitor, video hardware, framebuffer path,
   CP/M renderer, and MODX timer overrides.
2. The exact C9 pair boots the same machine, reaches CP/M, and passes its N4
   and disk workloads. Sync is present, but the local display remains entirely
   blank during a 60-second `VIDTEST`: no clear, border, text, or cursor.
3. RomBios 3.43m initially sets PPI0 PC7 with BSR byte `0Fh`, then resets it with
   BSR byte `0Eh` after POST and before installing the screen console. C9 sets
   `0Fh` but never emits the matching `0Eh`; its successful runtime Port C is
   therefore `81h` instead of `01h`.
4. A five-byte CP/M discriminator, `3E 0E D3 07 C9` (`MVI A,0Eh; OUT 07h;
   RET`), was loaded from a private cloned disk while C9 remained running.
   Local video returned immediately, before any reset or ROM replacement, and
   the following `VIDTEST` was visible.

The successful retained run is
`cpm-plus-juku/out/physical-CS00000-c9-pof-low-display-resume-20260827-01`.
Its acceptance runner and independent audit both pass 2/2 commands. The
unmodified blank-display control is
`cpm-plus-juku/out/physical-CS00000-c9-display-resume-20260827-01`.

This proves a C9 ROM-initialization defect. It is not a CS00000 hardware,
S21-mode, CP/M renderer, MODX, programmer, or host-console defect.

### Exact implementation contract

- Retain `82h` PPI0 mode setup and the initial `0Fh` BSR set during POST. This
  preserves the stock picture-off interval while RAM and ROM state are not yet
  ready for display.
- After every successful bounded POST check, emit `0Eh` to PPI0 control before
  copying/entering the runtime console and before changing to memory mode 1.
- Preserve every Port C bit other than PC7. The subsequent mode transition
  must retain the upper six bits and produce final Port C `01h`.
- POST failure paths remain in reset view with Port C `80h`, interrupts masked,
  and their existing audible C1--C5 reports.
- Do not hide the defect in CP/M, `VIDTEST`, or a startup utility. The ROM must
  establish the correct hardware state before the downloaded system executes.
- Keep the C9 images and hashes unchanged. The corrected bytes are emitted only
  under a separately named C10 combined image and D15/D16 pair.

This electrical correction does not by itself require a new ABI vector. C10
retains ABI 1.4. Runtime console switching belongs to the separate C12 release.

## Verification contract

The original gates checked the exact stock PIT sequence and the final memory
mode, but not the complete PPI0 Port C state. The abstract framebuffer could
therefore contain correct pixels while the physical mixer suppressed them.
The C10 automated gates cover the following; attended physical observation
remains a separate acceptance requirement:

- a reset-sequence guard proving ordered PPI0 writes `82h`, `0Fh`, then `0Eh`;
- successful boot/self-test checkpoints requiring complete Port C `01h`, not
  merely low bits `01b`;
- retained failure fixtures requiring Port C `80h` and mode 0;
- a digital POF visibility oracle: PC7 high classifies local pixels as
  suppressed and PC7 low permits the existing framebuffer/raster result;
- `STATUS` output that reports the current PPI0 Port C value and whether POF is
  released;
- a `DIAG VIDEO` check of POF plus renderer/timing state. Its wording must not
  claim that software has measured the analog VIDEO_OUT waveform or monitor picture;
  and
- an attended physical `VIDTEST` on a known-working display machine. A remote
  transcript alone is insufficient; a blank local result fails promotion.

The five-byte helper remains a bench discriminator only. It must not be
shipped as a normal recovery dependency or used to turn a failing C10 boot
into a passing acceptance result.

## C9 behavior to preserve

C9 physically established that the following implementation should carry
forward without redesign:

- unconditional 19,200-baud network boot for either value of reserved S21 bit
  0;
- bounded transmitter, receiver, prefix scan, and failure return;
- local-console authority with best-effort ordered N4 mirroring;
- recovery after immediate, repeated, and several-minute host outages without
  RESET;
- ABI 1.4 failure reason, flags, failed-operation, and reconnect telemetry;
- A:/B: reads, private-A writes/readback/erase, warm boot, long output, UI,
  history, status, diagnostics, bulk transfer, and soak;
- `0100h..9BFFh` TPA and all ABI 1.0--1.4 addresses and calling conventions;
  and
- zero clean-path target retries and UART errors in the retained passing
  physical runs.

The C10 POF change must not alter N3/N4, NetDisk-v3, Fastboot V16, D11 framing,
host replacement behavior, disk cache layout, or TPA.

## Disk continuity during host replacement

Keep the same disk contents when replacing the host under a running CP/M
session. CP/M retains directory/allocation state; replacing its volume with a
different image can invalidate that state. C10 does not invalidate CP/M caches
on host reconnection. Use a fresh boot when changing the mounted volume.

## Remaining physical acceptance

The completed implementation and desk gates do not establish physical
promotion of the named C10 pair. The sibling
`cpm-plus-juku/docs/c10-physical-acceptance-worksheet.md` owns its programming
and acceptance procedure. A bench run must bind the exact combined/D15/D16
hashes above and record built-in programmer verification.

On CS00000, require cold local video before network load, visible CP/M/MODX
output, attended `VIDTEST`, exact Port C `01h`, and the retained C9 workloads
with zero clean-path target retries/UART errors. The five-byte discriminator
cannot substitute for a correct C10 boot. The known-working RomBios 3.43m/C8 pairs
remain rollback paths.

Later C11/C12 features and their physical scope are described in the
[network-ROM overview](../spinoffs/jukuravi/network-rom/README.md).
[Runtime console switching](c12-runtime-console.md) is implemented in C12;
it is outside the immutable C10 contract.

## Reproduction

From this repository:

```sh
python3 spinoffs/jukuravi/network-rom/build_network_rom.py --check
sync/jukuhost_c10_cosim_check.sh
```

From the sibling `cpm-plus-juku` checkout, `make c10-check` checks the matching
system and `make c10-release-candidate` builds its reproducible package and
physical worksheet. Package production does not authorize programming or
establish physical acceptance.
