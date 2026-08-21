# Juku host configuration

The production C host accepts either an explicit `JUKUHOST.INI` path or the
long Linux command line retained for development tests:

```sh
build/jukuhost JUKUHOST.INI
build/jukuhost --config JUKUHOST.INI
```

The DOS build uses `JUKUHOST.INI` automatically when invoked without options.
The generated Pocket8086 folder therefore starts with either `JUKUHOST` or
`JUKU.BAT`; no command-line parameters are required. Its production defaults
are COM1, 19,200-baud NetDisk v3, `CON` for the local N4 console, a writable
A: snapshot, read-only native B:, and DOS-safe log/capture names.

Relative file names are resolved beside the configuration file. The format is
ASCII, line-oriented, and deliberately strict: section and key names are
case-insensitive, but duplicate keys, unknown sections or keys, malformed
numbers and hashes, incomplete artifact identities, and lines of 512 bytes or
more are rejected.

```ini
[host]
port=/dev/ttyS0
log=JUKUHOST.LOG
capture=JUKUHOST.CAP
console=/dev/pts/7
network_rom=yes
timeout=120
disk_timeout=0
boot_restarts=3
reconnect_timeout=30

[network]
protocol=3
baud=19200
read_ahead=3
reply_guard_ms=2

[system]
file=SYSTEM.BIN
size=18432
sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

[fastboot]
file=FAST16.BIN
size=7806
sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

[fallback_system]
file=SYSTEM2.BIN
size=18432
sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

[fallback_fastboot]
file=FAST162.BIN
size=7807
sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

[disk_a]
base=BASE.IMG
file=WORK.IMG
size=409600
sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
geometry=juku-cpm3
mode=snapshot

[disk_b]
file=APPS.JUK
size=819200
sha256=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
geometry=juku-native
mode=read-only
```

The hashes above are placeholders; a generated deployment file must contain
the hashes from its canonical build manifest.

Boot selection is explicit:

- no `[fastboot]` section selects a complete stock Janet bootstrap at
  9,600/8O1;
- `[fastboot]` with `network_rom=no` (the default) selects stock-assisted JF15:
  one 128-byte core through Janet at 9,600/8O1, then its checked extension and
  compressed system at 19,200/8N1;
- `[fastboot]` with `network_rom=yes` selects direct JF16 from the JukuNet C8
  ROM at 19,200/8N1.

`network_rom=yes` therefore requires a system and a JF16 Fastboot artifact;
stock-assisted mode requires an exact JF15 artifact. A fallback is optional,
but its system and Fastboot identities form one inseparable slot: if either
primary artifact is absent or fails its size/SHA-256 identity, both fallback
artifacts are selected. A JF1–JF14 fallback still fails validation; fallback
does not weaken the protocol boundary or switch direct/stock mode.

`boot_restarts` bounds complete bootstrap retransmissions after an explicit
target-reset indication; zero disables them. A V16 body is never resent merely
because its final acknowledgement was lost. The host retries only after the
reset ROM emits a fresh checked `JR16` readiness frame, so it cannot overwrite
a possibly running CP/M system.

Stock Janet begins with no added line-turn delay. If a particular client
resumes polling or rejects a just-sent frame, the host resends that exact
checked frame and raises only the current session's destination-zero guard
through 2, 5, and at most 10 ms. Fast clients therefore retain the zero-guard
path. After a JF15 core is executed, its overlap-safe `A5 3A` probe continues
until the configured `timeout`; a fixed short probe count is deliberately not
used because physical boards can take several seconds to complete the stock
execute handoff.

`reconnect_timeout` bounds named serial-device reopen attempts in seconds;
zero disables reopen. After a disk-session link loss, the host closes the stale
handle, retries the same configured path every 250 ms, restores 19,200 8O1,
discards any partial request, and advertises the normal NetDisk ready marker.
The service and its duplicate-reply cache remain live, so a retried write is
not applied twice. The integration-only inherited-descriptor mode cannot
reopen a descriptor and therefore fails cleanly instead.

Drive A supports three explicit policies:

- `mode=read-only` authenticates and serves `file` without writes;
- `mode=direct` authenticates and writes `file` through the crash journal;
- `mode=snapshot` authenticates immutable `base`, creates `file` as its working
  copy when absent, and thereafter resumes that correctly sized working copy.

Snapshot mode is the normal writable deployment policy because the admitted
base is never modified. `sha256` identifies the base in snapshot mode and the
served file in the other modes. Drive B is always `mode=read-only` with
`geometry=juku-native`.

`build/jukuhost --selftest` checks the portable checksum primitives without a
serial device. It is also the future headless Win32/Wine startup check.

When configured, the text log and binary capture are required evidence rather
than best-effort decoration. Failure to open, write, or flush either stream
stops the session with exit code 7. The capture contains CRC-protected RX, TX,
and local-event records; event flags 1, 2, and 3 denote INFO, WARN, and ERROR.
Startup settings, phase transitions, warnings/errors, media writes, and the
final summary are explicitly flushed. High-volume INFO request events remain
buffered so verbose evidence cannot perturb serial timing unnecessarily.

For the DOSBox-X integration test only, a console path of the form
`@12000:INPUT.TXT` delays scripted input by 12,000 ms. This is a deterministic
headless-harness facility, not a recommended deployment setting; Pocket8086
packages always use `console=CON`.
