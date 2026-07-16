# D2 physical READY path check

Status: **PHYSICAL D2 RAW POLARITY EXECUTES THROUGH D30**

This focused HDL guard executes the validated `.037` table as a physical
open-collector PROM. It proves raw row `00` sinks `READY_D` low, raw row `80`
(`F`) releases the modeled R6 pull-up high, either disabled enable releases all
outputs, and D30 section A latches each resulting level on `PHI2TTL`.

```sh
sync/d2_ready_path_check.sh
```

The used D0/pin12 reader channel was Nano D10, not the Nano D13 LED-loaded
channel implicated in the D6 D3 re-read. Direct continuity independently puts
D2.12 on D30.2 and the R6 pull-up. These facts pin D2's raw electrical polarity.
X1.107B/-BLOCK and R1 now close the `H` edge contact; this guard still does not
prove the complete cycle-by-cycle WAIT duration around that edge.
