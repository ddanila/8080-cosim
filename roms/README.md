# Juku ES101 ROM set (vendored)

Firmware ROM images for the Soviet/Estonian **Juku E5101** computer, vendored here so
the emulator (`cosim/`) and the HDL sims (`hdl/sim/`) can boot the real firmware and be
cross-validated in CI without an external ROM path.

## Provenance
Most boot ROMs are the canonical, preservation-grade Juku ROMs whose SHA-1
matches the hashes documented in the MAME `juku` driver (`ref/mame_juku.cpp`).
Additional public monitor images from the museum bundle are listed separately
in the same table:

| file | size | SHA-1 | role |
|---|---|---|---|
| `jmon33.bin`  | 16K | `76407d99bf83035ef526d980c9468cb04972608c` | **Juku Monitor v3.3** — default BIOS (MAME `ROM_BIOS(0)`), interrupt-driven |
| `ekta24.bin`  | 16K | `a7185d747c94cd519868692ed3d10fade90dd6d5` | EktaSoft BIOS '88 |
| `ekta31.bin`  | 16K | `73d62c032be1de06c0dd5618f4abccd4d0f3a329` | EktaSoft BIOS |
| `ekta32.bin`  | 16K | `57311d53f6fe1e87e0755990f400253caccd4795` | EktaSoft BIOS |
| `ekta35.bin`  | 16K | `7aa03497d88cfab9315aa3987765bc06ecb70013` | EktaSoft BIOS |
| `ekta37.bin`  | 16K | `29366d74c0e27129f2484a973f7a6de659b90cf4` | EktaSoft BIOS '88 (the **boot we validate** — polled, draws a banner) |
| `ekta43.bin`  | 16K | `a7419bfd8249871cc7dbf5c6ea85022d6963fc9a` | EktaSoft BIOS (stale block-1 checksum) |
| `jmon22.bin`  | 16K | `dee46441f6beeece3e2dfe897c8b1547939c7b1f` | Juku Monitor v2.2 from the public museum ROM bundle |
| `jbasic11.bin`| 8K  | `27e40395e8b49e2f9febf2b23773fbfe251befcf` | Juku BASIC 1.1 |

## Licensing / status
The Juku is **abandonware** (a 1980s Soviet-Estonian machine; the original manufacturer
no longer exists). These images are vendored for **preservation and research** — the same
basis on which MAME documents them. The repo owner is **contacting the rights holders**;
if anyone with a claim asks, the images will be **removed on request**. No warranty.
