# Transcription — Memory subsystem (Sheet 1, right)

Confidence tags as in `cpu-core.md`: **[scan]** read off the drawing, **[?]** to verify.

## Headline: the memory map is a decode PROM, not an 8255 "memory_view"
MAME abstracts banking as a 4-mode `memory_view` selected by 8255#0 Port C. The
**real board decodes the map with a bipolar PROM**:

- **D6 = К556РТ4** (256×4 bipolar PROM), the address-map / bank decoder. [scan]
  - Inputs A0–A7 = pins 5,6,7,4,3,2,1,15 ← buffered address (and very likely the
    8255 Port C mode bit) — **exact input lines TODO** [?].
  - Outputs: **ROM** = D0/pin12, **RAM** = D1/pin11, **REV** = D2/pin10,
    **ROE** = D3/pin9 (ROM output enable). Chip enables V1=13, V2=14. [scan]
  - Pull-ups R11, R12 (1k) on the ROM/RAM select lines. [scan]
- The map *truth table* lives in the **PROM contents** — NOT on the schematic.
  That's why the effective map (ROM@0x0000 in mode 0, RAM-under-ROM, etc.) had to
  be recovered from the **emulator trace / MAME**, and they agree. The schematic
  gives the *mechanism*; the emulator gives the *contents*.
- Implication: the 8255 Port C "mode" is an **input to this PROM** (combined with
  address), not a direct view-switch. Reconciles with MAME's behavioral result.

## Other memory chips (to transcribe)
- **ROM/EPROM**: array in sockets (Sheet 1 note: "D2,D6,D8,D15…D22 installed in
  sockets"); EPROM array D17–D22 with A0–A12, D0–D7, CS, OE. [scan, refdes [?]]
- **RAM**: К565РУ5 DRAM array (20×) — addressed/selected via RAM/REV signals +
  the РУ5 RAS/CAS/refresh logic. [scan]

## TODO (next passes)
1. Trace D6 (РТ4) input lines: which buffered address bits + the Port C mode bit.
2. Identify ROM/EPROM refdes + their CS/OE ← ROM/ROE; data → DB bus.
3. РУ5 DRAM array: address mux (μP vs video address — see Sheet 2 "VIDEO ADDRESS /
   μP ADDRESS"), RAS/CAS, WE ← RAM/MWR.
4. Model the decode PROM in HDL (as a chip with its select outputs) + LVS;
   keep the PROM *contents* sourced from the emulator-derived map.
