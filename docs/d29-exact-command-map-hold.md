# D29 exact .009 command pin map

Status: **SOURCE MODEL CORRECTED / PHYSICAL AND ROUTING HOLD**

The original-resolution `.009 Э3` sheet-1 crop
`ref/photos/dgsh5-109-009-e3/PXL_20260718_101813438.jpg`
`(1520,3000)–(2360,3580)` prints every D29 physical input pin, paired
output pin, and command label. The transcription is preserved in
`ref/schematics/d29-exact-009-pinmap-review.json`. Its pairs match the
КР580ВА86/Intel 8286 physical pairs: 1↔19, 2↔18, …, 8↔12. Symbol row order
is permuted and cannot substitute for pad numbers.

| Input pin | Output pin | Exact .009 output label | Replica output at that pad |
| ---: | ---: | --- | --- |
| 3 | 17 | `-INHIB` | `INHIB_N` |
| 1 | 19 | `CCLCK` | `CCLCK` |
| 2 | 18 | `-IO/M` | `IOM_N` |
| 7 | 13 | `-MWC` | `MWC_N` |
| 6 | 14 | `-MRC` | `MRC_N` |
| 8 | 12 | `-AMWC` | `AMWC_N` |
| 4 | 16 | `-IORC` | `IORC_N` |
| 5 | 15 | `-IOWC` | `IOWC_N` |

The board JSON, schematic, all three PCB pad maps, HDL bus ordering, and
8286 pinout audit use these exact rows. D29.1 is on PHI2TTL; D35.13 is
on the separate post-R35 node. The three passive parts R35, R106, and C29
exist in the source model but await footprint placement and owner measurements.
Registered probe centres and the cable-covered D29.2 waypoint are recorded
in [the D29 pin-2 review](../ref/photos/juku-pcb-2/d29-pin2-front-chase.json)
and [the D7 guide](d7-gates-source-review.md). Photo registration supports
the probe locations but does not close the hidden D29.2 segment or its
remote D7.3 join; verify both by continuity.

Exact sheet-1 detail `(1000,3040)–(1740,3540)` shows D7.3 directly feeding
D29.2; the riser crosses D29.7 without a dot. The lower continuation puts
D29.8 on `-MWR`/MEMW, D29.4 on `-IORD`, and D29.5 on `-IOWR`. These
connections are modeled. The source-drawn D7.3→D29.2 join still requires
owner-board continuity before physical fidelity can be claimed. Native
sheet-1 pixels show D7.11 and D105.3 on
separate local strokes, correcting the earlier claimed output tie.

## Verification and routing hold

Run from the repository root with Python's standard library:

```sh
python3 scripts/report_8286_pinout_audit.py
```

This regenerates [the pinout audit](8286-pinout-audit.md), checking selected
source-model endpoints and LVS mapping data. It does not run LVS or inspect
PCB copper. Current routing
and DRC holds are recorded in [factory-wire fidelity](factory-wire-route-fidelity.md)
and [the routed audit](routed-refresh-audit.md). Physical continuity and
R35/R106/C29 placement/value questions remain open.
