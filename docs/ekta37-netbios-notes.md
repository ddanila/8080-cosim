# ekta37 NetBios/Janet boot-path notes

Status: hand-written analysis of the pinned `roms/ekta37.bin` (EktaSoft '88
Serial #0037, RomBios 3.43m, SHA256
`fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27`),
2026-08-12. Byte-level claims are verified against the image and
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

`tools/janet_netboot.py` implements those captured turns, including retries;
it does not write simulator RAM. The five public `JUKUSYS.ZIP` images are
SYSGEN/system-track artifacts rather than 0100h executables: four `E5`-filled
sectors precede 52 system sectors. The host wraps those sectors in a one-record
8080 staging program. NetBios loads 6,784 bytes at `0100h`; the stub copies the
exact 6,656 bytes to the source-defined `CCP=B400h` and jumps to cold
`BIOS=CA00h`.

One simulator-only input distinction is explicit: the ROM's `1209h..123Bh`
hardware-configuration scan samples PB5 high for the unstrapped/onboard-D11
setting. Ordinary keyboard-idle reads remain the drawing-derived `CFh`; merging
those two contexts had previously made all configuration switches look closed
and selected the absent `F0h..F3h` expansion interface.

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

`tools/janet_disk_server.py` implements both phases. After `serve()` completes,
it keeps the physical serial device at 9600 and repeatedly
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

Physical CS00015 completed the full remote SMOKE.COM load and played the tune
at 9600. Early 19,200 experiments were not self-synchronizing and are not
hardware-fault evidence. A later one-shot run did establish one asymmetry:
`BRD!` arrived byte-exactly from CS00015 after the rate switch, but a continuous
136-byte host frame yielded no report, and one resend also yielded none. The
target then had no inter-byte timeout, so a single lost byte stranded it and
prevented localization.

The replacement BAUDTEST sends `B96!` before the rate switch and `BRD!` after
it, then sweeps independently framed host-to-Juku payloads of 1, 2, 4, 8, 16,
32, 64, and 133 unpaced bytes plus 133 bytes paced at 0.75, 1.25, and 2.0 ms.
Each case resets the 8251, has a bounded inter-byte timeout, returns count,
mismatch, checksum, and PE/OE/FE evidence, and waits for a host ACK before
advancing. It finishes with a continuous 133-byte Juku-to-host packet and a
9600 return handshake. The host writes partial JSON after each case.

The C 8251 model now consumes bytes at wire rate while RxRDY is full, latches
OE, discards the newcomer, and preserves the oldest unread byte across command
ER. Both a dedicated negative control and the full sweep guard those semantics.
At both nominal 9600 and 19,200, all eleven cases pass in cosim with character
time scaled to CS00015's measured execution rate; they remain clean at a
conservative 1.5 MHz. A deliberately truncated long case reports timeout and
all following cases still pass. This proves modeled polling throughput and
test recovery, not the unresolved analog/real-8251 host-to-Juku path.

The first recoverable physical sweep on CS00015 (station 08, 2026-08-12) is
saved as `cpmish/cs00015-baudtest-19200-sweep.json`. It sharply narrows that
boundary:

- CS00015 sent `BRD!` correctly at 19,200.
- Unpaced host-to-Juku payloads of 1, 2, 4, and 16 bytes passed exactly. The 8,
  32, 64, and 133-byte cases stopped after clean prefixes of 7, 9, 12, and 6
  payload bytes. There were no mismatches and no PE/OE/FE flags.
- The three nominally paced cases also timed out. Those old host writes were
  not followed by `tcdrain(3)`, however, so their sleeps did not establish
  physical inter-byte gaps through the CP2102 and cannot be used as pacing
  evidence.
- A continuous 133-byte Juku-to-host frame passed byte-exactly. The final ACK
  was not received (`D 00 !`), confirming the same receive-side loss after the
  reverse packet rather than a transmitter or general-rate failure.

Thus 19,200 and 8O1 framing are physically viable in both directions for short
traffic, D57 channel 0 generates a usable clock, and foreground polling can
receive at least sixteen continuous payload bytes. The receiver instead becomes
silent at a history-dependent point and resumes after a full 8251 reset. This
does not resemble ordinary overrun: OE was never latched, every received byte
was the correct clean prefix, a later longer case passed after a reset, and
slowing the host writes did not reliably restore reception.

