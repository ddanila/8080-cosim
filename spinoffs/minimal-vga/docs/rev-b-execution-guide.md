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

It covers shared facts, card completeness, GAL compilation, ROM packaging and
freshness, serial and PIT/POST,
three-ROM system behavior, LVS, board geometry, parts, power, mechanics and
release guards. Some individual checks skip missing tools, but the full suite
requires Galette, Icarus and KiCad Python: R5.I7 fails if KiCad Python is absent.
KiCad CLI is needed for DRC and Yosys for LVS; inspect skipped checks before
claiming those results. The parts checks also require the KiCad footprint library.
The behavioral checks need Python 3, a C compiler available as `cc`, and the
initialized `spinoffs/minimal-vga/external/tv80` submodule. Bring-up and EKTA
boot checks return 0 with `SKIP` if tv80 is missing. ROM freshness validates
the pinned EKTA/C10 input binaries and rebuilds DIAG and the packaged images;
it does not assemble EKTA or C10 from source.

The suite rewrites `footprints.<card>.json` while resolving library parts and
runs C-oracle checks that overwrite `cosim/vram.bin`. Save any framebuffer you
need, and inspect the working-tree diff afterward. It checks retained routed
sources; it does not regenerate layouts or fabrication packages.

`--ci` runs the behavioral smoke subset. `REVB_CI_GROUP=cards` selects card,
bus-assertion and bring-up tests; `system` selects serial, I/O expansion,
ROM-system and video tests; the default `all` runs both. All groups check shared
facts, board completeness and ROM freshness. The system subset limits EKTA's
Mode A/B boot comparison to 1,000 writes and omits the TTL-card boot, which CI
runs separately. It does not perform CAD, GAL compilation or release checks.

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
| Release evidence, archive identity and owner hold | `python3 spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py --self-test --package-root fab/minimal-vga/revb/package` |

Use `spinoffs/minimal-vga/kicad/revb/env.sh` for the CAD/tool locators.
Board generation, routing and physical checks live in the same directory.
`spinoffs/minimal-vga/kicad/revb/export_fab.sh` regenerates all five
fabrication packages and requires Bash, Python 3, KiCad CLI, KiCad Python,
the KiCad footprint library and `zip`. If KiCad CLI or KiCad Python is missing,
it returns 0 with `SKIP` before touching the package directory; existing files can therefore
remain from an earlier export. Check the output and candidate identities.
Without `--package-root`, the release checker validates recorded identities and
routed-source hashes but does not read the ZIPs. R5.I7 runs only that checker's
negative controls; its success does not validate a candidate package.

Export replaces the local package directory and rewrites its tracked manifest;
follow the [order plan](rev-b-five-board-order-plan.md) to review and reconcile
a regenerated candidate. Package identities belong in the machine-readable manifest and release record,
not in a second task ledger.

## Upload, order and bench gates

The [keyboard encoder pinout mismatch](rev-b-io-parts.md#keyboard-pinout-mismatch--release-blocker)
must be corrected and the I/O package requalified before upload. The release
checker verifies recorded identities and authorization; it does not detect this
manufacturer-pinout error.

Before uploading, the exact corrected candidate must satisfy:

```sh
python3 spinoffs/minimal-vga/kicad/revb/check_revb_release_gate.py \
  --require-released --package-root fab/minimal-vga/revb/package
```

Exit 3 means the record is valid but remains on **ORDER HOLD** without owner
authorization. Invalid or missing evidence instead exits 1.
Follow the [order record](rev-b-five-board-order-record.md) for vendor previews,
DFM changes and the separate payment decision. After delivery, follow the
[bench template](rev-b-b1-bench-log.md) in stage order, recording actual readbacks,
rails, current, clocks, PIT/POST and serial/video behavior before advancing.
