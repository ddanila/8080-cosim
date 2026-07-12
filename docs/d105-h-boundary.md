# D105 pin-10 H boundary

Status: **D105 H BOUNDARY CORRECTED / SOURCE UNRESOLVED**

The full-resolution `.006` sheet draws a named off-sheet `H` arrow into
D105 pin 10, a К155ЛА3 TTL logic input. A full-resolution sheet-2
supply table also contains `H (−5)`, disproving the earlier claim that no
H supply legend exists. Equating the two would put −5 V on a TTL input,
so this is retained as a revision/notation conflict rather than a supply
connection. The former connection also masked D2's used PROM output.

The correction removes D105.10 from −5 V in board JSON, source PCB, routed
PCB, DSN, SES, and HDL. This exposes one honest −5 V airwire in the
derived routed snapshot instead of hiding it through D105.10; replacement
copper remains a fabrication blocker. `H` remains a
singleton target-revision boundary;
the simulation low is an unresolved-input default that preserves the former
constant-low gate behavior, not a claim that H is a supply. The deep cosim
forces CPU `ready=1`, so it cannot constrain this WAIT input.

| Check | Result | Evidence |
| --- | --- | --- |
| H is a singleton D105.10 boundary | PASS | `[['D105', '10']]` |
| Derived -5 V excludes D105.10 | PASS | `[['D1', '11'], ['R19', '2'], ['VD5', '2'], ['E5', '1']]` |
| Derived -5 V remains a power net | PASS | `True` |
| Source PCB assigns D105.10 to H | PASS | `D105_10_H` |
| Source PCB has no routed segment on D105.10 | PASS | `0` |
| Routed PCB assigns D105.10 to H | PASS | `D105_10_H` |
| Routed PCB has no routed segment on D105.10 | PASS | `0` |
| DSN assigns singleton D105-10 to H | PASS | `kicad/juku.dsn` |
| SES M5V route no longer terminates at D105.10 | PASS | `kicad/juku.ses` |
| HDL exposes H as an independent low-default boundary | PASS | `hdl/juku_top.v` |

A `.037` dump supplies D2 truth but cannot identify the source or timing of
`H`. Both are required before releasing the physical WAIT chain. The routed
snapshot must also regain a DRC-clean −5 V connection before fabrication.
