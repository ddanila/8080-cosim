# CS00000 JukuPoly “Suspense” physical session

These files retain the successful 2026-08-30 physical run of the one-minute
JukuPoly arrangement of Robert Prince's “Suspense” from DOOM E1M5.  The exact
4,047-byte `SUSPENSE.COM` image played through the unmodified internal speaker
of Juku CS00000 and returned cleanly to CP/M Plus 3.1.

## Qualification

| Evidence | Result |
|---|---|
| Delivery | Reattached to the resident C10 JukuNet/NetDisk session; `WBOOT` relogged private drive A: before `SUSPENSE` |
| Console | Returned to a fresh `A>` prompt 64.541 seconds after the command |
| Listening | Operator accepted playback through the unmodified internal speaker |
| Host log | 19 successful reads; zero writes, retries, boot restarts or target resets |
| Score | 3,000 nominal 20 ms frames; cycle simulation covered a nine-second window |

The prompt interval includes file lookup, loading and CCP reload; it is not
an audio-duration measurement. Complete playback evidence comes from the
physical run. No electrical waveform or acoustic recording was taken.
The served volume was private; the source CP/M image was not modified.

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