The sole target operation correlated with every received byte in that build
was an unnecessary rewrite of command `34h` to pulse ER. The Intel-defined ER
operation clears PE/OE/FE; it need not be issued after a clean byte. BAUDTEST
was therefore changed to leave error flags latched for the report and reset the
8251 between cases. The physical host was also changed to call `tcdrain(3)`
before each requested pacing delay.

The revised CS00015 run rejects both explanations. Its JSON is
`cpmish/cs00015-baudtest-19200-revised.json`: only the two-byte unpaced case
passed; the other cases stopped after 0, 0, 0, 1, 7, 12, 5, 0, 0, and 2 payload
bytes. Most importantly, the 0.75, 1.25, and 2.0 ms wire-drained cases all
failed, despite the longest gap being roughly 3.5 character times. There were
again no mismatches or PE/OE/FE flags, Juku-to-host 133 bytes passed, and the
final host ACK was not received (`D 00 !`). Per-byte ER and target polling
throughput are therefore ruled out as primary causes.

The evidence now points to the physical host-to-Juku high-speed receive path.
D57.10 is common to D11 TxC pin 9 and RxC pin 25, so the exact long transmit
packet substantially lowers suspicion on the counter and common clock net.
The direction-specific path is X3.4 `S_SIN` -> D104.4 (К170УП2 receiver) ->
D104.13 -> D11.3 RxD. The К170УП2 datasheet specifies only 45/50 ns propagation
delay, far below a 52 us bit cell, so a healthy receiver is fast enough;
amplitude, threshold, supply, or marginal-device behavior still require bench
capture. The simulator retains no speculative ER-stall behavior because
physical A/B evidence rejected it.

CS00014 then supplied an independent control. Its stock ROM identifies on the
wire as Janet source station 09. At 9600, the corrected BAUDTEST passed all
eleven host-to-Juku cases, including the unpaced 133-byte frame, all three
paced frames, the reverse 133-byte frame, and final ACK with zero mismatches or
8251 errors (`cs00014-baudtest-9600-control.json`). Thus the program, D11
receive logic, D104 path, and complete external chain are sound at the stock
rate. At 19,200, CS00014 reproduced CS00015's receive-only failures while its
reverse 133-byte packet passed. One earlier CS00014 run additionally captured
one wrong byte plus FE, the first explicit framing evidence.

The same external CP2102/MAX/cable chain also passes DOSRAVI bidirectionally at
57,600. That makes a raw bandwidth limit of the chain implausible, though it is
not an identical framing control: DOSRAVI is 8N1 and Janet/BAUDTEST is 8O1.
BAUDTEST was also changed to insert the same empty CALL/RET recovery gap that
EktaSoft 3.7 places after every 8251 control write. A fresh CS00014 19,200 run
still failed in the same way (`cs00014-baudtest-19200-control-gaps.json`), so
back-to-back initialization is ruled out. The next clean discriminator at that
stage was
19,200 at 8N1, changing only parity on the host and D11. If that passes, the
fault is parity-specific; if it fails, the remaining boundary is Juku's
high-speed receive path rather than the general cable bandwidth.

That parity discriminator was run immediately afterward. A separate
`TEST8N1` target used mode `4Eh` (x16, eight data, no parity, one stop) only for
the 19,200 test phase; the host used 19,200/8N1, and both endpoints explicitly
restored 9600/8O1 afterward. CS00014 passed the one- and two-byte cases, proving
the framing change was mutually understood, but longer receive cases again
stopped after short clean prefixes. The 133-byte Juku-to-host packet passed and
the final host-to-Juku ACK failed. The capture is
`cpmish/cs00014-baudtest-19200-8n1.json`. Parity is therefore ruled out.

The remaining phenomenon follows the D57 divisor/rate, specifically in the
Juku receive direction. Two boards reproduce it, the complete external chain
works at 57,600/8N1 with DOSRAVI, and each Juku passes the exhaustive
9600/8O1 control.

The first proposed x16 rate ladder could not be executed with the classic
CP2102. Direct USB and Linux `termios2/BOTHER` requests for the D57-derived
10,989, 12,821, and 15,385 rates were accepted or echoed but quantized on the
wire into the CP2102's supported buckets; the repeated corrupt first marker at
10,989 is therefore host-rate mismatch, not Juku evidence. Baud aliasing could
make such rates persistent on a programmable classic CP2102, but rewriting an
adapter's EEPROM is not justified for diagnosis.

