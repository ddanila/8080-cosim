# Rev A Assembly Orientation Notes

Status: first-pass order-package notes; review against selected factory parts
before upload.

## Factory Assembly Intent

- Factory should mount the rows present in the generated JLCPCB BOM/CPL:
  sockets, assigned passives, selected connectors/protection/reset parts, and
  diagnostic LEDs where practical.
- Rows marked `Manual`, `DNP`, or `Do not populate` in the engineering BOM are
  deliberately excluded from the factory BOM/CPL and written to
  `manual-assembly.csv`.
- Do not factory-populate the socketed ICs themselves: Z80, ROM, DRAM, 8255,
  GAL/PAL, and 74xx logic ICs are owner/post-assembly insertion items unless
  the BOM is explicitly changed.

## Manual / Non-Factory Placements

Review `manual-assembly.csv` before ordering. Rev A currently expects manual
installation or later CPN/footprint resolution for:

- `D1` +5V TVS clamp.
- `J30` and `U40` bring-up/debug headers.
- `R6` PWR_OK link and `R15` keyboard encoder enable link.
- `U50` clock oscillator.
- `U51` reset supervisor.

If any of these should be factory-mounted, change the engineering BOM row back
to factory assembly and assign/verify an orderable CPN before export.

## Socket Orientation

- Install every DIP socket with its notch/key matching the silkscreen notch.
- `U..` refdes is placed on the keyed short side of DIP footprints.
- The chip name printed inside each DIP outline follows the long axis of the
  socket body.

## Post-Assembly IC Insertion

- Insert owner-supplied `Z0840004PSC` at `U1`.
- Insert the programmed `27C256`-class ROM at `U2`.
- Insert owner-supplied `KM4164B-10` DRAMs at `U10`-`U17`.
- Insert the programmed GAL/PAL devices at `U5` and `U24`.
- Insert `82C55`/compatible PPI at `U30`.
- Insert the remaining socketed 74HCT logic according to the silkscreen chip
  names and engineering BOM.

## Polarized Parts

- `D1` TVS polarity and footprint must be checked against the selected part
  before ordering.
- `D2`-`D7` diagnostic LEDs must be installed with polarity matching the LED
  footprint.
- `C50` bulk electrolytic polarity and lead pitch must be checked against the
  selected factory candidate.

## Connector Notes

- `J30` is the 1x15 original-keyboard wiring header; no keyboard power pins are
  present.
- `J1` is the 2-pin +5V/GND input before the fuse.
- `J3` is an optional power-only USB-C input before the fuse. It is in parallel
  with `J1`; use one input source at a time during bring-up.
- `J40` is the Rev A VGA bring-up/debug output: RGB, HSYNC, VSYNC, GND, and
  BLANK_N.
- `J40` and `J90`-`J93` have factory header candidates, but order-time review
  must confirm wave-solder fixture handling.
- `U40` is the TTL640x480 timing/header interface for Rev A, including the
  pixel-load timing handoff to `U41`; it is not the final onboard TTL VGA
  implementation.
