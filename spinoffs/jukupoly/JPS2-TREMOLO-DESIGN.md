# JPS v2 tremolo vertical-slice contract

Status: guarded M4 target design, 2026-09-01.  The host/oracle evidence is
implemented; the 8080 experiment described here is not yet an accepted player
feature.  The accepted M3 envelope player and JPS v1 output remain the
fallback.

## Scope and evidence

This slice approximates only OPL amplitude modulation which has a direct
audible path.  It adds one shared 3.7 Hz attenuation LFO and a per-tone depth
of zero through three Juku mixer levels.  It does not emulate an OPL waveform,
FM-modulator timbre changes, feedback, vibrato, or independent LFO phases.

[`OPL-TREMOLO-M4.json`](OPL-TREMOLO-M4.json) establishes that exact source AM
survives independent 4-bit quantization in 69,978 of 405,454 direct-AM channel
frames and never changes any of the 232,212 FM-modulator-only channel frames.
[`OPL-TREMOLO-CANDIDATE-M4.json`](OPL-TREMOLO-CANDIDATE-M4.json) establishes
one real joint envelope/tremolo fit worth carrying through a reversible target
experiment.  These reports justify an experiment, not default enablement.

## Compatibility boundary

Target support is compiled only in a new `-P5=1` experimental build, together
with the existing `-P4=1` envelope support.  The frozen `-P2=1` G0 player and
the `-P2=1 -P4=1` M3 envelope player remain separately reproducible.

The experimental library player accepts:

- `JPS\1`, capability `00h`: the original packet ABI;
- `JPS\2`, capability `01h`: fitted envelopes only;
- `JPS\2`, capability `03h`: fitted envelopes plus bounded tremolo;
- no other version or capability combination.

Capability bit 0 means fitted envelopes and bit 1 means tremolo.  Tremolo
cannot appear without the envelope capability.  An envelope-only player must
reject capability `03h`; an experimental player must reject tremolo packet
bits when the header advertises only capability `01h`.  The whole variable
row stream is still preflighted before the PIT is touched.

The first three-byte instruction at `prepare_frame` is patched at song start.
For JPS v1 and capability `01h` it remains the original
`LDA ch1_volume`.  For capability `03h` it becomes a same-size jump to the
tremolo preparation routine.  Consequently disabled tremolo adds no
instruction, call, branch, or cycle to normal frame preparation.  The
64-byte sample loop is neither moved semantically nor changed byte-for-byte.

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

The existing `ENV2_FLAGS` byte uses only its low nibble.  In the experimental
build, packet depth bits 2–3 are shifted into internal flag bits 4–5, already
in table-page-offset form (`00h`, `10h`, `20h`, or `30h`).  No new per-channel
byte is required.  New persistent state is exactly the two-byte shared phase;
scratch uses registers which normal preparation reloads before entering the
sample loop.

The phase table is consulted before the increment, so target frame zero uses
the same phase as `simulate_tremolo(..., start_frame=0)`.  The phase advances
even when all three current depths are zero in a capability `03h` song, which
keeps later notes aligned to absolute source time.

## Static resource guard

The M3 enhanced player is 4,537 bytes, ends at `12B9h`, has 49 declared state
bytes, and leaves 1,351 bytes before the `1800h` song window.  This experiment
may add:

- 64 bytes of fixed attenuation tables;
- exactly two declared state bytes;
- bounded parser, dispatch, and frame-boundary code, with no generated target
  code and no dynamic allocation;
- zero bytes per tone packet and therefore zero direct JPS growth.

Before acceptance, the assembled map must still end below `1800h`, declared
state must be exactly 51 bytes, and the existing stack/JPS size guards remain
unchanged.  These are limits to measure, not permission to consume all 1,351
available bytes.

## Cycle guard

The intended implementation does one phase lookup/update and at most three
clamped table subtractions at the 50 Hz boundary.  A conservative instruction
count is below 450 additional 8080 cycles on an enabled frame, roughly 1.3% of
the nominal 34,000-cycle frame and well below the rough 3,800-cycle combined
orientation budget.  This estimate is not an acceptance result.

The C-cosim report must measure empty, all-zero-depth, one-depth, and
three-depth frames.  Envelope, tremolo, Escape polling, percussion, and row
parsing share the single G2 budget: effective sample rate must remain at least
90% of the matching frozen baseline, full-song duration must remain within 1%
of source timing, and the phase-step table must match the selected measured
sample rate.  No reduction of pitch range, drum concurrency, Escape handling,
or the sample hot loop is permitted.

## Guarded implementation order

1. Extend pure host encoding and malformed-packet tests.  Prove capability
   `01h` bytes remain identical and `03h` is rejected by the old player.
2. Add the separate `-P5=1` dispatch/parser state while keeping both disabled
   compatibility profiles cycle-identical.
3. Add the shared-phase preparation routine and a synthetic target fixture.
   Compare every frame's three prepared mixer levels with the Python model.
4. Generate a report containing binary/map growth, state, hot-loop hash,
   exact enabled/disabled cycle distributions, effective rates, duration, and
   JPS sizes.
5. Render a bounded real representative excerpt with depth zero and the
   selected depth for host/reference comparison.
6. Perform CS00000 A/B listening before enabling tremolo in general library
   conversion.

Host policy remains disabled during steps 1–5.  A nonzero depth may eventually
be emitted only for a direct AM path, a change which survives exact 4-bit
quantization, and a joint envelope/tremolo fit which passes the recorded
quality gates.  Song-specific overrides are forbidden.

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
