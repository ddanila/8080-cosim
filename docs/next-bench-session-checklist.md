# Next bench / photo session — consolidated checklist

Status: **OWNER ACTION LIST** (hand-maintained; the auto-generated superset is
`docs/owner-measurement-shortlist.md`). Ordered by unlock value. **Before adding
or re-asking any measurement here, check `docs/owner-measured-facts.md` — it
indexes what has already been probed, so nothing gets re-requested.**

Use the exact `.009` drawings for source intent and owner photos for visible
construction. Continuity establishes electrical connections; photographs alone
cannot prove hidden joints, rail polarity, or absence of a connection. Resolve
conflicts explicitly before changing the model.

Closed D6 reader, D94 local-control, and D30 continuity results are indexed in
[owner-measured facts](owner-measured-facts.md). Do not request them again as
missing evidence.

## Remaining P0 connectivity (batch in the same session)

1. **D94 `.092` D0 closure and live steering:** owner continuity on 2026-07-21 closes
   D94 D5-D7/pins 6, 7, and 9 plus D104.10 as NC, matching the exact-revision
   drawing. Exact `.009` sheets 1 and 3 close D9.7 `CS7` to D94.15/D93.3. With
   D94 removed, repeat-check D94.1 against D101.1, physical D2.15, and an
   independently identified `-WREQ` point. Exact sheet 3 draws D94.1 to
   `WREQ (1)` and sheet 1 draws R8=2 kΩ on that node, while the owner check
   found only its local R8 branch. Identify the remote owner path or confirm
   its absence before merging the boundary into `WREQ_N`.
   During port `1F` data-register
   transfers, also capture D101.7/A4, D94.1/D0, D93.4 `/RE`, and D93.2 `/WE`:
   A4 low must steer to D0 with both D93 strobes released, while A4 high restores
   the direction-appropriate D93 strobe. This runtime capture corroborates the
   physical table but does not replace the D0 continuity check
   (`docs/d94-reconstruction-constraints.md`).
2. **FDC support pins** (only if pursuing FDC later; not on the VJUGA path):
   first isolate the tentative D96.6 observation from the source-closed 1 MHz
   slot route. Measure resistance from D96.6 to D40.11 in both probe
   polarities, preferably with D96 removed; sheet 3 requires D96.6 to remain
   local to D96.2 and not join the D40.11/D59.5/D92.2/.3/D95.5/.6 net.
   D96.1/.4 WREQ_N with Q1/.5 and Q1_N/.6 for post-release phase; D96.9 Q2↔D101.4/R92.1,
   D96.11 CLK2↔D94.2/D99.9/R89.1 and D96.11↔D96.10 isolation at their
   unmarked drawing crossing; then D96.13↔D99.10 and D99.10↔D100.11 T
   separately before tracing their quoted sheet-1 continuations;
   D99.4/.5/.11/.12; and
   D101.1 `/OE0` against D26.38 IMDRG, then D101.3/.5/.6 each against D101.4/R92.1/R99.2. D101's shared EARLY/LATE
   select pins 2/14 and its complete Q1 write-precomp half are already
   source-closed and must not be re-probed as missing paths
   (`docs/fdc-hardware-handoff.md`).
3. **Factory Вид В details:** D56.5->D34.9 and D56.12->D55.15/.18 are now
   owner-closed. D56's three physical callout locations are fixed as the
   separate left annulus plus D56.5/D56.12; identify the installed item-159
   material and the remaining auxiliary-annulus/adjacent-rail disposition.
   Position 150 is tubing, not a cut. The D11-local photo fit locates D14.2,
   D14.7, and its fifth landing on the solder face; confirm those same-hole
   matches, then test the fifth hole to D29.10/GND along its photo-traced
   strip and continuity-test D14.2/.7 remote conductors, three long traces,
   and the right-row dogleg. At D11,
   continuity-test the registered four-landmark bridge and its remote endpoints;
   two-sided package-local projection has exhausted the solder photos, and the
   old pins-4–6 scar is a different feature. D15's A2/A1 cut and D14's
   local D32.4/GND-to-D14.1 link are photo-closed (`docs/factory-modification-disposition.md`).
4. **P0 D7.3/D29.2 owner path:** with power removed, check D7.3 to its
   wire-covered front via near (3356,975) in 200411500 and candidate solder
   hole (2190,700) in 200525009. The visible solder run ends at (3065,730),
   photo-registered to D29.2's front waypoint near (2480,1015) in 200411500
   and (2255,2352) in 200354648. Check D29.2 to that waypoint and the
   waypoint to D7.3; the cable gaps and first same-hole match remain open.
   Trace any further `AMW_N` loads; keep it separate from D29.5, which the
   2026-07-19 owner continuity assigned to qualified peripheral `/WR`.
   See [the D7 path review](d7-gates-source-review.md).
