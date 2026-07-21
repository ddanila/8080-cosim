# Routed PCB refresh audit

The routed fabrication snapshot predates substantial photo-driven placement and
connectivity work. It cannot safely receive the current source PCB's pad nets by
name alone: added and moved footprints now intersect old copper corridors.

## Reproducible audit

```sh
/usr/bin/python3 kicad/refresh_routed_from_source.py
/usr/bin/python3 kicad/refresh_routed_from_source.py \
  --check-report docs/routed-refresh-audit.md
```

The script compares complete endpoint sets and exact pad coordinates per net.
It classifies copper as reusable only when both are identical between
`juku.kicad_pcb` and `juku_routed.kicad_pcb`. Candidate generation is explicit:

```sh
/usr/bin/python3 kicad/refresh_routed_from_source.py \
  --output /tmp/juku-routed-refresh.kicad_pcb
```

The temporary candidate is an audit artifact, not a fabrication deliverable.
Pass `--report docs/routed-refresh-audit.md` after an intentional source or
routed-snapshot change to regenerate the guarded current-result table.

## Current result

<!-- routed-refresh-current:start -->
| Item | Count |
| --- | ---: |
| Source PCB SHA-256 | `141d384c0b01e79cff33e04a099ea6626a2f5ed9ca6ebe4b9b87f6dd00d81afb` |
| Routed-snapshot PCB SHA-256 | `f14ade81d3ff7b48ece405d91bc436a63c9f94617444371d7048c9893e3dd315` |
| Source footprints | 321 |
| Routed-snapshot footprints | 241 |
| Source-only footprints | 107 |
| Routed-only footprints | 27 |
| Routed copper nets classified by the refresh | 324 |
| Nets with currently reusable routed copper | 83 |
| Routed nets currently quarantined | 241 |
| Reusable non-duplicate track/via items | 963 |
| Quarantined/duplicate track/via items | 7,702 |
| Common-pad net mismatches requiring reroute | 381 |
<!-- routed-refresh-current:end -->

The source-only set includes `A17`, `A21-A32`, `AX401-AX423`, `A45-A62`, newly
modeled FDC support/passive parts, the restored target VD1 reset diode, and the
photo-fitted serial and oscillator parts. The routed-only set contains superseded `.006` option parts and the
off-board `S1`, `S4`, `X3`, `X8`, and `X9` bodies; the authoritative source
represents the applicable cable landings instead. X4 is likewise
schematic-only in the source; its modeled `AX401-AX423` landing row is absent
from the stale routed snapshot.

### Live-source salvage baseline

The hash-bound live classification also seeds an aggressive, explicitly unsafe
same-name/additive migration candidate. It imports 8,397 copper items on 304
nets. `salvage_routed_copper.py` then removes only migrated UUIDs named by
electrical DRC blockers; one round removes 558 items. The accepted result has
all 321 source footprints and 2,434 pads, retains 7,839 routed items, and has
883 uncapped connectivity gaps versus 1,814 on the bare source. KiCad's CLI
report is capped at 499 markers, but the Python connectivity graph supplies the
uncapped count. Shorts, clearance, crossing, hole, and edge findings are all
zero; 199 dangling tracks and 56 dangling vias remain. This improves the older
1,190-open fresh-source trial on a now larger source, but is still convergence
evidence, not production copper. Exact hashes, configuration, and counts are
guarded in `ref/routing/current-source-salvage-baseline.json`.

The follow-on uncapped-prune pass uses KiCad's connectivity graph rather than
the CLI's truncated 499-item list as its acceptance boundary. Adaptive
transactions remove 2,872 migrated items, reduce the exact open count from
883 to 677, and eliminate all 199 dangling-track plus 56 dangling-via findings
while preserving the 321-footprint/2,434-pad source identity and zero
electrical blockers. One hundred thirty-three bounded proposals across P5V,
STSTB, GND, W10_QA_SEL, D40Q1_D39, LATCH_B, REV, SER_TXD_INV, D6_V_ENABLE, MEMW,
D40Q2_D33, D42_Q, D106_PRESET_HIGH, D101_D02_R92_R99, X4_DSEL1_N, VID_MUX_G,
RAS, PROM_EN, FDC_IRQ_CONDITIONED_N, SER_TXD, LATCH_PRE, D97_RC2_C19_R100,
D97_RC1_C16, D99_RC2_TIMING, FDC_CLK, FRAME_INT, D39Y, D102_C2_C20,
D92_NOACC, D100_CONTROL_SHEET1_BOUNDARY, D33_CLK_RC, RES_RC, FDC_READY,
OSC_PRE, SEP_D28_CLK, D97_C1_C16, D102_RC2_C20_R108, FDC_INTRQ,
PRECOMP_CASCADE_2, V3_RC, DB0, RAIL_H, P12V, MA3, BA13, D53_Y1_R50, X4_TR00_N,
CAS_PRE, D33_O4, D102_RC1_C22_R102, RESIN, MA0, D34_RC_NODE, PHI2TTL,
D98_Y1_R94, X4_DIR_N, X4_HLOAD_N, X4_WR_GATE_N, D13_4_D105_2, XTAL16M,
D103_LD, CAS, XTAL_TRIM, X4_MOTOR_ON_N, X4_SIDE_SEL, X4_READY_N, X4_RD_DATA,
S_OC, BA11, BA12, BA14, X4_INDEX_N, DB1, ROE, CLKG_D33, X3_HARNESS_1, PHI2,
WREQ_N, D40QA, MA5, OSC_FB, FDC_RE_N, D40_CTRL_PULL, MA7, VT2_BASE,
D102_C1_C22, USART_TXRDY_IRQ, BA15, D99_RC1_TIMING, D36_D33, FDC_RAW_READ, A10,
A12, A15, SEP_D106_Q3, IORD, ROM_CS_A000, S_DSR, FDC_CS_N, DB2, S_RTS,
W10_QA_SEL_D50, BA0, VA8, X4_STEP_N, ROM_SEL, D53_Y2_R51, X2_PB7, X2_PB6,
X2_PB5, X2_PB4, X2_PB3, FDC_SEPARATOR_CLOCK, MA6, WR, S_CTS,
D93_TEST_WF_VFOE, CLKG_D36, FDC_EARLY_SEL, DC3, D99_RC2_TIMING, PRECOMP_TAP_1,
D105_MEMW_INV, BA1, SER_DTR, ROM_CS_EXP17, D53_Y0_R49, DC1, PHI1, IR7, DC0,
IOWR, D39Y, D39_MEMCYC, BA11, PHI2TTL, FDC_DRQ, D34_SIG, FDC_DDEN, D40Q1_D39,
D99_C1_TIMING, RESET, OSC, DBIN, TIMING_TAG17, CLK_123M, CAS, FDC_STEP_TO_D100,
AVDC, KBD_K0, VID_CPU_SEL, VA11, FDC_PRECOMP_WRDATA, IORC_N, MRC_N,
D98_Y3_S1_2, S3_3, RAIL13, D39_MEMCYC, D105_WAIT_STAGE, VIDEO_OUT, RAIL12,
SOUND_CLAMP, D94_D1_D99_A2N, RAIL14, SND_BASE, D30B_D_PRE_N,
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
ROM_CS_4000, S_TTL_D3, S3_4, KBD_SC1, D105_10_H, MA4, D13_4_D105_2, KBD_SC2,
FDC_WE_N, SER_TXD_INV, CLK_123M, OSC_PRE, KBD_SC3, IOWR, PHI1_D35,
D97_C2_C19_R86_TARGET, PHI2_D35, CAS, BA14, BA13, DB6, DB7, SER_TXD, RAIL14,
S_SIN, DB2, SER_RTS, D40QA, FDC_RAW_READ, ROM_CS_D16, D56_QN_D34, D56_Q2_D34,
DB0, DB4, DB1, X2_PC1, LATCH_B, X2_PC2, X2_PC3, X2_PB0, X2_PB1, X2_PB2, BA11,
VA5, FDC_RCLK, BA5, DB3, PRECOMP_TAP_2, S3_2, D40Q2_D33, BA2, BA3, X4_DSEL0_N,
BA1, CS_D10, BA10, VA6, VA7, BA9, VA10, IOM_N, VA15, MWC_N, INHIB_N, BA6,
BA15, D94_A4_D101_Q0, BA13, CS_D11, CS_D27, IOWC_N, AMWC_N, MEMR, BA12,
X2_IRQ0, IORC_N, P12V, D6_V_ENABLE, DBIN_GATED, SYNC, D25_T, FRAME_INT, BA7,
OSC, VIDEO_OUT, XTAL16M, VID_MIX1, E2_COM, INTA, IOWR, FDC_DDEN,
D30_Q2N_D29_AIN7, FDC_DRIVE_SIZE_5_8, WREQ_N, PIT_BAUD, ROE, STSTB_D38, CTR_LD,
RAM_OUT_EN, MA2, MA1, S3_5, DB7, MEMR, BA9, BA1, D3_O4_D6_A6, E3_COM, INTR, RES_RC, D13_4_D105_2, D105_10_H, CS_D54, FDC_DSEL_IN, FDC_MOTOR_EN, FDC_SIDE_SEL, INT6_RAW, DB4, and VA14 then
each pass an independent uncapped check, reducing the exact count to 9; those
routes are promoted. The last six hundred sixty-four are
selected transactionally by
`close_unconnected_gaps_uncapped.py`, which continues past capped-only or
DRC-regressing candidates. Its conservative multilayer search is exhausted
through 260 mm, beyond the 252.637 mm maximum residual candidate, so all
distance-ranked gaps have now been attempted in that mode. Its standard
front/back A* search is exhausted with
no accepted route across 48.43–50, 65–70, 75–80, and the tested bands from 90
through 130 mm. The exact board/DRC hashes, search ceiling, exhausted ranges,
parameters, and tool hashes are guarded in
`ref/routing/current-source-uncapped-prune.json`.
The following rule-accurate multilayer phase uses 0.21 mm clearance against
the board's 0.20 mm rule and a 0.25 mm lattice, retaining only complete KiCad
DRC-neutral improvements. Uncapped sweeps exhaust all remaining distance-ranked
candidates through 260 mm, beyond the 252.637 mm maximum residual candidate, so
every distance-ranked gap has been attempted in that mode.
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
respectively, exceeding the guarded twenty-item limit. No failed transaction
is promoted; these nets require wider topology changes or net-specific routing
methods.
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
A widened 46-conflict CS_D57 transaction restores sixteen affected nets and
temporarily exposes PROM_EN as a DRC-neutral equal-open swap. After 23 safe
non-source orphan items are pruned, a `(0.075,0.075)` mm phased PROM_EN route
removes eight conflicts and restores BA10, BA12, BA5, GND, IORD, and
ROM_CS_4000. The resulting six-open board has 26,570 routed items, no missing
source copper, no electrical or dangling finding, and the same 710 cosmetic
reports. Exact hashes and transaction evidence are in
`ref/routing/current6-residual-topology.json`; cumulative promoted closures are
now 671.
On that new topology CS_D55 needs only 39 removable conflicts. A
`(0.025,0.1)` mm target phase restores twenty-one affected nets and temporarily
exposes DB5. After 30 safe orphan items are pruned, a `(0.05,0.075)` mm DB5
route removes one IORD conflict; IORD restores and 94 additional obsolete
non-source items are pruned. The resulting five-open board has 27,050 routed
items, no missing source copper, no electrical or dangling findings, and the
same 710 cosmetic reports. Exact evidence is in
`ref/routing/current5-residual-topology.json`; cumulative promoted closures are
now 672.
On the five-open topology a four-phase IOWR_RAW_N sweep finds a 33-conflict
route at `(0.1,0.025)` mm. The legal target route and all thirteen displaced
nets now restore, and two new non-source orphan items are pruned. The resulting
four-open board has 27,281 routed items, no missing source copper, no electrical
or dangling findings, and the same 710 cosmetic reports. Exact evidence is in
`ref/routing/current4-residual-topology.json`; cumulative promoted closures are
now 673.
The new bus topology gives formerly pathless INT7_RAW a 32-conflict route on
the 0.10 mm lattice. All seventeen displaced nets restore, and eight new
non-source orphan items are pruned. The resulting three-open board has 27,765
routed items, no missing source copper, no electrical or dangling findings,
and the same 710 cosmetic reports. Exact evidence is in
`ref/routing/current3-residual-topology.json`; cumulative promoted closures are
now 674.
A widened D94_D0_BOUNDARY transaction next removes 66 non-source conflicts on
the 0.10 mm lattice. After restoring the affected topology and pruning 15 safe
orphan items, independent KiCad 9.0.8 DRC reports only D3_O6_D6_A5 and
ROM_CS_EXP18 open. The resulting two-open board has 28,123 routed items across
409 nets, no electrical or dangling findings, and the unchanged 710 cosmetic
reports. Exact evidence is in `ref/routing/current2-residual-topology.json`;
cumulative promoted closures are now 675.
A D3_O6_D6_A5 equal-open swap followed by a `(0.025,0.075)` mm MEMW transaction
and a 2.06 mm ROE endpoint bridge reduces the source-preserving frontier to one
open. Independent KiCad 9.0.8 DRC reports only ROM_CS_EXP18 unconnected. The
board has 28,612 routed items across 410 nets, no electrical or dangling
findings, and the unchanged 710 cosmetic reports. Exact evidence is in
`ref/routing/current1-residual-topology.json`; cumulative promoted closures are
now 676.
The formerly final ROM_CS_EXP18 gap is also closed in a guarded recovery
checkpoint. Two legal DIP breakouts and a zero-fixed 32-conflict phased
transaction close ROM_CS_EXP18; a second transaction closes the displaced
ROM_SEL branch. Stable KiCad DRC leaves only BA2, BA14, and BA15 open, with no
electrical or dangling findings. Exact recovery hashes and parameters are in
`ref/routing/rom-closed-recovery-checkpoint.json`.
The next bounded cleanup closes BA14 without reopening either ROM net. A
retained 0.0875 mm diagnostic route identifies the D8.5 pad channel; its layer
transition is moved to `(83.25,110.25)` mm, and seven ROM_SEL elbow items are
collapsed to a single real gap. The guarded 0.10 mm closer then accepts a new
7.666 mm ROM_SEL route. Independent stable KiCad 9.0.8 DRC reports only BA2
and BA15 open, 28,953 routed items across 411 nets, no electrical or dangling
findings, and the unchanged 710 cosmetic reports. Exact evidence is in
`ref/routing/rom-closed-two-residual-checkpoint.json`.

