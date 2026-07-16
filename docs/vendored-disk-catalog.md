# Vendored disk catalog

Status: **VENDORED DISK DIRECTORY INDEXED**

This report indexes the visible CP/M directory entries in the vendored
Juku raw disk images under `media/disks/`. It is intentionally a
conservative catalog, not a full CP/M filesystem extractor.

The current images expose their directory at byte offset `0x5000`.
The scanner reads `128` directory entries of `32` bytes
and strips CP/M attribute bits from filename bytes.

## BASIC-relevant files

| Disk | Files |
| --- | --- |
| media/disks/JUKPROG2.CPM | `B80.COM`, `BASCOM.COM`, `BASCOM.DOK`, `BASLIB.REL`, `BRUN.COM`, `JBASIC.COM` |
| media/disks/JUKPROGX.CPM | `BASLIB.REL`, `BIO80.BAS`, `MATIC80.BAS`, `STIIL.BAS`, `YL80.BAS` |
| media/disks/JUKU1.CPM | `B80.COM`, `JBASIC.COM` |

## Programming-media PROM search

The three `JUKPROG` images were checked separately because factory doc 007
says the `.037`/`.038`/`.039`/`.092` programming tables were held on disk.
The audit checks active directory filenames, recoverable deleted-entry
filenames, and every raw image byte for strong ASCII drawing/part markers.
It also searches the complete raw images and every reconstructed active CP/M
file for exact encodings of all four validated physical PROM tables.
The exact search covers raw and asserted polarity, forward and reversed address
order, compact/space/line-oriented ASCII hex, checksum-valid Intel HEX,
and, where the table is nibble-wide, nibble ASCII plus both packed-nibble
orders.
No match under these common exact encodings rules out a plainly stored validated
table; a proprietary, permuted, compressed, or otherwise transformed encoding
still cannot be ruled out.

| Disk | Active candidate names | Deleted names | Raw marker hits | Exact table hits |
| --- | --- | --- | --- | --- |
| media/disks/JUKPROG1.CPM | none | none | none | none |
| media/disks/JUKPROG2.CPM | none | none | none | none |
| media/disks/JUKPROGX.CPM | none | none | none | none |

### Exact binary-table forensics

Each encoding is searched once in the physical byte stream and once in every
active file reconstructed in CP/M logical extent order. Offsets would be shown
for every match; `none` means the full encoding was absent from both views.

| Disk | Validated table | Corpora searched | Encoding forms tested | Matches |
| --- | --- | ---: | ---: | --- |
| media/disks/JUKPROG1.CPM | D2 .037 | 79 | 84 | none |
| media/disks/JUKPROG1.CPM | D6 .038 | 79 | 84 | none |
| media/disks/JUKPROG1.CPM | D8 .039 | 79 | 68 | none |
| media/disks/JUKPROG1.CPM | D94 .092 | 79 | 76 | none |
| media/disks/JUKPROG2.CPM | D2 .037 | 49 | 84 | none |
| media/disks/JUKPROG2.CPM | D6 .038 | 49 | 84 | none |
| media/disks/JUKPROG2.CPM | D8 .039 | 49 | 68 | none |
| media/disks/JUKPROG2.CPM | D94 .092 | 49 | 76 | none |
| media/disks/JUKPROGX.CPM | D2 .037 | 25 | 84 | none |
| media/disks/JUKPROGX.CPM | D6 .038 | 25 | 84 | none |
| media/disks/JUKPROGX.CPM | D8 .039 | 25 | 68 | none |
| media/disks/JUKPROGX.CPM | D94 .092 | 25 | 76 | none |

## Directory entries

### `media/disks/J3KUTIL4.JUK`

- Size: `819200` bytes
- Directory entries found: `59`

