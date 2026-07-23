# PLAN — working physical Juku recreation

Status date: **2026-07-23**.

Release status: **DESIGN HOLD / PACKAGE VERIFIED**. The promoted zero-open
main-board route and deterministic Gerber/drill ZIP pass the machine package
gates, but this is not fabrication authorization. Complete D2/D30 READY-cycle
timing through `H`/`-BLOCK`, D94 shared-enable/D0 closure, remaining FDC-support
pin closure, source-risk nets, and sourcing decisions still hold release.

This is the sole living project plan for the `ДГШ5.109.009` FDC-era processor
module. Owner photographs of the exact `ДГШ5.109.009 Э3` are the primary
electrical-schematic evidence; the earlier `.006` Э3 scan remains useful only
where it agrees and is subordinate wherever the revisions differ.
Generated evidence belongs in `docs/`; completed experiments and debug history
belong in Git history. Focused execution plans may live under `docs/` only when
they are subordinate to, and linked from, this project-wide plan.

## Definition of done

- **Tier 1 — boots:** a fabricated board powers safely, runs the real ROM,
  produces usable video, and accepts keyboard input.
- **Tier 2 — usable system:** Monitor 3.3, BASIC, EKDOS/floppy, beeper, serial,
  PSU, and keyboard work on physical hardware.
- **Tier 3 — historically faithful:** factory PROM contents, period parts,
  original-style peripherals/enclosure, and comparison with a surviving Juku.

Tape, classroom networking, mouse, and Multibus expansion are outside the
current critical path. The VJUGA/minimal-VGA board is a separate experiment and
is not a prerequisite for this replica, as is Jukuravi, the in-progress
diagnostic harness for the real .009 board (`spinoffs/jukuravi/README.md`).

### Physical acceptance contract

The tier labels above are capability goals, not permission to improvise a pass
on the bench. Before design release, freeze a verification row for every
capability below with a requirement ID, test method, numeric limits where
applicable, exact hardware/firmware configuration, evidence path, and explicit
PASS/FAIL result:

| ID | Capability | Minimum physical evidence |
| --- | --- | --- |
| `T1-PWR` | safe power | recorded no-IC and populated rail voltages/currents, current-limit settings, polarity, temperature observations, and discrepancy disposition |
| `T1-BOOT` | repeatable boot | repeated cold-start/reset results from the released first article, with ROM hashes and jumper population recorded |
| `T1-VIDEO` | usable video | stable readable Monitor output through the selected physical display/cable, with timing and level captures retained |
| `T1-KBD` | keyboard input | every fitted key and modifier exercised through the physical keyboard and cable |
| `T2-SW` | usable software | Monitor 3.3, BASIC, and EKDOS each reach their named physical acceptance point from a documented start state |
| `T2-FDC` | storage | scratch-media read, write, reread, and data-compare through the selected drive/emulator and cable |
| `T2-IO` | beeper and serial | audible beeper result plus physical serial loopback with byte/error counts |
| `T2-PSU` | operating supply | a sustained Tier-2 session on the selected PSU with rails, current, and temperature recorded |
| `T3-FID` | historical fidelity | as-built period-part/PROM inventory, original-style peripheral/enclosure disposition, and a like-for-like comparison record against a surviving Juku |

Simulation, DRC, LVS, and package checks can satisfy analysis prerequisites,
but they cannot close these physical rows. The first-article record must use
`docs/replica-first-article-record.md`; later units need their own acceptance
record rather than inheriting the first article's measurements.

## Current execution dashboard

Only this dashboard, **Release blockers**, and unchecked **Milestones** are the
active project backlog. Long investigation narratives below are retained
evidence and must not be counted as open work merely because they contain
"remaining" or "next". New active work gets a stable ID and an explicit
dependency/evidence link; checkbox counting alone is not a completeness audit.

| ID | Workstream | State | Next gate / decision | Authority or evidence |
| --- | --- | --- | --- | --- |
| `MAIN-P0` | replica connectivity | BLOCKED ON OWNER EVIDENCE | execute the P0 subset of the owner measurement packet; update source and reroute only from accepted evidence | `docs/owner-measurement-shortlist.md` |
| `MAIN-REL` | replica release | DESIGN HOLD | close `MAIN-P0`, sourcing and physical-acceptance definitions; regenerate and independently review the exact package | `docs/replica-manufacturing-readiness.md` |
| `MAIN-BUILD` | first article | NOT AUTHORIZED | after `MAIN-REL`, order, receive, record as-built configuration, and run the staged acceptance ladder | `docs/replica-first-article-record.md` |
| `JRV-HW` | Jukuravi harness | SOFTWARE/ROM GUARDED; HARDWARE BLOCKED | close X3/S1/testpoint measurements, freeze an exact isolated harness build, then run the first physical D0 session | `spinoffs/jukuravi/README.md` |
| `VJ-A` | VJUGA Rev A fixture | DESIGN HOLD | resolve remaining part/orientation review, full-board LVS disposition, fresh package, and independent review | `spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md` |
| `VJ-B` | VJUGA Rev B modular set | ORDER-SAFE CLAIM; OWNER DECISION | decide whether to buy one first-article set; do not begin B2 tape-out before B1 bench evidence | `spinoffs/minimal-vga/docs/rev-b-order-readiness.md` |
| `CVBS` | physical video/CRT model | EVIDENCE-GATED | continue only where a named main-board bring-up question requires it | `docs/crt-cvbs-simulation-plan.md` |

Priority rule: `MAIN-P0` and measurements that directly close it outrank all
spin-off implementation. A spin-off order or scope expansion is a separate
owner decision and never follows automatically from a green package.

### Project risk and change controls

Maintain these as explicit release considerations, not scattered prose:

| Risk | Trigger | Required response |
| --- | --- | --- |
| wrong or counterfeit vintage parts | seller provenance is weak, markings disagree, or incoming test fails | quarantine the part; retain seller/lot evidence; test against a known-good fixture before seating |
| undocumented physical configuration | board, programmed image, jumper, substitute, or rework differs from the released baseline | stop acceptance; record an as-built deviation and decide whether source, procedure, or unit must change |
| power or connector damage | polarity/rail/continuity differs from the pre-power checklist | do not seat ICs or attach peripherals; resolve and repeat the no-IC gate |
| measurement ambiguity | continuity or powered capture conflicts with drawing/model | retain raw evidence, open a discrepancy, and do not convert inference into copper |
| vendor/package drift | vendor preview, capability, or regenerated output differs from the released package | reject the upload, regenerate/review, and record the new exact artifact |
| spin-off resource diversion | a spin-off blocks or delays `MAIN-P0` work | pause the spin-off unless it directly supplies main-board evidence |

The owner is the release and waiver authority. Every waiver must name the
requirement, rationale, compensating evidence, affected configuration, and
whether it expires after the first article.

## Verified repository state

| Area | What is proved | Open boundary |
| --- | --- | --- |
| Digital twin | `cosim` and `juku_top` boot ekta37; framebuffer and keyboard guards pass; uninterrupted HDL reaches EKDOS `A>` and disk BASIC `READY`; the recovered ROMBIOS `0xA0/0xA2` 512-byte write-sector path is implemented in both models and byte-for-byte readback-tested on an explicitly writable disk copy; the C and HDL FDC models share guarded Type-I physical-head versus Track-register motion, update/verify/SEEK-ERROR, dynamic status, D95-selected 2 MHz 3/6/10/15 ms or 1 MHz 6/12/20/30 ms step timing plus respective 15/30 ms verify-settle timing with HLT gating, immediate valid-ID mismatch, four-revolution missing-ID failure, active-low TR00 status/Restore with a 255-step limit, and partial-D0 motion, D95-selected Type-II/III `E=1` 15/30 ms head-settle timing followed by exact HLT gating, exact command-load READY-low Type-II/III rejection with Type-I independence, and exact 15-idle-index head-unload semantics, Type-II multi-record continuation through end-of-track RNF, exact four-revolution missing-ID search, exact `C/S` side-ID comparison with fifth-index RNF, and exact Write Sector `a0` normal/deleted marks with Read Sector bit-5 RECORD TYPE through mounted metadata plus an explicit cross-run companion format, the datasheet's exact 22-byte MFM Write Sector preload interval plus streaming one-byte DRQ/LOST-DATA contract (read overwrite and later-write zero substitution), datasheet completion/status acknowledgement and the full Type-IV Force Interrupt event/acknowledgement/disarm lifecycle, a CRC-checked six-byte Read Address command, index-gated 6,250-byte one-revolution MFM Read Track reconstruction including `FB`/`F8`, and an index-gated/preloaded 6,230-write representable MFM Write Track formatter with all ten sector payloads and marks, partial-D0 persistence, and explicit flat-image representation faults; an extended exact EKDOS replay proves all 18,489 observed D93 accesses select 1 MHz through D26 PC3/D95; Monitor 3.3 reaches its cursor and selected commands; the cosim-referenced deep guard reaches `CTRACE-END` across 130,000 reads; runnable selection comes directly from the corrected, validated physical D6 table, including the owner-closed D7.8→D105.1/D6.15 A7 qualifier, while the old functional decoder is retained only as a diagnostic comparison; the official D1-D5-DB-ROM topology and period КР580ВК38/ВА87 diagrams exclude a hidden D5 inversion; exact static/runtime guards preserve the CMA/NOP firmware-profile split; standalone ВА87 behavior and the source-proved D23-D25 paths exhaustively guard all 256 values in both directions. The former opt-in D100/DAL builds remain diagnostic experiments only: recovered `.009` sheet 3 proves D100 is instead the drive-output buffer. The same sheet now closes D95's complete 1/2 MHz D93 and 4/8 MHz separator clock mux, which is structural and LVS-visible | Explain the historical purpose of the non-adopted CMA-profile variants; exact physical shared-DRAM video-slot/DOUT timing, complete controller behavior beyond the guarded media subset (including D93.24 oscillator accuracy/edge quality, D93.34 TR00 drive-status continuity, step-interface timing, arbitrary flux/deleted-data layouts beyond the companion format, and physical D93.32 READY/index timing through the source-proved E11 HLT strap), cartridge BASIC loading, and analog behavior |
| Connectivity | `sync/check.sh` reports 117 mapped instances and 308 matched nets; the physical D2/D6 PROM tables, measured D2/D30/D105/D13 READY/DBIN handoff, owner-proved D13-inverted FDC reset, D35 frame-interrupt inversion, D41 timing rails, reset/USART paths, D10 IR0/IR1 external-input pull-down paths, D7 strobe topology, D54/D55/D56 timing crossings, D95 clock mux, the owner-closed D40.11/D59.5/D92.2/.3/D95.5/.6 1 MHz slot rail, D106 recovery counter, D96 read-clock toggle, D28/D98 status conditioning, R94 DRQ pull-up, D97/D102/D101 write-precompensation chain, D99 timing/control paths, and the adopted photo/wire-table endpoints are source-modeled and LVS-visible | Routed-snapshot parity, omitted remote endpoints, behavioral correctness, analog waveforms, and historical correctness of assumed nets |
| PCB package | The promoted route has exact live-source identity: 322 footprints, 2,436 pads, 30,904 copper items across 412 serialized nets, zero opens, zero electrical blockers, and zero dangling tracks/vias under stable KiCad. The Gerber/drill inventory, exact-count cosmetic waiver, four-tool mixed-plating drill geometry, 0.20–1.00 mm power-width envelope, independent render, deterministic ZIP, and checksums all pass. Exact routing evidence is `ref/routing/zero-open-promoted-topology.json`; package evidence is `docs/replica-manufacturing-readiness.md`; the upload ZIP checksum is regenerated after every route promotion | The verified package remains under design hold and must not be uploaded or ordered until D2 timing, D94 shared-enable/D0 closure, remaining FDC-support functional pins, source-risk nets, and sourcing decisions close. Factory-wire landing geometry and construction fidelity remain explicit bring-up checks; any source or route change requires complete package regeneration and a new exact checksum |
| Sources/media | Factory drawings, 16 Baltijets PDFs, ROMs, EKDOS source, raw disks, system binaries, 50 owner photographs, cross-machine validated physical D2 `.037`/D6 `.038`/D8 `.039`/D94 `.092` dumps, the adopted third-source archival D15/D16 pair, 26 photographs of `ДГШ5.109.009 СБ` sheet 1, the ДУБЛИКАТ scan of its sheets 2-6 (таблица соединений, transcribed), and owner RE3 scans are local and checksum-guarded | Remaining continuity reads and the cartridge BASIC loading procedure; Baltijets programming-disk payloads are optional preservation provenance |

A preserved salvage against the pre-owner-timing-refresh
321-footprint/2,434-pad source established the routing-convergence baseline.
Same-name/additive migration imported 8,397
items; one transactional DRC round removes 558 blocker-implicated migrated
items and retains 7,839. The result has exact source identity, 883 uncapped
opens, 199 dangling tracks, 56 dangling vias, and zero electrical DRC findings.
It improves both the 1,814-open bare source and the earlier documented
1,190-open fresh-source trial, but remains convergence evidence rather than
production copper. Exact hashes and counts are guarded in
`ref/routing/current-source-salvage-baseline.json`.

