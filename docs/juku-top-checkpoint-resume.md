# juku_top checkpoint resume probe

Status: **PASS**

This probe regenerates the 30,000-write EKDOS/TDD cosim checkpoint,
loads its RAM image into the LVS-checked `juku_top`, injects the
visible CPU/PPI/PIC/FDC latches, seeds the vm80a core at a clean M1
fetch boundary, and lets the real top-level bus run forward.

The pass condition is deliberately narrow: reach the first post-checkpoint
ROMBIOS PIC programming event and the no-key keyboard poll through the
actual decoded top-level ports. It is not an EKDOS prompt proof.

## Command

```sh
sync/juku_top_checkpoint_resume_probe.py
```

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
- This probe is a mandatory push-CI guard for the post-checkpoint
  PIC/keyboard resume boundary; deeper checkpoint-resumed FDC and
  prompt paths remain local/deep guards because they are too slow for
  shared runners.
- Set `JUKU_TOP_CHECKPOINT_TRACE_RESUME=N` to include the first `N`
  resumed machine-cycle boundaries in this report.
