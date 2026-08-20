# Juku host configuration

The production C host accepts either an explicit `JUKUHOST.INI` path or the
long Linux command line retained for development tests:

```sh
build/jukuhost JUKUHOST.INI
build/jukuhost --config JUKUHOST.INI
```

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

`network_rom=yes` requires a system and a JF16 Fastboot artifact. A fallback
is optional, but its system and Fastboot identities form one inseparable slot:
if either primary artifact is absent or fails its size/SHA-256 identity, both
fallback artifacts are selected. A legacy JF1–JF15 fallback still fails the
runtime's admitted-V16 check; fallback does not weaken the protocol boundary.

`boot_restarts` bounds complete bootstrap retransmissions after an explicit
target-reset indication; zero disables them. A V16 body is never resent merely
because its final acknowledgement was lost. The host retries only after the
reset ROM emits a fresh checked `JR16` readiness frame, so it cannot overwrite
a possibly running CP/M system.

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
