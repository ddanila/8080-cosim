#!/usr/bin/env python3
import re
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


def summary_count(path, label, default):
    text = read(ROOT / path)
    match = re.search(rf"^- {re.escape(label)}: `([0-9,]+)`$", text, re.MULTILINE)
    if not match:
        return default
    return f"{int(match.group(1).replace(',', '')):,}"


def exists(path):
    return (ROOT / path).exists()


def count_baltijets_pdfs():
    path = ROOT / "ref" / "baltijets-tech-docs"
    if not path.exists():
        return 0
    return len(list(path.glob("*.pdf")))


def source_coverage_audited():
    text = read(ROOT / "docs" / "source-coverage-audit.md")
    return marker("docs/source-coverage-audit.md", "Status: **PASS**") and marker(
        ".github/workflows/lvs.yml",
        "Check source coverage audit freshness",
    ) and all(
        needle in text
        for needle in [
            "https://arti.ee/juku/",
            "https://elektroonikamuuseum.ee/failid/juku/",
            "https://github.com/infoaed/juku3000/tree/master/roms",
            "https://arvutimuuseum.ee/cs00000/",
            "https://github.com/vpyk/emu80v4",
            "Local WD1772 transistor/PLA files",
            "docs/public-manual-archive-inventory.md",
        ]
    )


def table_row(values):
    escaped = [str(value).replace("|", "/") for value in values]
    return "| " + " | ".join(escaped) + " |"


