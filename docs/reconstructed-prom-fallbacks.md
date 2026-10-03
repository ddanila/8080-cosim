# Reconstructed PROM fallback images

Status: **HISTORICAL D8 FALLBACK RETAINED / PHYSICAL PROM TABLES ADOPTED**

The D8 file records the former boot-oriented reconstruction for historical
comparison only. Validated physical D2, D6, D8, and D94 tables under
`ref/physical-proms/` now drive HDL and are the burnable PROM truth.

## Command

```sh
python3 scripts/export_reconstructed_proms.py
sync/prom_fallback_check.sh
```

## Files

| Stem | Size | BIN SHA256 | HEX SHA256 | Role |
| --- | ---: | --- | --- | --- |
| `d8_re3_rom_pager_reconstructed` | 32 | `0cecad4f89dce2e5e0dba0622c89d8cfa01324dd8ff3e9f7b8f92d20ced690b3` | `c95273ef8c46ab5db1fcbaabb6971f988e934752f6921ecb06dda6cc38b1a0bc` | D8 К155РЕ3 ROM-socket pager; byte values are active-low output rails. |

## Boundaries

- D2 `.037` has three validated captures including a separate power cycle;
  authoritative raw SHA256 is
  `953be4bf899e02f0885ecef53e4f9d26469b8d78ceea87394aa35cd28df0255b`.
- D6 `.038` has three validated captures including a separate power cycle;
  authoritative raw SHA256 is
  `c07ba671c4a75c35e1265e370a4fed4b82d1cd423859b5c56bc6cbc6572a9489`.
  This physical table supersedes the old reconstructed D6 image.
- D8 `.039` physical raw SHA256 is
  `345b67e66562741dd48e70f30e7862d4e3fc19d3a113f21c999d6ec497af59cc`.
  It differs from `d8_re3_rom_pager_reconstructed.*` at 19 rows and
  supersedes that artifact. HDL models its physical open-collector
  outputs: programmed zero sinks one socket-select rail and released
  bits recover high in the consumer pull-up/TTL environment.
- D94 `.092` physical raw SHA256 is
  `bcf942a87ee70adb1a16cebb7f018cf8f491ea2a74db0b0a5dd7d5c8db8a29e0`.
  HDL adopts its open-collector table; exact .009 CS7 closes the enable source; D0
  hidden load remains a board-evidence boundary.
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
physical voltage/timing. The model and test read the same retained tables;
independent dump identity and BIN/HEX agreement require the physical-PROM
guards. This test does not validate the historical D8 reconstruction.

CI also reruns `scripts/export_reconstructed_proms.py` and fails if the
generated files or this report are stale.

## Diff Procedure

When a dump arrives, compare size and SHA256 first, then byte-diff against
the matching validated physical table. Preserve raw reads and provenance
before interpreting a mismatch. A stable different table may identify a
board variant; do not replace the adopted target-board table until socket
identity, address/output mapping and electrical compatibility are verified.
