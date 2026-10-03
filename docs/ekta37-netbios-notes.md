# ekta37 NetBios/Janet boot-path notes

Status: hand-written analysis of the pinned `roms/ekta37.bin` (EktaSoft '88
Serial #0037, RomBios 3.43m, SHA256
`fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27`).
Byte-level claims are verified against the image and
reproducible with the commands at the end; interpretations are labeled.
Sibling identity/context is in
[`ektasoft-rombios-lineage.md`](ektasoft-rombios-lineage.md).

## What NetBios is

The 3.4x RomBios line's second BIOS is the school-network boot path. There
is no dedicated network hardware: NetBios drives the machine's one 8251
USART (D11, ports `08h/09h`), whose clock is D57 counter 0 and whose line
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
  machines. The boot subset is now capture-derived below; unrelated Janet
  services and the monitor call `FF7Ah`'s general contract remain untraced.
- The `FF89h` calls install interrupt/service handlers. Functional cosim now
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
- physical frames start `E4 E4`, carry destination/source/control, and finish
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

One simulator-only input distinction is explicit: the ROM's `1209h..123Bh`
hardware-configuration scan samples PB5 high for the unstrapped/onboard-D11
setting. Ordinary keyboard-idle reads remain the drawing-derived `CFh`; merging
those two contexts had previously made all configuration switches look closed
and selected the absent `F0h..F3h` expansion interface.

This PB5 behavior is specific to the archived EktaSoft 3.7 ROM. At offsets
`1211h..1216h` in `roms/ekta37.bin`, the bytes `DB 05 2F FB E6 20` read PPI
port B, complement it, and mask bit 5. The exact `.009 Э3` sheet-1 detail
instead connects D26 PB4/pin22 to E8.3, PB5/pin23 to E8.2, and `CONTRDAT`
to E8.4. The `.009 СБ` assembly drawing and owner board photo both show E8
bridged 3–4. Thus the ROM's PB5 S21 read and the surviving `.009` board's
PB4 selector are revision-incompatible as drawn. The simulator retains the
PB5 behavior for its EktaSoft 3.7 reference runs; the original board's
firmware/configuration behavior needs a matching ROM readback or a powered
PB4/PB5 observation before claiming the S21 path works on this revision.
The four other archived #0024/#0031/#0032/#0035 images use the same PB5
mask; #0043 has a different read sequence and no evidence for a PB4 S21
scan (`docs/ektasoft-rombios-lineage.md`).

The regression runs the five vendored clients plus an optional external system
in parallel and stops before the first
`CA00h` instruction. Every destination byte must match its source image:

