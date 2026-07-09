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
| D2 constraint report generated | PASS |
| D94 constraint report generated | PASS |
| FDC hardware handoff generated | PASS |
| Beeper source/handoff guarded | PASS |
| Serial USART behavior guarded | PASS |
| Decap value boundary guarded | PASS |
| D41 timing boundary guarded | PASS |
| Memory timing boundary guarded | PASS |
| Bring-up verification points generated | PASS |
| Source coverage audit current | PASS |
| Cartridge BASIC boundary documented | PASS |

## Highest-value physical asks

| Priority | Ask | Exact deliverable | Evidence source | Why it matters |
| --- | --- | --- | --- | --- |
| P0 | programming disk / PROM truth | Baltijets doc 007 disk files, or dumps of D2/D6 RT4, D8 RE3, D94 RE3, D15/D16 EPROMs | `docs/community-prom-media-request.md`; `docs/prom-dump-procedure.md`; `docs/d2-reconstruction-constraints.md` | unblocks preservation-grade PROM truth and validates/replaces reconstructed D6/D8 fallbacks |
| P0 | JUKU-1 media provenance | independent `JUKU-1` / `ДГШ5.106.105` disk image or checksum/provenance for `media/disks/JUKU1.CPM` | `docs/community-prom-media-request.md`; `docs/ekdos-media-acquisition.md` | turns the public EKDOS boot image into stronger physical-media evidence |
| P0 | cartridge BASIC truth | larger/different removable-memory BASIC cartridge image, programming artifact, or hardware-confirmed Monitor 3.3 launch procedure to BASIC `READY` | `docs/community-prom-media-request.md`; `docs/basic-launch-probe.md`; `docs/basic-cartridge-tail-hypotheses.md` | closes the remaining Monitor 3.3 cartridge BASIC compatibility boundary |
| P1 | D94 .092 continuity | D94 pin 15 enable and pins 1-7/9 output destinations on a .009 processor board | `docs/d94-reconstruction-constraints.md` | required before any defensible D94 reverse-engineered burnable table |
| P1 | FDC interrupt/buffer continuity | WD1793 DRQ/INTRQ to 8259 inputs, D93 MR/CLK, plus D100 OE/T if accessible | `docs/fdc-hardware-handoff.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` WS-F | reduces first EKDOS-on-hardware debug risk |
| P1 | memory-decode stragglers | D6 V1/V2 feed, C99 far plate, D36/D39/D53 RAM-strobe ambiguous feeds, and D41 timing-bus input/control pins | `docs/memory-timing-boundary.md`; `docs/d41-timing-boundary.md`; `docs/replica-bringup-verification-points.md`; `PLAN.md` WS-A/WS-F | tightens the as-built netlist around RAM/video timing before netlist freeze |
| P2 | analog/video/sound/serial bring-up captures | composite/RF/sync/audio nodes plus X3 serial loopback while running the staged bring-up ladder | `docs/replica-bringup-verification-points.md`; `docs/beeper-readiness.md`; `docs/video-readout-readiness.md`; `docs/serial-handoff.md` | bench evidence only; does not block PCB fabrication |
| P2 | photos and passive values | macro photos for the FDC/top-center quadrant, C35-C72 bypass-cap values by refdes/position, sound/video analog corner passives | `docs/decap-value-fidelity.md`; `PLAN.md` WS-F; generated BOM/sourcing docs | improves authenticity and reduces assembly substitutions |

## Current D94 blockers

- D94 failed evidence checks: `Enable pin D94.15 is traced, Any D94 output net is traced, .092 firmware artifact exists, Repository-wide .092 artifact filename exists`
- D94 address pins are already traced to `BA11..BA15`; the useful physical
  work is enable/output continuity plus a real `.092` dump/table.

## Pin-Level Closure

These rows mirror the unnetted functional pins exposed by
`docs/board-fidelity-gap-ledger.md`. They are the exact pin-level
closures that endpoint coverage cannot prove because the pins are not
yet modeled as nets.

| Ref | Unnetted functional pins | Needed evidence |
| --- | --- | --- |
| `D100` | `9:OE_N, 11:T` | FDC quadrant continuity |
| `D2` | `1:A6, 2:A5, 3:A4, 4:A3, 5:A0, 6:A1, 7:A2, 12:D0, 13:V1, 14:V2, 15:A7` | dump/programming disk plus sheet-1 continuity |
| `D41` | `1:DS, 2:A, 3:B, 4:C, 5:D, 6:LD, 8:G, 9:CK` | sheet-2 timing-chain continuity |
| `D93` | `19:MR_N, 24:CLK` | FDC quadrant continuity |
| `D94` | `1:D0, 2:D1, 3:D2, 4:D3, 5:D4, 6:D5, 7:D6, 9:D7, 15:E_N` | .092 dump/table plus enable/output continuity |
| `S4` | `1:P1, 2:P2` | sheet-1/SB switch continuity |

## Bring-up verification scope

- Generated bring-up verification nets: `36`
- `FDC`: `3` net(s)
- `logic`: `6` net(s)
- `memory/decode`: `9` net(s)
- `sound/analog`: `2` net(s)
- `timing/I/O`: `5` net(s)
- `video/analog`: `11` net(s)

## Practical sequencing

1. Ask for programming disk files and BASIC cartridge artifacts first;
   they can close PROM/software truth without touching fragile sockets.
2. If a board owner can help, dump socketed PROM/EPROM parts before
   continuity probing; repeated reads plus socket photos are enough to
   compare against the reconstructed fallbacks.
3. Use continuity only for the P1 nets above; broad bring-up checklist
   probes are deferred until a replica or owner board is already on the
   bench.
