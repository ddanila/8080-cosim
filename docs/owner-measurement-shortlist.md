# Owner measurement shortlist

Status: **READY**

This generated report compresses the remaining physical-owner asks into
the shortest useful list. It is not a bench log and does not claim any
measurement has been performed; it records what still cannot be derived
automatically from the current repo evidence.

## Command

```sh
python3 scripts/report_owner_measurement_shortlist.py
```

## Evidence freshness

| Check | Status |
| --- | --- |
| Community request packet ready | PASS |
| PROM dump procedure exists | PASS |
| D6/D8 reconstructed fallback exported | PASS |
| D94 constraint report generated | PASS |
| Bring-up verification points generated | PASS |
| Source coverage audit current | PASS |

## Highest-value physical asks

| Priority | Ask | Exact deliverable | Evidence source | Why it matters |
| --- | --- | --- | --- | --- |
| P0 | programming disk / PROM truth | Baltijets doc 007 disk files, or dumps of D2/D6 RT4, D8 RE3, D94 RE3, D15/D16 EPROMs | `docs/community-prom-media-request.md`; `docs/prom-dump-procedure.md` | unblocks preservation-grade PROM truth and validates/replaces reconstructed D6/D8 fallbacks |
| P0 | JUKU-1 media provenance | independent `JUKU-1` / `ДГШ5.106.105` disk image or checksum/provenance for `media/disks/JUKU1.CPM` | `docs/community-prom-media-request.md`; `docs/ekdos-media-acquisition.md` | turns the public EKDOS boot image into stronger physical-media evidence |
| P1 | D94 .092 continuity | D94 pin 15 enable and pins 1-7/9 output destinations on a .009 processor board | `docs/d94-reconstruction-constraints.md` | required before any defensible D94 reverse-engineered burnable table |
| P1 | FDC interrupt/buffer continuity | WD1793 DRQ/INTRQ to 8259 inputs, plus D100 OE/T if accessible | `docs/replica-bringup-verification-points.md`; `PLAN.md` WS-F | reduces first EKDOS-on-hardware debug risk |
| P1 | memory-decode stragglers | D6 V1/V2 feed, C99 far plate, and D36/D39/D53 RAM-strobe ambiguous feeds | `docs/replica-bringup-verification-points.md`; `PLAN.md` WS-A/WS-F | tightens the as-built netlist around RAM timing before netlist freeze |
| P2 | analog/video/sound bring-up captures | composite/RF/sync/audio nodes while running the staged bring-up ladder | `docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md` | bench evidence only; does not block PCB fabrication |
| P2 | photos and passive values | macro photos for the FDC/top-center quadrant, bypass-cap values by position, sound/video analog corner passives | `PLAN.md` WS-F; generated BOM/sourcing docs | improves authenticity and reduces assembly substitutions |

## Current D94 blockers

- D94 failed evidence checks: `Enable pin D94.15 is traced, Any D94 output net is traced, .092 firmware artifact exists`
- D94 address pins are already traced to `BA11..BA15`; the useful physical
  work is enable/output continuity plus a real `.092` dump/table.

## Bring-up verification scope

- Generated bring-up verification nets: `41`
- `FDC`: `3` net(s)
- `logic`: `7` net(s)
- `memory/decode`: `10` net(s)
- `sound/analog`: `2` net(s)
- `timing/I/O`: `8` net(s)
- `video/analog`: `11` net(s)

## Practical sequencing

1. Ask for programming disk files first; they can close PROM truth without
   touching fragile sockets.
2. If a board owner can help, dump socketed PROM/EPROM parts before
   continuity probing; repeated reads plus socket photos are enough to
   compare against the reconstructed fallbacks.
3. Use continuity only for the P1 nets above; broad bring-up checklist
   probes are deferred until a replica or owner board is already on the
   bench.
