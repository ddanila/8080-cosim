# Community PROM/media request packet

Status: **READY TO SEND**

This is the WS-F/WS-H packet for contacting Juku3000 / Juku hardware owners.
Primary public target: `infoaed/juku3000`
(`https://github.com/infoaed/juku3000`). The repository currently exposes Juku
software/media documentation and issues, but new issue creation may be
restricted for outside users; if so, send the same text to a maintainer or use
an existing appropriate contact thread.

## Why We Are Asking

The replica can boot `ROMBIOS 3.43` in the digital twin and the PCB fabrication
gates are now machine-ready, but several authenticity/fidelity items still need
real media or silicon truth:

- Baltijets doc 007 confirms the programmed-part drawings, but the small-PROM
  byte tables are marked `на диске` instead of printed.
- The current FDC cosim can load an external `.juk` image and perform WD1793
  sector reads, but the repo does not vendor copyrighted EKDOS media.
- The functional PROM maps are boot-validated reconstructions; dumped PROMs
  would turn them into preservation-grade evidence.

Relevant local docs:

- `docs/prom-dump-procedure.md`
- `docs/ekdos-media-acquisition.md`
- `ref/baltijets-tech-docs/README.md`
- `docs/replica-dual-config-bom.md`

## Exact Ask

1. Does anyone have the Baltijets programming disk files referenced by doc 007,
   especially tables/dumps for:
   - `ДГШ5.106.037` / `ДГШ5.106.038` (`КР556РТ4`, D2/D6 decode PROMs)
   - `ДГШ5.106.039` (`К155РЕ3`, D8)
   - `ДГШ5.106.092` (FDC-era PROM, D94 on the .009 board)
   - `ДГШ5.106.040` etc. EPROM programming files for the 2764/К573РФ5 ROM row
2. Does anyone have a known-good `.juk` image for the factory boot disk
   `JUKU-1` / `ДГШ5.106.105`, or a checksum/source pointer for it?
3. If a physical .009 processor board is available, can someone dump or help
   dump these socketed parts?
   - `К155РЕ3` D8, 32 bytes
   - `К155РЕ3` D94 / FDC-era top-corner PROM, 32 bytes
   - `КР556РТ4А` D2, 256 nibbles stored as 256 bytes
   - `КР556РТ4А` D6, 256 nibbles stored as 256 bytes
   - D15/D16 2764/M2764 EPROM pair, 8192 bytes each

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
```

Do not post copyrighted images publicly if rights are unclear. A checksum plus
private pointer is still useful for verification.

## Ready-To-Send Message

Subject:

```text
Juku E5104 .009 PROM dumps and JUKU-1 EKDOS media for preservation/replica validation
```

Body:

```text
Hello,

I am working on a preservation-oriented Juku E5101/E5104 processor-board
recreation and digital twin:

https://github.com/ddanila/8080-cosim

The current twin boots ROMBIOS 3.43 from the real ROM set and the PCB recreation
has machine fabrication gates, but a few items still need source-of-truth media
or hardware dumps before the replica can be called preservation-grade.

Baltijets doc 007 confirms several programmed-part drawings, but the byte tables
for the small PROMs are marked "на диске" rather than printed. I am looking for
either those programming disk files or dumps from a physical .009 processor
board:

- КР556РТ4А D2 and D6, drawing family ДГШ5.106.037/.038
- К155РЕ3 D8, drawing ДГШ5.106.039
- the FDC-era PROM ДГШ5.106.092, likely D94 on the .009 board
- the D15/D16 2764/M2764 ROM pair, if a physical board can be read

I am also looking for a known-good JUKU-1 / ДГШ5.106.105 EKDOS boot disk image
or checksum/source pointer. The cosim now accepts an external raw .juk image via:

    EKDOS_PROBE_DISK=/path/to/JUKU-1.juk sync/ekdos_fdc_probe.py

The repo will not vendor copyrighted media unless rights are clear; even a
checksum and provenance note would help.

The dump procedure and exact requested outputs are documented here:

https://github.com/ddanila/8080-cosim/blob/main/docs/prom-dump-procedure.md
https://github.com/ddanila/8080-cosim/blob/main/docs/community-prom-media-request.md

Happy to contribute back the traced netlist, KiCad board recreation, cosim
findings, and any corrections that are useful to juku3000/MAME.

Thanks!
```

## What To Do With Replies

1. Save binary dumps outside the repo until rights/provenance are clear.
2. Record metadata and hashes in a local note first.
3. For PROM dumps, compare repeated reads and reject all-`00`/all-`FF` files.
4. For a `.juk` disk, run:

   ```sh
   sync/juk_disk_check.sh
   EKDOS_PROBE_DISK=/path/to/JUKU-1.juk sync/ekdos_fdc_probe.py
   ```

5. If a dump cannot be published, record only the checksum/provenance and keep
   reconstructed tables as the buildable Tier-1/2 fallback.