| Entry | Offset | User | Filename | Extent | Records |
| ---: | ---: | ---: | --- | ---: | ---: |
| 0 | 0x05000 | 0 | `READ.ME` | 0 | 33 |
| 4 | 0x05080 | 0 | `LF.COM` | 0 | 16 |
| 5 | 0x050A0 | 0 | `MODX.COM` | 0 | 28 |
| 6 | 0x050C0 | 0 | `CAL.COM` | 1 | 14 |
| 7 | 0x050E0 | 0 | `CF.COM` | 0 | 8 |
| 8 | 0x05100 | 0 | `CF.HLP` | 0 | 12 |
| 9 | 0x05120 | 0 | `COMPU.COM` | 0 | 14 |
| 10 | 0x05140 | 0 | `DEMO.COM` | 0 | 41 |
| 11 | 0x05160 | 0 | `DEMO.DOC` | 0 | 70 |
| 12 | 0x05180 | 0 | `DEMO.HLP` | 0 | 28 |
| 13 | 0x051A0 | 0 | `DEMOS.COM` | 0 | 66 |
| 14 | 0x051C0 | 0 | `DEMOS.DOC` | 0 | 123 |
| 15 | 0x051E0 | 0 | `DOCTOR.COM` | 2 | 28 |
| 32 | 0x05400 | 0 | `EKDOS30.ASM` | 0 | 112 |
| 33 | 0x05420 | 0 | `FDMAINT.COM` | 0 | 81 |
| 34 | 0x05440 | 0 | `FX800.COM` | 0 | 14 |
| 35 | 0x05460 | 0 | `JCM.COM` | 0 | 96 |
| 36 | 0x05480 | 0 | `JCM.HLP` | 0 | 59 |
| 37 | 0x054A0 | 0 | `JLOAD.LDR` | 0 | 3 |
| 38 | 0x054C0 | 0 | `JSET.COM` | 0 | 4 |
| 39 | 0x054E0 | 0 | `KULT.COM` | 0 | 95 |
| 40 | 0x05500 | 0 | `KULT.HLP` | 0 | 69 |
| 41 | 0x05520 | 0 | `KUVA.COM` | 0 | 6 |
| 42 | 0x05540 | 0 | `LINK.COM` | 0 | 122 |
| 43 | 0x05560 | 0 | `MAC.COM` | 0 | 92 |
| 44 | 0x05580 | 0 | `MDUMP.COM` | 0 | 4 |
| 45 | 0x055A0 | 0 | `ME.COM` | 1 | 123 |
| 46 | 0x055C0 | 0 | `ME.DOC` | 0 | 96 |
| 47 | 0x055E0 | 0 | `MED.COM` | 0 | 24 |
| 64 | 0x05800 | 0 | `MIC.COM` | 0 | 30 |
| 65 | 0x05820 | 0 | `MIC.HLP` | 0 | 50 |
| 66 | 0x05840 | 0 | `MIT.COM` | 0 | 128 |
| 67 | 0x05860 | 0 | `MUSAM.COM` | 0 | 29 |
| 68 | 0x05880 | 0 | `PLAYER.ERL` | 0 | 4 |
| 69 | 0x058A0 | 0 | `POWER.COM` | 0 | 128 |
| 70 | 0x058C0 | 0 | `PRT.COM` | 0 | 32 |
| 71 | 0x058E0 | 0 | `PRT.DOC` | 0 | 58 |
| 72 | 0x05900 | 0 | `RESIDENT.DOC` | 0 | 13 |
| 73 | 0x05920 | 0 | `SDEL.COM` | 0 | 7 |
| 74 | 0x05940 | 0 | `SED80.COM` | 0 | 80 |
| 75 | 0x05960 | 0 | `SEIKO.COM` | 0 | 14 |
| 76 | 0x05980 | 0 | `SETS.COM` | 0 | 11 |
| 77 | 0x059A0 | 0 | `SK.COM` | 0 | 32 |
| 78 | 0x059C0 | 0 | `SYSINFO.COM` | 0 | 9 |
| 79 | 0x059E0 | 0 | `WSJ.COM` | 0 | 124 |
| 96 | 0x05C00 | 0 | `WSMSGS.OVR` | 1 | 90 |
| 97 | 0x05C20 | 0 | `WSOVLY1.OVR` | 2 | 10 |
| 98 | 0x05C40 | 0 | `BUGABOO.COM` | 1 | 11 |
| 99 | 0x05C60 | 0 | `BUGABOO.DAT` | 0 | 8 |
| 100 | 0x05C80 | 0 | `BUGABOO.MSG` | 0 | 11 |
| 101 | 0x05CA0 | 0 | `BUGABOO.TAB` | 0 | 1 |
| 102 | 0x05CC0 | 0 | `CATCHUM.COM` | 1 | 101 |
| 103 | 0x05CE0 | 0 | `CATCHUM.DAT` | 0 | 4 |
| 104 | 0x05D00 | 0 | `CHESS.COM` | 1 | 120 |
| 105 | 0x05D20 | 0 | `LADDER.COM` | 2 | 64 |
| 106 | 0x05D40 | 0 | `LADDER.DAT` | 0 | 4 |
| 107 | 0x05D60 | 0 | `SNAKE.COM` | 0 | 89 |
| 108 | 0x05D80 | 0 | `SNAKE.DAT` | 0 | 8 |
| 109 | 0x05DA0 | 0 | `XONIX.COM` | 0 | 30 |

