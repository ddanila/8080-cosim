# VJUGA simulation

`check.sh` is the experiment's aggregate check. It currently runs:

- the main replica's real-ROM boot regression, which guards shared repository
  code but does **not** execute the VJUGA design;
- a T80/VJUGA synthetic-ROM smoke test;
- logical HDL/KiCad structural comparison;
- Rev A source/PCB invariant and DRC checks; and
- the shared 4164-style DRAM unit test.

The VJUGA smoke program writes and reads RAM, exercises I/O, observes refresh
and video arbitration, samples keyboard-style input, and advances VGA timing.
It does not prove the Juku ROM mapping, firmware boot, or visible prompt.

The next meaningful simulation milestone is a real Juku ROM boot on the VJUGA
T80 top with a framebuffer/VGA-side oracle. Until that exists, aggregate check
success means "current smoke and package invariants pass," not "board works."