A CP2102-native one-boot ladder instead used D57 BCD divisors 85/77/64 and the
8251's x1 mode to approximate 14,400/16,000/19,200. CS00014 reached 14,400:
target-to-host markers and the 133-byte reverse packet passed, while two- and
four-byte host frames were data- and checksum-correct but latched PE (`08h`),
then later frames lost synchronization. The next rates were not reached. Since
x1 changes the receiver's sampling method, this does not locate a simple rate
threshold; it establishes that x1 is not a useful substitute on this board.

The external cable was then replaced. A fresh 9600/8O1 control again passed
all eleven cases in both directions and the final ACK with zero errors
(`cs00014-baudtest-9600-cable-control.json`). A fresh 19,200/x16/8O1 run with
the same replacement cable reproduced the direction-specific failure: only
the one-byte case passed, longer cases ended after clean prefixes, the reverse
133-byte packet passed, and the ACK failed
(`cs00014-baudtest-19200-x16-new-cable.json`). Cable replacement is therefore
ruled out.

A final x64 idea was invalid as first implemented. EktaSoft leaves D57 channel
0 in mode 3; an 8253 mode-3 periodic count has a documented minimum of 2, so
divisor 1 cannot generate the 1.23 MHz clock needed for x64 at 19,200. Physical
CS00014 emitted four zero bytes instead of `BRD!` and ran no cases. The cosim
model had falsely permitted that count; it now tracks BCD and mode and rejects
mode-2/3 divisor 1. The x64 image was removed, and this attempt is explicitly
non-diagnostic.

Normal Juku RAM refresh is a hardware side effect of video-slot DRAM reads
after EktaSoft programs the D54/D55 raster PITs; EktaSoft contains no software
refresh loop. T35/T36 cooperative software refresh is a CS00024 diagnostic
workaround and is unrelated to this CS00015 BAUDTEST. Until the recoverable
physical sweep completes, the stable network-disk default remains 9600. A
silent/disconnected server is still a separate robustness boundary: the BIOS
waits in a polled receive loop, while malformed replies are retried.

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
Together these examples support retaining 9600 as the proven default while
testing 19,200 as an optional resident protocol with explicit framing,
timeouts, retries, and measured receive behavior.

The consolidated electrical analysis, expected 9600/19,200 waveforms, ranked
diagnosis, and scope-first next-session decision tree are in
`juku-serial-19200-investigation.md`.

## Physical host use

Connect the Juku serial interface through the appropriate electrical-level
adapter, start the server, then type `TN` at a configured physical Juku ROM
prompt (no Enter). Use `TN0201` only if the ROM asks for `N=` and `S=`:

```sh
tools/janet_netboot.py /dev/ttyUSB0 media/system/EKDOS230.BIN
```

The host learns the destination and client station numbers from the first
checksum-valid bootstrap request by default, so the same command accepts any
configured Juku. `--client` and `--server` retain strict matching when needed
for diagnostics. The line defaults to 9600 baud, 8 data bits, odd parity, and
one stop bit. `--load-address` and `--entry` are available for a raw non-JUKUSYS
executable; ordinary 0100h executables are auto-detected.

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

The resident record format already carries a drive byte. CP/Mish `NETROM2`
uses drive 0 for its writable 386 KiB A: volume and drive 1 for a read-only
native Juku B: volume. The latter keeps the period 160-track, 40-record/track,
4 KiB-block DPB; the host converts an unchanged physical 800 KiB `.JUK` image
from cylinder/head interleaving to logical side-then-track order in memory.
The dual-drive guard reads B:'s final track, rejects B: writes, and preserves A:
writes. A complete cosim run with the published `J3KGAME2.JUK` selects B:,
lists it, and loads `TETRIS.COM` through 71 B: reads.

## Relevance to current work

Period NetBios ran on exactly the components the Jukuravi diagnostics
exercise: the 8251 through X3, clocked by D57 counter 0. The Jukuravi
"upload over the 8251 and execute" service model is functionally a
re-creation of the machine's own production network-boot path. On CS00024,
whose D57 has a confirmed channel-2 fault, channel 0's health is therefore
both a diagnostic-link and a period-function concern.

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
