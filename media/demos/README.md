# Network boot demonstrations

These GIFs are deterministic simulator demonstrations, not recordings of a
physical display. Each combines framebuffer changes with timestamped host
output on a single monotonic timeline. `JUKU_REALTIME_HZ=1700000` prevents the
emulator from running ahead of a real Juku. The native C `jukuhost` retains
the scenario's 9,600- or 19,200-baud serial timing and writes a readable log
plus a raw byte capture beside the generated frames.

| File | Scenario |
| --- | --- |
| `stock-rom-cpm22.gif` | Stock ROM, Janet bootstrap, CP/Mish CP/M 2.2 |
| `stock-rom-fast-cpm31.gif` | Frozen historical V15 demonstration; retained as evidence but no longer generated or served by a supported host |
| `netboot-rom-cpm31.gif` | Current C8 network ROM, Fastboot V16, CP/M Plus 3.1, and selected tools |

The generator expects sibling `cpmish` and `cpm-plus-juku` checkouts under the
same parent directory. Build `jukuhost` and the referenced system images first,
install Pillow, then run one scenario or both:

```sh
python3 tools/netboot_demo_gifs.py --scenario cpm22
python3 tools/netboot_demo_gifs.py --scenario cpm31_netrom
python3 tools/netboot_demo_gifs.py --scenario all
```

Normal generation keeps the authentic 1.7 MHz wall-clock timeline. For a
faster desk validation of the same protocol and rendering path, set
`JUKU_DEMO_REALTIME_HZ=20000000`; generated presentation GIFs should continue
to use the default.

The generator invokes only `build/jukuhost` for production protocol serving.
Python remains the simulator/capture renderer and is not a Janet, Fastboot,
NetDisk, or N4 host in this workflow. Each run leaves
`SCENARIO.jukuhost.log` and `SCENARIO.jukuhost.cap` in the output directory.
The old stock-ROM fast CP/M Plus demonstration depended on the retired V15
loader. Its GIF is preserved as historical evidence, while current generation
covers the compatible stock Janet path and the admitted C8/V16 path.

`gifsicle -O3 --colors 256 input.gif -o output.gif` provides an optional
lossless size optimization after capture.