### Additive/rename-safe copper migration

Exact whole-net equality is still the default. The optional
`--allow-additive-renames` mode admits one additional mechanically proved
case: every old endpoint must still exist at the exact integer-nanometre pad
coordinate, every endpoint must map to one current net, and the old endpoint
set must be a subset of that current net. This permits copper to survive a
pure endpoint addition or merge/rename, while splits, removed endpoints, and
any moved pad remain quarantined. Copied items are relabeled to the current net
before duplicate detection.

Against the preserved zero-open candidate, the current source proves 28 such
maps; five carry copper. The unfiltered pass retains 588 more track/via items
than exact equality alone. As with every refresh, newly placed footprints can
still collide with otherwise valid old copper, so the first DRC must be fed
back through `--exclude-drc`. After that existing guard quarantines 27
DRC-implicated nets, the additive result retains 2,656 copper items and has
1,445 uncapped connectivity gaps, versus 2,634 items and 1,449 gaps for the
same exclusion under exact equality. Both cleaned candidates have zero shorts,
copper-clearance, crossing, hole-clearance, hole-to-hole, dangling, or
copper-to-edge findings. This closes four current-source gaps without relaxing
the DRC invariant; neither temporary board is a fabrication deliverable.

The experiment is reproducible without modifying a tracked PCB:

```sh
/usr/bin/python3 kicad/refresh_routed_from_source.py \
  --routed kicad/juku_routed_candidate.kicad_pcb \
  --allow-additive-renames \
  --output /tmp/juku-additive-refresh.kicad_pcb
"$(scripts/find-kicad-cli.sh)" pcb drc --format json \
  --output /tmp/juku-additive-refresh-drc.json \
  /tmp/juku-additive-refresh.kicad_pcb
/usr/bin/python3 kicad/refresh_routed_from_source.py \
  --routed kicad/juku_routed_candidate.kicad_pcb \
  --allow-additive-renames \
  --exclude-drc /tmp/juku-additive-refresh-drc.json \
  --output /tmp/juku-additive-refresh-clean.kicad_pcb
```

### Item-level DRC salvage

Whole-net quarantine is deliberately conservative: a single moved endpoint
discarded every old branch on that net. The optional
`--allow-drc-salvage` refresh mode instead emits an intentionally unsafe
source-based trial containing all same-name old copper plus the proved
additive/rename maps. `kicad/salvage_routed_copper.py` then owns the safety
transaction. It identifies migrated items only by UUID absence from the
authoritative source PCB, removes only migrated tracks/vias named by current
KiCad short, clearance, crossing, hole, or edge findings, and reruns DRC after
each batch. Source-owned copper is never eligible for removal.

The current raw trial copies 18,078 items on 351 nets and appears to have only
274 connectivity gaps, but it is invalid because old corridors cross moved
parts. One DRC-owned cleanup round removes 496 implicated items, retains
17,582, and exposes the honest 433-gap topology with zero short, clearance,
crossing, hole-clearance, hole-to-hole, or copper-to-edge findings. KiCad also
reports 199 track-dangling and 52 via-dangling findings. Those tails are kept
as explicit reconnection work: a test prune exposed the expected recursive
chain and was stopped rather than deleting otherwise useful routes before
their new endpoints are joined.

The first nineteen bounded multilayer A* transactions accepted 263 legal repairs. They
close GND/P5V branches plus MEMW/MEMR, D94 D0, memory-mode, W10 select,
rail-13/14, AMW, D39 memory-cycle/Y, REV, D105 WAIT, D42 Q, IORD, FDC `/WE`,
FRAME_INT, PHI2TTL, RAS, address/video-address branches, VIDEO_OUT/mix/mux,
RAM_OUT_EN, S_TTL, CAS, sound, serial-baud, ROM/expansion-select, INTA, HLDA,
VT2 base, and related gaps. The resulting temporary board has all 303 source
footprints and all 2,395 current
source pad identities, nets, and integer-nanometre coordinates, 21,427 copper
items, and 164 uncapped connectivity gaps. An independent KiCad DRC still
has zero short,
clearance, crossing, hole-clearance, hole-to-hole, or copper-to-edge findings;
it reports 199 track-dangling and 51 via-dangling tails. This is a much closer
current-source route, but its opens and retained tails keep it outside tracked
fabrication artifacts.

The earlier sweeps used a deliberately conservative 0.45 mm proposal clearance.
KiCad's actual board rules admit proposals made with 0.21 mm clearance. Targeted
INTR, PROM_EN, and CS_D54 closure first reduced the board from 164 to 157 gaps;
a full-distance 0.10 mm-grid sweep at the legal clearance then accepted 111
more routes and reached 46. Retrying BA13 after those additive changes found a
different clean path and established the 45-gap boundary. At that checkpoint
the guarded routing work had accepted 382 repairs and the temporary board
contains 29,009 copper items. It retains all 303 source footprints and exact
identity, net, and integer-nanometre coordinate parity for all 2,395 pads.
Independent KiCad DRC reports 45 uncapped opens, 199 track-dangling and 47
via-dangling tails, and zero short, clearance, crossing, hole-clearance,
hole-to-hole, or copper-to-edge findings.

`close_gap_by_ripup.py` generalizes the successful INTR transaction. A
diagnostic proposal identifies only pre-existing, non-source tracks or vias
that KiCad names as direct blockers of the new route. Source copper, pads,
edges, target-net items, and ambiguous blockers fail closed by default. The
opt-in mixed-blocker mode still never removes those fixed items: it tries only
the bounded removable subset and relies on the same final publication gates.
Affected-net restoration can try several explicit grid phases. The tool routes
the target at the final clearance, restores every affected net, and normally
writes an output only when total opens fall, the selected gap disappears, no
electrical blocker remains, and no DRC category increases. A separate opt-in
permits an equal-open, DRC-neutral topology swap for subsequent guarded sweeps;
it never permits an open-count increase. If displaced copper leaves a
pre-existing migrated via newly dangling, the transaction removes that via
only when it belongs to an affected net and is absent from source copper; the
ordinary open-count and whole-DRC gates then re-evaluate the cleaned board.
`--transaction-board` and `--transaction-report` can retain the restored
pre-acceptance artifacts when a final gate rejects them. INTR required one BA5
item to be replaced; PROM_EN, CS_D54, and BA13 proved clean-path cases through
the same guarded interface. `--restore-net-priority` permits reproducible order
experiments for constrained affected nets. Completed intermediate boards are
discarded as soon as their successor is verified, keeping large transactions
at constant scratch-board storage rather than one full board per grid attempt.
`--diagnose-only` records the complete removable/fixed blocker classification
and affected-net set without removing copper or writing a candidate board.
`--gap-report` can select the proposal endpoints from a retained DRC report
when different KiCad builds choose different representative marker pairs for
the same disconnected net islands. A fresh live DRC still supplies all counts
and publication gates. Target closure is proved by a decrease in the live
target-net gap count, not merely by disappearance of one coordinate pair.

`close_unconnected_gaps.py --attempted-state` canonicalizes endpoint order and
atomically records outcomes. State remains bound to the exact SHA-256 of the
additive board lineage, proposal parameters, and both routing-script hashes, so
a different board, configuration, or implementation fails closed. Schema 3
fixes one important monotonicity distinction: a proven A* no-path remains valid
when this workflow only adds obstacles, but a DRC-rejected path or timeout does
not. After every acceptance those geometry-dependent outcomes are invalidated,
allowing later copper to force a different legal route. A fresh full-distance
0.10 mm-grid/0.21 mm-clearance pass records all 45 residual gaps as proven
router no-path cases and accepts none. The earlier wrong-lineage guard remains
enforced.

The exact board rule is 0.20 mm, so a guarded follow-up tested that clearance
without weakening the KiCad acceptance invariant. A 0.10 mm lattice closes
IOWR, D40QA, VA10, BA1, and D105_10_H. Different grid phases are materially
distinct searches: 0.125 mm closes the first ROE gap; 0.15 mm closes VA12, the
second ROE gap, and DBIN_GATED; 0.175 mm closes CS_D55; and 0.1375 mm closes
D6_A7_D105_I1_BOUNDARY. The 0.20, 0.225, 0.25, and 0.30 mm lattices add no
routes, and a final full-distance 0.1125 mm sweep records all 34 residual gaps
without another acceptance. That checkpoint contains 393 repairs, 30,334
copper items, and 34 uncapped opens. Exact footprint/pad parity and every
electrical DRC invariant remain unchanged; the dangling counts stay at 199
tracks and 47 vias.

