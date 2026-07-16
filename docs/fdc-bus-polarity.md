# FDC data-bus polarity audit

Status: **FIRMWARE/PART POLARITY CONTRADICTION ISOLATED**

The `.009` population, straight D100-to-D93 channel wiring, and exact
firmware command bytes do not yet form one electrically coherent claim.
This report keeps the runnable logical FDC model separate from that physical
contradiction and turns it into a decisive operating-level measurement.

## Command

```sh
python3 scripts/report_fdc_bus_polarity.py
```

## Exact firmware observations

| Path | CPU-visible OUT 0x1C | Direct VG93 meaning | Through one 8287 inversion | Cycle | PC | VRAM writes |
| --- | ---: | --- | --- | ---: | ---: | ---: |
| EKDOS TDD first command | `0x02` | restore, step-rate 2 | write track (0xF? family) | `6666400` | `0xE5DE` | `63085` |
| Monitor 3.3 T command | `0xFD` | write track (0xF? family) | restore, step-rate 2 | `9237266` | `0xE2B7` | `230` |

The EKDOS path only succeeds when its first `0x02` is interpreted as
Restore; interpreting it as `0xFD` would request an entire-track write
before the boot-sector reads. Monitor 3.3 deliberately emits the opposite
byte at its `T` command boundary. The two observations exchange meanings
under a single inversion, so this is not a one-command decoder ambiguity.

## Upstream D5 cancellation excluded

D5 cannot supply a second, hidden complement that makes D100 electrically
transparent:

- The official population identifies D5 as `КР580ВК38`. The 1988 Soviet
  КР580 reference, section 3.12, draws every D0..D7 channel directly to its
  same-numbered DB0..DB7 channel with bidirectional arrows and no inversion
  bubbles (figures 3.73 and 3.74, printed page 161). It says the ВК28 and
  ВК38 differ only in the duration/source timing of the two write strobes.
- The same reference explicitly calls `КР580ВА87` the inverting variant
  beside non-inverting `КР580ВА86`, and draws bubbles on all ВА87 B-side
  channels (section 3.14, figure 3.79, printed page 166). The notation is
  therefore polarity-significant rather than an omitted drawing detail.
- Board topology is bit-for-bit from D1 CPU `DC0..DC7` through D5 to system
  `DB0..DB7`. Those same DB rails directly join D15/D16 data pins and D100
  A0..A7; there is no intervening data permutation or inverter.
- The guarded functional D15+D16 images concatenate exactly to the known
  `fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27`
  ekta37 image. Its reset bytes are `C3 17 00` (8080
  `JMP 0017`); one complement would be `3C E8 FF`, which is not that boot
  vector. This is a logical replica constraint, not a substitute for the
  still-requested Tier-3 physical D15/D16 repeat dumps.

The runnable `sysctl_8238` bridge therefore remains non-inverting. Making
D5 invert merely to cancel D100 would contradict the device symbol, the
straight board topology, and every direct system-bus ROM/peripheral path.

## Physical evidence

- Factory `.009` census position D100 is `КР580ВА87`, the inverting
  Intel-8287-compatible bidirectional transceiver; the target component
  photograph independently shows that marking.
- D100 channels are straight: A0..A7 on system `DB0..DB7` pair with
  B0..B7 on D93 `DAL0..DAL7`; no bit permutation can cancel a bitwise
  complement.
- D93 is the populated `КР1818ВГ93`. Its documented command families use
  the normal logical codes (`0x0?` Restore, `0xF?` Write Track), matching
  the FD1793 command set.
- D100 `/OE` pin 9 and direction `T` pin 11 remain physical singleton
  boundaries. Their control sources have not been measured.

Primary references: Intel M8286/M8287 data sheet
(<https://www.silicon-ark.co.uk/datasheets/m8286-m8287-datasheet-intel.pdf>);
КР580ВА87 device sheet
(<https://static.chipdip.ru/lib/052/DOC016052028.pdf>); local Western
Digital `FD179X-01` data sheet at
`ref/wd1772-vg93/fd179x-01-datasheet.pdf`; V. A. Shakhnov (ed.),
*Микропроцессоры и микропроцессорные комплекты интегральных микросхем*,
vol. 1 (1988), sections 3.12 and 3.14
(<https://djvu.online/file/iEIJ8fbnBceel>), printed pp. 161 and 166.

## Runnable-model boundary

`juku_top` instantiates the physical D100 package and its separate DAL nets
for LVS, but that package is deliberately non-driving while `/OE` and `T`
are unknown. The behavioral `fdc_1793` remains connected directly to logical
system `DB`, which is why EKDOS currently boots. This is an explicit
functional bypass, not proof that the populated D100 path is correct.

## Decisive bench capture

1. During the already pinned first EKDOS command at CPU PC `0xE5DE`, capture
   system DB, D100 B-side/D93 DAL, D100.9 `/OE`, D100.11 `T`, D93.2 `/WE`,
   and D93 STEP/WG if channels permit. The CPU-side byte must be `0x02`.
2. Record whether D93 DAL receives `0x02` or `0xFD`, and whether the
   controller performs Restore (STEP toward track zero) or Write Track (WG).
3. Repeat one status read to prove B-to-A direction and inversion rather than
   inferring it from command-side behavior.

Disposition:

- `DAL=0x02` makes the populated path functionally non-inverting; identify
  the physical cancellation or correct D100 to the proved part/topology.
- `DAL=0xFD` plus Restore would prove a nonstandard/inverted D93 bus sense.
- `DAL=0xFD` plus WG proves the `.009` hardware and preserved firmware are
  not the same working configuration; do not hide that with a simulator fit.