5. **D104 fourth receiver and R30 ground:** the receiver
   input is photo-traced to R30 lower; the source model assigns that lead to
   GND, but the owner rail polarity is not photo-proved. With power removed,
   confirm D104.7 to R30 lower, lower to known GND, and upper to D12.3/OC SOUT;
   D104.10 is owner-closed NC. Record tested endpoints and resistance in both probe polarities
   for any resistive path. See [the serial handoff](serial-handoff.md) and
   [unresolved endpoints](main-board-unresolved-endpoints.csv).
6. **D1.24 WAIT versus measured I/O-cycle net:** the exact .009 sheet draws
   D1.24 to D105.1, while owner continuity puts D105.1 with D7.8/D6.15.
   D1.24 and D7.8 are both output pins, so joining both reported paths on
   one fitted board would create an output-contention risk. With power off,
   first check D1.24 at its registered solder joint near `(2580,2381)` and
   its photo-traced open annulus `(1830,2395)` in `200527310`; then test that
   annulus directly to D105.1, D7.8, and D6.15. If D1 is socketed, repeat
   ambiguous continuity with it removed to distinguish board copper from
   a path through the device. Record resistance and probe polarity before
   merging WAIT with `IO_CYCLE_H` (`ref/photos/juku-pcb-2/d1-wait-source-review.json`).

The generated `docs/owner-measurement-shortlist.md` carries the lower-priority
timing, control, passive, and value reads with exact starting pins. Take those
after the P0 set if the board remains available; record unresolved results
instead of treating a silent meter or an unread photo as proof of no-connect.
Its P1 analog capture now names D34.8/R62.1, D34.11/R63.1, and the common
R62.2/R63.2/R64.1/VT2.3 node on the original .009 board, with X6 A:3 (after continuity to VT2.1/R65.1 is confirmed) as the
output comparison.

### D59 timing and oscillator probes (P1)

- The registered `200534267` solder row photo-joins D59.2 and D59.3. Its
  D59.3 branch reaches an open annulus near `(3160,2200)` through the extra
  joint near `(2975,2260)`. With power off, test that annulus to both Z1
  lugs, C73, D40.2, and D39.10 before merging OSC with XTAL16M. The front
  projection lies under the crystal-can area and is not a registered Z1 hole.
- In overlapping solder tile `200537608`, D59.11 reaches a separate open
  annulus near `(610,2350)`, mapped near `(2316,2476)` in `200534267`.
  Verify the possible front same-hole ring above R38 at `(1453,2380)` in
  `200452717.MP`, then check the annulus to source-modeled D39.8. The second
  front view `200443117` repeats that ring near `(1400,2900)` but does not
  prove the cross-face match.
- Probe D59.10 at the middle dark lower-row crown near `(2780,2450)` in
  `200534267` for its tag-10 destination. The visible west/east traces in
  the overlap belong to neighboring D59.11 and D59.9; keep D59.10 separate
  from D57.13 SOUND unless direct continuity proves an owner-board change.
  See `ref/photos/juku-pcb-2/d59-orientation-audit.json` and
  `ref/photos/juku-pcb-2/d59-pin10-solder-probe-target.json`.

## E8 selector and ROM configuration read (P1)

The exact `.009` drawing and the fitted white E8 3–4 wire select D26
PB4/pin22 for keyboard `CONTRDAT`; five archived Ekta ROMs instead mask PB5
in their S21 scans. With power removed, check D26.22 to both E8 wire ends,
the E8.4 end to the proposed full-band solder site 6 near `(2140,2375)` in
`PXL_20260710_200530933.MP.jpg`, and that site to X9.9/A50. Check D26.23
to E8.2 and for isolation from the wire. Record the actual A50 hole; the
15-site photo band alone cannot assign its fourteen cable wires.

If the machine can run a controlled PPI read, select scan columns 8–15 one
at a time, toggle one S21 switch, and record the Port B byte at each column.
The changed bit distinguishes PB4 from PB5 without inferring it from a ROM
version. Record the installed D15/D16 identification or dump alongside the
readback. See `ref/photos/juku-pcb-2/e8-bridge-photo-review.json` and
`docs/ektasoft-rombios-lineage.md`.

## Programmable-parts corroboration (optional, Tier-3)

- Independent re-reads of D2/D6/D8/D94 can corroborate the validated physical
  PROM captures.
- D15/D16 owner-board reads would establish fitted EPROM contents for comparison
  with the adopted archival pair; that pair is not an owner-board capture.
  These reads are optional preservation work, not replica release gates. See
  [firmware lineage](d15-d16-firmware-lineage.md) and
  [the acquisition request](community-prom-media-request.md).

The D6 output-order and D94 static-output blockers are closed; the highest-value
remaining D94 bench item is the chip-removed D0 continuity check above. The
port-`1F` steering capture is secondary corroboration.
