# D2 READY polarity simulation check

Status: **CAPTURED D2 RAW POLARITY GUARDED IN HDL**

This focused HDL bench loads the captured `.037` table into an open-collector
PROM model. It checks that address `00` sinks `READY_D`, address `80` (raw `F`)
releases the modeled pull-up, and either disabled enable releases all outputs.
D30 section A samples the low and released levels on `PHI2TTL`; its asynchronous
controls are held inactive in this bench.

```sh
sync/d2_ready_path_check.sh
```

The acquisition and independent D2.12-to-D30.2/R6 continuity evidence are
recorded in [D2 physical truth](d2-physical-truth.md). This bench checks the
model's sampling polarity; it does not measure hardware or exercise the
D38 status strobe, H/DBIN gating, or complete cycle-by-cycle WAIT duration.
See [memory timing](memory-timing-boundary.md) for the remaining boundary.
