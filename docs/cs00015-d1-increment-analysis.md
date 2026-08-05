# CS00015 D1 bit-12 increment diagnosis

Status: functionally confirmed on hardware and reproduced in the die-derived
vm80a HDL model.

## Physical signature

The T32 direct-register probe avoids every high-address memory access and
copies its results to low-A12 RAM. CS00015 returned:

| Operation | Correct | Physical |
| --- | --- | --- |
| `INX B`, `0FFFh` | `1000h` | `1000h` |
| `INX D`, `1A00h` | `1A01h` | `0A01h` |
| `INX H`, `5A00h` | `5A01h` | `4A01h` |
| `INX SP`, `9A00h` | `9A01h` | `8A01h` |
| `DAD D`, `1A00h + 1` | `1A01h` | `1A01h` |

Earlier LHLD, POP, SHLD, PC, and indirect-INX experiments show the same rule.
Exact ROM reads in every reconstructed D2 wait class also fail identically.

## Shared vm80a register unit

The vendored die-derived core models six 16-bit register paths: PC, the
HL/DE pair, BC, SP, and WZ. They share one address latch and one increment/
decrement result, `mxi`, before writeback. DAD uses the separate 8-bit ALU.
See `hdl/vendor/vm80a.v`, register-unit section.

For incrementing bit 12, define carry from the lower twelve bits as:

```text
C12 = A0 & A1 & ... & A11
S12 = A12 XOR C12
    = (!A12 & C12) | (A12 & !C12)
```

The physical cases distinguish the two terms:

- `0FFF -> 1000`: `A12=0`, `C12=1`; `!A12 & C12` works.
- `1A00 -> 1A01`: `A12=1`, `C12=0`; `A12 & !C12` is missing.
- DAD `1A00 + 1`: the separate ALU retains bit 12.

The bounded internal diagnosis is therefore loss of the bit-12
retain-high/no-carry term in D1's shared 16-bit increment path. It is not an
A12 register cell stuck low: direct loads and DAD retain A12. It is not one
register: BC, DE, HL, SP, PC, and WZ-related operations share the symptom.

## HDL reproduction

The local diagnostic parameter `FAULT_A12_INCREMENT_HIGH_LOSS` removes only
that product term while leaving carry into A12, decrement, direct loads, and
DAD untouched. `sync/jukuravi_vm80a_a12_check.sh` runs the same 81-byte probe
through the die-derived core in both modes:

```text
clean: 1000 1A01 5A01 9A01 1A01
fault: 1000 0A01 4A01 8A01 1A01
```

The faulted result is exactly the physical CS00015 result.

## Remaining physical boundary

`vm80a.v` is die-derived but expresses this block as the arithmetic operation
`a + 1`; it does not retain transistor-level node names for the bit-12 sum.
The fitted КР580ВМ80А is instruction-compatible but its physical die layout
also need not match the source die exactly. The evidence therefore identifies
the shared incrementer function and missing Boolean term, not a transistor or
bond wire.

The practical repair is to substitute D1, then rerun
`spinoffs/jukuravi/probe_a12_increment.py`. A clean five-word result confirms
the replacement. D4, D30, and ROM rework are not justified by this fault.
