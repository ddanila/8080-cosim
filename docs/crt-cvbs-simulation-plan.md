# Juku composite-video and CRT model contract

Status: **GENERIC RECEIVER AND STATIC OUTPUT MODEL IMPLEMENTED; PHYSICAL
VIDEO_OUT WAVEFORM AND END-TO-END ACCEPTANCE OPEN**.

[PLAN.md](../PLAN.md) owns project priorities and release gates. This contract
covers the path from source-complete video logic through loaded `VIDEO_OUT`
samples to receiver lock and monochrome display:

```text
physical timing + framebuffer slots → serializer + D34 picture/sync
→ resistor/transistor output stage + monitor load → voltage samples
→ synchronization receiver → recovered pixels → CRT presentation
```

## Authority and recorded provenance

This repository owns historical evidence, Juku nets/timing, component values,
waveform generation and physical acceptance. The
[decoder fork](https://github.com/ddanila/famicom-rf-hackrf-decoder) owns generic
sample ingestion, synchronization, DSP and display. Preserve its original
Famicom RF/IQ path alongside the separate baseband path. Upstream is
https://github.com/GOROman/famicom-rf-hackrf-decoder (MIT at the recorded fork point).

The [baseline report](crt-decoder-baseline.md) binds the recorded qualification:

| Scope | Recorded revision |
| --- | --- |
| Unmodified fork point | `6cce72d4a0e35ed364d086470191d61e3f6cd116` |
| Float32 baseband input (WP1) | `d383beb3dd038154364fb76f993ad32d12fe2d44` |
| Parameterized receiver (WP2) | `10bfa4b9ae6c1ce071633459170b067fe3e2d91f` |
| Synthetic Juku-timing fixture (WP3) | `b1d62c085e416c80cff35d8a77a8fbc397eead51` |
| Juku raster source for that fixture | `eb4d6ab6777db3f97306c9111e9c723c97dcf750` |

These identify measured evidence, not a claim that every later fork revision
has been requalified. New integration reports must bind both decoder and
waveform-source revisions.

## Implemented and bounded results

| Layer | Evidence and limit |
| --- | --- |
| Receiver input/sync (WP0–WP2) | Recorded RF/IQ regression, float32 headless input, explicit timing profiles, measured lock telemetry and positive/negative synthetic fixtures; no guessed built-in Juku preset |
| Digital probes (WP3) | [Physical contributor probes](video-physical-probes.md) expose source-proved serializer/sync nodes with unresolved slot schedule marked; not a complete picture waveform |
| Raster timing (WP3) | [PIT report](video-pit-timing.md) executes the exact EKTA programming: 64 µs lines, 313-line frames and guarded D56 pulses; does not close physical framebuffer slots or D34_SIG |
| Synthetic receiver fixture (WP3) | Ideal five-bar timing fixture exercises the decoder; it is separate from HDL pixels and physical voltage |
| Output stage (WP4) | [Static model](x7-output-stage-model.md) checks topology and loaded/corner solves with an official TI LS86 comparison driver; not exact К555ЛП5 calibration or video |

The abstract `juku_top.vid_out` serializes framebuffer bits. It bypasses physical
sync summing and VT2, and must not be labeled `VIDEO_OUT` voltage.

## Sample-domain interface

The receiver consumes monotonically sampled baseband voltage, initially
little-endian float32. It recovers synchronization and pixels from samples;
row/column/framebuffer metadata must not supply hidden truth. Sidecars record
sample rate, format, scale/offset, impedance, source revision, generation/capture
command and whether the stream is synthetic, HDL-derived, circuit-modeled or
measured.

A timing profile supplies acquisition bounds and polarity, then the receiver
reports measured line/frame periods and lock state. Active-window hints apply
after lock. Output-stage voltage, receiver recovery and CRT presentation remain
independently testable; cosmetic effects are applied after neutral-image checks.

## Remaining work and gates

- [ ] Replace the simulation-only framebuffer read port only after the
  shared-DRAM video-slot schedule is evidence-complete.

The [slot audit](video-slot-timing-audit.md) owns the unresolved timing boundary.
Also close D34_SIG and its physical picture/sync behavior before generating a
complete source-derived waveform.

WP4 still requires an exact-device nonlinear D34 source or loaded measurement,
installed VT2 calibration and justified edge behavior. TI typical LS86 data is
comparison evidence and cannot establish К555ЛП5 equivalence. Include R62/R63/R64,
VT2, R65, supply and explicit 75-ohm/unterminated loads. C94 remains absent until
its population, value and endpoints are established. The factory display cable
is X6; connector continuity limits are in the
[identity audit](x6-x7-connector-identity-audit.md).

WP5 requires receiver lock from actual modeled `VIDEO_OUT` samples and recovered
active pixels matching the independent 9640-byte framebuffer oracle, with
measured timing/levels and a neutral display before CRT effects.

WP6 requires surviving-board or first-article captures of picture/sync, VT2 base
and terminated output. Record board/firmware state, probe/load setup, bandwidth,
attenuation, sample rate and grounding. Compare polarity, pulse periods/widths,
levels, edge shape and loading; adjust only parameters justified by evidence.
Physical discrepancies must remain explicit.

## Verification

From this repository root:

```sh
python3 scripts/report_crt_decoder_baseline.py
python3 scripts/report_video_physical_probes.py
python3 scripts/report_video_pit_timing.py
python3 scripts/model_x7_output_stage.py
python3 scripts/report_video_slot_timing_audit.py
```

The baseline writer validates the retained qualification record and its
agreement with this contract. It checks decoder digest syntax without
recomputing artifact hashes or rerunning decoder tests; see
[its verification limits](crt-decoder-baseline.md#command). The other writers
publish their local model and source checks with explicit scope limits. A static
float32 step fixture is not video. An image match does not prove electrical
levels, and plausible voltage levels do not prove receiver lock. Completion
requires source-complete pixels, loaded-waveform validation, end-to-end recovery,
preserved receiver regressions and corroborating physical capture or quantified
physical discrepancy evidence. Completed experiment logs remain in Git and the
hash-bound qualification records.