Four further exact-clearance phases (0.12, 0.13, 0.14, and 0.16 mm) each
exhaust all 34 signatures without acceptance. Increasing the search margin from
60 to 100 mm also finds no legal detour for DB7, BA5, VA6, MA1, CS_D11, or MA6.
Guarded 0.15 mm diagnostics do find geometric paths for many other residuals,
but their direct blockers include fixed source pads—for example the D35/D53
cluster on PHI1_D35 and PHI2_D35, the D44/R42/R43 cluster on S3_1, D50 on
VA9/VA15, D5 on DC2/DC7/WR, and D3/D6/D12 on the long PROM-boundary nets.
Those are not eligible for copper rip-up. IORD, CS_D10, MEMR, and W10_QA_SEL_D50
still have no path even at the diagnostic clearance. This establishes that the
next useful automatic step needs topology-aware displacement around fixed-pad
rows, not more blind lattice enumeration. `close_gap_by_ripup.py
--diagnostic-report` retains the proposal's complete KiCad DRC JSON even when
the guarded transaction fails, so future blocker classification remains
machine-auditable instead of depending on terminal output.

The mixed-blocker follow-up first exercises a conservative equal-open S3_1
swap: the fixed D44/R42/R43 pads remain untouched, the selected S3_1 gap
disappears, and the replacement VA4 gap keeps the count at 34. Fresh 0.10 and
0.15 mm sweeps accept nothing from that topology, so it is not adopted. BA0 is
productive. Its diagnostic path also touches fixed D44/R40/R41/R44 pads, but the
transaction removes only ten named migrated-copper items across BA13, BA5,
GND, RAIL_H, VA1, VA4, VA7, and VA9. Restoration on 0.10 and 0.15 mm phases
closes BA0 while leaving 33 opens. Independent KiCad DRC reports 199
track-dangling and 47 via-dangling tails and zero short, clearance, crossing,
hole-clearance, hole-to-hole, or copper-to-edge findings. The resulting board
has 30,418 copper items and exact 303-footprint/2,395-pad identity, net, and
integer-coordinate parity with the source. The cumulative guarded result is
394 repairs and 33 uncapped opens. Fresh full-distance 0.10 and 0.15 mm sweeps
of that improved lineage exhaust all 33 signatures without another acceptance.

The next mixed transactions make three more net improvements. E3_COM removes
six migrated blockers while retaining the fixed R53/D53 ground pads, then
restores CTR_LD, E2_COM, GND, and VID_CPU_SEL to reach 32 opens and 30,578
copper items. DB7 removes fourteen migrated blockers while retaining D9.1,
restores BA10, BA5, CS_D27, CS_D54, and both CS_D55 branches. Its displaced
obsolete intermediate CS_D57 island disappears, leaving one honest D9.9-to-track
gap instead of the earlier two island-mediated findings, and the board reaches
30 opens. Two pre-existing vias on BA5 and CS_D55 become newly dangling only
because their adjacent migrated tracks were displaced; the transaction-owned
cleanup removes those two vias, returning the whole-board count from 49 to the
47-via baseline. Independent KiCad DRC reports the unchanged 199 track-dangling
tails and zero electrical blockers. The resulting board has 30,671 copper
items, exact 303-footprint/2,395-pad source parity, and a cumulative 397 guarded
repairs. Fresh full-distance 0.10, 0.125, 0.1375, and 0.15 mm sweeps exhaust all
30 signatures without acceptance. The 0.125 mm phase does geometrically propose
D26_PC0_D3_I5, but KiCad rejects it for three added clearance findings. A
separate 0.15 mm CS_D57 diagnostic needs 25 migrated blockers, beyond the
bounded 20-item transaction limit; the remaining honest gap is not disturbed.

Raising the diagnostic bound only for classified follow-up exhausts the next
three candidates without weakening publication. DC4's 21-item and VA15's
28-item removable sets still leave their selected target gaps after displacement,
proving fixed-corridor failures. CS_D57's 25-item set does permit a legal target
route, but alphabetical restoration finishes at 33 opens. Order experiments
explain the deficit: D25_T-first restores both of its formerly impossible
branches but blocks AMW_N; AMW_N-then-D25_T preserves those three closures but
uses the only CS_D55 corridor. Neither order can beat the independently verified
30-open board, so no exploratory candidate is published. The first full probe
also exposed why retaining every intermediate is unsustainable; sequential
discard now holds the same transaction to about 33 MB of scratch data instead
of hundreds of megabytes and avoids KiCad lock/report failures at the `/tmp`
quota.

The read-only classifier next surveys the remaining exact-clearance failures.
It finds bounded sets on CS_D11 (18 items), both VA13 gaps (19 and 18), VA9
(18), WR (18), and CS_D26 (17), while MA6 and MA7 require 36 and 47 items. Full
CS_D11 restoration ends at 33 opens and the short VA13 target remains blocked
after displacement. CS_D26 is the useful topology: its 17-item transaction
retains fixed D26.38, closes the 69.638 mm target, restores thirteen affected
nets, and ends as a DRC-neutral 30-open swap whose lone replacement is
D53_Y2_R51. That 7.517 mm replacement has exactly one removable CS_D26 blocker.
A second guarded transaction routes it and restores the short CS_D26 branch,
reaching 29 opens. Independent stable KiCad DRC reports the unchanged 199
track-dangling and 47 via-dangling counts and zero electrical blockers. The
board has 30,949 copper items, exact 303-footprint/2,395-pad source parity, and
a cumulative 398 guarded repairs. Fresh full-distance 0.10, 0.125, 0.1375, and
0.15 mm sweeps exhaust all 29 signatures without another acceptance; the
0.125 mm D26_PC0_D3_I5 proposal remains rejected by three added clearance
findings.

BA2 then exposes a productive composite topology that requires a deliberately
retained intermediate rather than publishing its first one-open regression.
Stable KiCad DRC selects the 36.389 mm BA2 track-to-via marker reproducibly;
nightly DRC can instead choose a 43.805 mm track-to-track marker for the same
disconnected islands. The first transaction closes BA2 but temporarily exposes
BA0 and VA8 and therefore retains, but does not publish, a DRC-neutral 30-open
board. A six-item VA8 transaction restores BA2, BA3, and GND and returns to 29.
A five-item BA0 equal swap restores VA1, VA5, VA0, and RAIL_H in constrained
order, leaving one 14.970 mm VA8 replacement. Matching both the diagnostic and
target lattice at 0.15 mm finds a four-item path for that final replacement;
S3_3, VID_CPU_SEL, and P5V all restore, and one newly orphaned migrated
VID_CPU_SEL via is removed under the existing whole-board gate. The resulting
board reaches 28 opens with 31,637 copper items. Independent stable KiCad DRC
reports 199 track-dangling and 46 via-dangling findings and zero short,
clearance, crossing, hole, or edge blockers. Exact parity holds for all 303
source footprints and 2,395 pads. Its SHA256 is
`e04c9ac76b87cfb12af5deea4da25cb4cedb02cb1abfb57430f595ab92de9dcf`.
A fresh 0.10 mm-grid, 100 mm-margin sweep exhausts all 28 residuals without an
acceptance; D26_PC0_D3_I5 produces seven added clearance findings and is
rejected.

Those seven D26_PC0_D3_I5 findings are a quantization boundary, not an occupied
corridor. The 0.20 mm-clearance proposal has no removable copper conflicts and
misses only four fixed pads: D93.14, D34.7, D101.1, and R63.1. KiCad measures its
clearances at 0.1962–0.1980 mm against the 0.2000 mm rule. Raising only the
router's proposal margin to 0.205 mm forces a different 163-segment/17-via path;
the diagnostic then has zero removable and zero fixed blockers. The ordinary
transaction publishes that path with no rip-up or restoration and reaches 27
opens. Independent stable KiCad DRC reports the unchanged 199 track-dangling
and 46 via-dangling findings and zero short, clearance, crossing, hole, or edge
blockers. Exact parity still holds for 303 footprints and 2,395 pads; the board
has 31,817 copper items and SHA256
`20c409f1aaf5f144b31071673ec06640664f9207264ae5eb8891fdb9db0bdc62`.
Fresh endpoint-correct 0.10, 0.125, 0.1375, and 0.15 mm-grid, 100 mm-margin
sweeps exhaust all 27 remaining signatures without additive acceptance. The
next smallest bounded mixed candidate, VA6, removes 13 migrated items across
BA10, MA4, MA7, VA1, VA14, VA15, and VA8, but the target still cannot route
through fixed D51.5/.6/.7 pads; that failed topology is not adopted.

The endpoint correction nevertheless changes displaced-net restoration. A
0.10 mm-clearance MA1 diagnostic identifies a bounded set of 14 migrated items
across MA0, MA2, VA10, VA11, VA2, VID_MUX_G, and W10_QA_SEL while retaining the
fixed D50 pad corridor. The guarded mixed-blocker transaction closes MA1 at the
real 15.533 mm endpoint pair. Endpoint-correct recovery restores both
VID_MUX_G branches, VA10's same-coordinate layer join, both VA11 branches, one
MA0 branch, and then the formerly trapped 4.457 mm MA0 branch on the 0.1375 mm
lattice. MA2 restores last, turning the old equal-open topology experiment into
a real 27-to-26 improvement; one transaction-orphaned migrated via is removed.
A fresh 0.125 mm exact-clearance sweep then closes MA6 and reaches 25 opens.
The other 0.10, 0.1375, and 0.15 mm phases accept nothing, and the accepted
0.125 mm pass exhausts every remaining signature after MA6.

Independent stable KiCad DRC on that 25-open board reports the unchanged 199
track-dangling and 46 via-dangling findings and zero short, clearance, crossing,
hole, or edge blockers. Exact identity, net, and coordinate parity holds for
all 303 footprints and 2,395 pads. The board contains 31,992 copper items, is
10,982,923 bytes, and has SHA256
`b0de0b804af22c71c50d790fa29ca2b4ed3ba218956403babf6529193530870b`.

Endpoint-correct blocker ranking after that checkpoint rules out the next
shortest options without mutating it. MA7's 0.10 mm diagnostic needs 54
migrated items across 30 nets and still names ten fixed blockers. BA5 has no
multilayer path even at 0.10 mm clearance. VA15 finds 19 removable items across
BA3, P5V, VA7, and VID_MUX_G, but after their removal the legal-clearance target
router still cannot pass fixed D51.12, E14.2, and R45.2. MEMW_D7P2 requires 38
items across thirteen nets plus five fixed findings.

VA13 is smaller but not competitive. Its first 14.295 mm branch closes after a
17-item displacement across CAS, GND, MA1, MA2, VA11, VA3, and W10_QA_SEL.
Restoring W10/VA11 first ends at 27 opens because two MA1 layer joins and one
VA3 branch remain. Restoring MA1 first proves the stronger blocker: the VA13
route creates two same-coordinate MA1 joins for which no legal via position
exists even before the other displaced nets return. Closing one VA13 open while
creating those two MA1 opens has a theoretical 26-open floor, so no remaining
restore order can beat 25; the transaction is discarded.

