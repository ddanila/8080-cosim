# Community PROM/media request packet

Status: **READY TO SEND**

This is the current packet for contacting Juku3000 / Juku hardware owners.
Primary public target: `infoaed/juku3000`
(`https://github.com/infoaed/juku3000`) or a known Juku hardware owner.

## Why We Are Asking

The replica can boot `ROMBIOS 3.43` in the digital twin and the saved PCB
package is reproducible, but the physical design remains on hold. Several
connectivity and programmable-part items still need real media or silicon
truth:

- Baltijets doc 007 confirms the programmed-part drawings, but the small-PROM
  byte tables are marked `на диске` instead of printed.
- The current FDC cosim vendors public Arti `JUKU1/JUKU2` disk images and
  boots `media/disks/JUKU1.CPM` to the EKDOS `A>` prompt, but physical-media
  provenance is still useful.
- D2 `.037` and D6 `.038` now have validated physical tables. Independent
  reads or original programming-disk files would provide useful corroboration.
- D8 remains a boot-validated reconstruction fallback under
  `ref/reconstructed-proms/`; it still needs disk/dump validation before it
  counts as preservation-grade PROM truth.
- Disk-side `JBASIC.COM` now reaches a visible `READY` prompt in cosim and
  uninterrupted HDL, but the public 8 KiB removable-memory BASIC cartridge
  remains a Monitor 3.3 compatibility boundary. Current probes show the body is
  copied, then the runtime bootstrap needs bytes beyond the public payload and
  simple tail/entry patches do not reach BASIC.

Relevant local docs:

- `docs/prom-dump-procedure.md`
- `docs/reconstructed-prom-fallbacks.md`
- `docs/ekdos-media-acquisition.md`
- `docs/cartridge-basic-boundary.md`
- `ref/baltijets-tech-docs/README.md`
- `docs/replica-dual-config-bom.md`

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
4. If a physical .009 processor board is available, can someone dump or help
   dump these socketed parts?
   - `К155РЕ3` D8, 32 bytes
   - `К155РЕ3` D94 / FDC-era top-corner PROM, 32 bytes
   - `КР556РТ4А` D2, 256 nibbles stored as 256 bytes
   - `КР556РТ4А` D6, 256 nibbles stored as 256 bytes
   - D15/D16 2764/M2764 EPROM pair, 8192 bytes each
5. Can an owner provide continuity readings, or clear trace-side photographs
   of an actual `.009` FDC-populated board, for the official footprints whose
   device pinouts are modeled but whose Juku signal nets remain untraced:
   D28, D95-D99, D101, D102, and D106? The FDC support cluster is the first
   priority. D105 is modeled; the useful WAIT ask is the `.009` replacement for
   the older sheet's D95 inverter after D105.6.

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
```

## Ready-To-Send Message

Subject:

```text
Juku E5104 .009 PROM dumps and JUKU-1 media provenance for preservation/replica validation
```

Body:

```text
Hello,

I am working on a preservation-oriented Juku E5101/E5104 processor-board
recreation and digital twin:

https://github.com/ddanila/8080-cosim

The current twin boots ROMBIOS 3.43 from the real ROM set. The PCB package is
reproducible but the physical design remains on hold while D2/D94, the
Juku-specific nets of 9 modeled FDC-support ICs, and programmable-part evidence
are incomplete.
D105 wait/MRD logic and most of D30 READY are already modeled and routed.

Baltijets doc 007 confirms several programmed-part drawings, but the byte tables
for the small PROMs are marked "на диске" rather than printed. I am looking for
either those programming disk files or dumps from a physical .009 processor
board:

Validated physical D2/D6 tables are now preserved; D8 remains a reconstructed
fallback. Factory programming-disk files are still valuable independent truth.

- КР556РТ4А D2 and D6, drawing family ДГШ5.106.037/.038
- К155РЕ3 D8, drawing ДГШ5.106.039
- the FDC-era D94 PROM ДГШ5.106.092 on the .009 board
- the D15/D16 2764/M2764 ROM pair, if a physical board can be read

The `.009` board also has 9 FDC-support devices whose packages and device-level
pin roles are now represented, but whose Juku-specific functional nets remain
untraced: D28, D95-D99, D101, D102, and D106. The current owner photographs do
show the FDC-equipped population, but sockets, wires, crossings, and incomplete
local registration hide most end-to-end paths. Continuity readings or clearer
trace-side photographs of those devices, D30's remaining section-B endpoints,
and the `.009` WAIT handoff would directly unblock the board.

The repo now vendors Arti's public JUKU1/JUKU2 raw disk images, and
media/disks/JUKU1.CPM boots to the EKDOS A> prompt in cosim. I am still looking
for an independently dumped JUKU-1 / ДГШ5.106.105 disk, or checksum/provenance
that can verify this public image. The cosim check is:

    sync/ekdos_fdc_probe.py

The disk-side JBASIC.COM path is now proven to a visible READY prompt, but the
public 8 KiB removable-memory BASIC cartridge is still unresolved with Monitor
3.3. Current probes show Monitor 3.3 copies the cartridge body, then the runtime
bootstrap needs a page beyond the public 8 KiB payload; simple fill, append,
final-page mirror, relocation-count, and direct body-entry patch hypotheses do
not reach BASIC. I am also looking for any larger/different BASIC cartridge
image, programming artifact, or hardware-confirmed launch procedure that reaches
the documented BASIC banner / READY prompt.

The dump procedure and exact requested outputs are documented here:

https://github.com/ddanila/8080-cosim/blob/main/docs/prom-dump-procedure.md
https://github.com/ddanila/8080-cosim/blob/main/docs/community-prom-media-request.md

Happy to contribute back the traced netlist, KiCad board recreation, cosim
findings, and any corrections that are useful to juku3000/MAME.

Thanks!
```

## What To Do With Replies

1. Record metadata and hashes in a local note first.
2. For PROM dumps, compare repeated reads and reject all-`00`/all-`FF` files.
3. For a raw Juku disk image, run:

   ```sh
   sync/juk_disk_check.sh
   EKDOS_PROBE_DISK=/path/to/image sync/ekdos_fdc_probe.py
   ```

4. For a BASIC cartridge image or launch procedure, compare its length, hash,
   entry metadata, and missing-page coverage against
   `docs/cartridge-basic-boundary.md` before starting new runtime experiments.

5. If a dump cannot be published, record only the checksum/provenance and keep
   reconstructed tables as the buildable Tier-1/2 fallback.
