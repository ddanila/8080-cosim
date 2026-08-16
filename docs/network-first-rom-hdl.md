# Network-first ROM structural HDL qualification

Status: **PASS for reset/POST, the resident ABI, and one NetDisk-v3 read**.

Run the complete focused gate with:

```sh
sync/network_first_rom_hdl_check.sh
```

The first fixture boots the exact `network-first-abi1-cs00015-c2` production
image in `juku_top` with the structural `vm80a` CPU. Its combined SHA-256 is
`928bdbbd8845f6d3b3f73ead8070a3a55a55bc4b284a8a4da8a0eed9e1c6671a`.
It proves reset, bounded POST, mode-1 selection, masked interrupts, the
D57 mode-2/count-4 clock, D11 `4Eh`/`35h` setup, and the first `C4h`
target-ready byte. A passing run ends with output equivalent to:

```text
NETWORK-FIRST-ROM-HDL: PASS post=00 ready=C4 mode=1 pit=mode2/count4 usart=4E/35 io=45 memw=1406 pc=0184
```

The second fixture uses test-only reset dispatch around the same resident
bytes and public vectors. It proves the copied mode-3 helper, 9,619 video-RAM
writes, shifted matrix-key input, ABI version 1, and the resident serial path
through the structural D57, D11, and D104 models. It transmits `ABI1`, consumes
the test receive byte, and emits host marker `C3h`.

The third run enables a test-only NetDisk caller. The unchanged resident C2
transaction code emits the exact v3 request, validates a CRC-protected reply,
and copies all 128 returned `5Ah` bytes to DMA memory. Its success line includes
`netdisk_dma=128`.

These fixtures deliberately stop at a small structural boundary. The C model
remains the practical full-system oracle for the V15 receive/decompression
stream, the actual CP/M Plus image and command transcript, exact cursor pixels,
fault recovery, server replacement, and long NetDisk soak. Physical CS00015
qualification remains mandatory: HDL agreement cannot validate analogue
levels, fitted silicon, board loading, or the actual serial cable.
