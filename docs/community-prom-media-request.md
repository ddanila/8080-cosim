# Community PROM/media request packet

Status: **READY TO SEND**

This is the current packet for contacting Juku3000 / Juku hardware owners.
Primary public target: `infoaed/juku3000`
(`https://github.com/infoaed/juku3000`) or a known Juku hardware owner.

## Why We Are Asking

The digital twin boots the preserved ROM set. Current PCB routing and package
release remain on design hold; see
[manufacturing readiness](replica-manufacturing-readiness.md).
Additional media and silicon reads are requested for preservation and
board-variant detection, not because the adopted PROM/EPROM set is incomplete:

- Baltijets doc 007 confirms the programmed-part drawings, but the small-PROM
  byte tables are marked `на диске` instead of printed.
- The current FDC cosim vendors public Arti `JUKU1/JUKU2` disk images and
  boots `media/disks/JUKU1.CPM` to the EKDOS `A>` prompt, but physical-media
  provenance is still useful.
- D2 `.037`, D6 `.038`, D8 `.039`, and D94 `.092` now have validated repeated
  physical tables. D8/D94 have three independent read events each, retained
  under two board-name aliases; those aliases do not prove cross-board reads.
  Independent acquisitions or original
  programming-disk files would provide optional further provenance. D94's
  D0 hidden load remains incomplete; exact `.009` sheets close its `CS7` enable source.
- The third-source archival `JUKUROM0/1` pair is adopted as the D15/D16 archive-37
  RomBios 3.43m content. Further EPROM reads may expose a board variant but are not a
  content or release gate.
- Disk-side `JBASIC.COM` now reaches a visible `READY` prompt in cosim and
  uninterrupted HDL, but the public 8 KiB removable-memory BASIC cartridge
  remains a Monitor 3.3 compatibility boundary: its bootstrap needs bytes
  beyond the public payload. A complete image or confirmed launch procedure
  is still useful.
- The public Monitor 2.2 image has damaged physical chips 7 and 8. The upstream
  catalog records a couple of errors in chip 7 and 50 divergences across seven
  chip-8 reads, but the public ZIP and Git history retain only the final
  concatenated image. The original per-read captures could resolve the two
  remaining bad ROM blocks without speculative byte repair.

Supporting records:

- [PROM read procedure](prom-dump-procedure.md)
- [Adopted PROM contents](reconstructed-prom-fallbacks.md)
- [Disk acquisition](ekdos-media-acquisition.md)
- [Cartridge BASIC boundary](cartridge-basic-boundary.md)
- [Monitor 2.2 reconstruction](jmon22-reconstruction.md)
- [Baltijets sources](../ref/baltijets-tech-docs/README.md)

## Exact Ask

1. Does anyone have the Baltijets programming disk files referenced by doc 007,
   especially tables/dumps for:
   - `ДГШ5.106.037` / `ДГШ5.106.038` (`КР556РТ4`, D2 bus/wait + D6 memory-decode PROMs)
   - `ДГШ5.106.039` (`К155РЕ3`, D8)
   - `ДГШ5.106.092` (FDC-era PROM, D94 on the .009 board)
   - `ДГШ5.106.040` etc. EPROM programming files for the 2764/К573РФ5 ROM row
2. Does anyone have an independently dumped factory boot disk
   `JUKU-1` / `ДГШ5.106.105`, or checksum/provenance that can verify the
   vendored public `media/disks/JUKU1.CPM` image?
3. Does anyone have a larger/different removable-memory BASIC cartridge image,
   programming artifact, or hardware-confirmed Monitor 3.3 launch procedure
   that reaches the documented BASIC banner / `READY` prompt?
4. If a physical .009 processor board is available, can someone independently
   re-read these socketed parts for corroboration or board-variant detection?
   - `К155РЕ3` D8, 32 bytes
   - `К155РЕ3` D94 / FDC-era top-corner PROM, 32 bytes
   - `КР556РТ4А` D2, 256 nibbles stored as 256 bytes
   - `КР556РТ4А` D6, 256 nibbles stored as 256 bytes
   - D15/D16 2764/M2764 EPROM pair, 8192 bytes each
5. Can the custodians of the Monitor 2.2 recovery provide the original physical
   chip-7 reads and all seven chip-8 reads, before consensus/concatenation? The
   useful package includes the raw 2 KiB files, read order, programmer/reader
   settings, and any log or note identifying the 50 divergent chip-8 bytes.
   Upstream commit `31c74684` is the first detailed catalog record of those
   unstable reads.
