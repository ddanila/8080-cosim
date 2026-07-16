# VJUGA simulation

`check.sh` is the experiment's aggregate check. It currently runs:

- the main replica's real-ROM boot regression, which guards shared repository
  code;
- the VJUGA T80 real-ROM boot against the cosim framebuffer oracle;
- the tv80 VJUGA twin boot in both real-РТ4 and GAL-internal decode modes;
- a T80/VJUGA synthetic-ROM smoke test;
- logical HDL/KiCad structural comparison;
- Rev A source/PCB invariant and DRC checks; and
- the shared 4164-style DRAM unit test.

The VJUGA smoke program separately writes and reads RAM, exercises I/O, observes refresh
and video arbitration, samples keyboard-style input, and advances VGA timing.
The two boot checks prove the patched Juku ROM mapping and framebuffer write
stream in simulation; they do not prove the physical board or a banner rendered
through the shared-DRAM VGA output path.

The U24 DRAM-timing GAL reference is now guarded against the slower vendored
MK4564-12 limits at 4 MHz. The next milestones are device-specific GAL
compilation/programming and rendering the real-ROM framebuffer through the VGA
path. Aggregate success still means "simulation and package invariants pass,"
not "physical board works."
