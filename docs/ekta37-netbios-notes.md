# ekta37 NetBios/Janet boot-path notes

Status: hand-written analysis of the pinned `roms/ekta37.bin` (EktaSoft '88
Serial #0037, RomBios 3.43m, SHA256
`fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27`),
2026-08-11. Byte-level claims are verified against the image and
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
    software-configured, not a ROM constant. The cold-boot value programmed
    at `01D4h..0221h` is control `1Fh`, count BCD 32 = 2400 baud;
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

The `34xxh` ROM region executes relocated to high RAM (the code's absolute
references target `EFxxh..FFxxh`), so the offsets above are ROM file
positions, not runtime addresses.

## Interpretation (labeled)

- The TxEN gating around transmissions plus RTS use and per-frame odd
  parity read as **shared half-duplex line discipline**: multiple stations
  on one line, only the active talker driving it, every frame
  error-checked. This fits the documented school deployment — one
  teacher station with floppy drives and printer serving diskless student
  machines — but the wrapped monitor call `FF7Ah` and the served protocol
  are not reverse-engineered here.
- The `FF89h` calls are consistent with installing interrupt/service
  handlers (the machine has a КР580ВН59/8259 PIC), which would make
  network reception interrupt-driven unlike the polled console; `FF89h`
  semantics are unverified.
- The configurable `D5B2h` divisor means Janet's line rate may differ from
  the 2400-baud boot default; where that variable is set is not traced.

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
```

External context (not load-bearing for the claims above):
[juku3000 project](https://j3k.infoaed.ee/),
[Juku E5104 at Arvutimuuseum](https://arvutimuuseum.ee/cs00000/).
