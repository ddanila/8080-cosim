# D6 input continuity correction

Status date: 2026-07-14

Status: **D6 A5/A6 MEASURED / A7 SOURCE BOUNDARY**

Direct continuity measurements on a physical `.009` processor board correct
the older-sheet assignment of D6's three high address inputs. The measurements
were accompanied by a visual copper trace where noted by the owner.

## Confirmed routes

```text
D26.15 PC1 --+-- D3.3 -> inverter -> D3.4 -- D6.1  A6
             +-- resistor pull-up -> +5 V

D26.14 PC0 --+-- D3.5 -> inverter -> D3.6 -- D6.2  A5
             +-- resistor pull-up -> +5 V

D6.15 A7 ------------------------------ D105.1
```

`D6.1 <-> D3.4` was reported as zero ohms and its copper was followed
visually. Direct continuity also proves `D6.2 <-> D3.6`, `D3.3 <-> D26.15`,
`D3.5 <-> D26.14`, and `D6.15 <-> D105.1`. The pull-up resistor references
and values at D3.3 and D3.5 were not identified.

The resulting proved D6 address order is:

```text
A0..A7 = BA15, BA14, BA13, BA12, BA11, /PC0, /PC1, unresolved A7 source
```

## Explicit negative evidence

- D6.1 does not connect to D26; the older D26.17/PC3 assignment is rejected.
- D6.2 does not connect to any D26 pin; the older D26.16/PC2 assignment is
  rejected.
- D6.15 does not connect to any D26 pin; the older D26.13/PC4/FDC-density
  assignment is rejected.
- D105.1 does not connect to D105.12.
- The separately reconfirmed write-strobe net remains
  `D105.12 <-> D105.13 <-> D5.26`.

No continuation beyond the two input endpoints `D6.15 <-> D105.1` was found.
Because both endpoints are inputs, the driver, pull source, or obscured branch
remains a continuity boundary. The model must not merge it with MEMW or FDC
density merely to supply a functional value.

## Modeling consequence

The structural model now routes D26 PC1 and PC0 through the measured D3
inverters before D6 A6 and A5. D6 A7 and D105.1 share an explicit boundary.
The separately named runnable memory-decode oracle remains in place until the
A7 source and the downstream D6/D13/D37/D58 path are physically closed and
boot/checkpoint guards pass from the physical topology.