The adjacent decoder/control survey likewise preserves the checkpoint. CS_D10,
IORD, and W10_QA_SEL_D50 have no path even at 0.10 mm diagnostic clearance.
CS_D11 finds 18 removable items across nine nets, but its 0.20 mm target route
still adds one clearance finding against fixed D9.6; a 0.205 mm proposal margin
finds no path. S3_1 needs 13 items and five fixed findings. PHI1_D35 needs eight
items but retains six fixed D35/R39/W14 findings.

PHI2_D35 reveals a distinct lattice-phase boundary. Its minimal 0.10 mm
diagnostic identifies nine migrated blockers across D36_D33, GND, P5V, PHI1,
PHI2TTL, RAM_RD_OE, and VID_MIX1. The 0.10 mm legal target misses D35.2 by only
2.5 µm, while 0.2025--0.205 mm proposal margins and the 0.125 mm lattice find
no path. The 0.1375 mm lattice instead produces a clean legal route. The
transaction wrapper therefore now accepts `--diagnostic-grid-step` separately
from the target `--grid-step`; omitting it preserves the prior behavior. Both
lattice values are recorded in diagnostic and accepted-transaction summaries.

The split-grid transaction closes PHI2_D35 and restores the displaced nets but
leaves one 4.667 mm D36_D33 replacement, so it is a guarded 25-open topology
swap rather than an improvement. A second 16-item transaction cleanly closes
D36_D33 and restores PHI2_D35, PHI2TTL, both VID_MIX1 branches, CAS_PRE,
TIMING_TAG17, and the ground branches. POF remains unroutable at 4.243 mm and
P5V at 9.211 mm on all four tested phases. Restoring P5V before or after
POF/TIMING/GND does not change those results; the chain has a 26-open floor and
is discarded. The independently verified 25-open board remains authoritative
at that stage.

The next left-edge decoder ranking finds four under-clearance topologies. DC4
needs 24 migrated items across thirteen nets and retains fixed D1/D5 pads. DC2
needs 16 items across eight nets and fixed D5 pads. CS_D57 has no fixed blocker
but needs 27 items across fourteen nets. DC7 is the useful bounded candidate:
its 0.10 mm diagnostic names only eight migrated items across DB1, DC0, DC5,
DC6, and ROE, plus fixed IORD pad D5.25. After those removals, legal DC7 target
routes are independently clean on the 0.10, 0.125, and 0.15 mm lattices; the
0.1375 mm phase is rejected for one clearance finding.

Restore order is decisive. Recovering DC0 before DC5 closes two DC5 branches
but leaves one 3.536 mm DC5 replacement, producing only a DRC-neutral DC7/DC5
swap. Recovering DC5 first closes its 2.828, 3.536, and 9.190 mm branches before
DC0 occupies the corridor. DC0 then restores at 22.521 mm, DB1 gains its
same-coordinate layer join, and ROE restores on the 0.125 mm phase. The guarded
transaction closes DC7 and reduces the board from 25 to 24 opens. It removes
two transaction-orphaned migrated vias.

Independent stable KiCad DRC on the 24-open checkpoint reports 199
track-dangling and 45 via-dangling findings and zero short, clearance, crossing,
hole, or edge blockers. Exact identity, net, and coordinate parity holds for
all 303 footprints and 2,395 pads. The board contains 32,167 copper items, is
11,007,712 bytes, and has SHA256
`054ded89f7524bbbc23190d1d279b9b1e858ec71b565605ca79424d118e77a81`.
Fresh full-distance 0.10, 0.125, 0.1375, and 0.15 mm exact-clearance sweeps each
exhaust all 24 residual signatures without acceptance.

Re-running the left-edge diagnosis on that accepted topology changes DC2's
corridor: its 0.10 mm diagnostic now names 25 removable items across A10, DB0,
DB1, DC3, DC5, HLDA, INTA, and MEMW, while touching fixed D5.11/DB6 and
D5.18/DB0 pads. Removing only those derived items permits independently clean
0.20 mm-clearance DC2 routes on the 0.10, 0.125, and 0.15 mm phases; the
0.1375 mm proposal is rejected for one clearance finding. Restore order is
again decisive. DB0-first restoration recovers every other displaced branch
but leaves a 19.377 mm A10 replacement, making a 24-for-24 swap. Restoring A10
first, then DB0, MEMW, DC3, HLDA, DB1, DC5, and INTA, reconnects every branch
and yields a guarded 24-to-23 improvement. Three transaction-orphaned migrated
vias are removed.

Independent stable KiCad DRC on the 23-open checkpoint reports the unchanged
199 track-dangling and 45 via-dangling findings and zero short, clearance,
crossing, hole, or edge blockers. Exact identity, net, and coordinate parity
holds for all 303 footprints and 2,395 pads. The board contains 32,475 copper
items, is 11,051,620 bytes, and has SHA256
`3dc2475580ce6217ad84484146d353a30b12237a5c4def2dbb40872ef763d37c`.
Fresh full-distance 0.10, 0.125, 0.1375, and 0.15 mm exact-clearance sweeps each
exhaust all 23 residual signatures without acceptance.

A fresh 0.1125 mm lattice with 100 mm search margin now exhausts the same exact
23-open lineage too: 21 signatures produce a proved router no-path and VA6 plus
CS_D11 reach the guarded 60-second timeout, with zero accepted routes. A
route-specific CS_D11 diagnostic on that lattice finds a 71-item geometric
proposal and 30 removable migrated-copper blockers across twelve nets. The
mixed transaction removes only those eligible items and retains the fixed
D9.12/CS_D27 and D9.6/V3_RC pads, but the target-net gap count still does not
decrease, so no candidate is published. The exact board/tool hashes, phase,
net census, and result are preserved in
`ref/routing/current23-grid01125-exhaustion.json`.

The next route-specific survey is run on that exact 23-open topology. MEMR has
no 0.10 mm diagnostic path. CS_D57's under-clearance proposal now names 33
removable items across fourteen nets and no fixed blocker. DC4 names 28 items
across thirteen nets plus fixed D5.18/DB0, D5.19/DC0, D1.4/DC5, and D1.5/DC6
pads; legal 0.20 mm-clearance target routes exist on the 0.10 and 0.125 mm
phases. Restoring DC2 first and HLDA late ends at 24 opens with GND and HLDA
replacements. Restoring HLDA first reconnects every displaced branch except a
14.080 mm GND gap, yielding a guarded 23-for-23 DC4/GND swap.

The chained GND diagnostic names 26 items on only DC1, DC2, DC4, DC5, and
MEMW, with no fixed blocker. Legal GND target routes exist on the 0.10, 0.125,
and 0.1375 mm phases. All tested target geometries restore the middle 5.657 mm
MEMW branch but cannot route its 0.510 or 36.009 mm replacements on the four
standard restoration phases. Even assuming every other displaced net restores,
the chain therefore has a 24-open floor and the equal swap is discarded.

VA9's 0.10 mm diagnostic names 27 removable items across BA0, BA10, BA13,
BA14, P5V, RAIL_H, S3_6, VA11, VA12, VA13, VA7, and VID_MUX_G, plus fixed
R41.1/S3_2 and D50.14/VA1 pads. Its 0.125 and 0.1375 mm target phases are
independently legal; the 0.10 and 0.15 mm proposals add clearance findings.
Restoring P5V first recovers all three power branches, all four VID_MUX_G
branches, and the remaining routable nets, but leaves two BA10 replacements
(a same-coordinate join and 10.607 mm branch), BA13 at 8.078 mm, and VA12 at
28.507 mm. Those four gaps also have no route when attempted immediately after
either legal VA9 target topology on the tested restoration phases. The complete
transaction ends at 26 opens, so VA9 is likewise rejected and the 23-open
checkpoint remains authoritative.

The next long-net survey ranks WR at 27 removable items across sixteen nets,
D6_V_ENABLE at 31 across sixteen, D3_O6_D6_A5 at 57 across twenty-seven, and
RAM_OUT_EN at 65 across nineteen. WR's diagnostic also touches D1.16, D1.32/A6,
and D4.8/A8. Legal WR targets exist on the 0.125 and 0.1375 mm phases; the 0.10
and 0.15 mm proposals add two and four clearance findings respectively. Both
legal geometries immediately expose the same 1.980 mm STSTB_D38 replacement,
which has no route on any of the four standard phases even when attempted
before every other restoration. WR therefore has an optimistic 23-open
equal-swap floor and is not adopted.

D6_V_ENABLE's diagnostic touches fixed R5.1/P5V,
D6.15/D6_A7_D105_I1_BOUNDARY, R6.2/READY_D, and D4.8/A8 pads. Its 0.10 and
0.125 mm target phases are legal. A guarded BA15-first transaction restores
BA15 at 8.485 mm on the 0.10 phase and at 6.021 mm on the 0.15 phase, both P5V
branches, all three BA0 branches, GND, BA1, A7, and D13_4_D105_2. BA2 at
24.520 mm and DBIN at 3.592 mm have no route on any standard phase. Even
assuming every later net restores, those two replacements give the chain a
24-open floor, so the transaction is stopped without publication.

The D3_O6_D6_A5 diagnostic additionally retains fixed D3.10/S_TTL_D3,
D12.7, and W20.2/S_TTL_D3 geometry. RAM_OUT_EN retains eleven named fixed pads
across R53, C21, D52, D37, E2, D35, D47, and D53. Their 57- and 65-item
displacements are therefore recorded but not attempted. The independently
verified 23-open checkpoint remains authoritative.

The previously unsurveyed companion PROM-address net `D3_O4_D6_A6` is now
classified on that same checkpoint. Its 173.442 mm diagnostic route names 55
removable migrated items across 27 nets and the fixed D3.14/P5V pad. After
removing only those migrated items, exact-clearance target attempts on the
0.10 and 0.125 mm phases remain DRC-rejected by four and two clearance
findings respectively; the 0.1375 mm phase legally closes the target. The
guarded restoration then reconnects BA1, BA12, BA6, both BA7 branches, three
CS_D55 branches, and one CS_D11 branch, but the remaining CS_D11 branch and
same-coordinate CS_D55 join each fail all four 0.10/0.125/0.1375/0.15 mm
phases. Even assuming every later displaced net restores, those two
replacements give the chain a 24-open floor. The transaction was stopped and
no candidate was published; the verified 23-open checkpoint remains
authoritative.

Two further exact-clearance lattice phases now close the remaining untested
spacing around the productive phase family without changing that checkpoint.
On the exact SHA256 `3dc247...37c` 23-open board, a 0.1625 mm/100 mm-margin
sweep proves router no-path for all 23 selected gaps. The much finer 0.0875 mm
phase proves no-path for PHI1_D35 and DC4 and reaches its explicit 45-second
cap on the other 21; those timeouts are not promoted to no-path claims. Both
output boards are byte-identical to the input, so neither phase found an
additive route. KiCad selected alternate all-layer versus B.Cu endpoint
markers at the same S3_1 coordinate between the two DRC runs; attempted-state
inheritance therefore remains phase-local. Exact configuration, tool hashes,
outcome counts, and that marker boundary are guarded in
`ref/routing/current23-grid-edge-phase-exhaustion.json`.

