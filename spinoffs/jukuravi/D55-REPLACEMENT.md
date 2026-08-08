# CS00015 D55 substitution runbook and evidence record

Status: **READY FOR OWNER BENCH ACTION**

This is the controlled before/substitute/after procedure for the remaining
known CS00015 fault. D55 is the middle КР580ВИ53/8253 and supplies vertical
video timing. Existing T15/T16 evidence strongly localizes intermittent and
recovery-spaced readback failures to D55, but substitution is required to
distinguish the package from its socket, bypass, supply, and local wiring.

Do not combine this run with D4/D30 rework, PROM substitution, Nano wiring, or
main-board P0 continuity changes. Change one variable: D55.

## Exact diagnostic media

| Label | Image | Size | Version | SHA-256 |
| --- | --- | ---: | ---: | --- |
| T15 | `firmware/diag-d0-pit-debug-slow.bin` | 8,192 bytes | `0C` | `34c110f209e7ccfffb3a261bea25b3b2e9d361eaaad57bcde638d744e8eed72a` |
| T16 | `firmware/diag-d0-d55-stress.bin` | 8,192 bytes | `0D` | `703514bd36ea3fb1c695b91259040571d601880f475f4562698c851ffbdfd0ce` |

Before programming or fitting either image:

```sh
sha256sum spinoffs/jukuravi/firmware/diag-d0-pit-debug-slow.bin \
  spinoffs/jukuravi/firmware/diag-d0-d55-stress.bin
python3 spinoffs/jukuravi/firmware/build_d0_pit_debug_slow.py --check
python3 spinoffs/jukuravi/firmware/build_d0_d55_stress.py --check
```

Record programmer model, adapter, device type, erase/program/verify result,
and the read-back SHA-256 below. Keep T15 and T16 on separately labeled media.

## Audible result key

Both images begin with the approximately 0.5-second nominal 1 kHz alive tone.
Clean success is three long nominal 2 kHz pulses followed by silence.

T15 failure reports 0.25-second 2 kHz count pulses, with an extra separator
after each group of five, then a continuous nominal 125 Hz tail:

| Pulses | First failed checkpoint |
| ---: | --- |
| 1–4 | D54 channels 0/1/2 high, then channel 0 low |
| 5 | D55 channel 0 high |
| 6 | D55 channel 1 high |
| 7 | D55 channel 2 high |
| 8 | D55 channel 0 low |
| 9–12 | D57 channels 0/1/2 high, then channel 0 low |

T16 checks only D55, repeating each predicate 32 times with recovery spacing:

| Pulses | First failed checkpoint |
| ---: | --- |
| 1 | D55 channel 0 high |
| 2 | D55 channel 1 high |
| 3 | D55 channel 2 high |
| 4 | D55 channel 0 low |

The established fitted-D55 signature is T16 code 3. A single success is not
enough to close an intermittent fault.

## Controlled procedure

### 1. Freeze the starting configuration

- Photograph the board, D55 orientation/notch, adjacent socket and bypass
  area, diagnostic ROM label, jumpers, cables, and PSU connections.
- Record the fitted D55 marking, lot/date code, package condition, socket type,
  board serial `CS00015`, PSU settings, ambient temperature, and operator.
- Verify the exact T15/T16 hashes and diagnostic-media readback.
- With the original D55 still fitted, perform **three cold-power T16 runs** and
  **three cold-power T15 runs**. Record every complete cadence; do not summarize
  variable results as a single code.

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
  unchanged T16 configuration, and photograph the installed substitute.
- Apply power under the same PSU settings. Stop immediately for excess current,
  heat, smell, missing alive tone, or behavior outside the known diagnostic
  envelope.

### 4. Require repeatable post-substitution evidence

- Perform **five cold-power T16 runs**. All five must produce the three-pulse
  success cadence and silence.
- Perform **three cold-power T15 runs**. All three must produce the same clean
  success cadence and silence.
- Run one T31 or T32 cold-boot smoke test to confirm the normal diagnostic
  ladder/loader still reaches its previously proven state. This is a regression
  check, not a new D55 discriminator.
- Preserve raw audio/video when practical and one written row per run. Do not
  discard anomalous repeats.

## Decision and rollback criteria

Classify the result only after the complete repetition matrix:

| Outcome | Disposition |
| --- | --- |
| Original reproduces a D55 code; substitute passes 5×T16 + 3×T15 and smoke test | D55 package fault confirmed; retain original bagged/labeled and leave the proven substitute fitted |
| Substitute produces any T15/T16 failure code | D55 package alone is not confirmed; power off, preserve both parts/configurations, inspect socket/supply/bypass evidence, and do not rework another circuit |
| Missing alive tone, new earlier code, excess current, or abnormal heating | Immediate rollback: power off, verify orientation/media/configuration, photograph state, and return to the last electrically safe configuration |
| Original cannot be retested or substitute provenance is weak | Record the limitation; classify as improved/unchanged behavior, not a confirmed package diagnosis |

Rollback means restoring the last safely documented package/configuration only
when extraction and reinsertion are mechanically safe. It never authorizes
unrelated rework. Preserve the removed original in ESD-safe packaging labeled
`CS00015 D55`, date, orientation, and observed T15/T16 codes.

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
| T15 programmed/read-back SHA-256 | |
| T16 programmed/read-back SHA-256 | |

### Component and socket provenance

| Field | Original D55 | Substitute D55 |
| --- | --- | --- |
| Full body marking | | |
| Manufacturer / type | | |
| Lot/date code | | |
| Source/donor inventory ID | `CS00015 fitted` | |
| Prior known-good evidence | established failure | |
| Pin/package condition | | |
| Orientation photo | | |

Empty-socket and local-area observations:

```text

```

### Run matrix

Use `success` only for three long 2 kHz pulses followed by silence. Otherwise
record the exact pulse count/tail or attach the raw observation.

| Phase | Image | Cold run | Alive tone | Result/cadence | Audio/video evidence | Notes |
| --- | --- | ---: | --- | --- | --- | --- |
| original | T16 | 1 | | | | |
| original | T16 | 2 | | | | |
| original | T16 | 3 | | | | |
| original | T15 | 1 | | | | |
| original | T15 | 2 | | | | |
| original | T15 | 3 | | | | |
| substitute | T16 | 1 | | | | |
| substitute | T16 | 2 | | | | |
| substitute | T16 | 3 | | | | |
| substitute | T16 | 4 | | | | |
| substitute | T16 | 5 | | | | |
| substitute | T15 | 1 | | | | |
| substitute | T15 | 2 | | | | |
| substitute | T15 | 3 | | | | |
| substitute | T31/T32 smoke | 1 | n/a | | | |

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
