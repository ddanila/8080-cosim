# VJUGA rev B execution guide

The [five-board order plan](rev-b-five-board-order-plan.md) controls the current
CPU/Memory/I/O/Backplane/Video design and release dependencies. The
[status page](rev-b-status.md) summarizes implementation and remaining gates.
Completed task histories are available in Git.

## Working rules

- Preserve the [bus contract](rev-b-bus-contract.md), ROM/I/O maps and explicit
  hardware boundaries. Resolve a conflicting observation against its source;
  obtain an owner decision when it changes the agreed machine or order scope.
- Keep VJUGA behavior separate from the faithful root Juku model. Use the shared
  machine-facts guard to detect accidental divergence in common constants.
- Update generators and their outputs together. Check pin-level connectivity,
  routed copper, programmable logic and simulation for changes affecting them.
- Commit and push coherent progress directly on `master` in the user's fork.
  Fetch and reconcile remote changes before pushing.
- Keep acquisition, qualification and release evidence tied to exact artifacts.
  A prepared template or technical PASS does not authorize upload or payment.

## Verification commands

Run from the repository root. The full suite is the entry point:

```sh
spinoffs/minimal-vga/sim/revb_tier_suite.sh
```

It covers shared facts, card completeness, GAL/ROM rebuilds, serial and PIT/POST,
three-ROM system behavior, LVS, board geometry, parts, power, mechanics and
release guards. CAD-dependent sections may report SKIP when tools are absent;
review that output before claiming the corresponding checks passed.
The `--ci` option runs the hosted behavioral smoke subset.

For focused changes:

| Change | Check |
| --- | --- |
| Shared maps or card specs | `python3 scripts/check_spinoff_commons.py` and `python3 scripts/check_revb_boards.py --completeness` |
| GAL sources | `spinoffs/minimal-vga/pld/revb/build_revb_gals.sh` |
| ROM sources | `python3 spinoffs/minimal-vga/roms/check_revb_rom_set.py` |
| PIT, POST or serial clock | `spinoffs/minimal-vga/sim/revb_io_expansion_check.sh` |
| Integrated ROM behavior | `spinoffs/minimal-vga/sim/revb_rom_system_check.sh` |
| Serial connector/electrical path | `python3 spinoffs/minimal-vga/kicad/revb/check_revb_serial_contract.py` and `python3 spinoffs/minimal-vga/kicad/revb/check_revb_serial_electrical.py` |
| Changed I/O source and system release checks | `spinoffs/minimal-vga/kicad/revb/revb_i7_release_check.sh` |
| Release evidence and owner hold | `python3 spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py --self-test` |

Use `kicad/revb/env.sh` for the CAD/tool locators. Board generation, routing,
physical checks and `kicad/revb/export_fab.sh` live under
`spinoffs/minimal-vga/`; export regenerates all five fabrication packages.
Package identities belong in the machine-readable manifest and release record,
not in a second task ledger.

## Upload, order and bench gates

Before uploading, the exact candidate must satisfy:

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py \
  --require-released --package-root fab/minimal-vga/revb/package
```

Exit 3 is the expected **ORDER HOLD** while owner authorization is absent.
Follow the [order record](rev-b-five-board-order-record.md) for vendor previews,
DFM changes and the separate payment decision. After delivery, follow the
[bench template](rev-b-b1-bench-log.md) in stage order, recording actual readbacks,
rails, current, clocks, PIT/POST and serial/video behavior before advancing.