An uncapped connectivity guard then transactionally removes 2,872 migrated
copper items from that historical source baseline. The exact open count improves
from 883 to 677, all 199 dangling tracks and 56 dangling vias are eliminated,
and all electrical blocker categories remain zero. Two hundred eighty-five
bounded nonzero-gap proposals, including P5V, STSTB, GND, W10_QA_SEL, D40Q1_D39,
LATCH_B, REV, SER_TXD_INV, D6_V_ENABLE, MEMW, D40Q2_D33, D42_Q,
D106_PRESET_HIGH, D101_D02_R92_R99, X4_DSEL1_N, VID_MUX_G, RAS, PROM_EN,
FDC_IRQ_CONDITIONED_N, SER_TXD, LATCH_PRE, D97_RC2_C19_R100, D97_RC1_C16,
D99_RC2_TIMING, FDC_CLK, FRAME_INT, D39Y, D102_C2_C20, D92_NOACC,
D100_CONTROL_SHEET1_BOUNDARY, D33_CLK_RC, RES_RC, FDC_READY, OSC_PRE,
SEP_D28_CLK, D97_C1_C16, D102_RC2_C20_R108, FDC_INTRQ, PRECOMP_CASCADE_2,
V3_RC, DB0, RAIL_H, P12V, MA3, BA13, D53_Y1_R50, X4_TR00_N, CAS_PRE, D33_O4,
D102_RC1_C22_R102, RESIN, MA0, D34_RC_NODE, PHI2TTL, D98_Y1_R94, X4_DIR_N,
X4_HLOAD_N, X4_WR_GATE_N, D13_4_D105_2, XTAL16M, D103_LD, CAS, XTAL_TRIM,
X4_MOTOR_ON_N, X4_SIDE_SEL, X4_READY_N, X4_RD_DATA, S_OC, BA11, BA12, BA14,
X4_INDEX_N, DB1, ROE, CLKG_D33, X3_HARNESS_1, PHI2, WREQ_N, D40QA, MA5,
OSC_FB, FDC_RE_N, D40_CTRL_PULL, MA7, VT2_BASE, D102_C1_C22, USART_TXRDY_IRQ,
BA15, D99_RC1_TIMING, D36_D33, FDC_RAW_READ, A10, A12, A15, SEP_D106_Q3, IORD,
ROM_CS_A000, S_DSR, FDC_CS_N, DB2, S_RTS, W10_QA_SEL_D50, BA0, VA8, X4_STEP_N,
ROM_SEL, D53_Y2_R51, X2_PB7, X2_PB6, X2_PB5, X2_PB4, X2_PB3,
FDC_SEPARATOR_CLOCK, MA6, WR, S_CTS, D93_TEST_WF_VFOE, CLKG_D36, and
FDC_EARLY_SEL, DC3, D99_RC2_TIMING, PRECOMP_TAP_1, D105_MEMW_INV, BA1,
SER_DTR, ROM_CS_EXP17, D53_Y0_R49, DC1, PHI1, IR7, DC0, IOWR, D39Y,
D39_MEMCYC, BA11, PHI2TTL, FDC_DRQ, D34_SIG, FDC_DDEN, D40Q1_D39,
D99_C1_TIMING, RESET, OSC, DBIN, TIMING_TAG17, CLK_123M, CAS, FDC_STEP_TO_D100,
AVDC, KBD_K0, VID_CPU_SEL, VA11, FDC_PRECOMP_WRDATA, IORC_N, MRC_N,
D98_Y3_S1_2, S3_3, RAIL13, D39_MEMCYC, D105_WAIT_STAGE, VIDEO_OUT, RAIL12,
SOUND_CLAMP, D94_D1_D99_A2N, RAIL14, SND_BASE,
D96_TOGGLE_FEEDBACK, S3_6, X4_WR_PROTECT_N, MA4, VID_MIX2, D33_CLK_RC,
MEMW_D7P2, SND_OUT, MEMR_D7, FDC_WE_N, STSTB_D38, D97_C2_C19_R86_TARGET,
PST_CLK, DB3, SER_RXD, S_DTP, D34_RC_DRIVE, A14, A9, RAM_RD_OE,
D97_RC2_C19_R100, MEMR, BA7, USART_RXRDY_IRQ, X4_TG43, PRECOMP_CASCADE_1, DB5,
DC5, SER_DSR_N, S_OC, LATCH_SIG, FDC_LATE_SEL, X4_WR_DATA_N, D33_D36,
D33_6_D36, W_RAIL16, S_SOUT, VA1, X2_IRQ0, SER_CTS_N, DB6, DB7, DC6, DC7,
LOAD_PRE, FDC_WG_TO_D100, LATCH_A, FDC_TG43_TO_D100, VA4, FDC_HLD_TO_D100,
FDC_WDATA_DELAY_IN, VERT_RTR, VA0, PRECOMP_TAP_3, DC2, D53_Y3_R52, VA9,
READY_D, ROM_CS_8000, D99_C2_TIMING, S3_1, VA2, FDC_DIR_TO_D100, POF,
ROM_CS_D15, BA8, FDC_WPRT_STATUS, FDC_INDEX_STATUS, VA3, BA2, BA4, IO_CYCLE_H,
FDC_TR00_STATUS, ROM_CS_6000, INHIB_STATUS_BOUNDARY, VA13, WR, MEMW, HLDA, and
ROM_CS_4000, SHIFT_G, M12V, D26_PC1_D3_I3, D26_PC0_D3_I5, D39_O8, S_TTL_D3,
S3_4, KBD_SC1, D105_10_H, MA4, D13_4_D105_2, KBD_SC2, FDC_WE_N, SER_TXD_INV,
CLK_123M, OSC_PRE, KBD_SC3, IOWR, PHI1_D35, D97_C2_C19_R86_TARGET, PHI2_D35,
CAS, BA14, BA13, DB6, DB7, SER_TXD, RAIL14, S_SIN, DB2, SER_RTS, D40QA,
FDC_RAW_READ, ROM_CS_D16, D56_QN_D34, D56_Q2_D34, DB0, DB4, DB1, X2_PC1,
LATCH_B, X2_PC2, X2_PC3, X2_PB0, X2_PB1, X2_PB2, BA11, VA5, FDC_RCLK, BA5,
DB3, PRECOMP_TAP_2, S3_2, D40Q2_D33, BA2, BA3, X4_DSEL0_N, BA1, CS_D10, BA10,
VA6, VA7, BA9, VA10, IOM_N, VA15, MWC_N, INHIB_N, BA6, BA15, D94_A4_D101_Q0,
BA13, CS_D11, CS_D27, IOWC_N, AMWC_N, MEMR, BA12, X2_IRQ0, IORC_N, P12V,
D6_V_ENABLE, DBIN_GATED, SYNC, D25_T, FRAME_INT, BA7, OSC, VIDEO_OUT, XTAL16M,
VID_MIX1, E2_COM, INTA, IOWR, FDC_DDEN, D30_Q2N_D29_AIN7, FDC_DRIVE_SIZE_5_8,
WREQ_N, PIT_BAUD, ROE, STSTB_D38, CTR_LD, RAM_OUT_EN, MA2, MA1, S3_5, DB7,
MEMR, BA9, BA1, D3_O4_D6_A6, E3_COM, INTR, RES_RC, D13_4_D105_2, D105_10_H, CS_D54, FDC_DSEL_IN, FDC_MOTOR_EN, FDC_SIDE_SEL, INT6_RAW, DB4, and VA14, each independently reduce the uncapped
graph, reaching 9 opens; all six hundred sixty-eight are promoted. The final
six hundred sixty-four are
selected by a transactional orchestrator that rejects
capped-only marker advances and continues searching.
Its conservative multilayer search is exhausted through 260 mm, beyond the
252.637 mm maximum residual candidate, so all distance-ranked gaps have now
been attempted in that mode.
The next rule-accurate multilayer phase uses 0.21 mm clearance against the
board's 0.20 mm rule and a 0.25 mm lattice; its accepted routes are also guarded
by complete KiCad DRC comparison. Uncapped sweeps exhaust all remaining
distance-ranked candidates through 260 mm, beyond the 252.637 mm maximum
residual candidate, so every distance-ranked gap has been attempted in that
mode.
A targeted finer-lattice phase uses 0.205 mm clearance and a 0.125 mm grid;
its `MA2`, `MA1`, `S3_5`, `DB7`, `MEMR`, `BA9`, `BA1`, `D3_O4_D6_A6`,
`E3_COM`, `INTR`, `RES_RC`, `D13_4_D105_2`, `D105_10_H`, `CS_D54`, `FDC_DSEL_IN`, `FDC_MOTOR_EN`, `FDC_SIDE_SEL`, and `INT6_RAW` attempts pass the same complete KiCad DRC guard.
DB4 then closes through a guarded conflict-derived transaction that removes six
non-source blockers and restores DB0, DB3, DB7, DC7, MEMW, and RESET before
publication. VA14 similarly removes one S3_4 blocker and restores S3_4 on the
alternate 0.10 mm lattice before publication.
The resulting nine-open topology is classified in
`ref/routing/current9-residual-topology.json`. GND cannot find a legal target
route after its bounded rip-up, while IOWR_RAW_N cannot restore BA11, CS_D10,
and the final VA13 gap. ROM_CS_EXP18 and INT7_RAW have no diagnostic path on
the 0.125 or 0.10 mm lattices. D3_O6_D6_A5, CS_D26, CS_D57, CS_D55, and
D94_D0_BOUNDARY require 26, 35, 33, 30, and 66 removable conflicts,
respectively, exceeding the guarded twenty-item limit. The localized rip-up
phase is therefore exhausted; these nets require wider topology changes or
net-specific routing methods.
The first wider topology step relocates BA11's layer transition to a legal via
at `(65,125)` mm and forces CS_D10 around its former straight B.Cu corridor.
Both swaps preserve nine opens, remove no source-owned copper, and retain the
complete DRC baseline. IOWR_RAW_N no longer displaces either net; its remaining
failed restoration is VA13, which is the next pre-route target.
VA13's two-via F.Cu bridge is then replaced by a legal 22.561 mm route between
its B.Cu endpoints, again preserving nine opens and all source copper. The
preferred IOWR_RAW_N transaction no longer displaces BA11, CS_D10, or VA13;
BA12 is now its first unrecoverable restoration and the next pre-route target.
BA12's two conflicting F.Cu items are replaced by a 37-item multilayer detour;
its entry layer change is shifted onto the `(86,122)` mm endpoint with a short
B.Cu bridge to `(85,122.9)` mm. This fourth source-preserving swap retains nine
opens and the complete DRC baseline, and BA12 now restores inside the preferred
IOWR_RAW_N transaction. BA15's 7.018 mm corridor is the next failed restoration.
The gap router now accepts deterministic sub-grid phases through
`JUKU_ROUTE_GRID_OFFSET_X_MM` and `JUKU_ROUTE_GRID_OFFSET_Y_MM`. A legal
`(0.05,0)` mm phase replaces BA15's two-item corridor with thirteen B.Cu
segments, again preserving nine opens and all source copper. This phase forces
IOWR_RAW_N onto a wider 38-conflict alternate path that does not displace BA12
or BA15; WREQ_N, A12, A9, BA1, and BA13 restore before BA5's remaining 6.364 mm
gap becomes the next pre-route target.
The rip-up orchestrator now supports per-net restoration lattice offsets and
optional retained checkpoints. BA5 closes completely at `(0.05,0)` mm when it
is restored before A12, but that ordering seals A12's 10.308 mm B.Cu gap;
restoring A12 first instead seals BA5's 6.364 mm gap. Exhaustive 0.02 mm phase
sweeps, including multilayer A12 attempts, prove this mutual exclusion on both
retained intermediate boards. The next topology step must separate A12 and BA5
rather than retry either restoration order.
Explicit diagnostic and target lattice offsets are now independently supported.
A complete 0.125 mm phase sweep finds four additional IOWR_RAW_N diagnostics at
`(0.025,0.1)`, `(0.05,0.075)`, `(0.075,0.05)`, and `(0.1,0.025)` mm; they need
36, 28, 29, and 26 removable conflicts and avoid A12. None can produce a legal
0.205 mm target route after its bounded rip-up, including both matched-phase
and default-target retries of the 26-conflict case, so this alternate branch is
exhausted.
A separate widened transaction is successful on CS_D26. Its 177.308 mm route
removes 34 non-source conflicts, restores all twenty affected nets across the
0.125, 0.10, and 0.0875 mm grids, and also closes the previously exhausted GND
residual. Two newly dangling non-source tracks are pruned afterward. The result
has 7 opens, 26,082 routed items, no missing source copper, and the unchanged
710 cosmetic-only DRC reports. Exact evidence is in
`ref/routing/current7-residual-topology.json`; cumulative promoted closures are
now 670.
Fresh diagnostics against that exact seven-open board reclassify five of the
remaining gaps. ROM_CS_EXP18 has no path on either the 0.125 or 0.10 mm
lattice. IOWR_RAW_N and D3_O6_D6_A5 require 48 and 61 removable conflicts.
CS_D57 requires 49 conflicts on the default lattice and 46 at 0.10 mm;
CS_D55 requires 52 and 56, respectively. None is eligible for the current
forty-item guarded transaction. INT7_RAW also has no diagnostic path on either
lattice, while D94_D0_BOUNDARY needs 75 removable conflicts across 29 affected
nets. Every residual on the seven-open board is therefore freshly classified;
the next bounded work requires net-specific topology changes rather than an
unguarded rip-up.
A widened CS_D57 transaction then proves that the former forty-item ceiling
was conservative: its 46 removable conflicts are bounded and all but PROM_EN
restore, producing a DRC-neutral equal-open swap after 23 non-source orphan
items are pruned. PROM_EN has no route on the default lattice, but a 0.10 mm
phase sweep finds an eight-conflict path at `(0.075,0.075)` mm that avoids
CS_D57. That second transaction restores BA10, BA12, BA5, GND, IORD, and
ROM_CS_4000 and reduces the board to 6 opens and 26,570 routed items. Stable
KiCad reports the unchanged 710 cosmetic-only findings, zero electrical or
dangling findings, and no missing source copper. Exact evidence is in
`ref/routing/current6-residual-topology.json`; cumulative promoted closures are
now 671.
On the six-open topology CS_D55 drops from 52 to 39 removable conflicts. Its
default legal target route has one clearance violation, but a `(0.025,0.1)` mm
target phase closes it and restores twenty-one affected nets; only DB5 remains,
so the result is a DRC-neutral equal-open swap. After 30 safe orphan items are
pruned, a DB5 phase sweep finds a one-conflict `(0.05,0.075)` mm route that
displaces only IORD. Restoring IORD and pruning 94 more orphan items produces a
5-open, 27,050-item board with no missing source copper, no electrical or
dangling findings, and the same 710 cosmetic reports. Exact evidence is in
`ref/routing/current5-residual-topology.json`; cumulative promoted closures are
now 672.
On the five-open topology, IOWR_RAW_N's default route needs 50 conflicts, but a
four-phase sweep reduces it to 33 at `(0.1,0.025)` mm. Unlike the same phase on
the older nine-open board, the legal 0.205 mm target route now succeeds. BA1,
BA11, D13_4_D105_2, D25_T, HLDA, IORC_N, IORD, both MEMW nets, PROM_EN, and all
three displaced ROM-select nets restore across the proven lattices. Pruning two
new non-source orphan items yields a 4-open, 27,281-item board with no missing
source copper, no electrical or dangling findings, and the same 710 cosmetic
reports. Exact evidence is in `ref/routing/current4-residual-topology.json`;
cumulative promoted closures are now 673.
After that bus-topology change, INT7_RAW gains a diagnostic path for the first
time: a 0.10 mm route removes 32 conflicts and restores A15, ADR4_N, both ADRF_N
branches, BA0, both BA1 branches, CCLCK, D30_Q2N_D29_AIN7, DAT7_N, DB3, DB5,
INTA, IOM_N, IORD, P5V, RESET, SER_RTS, and SER_TXD. Eight new non-source
orphan items are pruned. The result has 3 opens and 27,765 routed items, no
missing source copper, no electrical or dangling findings, and the same 710
cosmetic reports. Exact evidence is in
`ref/routing/current3-residual-topology.json`; cumulative promoted closures are
now 674.
A widened 0.10 mm D94_D0_BOUNDARY transaction then removes 66 non-source
conflicts along its 252.637 mm route. Restoration across the 0.125, 0.10, and
0.0875 mm lattices recovers the affected topology; a follow-up prune removes
15 newly exposed orphan items without touching source copper. Stable KiCad
9.0.8 DRC leaves only D3_O6_D6_A5 and ROM_CS_EXP18 open: the result has 2 opens,
28,123 routed items across 409 nets, zero electrical or dangling findings, and
the unchanged 710 cosmetic reports. Exact evidence is in
`ref/routing/current2-residual-topology.json`; cumulative promoted closures are
now 675.
A 0.10 mm D3_O6_D6_A5 transaction next removes 39 non-source conflicts and
closes its 172.151 mm gap, but leaves one short MEMW branch open after restoring
the other affected topology. Pruning 77 safe orphan items exposes one retained
source ROE endpoint. A MEMW phase sweep finds a two-conflict route at
`(0.025,0.075)` mm, restores BA12 and BA5, and a direct 2.06 mm B.Cu bridge
reconnects the ROE endpoint to its existing via. Stable KiCad 9.0.8 DRC leaves
only ROM_CS_EXP18 open: the result has 1 open, 28,612 routed items across 410
nets, zero electrical or dangling findings, and the unchanged 710 cosmetic
reports. Exact evidence is in `ref/routing/current1-residual-topology.json`;
cumulative promoted closures are now 676.
The final ROM_CS_EXP18 gap is now closed in a separately guarded recovery
topology. Legal F.Cu breakouts escape both DIP pad cages; a
`(0.025,0.0625)` mm diagnostic phase exposes a zero-fixed, 32-conflict corridor
and the restored 0.205 mm route closes the 42.433 mm remainder. A follow-up
ROM_SEL transaction closes that displaced select branch. After safe orphan
pruning and phased BA13 recovery, stable KiCad 9.0.8 DRC reports only BA2,
BA14, and BA15 open, with 28,904 routed items across 411 nets, zero electrical
or dangling findings, and the unchanged 710 cosmetic reports. Exact hashes are
checkpointed in `ref/routing/rom-closed-recovery-checkpoint.json`; this is a
recovery milestone rather than the promoted frontier until those three
displaced nets close.
The BA14 cleanup gap is now closed as a second recovery checkpoint. Retaining
the fine-grid diagnostic board exposed a D8.5 pad-channel transition; moving
that transition to `(83.25,110.25)` mm and collapsing seven displaced ROM_SEL
items to one true gap let the guarded 0.10 mm closer restore ROM_SEL on a new
7.666 mm path. Independent stable KiCad 9.0.8 DRC leaves only BA2 and BA15
open: 28,953 routed items across 411 nets, zero electrical or dangling
findings, and the unchanged 710 cosmetic reports. Exact hashes are in
`ref/routing/rom-closed-two-residual-checkpoint.json`; this remains a recovery
frontier until the last two displaced nets close.
BA15 is now closed in a third recovery checkpoint. A zero-fixed 24-conflict
fine-grid route closes the original 72.009 mm gap; bounded recovery, a 0.01 mm
REV clearance correction, and guarded pruning reduce the displaced topology to
a local 3.926 mm BA15 remainder. A final five-conflict transaction closes that
remainder and restores ROM_CS_D16, ROM_CS_EXP18, and ROM_SEL. Independent
stable KiCad 9.0.8 DRC leaves only BA2 open: 29,454 routed items across 411
nets, zero electrical or dangling findings, and the unchanged 710 cosmetic
reports. Exact hashes are in
`ref/routing/rom-closed-one-residual-checkpoint.json`.
The final BA2 recovery is complete and promoted to
`kicad/juku_routed.kicad_pcb`. A zero-fixed 31-conflict transaction closes the
56.957 mm BA2 remainder and restores 19 displaced branches across the ROM
selects, address bus, data bus, interrupt, CAS, and ground nets. The final
3.930 mm REV cleanup uses a four-item BA15 topology swap; a shifted 0.0875 mm
phase restores BA15 over 2.585 mm. After 46 final safe tail prunes, independent
KiCad 9.0.8 DRC reports zero opens, zero electrical blockers, zero dangling
items, and 701 exact-count cosmetic review findings after stable-library
cleanup. The source-parity gate proves
321 footprints, 2,434 identical pads, and zero coordinate delta. The promoted
board has 29,780 routed items across 412 nets. A later owner-timing topology
refresh reassigns D55.15/.18 and D56.10/.2 to their sheet- and continuity-proved
nets, replaces the four affected connections with 121 segments and nine vias,
and preserves zero opens and zero electrical blockers; exact evidence is in
`ref/routing/zero-open-promoted-topology.json`; the matching deterministic
package is pinned in `ref/routing/zero-open-fabrication-package.json`, and
cumulative promoted closures are now 677.
The separately preserved historical candidate remains useful for drift
auditing: it has 265 pad-net mismatches and 224 moved pads against the live
source, while the promoted board above has exact source identity.
The standard guarded front/back A* search is also exhausted without an accepted
route across 48.43–50, 65–70, 75–80, and the tested bands from 90 through 130 mm;
the tested search ceiling and zero-yield ranges are recorded to prevent repeats.
Exact hashes, parameters, and tool provenance are guarded in
`ref/routing/current-source-uncapped-prune.json`; this remains convergence
evidence rather than production copper.

