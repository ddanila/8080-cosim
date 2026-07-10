# jmon33 HDL command-surface probe

Status: **JMON33 HDL FDC T-COMMAND ORACLE PINNED**

This guard starts from a generated Monitor 3.3 cosim checkpoint,
loads that RAM and visible state into `juku_top`, injects a single
command plus Enter through the `juku_top` keyboard pins, and checks the
visible command-state oracles pinned by `docs/jmon33-command-probe.md`
or `docs/jmon33-idle-command-probe.md`, depending on the checkpoint.

## Command

```sh
sync/jmon33_hdl_fdc_command_probe.py
```

Environment overrides:

- `JMON33_HDL_COMMAND_MAX_MCYC` default `120000`
- `JMON33_HDL_COMMAND_TIMECAP` default `4000000000`
- `JMON33_HDL_COMMAND_FRAMEIRQ` default `200000`
- `JMON33_HDL_COMMAND_KHOLD` default `500000`
- `JMON33_HDL_COMMAND_KGAP` default `100000`
- `JMON33_HDL_COMMAND_CHECKPOINT_CYCLES` default `19900000`
- `JMON33_HDL_COMMAND_PHASE_CHECKPOINT` default `1`
- `JMON33_HDL_COMMAND_PHASE_CHECKPOINT_CYCLES` default `26050000`
- `JMON33_HDL_COMMAND_PHASE_START_VRAM` default `210`
- `JMON33_HDL_COMMAND_HOLD_FRAMES` default `20`
- `JMON33_HDL_COMMAND_GAP_FRAMES` default `6`
- Expected checkpoint SHA256 `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
- `JMON33_HDL_COMMAND_KEY_MCYC` default `50000`
- `JMON33_HDL_COMMAND_DEFER_IFF` default `1`
- `JMON33_HDL_COMMAND_FORCE_CLEAN_STATUS` default `1`
- `JMON33_HDL_COMMAND_DISK` default `/home/ddanila/fun/8080-cosim/media/disks/JUKU1.CPM`
- `JMON33_HDL_COMMAND_TRACEFDC` default `1`
- `JMON33_HDL_COMMAND_STOPFDC` default `8`
- `JMON33_HDL_COMMAND_CASES` selected `T-enter`

## Evidence

- Cosim checkpoint exit: `0`
- Cosim checkpoint cycle: `26050000`
- Cosim checkpoint PC: `0xE43C`
- Cosim checkpoint IFF: `1`
- Cosim checkpoint VRAM writes: `290`
- Cosim checkpoint VRAM SHA256: `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`
- Phase-checkpoint mode: `yes`

| Case | Key | Checkpoint | Exit | Timed out | Keyboard samples | Active key values | Stimulus | FDC trace | Idle cursor | Command oracle | Resume line | Visible blocks | Pixels | VRAM SHA256 | Result |
| --- | --- | --- | ---: | --- | ---: | --- | --- | --- | --- | --- | --- | --- | ---: | --- | --- |
| T-enter | `T\n` | `cyc=26050000 pc=0xE43C iff=1 kbd=2/0` | `0` | `False` | `0` | - | - | `[RESUME-FDC] IN  port=0x1c reg=0 data=0x40 mcyc=422 vram=290 ios=1`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x40 mcyc=430 vram=290 ios=2`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x40 mcyc=438 vram=290 ios=3`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x40 mcyc=446 vram=290 ios=4`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x40 mcyc=454 vram=290 ios=5`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x40 mcyc=462 vram=290 ios=6`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x40 mcyc=470 vram=290 ios=7`<br>`[RESUME-FDC] IN  port=0x1c reg=0 data=0x40 mcyc=478 vram=290 ios=8` | `yes` | `none` | `none` | `x=8,y=20` | `80` | `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397` | FAIL |

## Disposition

- The HDL checkpoint harness now has a generic two-key command stimulus
  path in addition to the fixed EKDOS `TDD` stimulus path.
- The default checkpoint is the monitor-idle cursor state. A later
  `JMON33_HDL_COMMAND_KEY_MCYC` delay lets the resumed keyboard scan
  settle before the command key is pressed.
- `JMON33_HDL_COMMAND_PHASE_CHECKPOINT=1` generates a per-case
  cosim checkpoint with the command key already in the monitor
  keyboard schedule, scales that frame phase into HDL M-cycles,
  and resumes through the remaining key/Enter path.
- The default checkpoint is deliberately before the 20,000,000-cycle
  ready-probe stop, because that stop is visually idle but lands in
  the frame interrupt vector (`PC=0xFF54`, `IFF=0`).
- The default checkpoint is the monitor-idle cursor state, so the
  default expected command hashes come from
  `docs/jmon33-idle-command-probe.md`, not from reset-time typed
  command runs.
- The current HDL rows are diagnostic until their final command
  framebuffers match the selected cosim oracle.
- The `Idle cursor` column checks whether the monitor-idle cursor
  block from the checkpoint survived into the final framebuffer.
- This proof is scoped to jmon33 monitor commands. Cartridge BASIC remains
  tracked by `docs/cartridge-basic-boundary.md`.

## FDC-Specific Disposition

- This wrapper intentionally stops on the FDC trace boundary, so the generic
  command framebuffer result remains `FAIL`/diagnostic.
- The pass condition is the structural `juku_top` path reading status `0x40`
  from the disk-backed FDC after the Monitor 3.3 `T` command has entered
  the write-track/write-protect polling loop.
- This matches the cosim oracle in `docs/jmon33-fdc-command-probe.md` and
  removes the previous ambiguity that the HDL `T` path was merely a
  keyboard-phase mismatch.
