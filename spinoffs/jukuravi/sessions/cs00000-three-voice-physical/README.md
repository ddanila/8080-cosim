# CS00000 three-voice physical session

These files retain the two JukuPoly runs performed on 2026-08-29 against
physical Juku board CS00000.  The board had the C10 JukuNet ABI 1.4 ROM fitted
and booted CP/M Plus 3.1 through Fastboot V16 and NetDisk v3 at 19200 baud.

The first run cold-booted a private copy of the C10 full volume containing the
161-byte quiet `TRIVOICE.COM`.  The second run reattached to the live N4
session and served a fresh private volume containing the 163-byte loud image.
Neither source CP/M volume was modified.

| Prefix | Contents |
|---|---|
| `quiet-` | initial 4–28 microsecond pulse experiment |
| `loud-` | final 100–124 microsecond pulse experiment |
| `three-voice-*.com` | exact CP/M transient served in that run |

Each run retains the exact `jukuhost` command, its native log, binary wire
capture, and N4 console transcript.  The quiet transcript includes the cold
boot banner; the loud transcript begins with the reattachment probe.  Both end
in `A>TRIVOICE` followed by a new `A>` prompt.

The observed host command-to-prompt intervals were 11.949 seconds for the cold
quiet run and 13.677 seconds for the reattached loud run.  These include CP/M
file lookup/load and CCP reload.  The cycle model measured the corresponding
music loops as 9.052 and 9.075 seconds.

Operator observations:

- quiet: three stages were audible and “very interesting and not that bad”,
  but at very low volume;
- loud: all stages were audible, with the result assessed as “Fantastic”.

Evidence scope is intentionally precise: the console and host files prove
delivery and clean return, while the listening observations prove physical
speaker output.  No electrical waveform or sound-pressure measurement was
taken.

## SHA-256

```text
427f1fe876ebda844a56aa93de47dd0367f070b3a358e372bc179339b5b1f37f  loud-command.txt
bdc02b4fae9d83a37990b9a40e41876dc547f846979aaf95cbd28f3e45df91d2  loud-console.bin
a960adbcb7063d75d62d2a069b4585d95727aad7d85a181178d456a440f6d296  loud-host.cap
08f7a33f9f2d27b84c3bdfd91dbea3b94b406c77f57c0e57766f9500fc  loud-jukuhost.log
273d3f7258975e4e809506c6acf4492a76d36cc9e1c1026c41052b6b04793429  quiet-command.txt
5376ef9fc5445ab26ebd02cc772f585ec81340f24473d59a85ab986150018918  quiet-console.bin
4311e480e502ea265a9251db5bad770ef6e330212ef37b6eca2bb3a54e1d37c1  quiet-host.cap
7b5b07146f820ba68e2c1ed162c5a832a034d02b1fe32436cd4b3c425dc353b2  quiet-jukuhost.log
1381c24e956f61b410d95d9423e9ca934344c3d0fe819092bed191264a31e838  three-voice-loud.com
6e1feff2267faceff75f1e27aef5f2865266f0245d75c509a0b0cbd29d8e19cc  three-voice-quiet.com
```
