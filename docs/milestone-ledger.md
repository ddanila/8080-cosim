# Milestone ledger audit

This generated audit maps the `PLAN.md` M1-M11 ledger to current repo
evidence. It is intentionally conservative: external vendor orders,
received parts, programmed PROMs, and bench results are not marked done
unless there is tracked evidence for them.

## Summary

| Status | Count |
| --- | ---: |
| BASIC RAM EXECUTION REACHED / PROMPT+HDL PENDING | 1 |
| EVIDENCE TEMPLATE READY / EXTERNAL PENDING | 1 |
| EXTERNAL PENDING | 5 |
| PARTIAL | 2 |
| REPO READY / EXTERNAL PENDING | 1 |
| VENDORED JUKU1 PROMPT PROVEN / HDL RAW-SECTOR READY | 1 |

## Milestones

| ID | Target | Status | Evidence | Next action |
| --- | --- | --- | --- | --- |
| M1 | Baltijets docs mined; PROM-truth status resolved | PARTIAL | 16 Baltijets PDFs present; PLAN records first-pass mining for 002/003/007/009/014/015; `docs/source-coverage-audit.md` records Arti, Elektroonikamuuseum, infoaed/juku3000 ROM, and Arvutimuuseum coverage; PROM bytes still need disk files, hardware dumps, or accepted reconstruction. | Locate programming disk/media or get RE3/RT4 dumps. |
| M2 | EKDOS boots in the twin | VENDORED JUKU1 PROMPT PROVEN / HDL RAW-SECTOR READY | `docs/ekdos-media-acquisition.md` records vendored Arti `JUKU1.7Z` / `JUKU2.7Z` media under `media/disks/`; `JUKU1.CPM` reaches `A>` through the factory `TDD` path; `docs/fdc-readiness.md` guards HDL WD1793 raw-sector reads from vendored `JUKU1.CPM`. `docs/ekdos-timing-reference.md` pins the fast cosim timing window for first frame IRQ and first FDC command. Full ROMBIOS-to-EKDOS prompt execution in `juku_top` remains open. | Drive the full ROMBIOS TDD path through juku_top to an EKDOS prompt. |
| M3 | VJUGA Rev A ordered | EXTERNAL PENDING | `fab/minimal-vga/order-readiness.md` is a coherent draft with machine gates PASS, but still requires human/vendor review before upload. | Perform final JLCPCB UI review and place the Rev A order. |
| M4 | Twin emits real video timing | PARTIAL | `docs/video-readout-readiness.md` proves the V2 byte-to-pixel path; the faithful RE3/AG3 shared-DRAM slot timing is explicitly still open. | Close the RE3/AG3 timing source and replace the sim-only framebuffer read. |
| M5 | jmon33 live prompt + BASIC launches in the twin | BASIC RAM EXECUTION REACHED / PROMPT+HDL PENDING | jmon33 interrupt/first-write/cosim cursor probes exist; `docs/basic-launch-probe.md` shows Monitor 3.3 reading the BASIC cartridge and executing in the 0x4000 RAM window, but that window only receives zero-byte writes; EktaSoft 3.43m #0037 remains a compatibility boundary. | Compare HDL at the stronger jmon33 cursor boundary, add a BASIC prompt oracle, and port the Monitor 3.3 BASIC path to HDL coverage. |
| M6 | VJUGA Rev A boots real Juku ROM on the bench | EXTERNAL PENDING | Requires fabricated and assembled Rev A hardware; no bench artifact exists in repo. | Order, assemble, and run the staged bring-up ladder. |
| M7 | Replica fab package passes order-readiness gates; boards ordered | REPO READY / EXTERNAL PENDING | `docs/replica-manufacturing-readiness.md` is READY TO UPLOAD and `fab/gerbers/order-readiness.md` is ORDER READY; `docs/replica-bringup-verification-points.md` tracks the residual source-risk nets for staged bring-up; no vendor order number or accepted order evidence is tracked. | Run `kicad/check_replica_manufacturing_ready.sh`, upload the ZIP, save vendor preview/order evidence. |
| M8 | Full functional parts kit in hand; firmware/PROMs programmed | EVIDENCE TEMPLATE READY / EXTERNAL PENDING | `docs/replica-sourcing-readiness.md` defines the source/test gate; `docs/replica-parts-inventory-template.md` defines the received-parts and PROM/EPROM programming evidence record, including carry-forward of the bring-up verification checklist. No filled inventory or programmer logs are tracked yet. | Buy/receive the functional kit, run acceptance tests, and fill the private inventory/programming record. |
| M9 | Replica assembled; staged bring-up complete to Tier 1 | EXTERNAL PENDING | Requires fabricated boards, parts, assembly, and bench bring-up. | Assemble sockets-first and execute the power/clock/ROM/RAM/video/keyboard ladder. |
| M10 | EKDOS boots from floppy emulator or drive on real hardware | EXTERNAL PENDING | Requires working replica hardware plus storage hardware/media. | Use Gotek/HxC-class emulator first, then confirm real drive path for Tier 3. |
| M11 | Authentic parts, dumped PROMs, original peripherals | EXTERNAL PENDING | Requires NOS parts, PROM dumps, original peripherals, and physical validation. | Converge after Tier 2 is stable. |

## Commands

```sh
python3 scripts/report_milestone_ledger.py
kicad/check_replica_manufacturing_ready.sh
```
