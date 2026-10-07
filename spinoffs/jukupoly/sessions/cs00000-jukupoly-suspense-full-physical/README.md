# CS00000 JukuPoly full “Suspense” physical session

These files retain the successful 2026-08-30 physical run of the complete
2:44 JukuPoly reduction of Robert Prince's “Suspense” from DOOM E1M5.  The
exact 10,701-byte `SUSPFULL.COM` image played through the unmodified internal
speaker of Juku CS00000 and returned cleanly to CP/M Plus 3.1.

## Qualification

| Evidence | Result |
|---|---|
| Delivery | Cold C10 JukuNet boot from private drive A:, Fastboot V16 and NetDisk v3 at 19,200 baud |
| Boot limitation | Host did not observe Fastboot ready/final markers; resident-stream fallback reached NetDisk and the captured CP/M banner/prompt |
| Console | `SUSPFULL` returned to a fresh `A>` prompt 170.108 seconds after the command |
| Listening | Operator accepted the complete arrangement; playback remained stable through the reduced layer transitions |
| Host log | 24 successful reads; zero writes, retries, boot restarts or target resets |
| Score | 8,200 nominal 20 ms frames; cycle simulation covered a nine-second window |

The prompt interval includes file lookup, loading and CCP reload; it is not
an audio-duration measurement. Complete playback evidence comes from the
physical run. PIT silence writes and stack restoration are implementation
properties; the console capture establishes return to CP/M. No electrical
waveform or acoustic recording was taken. The served volume was private;
the source CP/M image was not modified.

| File | Contents |
|---|---|
| `suspfull.com` | exact CP/M transient served in the run |
| `command.txt` | exact successful `jukuhost` invocation |
| `jukuhost.log` | native timestamped host log |
| `host.cap` | raw bidirectional host wire capture |
| `console.bin` | N4 console transcript |
| `result.txt` | observed command-to-prompt result |

## SHA-256

```text
557512c21597f5e2b80eac5caa4688ec7b28648da9bab02371b44440dc44dfd7  command.txt
ff73a5d1183b284889a47f50b02c516dd154636b77d5d753c4ffa8d2adbd1de9  console.bin
ea53d061e77e2d56348a6d4bd47b420b250c6eb08ed60694ce6511f92b946c27  host.cap
e7ee101fb378f5c5de8242ce88518122cb61350a3af21fce6bb6178dd25f5511  jukuhost.log
f07cbb4ab9635bacd37bcc47d65bda09f67778cd0668f79d820fd01ac722dc19  result.txt
1b11b7639cb54fa48185f4cd1cebcc8153bcef867c5e11ed4115f952d0ae4cd5  suspfull.com
```
