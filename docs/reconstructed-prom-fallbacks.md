# Reconstructed PROM fallback images

Status: **HISTORICAL D8 FALLBACK RETAINED / PHYSICAL PROM TABLES ADOPTED**

The D8 file records the former boot-oriented reconstruction for historical
comparison only. Validated physical D2, D6, D8, and D94 tables under
`ref/physical-proms/validated/` now supply the HDL table contents.
For physical programming, confirm the device, programmer, and bit
representation using [the PROM procedure](prom-dump-procedure.md).

## Command

Run from the repository root. Check retained files before the exporter
rewrites the historical image and its checksum manifest.

```sh
(cd ref/reconstructed-proms && sha256sum -c SHA256SUMS)
python3 scripts/export_reconstructed_proms.py
sync/prom_fallback_check.sh
```

## Files

| Stem | Size | BIN SHA256 | HEX SHA256 | Role |
| --- | ---: | --- | --- | --- |
| `d8_re3_rom_pager_reconstructed` | 32 | `0cecad4f89dce2e5e0dba0622c89d8cfa01324dd8ff3e9f7b8f92d20ced690b3` | `c95273ef8c46ab5db1fcbaabb6971f988e934752f6921ecb06dda6cc38b1a0bc` | Historical D8 pager hypothesis; retained for byte comparison, not programming. |

## Boundaries

- Adopted D2 `.037`, D6 `.038`, D8 `.039`, and D94 `.092` hashes and
  capture provenance belong to [the physical-PROM record](../ref/physical-proms/README.md).
- Physical D8 differs from the historical reconstruction at 19 rows.
  Physical D6 supersedes its earlier reconstructed image.
- HDL models raw zero as an open-collector sink and raw one or disabled
  output as release into the consumer pull-up/TTL environment.
- D94's exact .009 CS7 enable source is drawing-closed; its D0 hidden
  load remains a [board-evidence boundary](d94-reconstruction-constraints.md).
- No video/DRAM timing image is exported. The remaining shared-DRAM
  slot schedule requires traced control paths; D94 is FDC control, not
  a missing video PROM. See [the timing audit](video-slot-timing-audit.md).
- Do not program the historical reconstruction now that repeated physical
  D8 reads exist.

## HDL Consistency Guard

`sync/prom_fallback_check.sh` compiles `hdl/sim/prom_fallback_tb.v` against the
current `hdl/devices.v` modules. With modeled pull-ups and enables asserted,
it compares all 256 D2/D6 rows and all 32 D8/D94 rows against the retained
`.raw.hex` tables. Separate D6/D8 probes check disabled release and the
row-0 sink pattern. It does not sweep every enable combination or measure
physical voltage/timing. D2/D6 models and the test read the same retained
tables; D8/D94 models use decode cases checked against those tables.
Independent dump identity and BIN/HEX agreement require the physical-PROM
guards. This test does not validate the historical D8 reconstruction.

CI also reruns `scripts/export_reconstructed_proms.py` and fails if the
generated files or this report are stale.

## Diff Procedure

When a dump arrives, compare size and SHA256 first, then byte-diff against
the matching validated physical table. Preserve raw reads and provenance
before interpreting a mismatch. A stable different table may identify a
board variant; do not replace the adopted target-board table until socket
identity, address/output mapping and electrical compatibility are verified.
