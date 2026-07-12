# Physical RT4 PROM captures

These are owner-produced serial captures from the socketed `.009` processor
board and deterministic outputs from `scripts/validate_rt4_dump.py`. Raw
pin-level bytes are authoritative; `asserted.bin` is the separately named
active-low low-nibble complement.

## D2 — ДГШ5.106.037

Three captures parse identically, including
`d2_037_20260713_capture3_powercycled.txt`, which was acquired after a separate
power cycle. Validation command:

```sh
python3 scripts/validate_rt4_dump.py \
  ref/physical-proms/captures/d2_037_20260713_capture1.txt \
  ref/physical-proms/captures/d2_037_20260713_capture2.txt \
  ref/physical-proms/captures/d2_037_20260713_capture3_powercycled.txt \
  --out-dir ref/physical-proms/validated --name d2_037
```

Authoritative raw SHA256:
`953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b`.

## D6 — ДГШ5.106.038

Two preserved captures parse identically. They establish a stable physical
table, but a separately power-cycled third capture would further strengthen
the acquisition provenance.

```sh
python3 scripts/validate_rt4_dump.py \
  ref/physical-proms/captures/d6_038_20260713_capture1.txt \
  ref/physical-proms/captures/d6_038_20260713_capture2.txt \
  --out-dir ref/physical-proms/validated --name d6_038
```

Authoritative raw SHA256:
`05a127c330762600b398b6f1bccbecc1b1861b96f8d62ff3e5471dbae9383d39`.

The validated JSON manifests retain every input capture path and SHA256. Keep
the serial inputs unchanged; regenerate derived binaries instead of editing
them manually.
