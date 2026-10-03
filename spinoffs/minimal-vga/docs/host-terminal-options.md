# VJUGA host I/O and display

## Current design

The [Rev B five-board design](rev-b-five-board-order-plan.md) includes CPU,
Memory, I/O, Backplane and Video cards. Display output comes from the autonomous
VGA card, with local SRAM for the 9640-byte, 40×241 bitmap at `0xD800`.
The I/O card provides the keyboard interface. See the
[Video adoption note](rev-b-video-adoption.md) for the scanout design and provenance.
Physical board acceptance remains pending; desk verification does not establish
adapter interoperability or working assembled hardware.

## Connecting a host

The I/O card's sole 8251 reaches the protected `J_TTL` connector on the backplane.
Use the [serial-console contract](rev-b-serial-console.md) for pin directions,
jumper settings, voltage limits and acceptance commands. Connect adapter RX,
TX and ground; leave adapter power disconnected. This is TTL serial, not RS-232.

The direct console tests use 19,200 baud, 8N1, with a selectable 9,600-baud
recovery setting. The normal clock path is firmware-programmed through the PIT;
framing and host protocol depend on the selected ROM and service. A serial
terminal alone does not provide JukuNet disk service. Use the matching ROM and
host described in the [ROM guide](../roms/README.md).

## Scope of host display alternatives

An external host that reads video RAM through Z80 bus arbitration and injects
keyboard input is not part of the current Rev B design or its acceptance gates.
There is no qualified screen-scraping bridge, throughput measurement or host-board
selection here. Such a bridge would need its own bus, electrical and firmware
contract before it could replace the native display or keyboard path.