### `media/disks/JUKGAME1.CPM`

- Size: `819200` bytes
- Directory entries found: `42`

| Entry | Offset | User | Filename | Extent | Records |
| ---: | ---: | ---: | --- | ---: | ---: |
| 0 | 0x05000 | 0 | `BOWLING.COM` | 0 | 28 |
| 1 | 0x05020 | 0 | `MODX.COM` | 0 | 28 |
| 2 | 0x05040 | 0 | `LF.COM` | 0 | 16 |
| 6 | 0x050C0 | 0 | `LADDER.COM` | 2 | 64 |
| 7 | 0x050E0 | 0 | `LADDER.DAT` | 0 | 4 |
| 8 | 0x05100 | 0 | `BUGABOO.COM` | 1 | 11 |
| 9 | 0x05120 | 0 | `BUGABOO.DAT` | 0 | 8 |
| 10 | 0x05140 | 0 | `BUGABOO.MSG` | 0 | 11 |
| 11 | 0x05160 | 0 | `BUGABOO.TAB` | 0 | 2 |
| 12 | 0x05180 | 0 | `CATCHUM.COM` | 1 | 101 |
| 13 | 0x051A0 | 0 | `CATCHUM.DAT` | 0 | 4 |
| 14 | 0x051C0 | 0 | `HUNTER.COM` | 0 | 54 |
| 15 | 0x051E0 | 0 | `HUNTER.DAT` | 0 | 2 |
| 32 | 0x05400 | 0 | `LAND.COM` | 1 | 115 |
| 33 | 0x05420 | 0 | `LAND.DAT` | 0 | 5 |
| 34 | 0x05440 | 0 | `INDY.COM` | 1 | 85 |
| 35 | 0x05460 | 0 | `INDY.DAT` | 0 | 89 |
| 36 | 0x05480 | 0 | `ZOO.COM` | 1 | 72 |
| 37 | 0x054A0 | 0 | `XONIX.COM` | 0 | 30 |
| 38 | 0x054C0 | 0 | `MADUOK.COM` | 0 | 74 |
| 39 | 0x054E0 | 0 | `SNAKE.COM` | 0 | 89 |
| 40 | 0x05500 | 0 | `SNAKE.DAT` | 0 | 8 |
| 41 | 0x05520 | 0 | `TANK.COM` | 0 | 117 |
| 42 | 0x05540 | 0 | `TETRIS1.COM` | 0 | 15 |
| 43 | 0x05560 | 0 | `TETRIS.COM` | 1 | 53 |
| 44 | 0x05580 | 0 | `LUKK.TET` | 0 | 1 |
| 45 | 0x055A0 | 0 | `LAOLEO.COM` | 1 | 122 |
| 68 | 0x05880 | 0 | `KAPTEN.COM` | 1 | 121 |
| 69 | 0x058A0 | 0 | `KAP.COM` | 1 | 124 |
| 70 | 0x058C0 | 0 | `GAMEBOY.COM` | 1 | 52 |
| 71 | 0x058E0 | 0 | `GAMEBOY.Z79` | 0 | 48 |
| 72 | 0x05900 | 0 | `GAMEBOY.Z80` | 0 | 33 |
| 73 | 0x05920 | 0 | `GAMEBOY.Z81` | 0 | 23 |
| 74 | 0x05940 | 0 | `GAMEBOY.DAT` | 0 | 4 |
| 75 | 0x05960 | 0 | `CHESS.COM` | 1 | 120 |
| 76 | 0x05980 | 0 | `AVTEST.COM` | 0 | 107 |
| 77 | 0x059A0 | 0 | `AVTEST.DOC` | 0 | 21 |
| 78 | 0x059C0 | 0 | `ATSKOO.COM` | 1 | 16 |
| 79 | 0x059E0 | 0 | `MOND.COM` | 1 | 4 |
| 96 | 0x05C00 | 0 | `LOGER.COM` | 1 | 122 |
| 97 | 0x05C20 | 0 | `SHOT.COM` | 0 | 18 |
| 98 | 0x05C40 | 0 | `TET.COM` | 1 | 5 |