| Image | 0100h staging | B400h system | handoff |
| --- | ---: | ---: | ---: |
| `CPM22.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `CPM231E.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `EKDOS229.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `EKDOS230.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `EKDOSVSW.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| optional `JUKU_NETBOOT_SYSTEM` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |

Run the vendored proof with `sync/janet_netboot_check.sh`. For the CP/Mish Juku
branch, first build its system and add it as the sixth case:

```sh
JUKU_NETBOOT_SYSTEM=../cpmish/juku-system.bin sync/janet_netboot_check.sh
```

On 2026-08-12 that six-system run passed byte-exactly. This proves the stock
NetBios bootstrap transport and `CA00h` handoff. The CP/Mish diskless mode then
takes over the 8251, retains D57 counter-0 divisor 8 (nominal 9,600 baud), and
exchanges checksummed 128-byte CP/M disk records with a host-backed A: image.
Keeping the proven 9600/8O1 rate avoids modifying the ROM protocol while the
filesystem phase remains independently retried.

The native C `jukuhost` retains compatibility with the historical NetDisk-v1
handoff described here. In that configuration, after stock bootstrap it keeps
the physical serial device at 9600 and repeatedly
sends the `NR` synchronization marker until the resident BIOS sends a valid
request. Requests contain `JD`, operation, sequence, drive, 16-bit track,
logical sector, an optional 128-byte write payload, and XOR checksum. Replies
contain `DJ`, echoed sequence, status, optional read payload, and checksum.
The server recognizes duplicate sequence/request pairs and returns the previous
reply, making a retried write idempotent.

The cross-repository `make juku-net-cosim-check` proof runs with no local disk
attached to the simulator. DIR completed with 34 remote reads; SAVE completed
with 38 reads and four writes. Both had zero retries, reached the visible `A>`
prompt, and the resulting flat host volume reopened through cpmtools with an
extractable 256-byte `TEST.COM`. Cosim observed divisor 8 / 2,300 byte cycles
through both bootstrap and resident phases.

## Physical baud qualification

CS00015 completed remote `SMOKE.COM` loading and playback at 9600. Historical
BAUDTEST runs on CS00014 and CS00015 then exposed direction-specific loss at
19,200 with D57 mode 3/count 4: long Juku-to-host packets passed while
host-to-Juku packets stopped after clean prefixes. These were finite diagnostic
runs, not evidence that every 19,200 configuration fails.

The controls ruled out parity selection, per-byte error reset, initialization
recovery gaps, and cable replacement as sufficient fixes. Drained host pacing
also failed. A classic CP2102 quantized the requested intermediate baud rates,
so that rate ladder was not diagnostic. The x1 experiment changed sampling
behavior; the x64/19,200 attempt used invalid periodic divisor 1 and was
removed. Neither establishes a receive-rate threshold.

The subsequent BAUDTEST2 run on CS00014 passed all six 19,200/x16 cases with
**D57 mode 2/count 4**. A remote-disk soak then completed 108 reads and 67
writes, verified its 8 KiB test file after close/reopen, deleted it, and emitted
`M2PASS!`, with zero retries and UART error-counter deltas. This narrows the
remaining diagnosis to clock edge/duty sensitivity; it does not identify a
faulty component or qualify the same setup on CS00015.

The [serial investigation](juku-serial-19200-investigation.md) owns the detailed
physical results, capture identities, electrical analysis and scope decision
tree. Earlier capture names in the sibling `cpmish` checkout remain useful
for interpreting the controls:

| Control | Capture |
| --- | --- |
| CS00015 initial/revised 19,200 sweep | `cs00015-baudtest-19200-sweep.json`, `cs00015-baudtest-19200-revised.json` |
| CS00014 stock-rate control | `cs00014-baudtest-9600-control.json` |
| CS00014 initialization-gap and parity controls | `cs00014-baudtest-19200-control-gaps.json`, `cs00014-baudtest-19200-8n1.json` |
| CS00014 replacement-cable controls | `cs00014-baudtest-9600-cable-control.json`, `cs00014-baudtest-19200-x16-new-cable.json` |

Current recoverable stock-ROM sessions use **JF17 at 9600/8O1 throughout**;
see [the bootstrap guide](janet-fastboot.md). The mode-2 results above describe
named historical CP/Mish images. Normal video-slot DRAM refresh and the
CS00024 T35/T36 cooperative diagnostic refresh are separate from these baud
tests.

## Comparable period implementations

The rate is not beyond the period silicon. Intel specifies the 8251A for
asynchronous operation through 19.2 kbaud
([8251A datasheet](https://community.intel.com/cipcp26785/attachments/cipcp26785/programmable-devices/89914/1/P8251A.pdf)). More directly, the Soviet
Korvet ПК8010/8020 technical source documents a КР580ВВ51А local-network
adapter clocked at 312 kHz in x16 mode, yielding about 19,500 bit/s. Its mode
constant is the same x16, 8-bit, parity-enabled, one-stop combination as
Juku's `5Eh`, and it exposes a receive-byte interrupt
([Korvet technical documentation](https://emu80.org/docs/korvet_techinfo)).
This proves the Soviet 8251 clone was used near this rate; it does not prove
Juku's analog path or polling implementation.

Robotron PC1715 is a useful conservative comparison rather than a 19,200
precedent. Its undocumented ROM serial bootstrap is documented as 9600/8O1,
and its bidirectional V.24 expansion made baud, data bits, stop bits, and
handshaking software-configurable
([PC1715 serial boot](https://oldcomputer.info/8bit/robo1715/index.htm),
[PC1715 interfaces](https://www.robotrontechnik.de/html/computer/pc1715.htm)).
These comparisons provide period context. Juku qualification depends on the
actual clock mode, resident protocol and physical results above.

The consolidated electrical analysis, expected 9600/19,200 waveforms, ranked
diagnosis, and scope-first next-session decision tree are in
`juku-serial-19200-investigation.md`.

## Physical host use

For current recoverable CP/M Plus sessions, use the
[JF17 bootstrap guide](janet-fastboot.md). The command below serves an archived
stock system; the subsequent CP/Mish results describe the named historical
images, not the current CP/M Plus implementation.

Connect the Juku serial interface through the appropriate electrical-level
adapter, start the server, then type `TN` at a configured physical Juku ROM
prompt (no Enter). Use `TN0201` only if the ROM asks for `N=` and `S=`:

```sh
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

