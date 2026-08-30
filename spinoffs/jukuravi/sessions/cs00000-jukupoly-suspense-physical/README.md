# CS00000 JukuPoly “Suspense” physical session

These files retain the successful 2026-08-30 physical run of the one-minute
JukuPoly arrangement of Robert Prince's “Suspense” from DOOM E1M5.  The exact
4,047-byte `SUSPENSE.COM` image played through the unmodified internal speaker
of Juku CS00000 and returned cleanly to CP/M Plus 3.1.

`jukuhost` reattached to the powered, resident C10 JukuNet/NetDisk session; no
hardware reset or cold boot was used.  Sending a carriage return caused CP/M
to emit a fresh prompt, after which `WBOOT` relogged the substituted private
drive A: and `SUSPENSE` ran.  The console transcript normalizes to:

```text
A>WBOOT
A>SUSPENSE
A>
```

The new prompt arrived 64.541 seconds after the program command.  That is a
host command-to-prompt interval, including CP/M directory lookup, COM loading,
and CCP reload; it is not presented as an audio-duration measurement.  The
score contains 3,000 nominal 20 ms frames.  In accordance with the operator's
request, only a bounded nine-second cycle window—not the full minute—was run
in the simulator.

The operator reported that it “sounds good” and described the progress as
“amazing.”  This qualifies physical playback and clean return for the
one-minute arrangement.  No electrical waveform or acoustic recording was
taken.

The host log records 19 successful reads, zero writes, zero retries, zero boot
restarts, and zero target resets.  The served disk was a private volume, so no
source CP/M image was modified.

| File | Contents |
|---|---|
| `suspense.com` | exact CP/M transient served in the run |
| `command.txt` | exact successful `jukuhost` invocation |
| `jukuhost.log` | native timestamped host log |
| `host.cap` | raw bidirectional host wire capture |
| `console.bin` | N4 console transcript |
| `result.txt` | observed command-to-prompt result |

## SHA-256

```text
21b259a149d01946cc7b0b054434de12b807b827260335b624f4926668f74382  command.txt
203321e7c573de5ac207cafb587201f5f9e272e5c61f53c5548822a41aebf1d9  console.bin
689314aa12c27eba172a1d8a5da01ee6f4f55b3cd784efcdc60f693faaa244fc  host.cap
d4447212dfc9da7779551c54774df9892dba1eeaadb6f14a67a56e3aac16f09a  jukuhost.log
52d5eb312a721a9c409ee8908018a3ef96b91c9c4ac2152c178295989b40b6e5  result.txt
cd7692867e692b392ca54f3f5423c6c62438307c8336d907edbadd73b7fd8ff7  suspense.com
```