### `media/disks/JUKPROG1.CPM`

- Size: `819200` bytes
- Directory entries found: `78`

| Entry | Offset | User | Filename | Extent | Records |
| ---: | ---: | ---: | --- | ---: | ---: |
| 0 | 0x05000 | 0 | `JCM.HLP` | 0 | 59 |
| 1 | 0x05020 | 0 | `CF.HLP` | 0 | 12 |
| 2 | 0x05040 | 0 | `XDIR.COM` | 0 | 18 |
| 3 | 0x05060 | 0 | `STAT.COM` | 0 | 41 |
| 4 | 0x05080 | 0 | `FMT.COM` | 0 | 10 |
| 5 | 0x050A0 | 0 | `FORMAT.COM` | 0 | 10 |
| 6 | 0x050C0 | 0 | `DOSGEN.COM` | 0 | 7 |
| 7 | 0x050E0 | 0 | `CF.COM` | 0 | 8 |
| 8 | 0x05100 | 0 | `MODX.COM` | 0 | 28 |
| 9 | 0x05120 | 0 | `LF.COM` | 0 | 16 |
| 13 | 0x051A0 | 0 | `JSET.COM` | 0 | 4 |
| 14 | 0x051C0 | 0 | `KUVA.COM` | 0 | 6 |
| 15 | 0x051E0 | 0 | `MODE.COM` | 0 | 2 |
| 16 | 0x05200 | 0 | `PUNK.PIC` | 0 | 5 |
| 17 | 0x05220 | 0 | `SIPELGAS.PIC` | 0 | 27 |
| 18 | 0x05240 | 0 | `RAHA.PIC` | 0 | 14 |
| 19 | 0x05260 | 0 | `BIGDASAR.PIC` | 0 | 10 |
| 20 | 0x05280 | 0 | `KLIRR.PIC` | 0 | 64 |
| 21 | 0x052A0 | 0 | `MIKA.PIC` | 0 | 9 |
| 22 | 0x052C0 | 0 | `MEHHAAN2.PIC` | 0 | 41 |
| 23 | 0x052E0 | 0 | `JEESUS.PIC` | 0 | 55 |
| 24 | 0x05300 | 0 | `MUSKETAR.PIC` | 0 | 10 |
| 25 | 0x05320 | 0 | `KORVITS2.PIC` | 0 | 23 |
| 26 | 0x05340 | 0 | `KLAABUTV.PIC` | 0 | 9 |
| 27 | 0x05360 | 0 | `JAIL.PIC` | 0 | 18 |
| 28 | 0x05380 | 0 | `ALIENS.PIC` | 0 | 13 |
| 29 | 0x053A0 | 0 | `CD.PIC` | 0 | 27 |
| 30 | 0x053C0 | 0 | `READ.ME` | 0 | 33 |
| 31 | 0x053E0 | 0 | `HOTEL.PIC` | 0 | 32 |
| 32 | 0x05400 | 0 | `MED.COM` | 0 | 24 |
| 33 | 0x05420 | 0 | `JCM.COM` | 0 | 96 |
| 34 | 0x05440 | 0 | `GTR.COM` | 1 | 87 |
| 35 | 0x05460 | 0 | `ME.COM` | 1 | 123 |
| 36 | 0x05480 | 0 | `PLAYER.ERL` | 0 | 4 |
| 37 | 0x054A0 | 0 | `WSJ.COM` | 0 | 124 |
| 38 | 0x054C0 | 0 | `WSMSGS.OVR` | 1 | 90 |
| 39 | 0x054E0 | 0 | `WSOVLY1.OVR` | 2 | 10 |
| 40 | 0x05500 | 0 | `MIC.COM` | 0 | 30 |
| 41 | 0x05520 | 0 | `SED.COM` | 0 | 80 |
| 42 | 0x05540 | 0 | `SED80.COM` | 0 | 80 |
| 43 | 0x05560 | 0 | `SETS.COM` | 0 | 11 |
| 44 | 0x05580 | 0 | `MUSAM.COM` | 0 | 29 |
| 45 | 0x055A0 | 0 | `FDMAINT.COM` | 0 | 81 |
| 46 | 0x055C0 | 0 | `RDEM.COM` | 1 | 107 |
| 47 | 0x055E0 | 0 | `DEMO.COM` | 0 | 41 |
| 48 | 0x05600 | 0 | `GAMEBOY1.PIC` | 0 | 7 |
| 64 | 0x05800 | 0 | `DEMO.HLP` | 0 | 28 |
| 65 | 0x05820 | 0 | `DEMOS.COM` | 0 | 66 |
| 66 | 0x05840 | 0 | `CAL.COM` | 1 | 14 |
| 67 | 0x05860 | 0 | `DOCTOR.COM` | 2 | 28 |
| 68 | 0x05880 | 0 | `KULT.COM` | 0 | 95 |
| 69 | 0x058A0 | 0 | `FX800.COM` | 0 | 14 |
| 70 | 0x058C0 | 0 | `COMPU.COM` | 0 | 14 |
| 71 | 0x058E0 | 0 | `CM6329.COM` | 0 | 14 |
| 72 | 0x05900 | 0 | `D100M.COM` | 0 | 11 |
| 73 | 0x05920 | 0 | `SEIKO.COM` | 0 | 14 |
| 74 | 0x05940 | 0 | `PIP.COM` | 0 | 58 |
| 75 | 0x05960 | 0 | `SYSINFO.COM` | 0 | 9 |
| 76 | 0x05980 | 0 | `SK.COM` | 0 | 32 |
| 77 | 0x059A0 | 0 | `SDEL.COM` | 0 | 7 |
| 78 | 0x059C0 | 0 | `POWER.COM` | 0 | 128 |
| 79 | 0x059E0 | 0 | `DIGGER.COM` | 0 | 9 |
| 96 | 0x05C00 | 0 | `FLIGHT.COM` | 0 | 7 |
| 97 | 0x05C20 | 0 | `ME.DOC` | 0 | 96 |
| 98 | 0x05C40 | 0 | `DEMO.DOC` | 0 | 70 |
| 99 | 0x05C60 | 0 | `DEMOS.DOC` | 0 | 123 |
| 100 | 0x05C80 | 0 | `KULT.HLP` | 0 | 69 |
| 101 | 0x05CA0 | 0 | `PRT.DOC` | 0 | 58 |
| 102 | 0x05CC0 | 0 | `MIC.HLP` | 0 | 50 |
| 103 | 0x05CE0 | 0 | `GTR.DOK` | 0 | 98 |
| 104 | 0x05D00 | 0 | `DEMO.DOK` | 0 | 64 |
| 105 | 0x05D20 | 0 | `AVE.PLR` | 0 | 16 |
| 106 | 0x05D40 | 0 | `BEETHOVE.PLR` | 0 | 2 |
| 107 | 0x05D60 | 0 | `PACIUS.PLR` | 0 | 2 |
| 108 | 0x05D80 | 0 | `BACH.PLR` | 0 | 2 |
| 109 | 0x05DA0 | 0 | `BIZET.PLR` | 0 | 4 |
| 110 | 0x05DC0 | 0 | `VALGRE.PLR` | 0 | 1 |
| 111 | 0x05DE0 | 0 | `PATTERN.PIC` | 0 | 57 |

