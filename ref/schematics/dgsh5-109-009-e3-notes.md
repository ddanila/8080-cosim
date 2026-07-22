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
| 1 | 1 overview + 8 overlapping details | CPU, bus, decode PROMs, ROM, PIC/PPI/PIT/USART, serial and inter-sheet continuations reviewed against `.006` and the board model. Exact-revision continuations into sheet 3 are adopted; one stale tape interrupt label remains explicitly unresolved. |
| 2 | 1 overview + 8 overlapping details | DRAM, video, timing and analog boundary reviewed against `.006` and the board model. No wholesale functional replacement is present; native reads correct individual inferred nets and values listed below. |
| 3 | 1 overview + 4 overlapping details | Complete VG93 floppy controller, clock/data separator, write precompensation, drive buffers/status and X4 interface transcribed. This sheet replaces the `.006` tape subsystem rather than supplementing it. |

The detail tiles cover every circuit region. The faint sheet-2 overview is a
layout oracle only; its eight native detail frames are the pin-level evidence.

## Sheets 1–2 divergence audit

| region | `.009` result and source-model disposition | evidence artifact |
| --- | --- | --- |
| D6/D8/D13 memory decode | Direct D6.12→R11→D8.15 and D6.9→R14→D13.1; no hidden inverter. Physical PROM truth and owner continuity agree. | `docs/d6-physical-decode.md` |
| low-I/O decode | D6.10 `REV` enables tied D9 inputs through the exact 1 kΩ pull-up branch. | `docs/io-decode-boundary.md` |
| D26 floppy controls | PC2/PC4/PC5/PC6 continue as MOTOR EN, FM/MFM, D_SEL and S.SEL. PC3 is the 5/8-inch clock selection. | `ref/schematics/fdc-x4-ngmd-wire-map.md` |
| direct FDC host bus | Sheet-1 D0–D7 bundle continues directly to D93.7–.14; the inference-era D100 DAL transceiver is disproved. | `docs/fdc-bus-polarity.md` |
| serial/PIC | RxRDY→IR2, shared TxC/RxC baud path, SYNDET switch path and X3/X5/X6 handoff are source-closed. IR4 still says `(3) TAPE RUN INT`, but replacement sheet 3 has no mate; it remains a stale-sheet boundary, not an invented FDC IRQ. | `docs/serial-handoff.md` |
| sheet-2 memory read | Native `-MRD` arrivals close D33.3 and D92.13 onto MEMR, including the factory W11 continuation. | `docs/memory-timing-boundary.md` |
| sheet-2 clocks | Native labels plus owner continuity close D40.11 onto the D59.5 mux-enable source, tied D92.2/.3 timing inputs, and the sheet-3 D95.5/.6 1 MHz continuation. This exposes a pending atomic correction to the model's former `LATCH_B`/`VID_MUX_G` split and D92 `PHI2TTL` attribution. | `docs/d40-d59-d92-d95-1mhz-route.md` |
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
| D97/D102/D101 write precompensation | `fdc-write-precomp-map.md` |
| D99 one-shot timing | `fdc-d99-timing-map.md` |
| DRQ/INTRQ conditioner | `fdc-irq-conditioner-map.md` |
| exact-revision unused pins | `fdc-unused-pin-dispositions.md` |

Together these maps account for every functional D93 pin, all D95/D96/D98/D100/
D106 pins used by sheet 3, both D99 timing networks, and the locally drawn
D28/D97/D101/D102 sections. Drawing-internal R86/R94/R99 reference conflicts
are explicitly overridden only where registered target-board evidence is
stronger.

## Remaining boundaries after transcription

- D96.9 and D96.11 leave through distinct sheet-1 continuations whose remote
  endpoints are not uniquely visible; D100.9/.11 share a third unresolved
  sheet-1 control continuation. They require continuity, not schematic guesswork.
- D99.10 and the other remote D99 section pins remain traced only to sheet
  boundaries. D101.1/.3/.5/.6 remain the exact open precomp-support endpoints.
- X4.2–.5 retain revision/cable disposition because target sheet 3 omits them;
  X4.1–.6 are grouped returns on the НГМД side but unseen cable conductors are
  not invented.
- The factory sheet's reset label polarity and physical FDC clock/analog edge
  quality remain bring-up measurements, not missing transcription.

These are external-evidence boundaries. All source-visible `.009` corrections
are represented or explicitly dispositioned; this audit supplies no authority
to fabricate while the separate P0 connectivity and routing gates remain open.