This was confirmed on physical CS00014 on 2026-08-13. The corrected CP/Mish
image booted through the stock 9600-baud loader, ran its Janet A: disk at
19200/8O1 using D57 mode 2/count 4, accepted `DIR`, displayed all of
`README.TXT`, and survived `Ctrl-C` warm boot followed by another `DIR`.
Requests through sequence `90` completed with status zero and the prior
vertical-line display corruption did not recur.

The old handoff is now reproducible without hardware. CP/Mish builds a
simulator-only negative image which deliberately omits the early interrupt
exclusion, NetBios service-vector detach, and coherent PIC hardware/shadow
update. It reaches the normal initial prompt, but matrix input `DIR` is neither
echoed nor executed and network reads remain at the 32 startup directory
records. The corrected RomBios control immediately accepts the same input and
reaches 35 reads. The negative checkpoint still contains the original
`D79Fh = E3 22 56 D4 E1` dispatcher prefix. This isolates the stale NetBios
registrations as sufficient to reproduce the dead keyboard; the separately
observed interim D79F overwrite remains an additional architectural violation
associated with the physical video corruption.

This result defined the safe route toward a RAM-owned CP/M console. The 52K
`B400h/BC00h/CA00h` RomBios build remains the baseline; the separate 51K
experiment shifts CCP/BDOS/BIOS to `B000h/B800h/C600h`, retaining the same
exclusive `CE00h` upper boundary while gaining 1 KiB for a renderer and font.
The unmodified ROM now boots that layout through the host-supplied `JUKU51`
staging copier.

The historical renderer-only Stage 1 is simulator-proven. CP/M output is rendered from RAM through temporary
all-RAM mode 3, while RomBios still owns input and IR5. The retained firmware
frame service first had to be told `ESC 4`: otherwise it painted a solid cursor
at its stale coordinates over the independent RAM screen. The focused test
boots through stock Janet, executes matrix-typed `DIR`, completes 35 disk
reads, preserves `D79Fh`, and compares all 9,600 framebuffer bytes with a
reference rendering of the captured BIOS transcript. It caught and rejected
both a broken clear loop and the stale cursor. This renderer-only result does not establish physical qualification of that
image. Later independent RAM-BIOS/NetDisk-v3 qualification is summarized in
[the serial investigation](juku-serial-19200-investigation.md). A system retaining
RomBios must preserve its interrupt contract; D79F is not a standalone keyboard
hook.

The resident record format already carries a drive byte. CP/Mish `NETROM2`
uses drive 0 for its writable 386 KiB A: volume and drive 1 for a read-only
native Juku B: volume. The latter keeps the period 160-track, 40-record/track,
4 KiB-block DPB; the host converts an unchanged physical 800 KiB `.JUK` image
from cylinder/head interleaving to logical side-then-track order in memory.
The dual-drive guard reads B:'s final track, rejects B: writes, and preserves A:
writes. A complete cosim run with the published `J3KGAME2.JUK` selects B:,
lists it, and loads `TETRIS.COM` through 71 B: reads.

Physical CS00014 then passed the same `NETROM2` dual-drive configuration on
2026-08-13: the existing network A: remained available and the machine selected
and used the native `J3KGAME2.JUK` B:. This validates the drive-1 record path,
160-track CP/M DPB, and in-memory physical-image conversion on real hardware;
B: remains read-only by design.

Physical CS00015 independently passed the complete interactive path on
2026-08-13: it reached the CP/Mish prompt, completed `DIR` on A:, selected B:,
completed `DIR` on the native game disk, and started `TETRIS.COM`. The same
dual-drive implementation is therefore physically validated on both CS00014
and CS00015.

## Relevance to current work

Period NetBios ran on exactly the components the Jukuravi diagnostics
exercise: the 8251 through X3, clocked by D57 counter 0. The Jukuravi
"upload over the 8251 and execute" service model is functionally a
re-creation of the machine's own production network-boot path. Channel 0's
health is therefore both a diagnostic-link and a period-function concern. The legacy CS00024 channel-2 `99/99` samples do not establish a D57
fault: they were read before a guaranteed vertical-retrace clock edge.
[The corrected D57 probe](cs00024-t36-diagnosis.md#d57-channel-2-timing-correction)
has a positive control on CS00015 and still requires a CS00024 rerun.

## Reproduction

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

External context (not load-bearing for the claims above):
[juku3000 project](https://j3k.infoaed.ee/),
[Juku E5104 at Arvutimuuseum](https://arvutimuuseum.ee/cs00000/).
