# juku_top checkpoint resume probe

Status: **PASS**

This probe regenerates the 30,000-write EKDOS/TDD cosim checkpoint,
loads its RAM image into the `juku_top`, seeds CPU/PPI/PIC/FDC
latches from testbench defaults, and starts the vm80a core at a clean M1
fetch boundary. The runner does not import the generated `.state` file.

The pass condition is deliberately narrow: reach the first post-checkpoint
ROMBIOS PIC programming event and the no-key keyboard poll through the
actual decoded top-level ports: a PIC command-register write of `0xd6`
and a PPI0 port-B read of `0xcf`. The bench checks chip selects, register
address bits, and data; it does not require particular PC values or event
cycle counts. It is not an EKDOS prompt proof.

## Command

Run with Python 3, a C compiler (`CC`, default `cc`), and Icarus Verilog
(`iverilog` and `vvp`). The runner overwrites this report and uses a temporary
directory for builds and checkpoint files. It restores `cosim/vram.bin`
after checkpoint capture completes normally.

```sh
sync/juku_top_checkpoint_resume_probe.py
```

Connectivity is checked by the separate [LVS guard](../sync/README.md).
This runner does not invoke it.

## Evidence

- Cosim checkpoint exit code: `0`
- HDL resume exit code: `0`
- Resume pass line: `JUKU-TOP-CHECKPOINT-RESUME: PASS pc=0x1213 mcyc=25744 vram=30321 ios=26`
- First PIC line: `[RESUME-PIC] OUT port=0x00 data=0xd6 mcyc=25615 vram=30321 pc=0x02b9`
- First keyboard IN line: `[RESUME-KBD] IN port=0x05 data=0xcf mcyc=25744 vram=30321 pc=0x1213`
- Stop/fail line: `none`

## Boundary

- This remains a checkpoint-resume diagnostic, not the full `TDD` to `A>`
  CPU path.
- The seeded core state intentionally starts from an instruction-fetch
  boundary rather than a transistor-exact mid-instruction microstate.
- The HDL workflow runs this probe when its FDC lane is selected by
  changed paths, schedule, or manual dispatch. Deeper checkpoint-resumed
  FDC and prompt paths remain local
  because they exceed the hosted time budget.
- Set `JUKU_TOP_CHECKPOINT_TRACE_RESUME=N` to include the first `N`
  resumed machine-cycle boundaries in this report.
