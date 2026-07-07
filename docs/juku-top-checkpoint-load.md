# juku_top checkpoint load

Status: **PASS**

This diagnostic regenerates the 30,000-write EKDOS/TDD cosim checkpoint,
loads its 64 KiB RAM image into the LVS-checked `juku_top` D84..D91
bit-sliced DRAM planes, and injects the checkpoint's visible CPU
architectural registers plus key PPI/PIC/FDC latches. It then dumps RAM
and framebuffer bytes back out of `juku_top` and compares hashes.

This is not a CPU resume proof. It proves the RAM and visible-state
halves of the future post-banner resume harness can be injected into the
real top-level model without replaying the slow ROMBIOS draw.

## Command

```sh
sync/juku_top_checkpoint_load_check.py
```

## Evidence

- Cosim trace exit code: `0`
- HDL loader exit code: `0`
- HDL RAM pass line: `yes`
- HDL state pass line: `yes`
- Cosim RAM SHA256: `eaa42964cdbc37bce58081edc085c5bcf94e95deed6454230e1aab8f1c3a38d4`
- HDL RAM SHA256: `eaa42964cdbc37bce58081edc085c5bcf94e95deed6454230e1aab8f1c3a38d4`
- Cosim VRAM SHA256: `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68`
- HDL VRAM SHA256: `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68`

## Boundary

- CPU microcycle latches are still not initialized, so the die-accurate
  core is not resumed from this state.
- Peripheral state coverage is limited to the visible latches needed at
  the 30,000-write pre-PIC boundary.
- The next resume step is either microcycle-state initialization or a
  narrower ROMBIOS subroutine harness starting from this loaded state.
