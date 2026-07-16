# FDC data-bus polarity audit

Status: **FIRMWARE/HARDWARE POLARITY PROFILES PROVED / TARGET EPROM DUMPS PENDING**

The apparent D100/firmware contradiction is a configuration split, not an
unknown controller polarity. Preserved firmware contains two complete VG93
I/O profiles: one complements every transfer for an inverting КР580ВА87,
while the other replaces every complement with a NOP for a non-inverting
path. The target `.009` board visibly carries the former part.

## Command

```sh
python3 scripts/report_fdc_bus_polarity.py
```

## Exact firmware observations

| Path | CPU-visible OUT 0x1C | Modeled bus | VG93 receives | Meaning | Cycle | PC |
| --- | ---: | --- | ---: | --- | ---: | ---: |
| EKDOS TDD first command | `0x02` | non-inverting | `0x02` | Restore, step-rate 2 | `6666400` | `0xE5DE` |
| Monitor 3.3 T command | `0xFD` | inverting | `0x02` | Restore, step-rate 2 | `9237266` | `0xE2B7` |

The trace checkpoint proves the controller-side byte, not merely the CPU
log: Monitor 3.3's `0xFD` crosses the modeled ВА87 complement and latches
as `0x02` in the VG93 model. Status `0x00` returns to the CPU as `0xFF`,
then the firmware's following `CMA` restores the logical status.

## Preserved firmware profiles

| Firmware | Opcode at every VG93 write/read boundary | Writes | Reads | Required data path |
| --- | --- | ---: | ---: | --- |
| EktaSoft 2.4 | `CMA` (`0x2F`) | `12` | `6` | one inversion (КР580ВА87) |
| EktaSoft 3.1 | `NOP` (`0x00`) | `12` | `6` | non-inverting (КР580ВА86/bypass) |
| EktaSoft 3.5 | `NOP` (`0x00`) | `12` | `6` | non-inverting (КР580ВА86/bypass) |
| EktaSoft 3.7 | `NOP` (`0x00`) | `12` | `6` | non-inverting (КР580ВА86/bypass) |
| Monitor 3.3 | `CMA` (`0x2F`) | `12` | `6` | one inversion (КР580ВА87) |

This is a whole-interface convention, not a patched command constant.
Each listed ROM has exactly 12 writes to ports `0x1C..0x1F` and six
reads. In the ВА87 profiles every OUT is immediately preceded by `CMA`
and every IN immediately followed by `CMA`; in the non-inverting profiles
all 18 positions are deliberately occupied by one-byte `NOP`s. EktaSoft
3.2/4.3 and Monitor 2.2 use a different port-1C/1D bit-stream routine and
are not falsely classified as this register-mapped VG93 template.

Configuration consequence:

- Stock `.009` D100=`КР580ВА87` is compatible with EktaSoft 2.4 and
  Monitor 3.3's guarded VG93 routines.
- EktaSoft 3.1, 3.5, and 3.7 require a non-inverting D100 replacement or
  an explicit bypass. Programming `ekta37` into an otherwise stock `.009`
  board would turn its first Restore `0x02` into Write Track `0xFD`.
- The public ROM names do not prove which pair was installed in this exact
  board. Repeatable physical D15/D16 dumps remain the Tier-3 configuration
  authority and must be preserved as a variant if they differ.

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
  the FD1793 command set. The original Soviet paper defines pins 7..14 as
  the bidirectional DB0..DB7 bus, `/W` as loading that bus into the selected
  register, and Table 3 as the command-register bit codes.
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

`juku_top` still instantiates physical D100 and separate DAL nets for LVS,
but keeps that package non-driving while `/OE` and `T` sources are unknown.
Its behavioral `fdc_1793` consumes logical DB, matching the default ekta37
regression profile. The C trace now exposes `JUKU_FDC_BUS_INVERT=1`; the
guarded Monitor 3.3 run uses it to model the populated `.009` ВА87 path
without changing the controller's logical command semantics.

## Remaining physical closure

1. Dump D15 and D16 twice each and identify the installed polarity profile.
2. Continuity-map D100.9 `/OE` and D100.11 `T`; their remote sources remain
   singleton boundaries even though the required data polarity is resolved.
3. With a matching CMA-profile ROM, capture the first command write and one
   status read: CPU `0xFD` must become DAL `0x02` on write, and logical VG93
   status `0x00` must become CPU-side `0xFF` before firmware `CMA`.
4. If the installed ROM is a NOP profile, record the board modification that
   replaces or bypasses D100; do not silently mix the two configurations.
