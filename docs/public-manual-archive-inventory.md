# Public manual archive inventory

Status date: 2026-07-09.

Status: **PUBLIC MANUAL ARCHIVE CLASSIFIED**

This generated report classifies the public Juku manual and drawing
listings that sit next to the software archives. It records which
documents already feed the board/twin evidence, which are covered by
stronger Baltijets packets, and which remain optional user/mechanical
context rather than automatic blockers.

## Checks

| Check | Result |
| --- | --- |
| Board-critical schematic/component PDFs exist locally | PASS |
| Arti root manual/drawing listing classified | PASS |
| Elektroonikamuuseum `e5101-joonised/` listing classified | PASS |
| Elektroonikamuuseum `kirjandus/` listing classified | PASS |

## Arti Root Manual/Drawing Listing

| Archive item | Size | Listing date | Disposition | Local evidence | Role |
| --- | ---: | --- | --- | --- | --- |
| `JUKU E5104 Kasutusjuhend 1 osa (27lk, vene k).pdf` | 5.6 MiB | 2019-08-16 | optional-user-manual | - | Russian user manual part 1; not a board/PROM source after Baltijets docs |
| `JUKU E5104 Kasutusjuhend 2 osa (15lk, vene k).pdf` | 8.0 MiB | 2019-08-16 | optional-user-manual | - | Russian user manual part 2; not a board/PROM source after Baltijets docs |
| `JUKU E5104 Kasutusjuhend 3 osa (286lk, vene k).pdf` | 42.5 MiB | 2019-08-16 | optional-service-manual | - | large Russian manual; useful for Tier-3 procedure context, not current net/PROM truth |
| `JUKU E5104 kasutusjuhend.txt` | 817 B | 2019-08-16 | documented | `docs/public-manual-archive-inventory.md` | short listing text; no board payload |
| `Juku arvuti ES101 joonised - emaplaat.pdf` | 266.4 KiB | 2019-08-16 | vendored | `ref/schematics/es101_emaplaat.pdf` | main-board drawing source |
| `Juku arvuti ES101 joonised - klaviatuur.pdf` | 2.8 MiB | 2019-08-16 | vendored | `ref/schematics/es101_klaviatuur.pdf` | keyboard drawing source |
| `Juku arvuti ES101 joonised - korpus.pdf` | 4.7 MiB | 2019-08-16 | optional-mechanical | - | case mechanical drawing; Tier-3 enclosure work, not PCB/twin blocker |
| `Juku arvuti ES101 joonised - nimekiri joonised.pdf` | 1.7 MiB | 2019-08-16 | covered | `ref/baltijets-tech-docs/000 Info.pdf` | drawing-index role covered by Baltijets packet/index |
| `Juku arvuti ES101 joonised - nimekiri komponendid.pdf` | 2.0 MiB | 2019-08-16 | vendored | `ref/schematics/es101_nimekiri_komponendid.pdf` | component-list/BOM source |
| `Juku arvuti ES101 joonised - protsessori moodul.pdf` | 4.8 MiB | 2019-08-16 | vendored | `ref/schematics/juku_es101_processor_module.pdf` | processor-module schematic source |
| `Juku arvuti ES101 joonised - toiteplokk.pdf` | 3.9 MiB | 2019-08-16 | covered | `ref/baltijets-tech-docs/012 Power supply.pdf` | PSU context covered by Baltijets power-supply packet |
| `Mikroarvuti Juku E5101 kasutamisjuhend 1988 (168lk, eesti k).pdf` | 51.3 MiB | 2019-08-16 | optional-user-manual | - | Estonian user manual; optional Tier-2/Tier-3 operation context |
| `Mikroarvuti Juku E5101 kasutamisjuhend 1988 (168lk, eesti k)_RAW.rar` | 51.6 MiB | 2019-08-16 | defer-large | - | raw scan archive; no unique board/PROM payload identified |
| `kõik_juku_failid.zip` | 180.0 MiB | 2019-08-16 | defer-large | - | aggregate archive; represented by individually classified rows |

## Elektroonikamuuseum `e5101-joonised/` Listing

| Archive item | Size | Listing date | Disposition | Local evidence | Role |
| --- | ---: | --- | --- | --- | --- |
| `emaplaat.pdf` | 267 KiB | 2024-11-14 | covered | `ref/schematics/es101_emaplaat.pdf` | same main-board drawing family as Arti mirror |
| `jooniste_nimekiri.pdf` | 1764 KiB | 2024-11-14 | covered | `ref/baltijets-tech-docs/000 Info.pdf` | drawing-index role covered by Baltijets packet/index |
| `klaviatuur.pdf` | 2857 KiB | 2024-11-14 | covered | `ref/schematics/es101_klaviatuur.pdf` | same keyboard drawing family as Arti mirror |
| `komponendid.pdf` | 2069 KiB | 2024-11-14 | covered | `ref/schematics/es101_nimekiri_komponendid.pdf` | same component-list family as Arti mirror |
| `korpus.pdf` | 4850 KiB | 2024-11-14 | optional-mechanical | - | case mechanical drawing; Tier-3 enclosure work |
| `protsessori_moodul.pdf` | 4961 KiB | 2024-11-14 | covered | `ref/schematics/juku_es101_processor_module.pdf` | same processor-module schematic family as Arti mirror |
| `toiteplokk.pdf` | 3995 KiB | 2024-11-14 | covered | `ref/baltijets-tech-docs/012 Power supply.pdf` | PSU context covered by Baltijets power-supply packet |

## Elektroonikamuuseum `kirjandus/` Listing

| Archive item | Size | Listing date | Disposition | Local evidence | Role |
| --- | ---: | --- | --- | --- | --- |
| `juku_e5104_rus_1.pdf` | 6416 KiB | 2026-04-05 | optional-user-manual | - | Russian user manual part 1; no current board/PROM dependency |
| `juku_e5104_rus_2.pdf` | 2399 KiB | 2026-04-05 | optional-user-manual | - | Russian user manual part 2; no current board/PROM dependency |
| `juku_e5104_rus_3.pdf` | 47624 KiB | 2026-04-05 | optional-service-manual | - | large Russian manual; useful only if a future procedure clue is needed |
| `juku_e5104_rus_sisukord.txt` | 2 KiB | 2026-04-05 | documented | `docs/public-manual-archive-inventory.md` | table-of-contents note; no board payload |
| `Mikroarvuti_JUKU_kasutamisjuhend_1988.pdf` | 17161 KiB | 2024-10-16 | optional-user-manual | - | Estonian user manual; optional operation context |

## Disposition

- The board-critical drawings are already represented by `ref/schematics/`
  and the Baltijets technical packet under `ref/baltijets-tech-docs/`.
- The currently unvendored public manuals are large user/service or
  mechanical-context files. They are legitimate preservation inputs,
  but the current automatic board/PROM/FDC/BASIC proof does not depend
  on their bytes.
- If a future task needs enclosure dimensions, original user workflows,
  or service-procedure wording, promote the specific source file into
  `ref/` with a checksum and a generated inspection report at that time.
- No row in these listings advertises the missing Baltijets programming
  disk files or a `ДГШ5.106.037` / `.039` / `.092` PROM table.
