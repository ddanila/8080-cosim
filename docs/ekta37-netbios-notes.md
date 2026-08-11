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
    software-configured, not an immediate operand. The runnable `TN0201`
    path writes `08h`. D57 pin 9 is on the drawing's `1,23M` rail, generated
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

- client keys are `TN0201`, with two hexadecimal digits for maximum station
  (`N=02`) and own station (`S=01`); there is no Enter;
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

The regression runs five clients in parallel and stops before the first
`CA00h` instruction. Every destination byte must match its source image:

| Image | 0100h staging | B400h system | handoff |
| --- | ---: | ---: | ---: |
| `CPM22.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `CPM231E.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `EKDOS229.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `EKDOS230.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |
| `EKDOSVSW.BIN` | 6,784 exact bytes | 6,656 exact bytes | `CA00h` |

Run the complete proof with `sync/janet_netboot_check.sh`.

## Physical host use

Connect the Juku serial interface through the appropriate electrical-level
adapter, start the server, then type `TN0201` at the Juku ROM prompt:

```sh
tools/janet_netboot.py /dev/ttyUSB0 media/system/EKDOS230.BIN
```

Defaults are station 02 serving station 01 at 9600 baud, 8 data bits, odd
parity, one stop bit. `--load-address` and `--entry` are available for a raw
non-JUKUSYS executable; ordinary 0100h executables are auto-detected.

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
