# Rev A current-source DRC readiness

Status date: **2026-07-23**.

Status: **CURRENT SOURCE DRC CLEAN**.

This report binds a full KiCad error-level DRC result to the exact routed
Rev-A PCB after the D1 DO-41 correction, the U20/U21 active-low
address-mux enable correction, the U22 refresh-counter cascade
correction, and inner-plane refill. It does not release fabrication;
package regeneration, vendor preview, sourcing, and human review remain
separate gates.

## Result

- Board: `spinoffs/minimal-vga/kicad/rev-a-physical.kicad_pcb`
- Board SHA-256: `1326703605818b168dff3fd9f0879d36f8494393e8f8567ca7894061c7419650`
- KiCad CLI: `/home/ddanila/fun/8080-cosim/scripts/kicad-flatpak-cli.sh`
- KiCad version: `10.0.5`
- Board file version: `20260206`
- Board generator version: `10.0`
- Error-level DRC violations: **0**
- Unconnected items: **0**

## Refill disposition

- U20.15 and U21.15 are the active-low enables of the two 74HCT157
  address multiplexers. The correction moves both pads and their four
  retained F.Cu segments from the former floating `ADDRMUX_OE_N` island
  to GND; filled In1.Cu then provides the return connection.
- U22.2 and U22.12 are the 74HCT393 active-high reset inputs. The
  correction moves both pads and the three retained former
  `REFRESH_CLR` trace segments to GND.
- U22.6 (1Q3) is cascaded to U22.13 (2CP) on `REFRESH_ROW3` with eight
  signal segments and two through vias, forming the intended 8-bit
  refresh-row counter.
- The saved post-correction board passes DRC after a stable-KiCad refill.
  The prior fabrication package predates these source changes and is stale;
  package freshness requires a new guarded export and checksum.

## Command

```sh
python3 spinoffs/minimal-vga/kicad/report_rev_a_drc_readiness.py
```

The saved board already contains current zone fills. Refill and save zones
with the same KiCad generation after any pad, track, via, or zone change,
then regenerate this report. Gerber/drill export, package-integrity checks,
vendor preview, and human release review remain separate gates.
