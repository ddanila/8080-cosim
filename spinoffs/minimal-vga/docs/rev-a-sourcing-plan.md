# Rev A future sourcing policy

Status: **DESIGN HOLD / NOT A SHOPPING LIST**.

This document preserves the assembly responsibility and verification rules for
a possible future VJUGA build. Specific stock, prices, vendor capabilities, and
assembly-library CPNs are intentionally not treated as durable documentation;
they must be rechecked only after functional design release.

## Assembly responsibility

| Group | Intended handling after release |
| --- | --- |
| Z80, ROM, DRAM, 8255, GAL/PAL, DIP logic | socketed; owner-supplied IC insertion after board assembly |
| Sockets, ordinary passives, protection, connectors, diagnostics | factory candidate if the selected process and parts support them |
| Rows marked `Manual`, `DNP`, or `Do not populate` | excluded from factory BOM/CPL and installed or left empty per the final record |
| Programmed ROM/GAL devices | program and verify before insertion; retain source and readback hashes |

The generated assembly BOM must describe sockets at the `U*` designators, not
the owner-supplied ICs. `post-assembly-insertion.csv` owns the later IC list.
Never upload the engineering BOM as a factory placement BOM.

## Part classes to freeze

- DIP-40 sockets for Z80 and 8255.
- DIP-28 socket and an electrically compatible 27C256/28C256-class ROM choice.
- DIP-24 sockets and a supported GAL22V10-class programming workflow.
- Eight narrow DIP-16 sockets and exact 4164-compatible DRAM pinout/timing.
- DIP-14/16 logic sockets with the final HCT/TTL family decision.
- 100 nF local decoupling, bulk capacitance, pullups, keyboard/video series
  resistors, diagnostic LEDs/resistors, and configuration links.
- +5 V input connector/USB-C sink, CC resistors, fuse, TVS, clock oscillator,
  reset supervisor, debug headers, and cable-facing keyboard/VGA headers.

Recorded owner-supplied candidates are a `Z0840004PSC` 4 MHz DIP Z80 and
`KM4164B-10` 100 ns DIP DRAM. Treat these as candidates until their actual
markings, pinout, electrical limits, and bench behavior are checked.

## Current manual rows

The present draft classifies six placements as manual:

- `D1` TVS;
- `J30` keyboard header;
- `R6` and `R15` zero-ohm links;
- `U50` oscillator; and
- `U51` reset supervisor.

The generated manual-row report checks that this set does not change silently.
It does not prove the selected parts fit or function.

## Release-time checks

After real-ROM boot, VGA output, and GAL/timing validation release the design:

1. Verify every IC and connector pinout against the selected manufacturer's
   datasheet and the final PCB footprint.
2. Recalculate the +5 V budget and fuse/trace margin with the selected lots.
3. Check socket body width, lead spacing, insertion orientation, and assembly
   process support.
4. Requery the vendor's official parts library for every factory-mounted row;
   reject obsolete, out-of-stock, or package-mismatched CPNs.
5. Regenerate BOM/CPL/manual/post-insertion outputs and compare their designator
   sets.
6. Save the selected-part datasheets, order-time CPN export, vendor DFM/preview,
   and final package hashes with the private build record.

Useful order-time primary sources are the chosen manufacturers' datasheets and
the vendor's official parts library/assembly documentation. Marketplace seller
claims are not compatibility evidence.
