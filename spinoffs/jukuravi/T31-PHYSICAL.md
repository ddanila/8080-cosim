# T31 physical validation on CS00015

Date: 2026-08-03  
Board: Arvutimuuseum Juku processor board `CS00015`  
ROM socket: D15, AT28C64B; D16 unpopulated  
Serial: X3 through MAX3232 and CP2102, 2400 baud

## Image

- DOS name: `T31HOST.BIN`
- ROM version: `1Ah`
- Self-CRC16: `72EF`
- SHA-256: `a4fed9185616bbfbef22ab6f0b18202e6d79ad7dbe3b7c46a77a700d3af3676c`
- Executed monitor boundary: loader ends at `0FFFh`

## Cold-boot probe

The ROM produced one happy beep and did not enter the T30 restart cycle. The
host decoded the exact `1A/72EF` banner, completed the adaptive handshake with
zero mismatches, and reported:

- PIC: PASS
- PPI: PASS
- D54: PASS
- D55: FAIL (the independently known CS00015 fault)
- D57: PASS
- RAM `4000h-4FFFh`: PASS
- RAM `C000h-CFFFh`: PASS
- loader API v2: READY at `0A00h`, maximum chunk 32 bytes
- loader API v2 control PROBE: complete, RAM unchanged

Evidence: `sessions/t31-real/20260803T150916.115911Z.json`.

## Resident attach, upload, and CALL/RET

After the first host exited, a new host process attached to the still-running
loader without RESET. It uploaded the 29-byte `return-4000.bin` to `4000h` in
one transaction, obtained exact readback, called it, and received:

- RUN acknowledged, one attempt
- returned A: `42h`
- RETURN replays: 0
- result RAM at `4100h`: `54 32 38 52 45 54 21 00` (`T28RET!\0`)
- result read attempts: 1
- final host status: `ok`

Evidence: `sessions/t31-call/20260803T151046.564402Z.json`.

This proves the required operating model on real hardware: a host can attach
without reset, upload arbitrary 8080 bytes, execute a cooperative snippet by
CALL, receive A and a RAM result block after ordinary RET, and keep the ROM
monitor resident for subsequent work.

## Upper D15 data reads versus instruction fetch

This investigation is a CS00015 physical result, not a general diagnosis of
all `.009` boards.  It began as an A12-alias test, but the evidence does not
show a simple stuck-low A12 address line:

| RAM-resident probe | Physical result |
| --- | --- |
| read `0017h` 16 times | `01h` on all 16 reads |
| read `1017h` 16 times | `FEh` on all 16 reads |
| read `100Ch` 16 times | `B1h` on all 16 reads |
| read `106Fh` 16 times | `C3h` on all 16 reads |
| read `1070h` 16 times | `0Ch` on all 16 reads |
| read `1071h` 16 times | `0Ah` on all 16 reads |

The lower and upper values differ where expected, and the four bytes around
the upper loader trampoline exactly match the burned T31 image.  Thus RAM code
can read the upper `1000h..1FFFh` half of D15 correctly and repeatably.

Execution distinguishes the failure:

- `rom-reenter-4000.bin` is `JMP 0A0Ch` entirely from RAM. It restarted the
  T31 loader, and a fresh host attached successfully. This proves the loader
  entry and host reattachment path independently of upper-ROM execution.
- `rom-exec-106f.bin` is `JMP 106Fh`. The bytes at `106Fh` are `C3 0C 0A`, so
  one correct upper-ROM instruction fetch should execute `JMP 0A0Ch` and
  restart the same loader. On CS00015 it did not return to the loader; repeated
  runs produced the failure tone or a non-responsive monitor.
- Replacing D2 with the donor D2 from the Danila Sukharev board did not make
  the `106Fh` execution probe succeed. This rules out the original D2 IC as
  the sole cause, but not the surrounding READY/decode/timing circuitry.

Cosim boots the exact T31 image, passes the lower and upper data probes, passes
RAM re-entry, and returns through the real `106Fh` trampoline. An intentionally
A12-low image instead aliases the upper 4 KiB to the lower 4 KiB and reaches
the expected `066Ch` HLT/250 Hz CPU-failure path. The regression therefore
proves that the probe distinguishes correct upper instruction fetch from the
simple A12-low case.

The narrow conclusion is: **CS00015 has correct upper-D15 data reads but fails
the tested upper-D15 instruction-fetch transition.** The failing component or
edge has not been localized. D15 contents, an ordinary A12-low data alias, the
original D2 package, the loader entry, and host reattachment are individually
excluded by the tests above. The PHI2TTL/READY route remains relevant to the
open timing investigation; its corrected schematic interpretation is recorded
in [`../../docs/phi2ttl-d29-clock-route.md`](../../docs/phi2ttl-d29-clock-route.md).