The remaining no-fixed-blocker candidate `CS_D57` is now transactionally
exhausted as well. Its 0.10 mm diagnostic route crosses 33 removable migrated
items on fourteen nets and no fixed pads. Exact-clearance targets at 0.10,
0.125, and 0.15 mm are rejected by four, two, and one new clearance findings;
only the 0.1375 mm target is legal. Sorted restoration returns fifteen of the
nineteen rip-up-created opens and finishes at 26. Restoring the failed
CS_D55/GND/ROE/SYNC group first recovers the same group but loses one DB5
branch and finishes at 27. The retained priority-run DRC has zero short,
clearance, crossing, hole, or edge blockers. Both orders are worse than 23,
so neither topology is adopted. Exact phase results, transaction hashes, DRC
counts, and tool hashes are guarded in
`ref/routing/current23-cs-d57-transaction.json`.

The next guarded cleanup attacks obstruction rather than another route lattice.
All 244 dangling findings on the exact 23-gap checkpoint belong to migrated
copper; none of their UUIDs exists in the source PCB. `prune_dangling_tracks.py`
now supports nonzero-open boards only when every deletion is non-source copper,
the open count never rises, no electrical DRC category appears, and no other
DRC category grows. Its chunked mode tries large deletion sets first and halves
only after rejection, retaining the same item-by-item proof at a batch size of
one. A bounded 641-item transaction removes dead chains, reduces track-dangling
findings from 199 to 87 and via-dangling findings from 45 to 11, and collapses
one obsolete MEMR island plus one VA13 island. The result has 21 opens, 31,834
routed items, and zero short, clearance, crossing, hole, or edge findings. A
fresh 0.10 mm/100 mm-margin sweep accepts no additive route on the cleaned
topology. `ref/routing/current21-dangling-prune.json` guards the exact board,
configuration, DRC counts, and tool hashes. The input still belongs to the
older 303-footprint/2,395-pad convergence lineage rather than the subsequently
expanded current source PCB, so this supersedes the 23-gap checkpoint only as
routing evidence and remains inadmissible as production copper.

A second bounded continuation adds adaptive batch descent: after accepting a
short final chunk it keeps that smaller transaction size instead of repeatedly
rescanning live branches at the original width. Starting from the reproduced
21-gap board, 614 further non-source items are removed. Track-dangling findings
fall from 87 to 23 and via-dangling findings from 11 to 2, while the same 21
open nets and every zero-valued electrical DRC category are preserved. This
leaves 31,220 routed items and frees substantially more corridor area without
inventing a connection. The exact input/output/DRC/configuration/tool hashes are
guarded in `ref/routing/current21-deep-dangling-prune.json`. Twenty-five tails
remain for the next guarded continuation. A fresh bounded 0.10 mm/100 mm-margin
sweep attempts all 21 cleaned signatures and accepts none; its output is
byte-identical to the deep-pruned input. Removing obsolete intermediate islands
exposes wider honest marker pairs, including MA7 changing from 5.709 to 19.421
mm, CS_D10 from 20.575 to 29.610 mm, and IORD from 20.141 to 32.098 mm. As
above, this is still the older 303-footprint/2,395-pad convergence lineage and
not production copper.

Fine adaptive continuation from that exact hash removes another 160 migrated
items, bringing the cumulative cleanup to 1,415 items. Both remaining dangling
vias are eliminated and track-dangling findings fall from 23 to 14; the same
21 open nets, 31,060 routed items, and zero electrical findings remain. A fresh
bounded 0.10 mm/100 mm-margin sweep again accepts no route and is byte-identical
to its input. As dead islands retreat, CS_D10's marker grows from 29.610 to
32.314 mm and IORD's from 32.098 to 33.437 mm. Exact hashes, counts, and sweep
state are guarded in `ref/routing/current21-fine-dangling-prune.json`;
fourteen migrated track tails remain for the next guarded continuation.

Two-item continuation removes another 102 migrated segments, bringing the
cumulative cleanup to 1,517. The track-tail frontier falls from 14 to 13 with
no dangling vias, no electrical findings, 30,958 routed items, and the same 21
open nets. A fresh bounded 0.10 mm/100 mm-margin sweep accepts no route and is
byte-identical to its input. Deleting the long obsolete branch exposes IORD's
honest 48.277 mm separation instead of the former 33.437 mm intermediate-island
marker. Exact evidence is guarded in
`ref/routing/current21-twoitem-dangling-prune.json`; thirteen migrated track
tails remain for continuation.

Continued two-item pruning removes another 70 migrated items, bringing the
cumulative cleanup to 1,587. The warning frontier contracts from thirteen
dangling tracks to ten tracks plus one via, with zero electrical findings,
30,888 routed items, and the same 21 open nets. A fresh bounded 0.10 mm/100
mm-margin sweep tests all 21 gaps, accepts no route, and is byte-identical to
its input. Exact evidence is guarded in
`ref/routing/current21-eleven-tail-prune.json`; eleven migrated tails remain.

A two-item then single-item continuation removes another 13 migrated items,
bringing cumulative cleanup to 1,600. It eliminates the remaining dangling
via and leaves ten dangling track tails, zero electrical findings, 30,875
routed items, and the same 21 open nets. A fresh bounded 0.10 mm/100 mm-margin
sweep tests all 21 gaps, accepts no route, and is byte-identical to its input.
Exact evidence is guarded in `ref/routing/current21-ten-tail-prune.json`.

Continued pruning along the long residual branches removes another 30 migrated
items, bringing cumulative cleanup to 1,630. The warning frontier plateaus at
ten dangling tracks, but routed items fall to 30,845 without changing the 21
open nets or introducing an electrical finding. A fresh bounded 0.10 mm/100
mm-margin sweep tests all gaps, accepts no route, and is byte-identical to its
input. Exact evidence is guarded in
`ref/routing/current21-ten-tail-plateau-prune.json`.

The next adaptive two-item continuation removes 14 more migrated items,
bringing cumulative cleanup to 1,644 and breaking the plateau from ten to nine
dangling tracks. Routed items fall to 30,831 while the 21 open nets and zero
electrical findings remain unchanged. A fresh bounded 0.10 mm/100 mm-margin
sweep tests all gaps, accepts no route, and writes a byte-identical board.
Exact evidence is guarded in `ref/routing/current21-nine-tail-prune.json`.

Adaptive single-item continuation removes another 30 migrated items along the
next long branch, bringing cumulative cleanup to 1,674. The frontier plateaus
at nine dangling tracks, but routed items fall to 30,801 with the same 21 open
nets and zero electrical findings. A fresh bounded 0.10 mm/100 mm-margin sweep
tests all gaps, accepts no route, and is byte-identical to its input. Exact
evidence is guarded in `ref/routing/current21-nine-tail-plateau-prune.json`.

Two further guarded single-item phases remove 56 migrated items, bringing
cumulative cleanup to 1,730 and reaching the next endpoint reduction from nine
to eight dangling tracks. Routed items fall to 30,745 while the 21 open nets
and zero electrical findings remain unchanged. A fresh bounded 0.10 mm/100
mm-margin sweep tests all gaps, accepts no route, and is byte-identical to its
input. Exact evidence is guarded in
`ref/routing/current21-eight-tail-prune.json`.

The next guarded single-item pass removes 27 migrated items, bringing
cumulative cleanup to 1,757 and reducing the warning frontier from eight to
seven dangling tracks. Routed items fall to 30,718 while the 21 open nets and
zero electrical findings remain unchanged. A fresh bounded 0.10 mm/100
mm-margin sweep tests all gaps, accepts no route, and is byte-identical to its
input. Exact evidence is guarded in
`ref/routing/current21-seven-tail-prune.json`.

Two more bounded single-item phases remove 60 migrated items along the next
long branch, bringing cumulative cleanup to 1,817. The frontier plateaus at
seven dangling tracks, but routed items fall to 30,658 with the same 21 open
nets and zero electrical findings. A fresh bounded 0.10 mm/100 mm-margin sweep
tests all gaps, accepts no route, and is byte-identical to its input. Exact
evidence is guarded in `ref/routing/current21-seven-tail-plateau-prune.json`.

A further bounded single-item phase removes 30 migrated items, bringing
cumulative cleanup to 1,847 and 90 along the current long branch. The
seven-tail frontier persists, but routed items fall to 30,628 with the same 21
open nets and zero electrical findings. A fresh bounded 0.10 mm/100 mm-margin
sweep tests all gaps, accepts no route, and is byte-identical to its input.
Exact evidence is guarded in
`ref/routing/current21-seven-tail-deep-prune.json`.

```sh
for NET in WR D6_V_ENABLE RAM_OUT_EN D3_O6_D6_A5; do
  /usr/bin/python3 kicad/close_gap_by_ripup.py \
    /tmp/juku-dc2-24-a10first.kicad_pcb \
    "/tmp/juku-long-${NET}-unused.kicad_pcb" \
    --net "$NET" --diagnostic-clearance 0.10 \
    --diagnostic-grid-step 0.10 --grid-step 0.10 \
    --route-clearance 0.20 --search-margin 100 --timeout 300 \
    --max-conflicts 256 --diagnose-only \
    --diagnostic-report "/tmp/juku-long-${NET}-diag-drc.json" \
    --summary "/tmp/juku-long-${NET}-diag-summary.json"
done
```

```sh
/usr/bin/python3 kicad/close_gap_by_ripup.py \
  /tmp/juku-dc7-25-dc5first.kicad_pcb \
  /tmp/juku-dc2-24-a10first.kicad_pcb \
  --net DC2 --diagnostic-clearance 0.10 \
  --diagnostic-grid-step 0.10 --grid-step 0.125 \
  --route-clearance 0.20 --search-margin 60 --timeout 240 \
  --max-conflicts 64 --allow-mixed-diagnostic-blockers \
  --restore-grid-steps 0.10,0.125,0.1375,0.15 \
  --restore-net-priority A10,DB0,MEMW,DC3,HLDA,DB1,DC5,INTA \
  --diagnostic-report /tmp/juku-dc2-24-a10first-diag.json \
  --transaction-board /tmp/juku-dc2-24-a10first-restored.kicad_pcb \
  --transaction-report /tmp/juku-dc2-24-a10first-restored.json \
  --summary /tmp/juku-dc2-24-a10first-summary.json
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-dc2-24-a10first.kicad_pcb OUTPUT \
  --min-distance 0 --max-distance 450 --mode M --search-margin 100 \
  --grid-step GRID --route-clearance 0.20 --timeout 180 --limit 0 \
  --attempted-state STATE
# Run the final command with fresh OUTPUT/STATE paths for GRID values
# 0.10, 0.125, 0.1375, and 0.15.
```

