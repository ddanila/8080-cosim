# JPS v2 pitch and vibrato contract

Status: implemented held-note pitch and runtime vibrato in the reusable library
player. The complete capability-05 At Doom's Gate payload has physical listening
evidence. Combined capability-07 has synthetic timing/compatibility evidence;
that does not extend the physical qualification to every feature combination.
[OPL-PLAN-STATUS.json](OPL-PLAN-STATUS.json) owns delivery and remaining gates.

## Scope and evidence

This slice has two deliberately separate parts:

1. Preserve source frequency-register changes while a selected logical note
   remains keyed.  This reuses an existing JPS v2 legato tone packet and adds
   no target instruction or state.
2. Approximate only conservative direct common-pitch OPL vibrato with one
   shared eight-position LFO and a host-precomputed phase-step delta.  It does
   not turn FM-modulator-only VIB or one-sided additive VIB into whole-note
   pitch modulation.

[The source analysis](OPL-PITCH-M5.json) records direct common-pitch
candidates, logical layering, three-voice allocation and held-key events that
retain target-channel ownership. Protected-v1 onset regressions remain zero.
Target execution and physical qualification are established separately by the
evidence below.

## Compatibility boundary

Runtime library support uses `-P2=1 -P4=1 -P6=1 -P7=1`; `-P2=1` selects
the library player. Add `-P5=1` for tremolo.
JPS v2 capability bit 2 means bounded pitch/vibrato.
The accepted capability combinations are:

- `01h`: fitted envelopes;
- `03h`: fitted envelopes plus tremolo;
- `05h`: fitted envelopes plus pitch/vibrato;
- `07h`: fitted envelopes, tremolo, and pitch/vibrato.

Bit 2 cannot appear without bit 0.  Players which do not implement bit 2 must
reject `05h` and `07h` before touching the PIT.  A capability-`05h` player
must reject tremolo packet bits, and every player must reject packet fields
which were not advertised.  JPS v1 and capability `01h` retain their exact
existing parser and frame profiles.

Held-note pitch automation does not require capability bit 2 by itself.  It is
already exactly expressible as a normal nonzero JPS v2 tone packet with the
high phase-step legato bit set.  The existing parser replaces `chN_step` and
the packet settings without resetting the phase accumulator or envelope.
Host conversion must emit such a packet only when the selected note still
owns the same target channel.

## Packet encoding

The first five bytes of every nonzero tone packet retain their current layout.
Byte 4 becomes:

| Bit | Meaning |
|---:|---|
| 0 | release rate code bit 2 |
| 1 | sustain while keyed (`EGT`) |
| 2–3 | tremolo depth `0..3` |
| 4–5 | vibrato mode: `0` off, `1` shallow, `2` deep, `3` invalid |
| 6–7 | reserved; must be zero |

Mode zero leaves the packet exactly five bytes.  Mode one or two appends one
byte encoding `peak_step_delta - 1`, so the representable host-precomputed
positive magnitude is `1..256`.  The conditional byte is present only under
capability bit 2.  This covers the complete 15-bit phase-step range without
runtime multiplication and avoids charging non-vibrato packets.

The score-side record is `opl_vibrato` adjacent to
`opl_envelope`, containing source mode (`shallow` or `deep`) and the already
resolved `peak_step_delta` in `1..256`.  The compiler must reject booleans,
unknown fields, zero deltas, mode 3, vibrato on key-off, or a field on a song
without JPS v2 envelopes.  Omitting it is byte-identical mode zero.

Preflight must walk the conditional byte and prove, for every vibrato packet:

- the base step is nonzero and below `8000h` after removing the legato bit;
- `base - peak_delta` remains positive;
- `base + peak_delta` remains below `8000h`;
- mode and capability agree;
- the row and JPS image remain bounded.

Malformed input is rejected before playback rather than clipped at runtime.
This preserves the qualified low/high frequency range and makes target
underflow or 15-bit overflow impossible in the hot path.

## Exact target semantics

The host and pinned oracle establish Nuked's eight positions as
`0,+half,+full,+half,0,-half,-full,-half`.  At the DOOM OPL clock, one cycle
is 6.068835788 Hz.  The target uses:

