# Rev A current-source DRC readiness

Checked (UTC): **2026-10-04**.

Status: **CURRENT SOURCE DRC CLEAN**.

This report binds KiCad's error-level DRC result to the exact PCB hash below.
It does not include warning-level violations, refill zones or qualify fabrication.
See [manufacturing readiness](rev-a-manufacturing-readiness.md) for release gates.

## Result

- Board: `spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb`
- Board SHA-256: `1326703605818b168dff3fd9f0879d36f8494393e8f8567ca7894061c7419650`
- KiCad CLI: `/usr/bin/kicad-cli`
- KiCad version: `10.0.6`
- DRC command exit code: `0`
- Board file version: `20260206`
- Board generator version: `10.0`
- Error-level DRC violations: **0**
- Unconnected items: **0**

## Command

```sh
python3 spinoffs/minimal-vga/kicad/report_rev_a_drc_readiness.py
```

Run from the repository root with KiCad 10 or newer; `KICAD_CLI` overrides
the repository locator. Optional positional arguments select the PCB and output
report paths. The command overwrites this report by default, including on DRC failure.

Refill and save zones with a compatible KiCad version after pad, track, via or
zone changes before running this check. A clean result requires command success,
zero error-level violations and zero unconnected items. Package freshness, vendor
preview and human release review remain separate gates.
