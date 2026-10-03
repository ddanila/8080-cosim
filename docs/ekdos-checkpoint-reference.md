# EKDOS checkpoint reference

Status: **PASS**

This guard generates a cosim checkpoint at 30,000
framebuffer writes on the vendored `media/disks/JUKU1.CPM` `TDD` path.
This diagnostic stop precedes the later PIC/configuration-scan window at
30,520 writes. The [uninterrupted HDL prompt run](juku-top-fdc-verilator-probe.md)
records execution through the EKDOS `A>` prompt at 73,405 writes.

Temporary checkpoint files are deleted when this command finishes.
Checkpoint-resumed HDL diagnostics generate their own input files.

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

Only the fields listed in the generator’s `EXPECTED` mapping are compared
with fixed values. The other state rows and cycle count are observations.

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
| `fdc_physical_track` | `00` |
| `fdc_sector` | `01` |
| `fdc_drq_ticks` | `0` |
| `fdc_write_first_byte_pending` | `0` |

## Boundary

- This guard checks selected state fields, the write count, and RAM/VRAM hashes at
  this stop. It does not resume the die-accurate HDL CPU.
- Checkpoint-resumed HDL diagnostics avoid replaying the framebuffer
  draw. The uninterrupted prompt run separately checks execution from reset.
