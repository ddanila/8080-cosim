# T31 physical validation on CS00015

> **D55 supersession, 2026-08-09:** the T31 D55 predicate latched Mode-0
> counts without first establishing the D54/D56 clocks required to transfer
> them into a real 8253 counting element. Its `D55: FAIL` result is not valid
> evidence of a D55 package or functional-path defect. Transport, RAM and
> loader findings in this record are unaffected. See
> [`../../docs/jukuravi-d55-diagnostic-audit.md`](../../docs/jukuravi-d55-diagnostic-audit.md).

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
- D55: FAIL (historical T31 bitmap; invalidated as D55 evidence by the
  2026-08-09 clock audit)
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

This session demonstrates host replacement without RESET, verified upload
and CALL/RET of the 29-byte fixture, and returned A and RAM results while the
ROM monitor remains resident. The general payload and execution requirements
are defined by [loader API v2](LOADER-API-V2.md).

## Upper D15 data reads versus instruction fetch

RAM-resident probes read the upper D15 bytes correctly and repeatedly,
including the `C3 0C 0A` trampoline at `106Fh`. A RAM jump directly to loader
entry `0A0Ch` succeeded, but jumping through that upper-ROM trampoline lost
the loader. Donor D2 substitution did not restore it. These observations did
not distinguish instruction fetch from data reads: both use `MEMR`.

The later [T32 investigation](T32-PHYSICAL.md#direct-d1-register-confirmation)
localized the failure to D1's 16-bit increment path. Incrementing an
already-high A12 cleared it, while carry into A12 and DAD remained correct.
The unchanged register probe passed after D1 replacement. The
[D1 analysis](../../docs/cs00015-d1-increment-analysis.md) owns the resolved
diagnosis and die-level limits; READY timing is not an outstanding diagnosis
of this repaired fault.

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

These runs support single-vote operation on the recorded CS00015 link under
the tested conditions; they do not establish reliability on another setup.
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

The recorded 134-byte image uploaded in five chunks at one vote / 6 ms guard.
Every LOAD and independent RAM CRC passed on its first attempt, with zero
parser-store retries or handshake mismatches. The operations took 32.758
seconds; execution returned `A=0Ch`, wrote `SMOK\0` to result RAM, and left
the T31 monitor active.

Capture: `sessions/smoke-rhythm-real/20260803T172545.786878Z.*`.
Accepted image SHA-256:
`db117afa1a150396094f624f2f00dc2ff938c13135ae098bc37f355d2bf8186e`.
The current `firmware/smoke-4000.asm` and `.bin` have changed; this physical
result qualifies only the recorded image.
