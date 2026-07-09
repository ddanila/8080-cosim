# EKDOS checkpoint reference

Status: **PASS**

This guard regenerates a full cosim machine checkpoint at 30,000
framebuffer writes on the vendored `media/disks/JUKU1.CPM` `TDD` path.
That is the last byte-identical `juku_top` comparison point before the
first PIC/PPI setup window at 30,520 writes.

The generated checkpoint files are not committed. They are an automation
source for the checkpoint-resumed HDL diagnostics and a historical
anchor for the uninterrupted prompt guard.

## Command

```sh
sync/ekdos_checkpoint_reference.py
```

## Evidence

- Trace exit code: `0`
- VRAM writes: `30000`
- CPU cycles: `1963707`
- RAM SHA256: `eaa42964cdbc37bce58081edc085c5bcf94e95deed6454230e1aab8f1c3a38d4`
- VRAM SHA256: `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68`

| Field | Value |
| --- | ---: |
| `pc` | `0484` |
| `sp` | `D44C` |
| `a` | `A1` |
| `b` | `D7` |
| `c` | `E7` |
| `d` | `00` |
| `e` | `A1` |
| `h` | `FD` |
| `l` | `2F` |
| `sf` | `1` |
| `zf` | `0` |
| `hf` | `0` |
| `pf` | `0` |
| `cf` | `0` |
| `iff` | `0` |
| `mode` | `0` |
| `portc` | `80` |
| `kbd_col` | `0F` |
| `pic_icw1` | `00` |
| `pic_icw2` | `00` |
| `pic_mask` | `FF` |
| `fdc_enabled` | `1` |
| `fdc_motor_on` | `0` |
| `fdc_track` | `00` |
| `fdc_sector` | `01` |

## Boundary

- This proves the cosim checkpoint is stable; it does not by itself
  resume the die-accurate HDL CPU.
- This checkpoint is now a historical lower-level anchor: later
  checkpoint-resumed diagnostics and the uninterrupted Verilator prompt
  guard cover the first PIC/PPI/FDC window without replaying the full
  framebuffer draw in every routine check.
