# ДГШ5.109.009 СБ extraction audit

Status date: **2026-07-11**.

Status: **SHEETS 1-6 ADOPTED / WIRE-TABLE PIN MAPPING PENDING**

This generated audit turns the photographed factory assembly drawing into
guarded project evidence. Sheet 1 proves component posture, mounting/cable
details, and factory cut/patch operations; sheets 2-6 (ДУБЛИКАТ scan)
document the wire/cable connection table and change registration. Neither
is promoted as a copper netlist.

## Extraction checks

| Check | Result | Evidence |
| --- | --- | --- |
| All 26 photographed sheet-1 views are local, real JPEGs, and indexed | PASS | `ref/photos/dgsh5-109-009-sb/` |
| Factory solder-side cuts/patches are protected as designed operations | PASS | `BODGE-TRIAGE.md`; Вид В photos 114626340/114633498/114638730 |
| D94/D100/D98 retain the corrected horizontal assembly posture | PASS | final `kicad/juku.kicad_pcb`; `kicad/check_fdc_cluster_placement.py` |
| Cable geometry is recorded from the drawing | PASS | assembly-photo README |
| Factory wires 17 and 18 carry documented S1 far ends without conflation | PASS | sheets 2-5 wire table rows 11/12 plus accepted two-sided/photo-package evidence |
| Bracket-mounted S1 is distinguished from PCB wire landings А:17/А:18 | PASS | sheet-1 top-bracket view; owner photo 200402344; sheets 2-5 rows 11/12 |
| Bracket-mounted S1 is excluded from generated PCB footprints | PASS | `kicad/gen_kicad_pcb.py`; generated `kicad/juku.kicad_pcb`; PLAN source-PCB correction |
| Dedicated А:17 landing is present on RES_RC in the board spec and source PCB | PASS | two-sided owner photos; `kicad/juku.board.json`; `kicad/check_factory_switch_landings.py` |
| R94 is modeled as 220 ohms from D98.3 with its far endpoint unresolved | PASS | `.009` assembly drawing; owner component photo; `kicad/check_r94_landing.py` |
| X9 is schematic-only and its reversed ribbon uses PCB landings A45-A58 | PASS | sheets 4-5 X9 wire table; `kicad/check_x9_offboard_landings.py` |
| X8 is schematic-only and its six-conductor cable uses PCB landings A59-A62 | PASS | sheet 2 X8 power-cable table; `kicad/check_x8_offboard_landings.py` |
| X3 is schematic-only and its cable uses photo-fitted PCB landings A21-A32 | PASS | sheet 1 circuit; sheets 4-5 cable table; owner photos; `kicad/check_x3_offboard_landings.py` |
| X4 first five legacy circuit exits are explicitly dispositioned | PASS | `.006` sheet-1 exit codes 401-405; `.009` target continuity still required |
| Connection-table sheets 2-6 are adopted and transcribed | PASS | `ref/schematics/dgsh5_109_009_sb_sheets2-6.pdf`; `ref/schematics/dgsh5-109-009-sb-wire-table.md` |

## Photograph inventory