### `media/disks/JUKPROG2.CPM`

- Size: `819200` bytes
- Directory entries found: `48`

| Entry | Offset | User | Filename | Extent | Records |
| ---: | ---: | ---: | --- | ---: | ---: |
| 0 | 0x05000 | 0 | `CF.HLP` | 0 | 12 |
| 1 | 0x05020 | 0 | `BASCOM.DOK` | 0 | 87 |
| 2 | 0x05040 | 0 | `CF.COM` | 0 | 8 |
| 3 | 0x05060 | 0 | `FORMAT.COM` | 0 | 10 |
| 4 | 0x05080 | 0 | `DOSGEN.COM` | 0 | 7 |
| 5 | 0x050A0 | 0 | `PRT.COM` | 0 | 32 |
| 6 | 0x050C0 | 0 | `MDUMP.COM` | 0 | 4 |
| 7 | 0x050E0 | 0 | `ASM.COM` | 0 | 64 |
| 8 | 0x05100 | 0 | `LOAD.COM` | 0 | 14 |
| 9 | 0x05120 | 0 | `SID.COM` | 0 | 56 |
| 10 | 0x05140 | 0 | `B80.COM` | 1 | 62 |
| 11 | 0x05160 | 0 | `JBASIC.COM` | 0 | 65 |
| 12 | 0x05180 | 0 | `BRUN.COM` | 0 | 121 |
| 13 | 0x051A0 | 0 | `BASLIB.REL` | 1 | 67 |
| 14 | 0x051C0 | 0 | `BASCOM.COM` | 1 | 125 |
| 15 | 0x051E0 | 0 | `MAC.COM` | 0 | 92 |
| 32 | 0x05400 | 0 | `ED.COM` | 0 | 52 |
| 33 | 0x05420 | 0 | `SUBMIT.COM` | 0 | 10 |
| 34 | 0x05440 | 0 | `JLOAD.LDR` | 0 | 3 |
| 35 | 0x05460 | 0 | `LINK.COM` | 0 | 122 |
| 36 | 0x05480 | 0 | `MTEST.COM` | 0 | 36 |
| 37 | 0x054A0 | 0 | `MTEST2.COM` | 0 | 76 |
| 38 | 0x054C0 | 0 | `CPU.COM` | 1 | 22 |
| 39 | 0x054E0 | 0 | `QRUN.COM` | 0 | 38 |
| 40 | 0x05500 | 0 | `QDISK.COM` | 0 | 57 |
| 41 | 0x05520 | 0 | `DUMP.COM` | 0 | 4 |
| 42 | 0x05540 | 0 | `L80.COM` | 0 | 84 |
| 43 | 0x05560 | 0 | `TERM.COM` | 0 | 76 |
| 44 | 0x05580 | 0 | `NETR.COM` | 0 | 52 |
| 45 | 0x055A0 | 0 | `NETD.COM` | 0 | 59 |
| 46 | 0x055C0 | 0 | `MIT.COM` | 0 | 128 |
| 47 | 0x055E0 | 0 | `SID.DOK` | 1 | 20 |
| 64 | 0x05800 | 0 | `RESIDENT.DOC` | 0 | 13 |
| 65 | 0x05820 | 0 | `EKDOS30.ASM` | 0 | 112 |
| 66 | 0x05840 | 0 | `MP.COM` | 1 | 1 |
| 67 | 0x05860 | 0 | `MP.HLP` | 2 | 59 |
| 68 | 0x05880 | 0 | `MP.OVR` | 2 | 83 |
| 71 | 0x058E0 | 0 | `INSTALL.COM` | 0 | 51 |
| 72 | 0x05900 | 0 | `INSTALL.DAT` | 1 | 34 |
| 73 | 0x05920 | 0 | `INSTALL.MSG` | 0 | 93 |
| 74 | 0x05940 | 0 | `INSTALL.OVR` | 1 | 110 |
| 75 | 0x05960 | 0 | `INSTALL.SPC` | 0 | 2 |
| 76 | 0x05980 | 0 | `DBASE.COM` | 1 | 24 |
| 77 | 0x059A0 | 0 | `DBASEMSG.TXT` | 3 | 28 |
| 78 | 0x059C0 | 0 | `DBASEOVR.COM` | 2 | 58 |
| 79 | 0x059E0 | 0 | `DBINST.COM` | 0 | 106 |
| 96 | 0x05C00 | 0 | `MPLAN.DOK` | 1 | 128 |
| 97 | 0x05C20 | 0 | `DBAAS.DOK` | 1 | 91 |