**Framing correction (desk analysis).** The "data read versus instruction
fetch" wording above is not a distinction this hardware can draw: `MEMR` is
asserted for both cycle types, the 8238 decodes only `INP`/`OUT`/`INTA`, and no
`M1`-derived net exists on the board, so no decode, chip select or wait input
can be fetch-selective. Deriving the D2 `.037` wait class of every page instead
shows that all five upper probes land inside `1000-10FF`, the single
**CAS-gated** class, while the lower probe and the loader entry `0A0Ch` are in
unwaited pages. The experiment therefore contrasted CAS-gated against unwaited
access, not upper against lower and not fetch against read. That analysis, the
per-page table, the refuted slow-EPROM hypothesis, the evidence that the
factory firmware itself calls into the CAS-gated pages, and two cheap
follow-up probes (an upper-half trampoline in the unwaited `1200-13FF` or
`1A00-1BFF`, and one in the always-wait `1400-17FF`) are recorded in
[`../../docs/d2-ready-cycle-analysis.md`](../../docs/d2-ready-cycle-analysis.md).

Physical evidence:

- `sessions/a12-low-real/20260803T193022.823717Z.*`
- `sessions/a12-high-real/20260803T193145.403259Z.*`
- `sessions/a12-upper-real/20260803T200107.338948Z.*`
- `sessions/a12-exec-real/20260803T193450.936728Z.*`
- `sessions/a12-exec-repeat-real/20260803T200253.089207Z.*`
- `sessions/a12-reenter-real/20260803T202000.424068Z.*`
- `sessions/a12-reenter-attach-real/20260803T202045.927340Z.*`
- `sessions/a12-d2swap-exec-real/20260803T204013.876817Z.*`
- `sessions/a12-d2swap-exec-retry-real/20260803T204159.038041Z.*`

The earlier aggregate attempt and failed attach/retry captures are retained as
raw chronology under the other `sessions/a12-*` directories. They are not
used as positive evidence. Reproducible sources, exact payloads, and the cosim
regression are `firmware/rom-a12-4000.*`, `firmware/rom-read-*`,
`firmware/rom-exec-106f*`, `firmware/rom-reenter-4000.*`, and
`tests/jukuravi_t31_a12_test.py`.

## Host-controlled transport speed experiment

The same T31 burn was benchmarked without RESET or a ROM change. The host
configured the vote count once per session and repeatedly wrote the 29-byte
`return-4000.bin` fixture to `4000h`. Every pass used an idempotent LOAD followed
by a separate ROM CRC over the written RAM. Three bounded whole-command attempts
were available, but none beyond the first was needed.

| Votes | Guard | Passes | Result | Retries | Mean LOAD + RAM CRC | Effective payload |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 12 ms | 5 | 5/5 | 0 | 45.299 s | 0.640 B/s |
| 3 | 8 ms | 5 | 5/5 | 0 | 22.465 s | 1.291 B/s |
| 1 | 8 ms | 10 | 10/10 | 0 | 7.628 s | 3.802 B/s |
| 1 | 6 ms | 10 | 10/10 | 0 | 6.847 s | 4.235 B/s |

All 30 passes also had zero parser-buffer store retries and zero handshake
mismatches. In particular, all 20 single-vote passes succeeded on their first
LOAD and first CRC command. Single-vote/6-ms was 6.62 times faster than the
first 5-vote/12-ms setting in this experiment.

This is evidence that majority voting is unnecessary on the presently assembled
CS00015 link under the tested conditions, not proof that it can never fail.
CRC-8 framing, the command CRC-16 over the parser buffer, the LOAD result's data
CRC, and an independent CRC over target RAM retain detection. LOAD is idempotent,
so the simpler operational policy is to let the host resend the complete command
when any layer rejects it or times out. Exact READ remains available for a final
high-assurance comparison.

The host now defaults to the proven 1-vote / 6 ms setting. CRC-protected
whole-command retries remain enabled, while `--loader-guard-ms` and
`--loader-votes` can add margin for another physical link. Raw evidence:

- `sessions/speed-v5-g12/20260803T152950.248602Z.*`
- `sessions/speed-v3-g8/20260803T153445.958908Z.*`
- `sessions/speed-v1-g8/20260803T153744.281550Z.*`
- `sessions/speed-v1-g6/20260803T154002.040501Z.*`

## Uploaded speaker demo

The 134-byte speaker demo follows the published four-bar intro at 112 BPM.
It expresses the phrase as exactly 32 eighth-note units (267.857 ms ideal),
including the notated rests, direct D-flat-to-C transition, and sustained final
G. Cosim measured the first twelve note onsets at nominal milliseconds:

```text
0.0  535.8  1071.6  1875.3  2411.1  2946.9
3214.9  4286.4  4822.2  5358.1  6161.7  6697.6
```

On CS00015, the corrected image uploaded as four 32-byte chunks plus six bytes.
Every LOAD and independent RAM CRC succeeded on its first attempt at one vote /
6 ms guard, with zero parser-store retries and zero handshake mismatches. The
five LOAD+CRC operations took 32.758 seconds. Execution returned `A=0Ch`, RAM
contained `53 4D 4F 4B 00` (`SMOK\0`), and the T31 monitor remained active. The
operator confirmed the revised timing sounded better. Evidence:
`sessions/smoke-rhythm-real/20260803T172545.786878Z.*`.

Source and committed payload:

- `spinoffs/jukuravi/firmware/smoke-4000.asm`
- `spinoffs/jukuravi/firmware/smoke-4000.bin`
