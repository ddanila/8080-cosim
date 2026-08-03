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
- T28-compatible control PROBE: complete, RAM unchanged

Evidence: `jukuravi-logs-t31-real/20260803T150916.115911Z.json`.

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

Evidence: `jukuravi-logs-t31-call/20260803T151046.564402Z.json`.

This proves the required operating model on real hardware: a host can attach
without reset, upload arbitrary 8080 bytes, execute a cooperative snippet by
CALL, receive A and a RAM result block after ordinary RET, and keep the ROM
monitor resident for subsequent work.

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

The conservative 7-vote/20-ms defaults remain unchanged pending a larger and
more varied sample. The current fast experimental setting is 1 vote / 6 ms;
whole-command retry counts must remain visible in logs. Raw evidence:

- `jukuravi-logs-speed-v5-g12/20260803T152950.248602Z.*`
- `jukuravi-logs-speed-v3-g8/20260803T153445.958908Z.*`
- `jukuravi-logs-speed-v1-g8/20260803T153744.281550Z.*`
- `jukuravi-logs-speed-v1-g6/20260803T154002.040501Z.*`

Two earlier `v5-g12` sessions at `15:21:25Z` and `15:28:08Z` are invalid speed
samples: the direct CP2102 was accidentally opened at the host CLI's 115200-baud
default instead of 2400. Their RX logs contain only `00`, they transmitted zero
bytes, and they never reached RESYNC, CONFIG, or LOAD. They therefore say
nothing about five-vote or 12-ms reliability and are retained as diagnostic
evidence for always specifying `--baud 2400` on this direct adapter chain.

## Uploaded speaker demo

T31's resident loader was also used for an audible application experiment,
without RESET or another ROM burn. The first 118-byte iteration played the
correct twelve pitches but compressed the rests into uniform 60 ms gaps. It
uploaded in four first-attempt LOAD+CRC chunks, returned `A=0Ch`, left
`SMOK\0` at `4100h`, and was audibly recognized on CS00015. Evidence:
`jukuravi-logs-smoke-real/20260803T154837.479128Z.*`.

The corrected 134-byte version follows the published four-bar intro at 112 BPM.
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
`jukuravi-logs-smoke-rhythm-real/20260803T172545.786878Z.*`.

Source and committed payload:

- `spinoffs/jukuravi/firmware/smoke-4000.asm`
- `spinoffs/jukuravi/firmware/smoke-4000.bin`