| File | Bytes | SHA256 |
| --- | ---: | --- |
| PXL_20260711_114553710.jpg | 1803153 | `a0285bfebba8bfe5ecf66af40322bd708bd5e0ba74493132293ab74990fa334d` |
| PXL_20260711_114556899.jpg | 1859932 | `9cfa71a46d1af2224742394c15d249075e59d54ddaf6281eff70fbf55cf65f21` |
| PXL_20260711_114600417.jpg | 2065421 | `43343d7de0fe671fbe73db933755de1acf6c23c297a741085e05cf94b9c8a53d` |
| PXL_20260711_114604420.jpg | 1962524 | `50d4c40734d367c6be98bcf453766084e02891065733180d2c324786744ca6a1` |
| PXL_20260711_114607591.jpg | 1957406 | `a7a7c64fc71d9c0dbc42546bea6998f7fc86cf9e14a19a30c03c54803e455217` |
| PXL_20260711_114611058.jpg | 2054374 | `8483bec7e30bc7683a880b0a3123f4d6406f79a47bac44c321983804965a5a39` |
| PXL_20260711_114615300.jpg | 2034137 | `e27743658303619b6f356fc164744e199848bb6186d7d1d8c68d6af1cc65b77d` |
| PXL_20260711_114617677.jpg | 2076899 | `157a5671b7ffab1f4bc66dce72d89cbb8bf3b30c3d37151a12dbc47361f8bf69` |
| PXL_20260711_114620466.jpg | 2085829 | `411ac100a179bcff0cf94e5dbd5e189781ae80f29c7f549973428d72fd8a9abe` |
| PXL_20260711_114626340.jpg | 1955496 | `d149ac67a5e23f65dd9054f8da8e853c1f6b0abce8e9525b281bae1892885261` |
| PXL_20260711_114633498.jpg | 1936786 | `5897059c29b95b33edd948adb9d242325bfaa20940142c59a79ca5809fb8f839` |
| PXL_20260711_114638730.MP.jpg | 4210441 | `8c996f2e5115c4e0a0680d127fa7cffaffe7de00d76f881eee19c7ba75742f7b` |
| PXL_20260711_114649169.jpg | 2328700 | `43a97ebebef63e72d1c488201158d971a059876590c44dbc923f14f9c48f2aab` |
| PXL_20260711_114655078.jpg | 2547432 | `a60bf51d224f9e854acd7c864d67aae27230818baaa010459fcca429ef53e5c4` |
| PXL_20260711_114700250.jpg | 2442826 | `d69da5d603f64a3b0771f1baec96e4c459087b5a9ffd89e33865c729966cace0` |
| PXL_20260711_114703874.jpg | 2369032 | `372bc01010335e6419623ba626df8a2967d832ef7b02a0cdfc70c785facc8ae0` |
| PXL_20260711_114706095.jpg | 2020469 | `9bcdc4b8f40b80d7ab20b27da3b4e68227e543ef6056274b0b94affeaff25256` |
| PXL_20260711_114708501.jpg | 2501826 | `b4e3ff69071650b92e3d55da1e2d625fa3938a4ab10c0ad1b80ddca9c44bb853` |
| PXL_20260711_114711315.jpg | 2258009 | `98d6d0f0b47f4af56a789b5db7574653008bded2f37e50d6176a1c811bc3c67a` |
| PXL_20260711_114714031.jpg | 2424532 | `a5ff7c4392efcb4168b95abedc8e517502b8387dc3c19a662c419bc23d64211c` |
| PXL_20260711_114718331.jpg | 2064122 | `286753e66528babb4cac64dde60d745980a2aebe4b24cf0898c6810490021348` |
| PXL_20260711_114721647.jpg | 2158678 | `30763d2f0cbbec47a9f9fe26d9562832266edf76f2445822a1dc7f13344692c1` |
| PXL_20260711_114725830.jpg | 1792025 | `c580969326e40ffb29dc3d6b7cd9ce4237f2868b2e9d76f20167e4563c28864d` |
| PXL_20260711_114731214.jpg | 1514700 | `e72cb94b982a3fddcbbac6165b2fe0a543197eaff4b3ee8c4056cb96f3d4b0d0` |
| PXL_20260711_114734104.jpg | 1612958 | `f761ba2bba76b7ce373707967abba7138b02366cc78787a7cd96959851d004ed` |
| PXL_20260711_114740861.jpg | 1674135 | `d75a952734b8984b20fa8eb468e9a0359e0cb4f7efedfe3e7a2633fdd7327399` |

## Connection-table scan (sheets 2-6)

| File | Bytes | SHA256 |
| --- | ---: | --- |
| dgsh5_109_009_sb_sheets2-6.pdf | 4743658 | `779bca02a2b7d0aba9b170b39ab55ff5f980d06f3f324fd91958ece646ddfc2b` |

Transcription: `ref/schematics/dgsh5-109-009-sb-wire-table.md`.

## Release interpretation

- Preserve the electrical result of the factory D56/D15/D14/D11 modifications.
- Keep D94/D100/D98 horizontal during the source-PCB reroute.
- Wire 17 is promoted as A17.1/А:17 to S1:1; wire 18 is promoted as D98.7/А:18 to S1:2.
- S1 remains an off-board bracket component and is excluded from generated PCB footprints.
- Map each wire-table А:N point to a package pin before board-model promotion; the table gives point numbers, not pins.
