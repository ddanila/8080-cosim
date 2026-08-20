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
