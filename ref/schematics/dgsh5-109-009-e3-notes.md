# `ДГШ5.109.009 Э3` reviewed transcription and divergence audit

Status: **REVIEWED / DIFF-FIRST TRANSCRIPTION COMPLETE**

This is the index and disposition record for the recovered three-sheet FDC-era
processor schematic. It checksum-pins all 23 owner frames and guards the
already reviewed pin-level transcriptions against the source board. It does
not duplicate hundreds of unchanged `.006` wires into a second hand-maintained
netlist: per the exploitation plan, sheets 1–2 are audited by subsystem and
only new/divergent evidence is transcribed in full; sheet 3 is the wholesale
replacement circuit and is covered pin-by-pin by the linked maps.

## Drawing identity and coverage

| sheet | frames | reviewed disposition |
| ---: | ---: | --- |
| 1 | 1 overview + 8 overlapping details | CPU, bus, decode PROMs, ROM, PIC/PPI/PIT/USART, serial and inter-sheet continuations reviewed against `.006` and the board model. Exact-revision continuations into sheet 3 are adopted; one unmatched tape interrupt continuation remains explicitly unresolved. |
| 2 | 1 overview + 8 overlapping details | DRAM, video, timing and analog boundary reviewed against `.006` and the board model. No wholesale functional replacement is present; native reads correct individual inferred nets and values listed below. |
| 3 | 1 overview + 4 overlapping details | Complete VG93 floppy controller, clock/data separator, write precompensation, drive buffers/status and X4 interface transcribed. This sheet replaces the `.006` tape subsystem rather than supplementing it. |

The detail tiles cover every circuit region. The faint sheet-2 overview is a
layout oracle only; its eight native detail frames are the pin-level evidence.

## Sheets 1–2 divergence audit

