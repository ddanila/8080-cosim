# FDC/VG93 core survey

Status date: 2026-07-07.

The current `hdl/devices.v` `fdc_1793` block is a bounded simulation shim, not a
full manual ВГ93 clone. It exists to let `juku_top` exercise the boot-critical
WD1793 register path against vendored raw Juku media while the board connectivity
stays LVS-checked. It covers restore, seek, read-sector, status/data register
behavior, side select, motor-not-ready, and `+disk=media/disks/JUKU1.CPM`
sector streaming.

Do not keep expanding this shim into a full floppy controller. If we need full
format/write/timing behavior, replace or wrap it with an upstream core whose
license is acceptable for this repository.

## Candidate Cores

| Candidate | Source | Fit | License status | Disposition |
|---|---|---|---|---|
| Sorgelig / MiST `wd1793.sv` | `https://github.com/sorgelig/ZX_Spectrum-128K_MIST/blob/master/wd1793.sv` | Mature WD1793/WD1772/WD1773 replica with write capability; supports 10 x 512-byte sector geometry via `size_code`; expects RAM/SD image buffering rather than direct simulator file reads. | File header is GPL v2 or later. | Good technical candidate if GPL HDL is acceptable in-tree or isolated under a clear vendor boundary. Needs a Juku adapter for `cs_n/rd_n/wr_n/A/D`, side/motor/ready, and raw image preload. |
| MiSTer SAM Coupe `wd1793.sv` | `https://github.com/MiSTer-devel/SAM-Coupe_MiSTer/blob/master/rtl/wd1793.sv` | Same Sorgelig-lineage style: full-featured compared with our boot shim, but not a drop-in for the current testbench. | File header is GPL v2 or later. | Same as above. Prefer a single vendored source of this lineage if chosen. |
| Solegstar `FDC1793-Emul` | `https://github.com/solegstar/FDC1793-Emul` | VG93/FDC1793 FPGA emulator derived from IanPo/andykarpov work. It models MFM/DPLL/control-level behavior and exposes VG93-style pins. | No license file was found in the repository during the 2026-07-07 survey. Some subfiles carry copyright comments. | Do not vendor without explicit license clarification. Useful as a reference pointer only. |
| Emu80v4 `Fdc1793` | `https://github.com/vpyk/emu80v4/blob/master/src/Fdc1793.cpp` | Software emulator model for КР580ВГ93/FDC1793 used by multiple Soviet-machine targets. It covers Type-I step family, sector read/write, read-address, write-track, DRQ/IRQ, index pulse status, write protect, and raw sector-image geometry. No Juku-specific driver/config was found. | Repository is GPL-3.0-or-later. | Do not copy code into the local shim. Keep as a behavioral checklist if decoded FDC I/O is reached and the current boot/media shim proves insufficient. Details recorded in `docs/emu80v4-survey.md`. |
| Local WD1772 transistor/PLA reference | `/home/ddanila/Downloads/wd1772.pdf`, `/home/ddanila/Downloads/wd1772pla.txt` | User-provided reverse-engineering material for the WD1772/FD1773/VG93 lineage. The PDF is a searchable KiCad transistor/gate schematic; the text file is a 120-row PLA/PLM table with 19 input and 20 output columns. | License/provenance not established in this repo. | Do not vendor yet. Keep hashes and usage boundary in `docs/wd1772-vg93-reference.md`; use only as a deep signal/state-machine cross-check if a full controller model is required. |

## Current Decision

Keep the local shim only as a minimal HDL media bridge until a full core is
needed. The next functional target is not "implement all ВГ93 internals"; it is:

1. Drive the full `ROMBIOS 3.43` `<T>, <D>, <D>` path through `juku_top` with
   `+disk=media/disks/JUKU1.CPM`.
2. Reach the EKDOS `A>` prompt in HDL, matching the existing cosim proof.
3. If controller behavior beyond the current read path becomes the blocker,
   decide whether to accept GPL HDL and vendor/adapt Sorgelig-lineage `wd1793.sv`,
   using the Emu80v4 software model and local WD1772/PLA reverse-engineering
   files as additional behavior checklists.

## Verification

The bounded shim is guarded by:

```sh
sync/fdc_check.sh
sync/boot_check.sh
sync/check.sh
```

`sync/fdc_check.sh` now runs both synthetic-sector checks and a vendored-media
check against `media/disks/JUKU1.CPM`.
