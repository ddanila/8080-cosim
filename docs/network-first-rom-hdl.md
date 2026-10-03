# Network-first ROM structural HDL checks

The focused gate checks firmware through structural `juku_top` and its
`vm80a` CPU. Run the full local profile from the repository root:

```sh
sync/network_first_rom_hdl_check.sh
```

## Full-profile coverage

| Fixture | Boundary |
| --- | --- |
| Committed C4 / ABI 1.0 ROM | Reset, bounded POST, memory mode 1, masked interrupts, D57 mode-2/count-4 clock, D11 `4Eh`/`35h`, and first `C4h` target-ready byte |
| Test-only C4 ABI dispatch | Copied mode-3 video helper, matrix-key input, public vectors and serial exchange through the modeled D57/D11/D104 path |
| Test-only C9/C10/C11/C12 ABI dispatch | Each release's resident ABI behavior, with the POF release option for C10 and successors |
| Video POF fixture | The C9 blank versus C10 visible boundary |
| Test-only C4 NetDisk caller | Exact v3 request, CRC-checked reply and all 128 returned `5Ah` bytes copied to DMA memory |

The committed C4 artifact is
`spinoffs/jukuravi/network-rom/juku-network-rom-abi1.bin`, SHA-256
`931218a654412e2f9b0776a81bd5369f0c22c1da45cada220a2b96bbe70854c0`.
The gate first checks artifact freshness, then builds temporary self-test
variants. Those variants use test dispatch to exercise resident code; they
are not complete production reset-to-CP/M runs for every release.

## Bounded CI profile

```sh
sync/network_first_rom_hdl_check.sh --ci
```

This profile builds the fixtures, elaborates both structural ROM benches and
executes the video POF guard. It skips the firmware simulations listed above.
Its PASS therefore does not establish the full local profile's runtime result.

## Limits and related evidence

The C model remains the practical full-system oracle for bootstrap reception,
decompression, CP/M commands, cursor pixels, recovery, host replacement and
longer NetDisk workloads. Use [the network-ROM guide](../spinoffs/jukuravi/network-rom/README.md)
for the corresponding gates and artifact identities.

Structural HDL agreement does not qualify analog levels, fitted silicon,
loading or the physical cable. Physical results remain board- and
artifact-specific; [C12 qualification](c12-runtime-console.md) records the
focused corrected-pair CS00000 results and remaining limits.
