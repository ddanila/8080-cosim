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
                + "PROM bytes still need disk files, hardware dumps, or accepted reconstruction."
            ),
            "next": "Locate programming disk/media or get RE3/RT4 dumps.",
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
                    " `docs/ekdos-timing-reference.md` pins the fast cosim timing window "
                    "for first frame IRQ and first FDC command. "
                    if ekdos_timing_guard
                    else " "
                )
                + "Full ROMBIOS-to-EKDOS prompt execution in `juku_top` remains open."
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
                "Drive the full ROMBIOS TDD path through juku_top to an EKDOS prompt."
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
                "the faithful RE3/AG3 shared-DRAM slot timing is explicitly still open."
            ),
            "next": "Close the RE3/AG3 timing source and replace the sim-only framebuffer read.",
        },
        {
            "id": "M5",
            "target": "jmon33 live prompt + BASIC launches in the twin",
            "status": "BASIC RAM EXECUTION REACHED / PROMPT+HDL PENDING" if basic_launch_reached else "PARTIAL",
            "evidence": (
                "jmon33 interrupt/first-write/cosim cursor probes exist; "
                "`docs/basic-launch-probe.md` shows Monitor 3.3 reading the BASIC "
                "cartridge and executing in the 0x4000 RAM window, but that window "
                "only receives zero-byte writes; EktaSoft 3.43m #0037 remains a "
                "compatibility boundary."
                if basic_launch_reached
                else "jmon33 interrupt/first-write/cosim cursor probes exist; "
                "`docs/basic-launch-probe.md` still says BASIC LAUNCH NOT YET REACHED."
            ),
            "next": "Compare HDL at the stronger jmon33 cursor boundary, add a BASIC prompt oracle, and port the Monitor 3.3 BASIC path to HDL coverage.",
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