def milestone_rows():
    pdf_count = count_baltijets_pdfs()
    public_sources_audited = source_coverage_audited()
    owner_measurement_shortlist = marker(
        "docs/owner-measurement-shortlist.md",
        "Status: **READY**",
    ) and marker(
        "docs/owner-measurement-shortlist.md",
        "D94 pin 15 enable",
    )
    bringup_endpoint_count = summary_count(
        "docs/replica-bringup-verification-points.md",
        "Verification-point endpoints checked in PCB",
        "unknown",
    )
    board_endpoint_count = summary_count(
        "docs/replica-bringup-verification-points.md",
        "All board endpoints checked in source PCB",
        "unknown",
    )
    d2_constraints_generated = marker(
        "docs/d2-reconstruction-constraints.md",
        "Status: **D2 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**",
    ) and marker(
        ".github/workflows/lvs.yml",
        "docs/d2-reconstruction-constraints.md",
    )
    fdc_handoff_guarded = marker(
        "docs/fdc-hardware-handoff.md",
        "Status: **BUS-SIDE GUARDED / OWNER CONTINUITY REQUIRED**",
    ) and marker(
        ".github/workflows/lvs.yml",
        "Check owner measurement shortlist freshness",
    )
    serial_handoff_guarded = marker(
        "docs/serial-handoff.md",
        "Status: **SERIAL USART BEHAVIOR GUARDED / EXTERNAL LOOPBACK PENDING**",
    ) and marker(
        ".github/workflows/lvs.yml",
        "docs/serial-handoff.md",
    )
    beeper_handoff_guarded = marker(
        "docs/beeper-readiness.md",
        "Status: **DIGITAL BEEPER SOURCE + BOARD HANDOFF READY**",
    ) and marker(
        ".github/workflows/lvs.yml",
        "docs/beeper-readiness.md",
    )
    reconstructed_proms_exported = marker(
        "docs/reconstructed-prom-fallbacks.md",
        "Status: **BOOT-VALIDATED RECONSTRUCTION FALLBACKS EXPORTED**",
    ) and marker(
        "ref/reconstructed-proms/SHA256SUMS",
        "d8_re3_rom_pager_reconstructed.bin",
    )
    firmware_gap_ledger_ready = marker(
        "docs/firmware-gap-ledger.md",
        "Status: **PROM GAP LEDGER READY / DUMP TRUTH PENDING**",
    ) and marker(
        "docs/firmware-gap-ledger.md",
        "only the D6 and D8",
    ) and marker(
        "docs/firmware-gap-ledger.md",
        "D94 is not reconstructable",
    ) and marker(
        ".github/workflows/lvs.yml",
        "Check firmware gap ledger freshness",
    )
    re3_firmware_inspected = marker(
        "docs/re3-firmware-inspection.md",
        "Status: **PASS**",
    ) and marker(
        "ref/firmware/SHA256SUMS",
        "re3_dgsh5.106.113.hex",
    ) and marker(
        ".github/workflows/lvs.yml",
        "Check RE3 firmware inspection freshness",
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
    public_software_inventory = marker(
        "docs/public-software-archive-inventory.md",
        "Status: **PUBLIC SOFTWARE INVENTORY CLASSIFIED**",
    ) and marker(
        ".github/workflows/lvs.yml",
        "Check source coverage audit freshness",
    )
    public_manual_inventory = marker(
        "docs/public-manual-archive-inventory.md",
        "Status: **PUBLIC MANUAL ARCHIVE CLASSIFIED**",
    ) and marker(
        ".github/workflows/lvs.yml",
        "docs/public-manual-archive-inventory.md",
    )
    ekdos_source_vendored = exists("ref/ekdos-source/EKDOS30.ASM") and marker(
        "ref/ekdos-source/SHA256SUMS",
        "EKDOS30.ASM",
    )
    ekdos_source_inspected = marker(
        "docs/ekdos-source-inspection.md",
        "Status: **PASS**",
    ) and marker(
        ".github/workflows/lvs.yml",
        "Check EKDOS source inspection freshness",
    )
    vendored_disk_cataloged = marker(
        "docs/vendored-disk-catalog.md",
        "Status: **VENDORED DISK DIRECTORY INDEXED**",
    ) and marker(
        "docs/vendored-disk-catalog.md",
        "JBASIC.COM",
    ) and marker(
        ".github/workflows/lvs.yml",
        "Check vendored disk catalog freshness",
    )
    basic_disk_extracted = marker(
        "docs/basic-disk-extraction.md",
        "Status: **BASIC DISK FILES EXTRACTED**",
    ) and exists(
        "ref/extracted-software/JUKPROG2_JBASIC.COM"
    ) and exists(
        "ref/extracted-software/JUKPROG2_JBASIC_live_candidate.COM"
    ) and exists(
        "ref/extracted-software/JUKU1_JBASIC_raw_candidate.COM"
    ) and marker(
        ".github/workflows/lvs.yml",
        "Check BASIC disk extraction freshness",
    )
    ekdos_source_m1_phrase = ""
    ekdos_source_m2_phrase = ""
    if ekdos_source_inspected:
        ekdos_source_m1_phrase = (
            "Arti's EKDOS 2.30 source is vendored under `ref/ekdos-source/` "
            "and source-inspected; "
        )
        ekdos_source_m2_phrase = (
            " `docs/ekdos-source-inspection.md` confirms the EKDOS source's "
            "ROMBIOS floppy entries, 160 side-tracks, and 40-sector "
            "translation table."
        )
    elif ekdos_source_vendored:
        ekdos_source_m1_phrase = (
            "Arti's EKDOS 2.30 source is vendored under `ref/ekdos-source/`; "
        )
        ekdos_source_m2_phrase = (
            " `ref/ekdos-source/EKDOS30.ASM` preserves the EKDOS 2.30 BIOS "
            "source reference for monitor/FDC interface checks."
        )
    manufacturing_ready = marker(
        "docs/replica-manufacturing-readiness.md",
        "Status: **READY TO UPLOAD**",
    )
    bringup_verification_ready = marker(
        "docs/replica-bringup-verification-points.md",
        "Status: **READY**",
    )
    board_fidelity_gaps_cataloged = marker(
        "docs/board-fidelity-gap-ledger.md",
        "Status: **BOARD FIDELITY GAPS CATALOGED**",
    ) and marker(
        ".github/workflows/lvs.yml",
        "Check board fidelity gap ledger freshness",
    )
    order_ready = marker("fab/gerbers/order-readiness.md", "Status: **ORDER READY**") or marker(
        "docs/replica-manufacturing-readiness.md",
        "| Order readiness | `fab/gerbers/order-readiness.md`",
    )
    sourcing_ready = marker(
        "docs/replica-sourcing-readiness.md",
        "Status: **SOURCING READY / PROGRAMMING BLOCKED**",
    )
    dual_config_bom_ready = marker(
        "docs/replica-dual-config-bom.md",
        "Source: `kicad/juku.board.json`",
    ) and exists("docs/replica-dual-config-bom.csv")
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
    hdl_checkpoint_resume_ci_guard = marker(
        "docs/juku-top-checkpoint-resume.md",
        "Status: **PASS**",
    ) and marker(
        ".github/workflows/lvs.yml",
        "./sync/juku_top_checkpoint_resume_probe.py",
    )
    hdl_uninterrupted_prompt_hook = marker(
        "sync/juku_top_fdc_probe.sh",
        "JUKU_TOP_FDC_STOPPROMPT",
    ) and marker(
        "hdl/sim/juku_top_tb.v",
        "[PROMPT] EKDOS A> prompt reached",
    )
    hdl_verilator_fdc_prompt = marker(
        "docs/juku-top-fdc-verilator-probe.md",
        "Status: **HDL JUKU_TOP EKDOS PROMPT REACHED**",
    ) and marker(
        "docs/juku-top-fdc-verilator-probe.md",
        "FDC state line: `[FDCSTATE] data_reads=10752 buffer_pos=0 buffer_len=0`",
    )
    hdl_fdc_alignment = marker(
        "docs/juku-top-fdc-alignment.md",
        "Status: **HDL RESET RUN REACHES EKDOS A> PROMPT**",
    )
    hdl_prompt_ready = hdl_verilator_fdc_prompt and hdl_fdc_alignment
    hdl_prompt_guarded = hdl_prompt_ready and marker(
        "sync/juku_top_fdc_prompt_check.sh",
        "JUKU-TOP-FDC-PROMPT-CHECK: PASS",
    ) and marker(
        ".github/workflows/lvs.yml",
        "./sync/juku_top_fdc_prompt_check.sh",
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
    basic_low_stub_inspected = marker(
        "docs/basic-low-stub-inspection.md",
        "Status: **LOW STUB PATCHED / BODY MATCHES**",
    ) and marker(
        "docs/basic-low-stub-inspection.md",
        "Relocation Self-overwrite Audit",
    )
    basic_cartridge_length_audited = marker(
        "docs/basic-cartridge-length-audit.md",
        "Status: **CARTRIDGE BASIC TAIL PAGE MISSING**",
    ) and marker(
        "docs/basic-cartridge-length-audit.md",
        "Missing source bytes | `256`",
    ) and marker(
        "docs/basic-cartridge-length-audit.md",
        "Vendored Raw Disk Sweep",
    ) and marker(
        ".github/workflows/lvs.yml",
        "Check BASIC low-stub inspection freshness",
    )
    basic_tail_hypotheses_rejected = marker(
        "docs/basic-cartridge-tail-hypotheses.md",
        "Status: **SIMPLE TAIL HYPOTHESES REJECTED**",
    ) and marker(
        "docs/basic-cartridge-tail-hypotheses.md",
        "7e 12 23 13 0b 78 b1 c2 09 20 c3",
    ) and marker(
        "docs/basic-cartridge-tail-hypotheses.md",
        "patch-loop-count-1f00",
    ) and marker(
        "docs/basic-cartridge-tail-hypotheses.md",
        "patch-entry-jump-0200",
    )
    basic_missing_page_constrained = marker(
        "docs/basic-cartridge-missing-page-constraints.md",
        "Status: **MISSING PAGE CONSTRAINED / ARTIFACT REQUIRED**",
    ) and marker(
        "docs/basic-cartridge-missing-page-constraints.md",
        "| Control-transfer references | 1 |",
    ) and marker(
        ".github/workflows/lvs.yml",
        "docs/basic-cartridge-missing-page-constraints.md",
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
    ekdos_jbasic_command_pinned = marker(
        "docs/ekdos-jbasic-command-probe.md",
        "Status: **EKDOS JBASIC PROMPT ORACLE PINNED**",
    ) and marker(
        ".github/workflows/lvs.yml",
        "sync/ekdos_jbasic_command_probe.py",
    )
    hdl_jbasic_stimulus = (
        marker(
            "docs/juku-top-checkpoint-jbasic-probe.md",
            "Status: **HDL EKDOS JBASIC READY**",
        )
        or
        marker(
            "docs/juku-top-checkpoint-jbasic-probe.md",
            "Status: **HDL EKDOS JBASIC FDC DATA READ READY**",
        )
        or marker(
            "docs/juku-top-checkpoint-jbasic-probe.md",
            "Status: **HDL EKDOS JBASIC POST-COMMAND FDC READY**",
        )
        or marker(
            "docs/juku-top-checkpoint-jbasic-probe.md",
            "Status: **HDL EKDOS JBASIC KEYBOARD SAMPLING READY**",
        )
        or marker(
            "docs/juku-top-checkpoint-jbasic-probe.md",
            "Status: **HDL EKDOS JBASIC COMMAND STIMULUS READY**",
        )
    ) and marker(
        "hdl/sim/juku_top_checkpoint_resume_tb.v",
        "stopjbasicready",
    )
    hdl_jbasic_checkpoint_guard = hdl_jbasic_stimulus and Path("sync/ekdos_jbasic_checkpoint_check.sh").exists()
    hdl_jbasic_late_ready = marker(
        "docs/juku-top-checkpoint-jbasic-late-probe.md",
        "Status: **HDL EKDOS JBASIC LATE READY**",
    ) and marker(
        "docs/juku-top-checkpoint-jbasic-late-probe.md",
        "[RESUME-JBASIC] READY prompt reached",
    )
    hdl_jbasic_mid_drain = marker(
        "docs/juku-top-checkpoint-jbasic-mid-probe.md",
        "Status: **HDL EKDOS JBASIC MID FDC DRAIN READY**",
    ) and marker(
        "docs/juku-top-checkpoint-jbasic-mid-probe.md",
        "target=10752",
    )
    hdl_jbasic_uninterrupted_ready = marker(
        "docs/juku-top-jbasic-verilator-probe.md",
        "Status: **HDL JUKU_TOP JBASIC READY REACHED**",
    ) and marker(
        "docs/juku-top-jbasic-verilator-probe.md",
        "FDC state line: `[FDCSTATE] data_reads=19968 buffer_pos=0 buffer_len=0`",
    )
    hdl_jbasic_uninterrupted_guarded = hdl_jbasic_uninterrupted_ready and marker(
        "sync/juku_top_jbasic_prompt_check.sh",
        "JUKU-TOP-JBASIC-PROMPT-CHECK: PASS",
    ) and marker(
        ".github/workflows/lvs.yml",
        "./sync/juku_top_jbasic_prompt_check.sh",
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
    jmon33_hdl_cursor = marker(
        "docs/jmon33-hdl-cursor-probe.md",
        "Status: **JMON33 HDL CURSOR ORACLE REACHED**",
    ) and marker(
        "docs/jmon33-hdl-cursor-probe.md",
        "framebuffer SHA256 | `f18897c84ae0697adc779c60de95eb32c869ae7f000f4a2007aa9c64df8e2397`",
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
    video_slot_timing_audit = marker(
        "docs/video-slot-timing-audit.md",
        "Status: **VIDEO SLOT TIMING AUDITED / D94 PROM DUMP PENDING**",
    ) and marker(
        "docs/video-slot-timing-audit.md",
        "D94 `.092`",
    )
    d94_constraints = marker(
        "docs/d94-reconstruction-constraints.md",
        "Status: **D94 RECONSTRUCTION CONSTRAINED / DUMP REQUIRED**",
    ) and marker(
        "docs/d94-reconstruction-constraints.md",
        "D94.10-D94.14",
    ) and marker(
        "docs/d94-reconstruction-constraints.md",
        "Textual / Photo Survey Leads",
    ) and marker(
        "docs/d94-reconstruction-constraints.md",
        "Address Space",
    ) and marker(
        "docs/d94-reconstruction-constraints.md",
        "2^256",
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
                    "`docs/source-coverage-audit.md` is a generated PASS audit for "
                    "Arti, Elektroonikamuuseum, infoaed/juku3000 ROM, "
                    "Arvutimuuseum, Emu80v4, and local WD1772/VG93 reference "
                    "coverage; "
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
                    "`docs/firmware-gap-ledger.md` consolidates PROM burnability: "
                    "D6/D8 have repo-burnable Tier 1/2 fallbacks while D2/D94 "
                    "remain no-burn until disk files or dumps land; "
                    if firmware_gap_ledger_ready
                    else ""
                )
                + (
                    "`docs/d2-reconstruction-constraints.md` pins D2 `.037` as a "
                    "bus-arbitration/wait PROM with no current signal nets in "
                    "board JSON/DSN/PCB or burnable fallback; "
                    if d2_constraints_generated
                    else ""
                )
                + (
                    "`docs/re3-firmware-inspection.md` guards the scanned `.113`/"
                    "`.117` РЕ3 tables and keeps them explicitly out of the D8/D94 "
                    "burnable fallback set; "
                    if re3_firmware_inspected
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
                + (
                    "`docs/public-software-archive-inventory.md` classifies the "
                    "public Arti/museum software listings and vendors the required "
                    "`J3KUTIL4.JUK` prompt-proof disk while confirming "
                    "`JUKUROMS.ZIP` is byte-identical to `roms/`; "
                    if public_software_inventory
                    else ""
                )
                + (
                    "`docs/public-manual-archive-inventory.md` classifies the "
                    "public Arti/museum manual and drawing listings, with "
                    "board-critical PDFs mirrored or covered and large user/service "
                    "manuals kept optional; "
                    if public_manual_inventory
                    else ""
                )
                + ekdos_source_m1_phrase
                + (
                    "`docs/owner-measurement-shortlist.md` reduces the remaining "
                    "owner/community asks to programming/PROM/media truth, "
                    "cartridge BASIC truth, and P1 continuity items; "
                    if owner_measurement_shortlist
                    else ""
                )
                + (
                    "`docs/fdc-hardware-handoff.md` guards the FDC bus-side board "
                    "handoff while keeping D93 INTRQ/DRQ, MR/CLK, and D100 OE/T as "
                    "owner-continuity items; "
                    if fdc_handoff_guarded
                    else ""
                )
                + (
                    "`docs/serial-handoff.md` guards the D11 USART bus-side path, "
                    "D57 baud handoff, line drivers, receiver, X3 nets, and a "
                    "minimal 8251 Tx/Rx loopback behavior slice while leaving "
                    "external X3 loopback/full protocol modes as Tier-2 work; "
                    if serial_handoff_guarded
                    else ""
                )
                + (
                    "`docs/beeper-readiness.md` guards the D57 channel-1 digital "
                    "`SOUND` source plus the traced R90/VT1/VD4/R91/R48/SPKR board "
                    "handoff while leaving speaker current/level proof to bring-up; "
                    if beeper_handoff_guarded
                    else ""
                )
                + "PROM truth still needs disk files or hardware dumps for Tier 3."
            ),
            "next": "Send the owner/community request, locate programming disk/media or get RE3/RT4 dumps, and check any BASIC cartridge artifact/procedure against the current probes.",
        },
        {
            "id": "M2",
            "target": "EKDOS boots in the twin",
            "status": (
                "VENDORED JUKU1 PROMPT PROVEN / HDL PROMPT GUARDED"
                if ekdos_juku1_prompt and hdl_prompt_guarded
                else "VENDORED JUKU1 PROMPT PROVEN / HDL PROMPT READY"
                if ekdos_juku1_prompt and hdl_prompt_ready
                else "VENDORED JUKU1 PROMPT PROVEN / HDL RAW-SECTOR READY"
                if ekdos_juku1_prompt and hdl_fdc_vendored_sector
                else "VENDORED JUKU1 PROMPT PROVEN / HDL PENDING"
                if ekdos_juku1_prompt
                else "COSIM PROMPT PROVEN / HDL PENDING" if ekdos_external_prompt else "PARTIAL"
            ),
            "evidence": (
                "`docs/ekdos-media-acquisition.md` records vendored Arti `JUKU1.7Z` / "
                "`JUKU2.7Z` media under `media/disks/`; `JUKU1.CPM` reaches `A>` "
                "through the factory `TDD` path; `docs/fdc-readiness.md` guards the "
                "HDL WD1793 raw-sector path and records the uninterrupted `juku_top` "
                "prompt proof."
                + ekdos_source_m2_phrase
                + (
                    " `docs/juku-top-checkpoint-resume.md` is now a push-CI "
                    "checkpoint-resume guard for the post-checkpoint PIC `0xD6` "
                    "write and no-key keyboard `0xCF` read through decoded "
                    "`juku_top` ports."
                    if hdl_checkpoint_resume_ci_guard
                    else ""
                )
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
                + (
                    "`docs/juku-top-fdc-verilator-probe.md` records the faster "
                    "reset-driven Verilator run reaching decoded PIC setup, frame "
                    "interrupts, 10,752 FDC data-register reads, and the EKDOS `A>` "
                    "bitmap at VRAM 73,405. "
                    if hdl_verilator_fdc_prompt
                    else ""
                )
                + (
                    "`docs/juku-top-fdc-alignment.md` compares that state with "
                    "cosim and pins the prompt-ready boundary at PC `0x097A`. "
                    if hdl_fdc_alignment
                    else ""
                )
                + (
                    "`sync/juku_top_fdc_prompt_check.sh` is the routine guard for "
                    "the committed prompt evidence, with an opt-in deep Verilator "
                    "rerun mode for local proof refresh."
                    if hdl_prompt_guarded
                    else "The prompt path is proven; add the routine guard before closing M2."
                )
                if ekdos_juku1_prompt and hdl_prompt_ready
                else "`docs/ekdos-media-acquisition.md` records vendored Arti `JUKU1.7Z` / "
                "`JUKU2.7Z` media under `media/disks/`; `JUKU1.CPM` reaches `A>` "
                "through the factory `TDD` path; `docs/fdc-readiness.md` guards HDL "
                "WD1793 raw-sector reads from vendored `JUKU1.CPM`."
                + ekdos_source_m2_phrase
                + "The reset-driven `juku_top` ROMBIOS-to-EKDOS prompt proof remains open."
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
                "Move on to the remaining video timing, PROM-truth, BASIC, and PCB tasks."
                if hdl_prompt_guarded
                else "Add the routine guard for the uninterrupted juku_top prompt proof."
                if hdl_prompt_ready
                else "Finish the reset-driven juku_top ROMBIOS TDD prompt path without checkpoint/resume."
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
                + (
                    "`docs/video-slot-timing-audit.md` now verifies the traced "
                    "D42/D43 serializer, D48-D53 mux/decode presence, explicit "
                    "sim-only `VA/VQ` read path, and missing D94 `.092` timing "
                    "PROM/table; "
                    if video_slot_timing_audit
                    else ""
                )
                + (
                    "`docs/d94-reconstruction-constraints.md` pins the automatic "
                    "D94 `.092` reconstruction boundary: address inputs are traced "
                    "to `BA11..BA15` and the official `.009` BOM/photo trail "
                    "identifies D94 as `.092`, while `E_N`, all data-output "
                    "destinations, and the `.092` contents remain absent from the "
                    "repository artifact scan; the generated 32-row address-space "
                    "table leaves 256 content bits unresolved, with "
                    "`kicad/juku.dsn` and `kicad/juku.kicad_pcb` confirming only "
                    "D94 power/address coverage; "
                    if d94_constraints
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
                "EKDOS JBASIC HDL READY / JMON33 RESET+CARTRIDGE BASIC PENDING"
                if jmon33_checkpoint_cursor and basic_launch_reached and jmon33_command_surface and hdl_jbasic_uninterrupted_guarded
                else
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
                    "`docs/jmon33-hdl-cursor-probe.md` now proves the uninterrupted "
                    "`juku_top` Monitor 3.3 reset-to-cursor path reaches the full "
                    "10/10-row cursor and exact cosim framebuffer hash under Verilator. "
                    if jmon33_hdl_cursor
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
                "cartridge, then later executing in the 0x4000 RAM window, but "
                "that execution is a mode-1 RAM `0x3FFF -> 0x4000` fall-through "
                "and only sees zero-byte writes. "
                "The same report now records that the cartridge body from 0x0200 "
                "is copied into matching low RAM "
                "for 7,680 bytes with 0 body mismatches, while the low "
                "entry/control area has 14 byte mismatches, plus "
                "the local MAME Monitor 3.3/JBASIC compatibility warning and the "
                "BASIC images' absolute JMP 0x0107 entry. "
                + (
                    "`docs/basic-low-stub-inspection.md` now groups those 14 "
                    "low-stub deltas and pins the Monitor 3.3 high-ROM handoff: "
                    "the monitor validates the cartridge header, copies from "
                    "the `0x4000` cartridge window into low RAM at `0x0100`, "
                    "then jumps to `0x0100`; the runtime bootstrap then runs "
                    "`0x0100 -> 0x0107 -> 0x2000` and relocates runtime "
                    "`0x0200..0x21FF` down to `0x0100..0x20FF`. The loaded "
                    "image changes the "
                    "`0x0100` stack pointer to `0xFFFE`, leaves the body exact, "
                    "and pins the relocation self-overwrite: `0x2009` is replaced "
                    "from zero-filled `0x2109` with 246 copies left, and the "
                    "nominal `JMP 0x0100` at `0x2013` is replaced from `0x2113` "
                    "with 236 copies left. That narrows the remaining cartridge "
                    "work to a public-8K-payload/Monitor-3.3 compatibility "
                    "boundary after the `0x2000` bootstrap. "
                    if basic_low_stub_inspected
                    else ""
                )
                + (
                    "`docs/basic-cartridge-length-audit.md` sharpens that boundary: "
                    "the public 8 KiB payload loaded at `0x0100` ends at `0x20FF`, "
                    "but the bootstrap copies `0x0200..0x21FF`, leaving an exact "
                    "missing tail page `0x2100..0x21FF`; disk-side BASIC candidates "
                    "and all vendored raw `*.CPM`/`*.JUK` images are checked and "
                    "are not direct tail donors. "
                    if basic_cartridge_length_audited
                    else ""
                )
                + (
                    "`docs/basic-cartridge-tail-hypotheses.md` derives the loop-tail "
                    "bytes required for a viable missing page and rejects fill, raw "
                    "append, final-page mirror, the simple `0x1F00` relocation-"
                    "count patch, and a direct `0x0200` body-entry jump at runtime. "
                    if basic_tail_hypotheses_rejected
                    else ""
                )
                + (
                    "`docs/basic-cartridge-missing-page-constraints.md` further "
                    "constrains the unknown page: known-body direct operands "
                    "reference 15 unique bytes in `0x2000..0x2018`, and the sole "
                    "direct control transfer is the relocation loop's `JNZ 0x2009`; "
                    if basic_missing_page_constrained
                    else ""
                )
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
                + (
                    " `docs/vendored-disk-catalog.md` records a disk-side BASIC "
                    "lead: `JUKU1.CPM` contains `JBASIC.COM`, and `JUKPROG2.CPM` "
                    "contains `JBASIC.COM` plus BASIC compiler/runtime files."
                    if vendored_disk_cataloged
                    else ""
                )
                + (
                    " `docs/basic-disk-extraction.md` vendors the strongest "
                    "disk-side BASIC inputs under `ref/extracted-software/`: "
                    "`JUKPROG2_JBASIC.COM` as the conservative directory-backed "
                    "extraction lead, `JUKPROG2_JBASIC_live_candidate.COM` as the "
                    "live EKDOS-loaded payload, and `JUKU1_JBASIC_raw_candidate.COM` "
                    "as a raw-offset candidate with `BASIC`/`READY`/`ERROR` strings."
                    if basic_disk_extracted
                    else ""
                )
                + (
                    " `docs/ekdos-jbasic-command-probe.md` pins the next EKDOS "
                    "disk-side BASIC prompt oracle: `TDD` plus a prompt-wait marker and `JBASIC\\r` waits for the `A>` prompt "
                    "bitmap, consumes all command keys on `JUKPROG2.CPM`, triggers "
                    "19,968 WD1793 data reads in a deeper 900,000,000-cycle run, "
                    "leaves the live candidate entry signature plus relocated "
                    "`ERROR`/`READY`/`BASIC` strings in RAM, and pins exact "
                    "8x7 glyph matches for visible `A>JBASIC`, `READY`, and the "
                    "block cursor with final video/PIT port-state context."
                    if ekdos_jbasic_command_pinned
                    else ""
                )
                + (
                    " `docs/juku-top-checkpoint-jbasic-probe.md` now bridges "
                    "that path into a checkpoint-resumed HDL BASIC prompt: "
                    "`juku_top` loads the `JUKPROG2.CPM` `A>` checkpoint "
                    "with `state_pc_bias=-1`, injects `JBASIC` plus Return with "
                    "frame-scale holds/gaps and `+jbasickeys=1`, observes the "
                    "full visible `A>JBASIC` command oracle, completes disk-backed "
                    "FDC data reads, and reaches `[RESUME-JBASIC] READY prompt "
                    "reached` at mcyc 823,184 / 73,925 VRAM writes. "
                    "The FDC model now latches side effects on decoded active I/O "
                    "strobes, fixing the stale-register 4,096-read boundary."
                    + (
                        " `sync/ekdos_jbasic_checkpoint_check.sh` is the named "
                        "local/deep guard for this checkpoint-resumed BASIC READY "
                        "boundary."
                        if hdl_jbasic_checkpoint_guard
                        else ""
                    )
                    if hdl_jbasic_stimulus
                    else ""
                )
                + (
                    " `docs/juku-top-checkpoint-jbasic-late-probe.md` proves "
                    "the late checkpoint-resumed HDL boundary: from the cosim "
                    "state after 19,968 WD1793 data-register reads, `juku_top` "
                    "continues with no keyboard stimulus to `[RESUME-JBASIC]` "
                    "and renders the fixed-`0xD800` `READY` glyph at scanline 121."
                    if hdl_jbasic_late_ready
                    else ""
                )
                + (
                    " `docs/juku-top-checkpoint-jbasic-mid-probe.md` preserves "
                    "the bounded mid-transfer checkpoint: from the 17,408-read cosim checkpoint, "
                    "checkpoint-resumed `juku_top` drains 10,752 additional "
                    "decoded `IN 0x1F` data-register reads before the bounded stop."
                    if hdl_jbasic_mid_drain
                    else ""
                )
                + (
                    " `docs/juku-top-jbasic-verilator-probe.md` proves the "
                    "uninterrupted reset-driven `juku_top` path on `JUKPROG2.CPM`: "
                    "EKDOS `A>` at VRAM 73,405, visible `A>JBASIC` at VRAM "
                    "73,485, BASIC `READY` at VRAM 73,885, and 19,968 WD1793 "
                    "data-register reads; `sync/juku_top_jbasic_prompt_check.sh` "
                    "guards the committed evidence with an opt-in deep rerun."
                    if hdl_jbasic_uninterrupted_guarded
                    else ""
                )
                if jmon33_checkpoint_cursor and basic_launch_reached
                else "jmon33 interrupt/first-write/cosim cursor probes exist; "
                "`docs/basic-launch-probe.md` shows Monitor 3.3 reading the BASIC "
                "cartridge, then later executing in the 0x4000 RAM window, but "
                "that execution is a mode-1 RAM `0x3FFF -> 0x4000` fall-through "
                "and only sees zero-byte writes. "
                "The same report now records that the cartridge body from 0x0200 "
                "is copied into matching low RAM "
                "for 7,680 bytes with 0 body mismatches, while the low "
                "entry/control area has 14 byte mismatches, plus "
                "the local MAME Monitor 3.3/JBASIC compatibility warning and the "
                "BASIC images' absolute JMP 0x0107 entry. "
                + (
                    "`docs/basic-low-stub-inspection.md` now groups those 14 "
                    "low-stub deltas and pins the Monitor 3.3 high-ROM handoff: "
                    "the monitor validates the cartridge header, copies from "
                    "the `0x4000` cartridge window into low RAM at `0x0100`, "
                    "then jumps to `0x0100`; the runtime bootstrap then runs "
                    "`0x0100 -> 0x0107 -> 0x2000` and relocates runtime "
                    "`0x0200..0x21FF` down to `0x0100..0x20FF`. The loaded "
                    "image changes the "
                    "`0x0100` stack pointer to `0xFFFE`, leaves the body exact, "
                    "and pins the relocation self-overwrite: `0x2009` is replaced "
                    "from zero-filled `0x2109` with 246 copies left, and the "
                    "nominal `JMP 0x0100` at `0x2013` is replaced from `0x2113` "
                    "with 236 copies left. That narrows the remaining cartridge "
                    "work to a public-8K-payload/Monitor-3.3 compatibility "
                    "boundary after the `0x2000` bootstrap. "
                    if basic_low_stub_inspected
                    else ""
                )
                + (
                    "`docs/basic-cartridge-length-audit.md` sharpens that boundary: "
                    "the public 8 KiB payload loaded at `0x0100` ends at `0x20FF`, "
                    "but the bootstrap copies `0x0200..0x21FF`, leaving an exact "
                    "missing tail page `0x2100..0x21FF`; disk-side BASIC candidates "
                    "and all vendored raw `*.CPM`/`*.JUK` images are checked and "
                    "are not direct tail donors. "
                    if basic_cartridge_length_audited
                    else ""
                )
                + (
                    "`docs/basic-cartridge-tail-hypotheses.md` derives the loop-tail "
                    "bytes required for a viable missing page and rejects fill, raw "
                    "append, final-page mirror, the simple `0x1F00` relocation-"
                    "count patch, and a direct `0x0200` body-entry jump at runtime. "
                    if basic_tail_hypotheses_rejected
                    else ""
                )
                + (
                    "`docs/basic-cartridge-missing-page-constraints.md` further "
                    "constrains the unknown page: known-body direct operands "
                    "reference 15 unique bytes in `0x2000..0x2018`, and the sole "
                    "direct control transfer is the relocation loop's `JNZ 0x2009`; "
                    if basic_missing_page_constrained
                    else ""
                )
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
                + (
                    " `docs/vendored-disk-catalog.md` records a disk-side BASIC "
                    "lead: `JUKU1.CPM` contains `JBASIC.COM`, and `JUKPROG2.CPM` "
                    "contains `JBASIC.COM` plus BASIC compiler/runtime files."
                    if vendored_disk_cataloged
                    else ""
                )
                + (
                    " `docs/basic-disk-extraction.md` vendors the strongest "
                    "disk-side BASIC inputs under `ref/extracted-software/`: "
                    "`JUKPROG2_JBASIC.COM` as the conservative directory-backed "
                    "extraction lead, `JUKPROG2_JBASIC_live_candidate.COM` as the "
                    "live EKDOS-loaded payload, and `JUKU1_JBASIC_raw_candidate.COM` "
                    "as a raw-offset candidate with `BASIC`/`READY`/`ERROR` strings."
                    if basic_disk_extracted
                    else ""
                )
                + (
                    " `docs/ekdos-jbasic-command-probe.md` pins the next EKDOS "
                    "disk-side BASIC prompt oracle: `TDD` plus a prompt-wait marker and `JBASIC\\r` waits for the `A>` prompt "
                    "bitmap, consumes all command keys on `JUKPROG2.CPM`, triggers "
                    "19,968 WD1793 data reads in a deeper 900,000,000-cycle run, "
                    "leaves the live candidate entry signature plus relocated "
                    "`ERROR`/`READY`/`BASIC` strings in RAM, and pins exact "
                    "8x7 glyph matches for visible `A>JBASIC`, `READY`, and the "
                    "block cursor with final video/PIT port-state context."
                    if ekdos_jbasic_command_pinned
                    else ""
                )
                + (
                    " `docs/juku-top-checkpoint-jbasic-probe.md` now bridges "
                    "that path into a checkpoint-resumed HDL BASIC prompt: "
                    "`juku_top` loads the `JUKPROG2.CPM` `A>` checkpoint "
                    "with `state_pc_bias=-1`, injects `JBASIC` plus Return with "
                    "frame-scale holds/gaps and `+jbasickeys=1`, observes the "
                    "full visible `A>JBASIC` command oracle, completes disk-backed "
                    "FDC data reads, and reaches `[RESUME-JBASIC] READY prompt "
                    "reached` at mcyc 823,184 / 73,925 VRAM writes. "
                    "The FDC model now latches side effects on decoded active I/O "
                    "strobes, fixing the stale-register 4,096-read boundary."
                    + (
                        " `sync/ekdos_jbasic_checkpoint_check.sh` is the named "
                        "local/deep guard for this checkpoint-resumed BASIC READY "
                        "boundary."
                        if hdl_jbasic_checkpoint_guard
                        else ""
                    )
                    if hdl_jbasic_stimulus
                    else ""
                )
                + (
                    " `docs/juku-top-checkpoint-jbasic-late-probe.md` proves "
                    "the late checkpoint-resumed HDL boundary: from the cosim "
                    "state after 19,968 WD1793 data-register reads, `juku_top` "
                    "continues with no keyboard stimulus to `[RESUME-JBASIC]` "
                    "and renders the fixed-`0xD800` `READY` glyph at scanline 121."
                    if hdl_jbasic_late_ready
                    else ""
                )
                + (
                    " `docs/juku-top-checkpoint-jbasic-mid-probe.md` preserves "
                    "the bounded mid-transfer checkpoint: from the 17,408-read cosim checkpoint, "
                    "checkpoint-resumed `juku_top` drains 10,752 additional "
                    "decoded `IN 0x1F` data-register reads before the bounded stop."
                    if hdl_jbasic_mid_drain
                    else ""
                )
                + (
                    " `docs/juku-top-jbasic-verilator-probe.md` proves the "
                    "uninterrupted reset-driven `juku_top` EKDOS `JBASIC` path "
                    "to visible BASIC `READY`, and "
                    "`sync/juku_top_jbasic_prompt_check.sh` guards it."
                    if hdl_jbasic_uninterrupted_guarded
                    else ""
                )
                if basic_launch_reached
                else "jmon33 interrupt/first-write/cosim cursor probes exist; "
                "`docs/basic-launch-probe.md` still says BASIC LAUNCH NOT YET REACHED."
            ),
            "next": (
                "Identify the correct Monitor 3.3 cartridge BASIC launch path and "
                "keep the disk-side EKDOS `JBASIC` HDL guard fresh."
                if jmon33_checkpoint_cursor
                else "Compare HDL at the stronger jmon33 cursor boundary, identify the correct Monitor 3.3 cartridge BASIC launch path, and keep the pinned EKDOS BASIC HDL guard fresh."
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
                    "residual source-risk nets for staged bring-up and checks "
                    f"{bringup_endpoint_count} listed endpoints against "
                    "`kicad/juku.kicad_pcb` pad net assignments, and all "
                    f"{board_endpoint_count} modeled board endpoints "
                    "against both source and routed PCB pad net assignments"
                    + (
                        ", and `docs/fdc-hardware-handoff.md` narrows the FDC "
                        "physical handoff to guarded bus-side wiring plus owner-only "
                        "continuity points"
                        if fdc_handoff_guarded
                        else ""
                    )
                    + (
                        ", and `docs/serial-handoff.md` guards the serial bus-side "
                        "D11/X3 handoff plus a minimal 8251 Tx/Rx loopback behavior "
                        "slice while keeping external loopback proof for bring-up"
                        if serial_handoff_guarded
                        else ""
                    )
                    + (
                        ", and `docs/beeper-readiness.md` guards the beeper digital "
                        "source plus traced speaker handoff while leaving only analog "
                        "level/current proof for bring-up"
                        if beeper_handoff_guarded
                        else ""
                    )
                    + (
                        ", and `docs/board-fidelity-gap-ledger.md` catalogs the "
                        "chip-provenance and net-source gaps that still separate "
                        "the upload-ready PCB from fully historical-source-proven "
                        "1:1 reproduction"
                        if board_fidelity_gaps_cataloged
                        else ""
                    )
                    + "; "
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
                + (
                    "`docs/replica-dual-config-bom.md` and "
                    "`docs/replica-dual-config-bom.csv` provide the generated "
                    "functional/modernized kit BOM; "
                    if sourcing_ready and dual_config_bom_ready
                    else ""
                ) +
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
