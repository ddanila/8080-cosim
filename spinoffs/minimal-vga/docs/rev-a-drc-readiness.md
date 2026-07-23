# Rev A current-source DRC readiness

Status date: **2026-07-23**.

Status: **CURRENT SOURCE DRC CLEAN**.

This report binds a full KiCad error-level DRC result to the exact routed
Rev-A PCB after the D1 DO-41 correction and inner-plane refill. It does
not release fabrication; package integrity, vendor preview, sourcing, and
human review remain separate gates.

## Result

- Board: `spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb`
- Board SHA-256: `a056d758c89801737bb285ce58f96e922cabff62d8d769d3e5c300267940b746`
- KiCad CLI: `/home/ddanila/fun/8080-cosim/scripts/kicad-flatpak-cli.sh`
- KiCad version: `10.0.5`
- Board file version: `20260206`
- Board generator version: `10.0`
- Error-level DRC violations: **0**
- Unconnected items: **0**

## Refill disposition

- For the 2026-07-23 D1 correction, `kicad-cli pcb diff` against
  `95c40381` reports only the two filled-zone polygons; no board
  metadata, footprint, track, or via semantic change.
- A post-refill CLI smoke export emitted the complete 10-file
  Gerber/job set, one Excellon drill file, and all 119 position rows.
  Package freshness is bound separately by its manifest and checksum.

## Command

```sh
python3 spinoffs/minimal-vga/kicad/report_rev_a_drc_readiness.py
```

The saved board already contains current zone fills. Refill and save zones
with the same KiCad generation after any pad, track, via, or zone change,
then regenerate this report. Gerber/drill export, package-integrity checks,
vendor preview, and human release review remain separate gates.
