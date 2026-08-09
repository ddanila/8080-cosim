# CS00015 D55 substitution runbook and evidence record

Status: **HOLD — RUN T34 BEFORE SUBSTITUTION**

This is the controlled before/substitute/after procedure if the corrected T34
functional-path test first reproduces a CS00015 D55-path failure. D55 is the
middle КР580ВИ53/8253 and supplies vertical video and frame timing.

The 2026-08-09 desk audit invalidated T15/T16/T31/T32 as D55 evidence. They
latched newly written Mode-0 counts without establishing the D54/D56 clocks
required by a real 8253. Do not remove or substitute D55 on the strength of
those historical codes. See
[`../../docs/jukuravi-d55-diagnostic-audit.md`](../../docs/jukuravi-d55-diagnostic-audit.md).

Do not combine this run with D4/D30 rework, PROM substitution, Nano wiring, or
main-board P0 continuity changes. Change one variable: D55.

## Exact diagnostic media

| Label | Image | Size | Version | SHA-256 |
| --- | --- | ---: | ---: | --- |
| T34 | `firmware/diag-d0-clocked-pit.bin` | 8,192 bytes | `1C` / CRC `A637` | `63f69281e632324083bd5e7040d19a7939936b98a4d5cb245e008ea491d45cb5` |

Before programming or fitting either image:

```sh
sha256sum spinoffs/jukuravi/firmware/diag-d0-clocked-pit.bin
python3 spinoffs/jukuravi/firmware/build_d0_clocked_pit.py --check
sync/jukuravi_d55_clock_audit.sh
```

Record programmer model, adapter, device type, erase/program/verify result,
and the read-back SHA-256 below. Label the medium `T34HOST`.

## Result key

Use the T34 host report and retain its JSON/raw serial capture. The exact ROM
identity is `1C/A637`. Diagnostic bit `08` means **D55 functional path failed**;
it does not mean “D55 package bad.” PIC, PPI, D54 and D57 have bits `01`, `02`,
`04` and `10`. A clean T34 result clears the tested path and cancels this
substitution run. A repeated `08` authorizes the controlled discriminator
below, while retaining D9, socket/power, local bus and D54/D56 clocks as
alternative causes.

## Controlled procedure

### 1. Freeze the starting configuration

- Photograph the board, D55 orientation/notch, adjacent socket and bypass
  area, diagnostic ROM label, jumpers, cables, and PSU connections.
- Record the fitted D55 marking, lot/date code, package condition, socket type,
  board serial `CS00015`, PSU settings, ambient temperature, and operator.
- Verify the exact T34 hash, `1C/A637` identity and diagnostic-media readback.
- With the original D55 still fitted, perform **three cold-power T34 runs**.
  Preserve every host JSON/raw capture. Stop the substitution plan if all three
  report a clean D55 path.

### 2. Inspect without altering the diagnosis

- Remove power and all external cables; wait for rails to discharge and use
  ESD-safe handling.
- Extract D55 without levering adjacent packages or repeatedly disturbing D6,
  D8, D1, or the diagnostic ROM.
- Photograph D55 pins and the empty socket. Record bent, oxidized, recessed,
  spread, contaminated, cracked, or heat-discolored contacts.
- Visually inspect the local socket solder joints and bypass component. Do not
  reflow, clean aggressively, bend contacts, or replace other parts during the
  substitution discriminator. If safe insertion is not possible, stop.

### 3. Substitute exactly one known-good PIT

- Record donor/source identity, complete marking, provenance, prior test
  result, and whether the part is КР580ВИ53, 8253, or a deliberately accepted
  compatible 8254.
- Confirm pin 1/notch orientation twice, seat the package evenly, restore the
  unchanged T34 configuration, and photograph the installed substitute.
- Apply power under the same PSU settings. Stop immediately for excess current,
  heat, smell, missing alive tone, or behavior outside the known diagnostic
  envelope.

### 4. Require repeatable post-substitution evidence

- Perform **five cold-power T34 runs**. All five must report D55 clear while
  retaining clean D54 and D57 results.
- Run the standard EKTA 3.7 or JMON 3.3 configuration and verify its normal
  video/frame behavior. This is a functional regression, not the package
  discriminator by itself.
- Preserve raw serial/video evidence and one written row per run. Do not
  discard anomalous repeats.

## Decision and rollback criteria

Classify the result only after the complete repetition matrix:

| Outcome | Disposition |
| --- | --- |
| Original repeats T34 `08`; substitute clears D55 in 5×T34 and standard video/frame behavior is normal | D55 package fault confirmed for the tested path; retain original bagged/labeled and leave the proven substitute fitted |
| Substitute produces any T34 D55-path failure | D55 package alone is not confirmed; power off, preserve both parts/configurations, inspect select/socket/supply/bus/D54/D56 evidence, and do not rework another circuit |
| Missing alive tone, new earlier code, excess current, or abnormal heating | Immediate rollback: power off, verify orientation/media/configuration, photograph state, and return to the last electrically safe configuration |
| Original cannot be retested or substitute provenance is weak | Record the limitation; classify as improved/unchanged behavior, not a confirmed package diagnosis |

Rollback means restoring the last safely documented package/configuration only
when extraction and reinsertion are mechanically safe. It never authorizes
unrelated rework. Preserve the removed original in ESD-safe packaging labeled
`CS00015 D55`, date, orientation, and observed T34 results.

## Evidence record template

### Session identity

| Field | Recorded value |
| --- | --- |
| UTC date/time | |
| Operator / location | |
| Board / serial | `CS00015` |
| PSU model, limits, measured rails | |
| Ambient temperature | |
| Diagnostic ROM/programmer/adapter | |
| T34 programmed/read-back SHA-256 | |
| T34 version / self-CRC16 | `1C` / `A637` |

### Component and socket provenance

| Field | Original D55 | Substitute D55 |
| --- | --- | --- |
| Full body marking | | |
| Manufacturer / type | | |
| Lot/date code | | |
| Source/donor inventory ID | `CS00015 fitted` | |
| Prior known-good evidence | historical unverified path result | |
| Pin/package condition | | |
| Orientation photo | | |

Empty-socket and local-area observations:

```text

```

### Run matrix

Use `clear` only when the exact `1C/A637` T34 host report has no D55 bit.
Retain the JSON/raw capture for every row.

| Phase | Image | Cold run | ROM identity | D54/D55/D57 | JSON/raw evidence | Notes |
| --- | --- | ---: | --- | --- | --- | --- |
| original | T34 | 1 | | | | |
| original | T34 | 2 | | | | |
| original | T34 | 3 | | | | |
| substitute | T34 | 1 | | | | |
| substitute | T34 | 2 | | | | |
| substitute | T34 | 3 | | | | |
| substitute | T34 | 4 | | | | |
| substitute | T34 | 5 | | | | |
| substitute | EKTA/JMON video | 1 | n/a | | | |

### Final disposition

| Field | Recorded value |
| --- | --- |
| Outcome classification | |
| D55 package fault confirmed? | YES / NO / INCONCLUSIVE |
| Package left fitted | |
| Original storage label/location | |
| Rollback performed and why | |
| New discrepancy opened | |
| Evidence paths committed | |
| Reviewer/date | |

Free-form observations:

```text

```
