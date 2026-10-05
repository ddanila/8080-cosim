# К155РЕ3 factory programming tables (owner's scans, 2026-07)

Source: `Juku_К155РЕ3_firmware.pdf` — two «Микросхема» drawings with their Д1 programming tables:

- **ДГШ 5.106.113** (изм. 2, 15.11.90): all FF except addr 14h-17h = `07 0B 0D 0E`
- **ДГШ 5.106.117** (изм. 1, 28.07.89): addr 08h-0Bh=`07`, 0Ch-0Fh=`0B`, 10h-13h=`0D`, 14h-17h=`0E`

Both «перв. примен. ДГШ 5.106.103» — i.e. they belong to the .106.103 assembly family, distinct from
the processor module's set: the .006 ВП lists D8's programmed part as ДГШ5.106.039 and the
.009 ПЭЗ adds .092 for D94. Neither table is printed in this owner scan;
validated physical `.039` and `.092` captures are preserved separately under
`ref/physical-proms/validated/`.

## D15/D16 archival EPROM pair

`JUKUROM0.HEX` and `JUKUROM1.HEX` are raw 8 KiB binary images despite their
suffixes. Their concatenation is byte-for-byte `roms/ekta37.bin`; the guarded
comparison covers eight explicitly named 16 KiB ROM candidates in
[the lineage audit](../../docs/d15-d16-firmware-lineage.md). It does not scan
all preserved or externally available firmware. The matching image identifies
serial #0037 and `RomBios 3.43m`; `37` is not the BIOS version. The archival filenames do not bind the
bytes to physical refdes or to factory programs `ДГШ5.106.087/.041`, so this
identity supports the functional replica image but is not represented as an
owner-board dump or original factory-programming record.

## Interpretation and checks

The low-nibble patterns `07/0B/0D/0E` each contain one low bit. Their shape
supports a timing/phase-select interpretation, but does not identify a fitted
socket. The processor-module parts list assigns D8 `.039` and D94 `.092`;
the validated physical tables differ from both scanned programs.

Use [the generated inspection](../../docs/re3-firmware-inspection.md) for exact
byte comparisons, source identities, and interpretation limits. Physical
captures and raw/asserted polarity are documented in
[the physical PROM reference](../physical-proms/README.md).

```sh
(cd ref/firmware && sha256sum -c SHA256SUMS)
```

To regenerate the inspection and manifest, run
`python3 scripts/report_re3_firmware_inspection.py`. The writer compares the
retained HEX bytes with its fixed transcriptions, then rewrites the manifest
from current files. Run the checksum verification before regeneration when
checking artifact integrity; regeneration is not a substitute for that check.
It does not repeat physical acquisition or establish a programming format.
