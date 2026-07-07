# juku_top checkpoint load

Status: **PASS**

This diagnostic regenerates the 30,000-write EKDOS/TDD cosim checkpoint
and loads its 64 KiB RAM image into the LVS-checked `juku_top` D84..D91
bit-sliced DRAM planes. It then dumps RAM and framebuffer bytes back out
of `juku_top` and compares hashes.

This is not a CPU resume proof. It proves the RAM half of the future
post-banner resume harness can be injected into the real top-level DRAM
representation without replaying the slow ROMBIOS draw.

## Command

```sh
sync/juku_top_checkpoint_load_check.py
```

## Evidence

- Cosim trace exit code: `0`
- HDL loader exit code: `0`
- HDL pass line: `yes`
- Cosim RAM SHA256: `eaa42964cdbc37bce58081edc085c5bcf94e95deed6454230e1aab8f1c3a38d4`
- HDL RAM SHA256: `eaa42964cdbc37bce58081edc085c5bcf94e95deed6454230e1aab8f1c3a38d4`
- Cosim VRAM SHA256: `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68`
- HDL VRAM SHA256: `0b94d9d02f9c53bdd86f6f0be9921253eb3f99400ee00e62203eeac17eda1c68`

## Boundary

- CPU architectural and microcycle state is still not injected.
- Peripheral register state is still tracked by the cosim checkpoint
  reference and by direct-bus top-level guards, not by this RAM-load test.
- The next resume step is a deliberately instrumented CPU-state loader or
  a narrower ROMBIOS subroutine harness starting from this loaded RAM.
