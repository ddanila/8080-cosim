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
  to runtime `0x2000..0x20FF`.
- The self-overwriting relocation loop requires the missing page to preserve
  its tail at source `0x2109..0x2115`:
  `7e 12 23 13 0b 78 b1 c2 09 20 c3 00 01`.
- No current ROM, extracted software file, or vendored disk provides a
  defensible page-shaped donor.

## Rejected shortcuts

Bounded experiments did not reach a BASIC banner or `READY` after trying fill
bytes, appending/mirroring the final page, changing the relocation count, or
jumping directly into the copied body. No patched cartridge is exported.

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
