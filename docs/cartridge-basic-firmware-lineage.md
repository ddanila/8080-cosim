# Cartridge BASIC firmware-lineage audit

Status: **ONBOARD BASIC LINEAGE PINNED / MISSING PAGE NOT DERIVED**

This generated audit tests whether the Monitor ROMs contain source evidence
for the unresolved `jbasic11.bin` cartridge tail. It establishes a strong
lineage match, but deliberately does not export a reconstructed cartridge:
the exact match ends before the missing page.

## Command

```sh
python3 scripts/report_cartridge_basic_firmware_lineage.py
```

## Exact body mapping

Cartridge offsets `0x0100..0x1D37` map to
Monitor-ROM offsets `0x03C8..0x1FFF`
with a constant source delta of `+0x2C8`. The compared span is
`7224` bytes (`0x1C38`).

| Firmware | SHA256 | Compared slice SHA256 | Mismatches | Disposition |
| --- | --- | --- | ---: | --- |
| Monitor 2.2 (`roms/jmon22.bin`) | `1b68f89ae4355391f434b3fae34e95cb4b150bf4bbcb967b5b177d48cd390589` | `fdc504aaf873427f27700a67a6a840e4e741b5a28e1fbf0e37aed78e01207247` | `1` | single-byte divergence |
| Monitor 3.3 (`roms/jmon33.bin`) | `ce9e9c63abbb1780566423a871081bd0bf048a2f3c79e370b465ea9869ff51b8` | `9d001c1e6312e80a541e8862301634572dd0811f54e378c1adbf7e965a2b71d1` | `0` | byte-exact |

Mismatch detail:

- Monitor 2.2: cartridge `0x1C34=0xDA`; Monitor ROM `0x1EFC=0x9A`.

The Monitor 3.3 slice is byte-identical to the cartridge slice. Monitor
2.2 differs at only one byte. This proves that the public cartridge and
the onboard BASIC are the same firmware lineage, and it supplies the
entire meaningful BASIC body already present in the 8 KiB cartridge.

## Cartridge suffix

| Span | Bytes | Non-zero bytes | SHA256 | Interpretation |
| --- | ---: | ---: | --- | --- |
| `0x1D38..0x1EFF` | `456` | `0` | `b960fb5cb94682dfc4a873035d65f8befdcb9bed0e7db0feb905f0dcf437b38c` | zero padding |
| `0x1F00..0x1FFF` | `256` | `18` | `e625e901f06b6eca4a5c9b8dca79b889fd90cf2db1f7771f67e9284365a70a9b` | relocation bootstrap page |

The required loop-survival sequence occurs at bootstrap offset
`0x09`. The earlier final-page-mirror experiment therefore
already tested the strongest source-adjacent reconstruction: a second copy
of this bootstrap page after the known 8 KiB image. It completed the
self-overwriting relocation but still did not render `READY`.

## Monitor 2.2 integrity

The Monitor 2.2 reset code verifies eight 2 KiB ROM blocks using checksum
bytes at offsets `0x0003..0x000A`. The public museum image fails three
blocks before it can exercise an early-firmware BASIC path: blocks 3, 6, and 7.

| Block | Covered bytes | Stored | Computed | Result |
| ---: | --- | ---: | ---: | --- |
| `0` | `0x0004..0x07FF` | `0xD2` | `0xD2` | PASS |
| `1` | `0x0800..0x0FFF` | `0x72` | `0x72` | PASS |
| `2` | `0x1000..0x17FF` | `0x0A` | `0x0A` | PASS |
| `3` | `0x1800..0x1FFF` | `0x33` | `0xF3` | FAIL |
| `4` | `0x2000..0x27FF` | `0x6E` | `0x6E` | PASS |
| `5` | `0x2800..0x2FFF` | `0x31` | `0x31` | PASS |
| `6` | `0x3000..0x37FF` | `0x91` | `0x51` | FAIL |
| `7` | `0x3800..0x3FFF` | `0x58` | `0xB5` | FAIL |

A bounded diagnostic with checksum bytes repaired in temporary memory
passed the self-test, but then executed at `0xC482`, outside the validated
E5104 upper-ROM window (`0xD800..0xFFFF`). Widening that temporary window
advanced execution into further low-ROM dependencies without reaching a
visible prompt. This is evidence for an earlier hardware/firmware mapping,
not authority to alter the reproduced E5104 decode or publish a patched ROM.

## Boundary

- The cartridge's BASIC body is no longer an unknown implementation: it is
  byte-exactly present in Monitor 3.3 and nearly exact in Monitor 2.2.
- The exact shared span ends at cartridge offset `0x1D37`; extrapolating the
  `+0x2C8` source delta into later monitor/bootstrap code is not a defensible
  missing-page donor.
- A mirrored bootstrap/survival page fixes relocation mechanics but does not
  fix the later monitor ABI/configuration mismatch or reach `READY`.
- The remaining preservation input is therefore a complete removable-memory
  image or a documented early-board decode/loading procedure, not another
  copy of the BASIC body already recovered here.
