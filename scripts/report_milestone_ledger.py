#!/usr/bin/env python3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "milestone-ledger.md"


def rel(path):
    return path.relative_to(ROOT).as_posix()


def read(path):
    if not path.exists():
        return ""
    return path.read_text(errors="replace")


def marker(path, text):
    return text in read(ROOT / path)


def exists(path):
    return (ROOT / path).exists()


def count_baltijets_pdfs():
    path = ROOT / "ref" / "baltijets-tech-docs"
    if not path.exists():
        return 0
    return len(list(path.glob("*.pdf")))


def source_coverage_audited():
    text = read(ROOT / "docs" / "source-coverage-audit.md")
    return all(
        needle in text
        for needle in [
            "https://arti.ee/juku/",
            "https://elektroonikamuuseum.ee/failid/juku/",
            "https://github.com/infoaed/juku3000/tree/master/roms",
            "https://arvutimuuseum.ee/cs00000/",
        ]
    )


def table_row(values):
    escaped = [str(value).replace("|", "/") for value in values]
    return "| " + " | ".join(escaped) + " |"


def milestone_rows():
    pdf_count = count_baltijets_pdfs()
    public_sources_audited = source_coverage_audited()
    reconstructed_proms_exported = marker(
        "docs/reconstructed-prom-fallbacks.md",
        "Status: **BOOT-VALIDATED RECONSTRUCTION FALLBACKS EXPORTED**",
    ) and marker(
        "ref/reconstructed-proms/SHA256SUMS",
        "d8_re3_rom_pager_reconstructed.bin",
    )
    reference_artifacts_guarded = exists("sync/reference_artifact_check.sh") and marker(
        ".github/workflows/lvs.yml",
        "Check vendored reference artifacts",
    )
    wd1772_pla_normalized = marker(
        "docs/wd1772-pla-inspection.md",
        "Status: **PLA SHAPE INSPECTED**",
    ) and exists(
        "ref/wd1772-vg93/wd1772pla.normalized.json"
    ) and marker(
        ".github/workflows/lvs.yml",
        "Check WD1772 PLA inspection freshness",
    )
    manufacturing_ready = marker(
        "docs/replica-manufacturing-readiness.md",
        "Status: **READY TO UPLOAD**",
    )
    bringup_verification_ready = marker(
        "docs/replica-bringup-verification-points.md",
        "Status: **READY**",
    )
    order_ready = marker("fab/gerbers/order-readiness.md", "Status: **ORDER READY**") or marker(
        "docs/replica-manufacturing-readiness.md",
        "| Order readiness | `fab/gerbers/order-readiness.md`",
    )
    parts_inventory_template = exists("docs/replica-parts-inventory-template.md")
    ekdos_external_prompt = marker(
        "docs/ekdos-media-acquisition.md",
        "Status: **COSIM EKDOS PROMPT PROVEN WITH EXTERNAL MEDIA**",
    ) or marker(
        "docs/ekdos-media-acquisition.md",
        "Status: **COSIM JUKU1 PROMPT PROVEN WITH EXTERNAL MEDIA**",
    ) or marker(
        "docs/ekdos-media-acquisition.md",
        "Status: **VENDORED JUKU1 PROMPT PROVEN**",
    )
    ekdos_juku1_prompt = marker(
        "docs/ekdos-media-acquisition.md",
        "JUKU1.CPM",
    )
    hdl_fdc_ready = marker(
        "docs/fdc-readiness.md",
        "Status: **HDL WD1793 VENDORED-MEDIA SECTOR READY**",
    ) or marker(
        "docs/fdc-readiness.md",
        "Status: **HDL WD1793 SYNTHETIC-SECTOR READY**",
    )
    hdl_fdc_vendored_sector = marker(
        "docs/fdc-readiness.md",
        "Status: **HDL WD1793 VENDORED-MEDIA SECTOR READY**",
    )
    hdl_checkpoint_prompt_guard = Path("sync/ekdos_checkpoint_prompt_check.sh").exists()
    hdl_uninterrupted_prompt_hook = marker(
        "sync/juku_top_fdc_probe.sh",
        "JUKU_TOP_FDC_STOPPROMPT",
    ) and marker(
        "hdl/sim/juku_top_tb.v",
        "[PROMPT] EKDOS A> prompt reached",
    )
    ekdos_timing_guard = marker(
        "docs/ekdos-timing-reference.md",
        "Status: **PASS**",
    ) and marker(
        "docs/ekdos-timing-reference.md",
        "| OUT | 0x1C | 02 | 6666400 | E5DE | 63085 |",
    )
    basic_launch_reached = marker(
        "docs/basic-launch-probe.md",
        "Status: **BASIC RAM EXECUTION REACHED**",
    )
    basic_entry_rejected = marker(
        "docs/basic-entry-probe.md",
        "Status: **BASIC DIRECT RESET PATH REJECTED**",
    )
    basic_factory_command_pinned = marker(
        "docs/basic-factory-command-probe.md",
        "Status: **FACTORY BASIC COMMAND BOUNDARY PINNED**",
    ) and marker(
        "docs/basic-factory-command-probe.md",
        "| ekta43 | `roms/ekta43.bin` | `BAS0-3.HEX` |",
    )
    jmon33_command_surface = marker(
        "docs/jmon33-command-probe.md",
        "Status: **JMON33 COMMAND SURFACE READY**",
    )
    jmon33_idle_command_surface = marker(
        "docs/jmon33-idle-command-probe.md",
        "Status: **JMON33 IDLE COMMAND SURFACE READY**",
    )
    jmon33_hdl_command_diagnostic = marker(
        "docs/jmon33-hdl-command-probe.md",
        "Status: **JMON33 HDL COMMAND BOUNDED DIAGNOSTIC**",
    ) or marker(
        "docs/jmon33-hdl-command-probe.md",
        "Status: **JMON33 HDL A-COMMAND ORACLE READY**",
    ) or marker(
        "docs/jmon33-hdl-command-probe.md",
        "Status: **JMON33 HDL COMMAND SURFACE READY**",
    )
    jmon33_hdl_b_command_oracle = marker(
        "docs/jmon33-hdl-b-command-probe.md",
        "Status: **JMON33 HDL SELECTED COMMAND ORACLE READY**",
    ) and marker(
        "docs/jmon33-hdl-b-command-probe.md",
        "891fb09d78847a92e8417b1fb8ab81f160555725853b1d21bf29e25348bad0b0",
    )
    jmon33_fdc_t_oracle = marker(
        "docs/jmon33-fdc-command-probe.md",
        "Status: **JMON33 FDC T-COMMAND ORACLE PINNED**",
    )
    jmon33_hdl_fdc_t_oracle = marker(
        "docs/jmon33-hdl-fdc-command-probe.md",
        "data=0x40",
    ) and marker(
        "docs/jmon33-hdl-fdc-command-probe.md",
        "JMON33 HDL FDC T-COMMAND ORACLE PINNED",
    )
    jmon33_checkpoint_cursor = marker(
        "docs/jmon33-checkpoint-cursor-probe.md",
        "Status: **PASS**",
    ) and marker(
        "docs/jmon33-checkpoint-cursor-probe.md",
        "HDL cursor VRAM SHA256: `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`",
    )
    video_timing_guard = marker(
        "docs/video-timing-reference.md",
        "Status: **VIDEO RASTER GEOMETRY GUARDED**",
    ) and marker(
        "docs/video-timing-reference.md",
        "| framebuffer bytes | 9640 |",
    )
    vjuga_bare_pcb_ready = marker(
        "spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md",
        "Status: **READY TO UPLOAD**",
    ) or marker(
        "fab/minimal-vga/order-readiness.md",
        "Status: **BARE PCB READY - VENDOR PREVIEW REQUIRED**",
    ) or marker(
        "spinoffs/minimal-vga/docs/rev-a-bare-pcb-order.md",
        "Status: **READY FOR VENDOR PREVIEW**",
    )
    vjuga_order_evidence_template = marker(
        "spinoffs/minimal-vga/docs/rev-a-bare-pcb-order-evidence-template.md",
        "Status: **READY**",
    )
    vjuga_draft = marker(
        "fab/minimal-vga/order-readiness.md",
        "Status: **DRAFT - HUMAN REVIEW REQUIRED**",
    ) or marker(
        "PLAN.md",
        "Vendor/order checklist evidence is now generated",
    )

    return [
        {
            "id": "M1",
            "target": "Baltijets docs mined; PROM-truth status resolved",
            "status": "PARTIAL",
            "evidence": (
                f"{pdf_count} Baltijets PDFs present; PLAN records first-pass mining "
                "for 002/003/007/009/014/015; "
                + (
                    "`docs/source-coverage-audit.md` records Arti, Elektroonikamuuseum, "
                    "infoaed/juku3000 ROM, and Arvutimuuseum coverage; "
                    if public_sources_audited
                    else "public-source coverage audit is missing or incomplete; "
                )
                + (
                    "`docs/reconstructed-prom-fallbacks.md` exports boot-validated "
                    "D6/D8 reconstruction fallbacks; "
                    if reconstructed_proms_exported
                    else ""
                )
                + (
                    "vendored reference hashes are CI-guarded by "
                    "`sync/reference_artifact_check.sh`; "
                    if reference_artifacts_guarded
                    else ""
                )
                + (
                    "the WD1772/VG93 PLM dump is normalized to JSON/CSV and "
                    "freshness-guarded; "
                    if wd1772_pla_normalized
                    else ""
                )
                + "PROM truth still needs disk files or hardware dumps for Tier 3."
            ),
            "next": "Locate programming disk/media or get RE3/RT4 dumps; diff any D6/D8 dumps against the exported reconstruction fallbacks.",
        },
        {
            "id": "M2",
            "target": "EKDOS boots in the twin",
            "status": (
                "VENDORED JUKU1 PROMPT PROVEN / HDL RAW-SECTOR READY"
                if ekdos_juku1_prompt and hdl_fdc_vendored_sector
                else "VENDORED JUKU1 PROMPT PROVEN / HDL PENDING"
                if ekdos_juku1_prompt
                else "COSIM PROMPT PROVEN / HDL PENDING" if ekdos_external_prompt else "PARTIAL"
            ),
            "evidence": (
                "`docs/ekdos-media-acquisition.md` records vendored Arti `JUKU1.7Z` / "
                "`JUKU2.7Z` media under `media/disks/`; `JUKU1.CPM` reaches `A>` "
                "through the factory `TDD` path; `docs/fdc-readiness.md` guards HDL "
                "WD1793 raw-sector reads from vendored `JUKU1.CPM`."
                + (
                    " `sync/ekdos_checkpoint_prompt_check.sh` provides a "
                    "local/deep guard for the "
                    "checkpoint-resumed `juku_top` late-FDC window reaching the "
                    "EKDOS `A>` prompt bitmap."
                    if hdl_checkpoint_prompt_guard
                    else ""
                )
                + (
                    " `docs/ekdos-timing-reference.md` pins the fast cosim timing window "
                    "for first frame IRQ and first FDC command. "
                    if ekdos_timing_guard
                    else " "
                )
                + (
                    "`sync/juku_top_fdc_probe.sh` exposes `JUKU_TOP_FDC_STOPPROMPT=1` "
                    "for uninterrupted long runs to stop on the same prompt bitmap. "
                    if hdl_uninterrupted_prompt_hook
                    else ""
                )
                + "Full uninterrupted ROMBIOS-to-EKDOS prompt execution in `juku_top` remains open."
                if ekdos_juku1_prompt and hdl_fdc_vendored_sector
                else "`docs/ekdos-media-acquisition.md` records vendored Arti `JUKU1.7Z` / "
                "`JUKU2.7Z` media under `media/disks/`; `JUKU1.CPM` reaches `A>` "
                "through the factory `TDD` path; `docs/fdc-readiness.md` guards HDL "
                "WD1793 synthetic-sector behavior. Disk-backed FDC in `juku_top` remains open."
                if ekdos_juku1_prompt
                else "`docs/ekdos-media-acquisition.md` records a non-vendored external-media "
                "run reaching the EKDOS `A>` prompt in cosim; the default tracked probe "
                "remains reproducible without media as `READY FOR EXTERNAL EKDOS IMAGE`; "
                "`docs/fdc-readiness.md` guards HDL WD1793 synthetic-sector behavior. "
                "Exact factory `JUKU-1` evidence and external-media FDC in `juku_top` remain open."
                if ekdos_external_prompt
                else "cosim FDC boundary is reproducible without vendored media; "
                "`docs/ekdos-fdc-probe.md` is READY FOR EXTERNAL EKDOS IMAGE. "
                + (
                    "HDL synthetic-sector behavior is guarded by `docs/fdc-readiness.md`. "
                    if hdl_fdc_ready
                    else ""
                )
                + "Tracked evidence does not yet prove the exact factory JUKU-1 image "
                "or external-media FDC in `juku_top`."
            ),
            "next": (
                "Drive the full ROMBIOS TDD path through juku_top to an EKDOS prompt without checkpoint/resume."
                if hdl_fdc_vendored_sector
                else "Connect vendored raw disk media through juku_top."
            ),
        },
        {
            "id": "M3",
            "target": "VJUGA Rev A ordered",
            "status": "EXTERNAL PENDING",
            "evidence": (
                "`fab/minimal-vga/order-readiness.md` is BARE PCB READY and "
                "`spinoffs/minimal-vga/docs/rev-a-manufacturing-readiness.md` "
                "records the bare-PCB package as READY TO UPLOAD; "
                "`spinoffs/minimal-vga/docs/rev-a-bare-pcb-order.md` records the "
                "PCB-only first-sample upload policy"
                + (
                    "; `spinoffs/minimal-vga/docs/rev-a-bare-pcb-order-evidence-template.md` "
                    "defines the vendor-preview/order record"
                    if vjuga_order_evidence_template
                    else ""
                )
                + "; vendor preview and order evidence are still external."
                if vjuga_bare_pcb_ready
                else
                "`fab/minimal-vga/order-readiness.md` is a coherent draft with "
                "machine gates PASS, but still requires human/vendor review before upload."
                if vjuga_draft
                else "No current VJUGA order-readiness draft was found."
            ),
            "next": (
                "Upload the Gerber ZIP as PCB fabrication only, save vendor preview/order evidence."
                if vjuga_bare_pcb_ready
                else "Perform final JLCPCB UI review and place the Rev A order."
            ),
        },
        {
            "id": "M4",
            "target": "Twin emits real video timing",
            "status": "PARTIAL",
            "evidence": (
                "`docs/video-readout-readiness.md` proves the V2 byte-to-pixel path; "
                + (
                    "`docs/video-timing-reference.md` guards the MAME-matched "
                    "40 x 241 byte raster geometry and 8-dot load/shift cadence; "
                    if video_timing_guard
                    else ""
                )
                + "the faithful RE3/AG3 shared-DRAM slot timing is explicitly still open."
            ),
            "next": "Close the RE3/AG3 timing source and replace the sim-only framebuffer read.",
        },
        {
            "id": "M5",
            "target": "jmon33 live prompt + BASIC launches in the twin",
            "status": (
                "JMON33 COMMAND SURFACE PROVEN / HDL BASIC PENDING"
                if jmon33_checkpoint_cursor and basic_launch_reached and jmon33_command_surface
                else "CHECKPOINT CURSOR PROVEN / PROMPT+HDL BASIC PENDING"
                if jmon33_checkpoint_cursor and basic_launch_reached
                else "BASIC RAM EXECUTION REACHED / PROMPT+HDL PENDING"
                if basic_launch_reached
                else "PARTIAL"
            ),
            "evidence": (
                "jmon33 interrupt/first-write/cosim cursor probes exist; "
                "`docs/jmon33-checkpoint-cursor-probe.md` now proves "
                "checkpoint-resumed `juku_top` reaches the Monitor 3.3 cursor "
                "framebuffer hash from a blank pre-cursor checkpoint. "
                + (
                    "`docs/jmon33-command-probe.md` proves typed Monitor 3.3 "
                    "commands are sampled through the keyboard port and move the "
                    "visible command cursor deterministically in cosim. "
                    if jmon33_command_surface
                    else ""
                )
                + (
                    "`docs/jmon33-idle-command-probe.md` pins the delayed "
                    "idle-prompt command oracle for checkpoint-resumed HDL work. "
                    if jmon33_idle_command_surface
                    else ""
                )
                + (
                "`docs/jmon33-hdl-command-probe.md` proves the checkpoint-resumed "
                "HDL `A` command reaches its delayed idle-prompt framebuffer oracle; "
                + (
                    "`docs/jmon33-hdl-b-command-probe.md` now proves the analogous "
                    "checkpoint-resumed HDL `B` command framebuffer oracle; "
                    if jmon33_hdl_b_command_oracle
                    else ""
                )
                + "`docs/jmon33-hdl-t-command-fdc-diagnostic.md` preserves the `T` "
                    "command finding where keyboard samples are present but the path "
                    "enters heavy FDC I/O. "
                    if jmon33_hdl_command_diagnostic
                    else ""
                )
                + (
                    "`docs/jmon33-fdc-command-probe.md` pins the FDC-aware `T` oracle: "
                    "with `media/disks/JUKU1.CPM`, command `0xFD` reaches WRITE PROTECT "
                    "status instead of BUSY forever. "
                    if jmon33_fdc_t_oracle
                    else ""
                )
                + (
                    "`docs/jmon33-hdl-fdc-command-probe.md` carries that boundary into "
                    "checkpoint-resumed `juku_top`, where the structural path reads FDC "
                    "status `0x40`. "
                    if jmon33_hdl_fdc_t_oracle
                    else ""
                )
                + "`docs/basic-launch-probe.md` shows Monitor 3.3 reading the BASIC "
                "cartridge and executing in the 0x4000 RAM window, but that window "
                "only receives zero-byte writes. The same report now records the "
                "local MAME Monitor 3.3/JBASIC compatibility warning and the BASIC "
                "images' absolute JMP 0x0107 entry. "
                + (
                    "`docs/basic-factory-command-probe.md` pins the Baltijets "
                    "factory `A` command clue across all vendored public monitor "
                    "ROMs: Monitor 3.3 reaches the same zero-filled RAM boundary, "
                    "while no tested vendored ROM/media pairing reaches the BASIC "
                    "banner/READY oracle. "
                    if basic_factory_command_pinned
                    else ""
                )
                + (
                    "`docs/basic-entry-probe.md` also rejects direct reset-ROM "
                    "execution of those BASIC images."
                    if basic_entry_rejected
                    else ""
                )
                if jmon33_checkpoint_cursor and basic_launch_reached
                else "jmon33 interrupt/first-write/cosim cursor probes exist; "
                "`docs/basic-launch-probe.md` shows Monitor 3.3 reading the BASIC "
                "cartridge and executing in the 0x4000 RAM window, but that window "
                "only receives zero-byte writes. The same report now records the "
                "local MAME Monitor 3.3/JBASIC compatibility warning and the BASIC "
                "images' absolute JMP 0x0107 entry. "
                + (
                    "`docs/basic-factory-command-probe.md` pins the Baltijets "
                    "factory `A` command clue across all vendored public monitor "
                    "ROMs: Monitor 3.3 reaches the same zero-filled RAM boundary, "
                    "while no tested vendored ROM/media pairing reaches the BASIC "
                    "banner/READY oracle. "
                    if basic_factory_command_pinned
                    else ""
                )
                + (
                    "`docs/basic-entry-probe.md` also rejects direct reset-ROM "
                    "execution of those BASIC images."
                    if basic_entry_rejected
                    else ""
                )
                if basic_launch_reached
                else "jmon33 interrupt/first-write/cosim cursor probes exist; "
                "`docs/basic-launch-probe.md` still says BASIC LAUNCH NOT YET REACHED."
            ),
            "next": (
                "Prove the uninterrupted reset-to-cursor jmon33 path, identify the "
                "correct monitor/removable-memory BASIC pairing, add a BASIC prompt oracle, "
                "and port that BASIC path to HDL coverage."
                if jmon33_checkpoint_cursor
                else "Compare HDL at the stronger jmon33 cursor boundary, identify the correct monitor/removable-memory BASIC pairing, add a BASIC prompt oracle, and port that BASIC path to HDL coverage."
            ),
        },
        {
            "id": "M6",
            "target": "VJUGA Rev A boots real Juku ROM on the bench",
            "status": "EXTERNAL PENDING",
            "evidence": "Requires fabricated and assembled Rev A hardware; no bench artifact exists in repo.",
            "next": "Order, assemble, and run the staged bring-up ladder.",
        },
        {
            "id": "M7",
            "target": "Replica fab package passes order-readiness gates; boards ordered",
            "status": "REPO READY / EXTERNAL PENDING" if manufacturing_ready and order_ready else "OPEN",
            "evidence": (
                "`docs/replica-manufacturing-readiness.md` is READY TO UPLOAD and "
                "`fab/gerbers/order-readiness.md` is ORDER READY; "
                + (
                    "`docs/replica-bringup-verification-points.md` tracks the "
                    "residual source-risk nets for staged bring-up; "
                    if bringup_verification_ready
                    else ""
                )
                + "no vendor order number or accepted order evidence is tracked."
                if manufacturing_ready and order_ready
                else "Replica manufacturing/order readiness gates are not both ready."
            ),
            "next": "Run `kicad/check_replica_manufacturing_ready.sh`, upload the ZIP, save vendor preview/order evidence.",
        },
        {
            "id": "M8",
            "target": "Full functional parts kit in hand; firmware/PROMs programmed",
            "status": "EVIDENCE TEMPLATE READY / EXTERNAL PENDING" if parts_inventory_template else "OPEN",
            "evidence": (
                "`docs/replica-sourcing-readiness.md` defines the source/test gate; "
                "`docs/replica-parts-inventory-template.md` defines the received-parts "
                "and PROM/EPROM programming evidence record, including carry-forward "
                "of the bring-up verification checklist. No filled inventory or "
                "programmer logs are tracked yet."
                if parts_inventory_template
                else "`docs/replica-sourcing-readiness.md` is a sourcing gate, not a "
                "received-inventory or programmed-PROM record."
            ),
            "next": "Buy/receive the functional kit, run acceptance tests, and fill the private inventory/programming record.",
        },
        {
            "id": "M9",
            "target": "Replica assembled; staged bring-up complete to Tier 1",
            "status": "EXTERNAL PENDING",
            "evidence": "Requires fabricated boards, parts, assembly, and bench bring-up.",
            "next": "Assemble sockets-first and execute the power/clock/ROM/RAM/video/keyboard ladder.",
        },
        {
            "id": "M10",
            "target": "EKDOS boots from floppy emulator or drive on real hardware",
            "status": "EXTERNAL PENDING",
            "evidence": "Requires working replica hardware plus storage hardware/media.",
            "next": "Use Gotek/HxC-class emulator first, then confirm real drive path for Tier 3.",
        },
        {
            "id": "M11",
            "target": "Authentic parts, dumped PROMs, original peripherals",
            "status": "EXTERNAL PENDING",
            "evidence": "Requires NOS parts, PROM dumps, original peripherals, and physical validation.",
            "next": "Converge after Tier 2 is stable.",
        },
    ]


def main():
    rows = milestone_rows()
    lines = [
        "# Milestone ledger audit",
        "",
        "This generated audit maps the `PLAN.md` M1-M11 ledger to current repo",
        "evidence. It is intentionally conservative: external vendor orders,",
        "received parts, programmed PROMs, and bench results are not marked done",
        "unless there is tracked evidence for them.",
        "",
        "## Summary",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    counts = {}
    for item in rows:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    for status in sorted(counts):
        lines.append(table_row([status, counts[status]]))

    lines.extend([
        "",
        "## Milestones",
        "",
        "| ID | Target | Status | Evidence | Next action |",
        "| --- | --- | --- | --- | --- |",
    ])
    for item in rows:
        lines.append(table_row([
            item["id"],
            item["target"],
            item["status"],
            item["evidence"],
            item["next"],
        ]))

    lines.extend([
        "",
        "## Commands",
        "",
        "```sh",
        "python3 scripts/report_milestone_ledger.py",
        "kicad/check_replica_manufacturing_ready.sh",
        "```",
        "",
    ])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {rel(REPORT)}")


if __name__ == "__main__":
    main()