| region | `.009` result and source-model disposition | evidence artifact |
| --- | --- | --- |
| D6/D8/D13 memory decode | Direct D6.12→R11→D8.15 and D6.9→R14→D13.1; no hidden inverter. Physical PROM truth and owner continuity agree. | `docs/d6-physical-decode.md` |
| low-I/O decode | D6.10 `REV` enables tied D9 inputs through the exact 1 kΩ pull-up branch. | `docs/io-decode-boundary.md` |
| sheet-1 D7 outputs | Exact sheet 1 draws D7.3 to D29.2; a separate detail joins D7.11 to D105.3 on one stroke. The lower gate was formerly misread as D7, creating a false D7.3/D7.11 tie. Owner continuity closes D105.3 qualified /WR but has not tested it against D7.11/PROM_EN. Keep those nets separate pending a direct physical check. | `docs/d7-gates-source-review.md` |
| sheet-1 D104 supply | The exact power table assigns К170УП2 pin15 to +5 V and pin8 to ground but leaves its +12 V cell blank; the preserved device pinout calls pin16 a +12 V supply. Two owner front views hide pin16's trace under cable. The old solder fit is rejected; a D11-local cross-face fit registers pin16 near (2710,1480) in 200506061 without proving its rail. D104.16 remains a rail-assignment hold pending owner continuity. | `ref/schematics/d104-pin16-rail-conflict.json` |
| sheet-1 C99 decode RC | Exact sheet 1 draws C99=`160` (nominal 160 pF by the native convention) from R17.1/D9.6 to ground. Assembly places it horizontally left of R17. May and July owner photos show no distinct body. The corrected D9-local fit matches the two bare front candidates to separate solder joints within about 5–7 px; a third joint matches R17 lower and has a visible short B.Cu link to the right C99 candidate. The left solder candidate photo-traces to D2.14, grounded on exact sheet 1. Front-to-back same-hole identities, owner ground continuity, and population remain physical checks. | `ref/photos/juku-pcb-2/c99-assembly-photo-review.json` |
| D26 floppy controls | PC2/PC4/PC5/PC6 continue as MOTOR EN, FM/MFM, D_SEL and S.SEL. PC3 is the 5/8-inch clock selection. | `ref/schematics/fdc-x4-ngmd-wire-map.md` |
| direct FDC host bus | Sheet-1 D0–D7 bundle continues directly to D93.7–.14; the inference-era D100 DAL transceiver is disproved. | `docs/fdc-bus-polarity.md` |
| serial/PIC | RxRDY→IR2, shared TxC/RxC baud path, SYNDET switch path and X3/X5/X6 handoff are source-closed. IR4 still says `(3) TAPE RUN INT`, but replacement sheet 3 has no mate; it remains an unmatched source boundary. D14.2/.7 package roles are known, but no traceable D14 wire appears in the photographed serial circuit fields. | `docs/serial-handoff.md`; `docs/d14-exact-source-boundary.md` |
| sheet-2 memory read | Native `-MRD` arrivals close D33.3 and D92.13 onto MEMR, including the factory W11 continuation. | `docs/memory-timing-boundary.md` |
| sheet-2 clocks | Native labels plus owner continuity close D40.11 onto the D59.5 mux-enable source, tied D92.2/.3 timing inputs, and the sheet-3 D95.5/.6 1 MHz continuation. The source, HDL, schematic, and zero-open routed boards now preserve that single-driver net and keep D92 off the separate `PHI2TTL` rail. | `docs/d40-d59-d92-d95-1mhz-route.md` |
| sheet-2 phase pull-ups | Exact `PXL_20260718_101911242.jpg` shows R37 and R36 as separate 360-ohm branches from rail `B` (+12 V) to D35.10/Ф1 and D35.12/Ф2. The R36 feed crosses Ф1 without a junction; the audit guards both modeled phase nets against merging. Physical pad continuity remains open. | `docs/phi2ttl-d29-clock-route.md` |
| sheet-2 D33 clock input | Exact `PXL_20260718_101908284.jpg` prints R46=`200` from D40.14 to D33.9, with C6=`56` from that input node to the return symbol. The model and guarded nets preserve the branch; the native bare-value convention gives C6 nominal 56 pF. | `docs/native-capacitor-values.md` |
| sheet-2 D35 pulse shaper | Exact sheet 2 draws R35=330 Ω from PHI2TTL to D35.13/C29/R106, C29 marked bare `56` (nominal 56 pF by the native convention), and R106=910 Ω to ground. Owner May/July photos instead show a 510R-marked body at R106 and no distinct C29 body. The two-face owner photos support an upper C29-position joint on the R35-lower/R106-upper node and a middle candidate toward a D56.8-grounded rail. The physical D35.13 continuation, actual capacitor population and installed resistor value remain open. | `ref/photos/juku-pcb-2/c29-landing-pair-review.json`; `ref/photos/juku-pcb-2/r106-cross-date-review.json` |
| sheet-2 D34 pulse-shaper population | Both `.006` and exact `.009` sheet 2 give R33=`620` and C5=`560`, drawn between D34.6 and D34.2/R33. The factory assembly labels R33 above D39/D34 and C5 in their gap. May and July owner views show the R33-position body but no distinct C5 body at its drawn height. D34/D39 rows are registered across both faces; one D39.10/XTAL16M annulus is excluded. A short visible B.Cu strip joins D34.2 to the upper R33-left gap joint near front (3098,2345)/solder (1110,2007). Native crop separates the lower joint near (3098,2395)/(1110,2057), whose front trace reaches D34.6. The former two-face bridge claim is retracted. The pair aligns with the factory C5 outline and source terminal roles, making it a strong C5 pad candidate; same-hole continuity and population history remain open. | `ref/photos/juku-pcb-2/r33-c5-population-review.json`; `ref/photos/juku-pcb-2/d34-cross-face-contact-fit.json`; `ref/photos/juku-pcb-2/d39-cross-face-contact-fit.json`; `ref/photos/juku-pcb-2/c5-c82-d39-annulus-exclusion.json`; `ref/photos/juku-pcb-2/d34-pin2-pin6-c5-bridge-review.json` |
| sheet-2 oscillator attributes | Native `.009` detail `PXL_20260718_101908284.jpg` prints R31=`1к`, R32=`1,3к`, and D40 pull-up R34=`12к`, agreeing with owner bodies `1K0`, `1K3`, and `12K`; older `.006` prints 820 ohms, 1,2к, and 13к. Exact `.009` draws C73 without a range, while older `.006` says 4/20; C73's procurement value remains open. | `docs/master-oscillator-boundary.md` |
| sheet-2 analog/video | Populated non-RF video path is retained; `.006` RF-only parts are absent from the `.009` target. Exact `.009` C94 and several passive attributes remain honest photo/measurement boundaries. | `docs/video-analog-boundary.md` |

No further sheet-1/2 difference is promoted merely because a continuation mark
looks similar. Owner continuity outranks both revisions, and unresolved hidden
front-copper routes remain measurement asks.

## Sheet 3 complete circuit index

