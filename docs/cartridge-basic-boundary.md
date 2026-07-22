# Monitor cartridge BASIC boundary

Status: **ARTIFACT OR DOCUMENTED PROCEDURE REQUIRED**.

This is the durable result of the completed Monitor/cartridge BASIC
experiments. Detailed traces and rejected patch attempts remain in Git history;
they are not active project reports.

## What is proved

- `sync/basic_cart_check.sh` proves that the MAME-compatible cosim option exposes
  `roms/jbasic11.bin` at `0x4000`, while the validated physical D8 `.039` row is
  `0xFF` and does not select D22. The missing configuration/decode distinction
  is part of this boundary, not silently replaced by the old reconstruction.
- The public cartridge is 8,192 bytes with SHA256
  `ff86e17c7ce6de177e18bc0468d23cee7ed2ecd6e8adc56950138cdf6ee5ba60`.
- Monitor 3.3 reads and copies the cartridge body. The known body at runtime
  `0x0200..0x1FFF` matches; the low entry/workspace differs at 14 bytes.
- The cartridge bootstrap copies source `0x0200..0x21FF` to runtime
  `0x0100..0x20FF`, but the public 8 KiB image supplies data only through
  source `0x20FF`. The missing source page is exactly `0x2100..0x21FF`, mapped
  to runtime `0x2000..0x20FF`. The generated lineage audit now derives these
  ranges directly from the guarded `LXI H,0200` / `LXI D,0100` /
  `LXI B,2000` bootstrap operands rather than retaining arithmetic only in
  prose.
- The self-overwriting relocation loop requires the missing page to preserve
  its tail at source `0x2109..0x2115`:
  `7e 12 23 13 0b 78 b1 c2 09 20 c3 00 01`.
- `scripts/report_cartridge_basic_firmware_lineage.py` proves that cartridge
  offsets `0x0100..0x1D37` are byte-identical to Monitor 3.3 ROM offsets
  `0x03C8..0x1FFF` (7,224 bytes, constant `+0x2C8` source delta). Monitor 2.2
  differs in that same span at only one byte. The meaningful BASIC body is
  therefore already recovered from two independent firmware shapes.
- The remaining known cartridge suffix is 456 zero bytes followed by the
  relocation-bootstrap page. The exact Monitor/body correspondence stops
  before the missing page, so extending the `+0x2C8` delta into unrelated
  monitor/bootstrap code would not be a source-proven reconstruction.
- No current ROM, extracted software file, or vendored disk provides a
  defensible page-shaped donor.
- The [public Juku software catalog](https://j3k.infoaed.ee/tarkvara-kataloog/)
  was rechecked on 2026-07-22. It still lists `JBASIC11.BIN` as `8K` in
  `JUKUROMS` and exposes no larger cartridge BASIC artifact, so it ends at the
  same one-page boundary.

## Rejected shortcuts

Bounded experiments did not reach a BASIC banner or `READY` after trying fill
bytes, appending/mirroring the final page, changing the relocation count,
jumping directly into the copied body, or using the semantically aligned final
page from the live disk BASIC while preserving the relocation loop. No patched
cartridge is exported.

The public Monitor 2.2 museum image contains the same onboard BASIC lineage but
fails its own block checksums in blocks 3, 6, and 7. A temporary checksum-only
diagnostic then reaches code outside the validated E5104 upper-ROM window,
which indicates an earlier board/decode ABI rather than a safe replacement for
the reproduced hardware mapping.

Baltijets document 003 describes command `A` for a removable 32 KiB memory
expander. Tested public monitor/cartridge pairings did not reproduce that
acceptance path, so the correct pairing, decode state, media shape, or procedure
is still missing.

## What is not blocked

Disk-side `JBASIC.COM` is a different artifact and already reaches a visible
`READY` prompt in the C oracle and uninterrupted structural HDL. This
cartridge boundary is therefore optional preservation/compatibility work, not a
main-board fabrication blocker.

## Next useful input

Resume this branch only when one of these appears:

- a complete/larger cartridge image or programming file;
- source code or a factory memory-expander image; or
- a hardware-confirmed Monitor 3.3 loading procedure with board/configuration
  details.

Compare any new artifact by hash and byte layout before rerunning or designing
new reconstruction experiments.
