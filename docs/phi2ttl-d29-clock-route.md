# PHI2TTL and D29 command-buffer route

Status: **SOURCE AND OWNER VERIFIED / REPLICA MODEL CORRECTION PENDING**

The full-sheet `.009` electrical schematic and continuity on the CS00015
processor board correct the reconstructed D29 clock input.  D29 physical pin 1
is not `MEMW`; it is the input whose buffered output, D29.18, is `CCLCK`.

## Primary evidence

- Exact-revision source: `ref/photos/dgsh5-109-009-e3/PXL_20260718_101754468.jpg`
  (`ДГШ5.109.009 Э3`, sheet 1), SHA-256
  `effc98746807ef28dab97051ceba293f4433c0f3b39b86cbb55ddcaad24aeca4`.
- Owner continuity on CS00015, 2026-08-04, confirms that the D35.13 clock
  path reaches D29.1.

On sheet 1, `(2) Ф2 TTL` enters D30 CLK1/pin 3.  The junction immediately
before D30.3 branches downward; the conductor can be followed across the full
sheet to D29 physical pin 1.  D29.1 is the A1 command-buffer channel and its
paired output D29.18 is explicitly labelled `CCLCK`.

Sheet 2 places R35 (330 ohms) between the `Ф2TTL` trunk and the local D35.13
RC-shaped input node, with C29 and R106 on the D35 side.  Therefore D35.13 must
not be collapsed onto the zero-ohm `PHI2TTL` copper net in the replica model.

```text
                         +--> D30.3
PHI2TTL -----------------+--> D29.1 --> D29.18 CCLCK
                         +--> R35 330R --> D35.13
                                           +-- C29
                                           `-- R106
```

Expected powered-off checks are approximately 0 ohms from D29.1 to D30.3 and
330 ohms from D29.1 to D35.13.  Record the measured resistance rather than
relying only on a continuity beeper because some meters beep through 330 ohms.

## Root cause of the reconstruction error

The four numbered cross-sheet continuations drawn immediately below D29 are:

```text
1  -MRD
2  -MWR
7  -IOWR
8  -IORD
```

Those leading numbers are continuation identifiers, not D29 package-pin
numbers.  Treating the `1` beside `-MWR` as physical D29.1 incorrectly placed
D29.1 on `MEMW` and hid the clock route.

The readable D29 channel order on the exact `.009` sheet is:

| Input pin | Output pin | Output label |
| ---: | ---: | --- |
| 3 | 17 | `-INHIB` |
| 1 | 18 | `CCLCK` |
| 2 | 19 | `-IOM` |
| 5 | 14 | `-MWC` |
| 6 | 13 | `-MRC` |
| 4 | 12 | `-AMWC` |
| 8 | 16 | `-IORC` |
| 7 | 15 | `-IOWC` |

## Replica-model disposition

Until the migration is completed, all generated claims that place D29.1 on
`MEMW` or D35.13 directly on `PHI2TTL` are superseded by this source
correction.  The affected artifacts include `kicad/juku.board.json`,
`docs/8286-pinout-audit.md`, `docs/io-decode-boundary.md`,
`docs/memory-timing-boundary.md`, and the routed-board PHI2TTL guards.  The
atomic model fix must:

1. remove D29.1 from `MEMW` and add it to `PHI2TTL` with D30.3;
2. split D35.13 onto the post-R35 RC node;
3. audit all eight D29 input/output endpoints against the table above; and
4. migrate the source schematic, unrouted board, and routed-board copper
   together so the replica does not temporarily encode a false short or open.
