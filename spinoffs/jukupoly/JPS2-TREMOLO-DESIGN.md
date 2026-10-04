# JPS v2 tremolo contract

Status: implemented frame-boundary tremolo; three capability-03 tracks are
included in the mixed library. Physical listening was acceptable but inconclusive
for Dark Halls/Suspense. Qualification is scoped to the delivered payloads in
[OPL-PLAN-STATUS.json](OPL-PLAN-STATUS.json), not arbitrary future conversions.

## Scope and evidence

This slice approximates only OPL amplitude modulation which has a direct
audible path.  It adds one shared 3.7 Hz attenuation LFO and a per-tone depth
of zero through three Juku mixer levels.  It does not emulate an OPL waveform,
FM-modulator timbre changes, feedback, vibrato, or independent LFO phases.

[The host analysis](OPL-TREMOLO-M4.json) records where direct source AM
survives 4-bit quantization and verifies that FM-modulator-only channel levels
remain unchanged. [The candidate fit](OPL-TREMOLO-CANDIDATE-M4.json) supplies
the joint envelope/tremolo comparison. Implemented target, full-track and
physical-listening qualification are scoped by the evidence below; a host fit
alone does not authorize delivery.

## Compatibility boundary

Target support is compiled with `-P5=1`, together
with the existing `-P4=1` envelope support.  The frozen `-P2=1` G0 player and
the `-P2=1 -P4=1` M3 envelope player remain separately reproducible.

The tremolo-only extension build accepts:

- `JPS\1`, capability `00h`: the original packet ABI;
- `JPS\2`, capability `01h`: fitted envelopes only;
- `JPS\2`, capability `03h`: fitted envelopes plus bounded tremolo;
- no other version or capability combination.

Capability bit 0 means fitted envelopes and bit 1 means tremolo.  Tremolo
cannot appear without the envelope capability.  An envelope-only player must
reject capability `03h`; a tremolo-capable player must reject tremolo packet
bits when the header advertises only capability `01h`.  The whole variable
row stream is still preflighted before the PIT is touched.

The first three-byte instruction at `prepare_frame` is patched at song start.
For JPS v1 and capability `01h` it remains the original
`LDA ch1_volume`.  For capability `03h` it becomes a same-size jump to the
tremolo preparation routine.  Consequently disabled tremolo adds no
instruction, call, branch, or cycle to normal frame preparation.  The
assembled 64-byte sample loop remains byte-identical to the baseline; runtime
operand updates continue as described below.

## Packet encoding

The five-byte nonzero JPS v2 tone packet does not grow.  Byte 4 becomes:

| Bit | Meaning |
|---:|---|
| 0 | release rate code bit 2 |
| 1 | sustain while keyed (`EGT`) |
| 2–3 | tremolo depth, `0..3` mixer levels |
| 4–7 | reserved; must be zero |

For capability `01h`, bits 2–7 must all be zero.  A key-off remains the
existing two-byte zero phase step and does not serialize another depth.
Tremolo continues through the release tail.  A following nonzero tone packet
replaces the channel depth; legato changes may replace depth without
restarting the envelope or shared phase.

The score-side field is `opl_tremolo_depth`, adjacent to `opl_envelope`, and
must be an integer `0..3`.  The compiler infers capability `03h` only when at
least one tone packet has nonzero depth.  Omitting the field is exactly depth
zero and retains capability `01h`.  No track name, number, filename, or
instrument signature participates in encoding.

## Exact target semantics

The target uses the already-tested M4 host constants:

- 16-bit unsigned shared phase, reset to zero at song start;
- phase increment `4850` (`12F2h`) once per rendered music frame;
- table index `phase >> 12`, giving 37.0 cycles in ten seconds at 50 Hz;
- four 16-entry attenuation tables identical to `opl_tremolo.TABLES`;
- output `max(0, envelope_level - attenuation)`.

The current `chN_volume` bytes remain the unmodulated envelope levels.  The
tremolo routine writes only the three self-modified `ORI` immediates used by
the next sample batch, then joins normal preparation immediately before phase
steps are loaded.  Thus modulation cannot feed back into attack, decay,
sustain, or release state.

Envelope flags occupy the low nibble of `ENV2_FLAGS`. In the tremolo build,
packet depth bits 2–3 are shifted into internal flag bits 4–5, already
in table-page-offset form (`00h`, `10h`, `20h`, or `30h`).  No new per-channel
byte is required.  New persistent state is exactly the two-byte shared phase;
scratch uses registers which normal preparation reloads before entering the
sample loop.

The phase table is consulted before the increment, so target frame zero uses
the same phase as `simulate_tremolo(..., start_frame=0)`.  The phase advances
even when all three current depths are zero in a capability `03h` song, which
keeps later notes aligned to absolute source time.

## Resource and cycle guards

The tremolo layer adds exactly two persistent phase bytes, 64 fixed table bytes,
no per-channel byte and no tone-packet growth. The tremolo-only player declares
51 state bytes; exact map and cycle evidence is in
[OPL-TREMOLO-TARGET-M4.json](OPL-TREMOLO-TARGET-M4.json).
The combined tremolo/vibrato build is measured independently under the
[pitch contract](JPS2-PITCH-DESIGN.md).

Frame-boundary effects, row parsing, percussion and Escape share one
[rate/memory budget](OPL-REDUCTION-PLAN.md). Disabled paths retain their matched
compatibility profiles, the sample loop is frozen, the player must end below
`1800h`, and full-track measurements must determine calibration and delivery.
No tone-range, drum or Escape omission may buy cycles.

## Failure and rollback rules

This slice has independent acceptable stopping points:

- If exact target traces disagree, keep the host/oracle analysis and do not
  ship the target capability.
- If runtime cycles fail G2, try a smaller table or sparse host-baked level
  changes; do not lower the sample rate beyond the shared 10% limit.
- If code or state fails G4, remove target tremolo and retain envelopes.
- If representative error or physical listening is not better, retain the
  capability as an experimental result or remove it from production builds;
  depth zero/JPS v1 remains the fallback.
- If later vibrato or pitch work exhausts the combined budget, features are
  prioritized by measured benefit.  Passing M4 does not reserve the entire
  remaining budget for tremolo.

The success condition is therefore the best measured subset the hardware can
support—not completion of every OPL feature named in the wider plan.

## Qualification evidence

- [Target report](OPL-TREMOLO-TARGET-M4.json): exact prepared amplitudes, phase,
  state/map, enabled/disabled profiles and frozen sample loop.
- [Bounded real report](OPL-TREMOLO-REAL-M4.json) and
  [full-track report](OPL-TREMOLO-FULL-M4.json): generic joint fits, song sizes,
  measured rates/duration and target/reference render hashes.
- [M6 physical record](sessions/cs00000-jukupoly-m6-physical/README.md): exact
  tested payloads and listening limits. A delivered capability does not imply
  every source instrument benefits from tremolo.

The generic converter enables this reduction through `--enhanced-tremolo`;
only direct, quantization-surviving, beneficial fits receive depth. The mixed
library selection and fallbacks are recorded in the generated plan-status report.
Use `sync/jukupoly_check.sh` and `sync/jukupoly_library_check.sh` for host/target
semantics and preflight, and the linked report writers for exact measurement
freshness. Completed experiment chronology is in Git.
