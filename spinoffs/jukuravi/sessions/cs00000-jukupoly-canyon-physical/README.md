# CS00000 JukuPoly Canyon physical session

These files retain the 2026-08-30 physical listening run of the JukuPoly
compiled-pattern player on Juku board CS00000.  The 4,327-byte `JUKUPOLY.COM`
played the credited seven-second reduction of George Stone's “Trip Through the
Grand Canyon” through the unmodified internal speaker, then returned cleanly
to CP/M Plus 3.1.

The board remained powered after the preceding experiment.  `jukuhost` used
`--resume-disk` to reattach to the resident C10 JukuNet/NetDisk session; no
hardware reset or cold boot was needed.  The operator sent `WBOOT` once to
relog drive A: after substituting the private volume, then ran `JUKUPOLY`.
The console transcript is exactly:

```text
A>WBOOT
A>JUKUPOLY
A>
```

The fresh prompt arrived 13.152 seconds after the program command.  That host
interval includes CP/M directory lookup, COM loading, and CCP reload; the
cycle-qualified music interval is 7.440 seconds and is not inferred from the
host timing.  The host log records 20 successful reads, zero writes, zero
retries, zero boot restarts, and zero target resets.

The operator's listening assessment was “not bad; player ok.”  This qualifies
physical playback and clean return of the compiled-pattern engine.  The
cycle regression remains the evidence that all three tone accumulators and
percussion were concurrent; no multitrack electrical or acoustic capture was
taken during this session.

| File | Contents |
|---|---|
| `jukupoly.com` | exact CP/M transient served in the run |
| `command.txt` | exact `jukuhost` invocation |
| `jukuhost.log` | native timestamped host log |
| `host.cap` | raw bidirectional host wire capture |
| `console.bin` | N4 console transcript containing `WBOOT`, command, and return |

The served disk was a private volume, so the source CP/M volume was not
modified.  It is not retained because the exact player and all source/build
inputs are already versioned separately.

## SHA-256

```text
09003967dadfa0d11559ac6e224d650a48f1dba26834cc8eae107dab894505ec  command.txt
895b8a1c9840919b603b115015805e20b7d304429fa1d4ce5650e99b306865fe  console.bin
bc94630d4f474555845fa95843a68ee7b3a0ddedd4c4db7eec7651f10963db69  host.cap
fccf30cd930baac0f4236ec5cc3df3b44ab66f11aa1c5721c27d8ad89f06d804  jukuhost.log
6d752b19d15e6921c77643145ae2a9bc3801b11645c5c78f8d4b9cab25095800  jukupoly.com
```
