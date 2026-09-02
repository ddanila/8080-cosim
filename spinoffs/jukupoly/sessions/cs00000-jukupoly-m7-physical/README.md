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

The comparison disk used in this historical run claimed Escape support, but
its three standalone COM builds did not contain the library player's keyboard
poll.  The queued remote Escape consequently provides no standalone-player
evidence.  That medium was superseded by a standalone `-P8=1` build which
asserted both emitted poll sites and cycle-tested all normal and injected-
Escape returns.  The first such disk was SHA-256
`55c99c0ba265dc06d9e45a6d721a79032959c0daa92527775982900d12c1b1ee`.

## 2026-09-02 cold retest and root cause

CS00000 cold-booted C10/CP/M Plus with the four-way target-shape disk SHA-256
`20dd4ec7aea589df1fbf94a5c503705a7724fbdf7b51e2f57670aa9c805ac4ef`.
`B:REAROLD.COM` SHA-256
`4a843f92b7cc490f04b601a1ada36e3cd76f8b6f2bdf2d1ecb0548ad4d9b3a50`
again failed to return: the screen became striped and the machine stopped
servicing CP/M.  The host had loaded the complete COM with zero disk retries
or UART errors and saw no request after the final load at 66.443 seconds.
It was stopped 116 seconds later.  This reproduced the prior failure from a
clean boot and made the comparison result invalid; it was not an envelope-
quality verdict.

The same old COM then reproduced the failure under the complete C10 ROM,
CP/M, bank map, N4, and NetDisk cosim.  Its post-failure checkpoint wandered
at `PC=00AAh`, `SP=FFFEh` with interrupts disabled, after repeatedly crossing
the transient and PIT code.  This ruled out a CS00000 hardware fault and
exposed the lightweight audio harness's false assumption.

The standalone JPS-v2 startup set `SP=0000h` for tone channel 3 and only then
executed `CALL envelope_dispatch_init`.  The call therefore tried to push its
return address at `FFFEh`.  Flat-RAM tests accepted that write; real Juku mode
1 and the full-system cosim map the write-protected high BIOS ROM at
`D800h..FFFFh`, so `RET` consumed ROM bytes and entered garbage.  Library JPS
playback was unaffected because its dispatcher is initialized before
`player_start`.

The dispatcher call now runs while the caller's real stack is still active,
before `SP` is lent to tone 3.  The hot loop, per-frame work, and score bytes
are unchanged.  The focused envelope execution regression now models the
write-protected high-ROM overlay, so the old ordering fails instead of being
masked by flat RAM.  The repaired `REAROLD` completed under the same full C10
system, caused the expected A: warm-boot/CCP reads, and accepted a subsequent
B: `DIR`; the host recorded 22 reads, zero retries, zero boot restarts, and
zero UART errors.

The repaired-startup three-way disk was SHA-256
`3e79d3cf2bbab4a9855f830a88f87ff44fd3660cddd753a02d5bdf6caf2005b8`.
The repaired-startup OLD/NEW target-shape disk was SHA-256
`aea4ec6549a3b7f4b383c8efa95fce953b375eb854aa1b06a7a93520098e56d2`.
Physical listening of the latter remains pending; no broken standalone image
should be used for that gate.

The later host-side equal-phase member grouping correction changes the music
payloads without changing this startup fix. Its current three-way disk is
SHA-256
`00c7c66b20a1d567271f93e66b16f239d4d9f58ccb2bad3972c6e6e702c87870`;
its current OLD/NEW disk is SHA-256
`f092375387b9047ab0739e3a6fa8d62b82bc495e8f24a595af29704e8253affd`.
These newest images have not yet been run on CS00000.

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

The 2026-09-02 physical log and wire capture remain untracked under
`out/jukupoly-targetshape-physical-20260902-01/`:

```text
4d25dea2e0ae90eb9cbec9e9ea6c0ac7678e96b6d5e9cfaedb83fc8166d4c3b5  jukuhost.log
977927aa428e05b37837e0b9fc867ab6cc358149c4b699817adba69b5ab9f1d2  host.cap
```

The paired broken/fixed full-system checkpoints and host evidence remain
untracked under `out/jukupoly-targetshape-diagnosis-20260902/`.