| circuit | reviewed transcription |
| --- | --- |
| D93 host/static/strap pins | `docs/fdc-bus-polarity.md`, `fdc-controller-static-map.md`, `fdc-hlt-rg-map.md` |
| X4 outputs and drive inputs | `fdc-x4-ngmd-wire-map.md` |
| D95 controller/separator clocks | `fdc-clock-mux-map.md` |
| D106 recovery counter | `fdc-recovery-counter-map.md` |
| D96 read-clock toggle | `fdc-read-clock-toggle-map.md` |
| D97/D102/D101 write precompensation | `fdc-write-precomp-map.md`, `docs/d101-section-a-input-source-review.md`, `docs/d101-output-tie-photo-review.md` |
| D99 one-shot timing | `fdc-d99-timing-map.md`, `docs/d99-q1n-a4-conflict-photo-review.md` |
| DRQ/INTRQ conditioner | `fdc-irq-conditioner-map.md`, `docs/d96-clock2-source-review.md` |
| exact-revision unused pins | `fdc-unused-pin-dispositions.md` |

Together these maps account for every functional D93 pin, all D95/D96/D98/D100/
D106 pins used by sheet 3, both D99 timing networks, and the locally drawn
D28/D97/D101/D102 sections. Drawing-internal R86/R94/R99 reference conflicts
are explicitly overridden only where registered target-board evidence is
stronger.

## Remaining boundaries after transcription

- Exact sheet-1 detail `PXL_20260718_101824181.MP.jpg` identifies the E8
  terminal landings: D26 PB4/pin22 reaches E8.3, PB5/pin23 reaches E8.2,
  and E8.4 carries `CONTRDAT` on conductor 50 to continuation 909. The
  electrical drawing shows three open terminal circles and omits the bridge.
  The exact-revision assembly detail `PXL_20260711_114620466.jpg`, native
  crop `(700,650)-(1600,1150)`, places E8 below D26 and draws a horizontal
  3–4 bridge; the 1–2 row has no bridge line. Thus the factory intended
  E8.3-to-E8.4 selection joins PB4 to `CONTRDAT`, while PB5/E8.2 remains
  separate in that position. The owner front photo
  `PXL_20260710_200455512.jpg`, crop `(1300,1750)-(2650,2600)`, visibly has
  the white insulated 3–4 wire fitted. Registered D26 pin22 near `(1610,2270)`
  has a narrow exposed front run toward its left landing near `(1600,2390)`;
  pin23's contact-2 route stays separate. See
  `ref/photos/juku-pcb-2/e8-bridge-photo-review.json`. Measure both wire
  landings to D26.22 and the X9 `CONTRDAT` landing, plus D26.23 isolation,
  to confirm hidden solder continuity. The current replica model assigns
  `KBD_CONTRDAT` to D26.23 and isolates D26.22, contrary to the exact .009
  source and visible fitted link; the model and routed copper need correction
  after the X9/A50 physical landing is identified. The exposed E8.4 front
  trace descends to one joint in the lower cable row near `(2200,2450)`;
  D26's reflected fit projects it near full-band solder site 6 at
  `(2140,2375)` in `PXL_20260710_200530933.MP.jpg`. This is a useful probe
  waypoint, not an A50 assignment: the archived band has fifteen sites for
  fourteen factory A45–A58 wires.

- D96.9 Q2 runs to the joined D101 A0-A3 inputs in the full sheet-3
  overview; D96.11 reaches the D94.2/D99.9/R89.1 island there. Both physical
  branches need continuity checks. D100.9 joins D99.12 Q2_N, while D100.11
  has an unresolved sheet-1 control continuation.
- D99.10 shares D96.13 and an unread sheet-1 continuation. D99.4 is drawn
  to D94.14, conflicting with owner D94.14-D101.7 continuity; those physical
  endpoints need a three-point probe. D101.1 is source-joined to D26.38 on
  the `IMDRG` sheet-1/sheet-3 continuation; physical continuity is pending.
  Sheet 3 joins D101 section-A inputs pins3/4/5/6 at marked dots; owner
  imagery independently closes pin4 to R92/R99, while physical continuity
  of D96.9 and pins3/5/6 to that island remains unmeasured.
- X4.2–.5 retain revision/cable disposition because target sheet 3 omits them;
  X4.1–.6 are grouped returns on the НГМД side but unseen cable conductors are
  not invented.
- The factory sheet's reset label polarity and physical FDC clock/analog edge
  quality remain bring-up measurements, not missing transcription.

These are external-evidence boundaries. All source-visible `.009` corrections
are represented or explicitly dispositioned; this audit supplies no authority
to fabricate while the separate P0 connectivity and routing gates remain open.