The routed-refresh tool now proves and optionally retains additive/renamed
copper when every old endpoint survives at the exact same pad coordinate on
one current net and the old endpoint set is a strict subset. Against the
preserved zero-open checkpoint, 28 mappings pass that proof and five still
carry copper. After the ordinary DRC-feedback quarantine, this preserves 22
additional track/via items and closes four current-source gaps with zero
electrical-category findings. Splits, removed endpoints, and every moved pad
remain quarantined. A second item-level DRC salvage now recovers useful
same-name branches without relaxing safety: it removes 496 migrated items
actually implicated by current KiCad blockers, retains 17,582 clean items, and
starts at 433 honest gaps. Guarded A* routing now reaches
23 gaps with 32,475 copper items, exact parity across all 2,395 current source
pads, and zero short, clearance, crossing, hole, or edge findings. The decisive
follow-up uses the board-legal 0.21 mm clearance instead of the earlier
conservative 0.45 mm proposal keep-out; it closes 111 gaps after targeted INTR,
PROM_EN, and CS_D54 work. A generic DRC-derived rip-up transaction removes only
non-source copper named as a direct blocker, routes the target, restores every
affected net, and publishes only a net improvement with no DRC-class increase.
It closes INTR around one BA5 item; a later clean-path BA13 retry reaches the
45-gap boundary. Exact 0.20 mm board-rule clearance plus 0.10, 0.125, 0.15,
0.175, and 0.1375 mm lattice diversity then closes IOWR, D40QA, VA10, BA1,
D105_10_H, both ROE gaps, VA12, DBIN_GATED, CS_D55, and the
D6_A7_D105_I1_BOUNDARY, reaching 34 gaps. A bounded mixed-blocker transaction
then retains the fixed D44/R40/R41/R44 pad corridor, displaces only ten explicitly
named migrated-copper blockers, closes BA0, and restores the affected nets on
0.10/0.15 mm lattices, reaching 33 gaps. A six-item E3_COM transaction restores
CTR_LD, E2_COM, GND, and VID_CPU_SEL and reaches 32. A fourteen-item DB7
transaction then restores BA10, BA5, CS_D27, CS_D54, and CS_D55; it also removes
only the two pre-existing migrated vias made newly dangling by that
displacement. DB7 closes and an obsolete intermediate CS_D57 copper island
disappears, leaving its one honest pad-to-track gap; the transaction makes a
two-open net improvement and reaches the 30-gap boundary. Fresh full-distance
0.10, 0.125, 0.1375, and 0.15 mm exact-clearance sweeps
accept nothing further. Larger bounded diagnostics prove that removing DC4's
21-item or VA15's 28-item migrated-copper set still leaves the fixed-corridor
target gap. CS_D57 routes after a 25-item displacement, but complete restoration
ends at 33 opens: prioritizing D25_T recovers its two branches only by consuming
AMW_N or CS_D55 space, so tested orders cannot beat the 30-open checkpoint.
Read-only blocker surveys then identify CS_D26's bounded 17-item topology. Its
DRC-neutral equal-open swap closes CS_D26 but exposes D53_Y2_R51; a second
one-item transaction routes that replacement and restores CS_D26, reaching the
29-gap boundary. A further composite topology chain uses a retained stable
KiCad DRC marker to avoid nightly representative-endpoint variation on BA2.
It temporarily trades BA2 for BA0 and VA8, then closes those replacements in
three guarded transactions. The final 0.15 mm-grid VA8 transaction displaces
only four migrated items and restores S3_3, VID_CPU_SEL, and P5V, reaching the
current independently verified 28-gap boundary. Stable KiCad DRC reports 199
track-dangling and 46 via-dangling findings and zero electrical blockers. A
fresh full-distance 0.10 mm, 100 mm-margin sweep exhausts all 28 signatures
without acceptance; its only geometric result is a marginal, DRC-rejected
D26_PC0_D3_I5 proposal. That 0.20 mm-clearance path misses four fixed pads by
only 2–4 µm, while a conservative 0.205 mm proposal margin finds a different
path with no blockers and legally closes
the net, reaching the independently verified 27-gap boundary. Endpoint-correct
0.10, 0.125, 0.1375, and 0.15 mm sweeps first exhaust all 27 residuals without
an additive acceptance.
The next bounded VA6 diagnostic removes 13 migrated items but still cannot
route through the fixed D51 pad corridor, so it is not adopted.
Gap selection now resolves KiCad track-marker UUIDs to their nearest real
copper endpoints instead of routing from track midpoints. Replaying the bounded
MA1 transaction with endpoint-correct restoration displaces 14 migrated items,
closes MA1, and restores W10_QA_SEL, both VID_MUX_G branches, VA2, VA10, both
VA11 branches, both MA0 branches, and MA2. The decisive 0.1375 mm MA0 phase
turns the former equal-open swap into a real 27-to-26 improvement. A subsequent
0.125 mm exact-clearance sweep closes MA6 and establishes the current
independently verified 25-gap boundary. The board has 31,992 copper items;
stable DRC retains 199 track-dangling and 46 via-dangling findings and no
electrical blockers.
The next endpoint-correct blocker ranking rejects the shortest alternatives:
MA7 needs 54 migrated items and ten fixed blockers; BA5 has no path even at a
0.10 mm diagnostic clearance; VA15 still cannot cross fixed D51/E14/R45 after
all 19 migrated blockers are removed; and MEMW_D7P2 needs 38 items across
thirteen nets. A 17-item VA13 transaction closes its first branch but creates
two same-coordinate MA1 layer joins with no legal via position. Tested restore
orders end at 27 opens or have a theoretical floor of 26, so that topology is
also discarded.
The decoder/video follow-up finds no 0.10 mm diagnostic path for CS_D10, IORD,
or W10_QA_SEL_D50. CS_D11 displaces 18 items but its legal target still clips
fixed D9.6; S3_1 and PHI1_D35 retain larger fixed-pad sets. PHI2_D35 exposes a
useful split-phase case: a 0.10 mm diagnostic identifies nine conflicts, while
only the 0.1375 mm target lattice clears D35.2. `close_gap_by_ripup.py` now
supports an independent `--diagnostic-grid-step` so that guarded transaction is
representable. It produces a DRC-neutral PHI2_D35-to-D36_D33 swap. A chained
D36_D33 transaction can restore PHI2_D35 and the small video/timing branches,
but both tested restore orders leave P5V and POF replacements and cannot beat
26 opens, so neither swap is adopted and the 25-gap checkpoint remains current.
The left-edge decoder survey then compares DC4 (24 conflicts), DC2 (16),
CS_D57 (27), and DC7 (8). DC7 is the bounded topology: legal target routes
exist on 0.10, 0.125, and 0.15 mm lattices after displacing only DB1, DC0, DC5,
DC6, and ROE. Restoring DC0 before DC5 merely trades DC7 for a 3.536 mm DC5
gap. Reversing that order closes all three DC5 branches first, then restores
DC0, DB1, and ROE, yielding a guarded 25-to-24 improvement. Two orphaned
migrated vias are removed; independent DRC reports 199 track-dangling and 45
via-dangling findings, zero electrical blockers, 32,167 copper items, and exact
2,395-pad parity. Fresh 0.10, 0.125, 0.1375, and 0.15 mm sweeps exhaust all 24
remaining signatures without acceptance, establishing that intermediate
24-gap boundary. Re-diagnosing DC2 on the accepted topology exposes 25
migrated blockers across A10, DB0, DB1, DC3, DC5, HLDA, INTA, and MEMW. Legal
0.20 mm-clearance target routes exist on the 0.10, 0.125, and 0.15 mm phases.
Restoring DB0 first merely trades DC2 for a 19.377 mm A10 gap; restoring A10
before DB0 instead reconnects every displaced branch and produces a guarded
24-to-23 improvement. Three transaction-orphaned migrated vias are removed.
Independent DRC retains 199 track-dangling and 45 via-dangling findings with
zero electrical blockers; exact 303-footprint/2,395-pad parity holds. Fresh
0.10, 0.125, 0.1375, and 0.15 mm sweeps exhaust all 23 residual signatures
without acceptance, establishing the current 23-gap boundary.
A current-lineage 0.1125 mm/100 mm-margin sweep now exhausts all 23 signatures
as well, with 21 proved no-path results and two bounded timeouts. Its new
CS_D11 route-specific diagnostic identifies 30 removable blockers across
twelve nets, but removing all of them still cannot decrease the CS_D11 gap
count around the retained D9 pad corridor. The rejected transaction and exact
tool/board hashes are recorded in
`ref/routing/current23-grid01125-exhaustion.json`; the 23-gap checkpoint remains
authoritative.

The next current-topology survey rejects MEMR at the 0.10 mm diagnostic stage
and finds that CS_D57 has grown to 33 removable conflicts across fourteen
nets. DC4 and VA9 both admit legal target routes after bounded displacement,
but neither chain improves the checkpoint. DC4 displaces 28 items across
thirteen nets; restoring HLDA first recovers every branch except one 14.080 mm
GND replacement, producing a guarded 23-for-23 swap. That GND gap displaces 26
items, but every tested legal target topology leaves 0.510 and 36.009 mm MEMW
replacements and has a 24-open floor. VA9 displaces 27 items across twelve
nets. Its 0.125 and 0.1375 mm target routes inevitably expose two BA10 branches
plus BA13 and VA12 gaps that cannot route even when attempted before the other
restorations; the complete P5V-first transaction ends at 26 opens. Both chains
are discarded and the independently verified 23-gap checkpoint remains
authoritative.

The long-net follow-up ranks WR at 27 removable conflicts across sixteen nets,
D6_V_ENABLE at 31 across sixteen, D3_O6_D6_A5 at 57 across twenty-seven, and
RAM_OUT_EN at 65 across nineteen. WR has legal 0.125 and 0.1375 mm targets, but
both immediately create an all-phase-unroutable 1.980 mm STSTB_D38 replacement,
so its optimistic floor is an equal 23-open swap. D6_V_ENABLE has legal 0.10
and 0.125 mm targets. A BA15-first transaction restores both BA15 branches,
both P5V branches, all three BA0 branches, GND, BA1, A7, and D13_4_D105_2, but
BA2 at 24.520 mm and DBIN at 3.592 mm fail all four phases. Even assuming every
remaining net restores, that chain has a 24-open floor and is stopped. The
57/65-item D3/RAM candidates also retain fixed-pad blockers and are not ripped
up. No long-net topology supersedes the verified 23-gap checkpoint.

The unsurveyed companion PROM-address net D3_O4_D6_A6 is now also exhausted
on that exact checkpoint. Its diagnostic names 55 removable items across 27
nets plus fixed D3.14/P5V. A legal 0.1375 mm target exists after displacement,
but restoration leaves one CS_D11 branch and one same-coordinate CS_D55 join
unroutable on all four standard phases. Even granting every later restoration,
the chain has a 24-open floor, so it is discarded and the 23-gap checkpoint
remains authoritative.

Two interleaved exact-clearance phases extend that negative boundary: the
0.1625 mm lattice proves no route for all 23 residual signatures, while the
0.0875 mm lattice proves two no-path results and records 21 bounded timeouts.
Both results are byte-identical to the current 23-gap input. Their phase-local
S3_1 marker difference and exact tool/configuration hashes are guarded in
`ref/routing/current23-grid-edge-phase-exhaustion.json`; no route is adopted.

The last residual candidate without a fixed diagnostic blocker, CS_D57, is
also now exhausted transactionally. Of four target lattices only 0.1375 mm
routes legally after displacing 33 items on fourteen nets. Sorted restoration
ends at 26 opens; prioritizing CS_D55/GND/ROE/SYNC ends at 27 after losing a
second DB5 restoration. Both retained results remain free of electrical DRC
blockers but cannot beat 23, so neither is adopted
(`ref/routing/current23-cs-d57-transaction.json`).

The next guarded cleanup attacks obstruction rather than another route lattice.
All 244 dangling findings on the exact 23-gap checkpoint belong to migrated
copper; none of their UUIDs exists in the source PCB. `prune_dangling_tracks.py`
now supports nonzero-open boards only when every deletion is non-source copper,
the open count never rises, no electrical DRC category appears, and no other
DRC category grows. A bounded 641-item chunked transaction removes dead chains,
reduces dangling findings from 244 to 98, and collapses one obsolete MEMR island
plus one VA13 island, reaching 21 opens with zero electrical findings. A fresh
0.10 mm/100 mm-margin sweep accepts no additive route on the cleaned topology.
The exact hashes and the unchanged older-lineage boundary are recorded in
`ref/routing/current21-dangling-prune.json`; the 21-gap checkpoint now
supersedes the 23-gap board as routing-convergence evidence only.

A second bounded continuation adds adaptive batch descent: after accepting a
short final chunk it keeps that smaller transaction size instead of repeatedly
rescanning live branches at the original width. Starting from the reproduced
21-gap board, 614 further non-source items are removed. Track-dangling findings
fall from 87 to 23 and via-dangling findings from 11 to 2; the same 21 open nets
and every zero-valued electrical DRC category are preserved. The exact input,
output, DRC, configuration, and tool hashes are guarded in
`ref/routing/current21-deep-dangling-prune.json`. The remaining 25 tails and
21 gaps are the next automatic routing-convergence work. A fresh bounded
0.10 mm/100 mm-margin sweep attempts all 21 cleaned signatures and accepts
none; its output is byte-identical to the deep-pruned input. Several honest
marker distances grow after obsolete islands disappear, including MA7 from
5.709 to 19.421 mm. This is still the older routing lineage and not production
copper.

Fine adaptive continuation from that hash removes another 160 migrated items,
bringing the cumulative cleanup to 1,415 items. Both remaining dangling vias
are eliminated and track-dangling findings fall from 23 to 14; the same 21
open nets and zero electrical findings remain. A fresh bounded sweep again
accepts no route and is byte-identical to its input. As dead islands retreat,
CS_D10's marker grows from 29.610 to 32.314 mm and IORD's from 32.098 to 33.437
mm. Exact hashes and counts are guarded in
`ref/routing/current21-fine-dangling-prune.json`; fourteen migrated track tails
remain for the next guarded continuation.

Two-item continuation removes another 102 migrated segments, bringing the
cumulative cleanup to 1,517. The track-tail frontier falls from 14 to 13 with
no dangling vias, no electrical findings, and the same 21 open nets. A fresh
bounded sweep accepts no route and is byte-identical to its input; deleting the
long obsolete branch exposes IORD's honest 48.277 mm separation instead of the
former 33.437 mm intermediate-island marker. Exact evidence is guarded in
`ref/routing/current21-twoitem-dangling-prune.json`; thirteen migrated track
tails remain for continuation.

Continued two-item pruning removes another 70 migrated items, for 1,587
cumulative removals. The warning frontier contracts from thirteen dangling
tracks to ten tracks plus one via, while all 21 open nets and zero electrical
findings remain unchanged. A fresh bounded sweep tests every gap, accepts no
route, and writes a byte-identical board. Exact evidence is guarded in
`ref/routing/current21-eleven-tail-prune.json`; eleven migrated tails remain.

A two-item then single-item continuation removes another 13 migrated items,
for 1,600 cumulative removals. It eliminates the remaining dangling via and
leaves ten dangling track tails, with all 21 open nets and zero electrical
findings unchanged. A fresh bounded sweep again tests every gap, accepts no
route, and is byte-identical to its input. Exact evidence is guarded in
`ref/routing/current21-ten-tail-prune.json`.

Continuing along the long residual branches removes another 30 migrated items,
for 1,630 cumulative removals. The warning frontier plateaus at ten dangling
tracks, but routed items fall to 30,845 without changing the 21 open nets or
introducing any electrical finding. A fresh all-gap sweep accepts no route and
is byte-identical to its input. Exact evidence is guarded in
`ref/routing/current21-ten-tail-plateau-prune.json`.

The next adaptive two-item continuation removes 14 more migrated items, for
1,644 cumulative removals, and breaks the plateau from ten to nine dangling
tracks. Routed items fall to 30,831 while the 21 open nets and zero electrical
findings remain unchanged. A fresh all-gap sweep accepts no route and writes a
byte-identical board. Exact evidence is guarded in
`ref/routing/current21-nine-tail-prune.json`.

Adaptive single-item continuation removes another 30 migrated items along the
next long branch, for 1,674 cumulative removals. The frontier plateaus at nine
dangling tracks, but routed items fall to 30,801 with the same 21 open nets and
zero electrical findings. A fresh all-gap sweep accepts no route and is
byte-identical to its input. Exact evidence is guarded in
`ref/routing/current21-nine-tail-plateau-prune.json`.

Two further guarded single-item phases remove 56 migrated items, for 1,730
cumulative removals, and reach the next endpoint reduction from nine to eight
dangling tracks. Routed items fall to 30,745 while the 21 open nets and zero
electrical findings remain unchanged. A fresh all-gap sweep accepts no route
and is byte-identical to its input. Exact evidence is guarded in
`ref/routing/current21-eight-tail-prune.json`.

The next guarded single-item pass removes 27 migrated items, for 1,757
cumulative removals, and reduces the warning frontier from eight to seven
dangling tracks. Routed items fall to 30,718 while the 21 open nets and zero
electrical findings remain unchanged. A fresh all-gap sweep accepts no route
and is byte-identical to its input. Exact evidence is guarded in
`ref/routing/current21-seven-tail-prune.json`.

Two more bounded single-item phases remove 60 migrated items along the next
long branch, for 1,817 cumulative removals. The frontier plateaus at seven
dangling tracks, but routed items fall to 30,658 with the same 21 open nets and
zero electrical findings. A fresh all-gap sweep accepts no route and is
byte-identical to its input. Exact evidence is guarded in
`ref/routing/current21-seven-tail-plateau-prune.json`.

A further bounded single-item phase removes 30 migrated items, for 1,847
cumulative removals and 90 along the current long branch. The seven-tail
frontier persists, but routed items fall to 30,628 with the same 21 open nets
and zero electrical findings. A fresh all-gap sweep accepts no route and is
byte-identical to its input. Exact evidence is guarded in
`ref/routing/current21-seven-tail-deep-prune.json`.

Attempted-gap state retains proven router no-path
results across additive changes but invalidates DRC rejections and timeouts,
whose result can change when new copper forces a different path. The former 34
signatures exhaust fresh full-distance 0.1125 mm/0.20 mm-clearance work;
additional 0.20, 0.225, 0.25, and 0.30 mm lattices also accept nothing. More
0.12, 0.13, 0.14, and 0.16 mm phases and 100 mm-margin legal detours for six
short dense gaps likewise accept nothing. Guarded 0.15 mm diagnostics classify
the sampled alternatives as fixed source-pad corridors rather than removable
copper conflicts; route-specific topology work is next. Diagnostic DRC JSON can
now be retained even when a transaction fails, keeping that classification
machine-auditable. Reported dangling tails remain
reconnection work; the temporary board is convergence evidence, not a
replacement routed artifact
(`docs/routed-refresh-audit.md`).

Automatic device-level closure on 2026-07-17 also retires D103's former
high-impedance placeholder: `sync/ie10_check.sh` guards the complete
К555ИЕ10/74LS161 direct-clear, synchronous-load, enable, binary-count, and RCO
contract, while the structural top now uses the sheet-proved `0011` preset.
The already traced D103 RCO -> D33 inverter -> `/LOAD` loop therefore executes
as the documented modulo-13 divider and repeats `3..F` every thirteen 16 MHz
clocks. This does not promote the still-unproved OSC-to-XTAL16M source merge.

Target-photo registration now also closes the complete R49-R56 DRAM RAS
resistor bank (`docs/ras-resistor-bank.md`). The common `.006` assembly drawing
fixes the alternating top-to-bottom refdes order; two target component views
and the reflected panorama fix the column at x=221 mm with vertical 10.16 mm
lead spans. The red R49-R52 bodies directly read 75 ohm and the tan R53-R56
bodies read 5K1, retiring the former horizontal placement seed, unvalued/100
ohm working note, and fictional C69/R52 close pass without changing the traced
D53/RAS/GND connectivity.