```sh
/usr/bin/python3 kicad/refresh_routed_from_source.py \
  --routed kicad/juku_routed_candidate.kicad_pcb \
  --allow-additive-renames --allow-drc-salvage \
  --output /tmp/juku-drc-salvage-raw.kicad_pcb
/usr/bin/python3 kicad/salvage_routed_copper.py \
  /tmp/juku-drc-salvage-raw.kicad_pcb \
  /tmp/juku-drc-salvage-clean.kicad_pcb \
  --summary /tmp/juku-drc-salvage-clean.json
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-clean.kicad_pcb \
  /tmp/juku-drc-salvage-gap10.kicad_pcb \
  --min-distance 1 --max-distance 30 --mode M --timeout 20 --limit 10
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap10.kicad_pcb \
  /tmp/juku-drc-salvage-gap30.kicad_pcb \
  --min-distance 1 --max-distance 30 --mode M --timeout 20 --limit 20
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap30.kicad_pcb \
  /tmp/juku-drc-salvage-gap60.kicad_pcb \
  --min-distance 1 --max-distance 40 --mode M --timeout 20 --limit 30
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap60.kicad_pcb \
  /tmp/juku-drc-salvage-gap90.kicad_pcb \
  --min-distance 1 --max-distance 60 --mode M --timeout 20 --limit 30
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap90.kicad_pcb \
  /tmp/juku-drc-salvage-gap120.kicad_pcb \
  --min-distance 1 --max-distance 80 --mode M --timeout 20 --limit 30
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap120.kicad_pcb \
  /tmp/juku-drc-salvage-gap123.kicad_pcb \
  --min-distance 1 --max-distance 120 --mode M --timeout 20 --limit 3
STATE=/tmp/juku-gap-resume.json
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap123.kicad_pcb \
  /tmp/juku-drc-salvage-gap128.kicad_pcb \
  --min-distance 1 --max-distance 120 --mode M --timeout 20 --limit 5 \
  --attempted-state "$STATE"
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap128.kicad_pcb \
  /tmp/juku-drc-salvage-gap133.kicad_pcb \
  --min-distance 1 --max-distance 120 --mode M --timeout 20 --limit 5 \
  --attempted-state "$STATE"
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap133.kicad_pcb \
  /tmp/juku-drc-salvage-gap153.kicad_pcb \
  --min-distance 1 --max-distance 120 --mode M --timeout 20 --limit 20 \
  --attempted-state "$STATE"
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap153.kicad_pcb \
  /tmp/juku-drc-salvage-gap173.kicad_pcb \
  --min-distance 1 --max-distance 120 --mode M --timeout 20 --limit 20 \
  --attempted-state "$STATE"
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap173.kicad_pcb \
  /tmp/juku-drc-salvage-gap193.kicad_pcb \
  --min-distance 1 --max-distance 120 --mode M --timeout 20 --limit 20 \
  --attempted-state "$STATE"
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-gap193.kicad_pcb \
  /tmp/juku-drc-salvage-coarse20.kicad_pcb \
  --min-distance 1 --max-distance 120 --mode M --timeout 20 --limit 20 \
  --attempted-state "$STATE"
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-coarse20.kicad_pcb \
  /tmp/juku-drc-salvage-coarse-exhausted.kicad_pcb \
  --min-distance 1 --max-distance 120 --mode M --timeout 20 --limit 20 \
  --attempted-state "$STATE"
STATE_FINE=/tmp/juku-gap-fine.json
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-coarse-exhausted.kicad_pcb \
  /tmp/juku-drc-salvage-fine10.kicad_pcb \
  --min-distance 0 --max-distance 450 --mode M --search-margin 60 \
  --grid-step 0.25 --timeout 60 --limit 10 --attempted-state "$STATE_FINE"
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-fine10.kicad_pcb \
  /tmp/juku-drc-salvage-fine30.kicad_pcb \
  --min-distance 0 --max-distance 450 --mode M --search-margin 60 \
  --grid-step 0.25 --timeout 60 --limit 20 --attempted-state "$STATE_FINE"
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-fine30.kicad_pcb \
  /tmp/juku-drc-salvage-fine025-exhausted.kicad_pcb \
  --min-distance 0 --max-distance 450 --mode M --search-margin 60 \
  --grid-step 0.25 --timeout 60 --limit 20 --attempted-state "$STATE_FINE"
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-fine025-exhausted.kicad_pcb \
  /tmp/juku-drc-salvage-fine020-exhausted.kicad_pcb \
  --min-distance 0 --max-distance 450 --mode M --search-margin 60 \
  --grid-step 0.20 --timeout 90 --limit 10 \
  --attempted-state /tmp/juku-gap-fine020.json
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-fine020-exhausted.kicad_pcb \
  /tmp/juku-drc-salvage-fine0125-exhausted.kicad_pcb \
  --min-distance 0 --max-distance 450 --mode M --search-margin 60 \
  --grid-step 0.125 --timeout 120 --limit 10 \
  --attempted-state /tmp/juku-gap-fine0125.json
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-drc-salvage-fine0125-exhausted.kicad_pcb \
  /tmp/juku-drc-salvage-fine010-short.kicad_pcb \
  --min-distance 0 --max-distance 30 --mode M --search-margin 60 \
  --grid-step 0.10 --timeout 180 --limit 5 \
  --attempted-state /tmp/juku-gap-fine010.json
```

The legal-clearance and guarded rip-up continuation is reproducible from that
164-gap checkpoint. The six repeated sweep invocations below are deliberately
bounded writes against one lineage-bound state file; the final invocation
accepts the remaining eleven candidates before exhausting the state.

```sh
python3 kicad/close_gap_by_ripup.py \
  /tmp/juku-drc-salvage-fine010-short.kicad_pcb \
  /tmp/juku-ripup-intr.kicad_pcb --net INTR \
  --route-clearance 0.21 --summary /tmp/juku-ripup-intr.json
python3 kicad/close_gap_by_ripup.py \
  /tmp/juku-ripup-intr.kicad_pcb /tmp/juku-ripup-prom.kicad_pcb \
  --net PROM_EN --route-clearance 0.21
python3 kicad/close_gap_by_ripup.py \
  /tmp/juku-ripup-prom.kicad_pcb /tmp/juku-ripup-csd54.kicad_pcb \
  --net CS_D54 --route-clearance 0.21
STATE_021=/tmp/juku-gap-clear021.json
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-ripup-csd54.kicad_pcb /tmp/juku-clear021-20.kicad_pcb \
  --min-distance 0 --max-distance 450 --mode M --search-margin 60 \
  --grid-step 0.10 --route-clearance 0.21 --timeout 180 --limit 20 \
  --attempted-state "$STATE_021"
# Repeat the preceding command five times, advancing input/output by 20 routes.
python3 kicad/close_gap_by_ripup.py \
  /tmp/juku-clear021-120.kicad_pcb /tmp/juku-ripup-ba13.kicad_pcb \
  --net BA13 --route-clearance 0.21 --summary /tmp/juku-ripup-ba13.json
python3 kicad/close_unconnected_gaps.py \
  /tmp/juku-ripup-ba13.kicad_pcb /tmp/juku-clear021-exhausted.kicad_pcb \
  --min-distance 0 --max-distance 450 --mode M --search-margin 60 \
  --grid-step 0.10 --route-clearance 0.21 --timeout 180 --limit 20 \
  --attempted-state /tmp/juku-gap-clear021-final.json
```

Starting from the 45-gap board, the exact-clearance lattice sequence is:

```sh
python3 kicad/close_unconnected_gaps.py INPUT OUTPUT \
  --min-distance 0 --max-distance 450 --mode M --search-margin 60 \
  --grid-step 0.10 --route-clearance 0.20 --timeout 180 --limit 20 \
  --attempted-state /tmp/juku-gap-clear020-grid010.json
# Feed each accepted OUTPUT into the next invocation and use a fresh state file.
# The productive next grid steps are 0.125, 0.15, 0.175, and 0.1375 mm.
# Full 0.20, 0.225, 0.25, and 0.30 mm checks accept nothing.
python3 kicad/close_unconnected_gaps.py INPUT_34 OUTPUT_34 \
  --min-distance 0 --max-distance 450 --mode M --search-margin 60 \
  --grid-step 0.1125 --route-clearance 0.20 --timeout 180 --limit 20 \
  --attempted-state /tmp/juku-gap-clear020-grid01125-final.json
python3 kicad/close_gap_by_ripup.py OUTPUT_34 UNUSED_OUTPUT \
  --net S3_1 --diagnostic-clearance 0.15 --route-clearance 0.20 \
  --diagnostic-report /tmp/juku-s3-diagnostic.json
python3 kicad/close_gap_by_ripup.py OUTPUT_34 OUTPUT_33 \
  --net BA0 --diagnostic-clearance 0.15 --route-clearance 0.20 \
  --max-conflicts 20 --allow-mixed-diagnostic-blockers \
  --restore-grid-steps 0.10,0.15 --summary /tmp/juku-mixed-ba0.json
python3 kicad/close_gap_by_ripup.py OUTPUT_33 OUTPUT_32 \
  --net E3_COM --diagnostic-clearance 0.15 --route-clearance 0.20 \
  --max-conflicts 20 --allow-mixed-diagnostic-blockers \
  --restore-grid-steps 0.10,0.15,0.125 --summary /tmp/juku-mixed-e3.json
python3 kicad/close_gap_by_ripup.py OUTPUT_32 OUTPUT_30 \
  --net DB7 --diagnostic-clearance 0.15 --route-clearance 0.20 \
  --max-conflicts 20 --allow-mixed-diagnostic-blockers \
  --restore-grid-steps 0.10,0.15,0.125 --summary /tmp/juku-mixed-db7.json
python3 kicad/close_gap_by_ripup.py OUTPUT_30 UNUSED_OUTPUT \
  --net CS_D26 --diagnostic-clearance 0.15 --route-clearance 0.20 \
  --max-conflicts 20 --diagnose-only --summary /tmp/juku-diag-csd26.json
python3 kicad/close_gap_by_ripup.py OUTPUT_30 CS_D26_SWAP \
  --net CS_D26 --diagnostic-clearance 0.15 --route-clearance 0.20 \
  --max-conflicts 20 --allow-mixed-diagnostic-blockers \
  --allow-equal-open-swap --restore-grid-steps 0.10,0.15,0.125,0.1375
python3 kicad/close_gap_by_ripup.py CS_D26_SWAP OUTPUT_29 \
  --net D53_Y2_R51 --diagnostic-clearance 0.15 --route-clearance 0.20 \
  --max-conflicts 20 --allow-mixed-diagnostic-blockers \
  --restore-grid-steps 0.10,0.15,0.125,0.1375
# Pin BA2's track-to-via marker with stable KiCad; nightly DRC may choose a
# different representative pair for the same two disconnected islands.
/usr/bin/kicad-cli pcb drc --format json \
  --output /tmp/juku-29-stable-drc.json OUTPUT_29
python3 kicad/close_gap_by_ripup.py OUTPUT_29 UNUSED_OUTPUT \
  --net BA2 --gap-report /tmp/juku-29-stable-drc.json \
  --diagnostic-clearance 0.10 --route-clearance 0.20 --grid-step 0.10 \
  --search-margin 100 --max-conflicts 20 --allow-mixed-diagnostic-blockers \
  --allow-equal-open-swap --restore-grid-steps 0.10,0.15,0.125,0.1375 \
  --restore-net-priority VA8,VA7,P5V,BA5,BA0 \
  --transaction-board BA2_STAGE_30 || test -s BA2_STAGE_30
python3 kicad/close_gap_by_ripup.py BA2_STAGE_30 BA2_VA8_29 \
  --net VA8 --diagnostic-clearance 0.10 --route-clearance 0.20 \
  --grid-step 0.10 --search-margin 100 --max-conflicts 10 \
  --allow-mixed-diagnostic-blockers --allow-equal-open-swap \
  --restore-grid-steps 0.10,0.15,0.125,0.1375 \
  --restore-net-priority BA2,BA3,GND
python3 kicad/close_gap_by_ripup.py BA2_VA8_29 BA0_SWAP_29 \
  --net BA0 --diagnostic-clearance 0.10 --route-clearance 0.20 \
  --grid-step 0.10 --search-margin 100 --max-conflicts 10 \
  --allow-mixed-diagnostic-blockers --allow-equal-open-swap \
  --restore-grid-steps 0.10,0.15,0.125,0.1375 \
  --restore-net-priority VA1,VA5,VA8,VA0,RAIL_H
python3 kicad/close_gap_by_ripup.py BA0_SWAP_29 OUTPUT_28 \
  --net VA8 --diagnostic-clearance 0.15 --route-clearance 0.20 \
  --grid-step 0.15 --search-margin 100 --max-conflicts 10 \
  --allow-mixed-diagnostic-blockers --allow-equal-open-swap \
  --restore-grid-steps 0.15,0.10,0.125,0.1375 \
  --restore-net-priority S3_3,VID_CPU_SEL,P5V
python3 kicad/close_gap_by_ripup.py OUTPUT_28 OUTPUT_27 \
  --net D26_PC0_D3_I5 --diagnostic-clearance 0.205 \
  --route-clearance 0.205 --grid-step 0.10 --search-margin 100 \
  --max-conflicts 8
python3 kicad/close_gap_by_ripup.py OUTPUT_27 OUTPUT_26 \
  --net MA1 --diagnostic-clearance 0.10 --route-clearance 0.20 \
  --grid-step 0.10 --search-margin 100 --max-conflicts 20 \
  --allow-mixed-diagnostic-blockers --allow-equal-open-swap \
  --restore-grid-steps 0.10,0.15,0.125,0.1375 \
  --restore-net-priority W10_QA_SEL,VID_MUX_G,VA2,VA10,VA11,MA0,MA2
python3 kicad/close_unconnected_gaps.py OUTPUT_26 OUTPUT_25 \
  --min-distance 0 --max-distance 450 --mode M --search-margin 100 \
  --grid-step 0.125 --route-clearance 0.20 --timeout 180
python3 kicad/close_gap_by_ripup.py OUTPUT_25 UNUSED_PHI2_SWAP \
  --net PHI2_D35 --diagnostic-grid-step 0.10 --grid-step 0.1375 \
  --diagnostic-clearance 0.10 --route-clearance 0.20 \
  --allow-mixed-diagnostic-blockers --allow-equal-open-swap \
  --restore-grid-steps 0.1375,0.10,0.125,0.15 \
  --restore-net-priority PHI1,PHI2TTL,RAM_RD_OE,VID_MIX1,D36_D33,GND,P5V
python3 kicad/close_gap_by_ripup.py OUTPUT_25 OUTPUT_24 \
  --net DC7 --diagnostic-clearance 0.10 --route-clearance 0.20 \
  --grid-step 0.10 --search-margin 100 --max-conflicts 12 \
  --allow-mixed-diagnostic-blockers --allow-equal-open-swap \
  --restore-grid-steps 0.10,0.125,0.15,0.1375 \
  --restore-net-priority DC5,DC0,DC6,DB1,ROE
```

