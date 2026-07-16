# Physical D2 `.037` truth

Status: **PHYSICAL READY TRUTH CLASSIFIED AND GUARDED**

This generated report reduces the preserved D2 КР556РТ4 image to an exact
piecewise condition over its eight traced inputs. It describes raw electrical
levels; D0/pin12 is an open-collector input to the pulled-up D30 READY latch.

## Guarded artifact

- Raw image: `ref/physical-proms/validated/d2_037.raw.bin` (256 bytes)
- SHA256: `953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b`
- Index order, MSB to LSB: `WREQ_N, A10, XACK_N, A14, CAS, A9, A15, A12`
- Four-bit raw `F` (all outputs released/high): 86 rows
- Four-bit raw `0` (all outputs pulled low): 170 rows

All four physical outputs are identical at every address. Only D0/pin12 has
a proved board destination; the factory symbol makes pins 9-11 explicit no-connects.

## Exact piecewise classification

The raw output is `0` whenever `WREQ_N=0`. For `WREQ_N=1`:

| Condition | Raw output |
| --- | --- |
| `A10=0` and `A9=0` and `CAS=A12` and `A15!=A12` | `0` |
| `A10=0`, all other combinations | `F` |
| `A10=1` and `XACK_N=1` | `0` |
| `A10=1`, `XACK_N=0`, and `A14=1` | `F` |
| `A10=1`, `XACK_N=0`, `A14=0`, `A9=1`, `A15=1`, `A12=0` | `0` |
| `A10=1`, `XACK_N=0`, `A14=0`, all other combinations | `F` |

The classifier above is evaluated against all 256 preserved rows on every
report refresh. `CAS` is a don't-care in the `A10=1` half; `XACK_N` and
`A14` are don't-cares in the `A10=0` half.

## Executed READY polarity

The used physical D0/pin12 channel was sampled on Nano D10. The known
Nano D13 LED load affected only D3/pin9, which is an intentional no-connect
on the board. D0 also had its own external pull-up during capture, and direct
continuity puts it on board pull-up R6 and D30.2. The physical D0 raw sense is
therefore independent of the pending D6 D3 re-read.

`sync/d2_ready_path_check.sh` executes the preserved table through an
open-collector `wait_prom_037` and functional D30 section A. It guards:

- raw row `00` sinks `READY_D` and latches D30/READY low;
- raw row `80` (`F`) releases the pull-up and latches READY high; and
- disabling either PROM enable releases all outputs high.

## READY timing boundary

- Raw `0` means the open-collector D2 output actively pulls `READY_D` low.
- Raw `F` releases D0/pin12, allowing R6 to pull `READY_D` high.
- D30's raw level and sampling polarity are now executable and guarded.
  The `H` edge contact and R1 pull-up are now source-closed; complete
  cycle-by-cycle WAIT duration still depends on surrounding clock/control timing.
- Pins 9-11 remain physically programmed and were captured by the reader, but
  the factory symbol draws no external stubs; they are intentional no-connects
  and must not acquire PCB nets merely because their truth matches D0.