D53's timing evidence is now bounded without inventing physical-board delays.
The exact-revision identity and complete КР531ИД7 pin contract are guarded
against the board JSON, while a checksum-pinned primary TI SN54S138 sheet
supplies a pin/function-compatible 12 ns maximum at its published 5 V, 25 °C,
280 Ω/15 pF test point. `docs/memory-timing-boundary.md` keeps that value as an
order-of-magnitude comparison only: an exact КР531ИД7 process guarantee,
loaded-board behavior, decoder-enable origins, CPU/video slot schedule, and
D36 CAS-input source still require stronger evidence or measurements, so no
dynamic HDL delay was added.

The same target-photo pass corrects a package-identity error in the CAS timing
area without changing connectivity. The previously registered upper,
top-notched `КР1533ЛА3` beside decapped D92 is D39, not D37. The `.006`
assembly order and an independent target view place the actual bottom-notched
D37 in the lower `D36–R57–D37–D33` row at `(245.5,180.1)` mm, and place the
vertical 20-ohm R57 between D36 and D37 at `(236.7,177.6)` mm with a 10.16 mm
lead span. Electrical sheet 2 also closes R58's value as 5.1 kΩ while its
physical placement remains approximate. The raw frame also relocates vertical
200-ohm R46 from an overlapping seed into the photographed D33/D103 gap at
`(266.6,184.0)` mm. Separate D37 and D39 guards preserve the corrected
identities, notches, evidence hashes, and placement limits.

Native-sheet value extraction now also retires 23 formerly blank resistor
values (`docs/native-resistor-values.md`). Checksum-guarded sheet 1 closes the
four 1 kΩ decode pull-ups R11-R14 and 200 Ω R17; sheet 2 closes the common
15 kΩ R40-R45 S3 bank (correcting stale 13 kΩ prose), R47/R59/R61 timing,
R60 FRAME_INT, R62-R66 video summing, R90/R91 beeper-clamp, and 8.2 Ω R48
speaker-output values. The
board JSON and generated PCB are checked against the same literal table.
Connectivity is unchanged. The final axial hold R67 is now independently
target-photo closed as `4К7` in July and May views; this supersedes the `.006`
sheet's 2 kΩ value without inferring its still-open `.009` pin-2 continuation.

The matching native-capacitor audit now source-closes C7=`560 pF`, C8=`15 nF`,
and C99=`160 pF` from their retained electrical-sheet circuits
(`docs/native-capacitor-values.md`). C7/C8 are the two already traced D56
one-shot timing capacitors; C99's value closes independently of its still-open
far plate. The guard deliberately leaves C9-C12/C15 at their target-revision
holds, C16/C19 at their incomplete bare-body markings, and unlabelled C34
unvalued rather than importing superseded `.006` RF assignments or guessing
units. Connectivity is unchanged.

The native-semiconductor audit now also restores the reset diode omitted from
the former board model and closes the beeper clamp's exact fitted part
(`docs/native-semiconductors.md`). Native sheet 1 fixes VD1's cathode on +5 V
and anode on the R3/C1/R4 reset-RC junction; independent May and registered
July target views prove the populated red axial body at `(12.5,216.1)` mm; the
May body view directly reads `КД521В`. In the traced beeper cluster, the July
view directly reads the same `КД521В` designation on VD4 and the independent
May view corroborates its grade-В reverse face. The source PCB carries both physical
diodes with their sheet-proved polarities. This target-body evidence supersedes
the older `.006` group list's КД522А allocation without changing VD3/VD5.

The machine-verified upload ZIP SHA256 is
`90308b962433648cf52d0de44046367380e79f3e653151da75fc08bd9d949a46`.
Do not send this package to a fabricator while the design hold remains. After
the blockers below are closed, regenerate every fabrication file and gate
again before upload.

## Highest-priority work and evidence boundary

These are ordered. The 2026-07-19 revision-3 reader session closed the D6
output-order problem. Items 2-3 remain preservation requirements while the
remaining connectivity is measurement-gated.

1. **Physical D6 `.038` firmware — CONFIRMED and directly adopted
   (2026-07-19).** The runnable twin now runs its memory map from the corrected
   physical `decode_prom` table (not the oracle), with D0-D3 direct and A7=0,
   and boots byte-identical to cosim across the full guard suite.
   Historical investigation record: before the reader-order fault was found,
   the old artifact appeared to require two unjustified output inversions. That
   provisional fit is preserved below as the path that localized the fault; it
   is superseded by the corrected capture and is no longer implemented.
   physical `decode_prom` with A7=0 boots **byte-identical** to the cosim value
   oracle across the full suite — `boot_check`, the 130,000-read `cosim_check`
   (`CTRACE-END`), EKDOS `A>`, disk-BASIC `READY`, jmon33 Monitor, BASIC-cart,
   `prom_fallback`, and LVS. So the chip's **contents encode the correct memory
   map**: with A7=0 the boot modes land in rows `011`/`010`, where word `1` is
   the ROM overlay and word `8` is RAM — matching cosim's PC1/PC0 banking. That
   de-risks the map and is the real progress here.
   With the old reversed artifact, the byte-identical run required a *per-output polarity* with no clean
   physical basis: `rom_sel_n = ~D0`, `roe_n = ~D3` (inverted) while `rev = D2`,
   `ram_sel_n = D1` (direct). That mix contradicts measured evidence — continuity
   makes `D6.12->D8.15` a **direct** conductor into an active-low `E_N`, and the
   model already has `D13` inverting in the `roe_n->D58` chain, so a byte-correct
   boot needs an inversion between `D6.9`/`D13` (and `D6.12`/`D8`) that is neither
   measured nor modeled. A uniform complement (the `d6_038.asserted` table) does
   **not** work either: it flips `rev`, which disables the D9 io-decode the boot
   needs. So the earlier "the asserted complement resolves it in simulation"
   claim was wrong. Per the fixed decision that measured evidence outranks
   inference, that fit was explicitly provisional. It has now been removed.
   Gate-chain audit (2026-07-15): D13 (К555ТЛ2) inverts and D37 (К555ЛА3) is a
   NAND, both datasheet-correct, so the modeled chain requires `D6.9`=0 for the
   `B37A` RAM read and `D6.12`=0 to select ROM — but the raw `.038` dump has both
   high in those regions, while `D6.10`->D9 (`rev`)=0 works direct. The mismatch
   is localized to the D6 pin-9 and pin-12 output paths only.
   D13 = К555ТЛ2 (inverter) is owner-confirmed (2026-07-15), so that hypothesis
   is closed and the model is right there. The РТ4 reader's logical contract
   was also audited: its address/data pin order matches the HDL model exactly
   (no permutation), and
   К556РТ4 = 82S126/3601/74S387 is a NON-INVERTING open-collector PROM (virgin=0,
   fuse=1; a pull-up reads the stored data directly), so the pull-up does not
   invert (datasheet vendored at
   `ref/datasheets/82s126-556rt4-256x4-oc-prom.pdf`; D8 РЕ3 also boots from its
   raw `.039`, excluding a universal raw/asserted convention error). The
   original RT4 capture's channel order was not yet independently closed.
   Consumer-side chip-polarity audit (2026-07-15,
   against the vendored datasheets) also closes the enable-polarity hypothesis:
   D8/РЕ3 = SN74188 has an active-low enable (as modeled), and D13 (К555ТЛ2
   inverter), D37 (К155ЛА3 NAND) and D58 (ИР82 active-low OE) are all
   datasheet-standard as modeled -- no chip is mis-modeled. With pin order, chip
   senses, and a uniform complement excluded, the remaining alternatives are a
   **series inverter on the `D6.12->D8` and `D6.9->D13` conductors, OR an
   electrical/provenance error in the D6 dump's D0/D3 bits**.
   **Sim narrowing (2026-07-15):** driving the runnable selects from the physical
   table under three transforms — only inverting **D0 (pin 12 -> D8) and D3
   (pin 9 -> D13)** while leaving D1/D2 direct boots byte-identical across the
   full guard suite; a uniform 4-bit complement fails (11.2 us) and inverting
   only D3 fails immediately (2.3 us). So the anomaly is genuinely per-pin on
   exactly the two РТ4 outputs feeding D8 and D13.
   **Decisive test result:** since `D6.12->D8.15` is owner-recorded
   as DIRECT (`docs/owner-measured-facts.md`; a photo re-read also looks direct),
   the effective inversion is not visible in the known copper. The original reader wiring
   (`tools/rt4_dumper/rt4_dumper.ino`): PROM pin 9 (D3) is read on Arduino **D13,
   the on-board LED pin** (LED + series resistor to GND) -- a classic gotcha that
   can drag an open-collector HIGH down. Revision 3 instead reused the RE3 board,
   controlled both /CE pins, and required every disabled-output check to release
   to `F`. Three D2 controls reproduced the established table. Three matching D6
   reads, including a power cycle, plus continuity-confirmed wiring
   `pins 9,10,11,12 -> Nano A1,D2,D3,D4`, proved that the old artifact was an
   exact reversal of all four bits. D2's `0`/`F` values had hidden the fault.
   The recovered `.009 Э3` sheet 1 now independently closes the remaining
   drawing question. Two reviewed read passes over the guarded overview and
   D6/D8 detail frame show D6 D0/pin 12 labeled `ROM` running directly through
   R11 to D8 `E`/pin 15, while D6 D3/pin 9 labeled `ROE` runs directly through
   R14 to D13 pin 1. D13 is the only drawn inverter and its pin 2 is the
   `RAMOUTEN` output. Thus the factory drawing agrees with chip-removed
   continuity and rules out an omitted drawn series inverter; it cannot explain
   the old raw-table mismatch (`docs/d6-physical-decode.md`).
   **Status: confirmed and directly adopted.** The runnable twin now boots from
   the corrected physical table byte-identically; the oracle
   is retired from the boot path (`decode_prom_functional` kept in `devices.v`
   only as the B37A-diagnostic reference). The per-output correction and proposed
   operating-level probe are retired.
   None of this changes copper. The former D105.1/A7 ask is now closed by the
   owner-confirmed D7.8 I/O-cycle qualifier. The same resolution promotes VJUGA
   workbench Phase 2, which routes its decode through the same physical D6 РТ4
   chip (`spinoffs/minimal-vga/docs/workbench-plan.md`).
2. **Preserve the promoted route until the functional netlist freezes.** The
   deterministic rip-up/recovery workflow has now promoted an exact-source
   route with zero opens, zero electrical-category DRC findings, and zero
   dangling copper (`ref/routing/zero-open-promoted-topology.json`). Its
   stable-KiCad fabrication package is checksum-verified, but remains under
   design hold; any source-net change requires a complete reroute/package
   regeneration rather than carrying this checksum forward. A:7, A:8, A:10,
   A:11, A:14, A:19, and A:20 remain historically faithful splits: registered
   landings on separate PHI1, STSTB, W10_QA_SEL, MEMR, PHI2, MEMW, and S_TTL
   islands joined only by W7/W8/W10/W11/W14/W19/W20.
   All twenty endpoints are now registered
   in original drawing pixels. Both A8/A10/A11/A19/A20 terminals and the
   D38-side A9 terminal are now fitted to their physical joints and copper
   islands; both A7/A14 remote-joint pairs and the C96-side A12 joint are now
   fitted too, leaving four PCB coordinates/island assignments pending. A14B,
   A7B, and D41.1 now share one raw solder image and calibrated frame: A14B is
   58.911 mm from D41.1, clearing the former 0.784 mm collision. The source now
   preserves separate PHI2 landing islands joined only by W14. Both
   A13 ends have now been exhausted across registered component/solder
   panoramas: D13.1/D92.1 are bare at both faces, the C95-side and post-D38
   remote corridors lie under the factory-wire bundle/mastic junctions, and no
   printed 13 or unassigned third backside joint is exposed. They remain null
   deliberately rather than borrowing nearby A8/A9 joints. The
   D40-side photo frame beside the printed A7/A14 joints is now fitted on both
   faces, and legacy endpoint seeds that mislabeled the visibly marked
   КР531ИЕ17 as D35 have been withdrawn. The marked D1 CPU and its complete
   2x20 pad field are likewise fitted on both faces, isolating the separately
   printed D1-side A7/A14 joints below the package. The remaining D51-side A9
   joint has been chased across six overlapping
   component tiles and is consistently hidden beneath the factory-wire bundle
   and mastic, so its visible wire approach is not promoted as a landing.
   (`docs/factory-wire-route-fidelity.md`). The promoted board is convergence
   evidence and a reproducible package snapshot, not production authorization:
   final release still waits for the P0 functional netlist to freeze, followed
   by repeated endpoint parity, DRC, package regeneration, and visual review.
3. **Preserve the adopted factory wire-table construction through release.**
   The sheets 2-6 таблица соединений is transcribed and its two number spaces
   are now explicit: conductor positions are not `А:N` board-point labels
   (`ref/schematics/dgsh5-109-009-sb-wire-table.md`). X3/X4/X6/X8/X9 landings,
   S1 links and all ten on-board insulated links are endpoint-mapped
   and guarded. Final copper adoption must retain `А:7-А:14` and
   `А:19-А:20` as assembly wire rather than silently replacing them with etch.

Owner continuity on 2026-07-20 corrects the adjacent resistor identification:
R94 is the 10k FDC DRQ pull-up above D28, wired D28.11/D93.38 to +5 V. The
photo-exhausted 220-ohm body near D98 remains unassigned; its evidence record
is retained as superseded rather than conflated with R94 or D98.7/S1.2. The
board JSON, KiCad source/schematic, HDL, and the promoted zero-open route now
encode both this correction and the D13-inverted `FDC_RESET_N` path. The
unidentified 220-ohm body is preserved separately as `RUNK1` with explicit
measurement boundaries; it is not conflated with R94 or D98.

The target-revision R67.2 far end is likewise photo-exhausted. Registered July
and independent May component views stop at its isolated solder pool. A
D102-local cross-side fit using fourteen paired package pins maps that joint
onto a bare backside copper corner with no via in both overlapping solder
tiles, so the coincident trace is not treated as an inter-layer connection.
R67.2 remains a direct-continuity ask rather than inheriting the superseded
`.006` RF-option net.

## Release blockers

### P0: physical connectivity (measurement-gated)

Every ask below is queued with exact deliverables in
`docs/owner-measurement-shortlist.md`; each item names its gate document.

