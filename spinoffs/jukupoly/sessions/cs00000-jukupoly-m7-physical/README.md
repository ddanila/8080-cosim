# CS00000 Imp M7 physical comparison (partial)

This records the interrupted 2026-09-01 physical run of the exact Imp M7 A/B
disk on Juku CS00000.  The tested native B: image had SHA-256
`7fa29b3edee6c910f7d1da3a0da24d85001c89065389136125f3ae019b302dfa`.
The operator powered the machine off after the second candidate exposed a
target-only failure, so this is deliberately a partial result, not physical
qualification of M7.

## Delivery context

The initial host exited when its configured console PTY did not exist, after
successfully recovering a late ready frame and booting CP/M. Creating the PTY
and attaching with `--resume-disk` recovered disk service without RESET.
The recovered session recorded no disk retries, boot restarts, target resets,
reconnects or UART errors. The captures below distinguish this setup failure
from the later player startup failure.

## Listening result

| Program | Result |
|---|---|
| `IMPV1.COM` | Ran twice and returned to `A>`.  The attended run confirmed that the opening low lead is missing and first appears later; the early ticking/percussive voice sounds correct. |
| `IMPREAR.COM` | Loaded and began on the physical target, then failed to return.  The screen showed garbage and neither the expected end nor a remotely queued Escape restored CP/M.  The run was stopped after this failure. |
| `IMPDET.COM` | Not run after the `IMPREAR` failure. |

The failed `IMPREAR.COM` passed the lightweight flat-RAM audio harness, but
that harness did not model the write-protected high-ROM overlay. The complete
system diagnosis below supersedes that result as evidence of correct startup.

The historical comparison disk also claimed Escape support without including
the standalone keyboard poll. The queued remote Escape therefore supplies no
standalone-player evidence. Current comparison builds use `-P8=1` and check
both emitted poll sites and normal/injected-Escape returns.

## Cold retest and startup fault

CS00000 cold-booted C10/CP/M Plus with the four-way target-shape disk SHA-256
`20dd4ec7aea589df1fbf94a5c503705a7724fbdf7b51e2f57670aa9c805ac4ef`.
`B:REAROLD.COM` SHA-256
`4a843f92b7cc490f04b601a1ada36e3cd76f8b6f2bdf2d1ecb0548ad4d9b3a50`
again failed to return: the screen became striped and the machine stopped
servicing CP/M.  The host had loaded the complete COM with zero disk retries
or UART errors and saw no request after the final load.  This reproduced the prior failure from a
clean boot and made the comparison result invalid; it was not an envelope-
quality verdict.

The old COM also reproduced the failure in full-system C10/CP/M cosim,
which models the high-ROM overlay absent from the lightweight audio harness.

The standalone JPS-v2 startup set `SP=0000h` for tone channel 3 and only then
executed `CALL envelope_dispatch_init`.  The call therefore tried to push its
return address at `FFFEh`.  Flat-RAM tests accepted that write; real Juku mode
1 and the full-system cosim map the write-protected high BIOS ROM at
`D800h..FFFFh`, so `RET` consumed ROM bytes and entered garbage.  Library JPS
playback was unaffected because its dispatcher is initialized before
`player_start`.

The dispatcher call now runs while the caller's real stack is still active,
before `SP` is lent to tone 3. The focused envelope execution regression models the
write-protected high-ROM overlay, so the old ordering fails instead of being
masked by flat RAM.  The repaired `REAROLD` completed under the same full C10
system, caused the expected A: warm-boot/CCP reads, and accepted a subsequent
B: `DIR`; the host recorded zero retries, boot restarts or UART errors.

## Current retest boundary

Later equal-phase member grouping changed the music payloads without changing
the startup fix. Current disk identities, build settings and cycle/Escape
checks are in the [three-way comparison report](../../OPL-IMP-M7-PHYSICAL-AB.json)
and [OLD/NEW report](../../OPL-IMP-TARGET-SHAPE-PHYSICAL-AB.json).
Neither corrected disk has been run on CS00000. Physical A/B remains pending;
keep Imp v1 as the delivered library selection until corrected candidates
have listening evidence.

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
