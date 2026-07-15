# Package endpoint coverage

Status: **NON-POWER PACKAGE CONTRACTS COMPLETE**

The board JSON keeps many physical supply pads on tagged PCB power nets while
HDL-facing package maps omit those supply pins. This is an explicit modeling
convention, not an unowned-pad condition. Every signal/control/off-board endpoint
must still be declared in its chip contract; the report fails otherwise.

## Summary

- Undeclared non-power endpoints: `0`
- Undeclared explicit no-connect pins: `0`
- HDL-excluded physical power endpoints: `107` across `52` refs

| Tagged power net | Endpoints intentionally outside HDL pinmaps |
| --- | ---: |
| `GND` | 53 |
| `M12V` | 2 |
| `P12V` | 2 |
| `P5V` | 50 |

## Checks

| Check | Result |
| --- | --- |
| Every modeled non-power endpoint is declared by its chip/package | PASS |
| Every explicit no-connect exists in its chip/package | PASS |
| S1 off-board SPDT contact 3 is explicitly declared | PASS |
| Remaining undeclared endpoints belong only to tagged PCB power nets | PASS |