A follow-up MA1/MA0 topology experiment exposed a DRC-coordinate interpretation
bug rather than another legal closure. KiCad reports a track item's `pos` at
the track midpoint, while both gap wrappers had treated that marker as the open
copper end. For the residual MA0 marker this meant proposing from
`(110.8304,135.8083)` instead of the actual endpoint
`(111.9321,136.91)`, creating a false conflict with MA1. The wrappers now
resolve track/via and pad UUIDs against the current board and choose the nearest
real connection-point pair, falling back to DRC coordinates only for unknown
item types. The corrected initial MA0 gap is 3.8629 mm; an additive
exact-clearance retry finds no legal multilayer path. During the bounded MA1
displacement, however, the new endpoint resolver selects the actual open ends
of both replacement MA0 branches. The 0.1375 mm phase closes the final 4.457 mm
branch, enabling the verified 26-open transaction and subsequent 25-open MA6
checkpoint documented above.

The July-2026 refresh audit found 48 short violations in the first candidate.
Feeding that DRC JSON back through `--exclude-drc` quarantines 16 implicated
routed nets and removes every transplanted-track short. The remaining 12 DRC
short violations were six duplicated pad-to-pad placement collisions already
present in that source snapshot: approximate analog-part positions overlapped the
factory-registered D95/D97/D102 cluster. Later evidence briefly raised the
source count to ten, then complete `.009` assembly/owner coverage proved that
the colliding bodies belonged to the `.006`-only VT3/VT4 RF option. The current
source dispositions those fifteen parts DNP and has zero electrical placement
collisions. S4 is likewise correctly schematic/off-board. The old routed
candidate still remains rejected because it predates these source changes.
This corrected audit supersedes the earlier false zero-short
statement, which inspected a nonexistent top-level JSON field instead of
`violations[type=shorting_items]`.

## Direct MEMR/wire-11 promotion

The native `.006` sheets make one later source correction independently of a
full routed refresh: sheet 1 exports `-MRD`, and both sheet-2 arrivals bearing
that same label land on D33.3 and D92.13. Factory wire 11 continues D92.13 to
D7.1. The former `W11_D7_D92` net was therefore an artificial split and is now
merged into `MEMR` in the board JSON, source PCB, routed PCB, and structural
HDL/LVS contract.

The routed board's twelve existing wire-11 segments were retained as MEMR
copper. The first attempted 2.01 mm F.Cu join was rejected because strict DRC
showed it crossing four select traces. The adopted route instead places
0.6/0.3 mm vias at `(227.0497,127.5849)` and `(230,123)` and joins them on
B.Cu. The independent `M5V_DERIVED` islands are also closed with a via at
`(35,213)`, five short B.Cu segments around D105, and a direct F.Cu landing on
R19.2. Strict KiCad DRC now reports zero copper clearance, crossing, short, or
unconnected findings. These targeted promotions do not imply that the stale
fabrication ZIP has passed the full refresh audit.

A clean refresh therefore requires this order:

1. keep the now-clear source-placement gate guarded while functional connectivity stabilizes;
2. generate the compatible-copper candidate only after netlist freeze;
3. iteratively quarantine any transplanted net implicated by DRC using `--exclude-drc`;
4. route the quarantined nets against the current placement;
5. replace `juku_routed.kicad_pcb` only after endpoint parity and zero electrical
   DRC findings are both proved.

## Current full-refresh routing experiment

A source-complete candidate was generated after feeding its first two KiCad
DRC reports back through `--exclude-drc`. The second report contributed the two
clearance-implicated nets that the older short-only filter missed. The resulting
candidate retained 3,269 compatible copper items on 154 nets, quarantined 13
DRC-implicated nets, and began with zero KiCad shorts, copper-clearance
violations, track crossings, or placement collisions. Its 296 footprints and
2,383 pad identities/net assignments exactly match the source; Specctra import
quantized 54 pad coordinates by at most 38 nm, which is not a topology change.

Freerouting 2.2.4 reduced its internal incomplete count from 1,001 to 270 in
pass 1 (41 minutes 42 seconds), then to 195 in pass 2 (43 minutes 39 seconds).
After importing the session, KiCad reported 189 unconnected items across 83
nets, zero shorts, zero copper-clearance violations, and zero track crossings.
The two remaining non-connectivity copper findings are one dangling `OSC` track
and one `GND` track 0.2257 mm from an edge where the configured minimum is
0.3 mm. The temporary candidate is therefore a substantial convergence result,
not an adoptable routed board. Further routing must close all 189 connections
and both residual copper findings before replacing the tracked snapshot.

A continuation experiment re-exported that imported board and began with 222
Freerouting incompletes across 4,602 route items. Its first pass required 1 hour
48 minutes and reduced the count only to 207. Freerouting also recovered from
two `ShapeSearchTree.merge_entries_in_front` null-entry exceptions while
normalizing the dense imported traces. The remaining three configured passes
were stopped: this route was converging at only 15 internal connections per
pass, did not establish an improvement over the existing 189-item KiCad result,
and had not produced a trustworthy replacement session. Further automated work
should partition or simplify the residual nets instead of repeating whole-board
rip-up passes on this geometry.

Marking all 6,516 imported copper items locked before DSN export did not provide
that partition: Freerouting still reported the same 222 incompletes across
4,602 route items and reproduced the normalization exception within two
minutes. That duplicate run was stopped. KiCad's Specctra export therefore does
not turn the dense imported geometry into a cheap residual-only routing problem
merely by setting the board-item lock flag.

The deterministic follow-up uses the existing two-layer A* gap router through a
strict DRC transaction wrapper. Each proposal is made on a temporary board and
is accepted only if KiCad reports fewer unconnected items, no shorts,
clearance violations, or crossings, and no increase in any other DRC violation
type. The single-layer distance bands and bounded multilayer pass are
reproducible with:

KiCad 10.99 truncates the CLI DRC report at 499 unconnected markers. For a
newly refreshed board above that ceiling, `--accept-capped-progress` provides
an explicit opt-in transaction rule: the exact proposed endpoint pair must be
present before the route and absent afterward, both reports must remain at the
499-marker ceiling, and no violation category may increase. The ordinary
strict count-decrease rule remains the default and resumes automatically below
the ceiling. A current-source refresh trial used this mode to accept 125 local
routes, reducing the uncapped Python connectivity count from 1,190 to 1,065
while retaining zero electrical-category DRC findings. This also establishes
that local closure is useful for guarded repairs but is not an efficient
replacement for the bulk-routing stage at this scale.

```sh
python3 kicad/close_unconnected_gaps.py INPUT.kicad_pcb OUTPUT.kicad_pcb \
  --max-distance 30 --timeout 20
python3 kicad/close_unconnected_gaps.py OUTPUT.kicad_pcb OUTPUT_50.kicad_pcb \
  --min-distance 30 --max-distance 50 --timeout 20
python3 kicad/close_unconnected_gaps.py OUTPUT_50.kicad_pcb OUTPUT_M.kicad_pcb \
  --max-distance 15 --mode M --timeout 60 --limit 10
python3 kicad/close_unconnected_gaps.py OUTPUT_M.kicad_pcb OUTPUT_WIDE.kicad_pcb \
  --max-distance 450 --mode M --search-margin 60 --timeout 30
python3 kicad/close_unconnected_gaps.py OUTPUT_WIDE.kicad_pcb OUTPUT_FINE.kicad_pcb \
  --max-distance 450 --mode M --search-margin 60 --grid-step 0.25 --timeout 60
python3 kicad/close_unconnected_gaps.py OUTPUT_FINE.kicad_pcb OUTPUT_SHAPED.kicad_pcb \
  --max-distance 450 --mode M --search-margin 60 --grid-step 0.10 \
  --route-clearance 0.45 --timeout 180
```

The first two single-layer bands accepted 14 proposals and reduced KiCad's
unconnected count from 189 to 175. The initial bounded multilayer pass then
accepted 10 short residual gaps, including power, ground, `MA6`, and `CAS`, and
reached 165 unconnected items.

