# BASIC Direct-Entry Probe

Status: **BASIC DIRECT RESET PATH REJECTED**

This diagnostic runs the public BASIC images as if they were the reset ROM.
It is intentionally a negative proof: the expected usable path is a monitor
or removable-memory entry point, not a standalone low-ROM reset image.

Command shape:

```sh
sync/basic_entry_probe.py
```

| Image | Size | SHA256 | First bytes | Entry JMP | First VRAM write | Stop PC | Mode | Visible pixels | VRAM SHA256 |
| --- | ---: | --- | --- | --- | --- | --- | ---: | ---: | --- |
| jbasic11.bin | 8192 | `ff86e17c7ce6de177e18bc0468d23cee7ed2ecd6e8adc56950138cdf6ee5ba60` | `C3 07 01 BA DC 00 20 C3` | 0x0107 | 0xFFFE @ 125 cyc | 0x0038 | 0 | 19280 | `de20a00a49ba291fb092adaf0e076d11ca00131d314b40374683de16a0e1ef2a` |
| legacy BAS0-3.HEX | 8192 | `9fc9f2216f6a95c92bdac14991145b960b41c8318d086b1d80fdf470a806c9b4` | `C3 07 01 BA DC 00 20 C3` | 0x0107 | 0xFFFE @ 125 cyc | 0x0038 | 0 | 19280 | `de20a00a49ba291fb092adaf0e076d11ca00131d314b40374683de16a0e1ef2a` |

## Interpretation

- Both images begin with the same absolute `JMP 0x0107`, but direct reset execution
  does not produce a BASIC banner or `READY` prompt.
- Both direct-reset runs stop at `PC=0x0038` after the first video write to
  `0xFFFE`, with the same framebuffer hash.
- Treat these images as cartridge/removable-memory BASIC payloads. The remaining
  WS-B3 work is finding the correct monitor/removable-memory pairing and then
  adding a positive BASIC prompt oracle.
