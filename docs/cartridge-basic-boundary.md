# Monitor cartridge BASIC boundary

Status: **ARTIFACT OR DOCUMENTED PROCEDURE REQUIRED**.

The public cartridge's BASIC body is recovered, but its loading/configuration
contract remains unresolved. No reconstructed cartridge is exported. This
optional preservation work does not block main-board fabrication.

## Artifact and decode boundary

`roms/jbasic11.bin` is 8,192 bytes with SHA256
`ff86e17c7ce6de177e18bc0468d23cee7ed2ecd6e8adc56950138cdf6ee5ba60`.

- [Cartridge-window guard](basic-cart-readiness.md): cosim's explicit
  MAME-compatible option exposes the image at `0x4000`. The validated physical
  D8 `.039` row is `0xFF`, leaving D22 unselected in that state. Emulated
  visibility does not establish the reproduced board's cartridge decode.
- [Firmware-lineage audit](cartridge-basic-firmware-lineage.md): 7,224 body
  bytes are identical to Monitor 3.3; Monitor 2.2 differs at one byte. The
  bootstrap copies source `0x0200..0x21FF` to runtime `0x0100..0x20FF`, but
  the public image mapped at `0x0100` ends at source address `0x20FF`.
  These are mapped addresses, not offsets in the 8,192-byte file. The missing
  256-byte source page is `0x2100..0x21FF` (would-be file offsets
  `0x2000..0x20FF`). The shared body does not extend into that page.
- [Monitor 2.2 audit](jmon22-reconstruction.md): one body byte is recoverable,
  but ROM blocks 6 and 7 remain unresolved. It is not a validated substitute
  for the E5104 firmware/decode pairing.
- [Factory documents 003 and 014](../ref/baltijets-tech-docs/README.md)
  describe BASIC launch with command `A` from the removable 32 KiB memory
  expander. The tested public monitor/cartridge pairings did not reproduce
  that acceptance path.

Bounded reconstruction experiments did not reach a BASIC banner or `READY`.
Filling the absent page or repairing relocation mechanics alone has not
established a working cartridge. A new artifact or documented configuration
is needed to justify further reconstruction.

## Independent disk BASIC path

Disk-side `JBASIC.COM` is a different artifact. It reaches `READY` in the
[C oracle](ekdos-jbasic-command-probe.md). The
[recorded uninterrupted HDL run](juku-top-jbasic-verilator-probe.md) also
reached `READY`; current Verilator reruns have a
[build compatibility limitation](../sync/README.md#simulator-compatibility).
Neither disk result completes the cartridge boundary.

## Useful recovery input

Resume the cartridge investigation when one of these becomes available:

- a complete cartridge image, programming file, or source;
- a factory memory-expander image; or
- a hardware-confirmed loading procedure with monitor, board and decode details.

Compare a new artifact's hash and byte layout against the lineage audit before
starting further reconstruction experiments.
