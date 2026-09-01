# CS00000 Imp M7 physical comparison (partial)

This records the interrupted 2026-09-01 physical run of the exact Imp M7 A/B
disk on Juku CS00000.  The tested native B: image had SHA-256
`7fa29b3edee6c910f7d1da3a0da24d85001c89065389136125f3ae019b302dfa`.
The operator powered the machine off after the second candidate exposed a
target-only failure, so this is deliberately a partial result, not physical
qualification of M7.

## Boot and host finding

A reset which arrived after the initial three-second V16-ready window was
recovered correctly.  The byte capture contains the valid five-byte checked
ready frame `4A 52 10 01 09`, followed by the distinct raw stream-header ACK
`C6`; the host sent the system and CP/M Plus booted.  The apparent bootstrap
failure was instead the host's later attempt to open a nonexistent
`--console-pty` path.  It exited with only `phase=failed`/`exit=4`, orphaning
the otherwise valid CP/M boot and leaving CP/M to report an A: I/O error.

After a `socat` PTY pair was created, `--resume-disk` attached to CP/M's next
retry without RESET.  The recovered session served 7,666 requests and 34
reads (272 records) with zero writes, retries, boot restarts, target resets,
reconnects, or UART errors.  This proves the ROM/host late-ready recovery path
worked in this run; it does not support the earlier hypothesis that the
ready-frame checksum was mistaken for `C6`.

The host now preflights an explicitly requested console PTY before opening the
serial port or starting bootstrap, reports its path and OS error, and retains
the same diagnostic on the later runtime open.  A Linux PTY regression pins
the pre-bootstrap failure.  A future orchestration layer should create and
prove both PTY endpoints before launching `jukuhost`; host and ROM retry state
should continue to be tested with delayed ready, reset during stream, host
replacement, and an absent console as separate faults.

## Listening result

| Program | Result |
|---|---|
| `IMPV1.COM` | Ran twice and returned to `A>`.  The attended run confirmed that the opening low lead is missing and first appears later; the early ticking/percussive voice sounds correct. |
| `IMPREAR.COM` | Loaded and began on the physical target, then failed to return.  The screen showed garbage and neither the expected end nor a remotely queued Escape restored CP/M.  The host was stopped more than three minutes into the recovered session. |
| `IMPDET.COM` | Not run after the `IMPREAR` failure. |

The exact `IMPREAR.COM` still passes the instruction-level 8080 standalone
test offline: 1,500 frames, 29.863 seconds, PIT silence, restored stack, and
restored interrupt state.  Therefore no score/player change is justified yet.
The next hardware gate must start from a cold clean boot and run `IMPREAR`
alone before attempting any sequence test.  If it passes alone, repeat
`IMPV1` then `IMPREAR` while capturing the first divergent program counter or
memory write.  If it fails alone, the target-vs-emulator boundary is already
isolated.  Keep Imp v1 in the library and do not run `IMPDET` until this is
resolved.

The comparison disk README claims Escape support, but these three standalone
COM builds do not enable the library player's keyboard-polling build option.
The queued remote Escape consequently provides no standalone-player evidence;
this packaging/documentation mismatch must be corrected before the retest.

## Retained local evidence

The raw captures and native logs remain untracked under
`out/jukupoly-imp-m7-physical-20260901-01/`:

```text
310d4796b8f466de63892274fe82c6bd2f94e9f768617302e3987a3e7e9fdce4  jukuhost.log (891 bytes)
9b6cf403945dbb13df61fa3dbb6cc154588450f9d858750841e55a920b3ce24d  host.cap (63,090 bytes)
533dab1916b0559473535d642700577127374364c7e39ac3cfc8c7ba03b9681f  jukuhost-resume.log (2,977 bytes)
ba31e75ea2245445b6692d63d6a89f54701971209a46381b22729a3ed0d58b85  host-resume.cap (2,278,282 bytes)
da0a6c77c5b9ca9f059fcc6c17475098448296dbed9610b554d3b0b697473da3  jukuhost-clean.log (877 bytes)
7090c7f05d56a6bbce4d01caac48231dd9fab302217e0f17ed1ab2642616ea4a  host-clean.cap (63,708 bytes)
```

`jukuhost.log`/`host.cap` capture the valid recovered boot followed by the
missing-console failure.  `jukuhost-resume.log`/`host-resume.cap` capture the
recovered CP/M service, both v1 loads, and the `IMPREAR` load/failure.
`jukuhost-clean.log`/`host-clean.cap` are the final no-target run stopped after
the operator powered CS00000 off.

