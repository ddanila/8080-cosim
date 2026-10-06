# Rev A Assembly Orientation Notes

Status: **DESIGN HOLD / DRAFT ASSEMBLY INSTRUCTIONS**. Follow
[manufacturing readiness](../docs/rev-a-manufacturing-readiness.md) before release.

## Factory Assembly Intent

- Factory should mount the rows present in the generated JLCPCB BOM/CPL:
  sockets, assigned passives, selected connectors/protection/reset parts, and
  diagnostic LEDs where practical.
- Non-socket rows marked `Manual`, `DNP`, or `Do not populate` in the engineering
  BOM are excluded from factory BOM/CPL and written to `manual-assembly.csv`.
  The exporter always includes `U*` DIP socket footprints as factory sockets,
  even if their engineering row has one of those labels. U23 gets a socket
  but no IC insertion row.
- Do not factory-populate the socketed ICs themselves: Z80, ROM, DRAM, 8255,
  GAL/PAL, and 74xx logic ICs are owner/post-assembly insertion items unless
  the BOM is explicitly changed.

## Manual / Non-Factory Placements

Review `manual-assembly.csv` and the
[current manual-row list](../docs/rev-a-sourcing-plan.md#current-manual-rows)
before ordering. These placements need manual installation or further part/process
qualification; the generated file owns their exact exported identities.

If any of these should be factory-mounted, change the engineering BOM row back
to factory assembly and assign/verify an orderable CPN before export.

## Socket Orientation

- Install every DIP socket with its notch/key matching the silkscreen notch.
- `U..` refdes is placed on the keyed short side of DIP footprints.
- The chip name printed inside each DIP outline follows the long axis of the
  socket body.

## Post-Assembly IC Insertion

- Insert owner-supplied `Z0840004PSC` at `U1`.
- Insert the programmed ROM at `U2` using its 28C256 pin contract. The printed
  `27C256` label does not establish EPROM compatibility: a substitution requires
  explicit write-enable/programming-pin review; see
  [the chip map](../docs/rev-a-chip-map.md).
- Insert owner-supplied `KM4164B-10` DRAMs at `U10`-`U17`.
- Insert the programmed GAL/PAL devices at `U5` and `U24`.
- Insert the 74HC04 mode inverter at `U6` as part of the baseline logic.
- Leave `U3`/`U4` empty for the western Mode A baseline. Test К556РТ4 at `U3`
  in Mode B; observe К155РЕ3 outputs at `U4` in Mode A. Compare each part's
  content with the adopted physical table before insertion.
- Leave the spare `U23` socket empty (DNP).
- Insert `82C55`/compatible PPI at `U30`.
- Insert the remaining socketed 74HCT logic according to the silkscreen chip
  names and engineering BOM.

## Polarized Parts

- `D1` is unidirectional: install the cathode-band end at pad 1/`VCC` and the
  anode at pad 2/`GND`. Inspect 7.62 mm lead forming, body seating, and nearby
  clearance on the first article; the part is a pulse clamp, not sustained
  wrong-supply protection.
- `D2`-`D7` diagnostic LEDs must be installed with polarity matching the LED
  footprint.
- `C50` bulk electrolytic polarity and lead pitch must be checked against the
  selected factory candidate.

## Connector Notes

- `J30` is the 1x15 original-keyboard wiring header; no keyboard power pins are
  present.
- `J1` is the 2-pin +5V/GND input before the fuse.
- `J3` is an optional power-only USB-C input before the fuse. It is in parallel
  with `J1`; use one input source at a time during bring-up. The exact HRO
  TYPE-C-31-M-17 contact and shell-tab geometry is guarded by
  `../docs/rev-a-usb-c-candidate.md`; still confirm the vendor preview and
  first-article mouth/orientation before production.
- `J40` is the Rev A VGA bring-up/debug output: RGB, HSYNC, VSYNC, GND, and
  BLANK_N.
- `J40` and `J90`-`J93` have factory header candidates, but order-time review
  must confirm wave-solder fixture handling.
- `U40` is the TTL640x480 timing/header interface for Rev A, including the
  pixel-load timing handoff to `U41`; it is not the final onboard TTL VGA
  implementation. It has a factory header candidate, but order-time review must
  confirm wave-solder fixture handling.
