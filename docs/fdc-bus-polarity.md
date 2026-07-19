# FDC data-bus polarity audit

Status: **FIRMWARE PROFILES PROVED / PHYSICAL D100 ATTRIBUTION RETIRED / TARGET EPROM DUMPS PENDING**

Preserved firmware contains two complete VG93 I/O profiles: one complements
every transfer, while the other replaces every complement with a NOP.
Factory sheet 1 now proves D93 DAL0..DAL7 connect directly to system
DB0..DB7 and D100 instead buffers eight floppy-drive outputs. Therefore the
old attribution of the firmware split to D100 is retired; the installed ROM
pair and the historical reason for the two profiles remain open.

## Command

```sh
python3 scripts/report_fdc_bus_polarity.py
```

## Exact firmware observations

| Path | CPU-visible OUT 0x1C | Modeled bus | VG93 receives | Meaning | Cycle | PC |
| --- | ---: | --- | ---: | --- | ---: | ---: |
| EKDOS TDD first command | `0x02` | non-inverting | `0x02` | Restore, step-rate 2 | `6666400` | `0xE5DE` |
| Monitor 3.3 T command | `0xFD` | inverting | `0x02` | Restore, step-rate 2 | `9237266` | `0xE2B7` |

The diagnostic checkpoint proves the controller-side byte, not merely the
CPU log: Monitor 3.3's `0xFD` crosses the optional modeled complement and
latches as `0x02` in the VG93 model. On the read-only Track-0 fixture, the
dynamic Type-I status is `0x44` (WRITE PROTECT | TRACK 0); it returns
through that diagnostic adjunct as CPU `0xBB`, then the following `CMA`
restores logical `0x44`.

## Preserved firmware profiles

| Firmware | Opcode at every VG93 write/read boundary | Writes | Reads | Required data path |
| --- | --- | ---: | ---: | --- |
| EktaSoft 2.4 | `CMA` (`0x2F`) | `12` | `6` | one diagnostic inversion |
| EktaSoft 3.1 | `NOP` (`0x00`) | `12` | `6` | direct bus |
| EktaSoft 3.5 | `NOP` (`0x00`) | `12` | `6` | direct bus |
| EktaSoft 3.7 | `NOP` (`0x00`) | `12` | `6` | direct bus |
| Monitor 3.3 | `CMA` (`0x2F`) | `12` | `6` | one diagnostic inversion |

This is a whole-interface convention, not a patched command constant.
Each listed ROM has exactly 12 writes to ports `0x1C..0x1F` and six
reads. In the ВА87 profiles every OUT is immediately preceded by `CMA`
and every IN immediately followed by `CMA`; in the non-inverting profiles
all 18 positions are deliberately occupied by one-byte `NOP`s. EktaSoft
3.2/4.3 and Monitor 2.2 use a different port-1C/1D bit-stream routine and
are not falsely classified as this register-mapped VG93 template.

Configuration consequence:

- Factory sheet 1 requires a direct physical D93 data bus; D100 cannot
  explain or select either firmware profile.
- EktaSoft 3.1, 3.5, and 3.7 match the recovered direct bus. EktaSoft 2.4
  and Monitor 3.3 retain systematic CMA sites whose hardware context is
  not yet identified.
- The public ROM names do not prove which pair was installed in this exact
  board. Repeatable physical D15/D16 dumps remain the Tier-3 configuration
  authority and must be preserved as a variant if they differ.

## Direct physical bus constraint

The data path is now source-proved without an intervening D100:

- The official population identifies D5 as `КР580ВК38`. The 1988 Soviet
  КР580 reference, section 3.12, draws every D0..D7 channel directly to its
  same-numbered DB0..DB7 channel with bidirectional arrows and no inversion
  bubbles (figures 3.73 and 3.74, printed page 161). It says the ВК28 and
  ВК38 differ only in the duration/source timing of the two write strobes.
- Board topology is bit-for-bit from D1 CPU `DC0..DC7` through D5 to system
  `DB0..DB7`. Those same rails directly join D15/D16 and D93 pins 7..14;
  factory sheet 1 shows no intervening permutation or inverter.
- The guarded functional D15+D16 images concatenate exactly to the known
  `fc44df76b2601ab81745f2512edb7a56bb24dca6419e7173a5bf11cae4c1fc27`
  ekta37 image. Its reset bytes are `C3 17 00` (8080
  `JMP 0017`); one complement would be `3C E8 FF`, which is not that boot
  vector. This is a logical replica constraint, not a substitute for the
  still-requested Tier-3 physical D15/D16 repeat dumps.

The runnable `sysctl_8238` bridge therefore remains non-inverting. Making
D5 invert merely to explain the CMA profile would contradict the device symbol, the
straight board topology, and every direct system-bus ROM/peripheral path.

## Physical evidence

- Factory sheet 1 directly joins D93 pins 7..14 to DB0..DB7.
- The same sheet assigns D100 inputs to D93 DIR/STEP/HLD/TG43/WG, a
  write-data/precompensation boundary, and PPI motor/side-select outputs.
  D100 outputs land on X4 drive-control contacts 9..20.
- D93 is the populated `КР1818ВГ93`. Its documented command families use
  the normal logical codes (`0x0?` Restore, `0xF?` Write Track), matching
  the FD1793 command set. The original Soviet paper defines pins 7..14 as
  the bidirectional DB0..DB7 bus, `/W` as loading that bus into the selected
  register, and Table 3 as the command-register bit codes.
- D100 pins 9 and 11 are factory-drawn on the same continuation `1`; its
  upstream source and the D100.6 write-data input remain boundaries.

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

`juku_top` now instantiates physical D93 directly on DB and physical D100
on its recovered drive-output vector. The former opt-in inverted-bus builds
remain as an explicitly unmapped diagnostic firmware-profile adjunct. They
continue to guard the systematic CMA behavior without claiming board copper.

## Remaining physical closure

1. Dump D15 and D16 twice each and identify the installed polarity profile.
2. Identify why the preserved CMA-profile firmware exists; do not attribute
   it to physical D100 without new primary evidence.
3. Trace the upstream source of shared D100 pins 9/11 continuation `1` and
   the D100.6 write-data/precompensation input.
