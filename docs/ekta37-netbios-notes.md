# ekta37 NetBios/Janet boot-path notes

Status: hand-written analysis of the pinned `roms/ekta37.bin` (EktaSoft '88
Serial #0037, RomBios 3.43m). The canonical image identity is in
[the programming-image report](eprom-programming-images.md).
The commands at the end inspect selected banners and USART code and run
the archived-system bootstrap regression. Physical and cross-project claims
use the evidence cited in their sections; interpretations are labeled.
Sibling identity/context is in
[`ektasoft-rombios-lineage.md`](ektasoft-rombios-lineage.md).

## What NetBios is

The 3.4x RomBios line's second BIOS is the school-network boot path. There
is no additional network interface required for the tested onboard path:
NetBios drives the machine's 8251 USART (D11, ports `08h/09h`), whose clock is D57 counter 0 and whose line
is the X3 serial connector — the same path the Jukuravi diagnostic link
uses (see [`serial-handoff.md`](serial-handoff.md) and
[`cs00024-t36-diagnosis.md`](cs00024-t36-diagnosis.md)).

## Byte-verified observations (ROM offsets)

- `19A9h`: boot prompt `System from <D>isk, <N>et ?`.
- `2C22h`: `1Bh 'L'` then `Janet 1.2$` — the NetBios banner, printed with a
  leading `ESC L` control sequence (sequence meaning uninterpreted here).
  `Load $ >$Wait $` prompts follow at `2C2Fh` (CP/M `$`-terminated).
- `23C4h`: `1Bh 'L'` then `BOOTSTRAP v4.1 - 1793 on Main board$` — this
  3.43m image carries the same Bootstrap 4.1 generation that MAME's driver
  notes for the 2.43m homebrew image, and that `EKDOS30.ASM` declares
  compatibility with ("Bootstrap Vers 4.X").
- `34D6h..3505h`: the NetBios USART initialization:
  - `LDA D5B2h / OUT 18h` — the D57 counter-0 count (the USART clock
    divisor) is written **from a RAM variable**: the network baud is
    software-configured, not an immediate operand. The configured physical
    `TN` path and the zero-configuration `TN0201` fallback both write `08h`
    in the proven setup. D57 pin 9 is on the drawing's `1,23M` rail, generated
    by the source-closed 16 MHz /13 divider. With the 8251's x16 mode this is
    nominally **9600 baud** (`16 MHz / 13 / 8 / 16 = 9615.4`). A divisor of
    four, not the observed eight, would be required for 19200;
  - the canonical 8251 recovery sequence (three `00h` writes then `40h`
    internal reset) to control port `09h`;
  - mode `5Eh` = x16 clock, 8 data bits, **odd parity enabled**, 1 stop —
    unlike the parity-less console/diagnostic use of the same USART;
  - command `35h` = TxEN + RxE + error-reset + RTS, with the command byte
    shadowed at RAM `D5A7h`; then `IN 08h` flushes the receiver.
- `352Bh..353Fh`: a wrapper that clears 8251 command bit 0 (TxEN) via the
  `D5A7h` shadow, performs monitor call `FF7Ah` with `A=3, C=00h` (its
  companion at `3523h` uses `C=FFh`), then sets TxEN again.
- `3544h..3552h`: receive helper — `IN 08h` stores the byte, `IN 09h`
  status is masked with `38h` (framing/overrun/parity errors), and the
  shadowed command byte is rewritten.
- `3507h..351Fh`: three monitor calls `FF89h` pairing small indices with
  code addresses: `(9, F318h)`, `(3, EF50h)`, `(2, F55Dh)`.
- `34B7h..34D5h`: a two-command configuration parser: `'S'` stores two
  fetched bytes (`D5A8h`/`D5E0h`, `D5ABh`); `'J'` stores one (`D4E9h`).

The `34xxh` ROM region executes at `F4xxh` (the code's absolute references
target `EFxxh..FFxxh`) through memory-mode banking: modes 1/2 hardware-map
ROM `1800h-3FFFh` at `D800h-FFFFh` for reads. The offsets above are ROM
file positions, not runtime addresses.

## Interpretation (labeled)

- The TxEN gating around transmissions plus RTS use and per-frame odd
  parity read as **shared half-duplex line discipline**: multiple stations
  on one line, only the active talker driving it, every frame
  error-checked. This fits the documented school deployment — one
  teacher station with floppy drives and printer serving diskless student
  machines. The boot subset is capture-derived below; unrelated Janet
  services and the monitor call `FF7Ah`'s general contract remain untraced.
- The `FF89h` calls install interrupt/service handlers. Functional cosim
  proves D11 `RxRDY -> D10 IR2` and `TxRDY -> D10 IR3`: without those two PIC
  requests the stock code never drains its transmit descriptor or consumes a
  received frame.
- The configurable `D5B2h` divisor still permits other software-selected
  rates, but the tested stock network path is 9600 baud, 8O1.

## Captured Janet protocol and native boot proof

On 2026-08-12 two independent `ekta37` cosim machines were connected through
their PTYs. One booted `JUKPROG2.CPM`, ran the archived `NETD.COM`, and answered
as station 02 with its `P=00` onboard-D11 transport. The other entered stock
NetBios as station 01. It reached the visible `N-EKDOS 1.0` banner after
receiving 10,252 serial bytes. This is a native server/client boot, not a RAM
injection or replay.

The byte capture establishes the host implementation's boundaries:

- a configured physical client needs only `TN`, with no Enter. Its keyboard
  S21 switch bank supplies the interface, maximum-station range, and own
  station number. Only a zero configuration invokes the `N=`/`S=` fallback;
  `TN0201` supplies maximum station `02` and own station `01` there, and is
  used by the simulator because its configuration switches are open;
- wire-format frames in the PTY capture start `E4 E4`, carry destination/source/control, and finish
  with an XOR byte that makes the complete-frame XOR zero;
- `0Ch` is the directed poll, `08h` is positive acknowledgement, `09h` is
  reject/retry, and destination-zero/control-zero frames hand the line over;
- the client sends the eight-byte `03 04 ...` bootstrap request; server
  service types are start `05h`, memory record `02h`, end `06h`, and execute
  `0Fh`;
- a 128-byte memory record uses `02h`, `04h`, and `09h` first/middle/last
  fragment markers. The `09h` payload marker is distinct from control `09h`.

The frozen `tests/fixtures/legacy_janet_netboot.py` implements those captured
turns for PTY regression, including retries; it does not write simulator RAM.
The five public `JUKUSYS.ZIP` images are
SYSGEN/system-track artifacts rather than 0100h executables: four `E5`-filled
sectors precede 52 system sectors. The host wraps those sectors in a one-record
8080 staging program. NetBios loads 6,784 bytes at `0100h`; the stub copies the
exact 6,656 bytes to the source-defined `CCP=B400h` and jumps to cold
`BIOS=CA00h`.

The host also recognizes the separate experimental `JUKU51` format without
changing the ROM protocol. It sends a 7,808-byte staging executable: the same
one-record copier followed by 7,680 resident bytes. That copier targets
`B000h` and enters `C600h`, supporting CP/Mish's 51K RAM-console layout while
leaving ordinary 52K `JUKUSYS` recognition byte-for-byte compatible.

The simulator's S21 compatibility profile supplies active-low switch state
on PB5 while keyboard columns 8–15 are selected. An open switch reads high;
ordinary idle columns read `CFh`. This depends on the selected column, not
the caller's PC, so RAM-resident systems can read the same switch profile.
The ROM's `1209h..123Bh` scan uses that behavior for onboard-D11 selection.

This PB5 behavior is specific to the archived `ekta37.bin` ROM. At offsets
`1211h..1216h` in `roms/ekta37.bin`, the bytes `DB 05 2F FB E6 20` read PPI
port B, complement it, and mask bit 5. The exact `.009 Э3` sheet-1 detail
instead connects D26 PB4/pin22 to E8.3, PB5/pin23 to E8.2, and `CONTRDAT`
to E8.4. The `.009 СБ` assembly drawing and owner board photo both show E8
bridged 3–4. Thus the ROM's PB5 S21 read and the surviving `.009` board's
PB4 selector are revision-incompatible as drawn. The simulator retains the
PB5 behavior for its `ekta37.bin` reference runs; the original board's
firmware/configuration behavior needs a matching ROM readback or a powered
PB4/PB5 observation before claiming the S21 path works on this revision.
The four other archived #0024/#0031/#0032/#0035 images use the same PB5
mask; #0043 has a different read sequence and no evidence for a PB4 S21
scan; see [the lineage audit](ektasoft-rombios-lineage.md).

The regression boots the five vendored system images plus an optional external
system, with up to five concurrent clients by default (`JUKU_NETBOOT_JOBS`
controls concurrency). It then repeats the first image with `TN0907` to check
automatic station discovery. Each client stops before the first `CA00h`
instruction. Every destination byte must match its source image:

| Image | 0100h staging | B400h system | handoff |
| --- | ---: | ---: | ---: |
| `CPM22.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `CPM231E.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `EKDOS229.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `EKDOS230.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `EKDOSVSW.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| optional `JUKU_NETBOOT_SYSTEM` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |

Run the vendored proof with `sync/janet_netboot_check.sh`. Optional
`JUKU_NETBOOT_SYSTEM` must name a compatible 52K system-track image with
`B400h` load and `CA00h` entry. This fixed-layout regression does not cover
the host's separate `JUKU51`, `JUKURM1`, or ordinary executable formats.

The native C `jukuhost` retains compatibility with the historical NetDisk-v1
handoff described here when explicitly selected with `--disk-protocol 1` and
`--disk-baud 9600`, plus a compatible system and volume. The CLI defaults
are protocol 3 and 19200 baud. In the historical v1 configuration, after stock
bootstrap it keeps the physical serial device at 9600 and repeatedly
sends the `NR` synchronization marker until the resident BIOS sends a valid
request. Requests contain `JD`, operation, sequence, drive, 16-bit track,
logical sector, an optional 128-byte write payload, and XOR checksum. Replies
contain `DJ`, echoed sequence, status, optional read payload, and checksum.
Within a disk-service session, the server caches the most recent request and
reply. An immediate retry with identical sequence, operation, arguments, and
payload receives that reply without repeating the write. A different request
replaces the cache; this is not a history of completed transactions.

The cross-repository `make juku-net-cosim-check` proof runs with no local disk
attached to the simulator. DIR completed with 34 remote reads; SAVE completed
with 38 reads and four writes. Both had zero retries, reached the visible `A>`
prompt, and the resulting flat host volume reopened through cpmtools with an
extractable 256-byte `TEST.COM`. Cosim observed divisor 8 / 2,300 byte cycles
through both bootstrap and resident phases.

## Physical baud qualification

The [serial investigation](juku-serial-19200-investigation.md) owns the
physical captures, baud controls, electrical analysis, and next-session plan.
Both CS00014 and CS00015 reproduced direction-specific receive loss at
19,200 with D57 mode 3/count 4. CS00014 subsequently passed the six-case
BAUDTEST2 suite and a verified remote-disk soak at 19,200 with **mode 2/count
4**. That result qualifies the tested CS00014 image and serial profile;
it does not identify a faulty component or qualify the same setup on CS00015.

Current recoverable stock-ROM sessions use **JF17 at 9600/8O1 throughout**;
see [the bootstrap guide](janet-fastboot.md). The mode-2 results above describe
named historical CP/Mish images. Normal video-slot DRAM refresh and the
CS00024 T35/T36 cooperative diagnostic refresh are separate from these baud
tests.

## Physical host use

For current recoverable CP/M Plus sessions, use the
[JF17 bootstrap guide](janet-fastboot.md). The command below serves an archived
stock system; the subsequent CP/Mish results describe the named historical
images, not the current CP/M Plus implementation.

On Linux, build the host with Bash and a C99 compiler (`CC`, default `cc`).
Connect the Juku serial interface through the appropriate electrical-level
adapter, start the server, then type `TN` at a configured physical Juku ROM
prompt (no Enter). Use `TN0201` only if the ROM asks for `N=` and `S=`:

```sh
sync/jukuhost_linux_build.sh
build/jukuhost --serial /dev/ttyUSB0 \
    --system media/system/EKDOS230.BIN --boot-only
```

The host learns the destination and client station numbers from the first
checksum-valid bootstrap request, so the same command accepts any configured
Juku. The line uses 9600 baud, 8 data bits, odd parity, and one stop bit.
Ordinary 0100h executables and the archived system formats are auto-detected.

The CP/Mish `NETROM1` integration also established an important handoff rule.
NetBios registers RomBios service slots 2, 3, and 9 at `D773h`, `D777h`, and
`D78Fh`; service 9 can run from the ordinary frame path even after USART PIC
requests are masked. A downloaded system must enter under `DI`, restore those
slots to their pre-NetBios `RET` entries, preserve the generic interrupt
dispatcher at `D79Fh`, and update the hardware PIC mask together with its
RomBios shadow at `D454h`. Console I/O should continue through the public
RomBios entry points used by EKDOS rather than installing a replacement frame
handler.

The corrected historical CP/Mish image was qualified on CS00014 with
stock 9600-baud bootstrap followed by a 19200/8O1 mode-2 resident session,
including directory access, text output and warm boot. The
[serial investigation](juku-serial-19200-investigation.md) retains the
physical qualification and its limits.

A historical simulator negative control omitted interrupt exclusion,
service-vector detach, and the coherent PIC update. It reached the initial
prompt but could not echo or execute `DIR`; the corrected control accepted
that input. The negative checkpoint retained the original `D79Fh` dispatcher,
so stale NetBios registrations were sufficient to reproduce the dead keyboard.
Preserving `D79Fh` alone is therefore insufficient.

Systems retaining RomBios input or frame services must preserve that interrupt
contract. A separate RAM renderer must also disable the firmware cursor with
`ESC 4` to prevent the frame service from painting at stale coordinates.
Historical renderer-only simulator results do not qualify a physical RAM BIOS.
For later NetDisk-v3 qualification on CS00015, see the
[M2.1 physical acceptance record](portable-c-host-m2.1-physical-acceptance.md),
which binds the C8/V16 system and host identities to the tested serial profile.

The resident record format already carries a drive byte. CP/Mish `NETROM2`
uses drive 0 for its writable 386 KiB A: volume and drive 1 for a read-only
native Juku B: volume. The latter keeps the period 160-track, 40-record/track,
4 KiB-block DPB; the host converts an unchanged physical 800 KiB `.JUK` image
from cylinder/head interleaving to logical side-then-track order. The C runner maps logical offsets onto the unchanged file on each read,
without allocating an 800 KiB volume. See [the media format](juk-disk-format.md) and
[the host implementation](portable-c-host-implementation.md).
The dual-drive guard reads B:'s final track, rejects B: writes, and preserves A:
writes. A complete cosim run with the published `J3KGAME2.JUK` selects B:,
lists it, and loads `TETRIS.COM` through 71 B: reads.

The historical `NETROM2` dual-drive path passed on both CS00014 and CS00015:
A: remained available, B: listed the native game disk, and CS00015 started
`TETRIS.COM`. This qualifies those historical configurations. The
[CS00015 service record](cs00015-service-record.md#cpmish-dual-network-drive-validation)
retains the physical result; current C-host qualification is recorded in
[the M2.1 acceptance report](portable-c-host-m2.1-physical-acceptance.md).

## Diagnostic relevance

NetBios and the Jukuravi upload service use the same onboard 8251/X3 path,
clocked by D57 counter 0. Qualification of that path matters to both network
boot and the diagnostic link; it does not qualify D57's other channels.

## Reproduction

Run the inspection commands from the repository root. The regression requires
Bash, Python 3 with Unix PTY support, and a C compiler (`CC`, default `cc`)
with AddressSanitizer and UndefinedBehaviorSanitizer support. It runs the
native host-core checks and Python protocol checks before the ROM boot cases;
if `clang` is available, the core checks also use it. Compiled executables,
client captures, and RAM checkpoints are created in temporary directories and
removed when their checks exit; simulator captures do not overwrite
`cosim/vram.bin`.

```sh
python3 - <<'EOF'
import re
rom = open("roms/ekta37.bin","rb").read()
for m in re.finditer(rb"[ -~]{4,}", rom):
    s = m.group().decode()
    if any(k in s for k in ("Net", "Janet", "BOOTSTRAP", "System from")):
        print(f"0x{m.start():04X}: {s!r}")
print("ESC before banners:", hex(rom[0x2C22]), hex(rom[0x23C4]))
EOF

# USART init, TxEN wrapper, receive helper:
python3 cosim/dis8080.py roms/ekta37.bin 34B0 200

# Stock client + host-server regression for every archived system:
sync/janet_netboot_check.sh
```
