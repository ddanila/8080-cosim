#!/usr/bin/env python3
"""Inspect the vendored WD1772 PLA/PLM text dump."""
from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ref" / "wd1772-vg93" / "wd1772pla.txt"
REPORT = ROOT / "docs" / "wd1772-pla-inspection.md"

ROW_RE = re.compile(r"^(A\d{2})\|(R\d{3})\|([01]{19})\|([019]{19})$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def table_row(values: list[object]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def parse_rows() -> tuple[list[dict[str, object]], list[str], int]:
    rows: list[dict[str, object]] = []
    ignored: list[str] = []
    section = 1
    for raw in SOURCE.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("---+"):
            section += 1
            continue
        match = ROW_RE.match(line)
        if not match:
            ignored.append(line)
            continue
        a_id, r_id, inputs, outputs = match.groups()
        rows.append(
            {
                "section": section,
                "a": a_id,
                "r": r_id,
                "inputs": inputs,
                "outputs": outputs,
            }
        )
    return rows, ignored, section


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
    input_widths = sorted({len(str(row["inputs"])) for row in rows})
    output_widths = sorted({len(str(row["outputs"])) for row in rows})
    input_chars = sorted(set("".join(str(row["inputs"]) for row in rows)))
    output_chars = sorted(set("".join(str(row["outputs"]) for row in rows)))
    rows_with_9 = [row for row in rows if "9" in str(row["inputs"]) + str(row["outputs"])]
    section_counts = Counter(int(row["section"]) for row in rows)
    a_counts = Counter(str(row["a"]) for row in rows)
    r_counts = Counter(str(row["r"]) for row in rows)
    term_counts = Counter((str(row["inputs"]), str(row["outputs"])) for row in rows)

    failures = []
    if len(rows) != 120:
        failures.append(f"expected 120 data rows, found {len(rows)}")
    if input_widths != [19]:
        failures.append(f"expected 19 input bits, found widths {input_widths}")
    if output_widths != [19]:
        failures.append(f"expected 19 output bits, found widths {output_widths}")
    if input_chars != ["0", "1"]:
        failures.append(f"unexpected input character set: {input_chars}")
    if output_chars != ["0", "1", "9"]:
        failures.append(f"unexpected output character set: {output_chars}")
    if len(rows_with_9) != 1:
        failures.append(f"expected exactly one row with 9 markers, found {len(rows_with_9)}")
    if len(ignored) != 3:
        failures.append(f"expected 3 footer guide rows, found {len(ignored)}")

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
        marker_cols = [str(index) for index, char in enumerate(outputs) if char == "9"]
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
