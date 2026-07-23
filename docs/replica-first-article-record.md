# Replica first-article acceptance record

Status: **TEMPLATE / NO PHYSICAL UNIT AUTHORIZED**

Use one copy of this record per fabricated and assembled board. Do not fill it
from simulation, a vendor preview, or another unit. Preserve raw meter, scope,
logic-analyzer, terminal, programmer, and photograph artifacts beside the
completed record.

## Identity and released baseline

| Field | Recorded value |
| --- | --- |
| Unit serial / label | - |
| Bare-board order and quantity | - |
| Bare-board received date | - |
| Source commit | - |
| Released PCB SHA256 | - |
| Upload ZIP SHA256 | - |
| BOM revision / SHA256 | - |
| Assembly configuration | functional Tier 1/2 / historical Tier 3 / other: - |
| D2 / D6 / D8 / D94 image SHA256s | - |
| D15 / D16 image SHA256s | - |
| Jumper and switch configuration | - |
| Approved deviations / waivers | none / - |

## Parts, handling, and workmanship

- [ ] Incoming parts were inventoried by reference group, seller/lot, marking,
      and acceptance result; rejected or suspect parts were quarantined.
- [ ] Static-sensitive parts were stored, handled, and installed using the
      documented ESD controls.
- [ ] Socket, connector, polarized-part, and IC pin-1 orientation received a
      second-person or independent photo review before power.
- [ ] Solder joints, factory-wire equivalents, cuts/links, contamination, and
      unintended bridges received documented visual inspection.
- [ ] Every rework, substituted part, lifted pad, bodge wire, and DNP difference
      is listed in the deviation table below.

## Test equipment and environment

| Instrument / fixture | Model or identifier | Calibration / confidence check | Settings or firmware |
| --- | --- | --- | --- |
| Bench supply | - | - | - |
| DMM | - | - | - |
| Oscilloscope | - | - | - |
| Logic analyzer | - | - | - |
| PROM/EPROM programmer | - | - | - |
| Display / video cable | - | - | - |
| Keyboard / cable | - | - | - |
| Floppy drive or emulator / cable | - | - | - |
| Serial adapter / cable | - | - | - |

Ambient temperature and relevant setup notes: -

## Pre-power inspection

- [ ] The received outline, holes, layers, finish, drills, silk, and connector
      orientation agree with the released package and saved vendor preview.
- [ ] All rails and ground paths pass resistance/short checks with no ICs
      seated.
- [ ] Connector polarity and every externally supplied rail are independently
      checked at the board contact.
- [ ] Current limits and stop thresholds are written into the session record
      before energizing the board.
- [ ] The first energization uses the staged no-IC configuration from
      `PLAN.md`; no peripheral is attached early merely for convenience.

## Physical verification matrix

Fill numeric expectations before each test. A result is not PASS without a raw
evidence path and a named product configuration.

| ID | Configuration and method | Expected / limits | Result | Evidence |
| --- | --- | --- | --- | --- |
| `T1-PWR` | - | - | NOT RUN | - |
| `T1-BOOT` | - | - | NOT RUN | - |
| `T1-VIDEO` | - | - | NOT RUN | - |
| `T1-KBD` | - | - | NOT RUN | - |
| `T2-SW` | - | - | NOT RUN | - |
| `T2-FDC` | - | - | NOT RUN | - |
| `T2-IO` | - | - | NOT RUN | - |
| `T2-PSU` | - | - | NOT RUN | - |
| `T3-FID` | - | - | NOT RUN | - |

## Deviations, discrepancies, and rework

Stop the affected verification when observed. Record the configuration and raw
evidence before disturbing the setup, then disposition the product, procedure,
or expectation explicitly.

| ID | Observation | Affected requirement/configuration | Disposition and authority | Retest evidence |
| --- | --- | --- | --- | --- |
| - | - | - | - | - |

## Acceptance

| Decision | Value |
| --- | --- |
| Highest tier passed | none / Tier 1 / Tier 2 / Tier 3 |
| Open discrepancies | - |
| Restrictions on use | - |
| Accepted source commit and as-built configuration | - |
| Owner decision, name/date | - |

An accepted first article validates only the recorded configuration. Any later
source, programmed-image, part, jumper, rework, or procedure change must be
evaluated for targeted reverification; later fabricated units receive their own
acceptance record.