6. Can an owner supply powered-off continuity or registered trace-side photos
   for the remaining boundaries in
   [the FDC hardware handoff](fdc-hardware-handoff.md)? The 4 still-open
   support-device boundaries are D96, D99, D100 and D101. Their pin roles and
   much of their wiring are source-closed; target-board continuity and powered
   behavior remain separate requirements. Priority comparisons include
   D96.9-to-D101, D96.11-to-D94.2/D99.9, D96.13-to-D99.10, and the shared
   clear/B2 source. D30 and D105's measured local handoffs need no repeated
   generic continuity request.

## Minimal Useful Deliverables

For every dumped part or disk image:

- filename
- board revision / board number if known
- socket refdes and chip marking
- chip orientation photo before removal, if possible
- dump method/programmer
- SHA-256
- repeated-read confirmation, or a note that it is a single read

Suggested dump names:

```text
proms/re3_d8_<board>.bin
proms/re3_d94_<board>.bin
proms/rt4_d2_<board>.bin
proms/rt4_d6_<board>.bin
proms/m2764_d15_<board>.bin
proms/m2764_d16_<board>.bin
media/juku-1_dgsh5.106.105_<source>.juk
roms/jbasic_cartridge_<source>.bin
roms/jmon22_chip7_<source>_read<N>.bin
roms/jmon22_chip8_<source>_read<N>.bin
```

## Ready-To-Send Message

Subject:

```text
Juku E5104 .009 PROM dumps and JUKU-1 media provenance for preservation/replica validation
```

Body:

```text
Hello,

I am recreating the Juku .009 processor board and its digital twin:
https://github.com/ddanila/8080-cosim

The twin boots the preserved ROM set; physical PCB release is still held.
D2/D6/D8/D94 already have validated physical contents. Additional reads are
useful for provenance and board variants, rather than filling a missing set.

Do you have any of the following?

- Baltijets doc 007 programming-disk files for .037/.038/.039/.092 PROMs
  or the .040-family EPROMs; independent physical reads are also useful.
- An independently acquired JUKU-1 / ДГШ5.106.105 disk image, with provenance
  and checksum, to compare with the preserved public JUKU1/JUKU2 images.
- A different/larger BASIC cartridge image or a hardware-confirmed Monitor
  3.3 launch procedure. Disk JBASIC reaches READY, but the public 8 KiB
  cartridge's required runtime page remains unresolved.
- Original Monitor 2.2 chip-7 reads and all seven chip-8 reads, before the
  consensus image. The catalog records unstable reads; raw captures could
  resolve the remaining bad blocks without speculative repair.
- Continuity readings or original-resolution trace-side photos for the
  remaining .009 FDC support boundaries listed in our hardware handoff.

For reads, please retain board/socket identity, chip markings and orientation,
reader settings, raw files, hashes and whether repeated reads match.

The precise requests and preservation procedure are here:
https://github.com/ddanila/8080-cosim/blob/master/docs/community-prom-media-request.md
https://github.com/ddanila/8080-cosim/blob/master/docs/prom-dump-procedure.md

Thanks!
```

## What To Do With Replies

1. Record metadata and hashes in a local note first.
2. For PROM dumps, validate complete repeated captures with the appropriate
   RE3 or RT4 validator and compare against the adopted table. A uniform dump
   warrants checking enables, pull-ups, wiring, and device identity; repeated
   byte agreement alone does not establish a valid acquisition. Preserve the
   raw evidence while investigating.
3. For a raw Juku disk image, run:

   ```sh
   sync/juk_disk_check.sh
   EKDOS_PROBE_DISK=/path/to/image python3 sync/ekdos_fdc_probe.py /tmp/candidate-ekdos-fdc-probe.md
   ```

   The first command checks the vendored disk support. The second probes the
   candidate image and writes a separate report; compare its identity and
   results with the adopted baseline before replacing tracked media.

4. For a BASIC cartridge image or launch procedure, compare its length, hash,
   entry metadata, and missing-page coverage against
   `docs/cartridge-basic-boundary.md` before starting new runtime experiments.

5. If a dump cannot be published, record its checksum/provenance and compare it
   privately with the validated physical table; do not fall back to the
   superseded D8 reconstruction.
