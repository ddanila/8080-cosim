# Network ROM C9 plan

Status: **CANDIDATE SCOPE ONLY — C9 IS NOT AUTHORIZED**.

C8 (`juku-network-rom-abi1.3-c8.bin`) is immutable and remains the qualified
network ROM. This subordinate plan records one measured defect and the policy
change already reserved for a successor, so that a future C9 has a written
scope before anyone builds or burns one. It does not authorize a build; the
`spinoffs/jukuravi/network-rom/README.md` rule still applies, and neither item
below is on its own sufficient reason to produce C9.

## Defect: the resident console client never mirrors output

The ABI 1.3 host-console operation at `FF5Ch` negotiates N4, accepts remote
keystrokes, and observes every character CP/M prints — but never transmits one.
A host that offers `--console-pty` therefore sees a silent console for the
whole session, including the `A>` prompt.

### Evidence

All figures below come from one instrumented C8 session: 35 s, host
`jukuhost 0.3.1-m6`, target paced at 1.7 MHz, booting to `A>` and serving
1,677 NetDisk requests.

- The C8 CP/M Plus adapter is `adapter-romabi-host-native`, which links
  `cpm3-rom-host.rel`; its `NCENA`/`NCSTAT`/`NCIN`/`NCOUT`/`NCCFG` entries are
  thunks that call `JCGHOSTADDR`. The console client is resident in ROM, and
  the RAM `netconsole.asm` transport is not part of this profile.
- Watching the documented mutable block `D7E0h..D7FAh` for a full session
  records 49,585 accesses. The pending-operation byte at `D7E6h` only ever
  holds `20h` (console poll) and `26h` (capability query). `21h`
  (console out) and `28h` (bounded console-out block) never appear.
- Every byte written to the adjacent argument byte at `D7E7h`, in order,
  reconstructs the console text exactly:
  `\r\nCP/M Plus 3.1 Juku\r\nN3 19200\r\n\nA>`. The ROM therefore receives every
  character the BIOS hands to its OUT entry, and turns none of them into a
  request. The failure is emission, not observation.
- The host capture agrees. Decoding every request the target sent yields
  `20h` x 1,653, `14h` x 23, `26h` x 1, and nothing else: console polls,
  read-aheads, the single capability query, and zero console-output frames.
- The host side is correct and is not the cause. It emits the `NRN4` ready
  marker and answers the capability query `03 03 6f 01`, whose bit 0 — the
  flag the target's own `NCCFG` contract tests — is set.

### Why a simulator workaround is not a fix

Both current harnesses read the console by having the simulator hook the
adapter's CONOUT vector (`JUKU_CONSOLE_OUT_PC`): `cpm-plus-juku`'s
`tests/cosim_check.py`, and `vc8080`'s `tools/run_vc.py`. That is a simulator
affordance with no physical equivalent. On CS00015 there is no hook, so remote
console output is genuinely unavailable — the operator must read the local
screen. Any future headless bring-up, soak, or unattended physical regression
that wants console text needs the ROM to mirror it.

### Proposed C9 change

When N4 is negotiated and the host capability bit is set, the resident console
client should issue `21h` for each character passed to its OUT entry, or batch
into the bounded `28h` block where the existing 32-byte limit applies. The
established contract is unchanged and must be preserved: the local screen and
key matrix stay authoritative, mirroring is best effort, and a missing or
broken host degrades to local-only after bounded backoff rather than stalling
CONOUT.

### Acceptance

- `8080-cosim`: `tests/jukuhost_c8_cosim_test.py` passes with no CONOUT hook
  configured — it already expects `A>` from `jukuhost --console-pty` and is the
  reason this defect was found.
- `cpm-plus-juku`: `make c8-check` continues to pass unchanged, proving the
  local console path did not regress.
- `vc8080`: `tools/run_vc.py` drops its `JUKU_CONSOLE_OUT_PC` hook and reads
  the console from `--console-pty` again. Its guard,
  `test_runner_keeps_the_production_host_console_negotiated`, records that the
  hook is a stopgap and should assert the hook's absence once this lands.
- Physical: one CS00015 cold boot whose console transcript is captured only
  through the host, with the local screen agreeing character for character.
- The measured `0100h..99FFh` transient span and the 27-byte `D7E0h..D7FAh`
  mutable budget must both survive the change.

### Open question — settle before scoping the work

It is not known whether output mirroring ever worked. Nothing in CI would have
caught its absence: `.github/workflows/ci.yml` runs only
`bash -n sync/jukuhost_m2_check.sh`, a syntax check, leaving that whole gate
local-only. Run `python3 tests/jukuhost_c8_cosim_test.py` on a native
Linux host before treating this as a regression: a pass there makes it a
host-platform difference to chase instead, and a failure confirms the feature
was specified and never completed.

## Reserved policy: unconditional network boot

Already recorded in `spinoffs/jukuravi/network-rom/README.md`. For C9 or later,
S21 bit 0 is reserved rather than assigned to boot policy, and network boot
becomes unconditional; the concealed `N` gate has no visible prompt, monitor,
or distinct destination and does not justify a permanent configuration bit. C8
keeps interpreting bit 0 as documented.

This is the natural companion for the defect above: the README already requires
that the policy change ride along with another measured ROM improvement rather
than justify a burn by itself.

## Non-goals

Cryptographic boot authentication and write-back caching remain explicit
non-goals until their 8080 cost and failure semantics justify them. This plan
adds no ABI vector and no new mutable state beyond what mirroring needs.