1. **Complete FDC-era functional wiring.** D93's drive-interface pins plus
   D99 and D101 have package models but no complete
   functional signal closure (`docs/unmodeled-footprint-inventory.md`,
   `docs/fdc-hardware-handoff.md`). Trace each required pin end-to-end, or
   record a deliberate redesign/DNP decision. D93.40 `VDD_12V` is now
   owner-confirmed on the +12 V rail (`docs/d93-pin40-photo-chase.md`).
   Factory sheet 3 closes D106.7 Q3 -> D28.9, D28.8 -> D96.3, and
   D96.5 -> D93.26 RCLK; the older photo-only direct-net reading is retired.
   the standard К555ИЕ7/74LS193 digital device behavior is now independently
   closed and CI-guarded by `sync/ie7_check.sh`: asynchronous active-high
   clear, asynchronous active-low parallel load, rising-edge up/down count
   with the opposite clock high, active-low clock-width carry/borrow, and
   two-package cascade all match TI SDLS074. Recovered sheet 3 now also closes
   D106's complete board contract: R78 pulls UP and all four preset inputs high,
   D95.9 clocks DOWN, D97.4/D93.27 RAW READ drives /LOAD, CLR is grounded, Q3
   drives D28.9, and Q0-Q2 plus /CO and /BO are explicit no-connects
   (`ref/schematics/fdc-recovery-counter-map.md`). R78's value and placement,
   plus physical recovery-clock edge quality, remain honest bring-up boundaries.
   The same sheet closes D96 section 1 as the actual read-clock toggle:
   WREQ_N drives /CLR and /PRE, /Q feeds D, D28.8 clocks it, and Q drives
   D93.26 RCLK. A full-resolution reread restores section 2 in the local
   DRQ/INTRQ conditioner: wired D28.10/.12 feeds D96.10/.12 through R95,
   R93 pulls the INTRQ input high, D96.9/.11 continue to sheet 1, D96.13 is
   drawn unused, and pin8 retains its isolated test landing. The primary
   SN74LS74A truth table now exposes that exact section-2 wiring as set-only:
   its shared `/PRE2`/D2 node can set Q2 but cannot clear it, and the only clear
   pin is the sheet-omitted pin13. Primary truth also corrects section 1: WREQ
   asserts `/CLR1` and `/PRE1` simultaneously, so both outputs go high and the
   release phase is not deterministic, though `/Q` feedback divides after the
   first recovered-clock edge. D96 remains LVS-mapped; both sections' async
   behavior requires powered capture (`docs/d96-read-clock-readiness.md`).
   The same exact-revision omission convention now closes the remaining unused
   pins on adjacent devices: sheet 3 draws all six D28 inverters and five of
   six D98 buffers, so only D98.9/.10 are NC on those devices; it explicitly
   draws the used polarity of each D97/D102 one-shot output, leaving D97.13 and
   D102.4 NC. A structural guard prevents contradictory NC entries from
   returning on the live D28.5/.6 READY or D28.10-.13 IRQ inverters
   (`ref/schematics/fdc-unused-pin-dispositions.md`).
   D28 and D98 are now structural-only HDL cells and LVS-mapped. Their six
   open-collector inverter paths and five enabled status buffers are compared
   without inventing behavior for the intentionally absent D98 pair 4.
   the KP12 passive ladder is also target-photo closed: R92=`1К3` runs from
   D95.14 to D101.4/R99.2, and R99=`4К7` returns that junction to
   D101.8/GND. Recovered `.009` Э3 sheet 3 additionally closes the
   D97/D102/D101 write-precomp chain from D93.31 through three delay taps and
   D101.9 to D100.6, including EARLY/LATE selects and timing passives. Direct
   target continuity overrides the sheet's duplicated R99, conflicting R86,
   and tied-D101 drafting (`ref/schematics/fdc-write-precomp-map.md`).
   D97, D102, and D101 are now included as structural-only HDL cells and in the
   LVS instance map. Together with structural D28/D98 coverage, this raises the
   proved scope to 117 instances/308 nets and
   checks the delay cascade, EARLY/LATE selection, Q0-to-D94 path, and Q1-to-D100
   output without guessing C16/C19 timing or resolving the four real D101
   singleton boundaries by simulation fiat.
   A generated first-half constraint audit now fixes D101's exact 74LS253
   select cases, Q0 tri-state behavior, measured D02 density-control ladder,
   and the physical D94 register-3 response. It keeps the polarity-compatible
   D94.1/D0-to-D101.1 `/OE0` feedback possibility conditional on chip-removed
   continuity and reduces the true D101 asks to pins 1, 3, 5, and 6
   (`docs/d101-reconstruction-constraints.md`).
   The adjacent C20 and outer C22 body markings are now independently photo-read
   as `1Н5` and source-closed by GOST 11076-69 Table 1 as 1.5 nF; their
   tolerances and voltages remain explicit boundaries; sheet 3 closes their D102 endpoints. In the adjacent right-edge
   passive column, two independent target-board angles close R100, R102, and
   R108 as `12К`, and R86 as `4К7`. Uninterrupted component copper joins
   all four right-hand pin-2 leads to one common perimeter rail; sheet 3 closes
   that rail to +5 V and closes R102.1/R108.1 into the C22/C20 D102 timing
   networks. Two
   independent component angles also show C19.1/R100.1 and C19.2/R86.1
   terminating on their respective common landings. Sheet 3 closes the upper
   join to D97.7; target copper closes the lower join to D97.6 and resolves the
   drawing's conflicting R86 annotation. The
   solder-side D102.8 trace is not treated as a cross-layer join without direct
   continuity evidence. The same target-board angle literally
   resolves bare `27` on C16 and bare `22` on C19, but GOST 11076-69 requires
   a unit/decimal letter for a complete coded capacitance; both capacitors'
   values/units remain explicit measurement boundaries rather than guesses.
   Recovered sheet 3 also closes every D95 pin: grounded enables; FM/MFM and
   5-inch/8-inch selects; D40's 1/2 MHz rails selected onto D93.24; and its
   4/8 MHz rails selected onto D106.4. The structural HDL and LVS map now carry
   the same mux (`ref/schematics/fdc-clock-mux-map.md`). D95 therefore leaves
   the measurement-gated support-device list; physical oscillator accuracy and
   edge quality remain bring-up measurements rather than connectivity gaps.
   A full-resolution correction identifies the formerly assigned yellow body as
   the three-lead КТ315 VT2 marked `Б / 8901`, not C94. Its emitter/pin 1 shares
   R65.1/`VIDEO_OUT`; its other two component-side lap joints are the collector
   and base. The factory drawing separately places C94 immediately to its right,
   but owner imagery does not uniquely resolve C94 through the transistor body.
   C94 population, value, and both endpoints therefore remain measurement asks.
   The remaining first precomp probes are D101.1/.3/.5/.6. A generated D99
   constraint audit now proves its grounded-clear section 1 holds Q/pin13 low
   and `/Q`/pin4 high, proves physical D94 D1 drives section-2 A_N low on either
   selected read or write, and derives the nominal R97/C17 2.538 s pulse plus
   26.4 ms retrigger-inhibit window. D99 pins4/5/10/11/12 remain the physical
   remote-path targets (`docs/d99-reconstruction-constraints.md`). The former
   D93 EARLY/LATE, precomp-output, D97.13, and D102.4 probes are source-closed.
   An automatic handoff audit now also removes stale continuity requests for
   D93.15-.18/.26-.32/.34-.36 and D100.6: those step, direction, precomp,
   separator-clock, raw-read, head-load, write, READY, and drive-status paths
   are already source-closed. Chip-removed owner continuity supersedes the
   ambiguous exact-revision `RES (3)` reading: active-high CPU `RESET` reaches
   D13.9, and Schmitt-inverter output D13.8 drives D93.19 `MR_N` plus the
   outer-bus contact. The reset polarity and controller connection are therefore
   source-closed, while the exact outer-bus contact code remains a connector-
   orientation boundary. The exact-revision drawing also ties D93.22 TEST
   locally to D93.33 WF/VFOE. Exact-revision sheet 3 now closes both final
   anonymous controller pins: E11 is drawn in its 2-3 position, strapping
   D93.23 HLT to D93.32 READY (with MOTOR EN on the alternate post), while
   D93.25 RG is deliberately omitted between the explicitly drawn pin-24 and
   pin-26 paths and is therefore unused/open on this design. The remaining
   controller-side asks are the separately guarded DRQ/INTRQ assumptions.
   A further full-resolution sheet-3 read restores C17/C18/R97/R103 and both
   D99 RC networks, grounds D99.1, and marks the explicitly omitted D99.13
   unused. Cross-checking the sheet's continuation notation keeps D99.10 and
   the joined D100.9/.11 conductor as distinct sheet-1 boundaries rather than
   incorrectly treating each `(1)` marker as logic high. The same read restores
   D28 sections 5/6, D96 section 2, and R93/R95 as the local D93 DRQ/INTRQ
   path. Device-truth analysis exposes D96 section 2 as set-only unless its
   drawn-NC clear pin13 has an unrecorded source; D96.9/.11/.13 and the
   PIC-side destinations therefore remain functional verification asks.
   A separate automatic firmware audit still proves two incompatible VG93
   software profiles (`docs/fdc-bus-polarity.md`). EktaSoft 2.4 and Monitor 3.3
   place `CMA` around all 12 VG93 writes and six reads, while EktaSoft
   3.1/3.5/3.7 replace all 18 transforms with one-byte NOPs. The former
   `JUKU_FDC_BUS_INVERT` simulation path remains a valid functional profile
   test, but the recovered drawing now disproves its attribution to D100.
   The independent archival D15/D16 pair is adopted as EktaSoft 3.7 and fixes
   the replica to the direct-bus/NOP profile. Future socket reads may preserve
   another historical board variant, but are not a replica or release gate.
   The native sheet already closes CPU DB0-DB7 directly to D93
   DAL0-DAL7; only the historical purpose of the incompatible CMA-profile
   firmware remains unexplained. The
   standalone ВА87 model and source-proved D23-D25 paths retain their exhaustive
   guards; the D100-specific `/OE`/`T` bus-family claims are retired.
   Probe predictions from period references (guides, not Juku proof): the
   Чеботарев Вектор-06Ц FDC schematic (Радиолюбитель 11/92) uses exactly this
   part family — ВГ93 + К555ИЕ7 separator + two К555КП12 + К555ТМ2 + К155ИР1 —
   with `/RAWR` (ТМ2-resynchronized) jamming ИЕ7 `/LOAD` pin 11 on the same
   node as ВГ93 pin 27, 8 MHz on pin 4, strapped load inputs, and precomp
   taps ИР1 Q1/Q2/Q4 selected by КП12 under EARLY/LATE pins 17/18; WD's
   June-1980 Figure 11 grounds CLR pin 14, while a VFOE-gated (D93.33)
   variant is also plausible — meter both.

   **Recovered-sheet correction (2026-07-19):** `.009 Э3` sheet 3 and the
   matching НГМД drawing now close the X4/XS5 connector map from primary
   evidence. They also invalidate the inferred D100 DB↔DAL assignment: D100 is
   the inverting eight-channel drive-output buffer for TG43, DIR, STEP,
   WR.DATA, WR.GATE, H.LOAD, MOTOR.ON, and S.SEL. D28.2/.4 instead drive
   X4.21/.22 `-D.SEL1/0`, and D28.5/.6 participate in READY. The stale
   `FDC_DAL0..7`/D100 model and its `/OE`/`T` measurement plan are removed;
   the physical HDL/KiCad model now follows the factory drive-output role. A second native
   frame proves D93 DAL0-DAL7/pins 7-14 join the sheet-1 D0-D7 bundle directly;
   the numbered sheet-1 continuations also prove D26 PC2/PC4/PC5/PC6 as
   MOTOR EN/FM-MFM/D_SEL/S.SEL, and show that D28.9 belongs to the separator
   rather than DDEN. The same sheet and registered `.009 СБ` placement close
   R79-R83 (470-ohm X4/D98 input pull-ups), R84/R85 (470-ohm READY/separator
   pull-ups), and R98 (4.7-kohm -D.SEL1 pull-up). These source-proved nets replace the inferred bus
   (`ref/schematics/fdc-x4-ngmd-wire-map.md`).
2. **Finish D94 `.092` connectivity.** Content truth is closed. The 2026-07-19
   owner recheck corrects the earlier socket-number interpretation: D94.2 reaches
   D99.9 and R89, D94.3 reaches D93.4 and R88, and D94.4 reaches D93.2 and R87;
   all three resistors return to +5 V. D94.1 has its separate R8 2 kΩ pull-up and
   no other measured branch. Full-resolution visual inspection closes D94.5
   as NC; D93.1 alone owns the short trace ending at the visible gap.
   D94.13 is not D104.7 (~84 kΩ between them) and is not D5.27. It is the
   qualified peripheral `/WR` rail from D105.3, also owner-closed to D29.5,
   D10.2, D11.10, D26.36, and D27.36. D5.27 is instead raw `IOWR_N` into D7.10.
   D7.8 reaches D105.1 and D6.15, closing the former D6 A7 boundary as the
   I/O-cycle-active-high term; D13.3 receives raw CPU `/WR` from D1.18/D5.3 and
   D13.4 drives D105.2. Thus D105.3 is exactly the NAND-qualified peripheral
   write strobe predicted by the PROM equations.
   The minimized physical table also gives an exact D0 probe stimulus:
   BA1:BA0=`11`
   with A4/D101.7 low asserts D94.1 regardless of A3/A2 while both D93 `/RE`
   and `/WE` release; A4 high restores the normal register-3 strobe. A4 cancels
   from every other register row, proving D101.Q0 is exactly a register-3
   transfer-steering qualifier without identifying D0's alternate load. Scope
   D101.7, D94.1, `/RE`, and `/WE` together during port `1F` transfers. D2/D3
   minimize to mutually exclusive read/write equations,
   and D4-D7 are proved released at every address. Owner continuity on
   2026-07-21 and the exact `.009 E3` drawing close D94 pins 6, 7, and 9 as NC;
   these constraints sharpen continuity work without treating behavior as copper evidence. The
   former BA11..BA15 assignment was an unproved scaffold analogy and is retired;
   all five actual D94 inputs are now owner-mapped
   (`docs/d94-reconstruction-constraints.md`). A reflected D104 photo fit proves
   that pin 10 has no B.Cu departure in two backside views; owner continuity on
   2026-07-21 and the exact `.009 E3` drawing now close that output as NC.
3. **Close the remaining D6-area netlist asks.** Chip-removed continuity now
   proves D6.12->D8.15, D6.11-/->D8.15, and D6.11-/->D6.12, invalidating the
   earlier installed-PROM joined reading; D6.11 instead reaches D2.15/-WREQ.
   The D6.11->D92.5/R12.2 branch is now owner-confirmed, joining the already
   measured D6.11->D2.15/-WREQ conductor. D13.12->D6.14
   continuity plus visually confirmed bottom-layer D6.13<->D6.14 copper closes
   the enable branch. The complete D6.9->D13.1,
   D13.2->D37.4, D37.6->D58.9 endpoint chain is owner-confirmed. The remaining
   copper-truth asks are now reduced to rechecking the surprising
   D13.12->D16.13 report with D16 removed and the remaining unrelated boundaries.
   The 2026-07-19 owner measurements close D7.8 to D105.1/D6.15 and independently
   close D105.3 as the qualified peripheral `/WR` output; the adjacent sheet
   bundle codes were distinct signals, not unresolved destinations. The D37.5 second NAND
   input is already source-closed by the native sheet-2 route
   MEMR->D33.3/.4->D37.5 and is now regression-guarded together with
   D13.2->D37.4 and D37.6->D58.9. Simulation has narrowed the former
   all-mode `B37A` contradiction to the reader-order fault, now closed by the
   revision-3 captures and the direct full-boot comparison. The five live
   RAM-read levels named by `docs/d6-runtime-path-diagnostic.md` are optional
   Tier-3 confirmation rather than an adoption gate.
4. **Map the factory Вид В modifications.** The local Вид В details at D56,
   D15, D14, and D11 mix solder/copper context with assembly callouts. Note 11
   proves position 150 is tubing fitted at solder locations, not a cut; only
   the D15 detail explicitly says `Разрезать`. D15 is
   now photo-closed: two independent component views register the executed cut
   between the auxiliary D15.8/A2 and D15.9/A1 landings, and reflected solder
   copper confirms both pin destinations. The clean source already preserves
   the resulting separate A2/A1 nets; the unmeasured auxiliary-hole geometry is
   not invented. D14 is now partially photo-closed: notch-oriented registration
   maps both package rows, and two component views prove the position-159
   D32.4/GND-to-D14.1 copper link now preserved by the source model. Exact
   D56 geometry is now registered: three component views identify the actual
   notch-down К155АГ3 package, held-out-validated component/reflected local fits
   replace the displaced global seeds, and two solder views map all three
   callout locations as the separate left annulus plus D56.5/D56.12. Visible
   bare-board gaps separate both package pads from the adjacent rail, but the
   installed item-159 material and auxiliary-annulus disposition remain held.
   Exact `.009 E3` sheet 2 plus owner continuity on 2026-07-21 close the package
   pads themselves: D54.17/H.SYNC DSL reaches D56.10, D55.17/VERT SYNC DSL
   reaches D56.2, D56.12/Q2_N reaches tied D55.15/CLK1 and D55.18/CLK2, and
   D56.5/Q2 reaches D34.9. D57.17/SYNC B is separate, superseding the older
   `.006` scan chase that joined it to both D56 triggers. The same two solder views independently
   expose the wide perimeter conductor: D56.9 joins package-ground D56.8 on the
   upper rail and D56.1 returns to it along the uninterrupted left board edge.
   Both formerly unstubbed active-low A inputs are therefore source-promoted to
   GND, resolving the physical prerequisite for the two separately driven
   one-shots while leaving the separate item-159 field held. D14's fifth landing
   is now registered in two component views at `(207.887, 49.900) mm` with
   `0.011 mm` cross-view disagreement; its conductor, three long traces, and
   right-row dogleg remain held. Both reflected solder overlaps place the D14
   locality inside the same scraped/reworked two-row field, while the component
   views hide the immediate dogleg under the body; D14.2/.7 are therefore
   photo-exhausted direct-continuity asks. At D11,
   two component views now register the L trace and four position-159 solder
   locations and exclude the previously cited pins-4–6 solder scar as a
   different feature;
   held-out-validated component and reflected package fits now project the field
   into four overlapping solder photos. The upper point is rail-obscured and the
   lower three do not form a unique four-hole match, so imagery is exhausted and
   direct continuity of the bridge, D11 pin/net, and remote endpoints remains
   the P0 hold
   (`docs/factory-modification-disposition.md`).
5. **Disposition all remaining source-risk nets and omitted endpoints.**
   43 source-risk nets and 3 official FDC devices with untraced functional
   pins remain (`docs/replica-bringup-verification-points.md`,
   `docs/board-fidelity-gap-ledger.md`). Anything affecting boot, memory, bus
   direction, interrupts, or video timing must be source-proven, measured, or
   explicitly redesigned before release.
   The D10 interrupt audit narrows one non-critical exception without inventing
   copper: exact `.009` sheet 1 retains `IR4=(3) TAPE RUN INT`, while the
   complete replacement FDC sheet 3 contains no matching continuation. The
   model preserves only D10.22 as a stale-sheet boundary, and exact ekta37 code
   writes PIC mask `0xDF`, keeping IR4 masked while enabling frame IR5. Tape is
   outside the critical path; owner continuity remains Tier-3 historical
   evidence rather than a Tier-1/2 boot blocker.

Source-model state feeding this work: the authoritative board JSON defines all 2297/2297
PCB-scoped board-JSON endpoints, with 75 non-PCB or placement-held
endpoints intentionally excluded. The controlled D54/D55/D56 owner-timing
refresh is now applied to both source and promoted routed PCBs; the generated
coverage report proves 2297/2297 endpoint-name matches on each artifact, including
the source-proved D59.5/D59.6 complementary mux-enable endpoints, and
the routed-candidate gate preserves zero opens and exact source-pad identity.
Bracket-mounted S1/X3/X4/X6/X8/X9 use their
physical A-point cable landings. The photo-proven bare `.009` C63 callout is
kept distinct from the inherited C63 DRAM-grid verification landing: the full
4x8 common-artwork grid is fabricated and C63 remains assembly DNP. C51-C53/C70-C72 retain their
schematic rail-bypass intent but have no current source-PCB footprint: their
former near-chip coordinates were fit-to-space assumptions and remain held
until target placement/population evidence is registered
(`docs/replica-bringup-verification-points.md`); it has zero electrical
placement collisions (`docs/source-pcb-drc.md`) and no undeclared non-power
package endpoints (`docs/package-endpoint-coverage.md`). Off-board S4 is
likewise outside PCB-pad scope while its three switch contacts remain modeled
nets (`docs/s4-interrupt-boundary.md`).
Neither source nor routed PCB has an endpoint-coverage failure. The July photo workflow is
complete as a registration/review scaffold: all
639 observations have dispositions, 42 rows are accepted evidence, six rows
are rejected (including the former R94 assignment), and the other 591 remain
measurement requests
(`docs/photo-registration.md`).

Exit criterion: every required functional endpoint is modeled in both source
and routed PCBs; LVS, DRC, boot, and cosim checks remain green; the generated
design-release reports contain no P0 blocker.

Active generated boundary/gate documents — each names its own pending hold,
and `docs/owner-measurement-shortlist.md` queues them for the next hardware
session: `replica-bringup-verification-points.md` (endpoint coverage),
`unmodeled-footprint-inventory.md` (3 FDC devices),
`factory-modification-disposition.md` (Вид В pad mapping),
`assembly-drawing-extraction.md` (wire-table pin mapping),
`d30-section-b-scan-chase.md` (D30 section B continuity),
`routed-refresh-audit.md` (routed-board convergence),
`io-decode-boundary.md`, `memory-timing-boundary.md`,
`d41-timing-boundary.md`, `s4-interrupt-boundary.md`,
`master-oscillator-boundary.md`, `video-analog-boundary.md`,
`main-board-erc-parity.md`, `board-fidelity-gap-ledger.md`,
`decap-value-fidelity.md`, and `firmware-gap-ledger.md` (adopted PROM truth).

