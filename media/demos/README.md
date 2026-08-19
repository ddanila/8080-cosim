# Network boot demonstrations

These GIFs are deterministic simulator demonstrations, not recordings of a
physical display. Each combines framebuffer changes with timestamped host
output on a single monotonic timeline. `JUKU_REALTIME_HZ=1700000` prevents the
emulator from running ahead of a real Juku, and the Janet server retains the
scenario's 9,600- or 19,200-baud serial timing.

| File | Scenario |
| --- | --- |
| `stock-rom-cpm22.gif` | Stock ROM, Janet bootstrap, CP/Mish CP/M 2.2 |
| `stock-rom-fast-cpm31.gif` | Stock ROM, compact 19,200-baud loader, CP/M Plus 3.1 |
| `netboot-rom-cpm31.gif` | C6 network ROM, CP/M Plus 3.1, and selected tools |

The generator expects sibling `cpmish` and `cpm-plus-juku` checkouts under the
same parent directory. Build their referenced images first, install Pillow,
then run one scenario or all three:

```sh
python3 tools/netboot_demo_gifs.py --scenario cpm22
python3 tools/netboot_demo_gifs.py --scenario cpm31_stock
python3 tools/netboot_demo_gifs.py --scenario cpm31_netrom
python3 tools/netboot_demo_gifs.py --scenario all
```

`gifsicle -O3 --colors 256 input.gif -o output.gif` provides an optional
lossless size optimization after capture.
