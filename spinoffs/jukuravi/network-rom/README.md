# Juku network-first ROM

Status: **ABI 1.0 SKELETON — DO NOT PROGRAM INTO D15/D16**

This directory is the from-scratch successor to the frozen Ekta4401 monitor
and simulator-only Ekta4402 direct-fastboot experiment. The product goal is a
network-only ROM which performs bounded POST, boots automatically at 19,200
baud, exposes common platform services from its resident 10 KiB, and gives
CP/M Plus a larger TPA. The accepted staged plan and budgets live in the
`cpm-plus-juku` repository.

The present image proves only the versioned ROM ABI and overlay crossing. Its
split files are generated to test exact EPROM geometry, but their metadata says
`not for physical programming`; they are not bench candidates yet.

## Build and test

```sh
python3 spinoffs/jukuravi/network-rom/build_network_rom.py
sync/network_first_rom_abi_check.sh
```

Committed deterministic artifacts:

- `juku-network-rom-abi1.bin`: combined 16 KiB image;
- `juku-network-rom-abi1-d15.bin`: exact low 8 KiB half;
- `juku-network-rom-abi1-d16.bin`: exact high 8 KiB half;
- `juku-network-rom-abi1.json`: hashes, sizes, ABI identity, and prohibition.

The builder stores a 196-byte gate and 44-byte mode-3 helper in the boot-only
ROM, copies them to `D620h` and `D700h`, switches overlays through a transition
stub at `D600h`, and enters the resident byte at `D800h`. The resident manifest
is fixed at `FF00h`; stable three-byte vectors begin at `FF20h`.

The current resident advertises only serial and diagnostic feature bits. It
programs the proven D57 mode-2/count-4 19,200-baud clock, supports bounded 8251
send/receive, publishes build/workspace/helper metadata, and supplies a small
diagnostic signature. Console, keyboard, NetDisk, sound, automatic boot, and
real POST vectors deliberately return unavailable until migrated and tested.

## What the regression proves

`tests/network_first_rom_abi_test.py` checks:

- deterministic combined/D15/D16 images and exact `JUKUABI` 1.0 manifest;
- byte-exact gate/helper installation and successful signature/version init;
- reset mode 0 to resident mode 1 transition;
- a nested mode 1 -> mode 3 -> mode 1 framebuffer helper call;
- the corrected overlay rule: a direct mode-1 write at `D801h` is rejected,
  while the helper reaches and reads back underlying RAM at `D800h`;
- accumulator, BC, DE, and HL preservation around the crossing test;
- low/high stack sentinels, final SP, disabled interrupts, and masked PIC;
- D57/D11 state, four transmitted `ABI1` bytes, and a queued receive byte
  consumed after manifest/video/diagnostic/transmit calls.

The write rule matters: MAME maps the high window with `.rom()` and the C model
rejects writes into an active high-ROM overlay. Therefore **all** framebuffer
updates—not only packed read/modify/write—must execute in the copied low-RAM
helper while mode 3 is selected. Resident ROM code owns text policy and font
lookup but cannot paint directly.

## Next implementation boundary

Replace the self-test resident entry with reset-safe hardware initialization,
the bounded quick POST subset, and automatic host acquisition. Reuse the V15
checked receive/ZX0 mechanisms, but remove the stock Janet discovery and key
entry. The first automatic-boot checkpoint must recover when the server is
initially absent and must reach a loaded test payload without any keyboard
input before CP/M Plus services are migrated behind the ABI.
