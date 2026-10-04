# D6 firmware mode coverage

Status: **A6/A5 11/10 OBSERVED / A7 IO-CYCLE SOURCE CLOSED**

This generated report traces authentic ROMBIOS Port-C writes and separates
the measured physical D6 inputs A6=`/PC1`, A5=`/PC0` from the historical
emulator's non-inverted `PC1..PC0` banking convention. Owner continuity
closes D6 A7 through D105.1 to D7.8, the I/O-cycle-active-high NAND of raw
`/IORD` and `/IOWR`.

## Reproduction

```sh
python3 scripts/report_d6_firmware_modes.py
```

The generator builds the C trace harness and runs `ekta37` with a
50,000,000-cycle limit and 32,000-video-write stop, setting `JUKU_TRACE_IO=1`.
It replays captured PPI0 port `06/07` writes and checks 24 events and the
resulting mode sets. The D6 suffixes are calculated from Port C using the
registered physical inversion; this is software execution, not a logic capture.

## Early ROM trace

- Port-C events: `24`
- Physical D6 A6/A5 suffixes observed (`/PC1,/PC0`): `10, 11`
- Legacy emulator modes observed (`PC1..PC0`): `00, 01`

| Cycle | PC | VRAM writes | Port/value | Port C before -> after | D6 A6/A5 | Legacy view |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 123 | `01A8` | 0 | `0x07=0x82` | `0x00->0x00` | `11` | `00` |
| 140 | `01AC` | 0 | `0x07=0x0F` | `0x00->0x80` | `11` | `00` |
| 1970003 | `026D` | 30160 | `0x07=0x0E` | `0x80->0x00` | `11` | `00` |
| 3038115 | `0299` | 30200 | `0x07=0x0E` | `0x00->0x00` | `11` | `00` |
| 3064197 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `10` | `01` |
| 3064555 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `11` | `00` |
| 3064788 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `10` | `01` |
| 3064961 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `10` | `01` |
| 3065377 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `11` | `00` |
| 3065949 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `10` | `01` |
| 3066209 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `11` | `00` |
| 3066428 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `10` | `01` |
| 3066601 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `10` | `01` |
| 3066951 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `11` | `00` |
| 3067985 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `10` | `01` |
| 3068245 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `11` | `00` |
| 3068464 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `10` | `01` |
| 3068637 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `10` | `01` |
| 3069053 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `11` | `00` |
| 3069625 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `10` | `01` |
| 3069885 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `11` | `00` |
| 3070104 | `D7EF` | 30524 | `0x06=0x01` | `0x00->0x01` | `10` | `01` |
| 3070277 | `DCD5` | 30524 | `0x07=0x0E` | `0x01->0x01` | `10` | `01` |
| 3070627 | `D7EF` | 30524 | `0x06=0x00` | `0x01->0x00` | `11` | `00` |

ROMBIOS toggles `0x00/0x01` sixteen times around its high-ROM transition.
Those writes change PC0 and therefore toggle physical D6 A5 after the D3
inverter. Port C alone determines only suffix `11` or `10`; A7 is independent.
During memory cycles D7.8 is low, so the runnable table rows are `011` and
`010`. During the OUT event itself A7 is high, but those rows do not select
a firmware memory map.

## Later FDC/EKDOS evidence

The retained reports below contain a recognized Port-C value of `0x04`,
which sets PC2 but leaves PC1/PC0 clear. It therefore retains A6/A5=`11`.
The generator extracts the first matching value from each report and checks
that at least one value is found and all found values are `0x04`. Reports
without a matching field are omitted; their probes are not rerun here.
Recorded Verilator results remain subject to the current
[simulator compatibility limit](../sync/README.md#simulator-compatibility).

| Evidence | Port C | D6 A6/A5 |
| --- | ---: | --- |
| `docs/juku-top-fdc-verilator-probe.md` | `0x04` | `11` |
| `docs/juku-top-jbasic-verilator-probe.md` | `0x04` | `11` |

## Coverage boundary

- Calculated physical A6/A5 suffixes `11` and `10` have C firmware execution evidence.
- A7 is not a Port-C bit: owner continuity identifies the D7.8→D105.1/D6.15
  connection. Its NAND contract makes it high while raw `/IORD` or `/IOWR`
  is asserted; continuity alone does not measure that powered behavior. Memory-map selection
  therefore uses A7=`0`.
- Every physical A7=`1` row emits only `B` or `F`; both release ROM/RAM
  selects, so the I/O-cycle quadrant cannot express a competing memory map.
- This trace guards firmware writes, not the unresolved downstream meaning of
  every D6 output word; see `docs/d6-physical-decode.md`.
