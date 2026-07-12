# HDL structural model

`juku_top.v` is the runnable structural model of the Juku processor module and
the HDL side of the LVS comparison. Instances represent board devices; wires
represent modeled board nets. `devices.v` contains the behavioral models used
for simulation.

## Files

- `juku_top.v` — structural top and explicitly named simulation adjuncts.
- `devices.v` — CPU wrapper, memories, decode logic, peripheral behavior, and
  bounded timing/analog substitutes.
- `vendor/vm80a.v` — vendored die-level 8080/КР580ВМ80А-compatible core; see
  `vendor/README.md` and `vendor/license.md`.
- `sim/` — unit, boot, lockstep, video, FDC, and checkpoint testbenches.
- `juku_top.json` — generated Yosys netlist; regenerate with `sync/check.sh`.

## What currently runs

The structural top boots the real ekta37 ROM, matches the C oracle’s
framebuffer, handles keyboard and frame-interrupt paths, reads vendored Juku
disk media through the bounded FDC model, reaches EKDOS `A>`, and reaches disk
BASIC `READY`. Monitor 3.3 reset/cursor and selected command paths also have
HDL oracles.

The CPU, memory/ROM paging, populated bit-sliced DRAM bank, PPI/PIT/PIC/USART
behavior, FDC boot subset, serializer, and raster helper are functional models.
They are not generic cycle-accurate replacements for every original IC mode.

## Honest boundaries

- D2's physical inputs and D0/WAIT handoff are modeled, but the `.037` truth
  table is unknown and the runnable PROM remains a constrained placeholder.
- D94's first three outputs are wired to the accepted local FDC controls; its
  enable, remaining outputs, and `.092` contents are unknown.
- Nine official FDC-support devices have package pins and power endpoints in
  the board model but no functional signal closure or HDL instances;
  `docs/unmodeled-footprint-inventory.md` owns that boundary.
- 90 modeled nets still carry source-risk annotations requiring
  physical evidence or an explicit redesign before fabrication release.
- The runnable video path reads DRAM through a simulation-only second port.
  Physical D41/D42/D43 and mux/decode instances exist, but faithful shared-DRAM
  slot timing still needs D41 and adjacent one-shot/mux/counter evidence;
  D94's proved outputs belong to FDC control.
- Several device models implement only the modes exercised by the guarded Juku
  paths.
- Simulation-only CPU sampling, keyboard stimulus, framebuffer access, and
  interrupt helpers are excluded from LVS by an explicit allowlist in
  `sync/lvs.py`.

## Verification

```sh
sync/check.sh       # modeled KiCad/HDL connectivity
sync/boot_check.sh  # C and HDL boot/framebuffer regression
sync/cosim_check.sh # value-level structural/oracle comparison
```

See `../sync/README.md` for subsystem and deep checks. A green LVS result proves
only mapped connectivity; it does not cover omitted pins or validate device
behavior.