### `media/disks/JUKPROGX.CPM`

- Size: `819200` bytes
- Directory entries found: `24`

| Entry | Offset | User | Filename | Extent | Records |
| ---: | ---: | ---: | --- | ---: | ---: |
| 0 | 0x05000 | 0 | `FORT.DOK` | 2 | 73 |
| 1 | 0x05020 | 0 | `FORMAT.COM` | 0 | 10 |
| 2 | 0x05040 | 0 | `DOSGEN.COM` | 0 | 7 |
| 3 | 0x05060 | 0 | `F80.COM` | 1 | 85 |
| 4 | 0x05080 | 0 | `FORLIB.REL` | 1 | 79 |
| 5 | 0x050A0 | 0 | `MTPLUS.COM` | 2 | 27 |
| 6 | 0x050C0 | 0 | `MTPLUS.000` | 0 | 102 |
| 7 | 0x050E0 | 0 | `MTPLUS.001` | 0 | 87 |
| 8 | 0x05100 | 0 | `MTPLUS.002` | 0 | 56 |
| 9 | 0x05120 | 0 | `MTPLUS.003` | 0 | 58 |
| 10 | 0x05140 | 0 | `MTPLUS.004` | 1 | 5 |
| 11 | 0x05160 | 0 | `MTPLUS.005` | 0 | 68 |
| 12 | 0x05180 | 0 | `MTPLUS.006` | 0 | 49 |
| 13 | 0x051A0 | 0 | `LINKMT.COM` | 0 | 94 |
| 14 | 0x051C0 | 0 | `FPREALS.ERL` | 0 | 60 |
| 15 | 0x051E0 | 0 | `PASLIB.ERL` | 1 | 67 |
| 32 | 0x05400 | 0 | `TRANCEND.ERL` | 0 | 26 |
| 33 | 0x05420 | 0 | `MTERRS.TXT` | 0 | 38 |
| 34 | 0x05440 | 0 | `BASLIB.REL` | 3 | 4 |
| 35 | 0x05460 | 0 | `BIO80.BAS` | 0 | 16 |
| 36 | 0x05480 | 0 | `MATIC80.BAS` | 0 | 21 |
| 37 | 0x054A0 | 0 | `YL80.BAS` | 0 | 10 |
| 38 | 0x054C0 | 0 | `STIIL.BAS` | 0 | 4 |
| 39 | 0x054E0 | 0 | `MR.NOS` | 0 | 14 |

