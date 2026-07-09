# juku_top 30,520-write reachability probe

Status: **TIMEOUT BEFORE HDL DUMP**

This note records the attempted brute-force top-level probes immediately past
the proven 30,000-write checkpoint on the vendored `JUKU1.CPM` `TDD` path.

## Evidence

| Probe | Bound | Result |
| --- | --- | --- |
| `JUKU_TOP_FDC_STOPPC=02B9 sync/juku_top_fdc_probe.sh` | 360 seconds | Timed out after the 30,000-write progress line; no PC stop, PIC trace, or FDC trace. |
| `JUKU_TOP_30000_WRITES=30520 ./sync/juku_top_30000_state_probe.sh` | 900 seconds | Cosim reached 30,520 writes at PC `0x031C`, but HDL did not reach the dump point before timeout. |

The second run produced no HDL CPU/state line, so it is not evidence of a
functional mismatch. It is only reachability evidence: brute-force top-level
execution past the 30,000-write checkpoint is no longer a practical automatic
loop.

## Disposition

This is now a historical reachability boundary. The follow-up checkpoint and
uninterrupted Verilator prompt guards cover the first PIC/PPI/FDC and EKDOS
`A>` path; the useful lesson here is still not to grow the brute-force
Icarus timeout for this window.
