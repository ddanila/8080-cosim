# FDC readiness

Status: **HDL WD1793 SYNTHETIC-SECTOR READY**

This guard proves the first HDL-side WD1793 behavior slice needed by WS-B1:

- `hdl/devices.v` implements D93-compatible restore, seek, read-sector,
  status, track, sector, and data register behavior in `fdc_1793`.
- `hdl/sim/fdc_1793_tb.v` mirrors the C-side synthetic media guard:
  restore returns to track 0, seek copies the data register to the track
  register, read-sector streams 512 bytes, side select changes the stream,
  and motor-off read reports not-ready.
- The guard uses synthetic sector contents only. Vendored Juku disk images live
  under `media/disks/`, but the HDL path does not yet consume disk files.

## Command

```sh
sync/fdc_check.sh
```

## Evidence

| Check | Result |
| --- | --- |
| Restore command clears transfer and returns to track 0 | PASS |
| Seek command copies data register to track register | PASS |
| Read-sector command asserts BUSY/DRQ and streams 512 bytes | PASS |
| Side select affects the synthetic sector stream | PASS |
| Motor-off read reports NOT READY | PASS |

## Remaining Boundary

- Connect the same behavior to vendored raw disk media for `juku_top`.
- Preserve the Arti `JUKU1.CPM` cosim proof from
  `docs/ekdos-media-acquisition.md` as the disk-backed reference.
- Confirm D93 INTRQ/DRQ, MR, CLK, and D100 OE/T wiring during the owner session.