### `media/disks/JUKU1.CPM`

- Size: `819200` bytes
- Directory entries found: `23`

| Entry | Offset | User | Filename | Extent | Records |
| ---: | ---: | ---: | --- | ---: | ---: |
| 0 | 0x05000 | 0 | `FX800.COM` | 0 | 14 |
| 1 | 0x05020 | 0 | `GTR.COM` | 1 | 87 |
| 2 | 0x05040 | 0 | `PIP.COM` | 0 | 58 |
| 3 | 0x05060 | 0 | `DBASEOVR.COM` | 2 | 58 |
| 4 | 0x05080 | 0 | `DBASEMSG.TXT` | 3 | 28 |
| 5 | 0x050A0 | 0 | `DBINST.COM` | 0 | 106 |
| 6 | 0x050C0 | 0 | `DBASE.COM` | 1 | 24 |
| 7 | 0x050E0 | 0 | `B80.COM` | 1 | 62 |
| 8 | 0x05100 | 0 | `JBASIC.COM` | 0 | 65 |
| 9 | 0x05120 | 0 | `WSOVLY1.OVR` | 2 | 10 |
| 10 | 0x05140 | 0 | `WSJ.COM` | 0 | 124 |
| 11 | 0x05160 | 0 | `WSJ.BAC` | 0 | 124 |
| 12 | 0x05180 | 0 | `WSMSGS.BAC` | 1 | 90 |
| 13 | 0x051A0 | 0 | `WSMSGS.OVR` | 1 | 90 |
| 14 | 0x051C0 | 0 | `SED.COM` | 0 | 80 |
| 15 | 0x051E0 | 0 | `JCM.COM` | 0 | 96 |
| 32 | 0x05400 | 0 | `JCM.HLP` | 0 | 59 |
| 33 | 0x05420 | 0 | `EEEE___.PIC` | 0 | 6 |
| 34 | 0x05440 | 0 | `A.PIC` | 0 | 6 |
| 35 | 0x05460 | 0 | `AE.PIC` | 0 | 44 |
| 37 | 0x054A0 | 0 | `SEIN.PIC` | 0 | 6 |
| 38 | 0x054C0 | 0 | `MAJA.PIC` | 0 | 33 |
| 42 | 0x05540 | 0 | `RDEM.COM` | 1 | 107 |