- one 16-bit unsigned shared phase reset to zero at song start;
- phase increment `7955` (`1F13h`) once per rendered music frame;
- table index `phase >> 13`;
- the serialized peak delta and a right shift for half positions;
- a temporary `base step +/- delta` loaded for the next sample batch.

`chN_step` remains the immutable base between explicit source pitch events.
Vibrato must never write the temporary result back to it, so there is no mean
pitch drift.  Frame zero consults phase zero before incrementing.  The shared
phase advances in every capability-bit-2 song even when all current modes are
off, preserving absolute source-LFO alignment.

A legato pitch packet replaces the base step and current precomputed vibrato
delta together.  It does not reset the shared LFO, sample phase accumulator,
or envelope.  Key-off retains vibrato through the release tail, matching the
OPL phase generator. Release completion clears the base step, volume and
envelope stage; the vibrato preparation routine returns a zero step for that
inactive channel. The pitch wrapper clears the stored feature flags and delta
when the base step reaches zero, including an immediate key-off.

Global depth or operator VIB changes made while a key is held must become a
legato update at the next representable 50 Hz frame, or be reported as
unsupported.  The importer may not silently retain a stale delta.

## Resource and cycle guards

Runtime vibrato adds two shared phase bytes and one delta byte per channel;
existing `chN_step` words provide the base. No multiplication, allocation or
sample-loop work is introduced. Pitch-only runtime declares 54 state bytes and
the combined tremolo/vibrato build declares 56; maps and exact timing are in
[OPL-VIBRATO-TARGET-M5.json](OPL-VIBRATO-TARGET-M5.json).

All effects, parsing, percussion and Escape share the
[combined feasibility budget](OPL-REDUCTION-PLAN.md). Player end stays below
`1800h`; JPS size, worst frames, phase-table rate and complete-song duration
need measured evidence. Held-pitch-only automation adds row parsing but still
requires its own longest-track size/timing checks.

## Regression and rollback rules

Delivery requires exact parser/target agreement and the shared size, state,
timing and listening gates in [the reduction contract](OPL-REDUCTION-PLAN.md).
Held-pitch automation must also fit the longest track. Mixed or indirect
source pitch paths retain the previous conversion and are reported as unsupported.
If runtime vibrato fails qualification, retain host-baked held pitch where
qualified; capability `03h`, `01h`, and JPS v1 remain available fallbacks.

## Build and qualification boundaries

`build_jukupoly.py` encodes and validates vibrato JPS images, but its standalone
COM assembly path still rejects pitch/vibrato. The reusable library builder
`build_doom_library.build_player` supplies the runtime feature definitions.
Parser-only `-P6=1` fixtures do not apply vibrato; playback requires `-P7=1` too.

| Evidence | What it proves |
| --- | --- |
| [Held-pitch report](OPL-PITCH-REAL-M5.json) | Full-track legato automation, calibration, size and cycle measurements without runtime vibrato |
| [Parser report](OPL-VIBRATO-PARSER-M5.json) | Conditional-byte synchronization, strict capability/bounds checks and bounded state |
| [Target report](OPL-VIBRATO-TARGET-M5.json) | Exact shared-phase temporary steps, no drift, reset isolation, combined timing and compatibility |
| [Real report](OPL-VIBRATO-REAL-M5.json) and [full-track report](OPL-VIBRATO-FULL-M5.json) | Generic direct-VIB decisions, retained onsets, serialized bounds, calibrated timing and render identities |
| [Physical record](sessions/cs00000-jukupoly-m6-physical/README.md) | Delivered complete At Doom's Gate listening and Escape/CP/M behavior on CS00000 |

Source registers determine shallow/deep deltas; mixed or indirect paths are
reported and omitted. Legato setting changes preserve ownership, phase and
envelope. Recalibration must regenerate both base steps and deltas from source;
changing batch counts or declared rates alone would detune the score.

Run `sync/jukupoly_check.sh` and `sync/jukupoly_library_check.sh` for semantic
and preflight regressions. Use the linked report writers to verify measured
artifacts; physical conclusions stay limited to the exact tested payloads.
