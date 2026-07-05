# Rev A Assembly Orientation Notes

Status: first-pass order-package notes; review against selected factory parts
before upload.

## Factory Assembly Intent

- Factory should mount sockets, passives, headers/connectors, oscillator/reset,
  protection parts, and diagnostic LEDs where practical.
- Do not factory-populate the socketed ICs themselves: Z80, ROM, DRAM, 8255,
  GAL/PAL, and 74xx logic ICs are owner/post-assembly insertion items unless
  the BOM is explicitly changed.

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
  selected part.

## Connector Notes

- `J30` is the 1x15 original-keyboard wiring header; no keyboard power pins are
  present.
- `J1` is the 2-pin +5V/GND input before the fuse.
- `J3` is an optional power-only USB-C input before the fuse. It is in parallel
  with `J1`; use one input source at a time during bring-up.
- `J40` is the Rev A VGA bring-up/header output.
- `U40` is the TTL640x480 timing/header interface for Rev A, not the final
  onboard TTL VGA implementation.