### Programmable parts — adopted set closed

All four small-PROM dumps (D2 `.037`, D6 `.038`, D8 `.039`, D94 `.092`) are
validated physical raw tables backed by matching captures from two `.009`
boards, including power-cycled reads; `hdl/sim/prom_fallback_tb.v` pins each HDL table to its validated
hex, and the two capture validators (К556РТ4 and К155РЕ3) enforce the repeated-
read discipline (`docs/firmware-gap-ledger.md`). The deterministic D15/D16
`ekta37` split comes from a third, independent archival ROM source, and the
2764-class device decision is recorded in
`docs/eprom-programming-images.md`. A checksum-pinned lineage audit now proves
that the archival raw `JUKUROM0.HEX`/`JUKUROM1.HEX` pair concatenates exactly
and uniquely to that EktaSoft 3.7 image, while the owner overview independently
shows two populated ST `M2764AF1` packages with uncovered windows. The adopted
dump standard treats those independently sourced, exact-hash-guarded bytes as
content truth. The absent paper cross-reference from the archival filenames to
factory `.087/.041` drawing numbers remains a provenance note, not a content,
milestone, or release gate (`docs/d15-d16-firmware-lineage.md`).

The runnable boot executes from all four physical tables. The adoption record,
in dependency order:

1. **D2 `.037` — physical table and raw polarity execute.** `wait_prom_037`
   now models the РТ4's open-collector outputs and drives the measured D30/R29
   READY path. The focused guard proves raw `0` sinks READY low and raw `F` or
   disabled output releases the R6 pull-up high before D30 samples it. The used
   D0 reader channel was Nano D10, independent of the Nano D13 LED issue on the
   board-unused D3 channel; the later D6 reader correction did not change D2 polarity.
   D30 pins 8/11 are owner-closed; only complete cycle timing through the `H`
   edge contact remains P0 connectivity item 3, not a PROM-content gap.
2. **D8 `.039` — physical open-collector table executes; enable is still
   derived.** Programmed zeros now sink the eight ROM-socket select rails and
   released bits recover high through explicit simulation pull-ups, matching
   the К155РЕ3 electrical contract. The focused PROM guard also proves disabled
   outputs are high impedance and row 00 sinks only D4/D15 select. Its `E_N`
   input is the separate D6.12 ROM-select conductor, so full adoption completes
   with step 3. Exhaustive minimization closes its firmware semantics:
   `Q=(BA15==BA14)`, D4/D15 asserts at `Q & !BA13`, D5/D16 at `Q & BA13`,
   BA12/BA11 are don't-cares, and D0-D3/D6-D7 always release
   (`docs/d8-physical-decode.md`).
3. **D6 `.038` — corrected physical table executes directly.** Runnable selects
   come from `decode_prom U_DECODE` and the validated revision-3 physical table;
   `decode_prom_functional` is no longer instantiated by `juku_top` and remains
   only a diagnostic comparison. The superseded reader artifact fails the
   checkpoint-resume boundary at RAM `B37A` because all four bits were reversed.
   The underlying electrical model is faithful open collector:
   raw zero sinks and raw one/disabled releases through explicit R11-R14-backed
   simulation pull-ups. Revision-3 known-D2 controls, three D6 captures including
   a power cycle, continuity-confirmed reader wiring, and a full direct 6000-write
   boot comparison close the electrical/provenance gate.
   `docs/d6-firmware-mode-coverage.md` bounds
   what the trace proves: boot firmware observes A6/A5 suffixes `11` and `10`;
   A7 is functionally forced to `0`
   for all firmware-reachable maps (A7=1 rows emit only words `B`/`F` and can
   express neither observed banking map), while its physical driver on the
   D105.1 conductor is owner-closed to D7.8 as the I/O-cycle-active-high qualifier.
4. **D94 `.092` — physical table executes with guarded upstream fits.** The
   runnable behavioral `fdc_1793` now consumes the physical PROM's open-
   collector `/RE` and `/WE` outputs. A3 consumes the owner-closed D105.3
   qualified peripheral `/WR` conductor (`iowr_n`). Simulation alone derives
   the still-unresolved shared enable from `cs_fdc_n` and holds A4 high while
   D101's runtime mux semantics remain open; Yosys/LVS retains the separate
   physical boundary nets. The fast top-level
   bus guard checks both PROM strobes on every FDC register read/write. Full
   hardware release still requires shared-enable/D0 closure plus D93 functional
   closure, after which the two remaining upstream fits are replaced and
   `fdc_1793` is retired.

PROM adoption exit criterion is met: `prom_fallback_tb` equality stays green,
the runnable top instantiates all four physical tables, and every boot guard
passes with zero functional PROM stand-ins. D94's sim-only enable/A4 behavior fits
remain a physical-connectivity hold, not a firmware-table fallback.

Exit criterion: every populated programmable part has a burnable file,
checksum, device/pinout decision, and provenance. Any functional replacement
for an unavailable PROM must be documented and tested as a redesign.

### P1: fabrication review

After connectivity and programmable-part decisions stop changing:

1. Regenerate the schematic, source PCB, routed PCB, Gerbers, drill, renders,
   BOM, and checksum files on the CI toolchain.
2. Run LVS, behavioral guards, endpoint coverage, ERC/parity, DRC, package
   geometry, power-trace, and independent Gerber-render checks; also overlay
   the exported copper on the registered owner photographs (Mimeo-1-style
   artwork-over-photo validation) as an independent fidelity check.
3. Resolve changed DRC classes explicitly; do not carry blanket waivers across
   geometry changes.
4. Run `kicad/check_replica_manufacturing_ready.sh`. It must report a released
   design, not merely a coherent package.
5. Upload only the newly generated ZIP and preserve vendor preview/settings and
   order evidence using `docs/replica-order-evidence-template.md`.

## Blocked on external evidence

- **Owner measurement session:** `docs/owner-measurement-shortlist.md` is the
  queued, prioritized ask list for the next hardware session; it covers every
  P0 connectivity item above.
- **Community requests:** use `docs/community-prom-media-request.md` for
  optional additional PROM provenance, JUKU-1 media provenance, and cartridge
  BASIC artifacts. The Baltijets programming-disk payloads are presumed lost;
  the guarded `JUKPROG1/2/X` scan finds none of the four validated tables in
  raw images or reconstructed active files under common byte, address-reversed,
  ASCII/Intel-hex, or packed-nibble encodings (proprietary transforms remain
  possible);
  keep the ask open opportunistically, but nothing on the critical path may
  wait on them. The revision-3 reader experiment resolved the D6 contradiction;
  additional independent reads are preservation opportunities only.
- **Document gap:** the `.009 Э3` electrical-schematic revision is **recovered**
  — owner-photographed 2026-07-18, all three sheets, under
  `ref/photos/dgsh5-109-009-e3/` (sheet 3 = the КР1818ВГ93 FDC circuit). This
  drawing was not public anywhere per the 2026-07-14 web sweep. Remaining work
  is to transcribe it and reconcile `.006`→`.009` divergences. The НГМД block
  `ДГШ3.065.008` is **also recovered** in the same 2026-07-18 batch
  (`ref/photos/dgsh3-065-008-e3/`, ДУБЛИКАТ) — it gives the drive side of the
  floppy interface (ЕС5323 mechanisms + X1–X5), the mating counterpart of the
  processor board's X4; reconcile the two. The Arvutimuuseum team (which
  physically recovered the Baltijets archive in Narva, Nov 2024) remains the
  best source for anything still missing.
- **Peripheral / system drawings (2026-07-18 batch):** additional owner
  schematics now in-repo under `ref/photos/`, useful for bus/connector
  cross-checks and firmware ground-truth:
  `dgsh3-031-011-e6/` (`ДГШ3.031.011 Э6` system general schematic — inter-module
  connector map X1–X6), `dgsh5-104-015-e3/` (`ДГШ5.104.015 Э3` keyboard module),
  `dgsh5-106-103-e3/` (`ДГШ5.106.103 Э3` 32K memory-expander card — exposes the
  system-bus XP pinout, relevant to the rev-B backplane; its data/address/control
  core matches X1 exactly, but its A1-A3 power map conflicts with `.009` and is
  guarded as a non-pluggable variant), and
  `dgsh5-106-106-d1/` (`ДГШ5.106.106 Д1` factory ROM programming table; its
  reconstructed 0000–07FF page corrects the sole BAS0 typo at `021A` from
  photo evidence and matches `jbasic11.bin` exactly). The `.104.015` keyboard
  sheet is now also fully transcribed: all 70 fitted positions, the 1-based
  factory scan-line offset, non-binary 74148 row order, modifiers, and X1
  pinout are guarded; all prior cosim tuples agree and its omitted ASCII shift
  pairs/control keys are now implemented.
  **How to work through this batch is planned in
  `docs/factory-drawing-exploitation-plan.md`** — staged: legibility audit →
  targeted reads (D6 decode polarity for item 1, FDC X4↔НГМД, XP bus map) →
  ROM-table transcription/diff → full reviewed transcriptions → community
  exchange (owner-gated).
  All automatic stages are now complete: legibility, critical reads,
  bus/FDC maps, ROM reconstruction, keyboard/НГМД transcription, and the
  checksum-guarded three-sheet `.009` diff audit have reviewed artifacts.
  Only the explicitly owner-gated community exchange remains.
