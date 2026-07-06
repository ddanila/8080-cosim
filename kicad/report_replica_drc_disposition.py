#!/usr/bin/env python3
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DRC = ROOT / "fab" / "gerbers" / "juku_routed-drc.json"
DEFAULT_OUT = ROOT / "docs" / "replica-fab-drc-disposition.md"

BLOCKING_TYPES = {
    "clearance",
    "shorting_items",
    "unconnected_items",
    "copper_edge_clearance",
    "lib_footprint_issues",
}
REVIEW_ONLY_TYPES = {
    "courtyards_overlap": {
        "expected": 55,
        "disposition": "Waived as dense authentic placement after visual assembly-fit review.",
    },
    "pth_inside_courtyard": {
        "expected": 71,
        "disposition": "Waived as dense through-hole/socket proximity after visual assembly-fit review.",
    },
    "silk_over_copper": {
        "expected": 199,
        "disposition": "Cosmetic silkscreen clipping; order-time preview must confirm labels remain usable.",
    },
    "silk_overlap": {
        "expected": 199,
        "disposition": "Cosmetic silkscreen overlap in dense labels/outlines; order-time preview must confirm labels remain usable.",
    },
    "text_thickness": {
        "expected": 75,
        "disposition": "GOST/TrueType stroke warning; manufacturing-readability item, not copper geometry.",
    },
}


def repo_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value not in (None, "") else "-" for value in values) + " |"


def ref_from_description(description):
    match = re.search(r"\b(?:Footprint|of)\s+([A-Z]+[0-9]+)\b", description)
    return match.group(1) if match else ""


def violation_refs(violation):
    refs = []
    for item in violation.get("items", []):
        ref = ref_from_description(item.get("description", ""))
        if ref:
            refs.append(ref)
    return refs


def top_refs(violations, limit=8):
    counts = Counter()
    for violation in violations:
        counts.update(set(violation_refs(violation)))
    return ", ".join(ref for ref, _count in counts.most_common(limit)) or "-"


def build_report(drc_path):
    drc = json.loads(drc_path.read_text())
    violations = drc.get("violations", [])
    unconnected = drc.get("unconnected_items", [])
    counts = Counter(v.get("type", "unknown") for v in violations)
    by_type = defaultdict(list)
    for violation in violations:
        by_type[violation.get("type", "unknown")].append(violation)

    failures = []
    blocking_counts = Counter({name: counts.get(name, 0) for name in BLOCKING_TYPES if name != "unconnected_items"})
    blocking_counts["unconnected_items"] = len(unconnected)
    for name, count in sorted(blocking_counts.items()):
        if count:
            failures.append(f"Blocking DRC class `{name}` is nonzero: {count}")

    unknown_types = sorted(set(counts) - set(REVIEW_ONLY_TYPES) - (BLOCKING_TYPES - {"unconnected_items"}))
    for name in unknown_types:
        failures.append(f"Unexpected DRC class without disposition: `{name}`={counts[name]}")

    review_rows = []
    for name, spec in sorted(REVIEW_ONLY_TYPES.items()):
        actual = counts.get(name, 0)
        expected = spec["expected"]
        if actual != expected:
            failures.append(f"Review-only DRC count changed for `{name}`: expected {expected}, got {actual}")
        review_rows.append([
            f"`{name}`",
            actual,
            expected,
            top_refs(by_type.get(name, [])),
            spec["disposition"],
        ])

    status = "READY" if not failures else "REVIEW REQUIRED"
    lines = [
        "# Replica fab DRC disposition",
        "",
        f"Source report: `{repo_relative(drc_path)}`",
        f"Status: **{status}**",
        "",
        "This generated report is the tracked disposition record for the main-board",
        "fabrication DRC findings. It deliberately fails if a count changes or a new",
        "DRC class appears, so the order package cannot carry an old waiver forward",
        "silently.",
        "",
        "## Machine Blockers",
        "",
        "| Type | Count | Disposition |",
        "| --- | ---: | --- |",
    ]
    for name in sorted(blocking_counts):
        disposition = "Pass" if blocking_counts[name] == 0 else "Fix before order"
        lines.append(table_row([f"`{name}`", blocking_counts[name], disposition]))

    lines.extend([
        "",
        "## Review-Only Classes",
        "",
        "| DRC type | Count | Expected | Highest-repeat references | Disposition |",
        "| --- | ---: | ---: | --- | --- |",
    ])
    lines.extend(table_row(row) for row in review_rows)

    lines.extend([
        "",
        "## Order-Time Visual Checks",
        "",
        "- Review `fab/gerbers/external-gerber-review.md` and the generated Tracespace top/bottom PNGs.",
        "- Compare the courtyard/PTH clusters above against the vendor preview before payment.",
        "- Confirm silkscreen reference designators, polarity marks, connector labels, and bring-up labels remain readable.",
        "- Keep the 2-layer, 310 mm x 266 mm board outline and standard 1.6 mm FR-4 unless deliberately changed after DFM review.",
        "",
        "## Related Gates",
        "",
        "- `fab/gerbers/review-waivers.md`: exact-count waiver gate generated by `kicad/report_review_waivers.py`.",
        "- `fab/gerbers/external-gerber-review.md`: independent Tracespace render evidence.",
        "- `docs/replica-power-trace-readiness.md`: routed power-trace DFM envelope.",
        "- `docs/replica-order-upload-runbook.md`: final deterministic Gerber/drill upload archive and checksum command.",
        "",
        "## Resolved Items",
        "",
        "- `lib_footprint_issues`: resolved by vendoring `juku:CONN_X1`, `CONN_X2`, `CONN_X3`, `CONN_X8`, and `CONN_X9` under `kicad/juku.pretty/` with the project `kicad/fp-lib-table`.",
        "- `copper_edge_clearance` and `silk_edge_clearance`: resolved by deferring the two conflicting generated cutouts at `(104.0,251.4)` and `(300.3,138.1)` until the exact non-rectangular outline can be re-read.",
        "- Review-only DRC classes are accepted only at the exact counts above; changed counts require a fresh disposition.",
        "",
        f"Visual disposition failures: {len(failures)}",
    ])

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), not failures


def main():
    drc_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_DRC
    out_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_OUT
    report, ok = build_report(drc_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(report)
    print(f"Wrote {repo_relative(out_path)}")
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
