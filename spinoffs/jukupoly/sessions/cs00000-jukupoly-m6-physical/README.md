# CS00000 guarded M6 mixed-library physical session

This records the 2026-09-01 physical listening run of the first guarded M6
mixed DOOM library on Juku CS00000.  The exact tested 800 KiB B: image had
SHA-256 `6f61b809f4b5ac1450215742bd0162fcb1900c66c3b358cfe2000c84fabf350c`:
five enhanced payloads and 39 unchanged JPS v1 payloads under the 5,632-byte
capability-`07h` player.

The machine cold-booted CP/M Plus 3.1 over C10/NetDisk v3 at 19200 baud from
the private A: image, mounted the library read-only as B:, entered the Jukebox,
played the requested tracks, quit with `Q`, and returned to `A>`.  The final
host statistics were 19,171 requests, 116 successful reads (928 records),
zero writes, zero retries, zero boot restarts, zero target resets, zero
reconnects, and zero UART errors.

The listening matrix was:

| Track | Result |
|---|---|
| 02 At Doom's Gate | Complete playback; operator: “sounds decent.” |
| 03 The Imp's Song | Failed enhanced-fit qualification: the low lead entered immediately but sounded like a constant-volume tone, while the OPL source fades quickly. Stopped with Escape. |
| 04 Dark Halls | Operator: “acceptable”; generally good but too difficult to judge precisely. Stopped with Escape. |
| 06 Suspense | Operator: generally good, but too difficult to judge precisely. Stopped with Escape. |
| 41 Opening to Hell | Completed cleanly while the operator was away; no subjective assessment. |
| 05 Kitchen Ace | Unchanged-v1 compatibility control completed cleanly while the operator was away; no subjective assessment. |

The Imp failure was traced offline to a general representation problem, not a
track-specific patch.  Its first logical note merges four same-pitch OPL
layers with staggered renewed volume rises.  A single compact Juku ADSR cannot
represent those multiple keyed articulations.  A new generic delivery guard
rejects a note when it has a renewed keyed rise/fall of at least four mixer
levels and the best compact fit still exceeds two levels mean absolute error.
The full Imp candidate has 12 such notes and now receives the unchanged-v1
fit fallback.

That fallback changes the corrected disk SHA-256 to
`af0f44865952ca02cfae3b310b35a356d679a507566f41f8028e0f1680015bf9`
and its distribution to four enhanced plus 40 v1 tracks.  The player and the
other four enhanced payloads are byte-identical to the physical run.  Thus
this session qualifies their target execution and records the Imp candidate's
listening failure; it is not presented as a boot of the corrected disk hash.

The 5.8 MB raw capture and native log remain untracked under
`out/jukupoly-m6-physical-20260901-01/`.  Their hashes and the exact command are
recorded here without adding a large wire capture to the source repository.

## SHA-256

```text
219e143149ef9d1ef0820d438921abffa5eb343f0c1f4ea6b11d8cf91f122d5d  host.cap (5,776,633 bytes)
73f7fb48c9f8518e389e19cd00ebf14ee7577aac48cafc7808510d0b645e1942  jukuhost.log (8,875 bytes)
6f61b809f4b5ac1450215742bd0162fcb1900c66c3b358cfe2000c84fabf350c  tested jukupoly-doom-library.cpm
af0f44865952ca02cfae3b310b35a356d679a507566f41f8028e0f1680015bf9  corrected jukupoly-doom-library.cpm
```
