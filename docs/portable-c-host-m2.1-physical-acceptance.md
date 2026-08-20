# Portable C host M2.1 physical acceptance

Status: **ACCEPTED ON CS00015 — M2.2 DOS DESK PORT SUBSEQUENTLY COMPLETE**

On 2026-08-20 the exact native-Linux M2 host was qualified against physical
CS00015 fitted with JukuNet C8 / ROM ABI 1.3. This closes M2.1 without changing
the admitted C host or adding a hardware-specific timing workaround.

## Bound identities

| item | accepted identity |
| --- | --- |
| `8080-cosim` source checkpoint | `4547aea12f1b59b622997c75aea8ad7b4db70748` |
| native executable | `jukuhost 0.1.0-m2` |
| executable SHA-256 | `09b20fc58d9383282528b90cc4af21405bb738d2c0149780f442a5dd056317ec` |
| C8 manifest | `c6b733ec1574594427e1f8485c19aa2aeb0a3c377586e3490cfce9c46e0273b8` |
| C8 ROM | `a54cb877edfe25e939e05ada0e98783acb53cfc8969071c63928b119c8e09e46` |
| Fastboot V16 stage | `44735bf468a2014bbcf327d5d0770d9fcf21a3c33704499282180ad6c95898ea` |
| CP/M system | `ec9b7fd00db2d8e70258aae74500fa261f987b6b04bddfdb5ab44e56ca2ba3f1` |
| A: base image | `0b8523d04dc6b936bb711666e3676e6742c78c8e05a25dd99d0bd79e4810ad8f` |
| B: native image | `1003053769cac8c8b8dc3fef21039f3ce55071d4274701fe929effff6dcdb8b6` |

The physical configuration was `/dev/ttyUSB0`, Fastboot at 19,200 8N1, then
NetDisk v3 and N4 at 19,200 8O1 with read-ahead 8. A: used a private writable
journaled copy; B: remained read-only.

## Physical matrix

| retained run | purpose | target commands | reads / records | writes | disk retries | result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `physical-CS00015-m2.1-linux-02` | powered-off cold start and full blind matrix | 15/15 | 70 / 560 | 5 | 0 | pass |
| `physical-CS00015-m2.1-linux-reconnect-01` | replace host while CP/M remains live | 15/15 | 77 / 616 | 12 | 0 | pass |
| `physical-CS00015-m2.1-linux-reset-01` | reset the already-powered target into a new boot | 4/4 | 33 / 264 | 4 | 0 | pass |

Together these runs accepted 34 commands, 180 disk reads carrying 1,440
records, 21 controlled writes and 14,073 total NetDisk/N4 requests. They cover
A: and B: directory/read paths, bidirectional N4 including bulk and remote-key
traffic, `STATUS`, repeated `DIAG ALL`, disk soak, writable-A: mutation, warm
boot, clean shutdown, live host replacement, and target reset recovery.

The replacement host resumed the live request sequence at `4C`; it did not
rebootstrap the target. Both cold paths restarted at sequence `01`. All three
hosts exited normally after one `SIGINT`, with no forced termination or
journal residue. From the first physical disk request to `A>` was 3.040 s in
both measured cold paths. The much larger runner-to-prompt intervals include
the deliberate wait for the operator to power or reset CS00015 and are not
boot benchmarks.

The cold logs contain aggregate `retries=382` and `retries=186`. These are
fully explained pre-target counters: `jukuhost` increments that field once per
32 unanswered resident-scanner probes while the board is still off or has not
yet been reset. The structured request traces prove zero NetDisk checksum,
range, duplicate or retransmission retries after the target appears. Fastboot's
final completion byte was not observed in either cold run; the designed
fallback did not resend the already accepted stream, and the first valid
NetDisk request confirmed completion.

## Evidence and regression

Each retained directory contains the snapshotted executable, manifest,
artifacts, workload and runner plus `host.log`, native log, raw `host.cap`,
`console.bin`, `events.jsonl`, `requests.jsonl`, boot evidence where applicable,
and the private post-run A: image. Their raw-capture hashes are:

- cold: `dfa8db314f97bbf6afc5f94652a63c051f94ab8299877abea34b8d972e87c94f`;
- reconnect: `17667cc1f629b8b07fe1106d58a65f2d1bea38c02e355334e7a06d4aaa7315ba`;
- reset: `126a799cac4c393e612958b868d9ba04917de646df8ac8256bc7cadb2985a51f`.

All three directories pass the independent physical-evidence auditor. Fresh
conversion of the three raw captures reproduced every `requests.jsonl` byte
for byte and reproduced boot evidence semantically, differing only in the new
conversion timestamp. The modelable Linux PTY and complete C8 simulator paths
also pass: N3/N4, native B:, duplicate handling, journal recovery, capture
events, C8 V16 boot, `DIR`, missed-ready recovery, target reset and host
replacement. Operator power latency and the physical UART's absent final
completion byte remain correctly classified as physical observations rather
than simulator facts.

One pre-run harness failure is retained separately. Linux returns `EIO` from a
PTY master before any slave is open; the runner had closed its own slave while
the C host intentionally waits until NetDisk before opening N4. The runner now
treats that transient state as “not connected yet”, and a delayed-slave
regression prevents recurrence. The offline resume auditor was also aligned
with the native host's `phase=netdisk` evidence instead of a retired Python-host
message. Neither correction changes target or wire behavior.

## Decision

M2.1 passes. The C host accepted at M2 is the physically qualified Linux
baseline for CS00015. The subsequent M2.2 desk port now provides a
reproducible 16-bit Open Watcom DOS executable for Pocket8086. M3 remains
blocked until its M2.3 physical comparison against this baseline passes; see
[portable-c-host-m2.2-dos-acceptance.md](portable-c-host-m2.2-dos-acceptance.md).
