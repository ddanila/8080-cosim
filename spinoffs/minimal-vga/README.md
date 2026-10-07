# VJUGA minimal-VGA experiment

Status: **EXPERIMENTAL, WITH TWO PHYSICAL TRACKS**.

VJUGA explores a smaller +5 V, Z80-based board with socketed ROM, one 64 KiB
4164-style DRAM bank, keyboard I/O, and a VGA-oriented display path. It is an
independent experiment, not the main Juku replica and not a released hardware
product. The monolithic Rev A board remains on design hold. For modular Rev B,
the active order target is a complete five-board first article with VGA and TTL
serial; it remains on order hold while `docs/rev-b-five-board-order-plan.md` is
executed.

## Rev B modular status

[Rev B status](docs/rev-b-status.md) summarizes the five-card system and its
completed desk gates. The [five-board order plan](docs/rev-b-five-board-order-plan.md)
controls release; physical first-article acceptance remains pending. Use the
[current bench template](docs/rev-b-b1-bench-log.md) after the authorized order
arrives. Use only the exact five-archive candidate identified by the release
record; superseded packages must not be uploaded.

## Rev A monolithic status

### What works

- `sim/boot_check.sh` runs the patched Juku ROM on T80 in Z80 mode and
  compares the framebuffer with cosim after 6,000 video writes. This checks a
  bounded boot workload, not a complete banner, prompt or physical display.
