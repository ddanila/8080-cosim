# FDC write-precomp source map

The recovered ДГШ5.109.009 Э3 sheet 3 closes the target board's write-data delay and precompensation chain. The model adopts every non-conflicting sheet connection, while direct target-board continuity remains authoritative where the factory electrical drawing is internally inconsistent.

| Function | Closed path |
|---|---|
| Write-data input | D93.31 → D97.10 |
| First delay | D97.5 → D101.10; D97.12 → D102.10 |
| Cascaded delays | D102.5 → D101.11; D102.12 → D102.2; D102.13 → D101.12 |
| Selection | D93.17 EARLY → D101.2; D93.18 LATE → D101.14 |
| Precomp output | D101.9 → D100.6 |
| Clears/triggers | WREQ_N → D97.3/.11 and D102.3/.11; D97.1/.9, D102.1/.9 and D101.13/.15 → GND |
| Timing networks | C16 on D97.15/.14; C19/R100 on D97.7/.6; C20/R108 on D102.6/.7; C22/R102 on D102.14/.15; timing resistor rail → +5 V |

## Conflict resolution

The sheet prints `R99 4.7k` for both the D97 read-stage timing resistor and the D101 output pull-up, although the assembly has one R99. Target component and solder views instead close physical R99 between D101.4/R92.1 and D101.8/GND. That observed target topology is retained.

The sheet labels a separate `R86 470` WREQ reset pull-up. Target views unambiguously place physical R86=4.7k in the four-resistor timing column, with R86.1 on C19.2/D97.6 and R86.2 on the common +5 V rail. The target identity and connectivity override the sheet annotation.

The sheet also appears to tie D101 outputs/input lines in ways contradicted by direct continuity. The model retains target-proved D101.7 → D94.14/R88 and D101.4 → R92/R99, and imports only the non-conflicting D101 precomp paths above. D101.1/.3/.5/.6, D97.13, and D102.4 remain explicit boundaries.

Primary image: `ref/photos/dgsh5-109-009-e3/PXL_20260718_101648508.jpg`. Target corroboration: `ref/photos/juku-pcb-2/PXL_20260710_200418174.jpg` and `PXL_20260710_200522685.jpg`.