Profiling the next pass exposed an invariant full-board scan inside every A*
state: each possible layer change re-enumerated roughly 6,800 copper items to
check its distance from existing vias. `repair_fdc_route_gaps.py` now rasterizes
those existing-via keep-outs once per proposal. A previously 60-second timeout
then produced the same raw candidate in 1.3 seconds; the transaction wrapper
correctly rejected that particular candidate for a new short and clearance
violation. With no acceptance-rule relaxation, subsequent 0-30 mm multilayer
passes accepted 28 more routes. Two bounded 30-50 mm passes accepted another 15
across ground, data, timing, density, and latch nets before exhausting that
band's remaining legal proposals. Two 50-75 mm passes accepted 14 more routes,
including `IORD`, `IOWR`, `POF`, `FDC_DDEN`, `FDC_DAL7`, `DC1`,
`M5V_DERIVED`, and `X4_STOP_N`, before exhausting the band. The 75-100 mm band
accepted 10 more routes, including `HLDA`, `IORC_N`, `MEMW`,
and `D6_MEM_SELECT_N`; a second pass accepted none. The guarded candidate then
accepted eight routes in the 100-125 mm band, including `IORD`, `IOWR`,
`MEMW`, `ROE`, and `SYNC`, while rejecting its first `VIDEO_OUT` proposal.
The remaining 125-225 mm distance bands accepted 14 routes and reached 76
unconnected items; no DRC gap is longer than 232 mm.

The multilayer search corridor is now an explicit `--search-margin` parameter
instead of a fixed 30 mm. Exhaustive 60, 90, and 120 mm corridor sweeps accepted
8, 3, and 1 additional routes respectively, including `VIDEO_OUT`, `SER_DTR`,
`MEMW`, BA4/BA5, and another `P5V` island. The 120 mm sweep therefore establishes
the current corridor-expansion limit at 64 unconnected items on 50 nets and
10,326 copper items, a cumulative reduction of 125 from the Freerouting import.

The A* lattice is likewise explicit through `--grid-step`. A 0.25 mm sweep
accepted 21 routes that the default 0.5 mm grid could not represent, including
dense address/data-bus links plus `XTAL16M`, `PHI1`, `PHI2TTL`, `PIT_BAUD`,
`D26_PC5_RN_IN`, and `D39_O8`; a second complete pass accepted none. The
current temporary board has 43 unconnected items on 35 nets and 11,888 copper
items, a cumulative reduction of 146 from the Freerouting import. A subsequent
0.20 mm sweep accepted four routes and closed five more gaps, primarily in the
remaining `MA6`/`CAS` cluster. Its second-order result is 38 unconnected items
on 35 nets and 12,113 copper items, a cumulative reduction of 151. A 0.125 mm
sweep then accepted two more routes for `CAS` and `DB5`; the current temporary
board has 36 unconnected items on 34 nets and 12,161 copper items, a cumulative
reduction of 153. A final 0.10 mm sweep accepted one `DB1` route and reached 35
unconnected items on 33 nets with 12,306 copper items; further global lattice
reduction is no longer productive. Rejected proposals now report their exact
unconnected and DRC-count deltas to guide route-specific remediation.

Route-specific diagnosis then exposed a keep-out approximation error: the
router represented every pad by a circle based on its largest dimension. A
proposed diagonal P5V segment therefore cleared the circular approximation but
clipped the corner of square pad E2.1, producing 0.1546 mm actual clearance
against a 0.2 mm rule. Pad obstacles now use KiCad's shape- and
rotation-aware hit test on the applicable copper layer. Proposal clearance is
also exposed as `--route-clearance` so a wider keep-out can be tested without
changing the acceptance invariant. With the corrected pad geometry, the same
0.10 mm sweep legally closed P5V and BA13 and reached 33 unconnected items on
31 nets with 12,705 copper items, a cumulative reduction of 156 from the
Freerouting import. A complete second-order sweep accepted no other routes.

The next rejected MEMR proposal identified an independent layer-change bug:
its new via landed only 0.0198 mm from the drilled hole in same-net pad D92.13,
while the board rule requires 0.2495 mm. Same-net copper overlap is legal, but
hole spacing is net-independent. The multilayer router now keeps new vias away
from every drilled pad using the existing hole radius, the 0.3 mm proposal-via
drill, and a 0.25 mm edge-to-edge allowance. The corrected proposal closed
MEMR and reached 32 unconnected items on 30 nets with 12,844 copper items, a
cumulative reduction of 157. A complete hole-aware residual sweep accepted no
further routes.

P12V and RESET proposals then revealed that the old 0.4 mm hard-coded outer
rectangle was not an adequate board-edge model. In particular, P12V passed
only 0.35 mm from the circular Edge.Cuts hole centered at `(10.1,135.6)`;
the configured copper-to-edge rule is 0.5 mm. The router now rasterizes every
actual Edge.Cuts primitive through KiCad's shape-aware hit test, including the
internal mounting holes, with the rule clearance plus half the proposed track
width. Alternate P12V and RESET routes pass the strict transaction guard and
reach 30 unconnected items on 29 nets with 13,117 copper items, a cumulative
reduction of 159. The remaining M12V edge-related proposal becomes correctly
unroutable rather than producing a new violation.

The initial candidate also retained one imported GND segment only 0.2257 mm
from the circular Edge.Cuts hole at `(199,251.2)`. A reproducible targeted
repair in `kicad/repair_residual_copper_findings.py` preserves both live-chain
endpoints and replaces that segment with a three-segment F.Cu dogleg on the
open side of the hole; the lower side was rejected because it conflicts with
RAM_RD_OE. The accepted dogleg removes the last copper-to-edge finding without
changing the 30-open count. One intermediate pypcbnew save stopped reporting
the 53 `pth_inside_courtyard` entries, while subsequent router saves reported
them again with unchanged geometry; that transient count change was not
treated as a routing improvement.

Two final router assumptions explained the residual false proposals. DRC gap
items identify whether each endpoint is on F.Cu, B.Cu, or a through-hole pad,
but the wrapper discarded that information and let A* choose either endpoint
layer. OSC and DB3 routes therefore reached the right coordinates on the wrong
layers without closing their gaps. The wrapper now passes explicit F/B/A
endpoint constraints. Layer changes also used track-width keep-outs for a
0.6 mm via; a separate via-copper obstacle map now checks the full 0.3 mm via
radius against both layers. With those corrections, OSC closes at a guarded
0.30 mm proposal clearance, DB3 closes, and the residual cleanup removes the
now-redundant 1.555 mm OSC tail only after another OSC route reaches its
junction. This reached 28 unconnected items with zero electrical-category DRC
findings.

A complete rule-accurate 0.30 mm sweep then accepted 21 more routes: CAS,
BA11, PST_CLK, S3_2, BA4, IOM_N, MWC_N, INHIB_N, BA10, IOWC_N, DB7, AMWC_N,
BA12, SYNC, W10_QA_SEL, RESET, INT7_RAW, M12V, MEM_MODE0, STSTB, and
MEM_MODE1. The current candidate has 7 unconnected items on 7 nets (`BA1`,
`BA11`, `DB4`, `INTR`, `PHI2`, `MA6`, and `RAM_OUT_EN`) and 16,747 copper
items, a cumulative reduction of 182 from the Freerouting import. A complete
second pass accepted nothing.

The current authoritative DRC has zero shorts, copper-clearance violations,
track crossings, hole-clearance violations, dangling tracks, or copper-to-edge
findings. All 663 remaining non-electrical violation counts equal the prior
counts after removing the former GND edge and OSC dangling findings. Exact
identity/net parity with all 2,383 source pads also remains proved. This
candidate is still temporary and cannot replace the tracked routed board.

A guarded 0.25 mm proposal-clearance sweep then closed DB4, BA11, BA1, PHI2,
and RAM_OUT_EN. At the exact 0.20 mm board rule, MA6 also closed cleanly. The
current candidate therefore has one unconnected item, INTR between D1.14 and
D10.17, with 17,595 copper items and no electrical-category DRC findings: a
cumulative reduction of 188 from the Freerouting import. An intentionally
under-clearanced 0.15 mm diagnostic found a geometric path but strict DRC
rejected it with 79 new clearance findings. INTR is therefore blocked by a
broad occupied corridor, not merely lattice quantization; the next automatic
step is transactional rip-up and reroute of the displaced nets.

`kicad/close_intr_by_ripup.py` makes that final transaction reproducible. It
generates the guarded 0.15 mm diagnostic path, derives the conflicting copper
set from its DRC report rather than a hard-coded UUID list, and selects 25
items across 17 other nets. Removing them creates 22 opens across 18 nets;
INTR then closes at 0.21 mm proposal clearance. A 0.20 mm recovery sweep
restores 19 displaced gaps, a 0.21 mm pass restores the marginal P5V and IORD
gaps, and `prune_dangling_tracks.py` transactionally removes 17 dead track/via
tails while preserving zero opens after every removal.

Before the native rail-E correction, the independently repeated result was
preserved as `kicad/juku_routed_candidate.kicad_pcb`: 296 footprints, all
2,383 source pad identities and nets (maximum coordinate quantization 38 nm),
18,245 copper items, zero unconnected items, and zero shorts, clearance,
crossing, hole, dangling, or edge findings. That pre-correction checkpoint's
byte size was 8,370,737 and its SHA256 was
`d51b2b4a226712c1325ff2b770413911800ad458447343095bab73fe9d7a2f29`.
The remaining 663 findings are non-electrical
silkscreen/courtyard/library/text categories with unchanged counts. This is a
source-complete routing checkpoint, not fabrication authorization: the
functional P0 netlist is not frozen, and the tracked production routed board
and manufacturing package must still be regenerated and reviewed after that
freeze.

Subsequent wire-table review adds a stricter construction-fidelity hold:
`docs/factory-wire-route-fidelity.md` shows that all ten factory insulated-link
nets are present in this zero-open checkpoint as ordinary routed copper because
their paired `А:N` landing terminals and two-island partitions were not yet
modeled. The source PCB now splits A:7, A:8, A:10, A:11, A:14, A:19, and A:20 into landing
pairs joined by explicit assembly wires, so this checkpoint lacks those fourteen
pads and keeps the old PHI1, STSTB, W10_QA_SEL, MEMR, PHI2, MEMW, and S_TTL copper substitutions. The artifact remains useful convergence
evidence, but it must not
be adopted as production copper until those seven intentional assembly closures
replace the copper substitutions.

The preserved artifact is rechecked locally with:

```sh
$(scripts/find-kicad-python.sh) kicad/check_routed_candidate.py
```

## Post-checkpoint source drift

The formerly zero-open artifact remains routing-convergence evidence, not a
claim of parity with every later source edit. Merging the native drawing's
formerly separate rail-E model into ground exposes one real missing join between
that old copper island and the main ground domain; it must be rerouted rather
than hidden by another label. The candidate contains 2,383 pad identities,
while the current source contains 2,393; 2,369 identities are common and 24 are
source-only, including W7.1/W7.2, W8.1/W8.2, W10.1/W10.2, W11.1/W11.2,
W14.1/W14.2, W19.1/W19.2, and W20.1/W20.2. Among the common identities it finds 62 changed pad-net assignments and 202 pads
whose coordinates moved by more than 50 nm. The moved set is confined to
C69, D5, D7, D8, D9, D13, D37-D39, D50, D51, D105, R13, R14, R46, and R49-R57; one net-only
change is source C34.1, corrected from `RAIL_H` to `P5V` by the native E-F
drawing. `check_routed_candidate.py`
therefore correctly rejects the checkpoint against current source instead of
silently blessing stale copper. Refresh/reroute is deliberately deferred until
the remaining factory-wire islands and functional P0 netlist freeze; doing it
now would route the known-wrong copper substitutions again.
