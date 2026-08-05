# Interpretation

This raw run is retained as direct INX evidence, not as a valid seeded-memory
alias matrix. The exact uploaded source used `INX D` between its even and odd
stores. On CS00015 that increment lost an already-high A12 in every tested
A15:A14 region, so the odd value reached the low-A12 alias instead of the
intended target.

The corrected memory matrix is
`../t32-ram-a12-lhld-classes-physical/` and uses unrolled absolute STA setup.
