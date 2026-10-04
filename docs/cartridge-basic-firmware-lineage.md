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
2.2 differs at only one byte. The match establishes shared BASIC bytes
over the compared span; it does not supply the absent source page.

## Relocation range contract

If the cartridge is mapped at `0x0100`, its 22-byte bootstrap at
file offset `0x1F00` lies at
`0x2000`. Its literal 8080 operands load
`HL=0x0200`, `DE=0x0100`, and
`BC=0x2000`; the guarded loop copies one byte, increments
HL/DE, decrements BC, and repeats until BC is zero.

| Quantity | Derived range/value |
| --- | --- |
| Copy source | `0x0200..0x21FF` |
| Copy destination | `0x0100..0x20FF` |
| Public image mapped span | `0x0100..0x20FF` (`8192` bytes) |
| Missing source span | `0x2100..0x21FF` (`256` bytes, exactly one page) |
| Missing page destination | `0x2000..0x20FF` |

The copy count is therefore direct firmware evidence for a 256-byte
shortfall; it is not inferred from a failed runtime experiment.

## Cartridge suffix

| Span | Bytes | Non-zero bytes | SHA256 | Interpretation |
| --- | ---: | ---: | --- | --- |
| `0x1D38..0x1EFF` | `456` | `0` | `b960fb5cb94682dfc4a873035d65f8befdcb9bed0e7db0feb905f0dcf437b38c` | zero padding |
| `0x1F00..0x1FFF` | `256` | `18` | `e625e901f06b6eca4a5c9b8dca79b889fd90cf2db1f7771f67e9284365a70a9b` | relocation bootstrap page |

The required loop-survival sequence occurs at bootstrap offset
`0x09`. Its presence identifies relocation code, not a
validated donor for the absent source page.

## Monitor 2.2 integrity

The public Monitor 2.2 image has failing 2 KiB checksum blocks 3, 6, and 7.
The [Monitor 2.2 audit](jmon22-reconstruction.md#checksum-boundary)
records the full checksum table and proves that the
block-3 failure is the sole BASIC-body mismatch: replacing `0x9A` at
`0x1EFC` with the `0xDA` found in both Monitor 3.3 and this cartridge
exactly closes the stored checksum. It leaves the original dump unchanged
because blocks 6 and 7 remain unresolved.

This generator compares bytes and checksum constraints; it does not execute
a cartridge or patched monitor. The current acceptance and recovery inputs
are summarized in [the cartridge boundary](cartridge-basic-boundary.md).

## Boundary

- The exact shared span ends at cartridge offset `0x1D37`; extrapolating the
  `+0x2C8` source delta into later monitor/bootstrap code is not a defensible
  missing-page donor.
- A working loading/decode contract remains unverified; byte lineage and
  relocation operands alone do not establish BASIC startup.