- **Community coordination lead:** juku3000 issue #25
  (<https://github.com/infoaed/juku3000/issues/25>) shows the MAME driver
  maintainer hunting the same FDC-era schematic; the MAME driver's own TODO
  still reads "work out how the floppy interface really works", and the local
  validated К556РТ4/К155РЕ3 dumps appear to be published nowhere else —
  sharing them and the ИЕ7/КП12 findings is a two-way exchange opportunity.
- **Separator/precomp references:** WD FD179X Application Notes (June 1980),
  Рюмик's «Контроллер дисковода» survey, and the Чеботарев Радиолюбитель
  11/92 article — sources and URLs are recorded in
  `ref/wd1772-vg93/README.md`; see the probe predictions in P0 connectivity
  item 1.
- Recheck external sources only for a named blocker; the current inventory is
  `docs/source-coverage-audit.md` (the 2026-07-22 cartridge-BASIC recheck still
  finds only the catalogued 8 KiB `JBASIC11.BIN`, while its literal bootstrap
  requires one more 256-byte source page; the 2026-07-11 museum audit found
  duplicate `JUKUROMS.ZIP` ROMs and cassette-only `CASTOOLS.JUK`, not the
  programming disk).

## Parallel work

### CI hardening

`docs/ci-hardening-plan.md` is the executable plan for four reliability
improvements motivated by the 2026-07-20 twelve-hour red-CI window: a
one-command report-regeneration script, a shared LFS-aware photo-hash helper,
a CI-aware pre-push gate, and moving the EKDOS timing expectations into a
committed data file with a deliberate `--update` path. Items are independent
commits in the order 2 -> 1 -> 4 -> 3; CI must be green between them. The same
file also carries two 2026-07-20 CI cost-reduction items (5, 6): concurrency
groups with `cancel-in-progress` on all three workflows, and narrowing the
over-broad `scripts/**` / `ref/**` path gates on `reports.yml` that the routing
loop trips 77% of the time. Both preserve full coverage; either order.
After changing board JSON, report generators, or timing-relevant HDL, run
`scripts/regen_all.sh` (`--deep` for HDL/cosim changes) and commit its drift.
Pushes use the tracked pre-push hook to gate on green master CI; fix a red run
or explicitly override that check once with `CI_GATE=off`, never stack blindly.

### VJUGA spin-off — status and Linux-box handoff

VJUGA (the +5 V Z80 bench fixture for the scarce Juku РУ5/РТ4/РЕ3 parts) is a
separate experiment; details in `spinoffs/minimal-vga/docs/workbench-plan.md`
and `docs/phase4-bench-bringup.md`. Status as of 2026-07-19:

- **Simulation + board model DONE.** The Verilog twin boots the real firmware on
  tv80 through the real К565РУ5 + D6 К556РТ4 + D8 К155РЕ3 models; **both decode
  modes** (real РТ4 vs GAL-internal baseline) are byte-identical to cosim
  (`sim/vjuga_boot_check.sh`). The corrected reader-3 D6 table is consumed with
  physical D0/pin12 as active-low `ROM_N` in both the Rev-A and modular twins;
  the superseded provisional high-true interpretation is retired. Rev-A schematic is 119 refs / 135 nets with the
  decode sockets, mode inverter, jumpers, and observability headers; the
  socket↔twin and observability contracts are enforced
  (`kicad/check_rev_a_physical.py`).
- **Compact 200x200 placement DONE and collision-clean.** Re-laid-out from the
  sparse 285x285 experiment to a 200x200 mm board: all 119 parts placed by a
  footprint-size-driven floorplan in `kicad/gen_rev_a_pcb.py` (wide DIPs
  horizontal to keep bands short, DIP-16/14 vertical, decoupling caps at each
  chip's short side, a grid-aligned left resistor field). Parts and functional-
  block borders align to a 0.2" (5.08 mm) grid; block frames are computed from
  member footprints and shared by the checker. `kicad/check_rev_a_placement.sh`
  (silk/overlap), `kicad/check_rev_a_footprints.sh` (every modelled pin lands on
  a real pad), and `kicad/check_rev_a_pcb.sh` (5 mm edge keepout, block frames)
  all pass. GOST-font silk preview via `kicad/render_silk_preview.sh`.
- **Routing DONE and DRC-clean.** The 200x200 119-ref/135-net board contains
  2,873 tracks on F.Cu/B.Cu, with In1.Cu reserved/fill-checked as GND and In2.Cu
  as VCC. The freerouting fork (v1.9) routes all 357 nets with 0 unrouted / 0
  violations, and KiCad DRC reports zero violations and zero unconnected items.
  The stale per-net seed routes (tuned for the old 285x285 placement) were
  removed; only the recomputed J3 USB-C GND shield seed remains.
- **Phase 4 bench tooling DONE in software:** framebuffer-readback oracle
  (`sim/vjuga_readback_check.sh`, validated vs twin + cosim) and the UNO
  single-step sketch + twin reference trace (`tools/vjuga_single_step/`).
- **Router toolchain is now cross-platform.** The `external/freerouting` fork
  submodule + Gradle-provisioned Temurin JDK 25 in `~/.gradle/jdks` build and
  run on macOS arm64 as well as Linux; `route_rev_a_pcb.sh` probes both home-
  folder JDK layouts. Setup instructions:
  `spinoffs/minimal-vga/kicad/fab-notes.md` (Router toolchain section).

**Remaining before the first bare PCB:**

1. **Footprint review items:** exact HRO TYPE-C-31-M-17/C283540 USB-C
   compatibility is now checksum- and geometry-guarded in
   `spinoffs/minimal-vga/docs/rev-a-usb-c-candidate.md`, including its six
   contact pads, four shell tabs, body outline, and power-only CC/VBUS/GND
   contract. Exact Bourns MF-RG300-0-14/C3761779 PTC compatibility is now
   checksum-, electrical-, topology-, and static-fit-guarded in
   `spinoffs/minimal-vga/docs/rev-a-ptc-candidate.md`. Automation still cannot
   close physical pin-1 orientation of the socketed parts, the exact TVS
   variant, F1 thermal/load qualification and first-article insertion, or J3
   order-time stock/orientation and first-article inspection.
2. **Regenerate and review the fabrication package.** The routed source is
   machine-verified, but `docs/rev-a-manufacturing-readiness.md` marks the
   current frozen Gerber/drill ZIP stale against the compact 200x200 route.
   Re-export it on the canonical Linux toolchain, freeze the new checksum, and
   complete vendor preview, live-stock, and assembly-capability review.
3. **Disposition full-board LVS explicitly.** The decode/observability contract
   is guarded, but whole-board chip-accurate LVS remains incomplete. It is a
   bare-board release gate unless the owner records a specific waiver with an
   independent schematic/pinout/copper review as compensating evidence.

Not blocking the bare board, but settle before populating: U24's corrected
GAL22V10 pinout and Gray-coded DRAM timing now pass the slower MK4564-12 limits
at 4 MHz; device-specific compilation/programming remains. The former
real-ROM-through-VGA release item is formally out of Rev-A workbench scope:
framebuffer capture is the physical boot oracle, while VGA remains an
experimental output rather than a bare-board or chip-test gate. The formerly
stale real-ROM boot wording and guard are synchronized with the passing proof.
Full order-readiness checklist: `docs/rev-a-manufacturing-readiness.md`.

### VJUGA Rev B modular spin-off

Rev B is a distinct four-board modular experiment and must not be hidden under
the Rev-A workbench status. Its B1 CPU, memory, I/O, and backplane sources,
mechanical mating checks, packages, and pinned backplane parts are recorded as
order-safe in `spinoffs/minimal-vga/docs/rev-b-order-readiness.md`. Ordering one
first-article set is therefore an explicit owner purchasing decision, not an
automatic consequence of this plan.

If ordered, B1 bench bring-up is the only next implementation phase. Record
as-built parts and jumper settings, prove the bring-up serial/RAM result, check
slot clearance and convention-only card orientation, and capture power and bus
timing before authorizing duplicate boards or any B2 video-card tape-out.

### Parts and assembly preparation

- Use `docs/replica-dual-config-bom.csv` as a planning BOM, not a shopping
  cart. Programming, circuit-review, and mechanical-review rows remain gated.
- The 27 photo-proven bare DRAM-grid footprints remain fabricated but carry
  native KiCad DNP and position-file exclusion metadata; the schematic and
  generated populate-now BOM guard the same assembly disposition.
- Candidate static compatibility is now guarded in
  `docs/replica-candidate-parts-readiness.md`: Western Digital FD1793B-01
  plastic DIP matches D93's complete pin contract, +5/+12 V rails, 1 MHz
  mini-drive mode, and 0.600-inch footprint; Mostek MK4564-12 in its DIP option
  matches the populated bank's JEDEC 64Kx1 pin classes, single +5 V supply,
  128-cycle/2 ms refresh, 120 ns access, 220 ns cycle, and DIP-16 footprint.
  Before buying or seating parts, verify live seller stock/authenticity, fit E4
  2-3 and measure +5 V at DRAM pin 8, close the remaining FDC support gates,
  and bench-test the received parts and board timing.
- Buy/test long-lead parts early only when the choice cannot force a board
  change. Assemble sockets first and verify rails with no ICs installed.

### Digital-twin fidelity

The twin is already sufficient as a boot/FDC/BASIC oracle. Further work should
serve physical bring-up or historical fidelity:

The sample-domain X7 receiver and CRT-display work is specified separately in
[`docs/crt-cvbs-simulation-plan.md`](docs/crt-cvbs-simulation-plan.md). That
plan records the `ddanila/famicom-rf-hackrf-decoder` fork, keeps the Juku
waveform truth in this repository, and separates electrical waveform, receiver
lock, active-image, and CRT-presentation claims. Its first WP4 checkpoint now
guards the traced R62-R65/VT2/X7 DC topology, both 75-ohm and unterminated
loads, and a declared tolerance sweep. That result is deliberately provisional:
exact-device sheets now guard the К555ЛП5 voltage/fanout envelope and the
old-package КТ315Б pinout, gain endpoints, saturation, current, voltage, and
power limits. The SN74LS86A sheet independently corroborates the exact
К555ЛП5 sheet's fanout-derived currents, and the official TI SDLM061 PSpice
package now supplies a machine-guarded, data-sheet-generated typical-25-C
comparison driver: its supply-dependent 4.88–5.00 kΩ pull-up and
43.75–62.5 Ω pull-down resistances participate in the coupled D34/R62-R64/VT2
solve instead of fixed pin voltages. The nominal 75 Ω result is 0, 0, 0.244,
and 1.818 V across the four input states, while high-state current still
crosses the exact-device fanout-derived envelope. TI typical behavior is not
К555ЛП5 equivalence evidence; the exact device sheet still has no nonlinear
I/V curve. D34 loaded-drive behavior and physical calibration therefore remain
open before the model can claim physical X7 levels. The separate
decoder fork point is also clean-checkout reproduced on Linux: all three
targets build, CTest passes 1/1, and `synth_ntsc` decodes 29 frames with 7/7 bars; the
fork now records its upstream/fork authority and deterministic-fixture policy,
and Linux CI run `29885055666` passes the full RF/IQ build, CTest, and direct
synthetic regression. CVBS-plan WP0 is complete. WP1 is also complete at fork
commit `d383beb3dd038154364fb76f993ad32d12fe2d44`: strict little-endian float32
baseband ingestion bypasses RF-only DSP, supports polarity/gain/offset plus
auto or fixed AGC, and produces deterministic headless output. An independent
temporary six-field grayscale fixture matches all five output bars exactly;
Linux CI run `29886015187` passes the full build, all three CTests, and the
unchanged direct RF/IQ regression. This proves only the generic NTSC-rate
baseband boundary, not Juku timing, physical X7 voltage, or receiver lock.
CVBS-plan WP2 is now complete at decoder fork commit
`10bfa4b9ae6c1ce071633459170b067fe3e2d91f`: explicit timing profiles drive
line/sync/frame/active-window acquisition, monochrome bypasses NTSC chroma,
and JSON reports measured line/frame lock, rates, sync width, blank, and video
range. An independent 12.5 kHz/200-line fixture matches five exact bars, while
five malformed fixtures distinguish horizontal and vertical lock failure.
Linux CI run `29886839537` passes the full build, five CTests, and unchanged RF
regression. No Juku preset or timing constant has been guessed; physical Juku
waveform generation and lock remain separate later work packages. The first
WP3 checkpoint now exposes the source-proved D42/D43/D37 and D56/D34_SYNC
contributors through simulation-only probes and a guarded timestamped event
export. Controlled stimulus verifies the modeled D56 pulse widths and traced
D34 sync XOR, while every event machine-marks the shared-DRAM slot schedule as
unknown and deliberately omits the unresolved D34 signal input. It therefore
does not claim a Juku raster, framebuffer reconstruction, composite voltage, or
X7 samples. The following guarded checkpoint now executes the exact `ekta37`
D54/D55 control/count bytes through `juku_top` with 8253 BCD and modes 1/2:
the autonomous physical chain measures 15.625 kHz horizontal timing,
313-line/49.920128 Hz frames, 320x241 active geometry, and the modeled D56 sync
pulses. This closes digital raster timing only; shared-DRAM video slots,
D34_SIG, fetched pixels, and X7 voltage remain open. Decoder fork commit
`b1d62c085e416c80cff35d8a77a8fbc397eead51`, pinned to this repository's
`eb4d6ab6777db3f97306c9111e9c723c97dcf750` timing evidence, now exercises an
explicitly synthetic five-bar Juku-timing waveform. Linux CI run `29888769589`
passes the full application build, all six CTests, and the unchanged NTSC
regression. This closes only the planned known-good receiver fixture: it is not
a built-in Juku preset and makes no physical shared-DRAM, D34_SIG, X7-voltage,
or framebuffer-agreement claim. The physical pixel-chain audit also corrects
the shared D41/D42/D43 ИР16 primitive against the SN74LS295B contract: LD/SH
high loads on the falling clock edge, LD/SH low shifts right, and pin 8 is an
active-high three-state output control. Consequently `SHIFT_G` is now correctly
bounded as D42/D43 OC plus D41 clock, not a guessed serializer clock gate; its
remote source and `TIMING_TAG17` remain open. The adjacent D48-D52 КП14 model is
also corrected to the datasheet's inverting 74LS/S258 truth table and active-low
output enable. The РУ5 model removes that physical inversion only at its internal
storage index, preserving CPU-linear addressing and the guarded boot behavior;
full-resolution sheet-2 review also retracts the former D59.5/.6 no-connect
claim. D59.5 reaches E14 and the D50/D51 video-mux /G inputs, while its inverted
D59.6 output reaches E13 and the D48/D49 CPU-mux /G inputs. This closes the
local complementary enable topology. Owner continuity on 2026-07-22 now closes
D59.5's long source onto the D40.11 1 MHz rail through D92.2 and onward to
externally tied D95.5/.6; exact `.009` sheets 2/3 corroborate the 1 MHz labels,
the D92.2/.3 tie, and the external D95.5/.6 junction. This disproves both the
temporary TTL-high source boundary and the attribution of D92.2/.3 to the
separate 2 MHz/`PHI2TTL` path. The canonical JSON, HDL, generated schematic,
source/routed PCBs, LVS/DRC reports, and zero-open manifests now carry that
single-driver correction atomically. The promoted route retains 322 footprints
and 2,436 pads with 30,904 copper items, zero connectivity opens, zero electrical
blockers, and zero dangling items; exact topology is guarded by
`kicad/check_d40_1mhz_route.py` and documented in
`docs/d40-d59-d92-d95-1mhz-route.md`. Tentative D96.6 membership remains
rejected pending an isolated-pad resistance check because sheet 3 makes D96.6
an active `/Q1` feedback output.

1. Replace the simulation-only framebuffer read port after D41/shared-DRAM
   slot timing is evidence-complete.
2. Preserve reset-to-EKDOS and disk-BASIC guards while physical FDC wiring is
   corrected. The vendored EKDOS source requests write via `DKWR=0x12`, and
   disassembly of the exact `ekta37` ROMBIOS proves commands `0xA0/0xA2`
   followed by 512 port-`0x1F` writes. Both C and HDL models now implement and
   readback-test that bounded path. The C guard boots `ekta37` to install its
   RAM monitor services, invokes the EKDOS-facing `RWFLOPPY` vector at `0xFF59`,
   begins with a cold partial write that automatically prereads nonzero media,
   writes three distinct 128-byte offsets, reads all four cache records without
   extra FDC I/O, and then proves their single physical flush through the exact
   command sequence
   `0x80,0xA2,0x80`. The nested `FLOPPY` handler and monitor
   epilogues return with zero `ERRC`, and a disposable writable image preserves
   all three modified records plus the untouched original record; repository
   media remains read-only unless the caller explicitly opts into a writable
   copy. A second phase passes CP/M unallocated-write type `C=2`, fills all four
   records while `UNACNT` counts from 32 to 28 without a preread, and proves the
   optimized physical sequence `0xA2,0x80`. The public `RAMDISKSEL` vector is
   now exercised through its exact `FF5C->E9B3` ROM path: failed bank switching
   returns `0xFF` after restoring ordinary RAM, first use writes the guarded
   `RamDisk` signature and all 63 `0xE5` directory markers, and a signed drive
   reopens without formatting. Public cold `BOOT=0xCA00` is now bounded at its
   non-returning `CCP=0xB400` handoff: it installs exact low-memory WBOOT/BDOS
   vectors, DMA `0x0080`, zero cache state and drive 0, formats a blank cloned
   RAM disk, performs exactly 10,240 framebuffer writes through 144 monitor
   trampolines, and issues no FDC command. Public `WBOOT=0xCA03` also reaches
   CCP through its source-defined resident-BDOS branch, preserving a deliberate
   nonstandard `0xB506` resident target without framebuffer or FDC activity.
   Its default `WRetry` branch is now separately guarded after poisoning the
   five-sector CCP window. This closes a memory-model error: the low-ROM mode
   permits page-zero write-behind, allowing the Monitor's low-stack dispatcher
   to preserve its `0xFEE8` return frame; the high ROM remains write-protected
   as required by the independent Monitor 3.3 framebuffer oracle. Exact ROM code
   then reads physical sectors `3,2,4,6,5` with five `0x80` commands / 2,560
   data bytes, restores `SP=0x0100`, applies the source-defined three-byte
   `CCPExit` patch, and reaches the byte-exact reloaded CCP at `0xB400`.
   The RAM-drive data path is also exercised with
   the disk-booted EKDOS BIOS rather than a synthetic selector assignment:
   public `HOME` at `0xCA18` always selects track zero, invalidates a clean
   host-sector cache, and preserves an explicitly dirty cache for its later
   flush. Public `LISTST` at `0xCA2D` executes the source `POLLPT` target and
   returns `A=0` (printer not ready) even from a nonzero input accumulator.
   Public `PUNCH=0xCA12` and `READER=0xCA15` both execute their installed shared
   `XRA A; RET` target and return unavailable; this also recovers the intent of
   the archive-damaged `DP RTNEMPTY` PUNCH source line without rewriting it.
   Public `CONST=0xCA06` traverses `DoFunction` and exact monitor `CONSTA=0xFF98`;
   at the prompt's empty keyboard boundary (`0xCF` released matrix inputs) it
   returns `A=0`. Public `CONIN=0xCA09` traverses exact monitor `RDCHR=0xFFD3`
   and its interrupt-fed keyboard buffer: a held shifted-`T` at source-faithful
   matrix column 4 / encoder bit 3, sampled by two 200,000-cycle frame IRQs at
   exact vector `0xFED4`, produces 34 matrix reads, two active `0x88` samples,
   and returns ASCII `T=0x54` through the installed `D7E7` trampoline.
   Public `CONOUT=0xCA0C` traverses `DoFunction` and exact monitor
   `WRCHR=0xFFD9`; at the prompt checkpoint, `C='C'` renders its exact
   ten-scanline cell at byte column 2 / rows 70..79, including the seven
   source-ROM glyph bytes, performs exactly ten framebuffer writes, advances
   the monitor cursor to byte column 3, and enters the installed `D7E7`
   trampoline. The guard accepts either exact uniform `0x00` or `0xFF` cursor-blink
   phase and normalizes that phase before comparing the rendered glyph, because
   cycle-accurate FDC polling can shift the blink phase without changing output.
   Public `LIST=0xCA0F` traverses `PrintCh=0xFFEE` and the boot-installed
   `D7F1->E2A2` service; with USART transmitter-ready asserted at port `0x0E`,
   it emits the exact input character to data port `0x0C`.
   Public `SELDSK` at `0xCA1B` returns three contiguous 16-byte DPHs, rejects
   drive 3 without changing the selected drive, returns zero for unavailable
   drive C, and returns the source-exact RAM DPB when C is present. Its
   `DoFunction` trampoline switches from a guarded caller stack to
   `STAK=0xD2FC` while entering ROMBIOS. Every RAM-drive endpoint transfer now
   enters through public BIOS `SETTRK`, `SETSEC`, `SETDMA`, and `READ`/`WRITE`
   vectors (including CP/M write types 0 and 2), verifies the installed work
   fields and zero return status, and contains no synthetic track/sector/DMA
   assignment. Public `SECTRAN=0xCA30` is likewise exhaustive: its DPH-provided
   table returns the source-exact permutation for all 40 floppy records, while
   the RAM-drive null table preserves sector 0 and 127 unchanged. The
   source-guarded `MDISKPAR` describes
   192 x 1 KiB blocks: exact ROM writes and reads independent sector-0 and
   sector-127 patterns across all twelve track halves and all six port-`0x04`
   banks, including the final 128 bytes at bank-5 offset `0x7F80`; every slice
   restores bank 6 and emits no FDC command. A
   complementary read-only reopen proves the ROM consumes the EKDOS
   `VIARV=10` retry count, observes WRITE PROTECT without accepting data or
   changing media, then masks the failed dirty flush when its subsequent read
   clears `ERRC`; this exact historical error-propagation boundary is guarded.
3. Revisit cartridge BASIC only when a complete artifact or documented loading
   procedure appears; do not invent missing pages. The 2026-07-15 generated
   firmware-lineage audit proves that 7,224 bytes of the cartridge body are
   byte-identical inside Monitor 3.3 (and differ once in Monitor 2.2), so the
   BASIC implementation itself is recovered; the exact correspondence ends
   before the missing page. The Monitor 2.2 audit source-proves its sole BASIC
   byte correction and closes block 3, but the preservation catalog confirms
   unstable reads for the still-bad final two ROM blocks. An exhaustive bounded
   donor search across all seven related 16 KiB ROMs finds no checksum-closing
   three-byte-context donor and rejects the tempting `0x3BAA` EktaSoft match as
   a different restart-vector initializer; blocks 6 and 7 remain unpatched.
4. Extend sound/serial behavior only to answer concrete bench questions.
   The first Jukuravi prerequisite is now guarded: opt-in cosim D11/8251
   data/status mirrors at `0x08..0x0B` implement the async mode/command and
   TxRDY/RxRDY/TxEMPTY slice over a real PTY. Its transmit holding register and
   shifter now expose the distinct `00` (holding full), `01` (frame active),
   and `05` (fully empty) status stages in both cosim and HDL. A stack-free
   synthetic ROM sends `55 A5`, receives `3C`, and echoes it only after proving
   those transitions (`tests/cosim_usart_pty_test.py`). The first
   diagnostic-ROM boot rung is now
   a deterministic, exact-hash-guarded 8 KiB D15 image: it programs D57 for a
   nominal 1 kHz tone, delays 1,000,035 T-states, silences the channel, and
   halts with unchanged SP, IFF clear, mode 0, and no RAM writes. Its cosim I/O
   guard and the existing HDL SOUND-path guard are composed by
   `sync/jukuravi_d0_check.sh`; analog output remains a bench boundary. The
   next exact-hash-guarded 8 KiB image now adds the register-only CPU self-test:
   17 ALU/flag/rotate/DAA results fold to signature `D0`, while any conditional
   or final-signature mismatch selects a continuous nominal 250 Hz CPU-bad
   tone. Cosim and the vm80a-based full HDL top execute both success and
   injected-failure paths with exact I/O and no memory writes; the program uses
   no stack instructions. The next exact-hash-guarded image recovers and
   initializes D11, emits `55`, and requires the distinct `05 -> 00 -> 01 ->
   05` idle/holding/shift/empty states under two bounded register-only timeouts.
   Cosim and the full vm80a HDL top prove normal, injected stuck-TX (continuous
   nominal 500 Hz USART-bad tone), and predecessor CPU-bad paths with exact I/O
   and no memory writes. The HDL fixture drives only the already-documented
   unresolved upstream 16 MHz rail boundary and an explicitly asserted X3 CTS
   input; D104 and D103/D57/D11 remain integrated. The real Nano harness must
   likewise assert active-low CTS before reset because an open line receiver
   leaves transmission disabled; an HDL inactive-CTS injection proves that case
   takes the bounded 500 Hz path. This stage needs no received byte or ack.
   The next exact-hash-guarded image extends that first byte into a 16-byte `55`
   training run, emits a self-delimiting CRC-8 record carrying protocol/ROM
   versions and a whole-image CRC-16, and accepts only the matching framed ACK
   under bounded register-only waits. Cosim proves valid ACK, corrupt ACK, full
   timeout, local-TX failure, and CPU failure through a PTY. The vm80a full top
   shifts valid and corrupt ACK bits from X3 `SIN` through D104 into D11 and
   separately proves timeout; all paths write no RAM. Success gives a short
   nominal 2 kHz serial-confirmed beep, while missing/malformed ACK gives a
   continuous nominal 125 Hz serial-dead tone. USART sync/parity modes and
   physical baud timing remain outside the bounded model. The stack-free mode-0
   RAM survey and framed result stream are the next harness rung. That rung now
   has an exact-hash-guarded image: it replays the source-guarded D54/D55 timing
   setup, stays in mode 0, and runs fixed data/address/complement passes, a
   retention verification, and cross-page alias probes over every page
   `40..FF`. One CRC-protected record
   per page carries its page number and OR-mask of failing D84–D91 data bits.
   Full-range cosim proves identical traffic on every clean or failed page,
   maps a `7A5C` stuck-low/stuck-high injection to only page `7A`/mask `28`,
   and maps a page-`90`/page-`50` alias to exactly those pages with mask `FF`.
   The host decoder groups bad pages by chip and selects
   the largest all-bits-good window. The vm80a full top executes the identical
   loop body through clean and forced-D87 DRAM cells on a one-page bounded
   fixture, with exact framed output, mode 0 retained, and interrupts clear.
   The next cumulative image now implements the fixed-window serial-dead
   fallback as well. Missing/malformed ACK gives a finite nominal 125 Hz marker,
   initializes D54/D55, and wholesale-tests 4 KiB candidates at `4000` and
   `C000` with data/address/complement and retention passes. Any good candidate
   gives three short nominal 2 kHz pulses. If neither passes, 1–8 nominal 1 kHz
   pulses identify the first failing D84–D91 bit and a continuous nominal
   125 Hz tail declares no window. Exact-image cosim retains the acknowledged
   192-page path and proves clean/no-ACK plus global-D87-dead/no-ACK outcomes;
   the vm80a full top executes both fallback results through the bit-sliced
   DRAM bank with exact traffic and cadence. The next cumulative image adopts
   the official EktaSoft block-1 convention: `000A` stores the additive sum of
   `000B..07FF`, and a stack-free runtime loop checks all 2,037 bytes after the
   CPU signature but before D11 or RAM activity. Exact-image cosim retains the
   acknowledged survey and no-ACK fallback, while a `07FF` bit flip reaches
   only the continuous nominal 2 kHz ROM-bad tone; clean/corrupt vm80a paths
   prove the same D15 read branch. The next cumulative image initializes D10
   with the real `D6/FE` MCS-80 pair, reads the interrupt mask back as both
   `00` and `FF`, and restores every IRQ masked on success and failure. Cosim
   proves both stuck-bit polarities plus the cumulative ACK/no-ACK paths; vm80a
   proves clean and forced-low D10 readback with a distinct continuous nominal
   4 kHz failure tone, IFF clear, and no RAM write. The next cumulative image
   tests D27/8255 ports A/B/C as mode-0 outputs with complementary `00`/`FF`
   readback, then restores mode-0 all-input control and clears all output
   latches on success or failure. Exact-image cosim proves both stuck-bit
   polarities plus the cumulative ACK and fixed-window paths; vm80a proves the
   early clean/fault branches and the shared two-window fallback through the
   bit-sliced DRAM bank. X2 must be disconnected because this is a register and
   decode test, not an external-load test. Failure gives a distinct continuous
   nominal 750 Hz tone with D10 masked, IFF clear, and no USART or RAM write.
   The next cumulative image tests every D54/D55/D57 counter with latched,
   phase-tolerant DB7-high and DB7-low predicates. Its 251-byte post-table
   extension has a separate stack-free additive guard, and both verdicts
   recover D57 before continuing or selecting a distinct continuous nominal
   1.5 kHz PIT-bad tone. Exact-image cosim proves all counter/control selects,
   both restricted `JUKU_PIT_FAULT` mismatch polarities, the corrupt-extension
   branch, and cumulative ACK/no-ACK paths. vm80a proves clean, forced-D55,
   corrupt-extension, and both physical fallback outcomes across all three PIT
   instances. The final cumulative D0 image retains that ladder and, only on
   the acknowledged full-survey path, verifies the visible `D800..FDA7` range,
   writes all 9,640 bytes as an address-XOR field, and reads the field back.
   A bad precondition or readback gives a distinct continuous nominal 3 kHz
   tone with no completed pattern; the no-ACK fallback never assumes video RAM
   works. Both post-table executable regions are independently additive-
   guarded. Exact-image cosim proves the complete 40×241 draw, D84 fault path,
   both corrupt-extension branches, and no-ACK predecessor. vm80a proves a
   bounded eight-row physical DRAM draw/readback, 2,560 abstract pixels, the
   framebuffer-fault halt, and both version-8 fallback outcomes. This completes
   the planned D0 firmware ladder in simulation. The first Stage D1 checkpoint
   now runs the dependency-free host CLI as a separate process against that
   exact ROM: it validates the identity banner, sends the matching ACK, decodes
   all 192 page records, prints D84–D91 and largest-window verdicts, and retains
   timestamped RX/TX/JSON evidence. Clean and injected D87+D89 page-`7A` cosim
   sessions prove both human and machine-readable outputs. The second Stage D1
   checkpoint supplies the classic Nano's byte-transparent 115200-USB-to-
   nominal-9600-Juku bridge: a portable test covers all 256 byte values, the
   exact ACK, both directions, counters, and bounded service, while the actual
   `SoftwareSerial` sketch compiles for `arduino:avr:nano`. Its D10/MAX3232 CTS
   contract has a boot-safe pull-down and a latched overflow indicator. The
   third checkpoint adds D4's isolated startup-reset driver: a wrap-safe state
   machine asserts its optocoupler LED for 250 ms, enforces 50 ms of quiet
   recovery, and is boundary-tested across `millis()` rollover before the
   bridge runs. The fourth checkpoint makes each real `--port` session
   deliberately restart that Nano sequence: dependency-free POSIX modem
   control releases DTR for 50 ms, reasserts it, flushes stale transport bytes,
   and records both the request and completed control sequence in JSON. Mocked
   ioctl ordering/failure plus the no-reset `--fd` cosim path are guarded, with
   an explicit `--no-nano-reset` escape hatch. The fifth checkpoint adds
   conservative missing-banner recovery: reset-enabled `--port` sessions wait
   15 seconds for a valid banner, then perform at most two fresh DTR/reset
   attempts. By default, any decoded protocol frame, transport error, or
   failure after a valid banner aborts without retry; the later explicit
   heartbeat-gap budget is the sole exception. JSON retains per-attempt byte,
   frame, banner, error, and DTR evidence. The SPDT S1 board-side contact pair,
   physical use of uploaded-test heartbeat recovery and voltage-safe liveness
   probes remains gated on continuity measurements of the real
   S1/X3/testpoint wiring. The
   sixth checkpoint implements the low-voltage side of reset hold:
   grounding the Nano's pull-up D5 service input extends D4 assertion
   indefinitely or reasserts it after startup, gates both bridge directions,
   and requires the same minimum pulse plus fresh quiet recovery on release.
   Pin polarity, long hold, release boundaries, post-ready reassertion, and
   rollover-safe timing are guarded in the compiled sketch; D5 never crosses
   the isolation barrier and the S1 contact remains measurement-gated. The
   seventh checkpoint starts Stage D2 with a cumulative version-9 ROM: after
   the full D0 survey and framebuffer readback, a separately checksummed loader
   accepts CRC-framed 1–253-byte chunks in `4000..D7FF`, immediately verifies
   each RAM write, and runs an in-range entry. Fixed `0A00` serial-get, `0A03`
   serial-put, `0A06` return, and `0A09` print vectors make uploaded programs
   self-reporting. Exact-image cosim proves corrupt/short/range/unknown command
   rejection, successful upload and put/print/return execution, and injected
   RAM readback failure. The eighth checkpoint implements host file/chunk
   orchestration: `--load` waits for and validates READY, requires the requested
   range to fit both the ROM boundary and the survey's largest-good window,
   follows the advertised chunk limit, requires every LOAD_RESULT, and sends
   RUN unless `--load-only` was requested. Source SHA256, range, API contract,
   per-chunk status, RUN acknowledgment, and exact raw frames are durable
   session evidence. The actual CLI uploads 300 bytes in two chunks and runs an
   uploaded HLT under cosim; any upload-stage failure aborts without reset
   retry. The ninth checkpoint adds opt-in post-RUN heartbeat supervision.
   Uploaded programs send CRC-framed type-`0x30` records carrying heartbeat
   version 1 and a rolling sequence byte; `--heartbeat-count` requires a
   bounded consecutive run, including `FF -> 00` wrap, while
   `--heartbeat-timeout` bounds every gap. JSON retains each sequence and
   source frame index. The real CLI accepts three heartbeats from uploaded code
   and separately fails a spinning program after RUN_ACK with exact timeout
   evidence and no retry. The tenth checkpoint makes recovery software-ready
   without relaxing that physical gate. Explicit
   `--heartbeat-reset-retries N` is default-off and accepted only for a
   reset-enabled real `--port`; each heartbeat gap consumes at most one bounded
   budget entry and performs a completely fresh DTR/Nano reset, banner, survey,
   upload, RUN, and heartbeat attempt. Every attempt snapshots its loader and
   heartbeat evidence. Missing-banner retries retain their independent budget,
   while malformed heartbeats, upload/protocol/transport errors, and every
   other post-banner failure remain non-retryable. Mocked modem control proves
   success, exhaustion, counter accuracy, and all non-retry boundaries. The
   S1 board-side contact remains forbidden until directly measured. The
   eleventh checkpoint implements the disconnected-safe Nano side of liveness
   probing without inventing a Juku testpoint. Open/pulled-up D7 leaves the
   feature byte-transparent and emits nothing. A local D7-to-GND service jumper
   opts into a rollover-safe 100 ms post-reset observation: one-shot falling
   edges on D2/D3 latch conditioned clock/`-MRDC` activity and active-low D6
   latches conditioned RESET-released state. The Nano emits one exact type
   `0x40`, version-1 flags frame before releasing the buffered serial bridge.
   The host validates and retains it in both session and attempt evidence; a
   report without a subsequent ROM banner aborts rather than entering the
   evidence-free missing-banner reset loop. The portable core, exact CRC,
   reset-cycle clearing, default-off path, host rejection cases, and actual AVR
   sketch compile are guarded. D2/D3/D6 may connect only to a future
   isolated/open-collector conditioner; target board nets, voltage/polarity,
   and physical hookup remain measurement-gated.

## Physical bring-up sequence

Once a released board and programmed parts exist:

1. Bare-board shorts/continuity and connector polarity.
2. Current-limited rails, including derived -5 V, with no ICs seated.
3. Oscillator, reset, 8080 phases, READY/STSTB, then an 8080 free-run/NOP
   test (0x00 forced on the data bus, address lines counting) before trusting
   ROM/RAM, and first ROM fetch.
4. ROM decode and RAM write/read/refresh.
5. Video timing and composite output.
6. Keyboard scan and Monitor/ROM commands — **Tier 1**.
7. FDC with a floppy emulator, then beeper and serial — **Tier 2**.
8. Factory PROMs, period parts, original peripherals, and surviving-machine
   comparison — **Tier 3**.

## Milestones

- [x] Structural model boots and matches the software oracle.
- [x] EKDOS and disk BASIC reach visible prompts in uninterrupted HDL.
- [x] Current engineering PCB package is regenerated and DRC-clean for the
  accepted source topology. The deterministic upload ZIP and machine package
  gates pass; the separate functional/factory-construction design hold still
  forbids upload or ordering.
- [x] Deep value-level cosim guard reaches `CTRACE-END` across the default
  130,000-read window and fails on any address/data divergence.
- [x] Cosim exposes a regression-guarded 8251 async data/status slice through
  a PTY for Jukuravi diagnostic-ROM and host-tool development.
- [x] Jukuravi D0 rung 1 has an exact-hash-guarded, burn-sized D15 image whose
  stack-free/RAM-free alive-beep sequence executes under cosim and reaches the
  independently guarded HDL D57/SOUND path.
- [x] Jukuravi D0 rung 2 has an exact-hash-guarded, burn-sized D15 image whose
  register-only CPU signature test and distinct CPU-bad tone execute through
  both success and injected-failure paths in cosim and the vm80a HDL twin.
- [x] Jukuravi D0 rung 3a has an exact-hash-guarded, burn-sized D15 image whose
  local 8251 transmit-state test, bounded timeout, and distinct USART-bad tone
  execute through success and injected-failure paths in cosim and vm80a HDL.
- [x] Jukuravi D0 rung 3b has an exact-hash-guarded, burn-sized D15 image whose
  framed version/checksum banner, exact ACK, and distinct serial-confirmed/dead
  outcomes execute through valid, malformed, and timeout paths in cosim and
  through X3/D104/D11 in the vm80a HDL twin.
- [x] Jukuravi D0 rung 4a has an exact-hash-guarded, burn-sized D15 image whose
  full mode-0 48 KiB page survey, framed bit-mask output, retention pass, and
  host largest-good-window verdict execute in cosim, while clean and forced-bit
  loop paths execute through the bit-sliced vm80a HDL DRAM bank.
- [x] Jukuravi D0 rung 4b has an exact-hash-guarded cumulative D15 image whose
  no-ACK fixed-window tests, windows-found cadence, D84–D91 chip-ID count, and
  no-window continuous tone execute for clean and globally dead-bit RAM in
  cosim and through the bit-sliced vm80a HDL DRAM bank.
- [x] Jukuravi D0 rung 5a has an exact-hash-guarded cumulative D15 image whose
  official `000A=sum(000B..07FF)` convention, clean continuation, and distinct
  corrupt-ROM halt execute in cosim and through vm80a's physical D15 path
  before USART, RAM, interrupts, or a memory-mode change.
- [x] Jukuravi D0 rung 5b has an exact-hash-guarded cumulative D15 image whose
  D10 command/data decode, complementary IMR readback, safe terminal mask, and
  distinct PIC-bad halt execute for clean and stuck-bit cases in cosim and
  through the vm80a HDL twin before USART, RAM, or interrupt enable.
- [x] Jukuravi D0 rung 5c has an exact-hash-guarded cumulative D15 image whose
  D27 A/B/C complementary readback, all-input/zero-latch recovery, and distinct
  PPI-bad halt execute for clean and stuck-bit cases in cosim and vm80a, while
  the compact shared fallback loop is replayed through both physical DRAM
  windows for clean and forced-D87 outcomes.
- [x] Jukuravi D0 rung 5d has an exact-hash-guarded cumulative D15 image whose
  separately checksummed extension exercises all nine D54/D55/D57 counters
  with phase-tolerant complementary predicates, restores D57, and reaches the
  distinct PIT-bad halt for injected faults in cosim and vm80a, while both
  version-7 fallback outcomes retain exact physical PIT and DRAM traffic.
- [x] Jukuravi D0 rung 5e has an exact-hash-guarded cumulative D15 image whose
  acknowledged path verifies, draws, and reads back the complete 9,640-byte
  address-XOR framebuffer, suppresses the pattern for injected D84 failure,
  guards both executable extensions, and retains the no-ACK path in cosim and
  vm80a, including a bounded abstract-pixel comparison.
- [x] Jukuravi D1 host checkpoint runs the real CLI against the exact final D0
  ROM, validates and acknowledges its identity, decodes the complete clean and
  injected-fault surveys into D84–D91/window verdicts, and preserves timestamped
  raw RX, raw TX, and JSON session evidence.
- [x] Jukuravi D1 Nano bridge core preserves every byte in both directions
  between the 115200 hardware USB UART and nominal-9600 software UART; the exact
  ATmega328P sketch compiles, explicitly asserts CTS through a MAX3232 with a
  boot-safe pull-down, and latches receive overflow without contaminating the
  framed evidence stream.
- [x] Jukuravi D1 Nano startup-reset core drives only an isolated D4 optocoupler
  input, holds a conservative 250 ms switch closure, enforces 50 ms recovery
  before bridging, and passes exact boundary plus `millis()`-rollover tests in
  the compiled ATmega328P sketch; S1 board-side hookup remains measurement-
  gated.
- [x] Jukuravi D1 host-controlled session reset sends an explicit DTR
  release/wait/assert sequence before every real `--port` run, flushes stale
  bytes, logs requested/completed state without claiming physical observation,
  preserves raw `--fd` cosim sessions, and has a guarded opt-out and failure
  path.
- [x] Jukuravi D1 missing-banner recovery gives reset-enabled real-port
  sessions a short banner deadline and at most two fresh-reset retries; that
  policy never retries decoded partial or post-banner evidence and records each
  attempt plus the exact count of completed DTR sequences in JSON.
- [x] Jukuravi D1 local reset hold uses an active-low, pull-up Nano D5 service
  input to extend or reassert only the isolated D4 optocoupler drive, keeps the
  serial bridge gated, and enforces minimum assertion plus fresh recovery on
  every release; board-side S1 hookup remains measurement-gated.
- [x] Jukuravi D2 loader ROM preserves the cumulative D0 ladder, runtime-checks
  its own extension, verifies framed chunks in `4000..D7FF`, runs uploaded code,
  and exposes fixed serial/print/return vectors; exact-image cosim covers both
  executable success and injected readback failure.
- [x] Jukuravi D2 host upload orchestration validates READY and the surveyed
  good window, chunks and verifies a named file, optionally runs its in-image
  entry, and retains source hash, per-chunk results, RUN acknowledgment, and
  exact RX/TX evidence; post-survey failures do not retry unless the separate
  explicit heartbeat-gap recovery policy applies.
- [x] Jukuravi D1/D2 host heartbeat supervision validates CRC-framed versioned
  and consecutive post-RUN liveness records under a per-record timeout,
  retains exact frame/sequence evidence, and fails without retry; physical
  reset use remains S1-measurement-gated.
- [x] Jukuravi D1/D2 heartbeat recovery software is explicit, default-off,
  real-port/reset-only, bounded independently from missing-banner retries, and
  preserves each full loader/heartbeat attempt; only heartbeat gaps retry, and
  the board-side S1 connection remains forbidden pending measurement.
- [x] Jukuravi D1 Nano-side liveness capture is default-off and
  disconnected-safe, uses a local enable plus one-shot conditioned
  RESET/clock/`-MRDC` inputs, emits an exact framed report before bridge
  release, and is durable host evidence; Juku-side testpoints and conditioning
  remain measurement-gated.
- [ ] P0 physical connectivity is complete and rerouted.
- [x] Every populated PROM/EPROM has an exact-hash-guarded burnable Tier-1/2
  image, a device/pinout decision, and an explicit provenance boundary.
- [x] Independent reads from two `.009` boards corroborate the four adopted
  small-PROM tables, and the third-source archival D15/D16 pair exactly and
  uniquely supplies the adopted EktaSoft 3.7 contents.
- [x] Runnable boot executes from all four physical PROM tables. The D6
  memory-map oracle and the raw-strobe behavioral FDC bypass are retired;
  default FDC accesses consume D94's physical `.092` `/RE` and `/WE` outputs.
  D94's decoded enable/A4 functional fits and the behavioral ВГ93 device core
  remain explicitly separate connectivity/model-fidelity holds.
- [ ] Main-board design release passes; board is ordered.
- [ ] Functional parts kit is received and tested.
- [ ] Replica completes Tier 1 bring-up.
- [ ] Replica completes Tier 2.
- [ ] Replica completes Tier 3.

## Fixed decisions

- Historical evidence outranks emulator inference; `kicad/juku.board.json`
  records the current interpretation and provenance.
- The replica remains a 2-layer, 310 x 266 mm board unless new physical
  measurement contradicts it.
- Functional substitutions are allowed for Tier 1/2 only when electrically
  verified; Tier 3 requires historically appropriate parts and dumped PROMs.
- Independently sourced, repeated and exact-hash-guarded PROM/EPROM dumps are
  accepted as content truth once adopted; missing paper linkage between an
  archival filename and a factory programming-drawing number is retained as
  provenance nuance, not an open replica milestone.
- DRC, package checksums, or LVS of the modeled subset cannot alone authorize
  fabrication.