- `sim/vjuga_boot_check.sh` runs the tv80 twin with the shared РУ5 DRAM,
  D6 decode-PROM and D8 pager models from `hdl/devices.v`, using the validated
  PROM tables. Both Mode B (D6 decode) and Mode A (U5's coarse A15/A14 decode)
  match the same bounded framebuffer oracle. This exercises the modeled
  memory path; it does not qualify socketed chips or prove detection of every
  chip fault. D8's output is unused and is not checked by this guard. Mode B
  uses D6 D0/pin12 as active-low `ROM_N`.
- The pinned T80 core also executes a built-in synthetic ROM (smoke test).
- The synthetic test exercises CPU ROM/RAM/I/O cycles, a bit-sliced DRAM
  model, independent refresh, video arbitration, keyboard-style input, and one
  VGA timing frame.
- An eight-instance logical HDL/KiCad model passes structural comparison.
- Nine structural HDL/board-JSON LVS slices pass with mutation controls,
  covering power/clock/reset, decode, CPU/ROM, DRAM bank and muxes, refresh,
  spare socket, timing and PPI. Whole-board coverage remains incomplete;
  these comparisons do not establish routed-copper continuity. See
  [LVS coverage](docs/rev-a-lvs-coverage.md) for exact counts and boundaries.
- U23 is retained only as an empty DNP spare socket. Its eight outputs have no
  consumers and the verified video timing/request handoff is U40/U41; generated
  assembly artifacts therefore omit U23 from owner IC insertion while still
  mounting its routed socket. Stage 7 LVS guards that exact socket topology.
- The Rev A physical source has 119 refs and 133 modeled nets, and now sockets
  the real Juku decode PROMs (U3 К556РТ4, U4 К155РЕ3) with a Mode-A/Mode-B
  jumper plus the Phase 4 observability headers (J96 clock-control, J97 high
  address + write strobe, J98 control bus); `check_rev_a_physical` enforces
  decode-socket and observability contracts that match the verified twin.
- **The framebuffer-readback boot oracle is built and validated.**
  `sim/vjuga_readback_check.sh` boots the twin with `+capture`, reassembles the
  write stream (`tools/vjuga_fb_readback/reassemble.py`), and confirms it equals
  both the twin's own dump and cosim's `vram.bin` at the selected write cutoff
  (default 6000). This validates bounded replay, not completion of the banner
  or physical capture reliability. Bench comparisons require matching ROM,
  cutoff and initial state; see [the procedure](docs/phase4-bench-bringup.md). A twin
  reference trace (`tools/vjuga_single_step/`) backs the UNO single-step rig.
- The committed four-layer routed PCB includes the Phase 3 decode sockets and
  observability headers and passes the repository's KiCad DRC and
  unconnected-item checks. Independent schematic/copper and power-return review
  still holds release.
- Any Rev A fabrication package predates both the U20/U21
  address-mux enable correction and the U22 refresh-counter cascade correction,
  and is **stale; do not upload or order it**. Do not confuse it with the separately
  validated Rev B packages under `fab/minimal-vga/revb/package/`. The Rev A upload ZIP is absent from the current workspace;
  [manufacturing readiness](docs/rev-a-manufacturing-readiness.md) owns its release gates.
  A fresh guarded stable-KiCad export and checksum are required.

### CPU and ROM

The Z80 supports the experiment's single +5 V supply. The adapted ROM replaces
three 8080 undocumented NOP opcodes and updates one checksum byte. The boot
gate compares original and patched 8080 framebuffers at its selected write
cutoff, then compares the T80 Z80 result; it does not prove every firmware
service equivalent. See [ROM images](roms/README.md) for the patches, hashes
and reproduction commands. T80 runs in Z80 mode (`Mode => 0`).

### What does not work yet

- The current Rev A copper includes the Phase 3 decode sockets and observability
  headers and passes zero-violation/zero-unconnected KiCad DRC. Its two inner
  layers are reserved for filled GND/VCC planes; independent review remains.
- The U5 decode is simulated in both jumper modes, and U24's DRAM
  timing/wait-state reference passes the slower vendored MK4564-12 limits at
  4 MHz. Neither GAL has been compiled/programmed or validated in hardware.
- The physical U20/U21 mux inputs have CPU A0–A7 and refresh-row outputs,
  without CPU-column or video-address paths. The runnable DRAM scaffold does
  not close that hardware gap; see [the chip map](docs/rev-a-chip-map.md#dram-and-arbitration).
- The VGA test proves timing activity, not a Juku banner or prompt sourced from
  shared DRAM.
- No independent end-to-end schematic/design review has released the copper.

Therefore the fabrication outputs are useful engineering artifacts, but the
board is **not authorized for vendor upload, order, or assembly**.

### Current scope

Included in the experiment:

- socketed DIP Z80, ROM, 8255, programmable logic, and eight 4164-compatible
  DRAM devices;
- +5 V input protection, clock/reset, debug headers, and diagnostics;
- keyboard matrix interface;
- shared CPU/refresh/video DRAM scaffold;
- VGA timing/debug header and pixel-serializer path.

Excluded from Rev A: FDC, external bus, tape/serial/network/mouse interfaces,
historical placement, and the original composite/RF chain.

## Evidence map

- `docs/workbench-plan.md`: the bench-fixture direction (test the real Juku
  РУ5/РТ4/РЕ3 parts) and the phased build plan.
- `docs/phase4-bench-bringup.md`: the detailed Phase 4 plan — pre-fab
  observability design-ins, analyzer channel maps, the framebuffer-readback
  boot oracle, the UNO single-step rig, and the assembly/chip-test ladder.
- `hdl/README.md`: exactly what the synthetic simulation proves.
- `docs/rev-a-chip-map.md`: current physical decomposition.
- `docs/rev-a-gal-equations.md`: unvalidated programmable-logic draft.
- `docs/rev-a-placement-rules.md`: placement policy.
- `docs/rev-a-power-budget.md`: conservative planning estimate.
- `docs/rev-a-sourcing-plan.md`: future sourcing/assembly policy; stock must be
  rechecked at order time.
- `docs/rev-a-drc-readiness.md`: current stable-KiCad full-DRC result
  bound to the exact source-board SHA; the former fabrication package is
  explicitly stale after the mux-enable and refresh-counter corrections.
- `docs/rev-a-lvs-coverage.md`: exact staged physical-LVS scope, negative
  control, and the groups still outside the whole-board comparison.
- `docs/rev-a-usb-c-candidate.md`: checksum- and geometry-guarded exact HRO
  TYPE-C-31-M-17/C283540 J3 candidate; order-time orientation/stock remains.
- `docs/rev-a-ptc-candidate.md`: checksum-, electrical-, topology-, and
  static-fit-guarded Bourns MF-RG300-0-14/C3761779 F1 candidate; thermal,
  stock, and first-article checks remain.
- `docs/rev-a-tvs-candidate.md`: checksum-, polarity-, topology-, geometry-,
  and routed-clearance-guarded Littelfuse P4KE6.8A-B/C1666224 D1 candidate;
  surge, stock, and first-article checks remain.
- `kicad/fab-notes.md`: routed/package facts and release blockers.
- `docs/rev-a-manufacturing-readiness.md`: top-level package/design status.
- `external/`: pinned-core and third-party design notes.

Generated reports under `fab/minimal-vga/` are ignored build artifacts. Their
individual `READY` labels mean the named mechanical/package check passed; they
do not override the top-level design hold.

## Checks

Run the current simulation and structural/physical checks:

```sh
spinoffs/minimal-vga/sim/check.sh
```

Run only the logical schematic/HDL comparison:

```sh
spinoffs/minimal-vga/sync/check.sh
```

Run the completed physical-board LVS stages:

```sh
spinoffs/minimal-vga/sync/rev_a_power_clock_reset_lvs.sh
spinoffs/minimal-vga/sync/rev_a_decode_lvs.sh
spinoffs/minimal-vga/sync/rev_a_cpu_rom_lvs.sh
spinoffs/minimal-vga/sync/rev_a_dram_bank_lvs.sh
spinoffs/minimal-vga/sync/rev_a_dram_mux_lvs.sh
spinoffs/minimal-vga/sync/rev_a_refresh_counter_lvs.sh
spinoffs/minimal-vga/sync/rev_a_spare_socket_lvs.sh
spinoffs/minimal-vga/sync/rev_a_dram_timing_lvs.sh
spinoffs/minimal-vga/sync/rev_a_ppi_lvs.sh
```

Regenerate fabrication review artifacts only after accepting that they remain
non-release outputs:

```sh
spinoffs/minimal-vga/kicad/export_fab.sh
```

## Rev A release gate

This gate applies to the monolithic Rev A bench fixture. The modular Rev B
order criteria are in the [five-board order plan](docs/rev-b-five-board-order-plan.md).

Established simulation evidence:

- `sim/boot_check.sh` matches the cosim framebuffer at 6000 video writes.
- `sim/vjuga_boot_check.sh` matches both jumper modes through the Rev A top
  using the РУ5 DRAM and РТ4 decode models; the instantiated РЕ3 output is
  unused and unchecked.
- Decode and U24 DRAM-timing equations are simulated; see
  `sim/u24_dram_timing_check.sh`.

VGA output is waived for Rev A's bench-fixture scope: the guarded framebuffer
capture is its bounded boot oracle for the РУ5/РТ4 memory path. РЕ3 testing
requires a separate output-table capture from the debug header, as described
in the [bench procedure](docs/phase4-bench-bringup.md). This waiver does not
apply to the five-board Rev B order target.

Before Rev A can become an order candidate:

1. Complete the physical DRAM addressing and resolve its scanout scope under
   [the manufacturing requirements](docs/rev-a-manufacturing-readiness.md#remaining-release-requirements).
2. Compile, program and review the equations on the exact chosen GAL22V10
   devices.
3. Validate DRAM, reset, clock, power, connector and socket pinouts against
   selected parts.
4. Obtain an independent schematic, copper, Gerber, drill and power-return
   review, plus full-board LVS or an explicit owner waiver naming that
   independent review as compensating evidence.
5. Regenerate all package artifacts after the design is frozen.

Until then, work on VJUGA must not distract from the main replica's P0 closure
items in the repository-root `PLAN.md`.
