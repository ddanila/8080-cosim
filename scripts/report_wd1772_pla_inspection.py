#!/usr/bin/env python3
"""Inspect the vendored WD1772 PLA/PLM text dump."""
from __future__ import annotations

from collections import Counter

from wd1772_pla import ROOT, SOURCE, parse_rows, sha256, validate_shape

REPORT = ROOT / "docs" / "wd1772-pla-inspection.md"


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def duplicate_summary(counter: Counter[object], limit: int = 16) -> str:
    def render_key(key: object) -> str:
        if isinstance(key, tuple):
            return "/".join(str(part) for part in key)
        return str(key)

    dupes = [f"`{render_key(key)}` x{count}" for key, count in sorted(counter.items()) if count > 1]
    if not dupes:
        return "-"
    if len(dupes) <= limit:
        return ", ".join(dupes)
    return ", ".join(dupes[:limit]) + f", ... (+{len(dupes) - limit})"


def main() -> int:
    rows, ignored, sections = parse_rows()
    input_widths, output_widths, input_chars, output_chars, rows_with_9, failures = validate_shape(
        rows,
        ignored,
    )
    section_counts = Counter(int(row["section"]) for row in rows)
    a_counts = Counter(str(row["a"]) for row in rows)
    r_counts = Counter(str(row["r"]) for row in rows)
    term_counts = Counter((str(row["inputs"]), str(row["outputs"])) for row in rows)

    status = "PLA SHAPE INSPECTED" if not failures else "PLA SHAPE CHECK FAILED"
    lines = [
        "# WD1772 PLA/PLM inspection",
        "",
        f"Status: **{status}**",
        "",
        "This generated report inspects the vendored `wd1772pla.txt` dump as a",
        "reference artifact. It validates the text-table shape and records the",
        "ambiguous markers that need interpretation before the table can be used as",
        "machine equations. It does not translate the PLA into HDL.",
        "",
        "## Source",
        "",
        "| Field | Value |",
        "| --- | --- |",
        table_row(["File", f"`{SOURCE.relative_to(ROOT)}`"]),
        table_row(["SHA256", f"`{sha256(SOURCE)}`"]),
        "",
        "## Shape",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        table_row(["Data rows", len(rows)]),
        table_row(["Sections", sections]),
        table_row(["Rows per section", ", ".join(f"{idx}: {section_counts[idx]}" for idx in sorted(section_counts))]),
        table_row(["Input bit width", ", ".join(map(str, input_widths))]),
        table_row(["Output bit width", ", ".join(map(str, output_widths))]),
        table_row(["Input alphabet", "".join(input_chars)]),
        table_row(["Output alphabet", "".join(output_chars)]),
        table_row(["Ignored footer guide rows", len(ignored)]),
        "",
        "## Ambiguities",
        "",
        "| Item | Value |",
        "| --- | --- |",
    ]

    if rows_with_9:
        row = rows_with_9[0]
        outputs = str(row["outputs"])
        marker_cols = [str(index) for index in row["ambiguous_output_columns"]]
        lines.append(table_row(["Row with `9` markers", f"`{row['a']}/{row['r']}`"]))
        lines.append(table_row(["`9` output columns (zero-based)", ", ".join(marker_cols)]))
        lines.append(table_row(["Raw output field", f"`{outputs}`"]))
    else:
        lines.append(table_row(["Row with `9` markers", "-"]))

    lines.extend(
        [
            "",
            "## Duplicate Labels",
            "",
            "| Label class | Duplicates |",
            "| --- | --- |",
            table_row(["A labels", duplicate_summary(a_counts)]),
            table_row(["R labels", duplicate_summary(r_counts)]),
            table_row(["Input/output terms", duplicate_summary(term_counts)]),
            "",
            "## Footer Guide Rows",
            "",
        ]
    )
    if ignored:
        lines.extend(f"- `{line}`" for line in ignored)
    else:
        lines.append("- -")

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    REPORT.write_text("\n".join(lines))
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
